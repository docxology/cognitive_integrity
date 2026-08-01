"""Baseline detectors, null models, and the honest comparator harness.

The CIF evaluation reports a detection rate for the *layered* pipeline and
draws an architectural conclusion from it.  A detection rate is only
interpretable against a comparator: 12% is excellent if chance is 1% and
embarrassing if a twenty-line regex gets 38%.  Before this module the
repository contained no comparator of any kind — the only "baseline" in the
manuscript was a no-defense column that is zero by construction and therefore
cannot fail to be beaten.

This module supplies the missing floors:

``RandomDetector``
    The chance-level null.  Flags uniformly at a caller-supplied rate with no
    reference to the payload, so its expected Youden's J is exactly zero.  Any
    detector that does not clear this is measuring nothing.
``KeywordDetector``
    A deliberately plain case-insensitive regex list over well-known
    prompt-injection phrases.  The pattern list is frozen in the module
    (:data:`DEFAULT_KEYWORD_PATTERNS`) and was written from public
    prompt-injection literature *before* it was ever run against this corpus;
    it is not tuned per corpus in either direction.  Tuning it down to flatter
    CIF would be as much an overclaim as fabricating CIF's own numbers.
``LengthDetector``
    A non-semantic floor: flag anything longer than a character threshold.
``BagOfWordsDetector``
    TF-IDF features plus L2-regularised logistic regression fitted with
    ``scipy.optimize`` (numpy/scipy only — sklearn is not a dependency).  It is
    a *trained* detector, so it must only ever be scored out of fold; see
    :func:`out_of_fold_output`.
``CIFPipelineDetector``
    The full eight-module CIF pipeline, wrapped in the same interface so it is
    measured by exactly the same code as every baseline.

All detectors implement :class:`Detector`: ``score(payload) -> float`` (higher
means more attack-like, used for ROC/PR) and ``detect(payload) -> bool`` (the
deployed verdict, used for the operating-point metrics).  For CIF these are
*not* redundant: the series pipeline's verdict is the disjunction of the
module verdicts, which does not coincide exactly with thresholding the fused
score.  :attr:`DetectorMetrics.verdict_score_disagreements` records how often
they disagree so the discrepancy is visible rather than assumed away.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics.confidence import wilson_ci
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence, runtime_checkable

import numpy as np
from scipy.optimize import minimize

from attacks.corpus import AttackCorpus, AttackSample
from evaluation.precision_recall import bootstrap_ap_ci, compute_pr_curve
from evaluation.roc import ROCCurve, compute_roc, youdens_j

#: Filename of the artifact produced by ``scripts/run_baseline_comparison.py``.
COMPARISON_ARTIFACT_NAME = "baseline_comparison.json"

#: Canonical data directory (``<project>/output/data``), matching the
#: convention in :mod:`data.result_loaders`.
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "data"

__all__ = [
    "COMPARISON_ARTIFACT_NAME",
    "DEFAULT_DATA_DIR",
    "DEFAULT_KEYWORD_PATTERNS",
    "BagOfWordsDetector",
    "CIFPipelineDetector",
    "ComparisonRow",
    "CurveSummary",
    "Detector",
    "DetectorMetrics",
    "DetectorOutput",
    "KeywordDetector",
    "LabelledCorpus",
    "LengthDetector",
    "NullResult",
    "RandomDetector",
    "TrainableDetector",
    "auc_in_order",
    "build_evaluation_corpus",
    "compare_detectors",
    "curve_summary",
    "evaluate_detector",
    "evaluate_output",
    "load_comparison_artifact",
    "out_of_fold_output",
    "permutation_null",
    "permutation_null_from_output",
    "run_detector",
    "stratified_attack_sample",
    "stratified_folds",
]


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class Detector(Protocol):
    """Anything that can score and flag a single payload.

    ``score`` must be monotone in "attack-likeness" and live in ``[0, 1]``;
    ``detect`` is the deployed boolean verdict at the detector's own operating
    point, which need not be ``score >= 0.5``.
    """

    @property
    def name(self) -> str:
        """Stable identifier used as the key in comparison tables."""
        ...

    def score(self, payload: str) -> float:
        """Continuous attack-likeness score in ``[0, 1]``."""
        ...

    def detect(self, payload: str) -> bool:
        """Deployed boolean verdict for *payload*."""
        ...


@runtime_checkable
class TrainableDetector(Detector, Protocol):
    """A :class:`Detector` that must be fitted on labelled data first."""

    def fit(self, payloads: Sequence[str], labels: Sequence[bool]) -> None:
        """Fit the detector on *payloads* / *labels* (True = attack)."""
        ...


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


#: The 50 benign control messages used for false-positive measurement.
#:
#: Imported from the ablation runner rather than re-typed so the baseline
#: comparison and the published ablation share one negative set by
#: construction; a divergence here would silently make the comparison
#: apples-to-oranges.
def _benign_messages() -> list[str]:
    from ablation.runner import BENIGN_MESSAGES

    return list(BENIGN_MESSAGES)


@dataclass(frozen=True)
class LabelledCorpus:
    """A payload set with binary labels and stratification groups.

    Attributes:
        payloads: The message texts, attacks first then benign controls.
        labels: ``True`` for attack, ``False`` for benign.
        groups: Attack subcategory for attacks, ``"benign"`` for controls.
        top_categories: Top-level attack family, ``"benign"`` for controls.
        seed: Seed that produced the stratified attack sample.
    """

    payloads: tuple[str, ...]
    labels: tuple[bool, ...]
    groups: tuple[str, ...]
    top_categories: tuple[str, ...]
    seed: int

    def __post_init__(self) -> None:
        n = len(self.payloads)
        if not (len(self.labels) == len(self.groups) == len(self.top_categories) == n):
            raise ValueError(
                "LabelledCorpus fields must be the same length: "
                f"payloads={n}, labels={len(self.labels)}, "
                f"groups={len(self.groups)}, top_categories={len(self.top_categories)}"
            )
        if n == 0:
            raise ValueError("LabelledCorpus must not be empty")

    def __len__(self) -> int:
        return len(self.payloads)

    @property
    def label_array(self) -> np.ndarray:
        """Labels as a boolean ndarray."""
        return np.asarray(self.labels, dtype=bool)

    @property
    def n_positive(self) -> int:
        """Number of attack payloads."""
        return int(self.label_array.sum())

    @property
    def n_negative(self) -> int:
        """Number of benign payloads."""
        return len(self) - self.n_positive


def stratified_attack_sample(seed: int = 42, target_n: int = 100) -> list[AttackSample]:
    """Draw the canonical stratified attack sample used by the published study.

    This reproduces, step for step, the sampling inside
    ``ablation.runner.evaluate_component_subset`` — same corpus seed, same
    per-subcategory proportional allocation, same ``numpy`` generator draw
    order.  It is duplicated here rather than imported because the ablation
    helper returns only aggregate rates and never exposes the sample; the
    duplication is pinned by a test that asserts the CIF detector's TPR on
    this corpus equals the ablation runner's full-pipeline TPR exactly.

    Note that proportional rounding over the twelve subcategories yields 98
    samples, not the ``target_n`` of 100.

    Args:
        seed: Corpus-generation and sampling seed.
        target_n: Nominal sample size before per-stratum rounding.

    Returns:
        The selected attack samples, grouped by subcategory in corpus order.
    """
    corpus = AttackCorpus.generate(seed=seed)
    samples = list(corpus)
    by_subcategory: dict[str, list[AttackSample]] = defaultdict(list)
    for sample in samples:
        by_subcategory[sample.subcategory].append(sample)

    selected: list[AttackSample] = []
    total = len(samples)
    rng = np.random.default_rng(seed)
    for _subcat, group in by_subcategory.items():
        n_pick = max(1, round(len(group) / total * target_n))
        idx = rng.choice(len(group), size=min(n_pick, len(group)), replace=False)
        selected.extend(group[i] for i in idx)
    return selected


def build_evaluation_corpus(seed: int = 42, target_n: int = 100) -> LabelledCorpus:
    """Build the labelled corpus every detector in the comparison is scored on.

    Args:
        seed: Corpus and sampling seed.
        target_n: Nominal stratified sample size (see
            :func:`stratified_attack_sample`).

    Returns:
        A :class:`LabelledCorpus` of stratified attacks followed by the 50
        benign control messages.
    """
    attacks = stratified_attack_sample(seed=seed, target_n=target_n)
    benign = _benign_messages()

    payloads = [a.payload for a in attacks] + list(benign)
    labels = [True] * len(attacks) + [False] * len(benign)
    groups = [a.subcategory for a in attacks] + ["benign"] * len(benign)
    tops = [a.category.top_category for a in attacks] + ["benign"] * len(benign)

    return LabelledCorpus(
        payloads=tuple(payloads),
        labels=tuple(labels),
        groups=tuple(groups),
        top_categories=tuple(tops),
        seed=seed,
    )


def stratified_folds(
    corpus: LabelledCorpus,
    n_folds: int = 5,
    seed: int = 42,
) -> list[np.ndarray]:
    """Partition corpus indices into *n_folds* group-stratified folds.

    Stratification is on :attr:`LabelledCorpus.groups`, so each fold carries
    roughly the same subcategory mix (and the same attack/benign balance).

    Args:
        corpus: The corpus to partition.
        n_folds: Number of folds; must be at least 2.
        seed: Shuffle seed.

    Returns:
        A list of index arrays whose concatenation is a permutation of
        ``range(len(corpus))``.

    Raises:
        ValueError: If *n_folds* < 2 or exceeds the corpus size.
    """
    if n_folds < 2:
        raise ValueError(f"n_folds must be >= 2, got {n_folds}")
    if n_folds > len(corpus):
        raise ValueError(f"n_folds ({n_folds}) exceeds corpus size ({len(corpus)})")

    rng = np.random.default_rng(seed)
    buckets: list[list[int]] = [[] for _ in range(n_folds)]
    by_group: dict[str, list[int]] = defaultdict(list)
    for i, group in enumerate(corpus.groups):
        by_group[group].append(i)

    # sorted() so fold assignment never depends on dict insertion order or on
    # PYTHONHASHSEED — the folds must be byte-reproducible across processes.
    for group in sorted(by_group):
        members = np.array(by_group[group], dtype=np.int64)
        order = rng.permutation(len(members))
        for position, member_idx in enumerate(order):
            buckets[position % n_folds].append(int(members[member_idx]))

    return [np.array(sorted(b), dtype=np.int64) for b in buckets]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DetectorMetrics:
    """Operating-point metrics for one detector on one corpus.

    Attributes:
        name: Detector identifier.
        tp / fp / tn / fn: Confusion-matrix counts.
        tpr: True positive rate (recall / sensitivity).
        fpr: False positive rate.
        precision: Positive predictive value (1.0 when nothing is flagged).
        f1: Harmonic mean of precision and recall.
        youden_j: ``tpr - fpr``; 0 for a label-blind detector.
        balanced_accuracy: ``(tpr + tnr) / 2``.
        mcc: Matthews correlation coefficient.
        tpr_ci95 / fpr_ci95: Wilson score intervals for the two rates.
        verdict_score_disagreements: Payloads where ``detect(p)`` differs from
            ``score(p) >= 0.5``.  Non-zero means the ROC operating point at
            0.5 is not the deployed operating point.
    """

    name: str
    tp: int
    fp: int
    tn: int
    fn: int
    tpr: float
    fpr: float
    precision: float
    f1: float
    youden_j: float
    balanced_accuracy: float
    mcc: float
    tpr_ci95: tuple[float, float]
    fpr_ci95: tuple[float, float]
    verdict_score_disagreements: int

    @property
    def n_positive(self) -> int:
        """Number of positive (attack) payloads."""
        return self.tp + self.fn

    @property
    def n_negative(self) -> int:
        """Number of negative (benign) payloads."""
        return self.tn + self.fp

    @property
    def flag_rate(self) -> float:
        """Fraction of all payloads flagged."""
        total = self.n_positive + self.n_negative
        return (self.tp + self.fp) / total if total else 0.0

    def to_dict(self) -> dict[str, object]:
        """JSON-safe dict of every field plus the derived properties."""
        return {
            "name": self.name,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "n_positive": self.n_positive,
            "n_negative": self.n_negative,
            "tpr": self.tpr,
            "fpr": self.fpr,
            "precision": self.precision,
            "f1": self.f1,
            "youden_j": self.youden_j,
            "balanced_accuracy": self.balanced_accuracy,
            "mcc": self.mcc,
            "flag_rate": self.flag_rate,
            "tpr_ci95": list(self.tpr_ci95),
            "fpr_ci95": list(self.fpr_ci95),
            "verdict_score_disagreements": self.verdict_score_disagreements,
        }


@dataclass(frozen=True)
class DetectorOutput:
    """Raw per-payload output of a detector, aligned with the corpus order.

    Attributes:
        name: Detector identifier.
        scores: Continuous scores, one per payload.
        detections: Boolean verdicts, one per payload.
    """

    name: str
    scores: np.ndarray
    detections: np.ndarray

    def __post_init__(self) -> None:
        if len(self.scores) != len(self.detections):
            raise ValueError(
                f"scores ({len(self.scores)}) and detections "
                f"({len(self.detections)}) must be the same length"
            )


@dataclass(frozen=True)
class NullResult:
    """Label-permutation null distribution for a detector's Youden J.

    Attributes:
        observed_j: J on the true labels.
        null_mean_j: Mean J over label permutations.
        null_sd_j: Standard deviation of J over label permutations.
        p_value: Fraction of permutations with J >= observed (add-one
            corrected, so it is never exactly zero).
        n_permutations: Number of permutations drawn.
    """

    observed_j: float
    null_mean_j: float
    null_sd_j: float
    p_value: float
    n_permutations: int

    def to_dict(self) -> dict[str, float | int]:
        """JSON-safe dict."""
        return {
            "observed_j": self.observed_j,
            "null_mean_j": self.null_mean_j,
            "null_sd_j": self.null_sd_j,
            "p_value": self.p_value,
            "n_permutations": self.n_permutations,
        }


def _wilson(successes: int, total: int) -> tuple[float, float]:
    """Wilson 95% interval, degenerate ``(0, 0)`` for an empty denominator."""
    if total < 1:
        return (0.0, 0.0)
    _, lo, hi = wilson_ci(successes, total, confidence=0.95)
    return (float(lo), float(hi))


def evaluate_output(output: DetectorOutput, corpus: LabelledCorpus) -> DetectorMetrics:
    """Compute operating-point metrics from precomputed detector output.

    Args:
        output: Scores and verdicts aligned with *corpus*.
        corpus: The labelled corpus.

    Returns:
        The :class:`DetectorMetrics` for this detector/corpus pair.

    Raises:
        ValueError: If *output* is not aligned with *corpus*.
    """
    if len(output.scores) != len(corpus):
        raise ValueError(
            f"detector output length {len(output.scores)} != corpus size {len(corpus)}"
        )

    y = corpus.label_array
    pred = np.asarray(output.detections, dtype=bool)

    tp = int(np.sum(pred & y))
    fp = int(np.sum(pred & ~y))
    tn = int(np.sum(~pred & ~y))
    fn = int(np.sum(~pred & y))

    n_pos = tp + fn
    n_neg = tn + fp
    tpr = tp / n_pos if n_pos else 0.0
    fpr = fp / n_neg if n_neg else 0.0
    tnr = tn / n_neg if n_neg else 0.0
    # Precision is undefined with nothing flagged; 1.0 is the conventional
    # convention here and is never flattering — a detector that flags nothing
    # already scores tpr = 0, f1 = 0, J = 0.
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    f1 = (2 * precision * tpr / (precision + tpr)) if (precision + tpr) > 0 else 0.0

    mcc_den = float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / np.sqrt(mcc_den)) if mcc_den > 0 else 0.0

    disagreements = int(np.sum(pred != (np.asarray(output.scores, dtype=float) >= 0.5)))

    return DetectorMetrics(
        name=output.name,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        tpr=float(tpr),
        fpr=float(fpr),
        precision=float(precision),
        f1=float(f1),
        youden_j=float(tpr - fpr),
        balanced_accuracy=float((tpr + tnr) / 2.0),
        mcc=float(mcc),
        tpr_ci95=_wilson(tp, n_pos),
        fpr_ci95=_wilson(fp, n_neg),
        verdict_score_disagreements=disagreements,
    )


def run_detector(detector: Detector, corpus: LabelledCorpus) -> DetectorOutput:
    """Score and flag every payload in *corpus* with *detector*."""
    scores = np.empty(len(corpus), dtype=np.float64)
    detections = np.empty(len(corpus), dtype=bool)
    for i, payload in enumerate(corpus.payloads):
        scores[i] = float(detector.score(payload))
        detections[i] = bool(detector.detect(payload))
    return DetectorOutput(name=detector.name, scores=scores, detections=detections)


def evaluate_detector(detector: Detector, corpus: LabelledCorpus) -> DetectorMetrics:
    """Run *detector* over *corpus* and return its operating-point metrics."""
    return evaluate_output(run_detector(detector, corpus), corpus)


def permutation_null(
    detector: Detector,
    corpus: LabelledCorpus,
    n_permutations: int = 10_000,
    seed: int = 42,
) -> NullResult:
    """Label-permutation test for a detector's Youden J.

    Args:
        detector: The detector to test.
        corpus: The labelled corpus.
        n_permutations: Number of label shuffles.
        seed: Shuffle seed.

    Returns:
        A :class:`NullResult`; see :func:`permutation_null_from_output`.
    """
    return permutation_null_from_output(
        run_detector(detector, corpus), corpus, n_permutations=n_permutations, seed=seed
    )


def permutation_null_from_output(
    output: DetectorOutput,
    corpus: LabelledCorpus,
    n_permutations: int = 10_000,
    seed: int = 42,
) -> NullResult:
    """Label-permutation test on already-computed verdicts.

    The verdicts are held fixed while the labels are shuffled, which is the
    correct null: it destroys any association between payload and label while
    preserving both the flag rate and the class balance.  Taking verdicts as
    input (rather than a detector) is what lets an out-of-fold trained model be
    tested by the same procedure as a fixed rule.

    Args:
        output: Verdicts aligned with *corpus*.
        corpus: The labelled corpus.
        n_permutations: Number of label shuffles.
        seed: Shuffle seed.

    Returns:
        A :class:`NullResult`.  The p-value is add-one corrected —
        ``(1 + #{J_perm >= J_obs}) / (1 + n_permutations)`` — so it is bounded
        below by ``1/(1+n)`` and never reported as an impossible exact zero.

    Raises:
        ValueError: If *n_permutations* < 1, the output is misaligned, or a
            class is absent.
    """
    if n_permutations < 1:
        raise ValueError(f"n_permutations must be >= 1, got {n_permutations}")
    if len(output.detections) != len(corpus):
        raise ValueError(
            f"detector output length {len(output.detections)} != corpus size {len(corpus)}"
        )

    pred = np.asarray(output.detections, dtype=bool)
    y = corpus.label_array
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("permutation_null requires both classes to be present")

    observed_j = float(
        np.sum(pred & y) / n_pos - np.sum(pred & ~y) / n_neg
    )

    rng = np.random.default_rng(seed)
    null_js = np.empty(n_permutations, dtype=np.float64)
    for i in range(n_permutations):
        shuffled = rng.permutation(y)
        null_js[i] = np.sum(pred & shuffled) / n_pos - np.sum(pred & ~shuffled) / n_neg

    at_least = int(np.sum(null_js >= observed_j))
    p_value = (1.0 + at_least) / (1.0 + n_permutations)

    return NullResult(
        observed_j=observed_j,
        null_mean_j=float(np.mean(null_js)),
        null_sd_j=float(np.std(null_js, ddof=1)) if n_permutations > 1 else 0.0,
        p_value=float(p_value),
        n_permutations=n_permutations,
    )


# ---------------------------------------------------------------------------
# Baseline detectors
# ---------------------------------------------------------------------------


def _uniform_from_payload(payload: str, seed: int) -> float:
    """Deterministic uniform ``[0, 1)`` draw keyed on ``(seed, payload)``.

    Uses SHA-256 rather than :func:`hash` so the draw is identical across
    processes; ``hash`` on ``str`` is salted by ``PYTHONHASHSEED`` and would
    make the null model irreproducible.
    """
    digest = hashlib.sha256(f"{seed}\x00{payload}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


@dataclass
class RandomDetector:
    """Chance-level null: flags at a fixed rate, blind to the payload.

    The score is a deterministic pseudo-random uniform keyed on the payload
    text, so the detector is reproducible and idempotent while carrying zero
    information about the label.  Its expected Youden J is exactly 0 and its
    expected AUC exactly 0.5 — this is the floor every reported detection rate
    must clear before it means anything.

    Args:
        flag_rate: Target fraction of payloads to flag.
        seed: Stream seed.
        name: Identifier used in comparison tables.
    """

    flag_rate: float
    seed: int = 42
    name: str = "random_null"

    def __post_init__(self) -> None:
        if not 0.0 <= self.flag_rate <= 1.0:
            raise ValueError(f"flag_rate must be in [0, 1], got {self.flag_rate}")

    def score(self, payload: str) -> float:
        """Payload-independent pseudo-random score in ``[0, 1)``."""
        return _uniform_from_payload(payload, self.seed)

    def detect(self, payload: str) -> bool:
        """Flag when the pseudo-random score falls in the top *flag_rate*."""
        return self.score(payload) >= 1.0 - self.flag_rate


#: Frozen prompt-injection phrase list for :class:`KeywordDetector`.
#:
#: Written from published prompt-injection patterns (the "ignore previous
#: instructions" family, DAN/developer-mode jailbreaks, privilege-escalation
#: and filter-disabling phrasings) before being run against this corpus, and
#: deliberately not revised afterwards.  Editing this list in response to a
#: measured result — in either direction — would turn the comparator into an
#: authored artifact and destroy its value as a floor.
DEFAULT_KEYWORD_PATTERNS: tuple[str, ...] = (
    r"ignore\s+(?:all\s+|the\s+|any\s+)?(?:previous|prior|above|earlier)\s+"
    r"(?:instruction|direction|prompt|rule|message)",
    r"disregard\s+(?:all\s+|the\s+|your\s+|any\s+)?"
    r"(?:previous|prior|above|earlier|system|safety)",
    r"system\s+prompt",
    r"jailbreak",
    r"developer\s+mode",
    r"debug\s+mode",
    r"\bDAN\b",
    r"do\s+anything\s+now",
    r"bypass\s+(?:the\s+|all\s+|any\s+|your\s+)?"
    r"(?:safety|security|filter|restriction|authentication|guardrail|check)",
    r"(?:disable|turn\s+off|remove|override)\s+(?:all\s+|the\s+|your\s+)?"
    r"(?:safety|security|filter|restriction|guardrail|directive|mechanism)",
    r"no\s+(?:restrictions|limitations|filters|safety|guardrails|exceptions)",
    r"without\s+(?:any\s+)?(?:restrictions|limitations|filters|safety|censorship)",
    r"unrestricted",
    r"\bsudo\b",
    r"root\s+access",
    r"\bpretend\b",
    r"role[-\s]?play",
    r"act\s+as\s+(?:a\s+|an\s+|the\s+)?"
    r"(?:unrestricted|admin|root|system|developer|superuser)",
    r"reveal\s+(?:your\s+|the\s+)?(?:system\s+prompt|instructions|hidden|real)",
    r"admin(?:istrator)?\s+(?:command|mode|override|access|privileges)",
    r"elevated\s+privileges",
    r"execute\s+arbitrary",
    r"exfiltrate",
    r"safety\s+(?:mechanisms?|guidelines?|rules?)",
)


class KeywordDetector:
    """Case-insensitive regex baseline over known injection phrasings.

    The lexical floor.  Its ``score`` is ``1 - 2**-k`` for ``k`` matched
    patterns, which is 0 for no match and >= 0.5 for any match, so
    ``detect`` and ``score >= 0.5`` agree by construction.

    Args:
        patterns: Regex list; defaults to :data:`DEFAULT_KEYWORD_PATTERNS`.
        name: Identifier used in comparison tables.
    """

    def __init__(
        self,
        patterns: Sequence[str] | None = None,
        name: str = "keyword_regex",
    ) -> None:
        self.patterns: tuple[str, ...] = tuple(
            DEFAULT_KEYWORD_PATTERNS if patterns is None else patterns
        )
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        self._name = name

    @property
    def name(self) -> str:
        """Detector identifier."""
        return self._name

    def match_count(self, payload: str) -> int:
        """Number of distinct patterns that fire on *payload*."""
        return sum(1 for rx in self._compiled if rx.search(payload) is not None)

    def score(self, payload: str) -> float:
        """``1 - 2**-k`` for ``k`` matching patterns (0.0 when none match)."""
        k = self.match_count(payload)
        return 0.0 if k == 0 else float(1.0 - 2.0**-k)

    def detect(self, payload: str) -> bool:
        """Flag when at least one pattern matches."""
        return self.match_count(payload) > 0


@dataclass
class LengthDetector:
    """Non-semantic floor: flag anything longer than *threshold_chars*.

    Included because a corpus whose attacks are systematically longer than its
    benign controls can be "detected" with no understanding at all.  If this
    detector scores well, the corpus has a length confound.

    Args:
        threshold_chars: Flag payloads at least this long.
        scale_chars: Character count that maps to a score of ~0.63; the score
            is ``1 - exp(-len / scale_chars)``.
        name: Identifier used in comparison tables.
    """

    threshold_chars: int = 120
    scale_chars: float = 200.0
    name: str = "length_only"

    def __post_init__(self) -> None:
        if self.threshold_chars < 0:
            raise ValueError("threshold_chars must be non-negative")
        if self.scale_chars <= 0:
            raise ValueError("scale_chars must be positive")

    def score(self, payload: str) -> float:
        """Saturating function of payload length in ``[0, 1)``."""
        return float(1.0 - np.exp(-len(payload) / self.scale_chars))

    def detect(self, payload: str) -> bool:
        """Flag payloads at least *threshold_chars* long."""
        return len(payload) >= self.threshold_chars


_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokenize(payload: str) -> list[str]:
    """Lowercase word/number tokens."""
    return _TOKEN_RE.findall(payload.lower())


class BagOfWordsDetector:
    """TF-IDF + L2-regularised logistic regression, numpy/scipy only.

    A trained comparator: if a linear bag-of-words model on a few dozen
    examples matches or beats an eight-module semantic pipeline, the pipeline
    is not buying what the manuscript says it buys.  Because it is trained it
    must never be scored on its own training rows — use
    :func:`out_of_fold_output`.

    Optimisation is L-BFGS-B on the exact penalised negative log-likelihood
    with an analytic gradient and a zero initialisation, so the fit is fully
    deterministic and needs no learning-rate tuning.

    Args:
        l2: Ridge penalty on the weights (the intercept is unpenalised).
        threshold: Probability at or above which the payload is flagged.
        max_iter: L-BFGS-B iteration cap.
        name: Identifier used in comparison tables.
    """

    def __init__(
        self,
        l2: float = 1e-3,
        threshold: float = 0.5,
        max_iter: int = 1000,
        name: str = "bag_of_words_lr",
    ) -> None:
        if l2 < 0:
            raise ValueError("l2 must be non-negative")
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be in (0, 1)")
        self.l2 = l2
        self.threshold = threshold
        self.max_iter = max_iter
        self._name = name
        self._vocab: dict[str, int] = {}
        self._idf: np.ndarray = np.zeros(0, dtype=np.float64)
        self._weights: np.ndarray = np.zeros(0, dtype=np.float64)
        self._intercept: float = 0.0
        self._fitted = False
        self.converged: bool = False
        self.train_loss: float = float("nan")

    @property
    def name(self) -> str:
        """Detector identifier."""
        return self._name

    @property
    def fitted(self) -> bool:
        """Whether :meth:`fit` has been called."""
        return self._fitted

    @property
    def vocabulary_size(self) -> int:
        """Number of TF-IDF features learned from the training split."""
        return len(self._vocab)

    def _vectorize(self, payload: str) -> np.ndarray:
        counts = np.zeros(len(self._vocab), dtype=np.float64)
        for token in _tokenize(payload):
            j = self._vocab.get(token)
            if j is not None:
                counts[j] += 1.0
        vec = counts * self._idf
        norm = float(np.linalg.norm(vec))
        return vec / norm if norm > 0 else vec

    def fit(self, payloads: Sequence[str], labels: Sequence[bool]) -> None:
        """Fit vocabulary, IDF weights, and the logistic model.

        Args:
            payloads: Training payloads.
            labels: Training labels (``True`` = attack).

        Raises:
            ValueError: If the inputs disagree in length, are empty, or
                contain only one class (a single-class fit cannot produce a
                meaningful decision boundary and would silently degrade the
                comparator).
        """
        if len(payloads) != len(labels):
            raise ValueError("payloads and labels must be the same length")
        if len(payloads) == 0:
            raise ValueError("cannot fit on an empty training set")
        y = np.asarray(labels, dtype=np.float64)
        if y.sum() == 0 or y.sum() == len(y):
            raise ValueError("training split must contain both classes")

        tokenized = [_tokenize(p) for p in payloads]
        vocab_terms = sorted({t for doc in tokenized for t in doc})
        self._vocab = {term: i for i, term in enumerate(vocab_terms)}

        n_docs = len(tokenized)
        df = np.zeros(len(self._vocab), dtype=np.float64)
        for doc in tokenized:
            for term in set(doc):
                df[self._vocab[term]] += 1.0
        self._idf = np.log((1.0 + n_docs) / (1.0 + df)) + 1.0

        matrix = np.stack([self._vectorize(p) for p in payloads])
        n_features = matrix.shape[1]

        def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
            w = theta[:n_features]
            b = theta[n_features]
            z = matrix @ w + b
            # log(1 + exp(z)) computed stably.
            log1pexp = np.logaddexp(0.0, z)
            loss = float(np.sum(log1pexp - y * z) + 0.5 * self.l2 * float(w @ w))
            p = 1.0 / (1.0 + np.exp(-z))
            resid = p - y
            grad_w = matrix.T @ resid + self.l2 * w
            grad_b = float(np.sum(resid))
            return loss, np.concatenate([grad_w, [grad_b]])

        theta0 = np.zeros(n_features + 1, dtype=np.float64)
        result = minimize(
            objective,
            theta0,
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": self.max_iter},
        )
        self._weights = np.asarray(result.x[:n_features], dtype=np.float64)
        self._intercept = float(result.x[n_features])
        self.converged = bool(result.success)
        self.train_loss = float(result.fun)
        self._fitted = True

    def score(self, payload: str) -> float:
        """Predicted attack probability.

        Raises:
            RuntimeError: If the detector has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError("BagOfWordsDetector.score called before fit()")
        z = float(self._vectorize(payload) @ self._weights + self._intercept)
        return float(1.0 / (1.0 + np.exp(-z)))

    def detect(self, payload: str) -> bool:
        """Flag when the predicted probability reaches *threshold*."""
        return self.score(payload) >= self.threshold


class CIFPipelineDetector:
    """The full CIF defense pipeline behind the :class:`Detector` interface.

    ``detect`` returns the pipeline's own verdict — the quantity the
    manuscript reports as the detection rate — and ``score`` returns the
    pipeline's aggregated confidence, used for ROC/PR.  A one-entry memo means
    scoring and flagging the same payload costs one pipeline evaluation.

    Args:
        mode: ``"series"`` (the published configuration) or ``"parallel"``.
        name: Identifier used in comparison tables.
    """

    def __init__(self, mode: str = "series", name: str = "cif_full_pipeline") -> None:
        from composition.factory import create_full_pipeline

        self.mode = mode
        self._pipeline = create_full_pipeline(mode)
        self._name = name
        self._memo_payload: str | None = None
        self._memo_result: object | None = None

    @property
    def name(self) -> str:
        """Detector identifier."""
        return self._name

    def _evaluate(self, payload: str):  # type: ignore[no-untyped-def]
        if payload != self._memo_payload or self._memo_result is None:
            self._memo_result = self._pipeline.evaluate(payload)
            self._memo_payload = payload
        return self._memo_result

    def score(self, payload: str) -> float:
        """The pipeline's aggregated confidence score."""
        return float(self._evaluate(payload).score)

    def detect(self, payload: str) -> bool:
        """The pipeline's own detection verdict."""
        return bool(self._evaluate(payload).detected)


# ---------------------------------------------------------------------------
# Out-of-fold scoring and the comparison table
# ---------------------------------------------------------------------------


def out_of_fold_output(
    factory: Callable[[], TrainableDetector],
    corpus: LabelledCorpus,
    n_folds: int = 5,
    seed: int = 42,
    name: str | None = None,
) -> DetectorOutput:
    """Cross-validated out-of-fold scores for a *trained* detector.

    Every payload is scored by a model that never saw it, so the trained
    comparator is measured on exactly the same rows as the untrained ones with
    no leakage and no shrinking of the evaluation set.

    Args:
        factory: Zero-argument callable returning a fresh unfitted detector.
        corpus: The labelled corpus.
        n_folds: Number of stratified folds.
        seed: Fold-assignment seed.
        name: Override for the output name; defaults to the detector's own.

    Returns:
        A :class:`DetectorOutput` whose entries are all out-of-fold.

    Raises:
        ValueError: If any fold's training split is single-class, which would
            make the fold's predictions meaningless.
    """
    folds = stratified_folds(corpus, n_folds=n_folds, seed=seed)
    scores = np.full(len(corpus), np.nan, dtype=np.float64)
    detections = np.zeros(len(corpus), dtype=bool)
    payloads = corpus.payloads
    labels = corpus.label_array
    detector_name = name

    for fold_idx in folds:
        mask = np.ones(len(corpus), dtype=bool)
        mask[fold_idx] = False
        train_payloads = [payloads[i] for i in np.flatnonzero(mask)]
        train_labels = labels[mask]
        if train_labels.sum() == 0 or train_labels.sum() == len(train_labels):
            raise ValueError("a fold's training split is single-class; reduce n_folds")

        detector = factory()
        detector.fit(train_payloads, [bool(v) for v in train_labels])
        if detector_name is None:
            detector_name = detector.name
        for i in fold_idx:
            scores[i] = float(detector.score(payloads[i]))
            detections[i] = bool(detector.detect(payloads[i]))

    if np.isnan(scores).any():
        raise ValueError("out-of-fold scoring left unscored rows; folds are not a partition")

    return DetectorOutput(
        name=detector_name or "trained_detector",
        scores=scores,
        detections=detections,
    )


# ---------------------------------------------------------------------------
# Threshold-swept curves with measured bootstrap confidence intervals
# ---------------------------------------------------------------------------


def auc_in_order(fpr: np.ndarray, tpr: np.ndarray) -> float:
    """Trapezoidal AUC over ROC points that are *already* in sweep order.

    ``evaluation.roc.compute_auc_from_points`` re-sorts its inputs with
    ``np.argsort(fpr)``, whose default quicksort is not stable.  When many
    thresholds share one FPR — which is what every tied-score detector
    produces, including the keyword baseline — the tie order is scrambled and
    the trapezoid is taken against an arbitrary y-value.  Measured on this
    corpus the keyword baseline's AUC came out as 0.5561 that way versus
    0.6837 for the same points integrated in order.  Since the AUC of a
    *baseline* is exactly the number a crippled comparator would understate,
    this module integrates the arrays ``compute_roc`` already returns in
    ascending-FPR order and never re-sorts them.

    Args:
        fpr: False-positive rates in ascending sweep order.
        tpr: True-positive rates in the matching order.

    Returns:
        Area under the curve, clipped to ``[0, 1]``.

    Raises:
        ValueError: If the arrays differ in length or *fpr* is not
            non-decreasing (which would mean the caller's points are not in
            sweep order and this shortcut does not apply).
    """
    fpr_arr = np.asarray(fpr, dtype=np.float64)
    tpr_arr = np.asarray(tpr, dtype=np.float64)
    if fpr_arr.shape != tpr_arr.shape:
        raise ValueError("fpr and tpr must have the same shape")
    if fpr_arr.size and np.any(np.diff(fpr_arr) < -1e-12):
        raise ValueError("fpr must be non-decreasing; points are not in sweep order")
    trapezoid = getattr(np, "trapezoid", None) or np.trapz  # type: ignore[attr-defined]
    return float(np.clip(trapezoid(tpr_arr, fpr_arr), 0.0, 1.0))


@dataclass(frozen=True)
class CurveSummary:
    """Measured ROC and PR curves for one detector, with bootstrap CIs.

    Every field is computed from real per-payload scores.  ``n_bootstrap_used``
    is the number of resamples that actually contributed (single-class
    resamples are discarded), so a caption quoting the resample count can be
    bound to a measured quantity instead of an assumed one.
    """

    name: str
    fpr: np.ndarray
    tpr: np.ndarray
    roc_thresholds: np.ndarray
    auc: float
    auc_ci95: tuple[float, float]
    band_fpr: np.ndarray
    band_tpr_lo: np.ndarray
    band_tpr_hi: np.ndarray
    precision: np.ndarray
    recall: np.ndarray
    average_precision: float
    ap_ci95: tuple[float, float]
    band_recall: np.ndarray
    band_precision_lo: np.ndarray
    band_precision_hi: np.ndarray
    youden_threshold: float
    youden_j: float
    n_thresholds: int
    n_bootstrap_requested: int
    n_bootstrap_used: int
    n_positive: int
    n_negative: int

    @property
    def auc_ci_halfwidth(self) -> float:
        """Half-width of the AUC confidence interval."""
        return (self.auc_ci95[1] - self.auc_ci95[0]) / 2.0

    def to_dict(self, decimals: int = 6) -> dict[str, object]:
        """JSON-safe dict; arrays are rounded to *decimals* places."""

        def _round(a: np.ndarray) -> list[float]:
            return [round(float(v), decimals) for v in a]

        return {
            "name": self.name,
            "fpr": _round(self.fpr),
            "tpr": _round(self.tpr),
            "roc_thresholds": _round(self.roc_thresholds),
            "auc": round(self.auc, decimals),
            "auc_ci95": [round(v, decimals) for v in self.auc_ci95],
            "band_fpr": _round(self.band_fpr),
            "band_tpr_lo": _round(self.band_tpr_lo),
            "band_tpr_hi": _round(self.band_tpr_hi),
            "precision": _round(self.precision),
            "recall": _round(self.recall),
            "average_precision": round(self.average_precision, decimals),
            "ap_ci95": [round(v, decimals) for v in self.ap_ci95],
            "band_recall": _round(self.band_recall),
            "band_precision_lo": _round(self.band_precision_lo),
            "band_precision_hi": _round(self.band_precision_hi),
            "youden_threshold": round(self.youden_threshold, decimals),
            "youden_j": round(self.youden_j, decimals),
            "n_thresholds": self.n_thresholds,
            "n_bootstrap_requested": self.n_bootstrap_requested,
            "n_bootstrap_used": self.n_bootstrap_used,
            "n_positive": self.n_positive,
            "n_negative": self.n_negative,
        }


#: Fixed grid the bootstrap bands are interpolated onto (vertical averaging).
BAND_GRID: np.ndarray = np.linspace(0.0, 1.0, 101)


def curve_summary(
    name: str,
    y_true: np.ndarray,
    scores: np.ndarray,
    n_thresholds: int = 200,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> CurveSummary:
    """Compute measured ROC/PR curves, bootstrap CIs, and bootstrap bands.

    Bands are vertical-averaging bootstrap bands: each resample's curve is
    interpolated onto :data:`BAND_GRID` and the 2.5/97.5 percentiles are taken
    pointwise.  They are therefore real resampling output, and their width at
    a given point is a measured quantity that responds to sample size — the
    property the current manuscript caption asserts about bands that were
    ``rng.uniform(0.008, 0.025)`` draws.

    The AUC point estimate and every AUC replicate are computed on the *same*
    threshold grid with the *same* integrator, so the point estimate always
    lies inside its own interval.  (``evaluation.roc.bootstrap_auc_ci`` mixes a
    200-point point estimate with 100-point replicates, which on this corpus
    put the bag-of-words point estimate below its own lower bound.)  The AP
    interval comes from :func:`evaluation.precision_recall.bootstrap_ap_ci`,
    which draws from an identically seeded generator with the same call
    pattern, so both intervals rest on the same resamples.

    Args:
        name: Detector identifier carried into the summary.
        y_true: Boolean labels.
        scores: Continuous scores aligned with *y_true*.
        n_thresholds: Threshold-sweep resolution, shared by point and bootstrap.
        n_bootstrap: Requested resample count.
        seed: Bootstrap seed.

    Returns:
        A :class:`CurveSummary`.

    Raises:
        ValueError: If the inputs are misaligned or single-class.
    """
    y = np.asarray(y_true, dtype=bool)
    s = np.asarray(scores, dtype=np.float64)
    if y.shape != s.shape:
        raise ValueError(f"y_true {y.shape} and scores {s.shape} must match")
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        raise ValueError("curve_summary requires both classes to be present")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}")

    roc: ROCCurve = compute_roc(y, s, n_thresholds=n_thresholds)
    auc = auc_in_order(roc.fpr_points, roc.tpr_points)
    thr, j = youdens_j(roc)

    pr = compute_pr_curve(y.astype(int), s, n_thresholds=n_thresholds)
    ap, ap_lo, ap_hi = bootstrap_ap_ci(
        y.astype(int), s, n_bootstrap=n_bootstrap, confidence=0.95, seed=seed
    )

    rng = np.random.default_rng(seed)
    n = len(y)
    auc_replicates: list[float] = []
    tpr_replicates: list[np.ndarray] = []
    precision_replicates: list[np.ndarray] = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        by = y[idx]
        if by.sum() == 0 or by.sum() == n:
            continue
        bs = s[idx]
        broc = compute_roc(by, bs, n_thresholds=n_thresholds)
        auc_replicates.append(auc_in_order(broc.fpr_points, broc.tpr_points))
        tpr_replicates.append(np.interp(BAND_GRID, broc.fpr_points, broc.tpr_points))
        bpr = compute_pr_curve(by.astype(int), bs, n_thresholds=n_thresholds)
        # compute_pr_curve sweeps thresholds upward, so recall descends; np.interp
        # needs an ascending abscissa.
        precision_replicates.append(
            np.interp(BAND_GRID, bpr.recall[::-1], bpr.precision[::-1])
        )

    if auc_replicates:
        lo = float(np.percentile(auc_replicates, 2.5))
        hi = float(np.percentile(auc_replicates, 97.5))
        tpr_stack = np.vstack(tpr_replicates)
        band_tpr_lo = np.percentile(tpr_stack, 2.5, axis=0)
        band_tpr_hi = np.percentile(tpr_stack, 97.5, axis=0)
        prec_stack = np.vstack(precision_replicates)
        band_prec_lo = np.percentile(prec_stack, 2.5, axis=0)
        band_prec_hi = np.percentile(prec_stack, 97.5, axis=0)
    else:  # pragma: no cover - unreachable at any realistic class balance
        lo = hi = auc
        band_tpr_lo = band_tpr_hi = np.interp(BAND_GRID, roc.fpr_points, roc.tpr_points)
        band_prec_lo = band_prec_hi = np.interp(
            BAND_GRID, pr.recall[::-1], pr.precision[::-1]
        )

    return CurveSummary(
        name=name,
        fpr=roc.fpr_points,
        tpr=roc.tpr_points,
        roc_thresholds=roc.thresholds,
        auc=auc,
        auc_ci95=(lo, hi),
        band_fpr=BAND_GRID,
        band_tpr_lo=band_tpr_lo,
        band_tpr_hi=band_tpr_hi,
        precision=pr.precision,
        recall=pr.recall,
        average_precision=float(ap),
        ap_ci95=(float(ap_lo), float(ap_hi)),
        band_recall=BAND_GRID,
        band_precision_lo=band_prec_lo,
        band_precision_hi=band_prec_hi,
        youden_threshold=float(thr),
        youden_j=float(j),
        n_thresholds=n_thresholds,
        n_bootstrap_requested=n_bootstrap,
        n_bootstrap_used=len(auc_replicates),
        n_positive=n_pos,
        n_negative=n_neg,
    )


@dataclass(frozen=True)
class ComparisonRow:
    """One detector's entry in the comparison table.

    Attributes:
        metrics: Operating-point metrics.
        output: Raw per-payload scores and verdicts.
        trained: Whether the numbers are out-of-fold predictions of a trained
            model (``True``) or a fixed rule (``False``).
        extra: Free-form provenance for this row (fold count, flag rate the
            null was matched to, and so on).
    """

    metrics: DetectorMetrics
    output: DetectorOutput
    trained: bool = False
    extra: dict[str, object] = field(default_factory=dict)


def compare_detectors(
    outputs: Mapping[str, DetectorOutput] | Iterable[DetectorOutput],
    corpus: LabelledCorpus,
    trained_names: Sequence[str] = (),
) -> list[ComparisonRow]:
    """Build the comparison table from already-computed detector outputs.

    Rows are returned sorted by Youden's J descending, then by name, so the
    ordering is deterministic and the strongest detector is first regardless
    of which one it turns out to be.

    Args:
        outputs: Detector outputs, as a mapping or any iterable.
        corpus: The corpus every output was produced on.
        trained_names: Names whose rows come from out-of-fold predictions.

    Returns:
        The comparison rows, strongest first.

    Raises:
        ValueError: If fewer than two detectors are supplied — a "comparison"
            of one is exactly the failure mode this module exists to prevent.
    """
    items = list(outputs.values()) if isinstance(outputs, Mapping) else list(outputs)
    if len(items) < 2:
        raise ValueError(
            f"compare_detectors needs at least 2 detectors, got {len(items)}; "
            "a single-detector table is not a comparison"
        )

    trained = set(trained_names)
    rows = [
        ComparisonRow(
            metrics=evaluate_output(o, corpus),
            output=o,
            trained=o.name in trained,
        )
        for o in items
    ]
    rows.sort(key=lambda r: (-r.metrics.youden_j, r.metrics.name))
    return rows


def load_comparison_artifact(
    search_dirs: Sequence[Path] = (),
    path: Path | None = None,
) -> dict[str, Any]:
    """Load ``baseline_comparison.json``, failing loudly when it is absent.

    Figures call this rather than synthesising curves: a missing measurement
    must stop the render, not be replaced by a plausible shape.

    Args:
        search_dirs: Directories to check before the canonical
            :data:`DEFAULT_DATA_DIR`.
        path: Explicit artifact path, bypassing the search entirely.

    Returns:
        The decoded artifact.

    Raises:
        FileNotFoundError: If no artifact is found, with the command that
            produces it.
        ValueError: If the artifact is not stamped ``data_origin:
            real_pipeline`` — a figure must never plot synthetic scores as
            though they were measurements.
    """
    candidates = (
        [Path(path)]
        if path is not None
        else [Path(d) / COMPARISON_ARTIFACT_NAME for d in (*search_dirs, DEFAULT_DATA_DIR)]
    )
    for candidate in candidates:
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as handle:
                payload: dict[str, Any] = json.load(handle)
            origin = payload.get("data_origin")
            if origin != "real_pipeline":
                raise ValueError(
                    f"{candidate} is stamped data_origin={origin!r}; refusing to "
                    "plot it as measured detector scores"
                )
            return payload

    searched = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"{COMPARISON_ARTIFACT_NAME} not found (searched: {searched}). "
        "Run: python scripts/run_baseline_comparison.py --seed 42"
    )
