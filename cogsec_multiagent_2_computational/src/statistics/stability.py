"""Multi-seed stability analysis for detection metrics.

Evaluates pipeline consistency by running the evaluation across multiple
random seeds and computing the coefficient of variation (CV) for key
metrics.  A CV below a threshold indicates stable results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np


@dataclass
class SeedMetrics:
    """Per-seed evaluation metrics.

    Attributes:
        seed: Random seed used.
        overall_detection_rate: Aggregate detection rate.
        per_architecture: Detection rates keyed by architecture name.
        per_category: Detection rates keyed by attack category.
    """

    seed: int
    overall_detection_rate: float
    per_architecture: Dict[str, float] = field(default_factory=dict)
    per_category: Dict[str, float] = field(default_factory=dict)


@dataclass
class StabilityReport:
    """Report on multi-seed stability.

    Attributes:
        n_seeds: Number of seeds evaluated.
        overall_cv: Coefficient of variation for overall detection rate.
        per_architecture_cv: CV per architecture.
        per_category_cv: CV per category.
        cv_threshold: Threshold below which results are considered stable.
        stable: Whether all CVs are below the threshold.
        seed_metrics: Full per-seed results.
    """

    n_seeds: int
    overall_cv: float
    per_architecture_cv: Dict[str, float]
    per_category_cv: Dict[str, float]
    cv_threshold: float
    stable: bool
    seed_metrics: List[SeedMetrics]


def coefficient_of_variation(values: np.ndarray) -> float:
    """Compute the coefficient of variation (std / mean).

    Returns 0.0 when the mean is zero to avoid division by zero.
    """
    values = np.asarray(values, dtype=float)
    mean = np.mean(values)
    if mean == 0.0:
        return 0.0
    return float(np.std(values) / abs(mean))


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

    # Check stability
    all_cvs = [overall_cv] + list(per_arch_cv.values()) + list(per_cat_cv.values())
    stable = all(cv <= cv_threshold for cv in all_cvs)

    return StabilityReport(
        n_seeds=len(seeds),
        overall_cv=overall_cv,
        per_architecture_cv=per_arch_cv,
        per_category_cv=per_cat_cv,
        cv_threshold=cv_threshold,
        stable=stable,
        seed_metrics=all_metrics,
    )


__all__ = [
    "SeedMetrics",
    "StabilityReport",
    "coefficient_of_variation",
    "run_multi_seed_stability",
    "make_pipeline_eval_fn",
]


def make_pipeline_eval_fn(
    n_samples: int = 100,
) -> Callable[[int], SeedMetrics]:
    """Create a pipeline-based evaluation function for stability analysis.

    Parameters
    ----------
    n_samples : int
        Number of corpus samples to evaluate per seed (for speed).

    Returns
    -------
    callable
        ``(seed: int) -> SeedMetrics`` suitable for ``run_multi_seed_stability``.
    """
    def eval_fn(seed: int) -> SeedMetrics:
        from attacks.corpus import AttackCorpus
        from composition.factory import create_full_pipeline
        from utils.random_seed import set_global_seed

        set_global_seed(seed)
        pipeline = create_full_pipeline()
        corpus = AttackCorpus.generate(seed=seed)

        detected_count = 0
        total = 0
        for sample in list(corpus)[:n_samples]:
            result = pipeline.evaluate(sample.payload)
            if result.detected:
                detected_count += 1
            total += 1

        overall = detected_count / total if total > 0 else 0.0
        return SeedMetrics(
            seed=seed,
            overall_detection_rate=overall,
            per_architecture={"Claude Code": overall},
            per_category={},
        )

    return eval_fn

