"""Multi-seed stability analysis for detection metrics.

Evaluates pipeline consistency by running the evaluation across multiple
random seeds and computing the coefficient of variation (CV) for key
metrics.  A CV below a threshold indicates stable results.

Both arms of the operating point
--------------------------------
Every seed is evaluated against **two** corpora:

* the attack arm — samples from :class:`attacks.corpus.AttackCorpus` — which
  yields the true-positive rate (TPR, historically called the "detection
  rate" here); and
* the benign arm — samples from :class:`evaluation.benign_corpus.BenignCorpus`
  — which yields the false-positive rate (FPR).

A TPR reported without an FPR is not a performance claim: a detector that
returns ``detected=True`` unconditionally scores TPR = 1.0.  The paired
summaries below (Youden's J, precision, F1, specificity) are the quantities
that such a degenerate detector cannot fake — its J is exactly 0.

Reading precision and F1 honestly
---------------------------------
Precision and F1 depend on the ratio of attacks to benign messages in the
evaluation set.  That ratio is a *design choice* here (roughly 100 attacks to
120 benign messages), not an estimate of any deployment base rate, so these
two numbers are comparable **across configurations evaluated on the same
corpora** and are not deployment precision.  Youden's J and the (TPR, FPR)
pair are prevalence-independent and should be preferred for cross-study
comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

__all__ = [
    "SeedMetrics",
    "StabilityReport",
    "coefficient_of_variation",
    "run_multi_seed_stability",
    "make_pipeline_eval_fn",
    "youden_j",
    "precision_from_counts",
    "f1_from_counts",
]


# ---------------------------------------------------------------------------
# Operating-point helpers
# ---------------------------------------------------------------------------


def youden_j(tpr: float, fpr: float) -> float:
    """Youden's J statistic, ``TPR - FPR``.

    J is 0 for any detector that ignores its input — including the
    flag-everything detector (TPR = FPR = 1) and the flag-nothing detector
    (TPR = FPR = 0) — and 1 only for a perfect one.  It is the smallest
    summary that a degenerate detector cannot inflate.
    """
    return float(tpr) - float(fpr)


def precision_from_counts(true_positives: int, false_positives: int) -> float:
    """Positive predictive value ``TP / (TP + FP)``.

    Returns 0.0 when the detector made no positive predictions at all, since
    there is no positive predictive value to report in that case.
    """
    denom = true_positives + false_positives
    if denom <= 0:
        return 0.0
    return true_positives / denom


def f1_from_counts(true_positives: int, false_positives: int, n_attacks: int) -> float:
    """Harmonic mean of precision and recall.

    Returns 0.0 when precision and recall are both zero (no true positives),
    which is the conventional definition and matches the degenerate case.
    """
    if n_attacks <= 0:
        return 0.0
    precision = precision_from_counts(true_positives, false_positives)
    recall = true_positives / n_attacks
    if precision + recall <= 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Per-seed metrics
# ---------------------------------------------------------------------------


@dataclass
class SeedMetrics:
    """Per-seed evaluation metrics for both arms.

    Attributes:
        seed: Random seed used.
        overall_detection_rate: True-positive rate on the attack arm.
        per_architecture: Detection rates keyed by architecture name.
        per_category: Detection rates keyed by attack top-level category.
        false_positive_rate: Flag rate on the benign arm.
        n_attacks: Number of attack samples evaluated.
        n_detected_attacks: Attack samples the pipeline flagged.
        n_benign: Number of benign samples evaluated.  ``0`` means **no
            benign arm was run**, and every derived operating-point number
            below is therefore meaningless — see :attr:`has_benign_arm`.
        n_false_positives: Benign samples the pipeline flagged.
        benign_fpr_by_difficulty: FPR split by benign difficulty stratum.
        benign_fpr_by_category: FPR split by benign message category.
    """

    seed: int
    overall_detection_rate: float
    per_architecture: Dict[str, float] = field(default_factory=dict)
    per_category: Dict[str, float] = field(default_factory=dict)
    false_positive_rate: float = 0.0
    n_attacks: int = 0
    n_detected_attacks: int = 0
    n_benign: int = 0
    n_false_positives: int = 0
    benign_fpr_by_difficulty: Dict[str, float] = field(default_factory=dict)
    benign_fpr_by_category: Dict[str, float] = field(default_factory=dict)

    @property
    def has_benign_arm(self) -> bool:
        """Whether a benign corpus was actually evaluated for this seed.

        ``False`` means :attr:`false_positive_rate` is a default, not a
        measurement, and every paired summary must be suppressed rather than
        reported as zero.
        """
        return self.n_benign > 0

    @property
    def true_positive_rate(self) -> float:
        """Alias for :attr:`overall_detection_rate`, in operating-point terms."""
        return self.overall_detection_rate

    @property
    def specificity(self) -> float:
        """True-negative rate, ``1 - FPR``."""
        return 1.0 - self.false_positive_rate

    @property
    def youden_j(self) -> float:
        """``TPR - FPR`` for this seed."""
        return youden_j(self.overall_detection_rate, self.false_positive_rate)

    @property
    def precision(self) -> float:
        """``TP / (TP + FP)`` from the recorded counts."""
        return precision_from_counts(self.n_detected_attacks, self.n_false_positives)

    @property
    def f1(self) -> float:
        """Harmonic mean of :attr:`precision` and recall, from the counts."""
        return f1_from_counts(
            self.n_detected_attacks, self.n_false_positives, self.n_attacks
        )


@dataclass
class StabilityReport:
    """Report on multi-seed stability.

    Attributes:
        n_seeds: Number of seeds evaluated.
        overall_cv: Coefficient of variation for the attack-arm detection rate.
        per_architecture_cv: CV per architecture.
        per_category_cv: CV per attack category.
        cv_threshold: Threshold below which results are considered stable.
        stable: Whether all CVs (including the FPR CV) are below the threshold.
        seed_metrics: Full per-seed results.
        benign_arm_present: ``True`` only when every seed evaluated a
            non-empty benign corpus.  When ``False`` the false-positive and
            paired fields are ``None``, because reporting 0.0 for an arm that
            was never run is how an attack-only evaluation masquerades as a
            complete one.
        tpr_mean: Mean attack-arm TPR across seeds.
        fpr_mean: Mean benign-arm FPR across seeds (``None`` without the arm).
        fpr_cv: CV of the FPR across seeds (``None`` without the arm).
        precision_mean: Mean precision across seeds (``None`` without the arm).
        f1_mean: Mean F1 across seeds (``None`` without the arm).
        youden_j_mean: Mean Youden's J across seeds (``None`` without the arm).
        benign_fpr_by_difficulty_mean: Per-stratum mean FPR (empty without
            the arm).
        benign_fpr_by_category_mean: Per-category mean FPR (empty without
            the arm).
    """

    n_seeds: int
    overall_cv: float
    per_architecture_cv: Dict[str, float]
    per_category_cv: Dict[str, float]
    cv_threshold: float
    stable: bool
    seed_metrics: List[SeedMetrics]
    benign_arm_present: bool = False
    tpr_mean: float = 0.0
    fpr_mean: Optional[float] = None
    fpr_cv: Optional[float] = None
    precision_mean: Optional[float] = None
    f1_mean: Optional[float] = None
    youden_j_mean: Optional[float] = None
    benign_fpr_by_difficulty_mean: Dict[str, float] = field(default_factory=dict)
    benign_fpr_by_category_mean: Dict[str, float] = field(default_factory=dict)


def coefficient_of_variation(values: np.ndarray) -> float:
    """Compute the coefficient of variation (std / mean).

    Returns 0.0 when the mean is zero to avoid division by zero.
    """
    values = np.asarray(values, dtype=float)
    mean = np.mean(values)
    if mean == 0.0:
        return 0.0
    return float(np.std(values) / abs(mean))


def _mean_of_dicts(dicts: List[Dict[str, float]]) -> Dict[str, float]:
    """Mean each key across a list of dicts, over the entries that have it."""
    keys = sorted({k for d in dicts for k in d})
    out: Dict[str, float] = {}
    for key in keys:
        vals = [d[key] for d in dicts if key in d]
        out[key] = float(np.mean(vals)) if vals else 0.0
    return out


def run_multi_seed_stability(
    eval_fn: Callable[[int], SeedMetrics],
    seeds: Optional[List[int]] = None,
    cv_threshold: float = 0.05,
) -> StabilityReport:
    """Evaluate pipeline stability across multiple seeds.

    Parameters
    ----------
    eval_fn : callable
        ``(seed: int) -> SeedMetrics``.  Runs one full evaluation.
    seeds : list of int, optional
        Seeds to use.  Defaults to ``range(1, 31)``.
    cv_threshold : float
        CV below this is considered stable (default 5 %).

    Returns
    -------
    StabilityReport
        Paired operating-point fields are populated only when *every* seed
        reported a non-empty benign arm.
    """
    if seeds is None:
        seeds = list(range(1, 31))

    all_metrics: List[SeedMetrics] = []
    for seed in seeds:
        m = eval_fn(seed)
        all_metrics.append(m)

    # Overall CV
    overall_rates = np.array([m.overall_detection_rate for m in all_metrics])
    overall_cv = coefficient_of_variation(overall_rates)

    # Per-architecture CV
    arch_keys = sorted({k for m in all_metrics for k in m.per_architecture})
    per_arch_cv: Dict[str, float] = {}
    for key in arch_keys:
        vals = np.array([m.per_architecture.get(key, 0.0) for m in all_metrics])
        per_arch_cv[key] = coefficient_of_variation(vals)

    # Per-category CV
    cat_keys = sorted({k for m in all_metrics for k in m.per_category})
    per_cat_cv: Dict[str, float] = {}
    for key in cat_keys:
        vals = np.array([m.per_category.get(key, 0.0) for m in all_metrics])
        per_cat_cv[key] = coefficient_of_variation(vals)

    # Benign arm.  Fail closed: a single seed without a benign corpus
    # invalidates the aggregate, because the mean would silently average a
    # measurement with a default.
    benign_arm_present = bool(all_metrics) and all(m.has_benign_arm for m in all_metrics)

    tpr_mean = float(np.mean(overall_rates)) if all_metrics else 0.0
    fpr_mean: Optional[float] = None
    fpr_cv: Optional[float] = None
    precision_mean: Optional[float] = None
    f1_mean: Optional[float] = None
    j_mean: Optional[float] = None
    by_difficulty: Dict[str, float] = {}
    by_category: Dict[str, float] = {}

    if benign_arm_present:
        fprs = np.array([m.false_positive_rate for m in all_metrics])
        fpr_mean = float(np.mean(fprs))
        fpr_cv = coefficient_of_variation(fprs)
        precision_mean = float(np.mean([m.precision for m in all_metrics]))
        f1_mean = float(np.mean([m.f1 for m in all_metrics]))
        j_mean = float(np.mean([m.youden_j for m in all_metrics]))
        by_difficulty = _mean_of_dicts([m.benign_fpr_by_difficulty for m in all_metrics])
        by_category = _mean_of_dicts([m.benign_fpr_by_category for m in all_metrics])

    # Check stability.  The FPR CV joins the list when the arm exists: a
    # detector whose false-alarm rate swings across seeds is not stable, even
    # if its detection rate holds.
    all_cvs = [overall_cv] + list(per_arch_cv.values()) + list(per_cat_cv.values())
    if fpr_cv is not None:
        all_cvs.append(fpr_cv)
    stable = all(cv <= cv_threshold for cv in all_cvs)

    return StabilityReport(
        n_seeds=len(seeds),
        overall_cv=overall_cv,
        per_architecture_cv=per_arch_cv,
        per_category_cv=per_cat_cv,
        cv_threshold=cv_threshold,
        stable=stable,
        seed_metrics=all_metrics,
        benign_arm_present=benign_arm_present,
        tpr_mean=tpr_mean,
        fpr_mean=fpr_mean,
        fpr_cv=fpr_cv,
        precision_mean=precision_mean,
        f1_mean=f1_mean,
        youden_j_mean=j_mean,
        benign_fpr_by_difficulty_mean=by_difficulty,
        benign_fpr_by_category_mean=by_category,
    )


def make_pipeline_eval_fn(
    n_samples: int = 100,
    benign_per_stratum: int = 10,
) -> Callable[[int], SeedMetrics]:
    """Create a pipeline-based evaluation function for stability analysis.

    The returned function evaluates both arms for a given seed against the
    same freshly-built full pipeline:

    * attack arm — the first ``n_samples`` entries of
      ``AttackCorpus.generate(seed=seed)``.  This loop is unchanged from the
      attack-only version of this function, so the TPR it produces stays
      directly comparable to previously published multi-seed numbers.
    * benign arm — ``BenignCorpus.generate(seed=seed,
      n_per_stratum=benign_per_stratum)``, i.e. ``12 * benign_per_stratum``
      messages (120 at the default).  It is regenerated per seed so the FPR
      has its own across-seed variance rather than being a constant.

    Parameters
    ----------
    n_samples : int
        Number of attack samples to evaluate per seed.
    benign_per_stratum : int
        Benign samples per (category, difficulty) stratum.  Must be positive;
        there is deliberately no "no benign arm" setting, because that is the
        configuration this function exists to eliminate.

    Returns
    -------
    callable
        ``(seed: int) -> SeedMetrics`` suitable for ``run_multi_seed_stability``.

    Raises
    ------
    ValueError
        If ``benign_per_stratum`` is not positive.
    """
    if benign_per_stratum <= 0:
        raise ValueError(
            f"benign_per_stratum must be positive (the benign arm is mandatory), "
            f"got {benign_per_stratum}"
        )

    def eval_fn(seed: int) -> SeedMetrics:
        from attacks.corpus import AttackCorpus
        from composition.factory import create_full_pipeline
        from evaluation.benign_corpus import BenignCorpus
        from utils.random_seed import set_global_seed

        set_global_seed(seed)
        pipeline = create_full_pipeline()

        # --- attack arm ---
        corpus = AttackCorpus.generate(seed=seed)
        detected_count = 0
        total = 0
        cat_detected: Dict[str, int] = {}
        cat_total: Dict[str, int] = {}
        for sample in list(corpus)[:n_samples]:
            result = pipeline.evaluate(sample.payload)
            top = sample.category.top_category
            cat_total[top] = cat_total.get(top, 0) + 1
            if result.detected:
                detected_count += 1
                cat_detected[top] = cat_detected.get(top, 0) + 1
            total += 1

        overall = detected_count / total if total > 0 else 0.0
        per_category = {
            cat: cat_detected.get(cat, 0) / cat_total[cat] for cat in sorted(cat_total)
        }

        # --- benign arm ---
        benign = BenignCorpus.generate(seed=seed, n_per_stratum=benign_per_stratum)
        false_positives = 0
        diff_fp: Dict[str, int] = {}
        diff_n: Dict[str, int] = {}
        bcat_fp: Dict[str, int] = {}
        bcat_n: Dict[str, int] = {}
        for bsample in benign:
            bresult = pipeline.evaluate(bsample.text)
            diff_n[bsample.difficulty] = diff_n.get(bsample.difficulty, 0) + 1
            bcat_n[bsample.category] = bcat_n.get(bsample.category, 0) + 1
            if bresult.detected:
                false_positives += 1
                diff_fp[bsample.difficulty] = diff_fp.get(bsample.difficulty, 0) + 1
                bcat_fp[bsample.category] = bcat_fp.get(bsample.category, 0) + 1

        n_benign = len(benign)
        fpr = false_positives / n_benign if n_benign > 0 else 0.0

        return SeedMetrics(
            seed=seed,
            overall_detection_rate=overall,
            # The real CIF pipeline is architecture-agnostic and this
            # stability run evaluates one pipeline, not multiple adapters.
            # Do not relabel the overall series as an architecture result.
            per_architecture={},
            per_category=per_category,
            false_positive_rate=fpr,
            n_attacks=total,
            n_detected_attacks=detected_count,
            n_benign=n_benign,
            n_false_positives=false_positives,
            benign_fpr_by_difficulty={
                d: diff_fp.get(d, 0) / diff_n[d] for d in sorted(diff_n)
            },
            benign_fpr_by_category={
                c: bcat_fp.get(c, 0) / bcat_n[c] for c in sorted(bcat_n)
            },
        )

    return eval_fn
