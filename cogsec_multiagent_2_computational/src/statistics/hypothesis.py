"""Hypothesis testing for manuscript claims H1, H2, H3.

Provides statistical tests for the three core claims of the Cognitive
Integrity Framework evaluation:

- **H1**: CIF detection rate exceeds baseline (paired t-test, one-sided).
- **H2**: CIF outperforms each individual component (Bonferroni-corrected).
- **H3**: CIF maintains superiority per architecture (6 architectures).

All tests use ``scipy.stats`` under the hood and return structured
:class:`HypothesisResult` objects for downstream reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class HypothesisResult:
    """Structured result of a single hypothesis test.

    Attributes:
        name: Human-readable hypothesis label (e.g. ``'H1'``).
        test_statistic: Value of the test statistic (t, U, etc.).
        p_value: Achieved significance level.
        significant: Whether *p_value* < *alpha* (after any correction).
        alpha: Significance threshold used.
        description: Plain-English description of what was tested.
        method: Name of the statistical method (e.g. ``'paired t-test'``).
    """

    name: str
    test_statistic: float
    p_value: float
    significant: bool
    alpha: float
    description: str
    method: str


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def paired_ttest(
    x: np.ndarray,
    y: np.ndarray,
    alternative: str = "greater",
) -> Tuple[float, float]:
    """Paired-sample t-test wrapper.

    Args:
        x: Scores for the first condition (e.g. CIF).
        y: Scores for the second condition (e.g. baseline).
        alternative: ``'greater'``, ``'less'``, or ``'two-sided'``.

    Returns:
        ``(t_statistic, p_value)`` tuple.

    Raises:
        ValueError: If *x* and *y* have different lengths or fewer than 2
            observations.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if x.shape != y.shape:
        raise ValueError(
            f"Arrays must have the same shape, got {x.shape} vs {y.shape}"
        )
    if x.size < 2:
        raise ValueError("Need at least 2 paired observations")

    result = stats.ttest_rel(x, y, alternative=alternative)
    return float(result.statistic), float(result.pvalue)


def bonferroni_correct(
    p_values: List[float],
    alpha: float = 0.05,
) -> List[bool]:
    """Apply Bonferroni correction for multiple comparisons.

    Each *p*-value is compared against ``alpha / m`` where *m* is the
    total number of comparisons.

    Args:
        p_values: Raw p-values from individual tests.
        alpha: Family-wise error rate.

    Returns:
        List of booleans indicating significance after correction.
    """
    m = len(p_values)
    if m == 0:
        return []
    corrected_alpha = alpha / m
    return [p < corrected_alpha for p in p_values]


# ---------------------------------------------------------------------------
# H1: CIF vs. baseline
# ---------------------------------------------------------------------------

def test_h1_cif_vs_baseline(
    cif_scores: np.ndarray,
    baseline_scores: np.ndarray,
    alpha: float = 0.001,
) -> HypothesisResult:
    """H1 -- CIF detection rate exceeds baseline.

    Uses a one-sided paired t-test (CIF > baseline).

    Args:
        cif_scores: Per-run detection rates for the full CIF pipeline.
        baseline_scores: Per-run detection rates for the baseline.
        alpha: Significance threshold (manuscript uses 0.001).

    Returns:
        :class:`HypothesisResult` summarising the test.
    """
    t_stat, p_val = paired_ttest(
        np.asarray(cif_scores, dtype=np.float64),
        np.asarray(baseline_scores, dtype=np.float64),
        alternative="greater",
    )

    return HypothesisResult(
        name="H1",
        test_statistic=t_stat,
        p_value=p_val,
        significant=p_val < alpha,
        alpha=alpha,
        description=(
            "CIF detection rate is significantly greater than "
            "baseline detection rate (one-sided paired t-test)."
        ),
        method="paired t-test (one-sided, greater)",
    )


# ---------------------------------------------------------------------------
# H2: CIF vs. each individual component
# ---------------------------------------------------------------------------

def test_h2_cif_vs_components(
    cif_scores: np.ndarray,
    component_scores_dict: Dict[str, np.ndarray],
    alpha: float = 0.001,
) -> List[HypothesisResult]:
    """H2 -- CIF outperforms each individual defense component.

    Runs a paired t-test for every component and applies Bonferroni
    correction across all comparisons.

    Args:
        cif_scores: Per-run detection rates for the full CIF pipeline.
        component_scores_dict: Mapping of component name to per-run
            detection rates.
        alpha: Family-wise significance threshold.

    Returns:
        List of :class:`HypothesisResult`, one per component.
    """
    cif = np.asarray(cif_scores, dtype=np.float64)
    names = list(component_scores_dict.keys())
    m = len(names)

    raw_p_values: List[float] = []
    t_stats: List[float] = []

    for name in names:
        comp = np.asarray(component_scores_dict[name], dtype=np.float64)
        t, p = paired_ttest(cif, comp, alternative="greater")
        t_stats.append(t)
        raw_p_values.append(p)

    significant_flags = bonferroni_correct(raw_p_values, alpha)
    corrected_alpha = alpha / m if m > 0 else alpha

    results: List[HypothesisResult] = []
    for i, name in enumerate(names):
        results.append(
            HypothesisResult(
                name=f"H2_{name}",
                test_statistic=t_stats[i],
                p_value=raw_p_values[i],
                significant=significant_flags[i],
                alpha=corrected_alpha,
                description=(
                    f"CIF detection rate > {name} component "
                    f"(Bonferroni-corrected, m={m})."
                ),
                method="paired t-test (one-sided, Bonferroni-corrected)",
            )
        )

    return results


# ---------------------------------------------------------------------------
# H3: Per-architecture superiority

def _is_degenerate(*arrays: np.ndarray) -> bool:
    """True if any input series is constant (zero variance / zero range)."""
    for a in arrays:
        if a.size == 0:
            return True
        if np.allclose(a, a[0]):
            return True
    return False



# ---------------------------------------------------------------------------

def test_h3_per_architecture(
    results_by_arch: Dict[str, Tuple[np.ndarray, np.ndarray]],
    alpha: float = 0.001,
) -> List[HypothesisResult]:
    """H3 -- CIF superiority holds within each architecture.

    Args:
        results_by_arch: Mapping of architecture name to
            ``(cif_scores, baseline_scores)`` tuples.
        alpha: Significance threshold (per architecture, no further
            correction -- each architecture is a separate sub-hypothesis).

    Returns:
        List of :class:`HypothesisResult`, one per architecture.
    """
    results: List[HypothesisResult] = []

    for arch_name, (cif, baseline) in results_by_arch.items():
        cif_arr = np.asarray(cif, dtype=np.float64)
        base_arr = np.asarray(baseline, dtype=np.float64)

        t_stat, p_val = paired_ttest(cif_arr, base_arr, alternative="greater")

        # Degenerate-operating-point guard (P2-18): a paired t-test on a
        # constant series (e.g. every cell at rate 1.0) yields a meaningless
        # tiny p-value.  Surface it explicitly instead of reporting it as
        # evidence of superiority; the numeric p is preserved for the
        # artifact, but it is not marked significant.
        degenerate = _is_degenerate(cif_arr, base_arr)
        desc = (
            f"CIF detection rate > baseline for architecture "
            f"'{arch_name}' (one-sided paired t-test)."
        )
        if degenerate:
            desc += (" DEGENERATE OPERATING POINT: one or both input series "
                     "is constant (zero variance); the paired t-test is not "
                     "meaningful here and this row is not treated as evidence.")

        results.append(
            HypothesisResult(
                name=f"H3_{arch_name}",
                test_statistic=t_stat,
                p_value=p_val,
                significant=False if degenerate else (p_val < alpha),
                alpha=alpha,
                description=desc,
                method="paired t-test (one-sided, per-architecture)",
            )
        )

    return results
