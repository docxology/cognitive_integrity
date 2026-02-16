"""Non-parametric tests: Kruskal-Wallis, Mann-Whitney U.

Distribution-free alternatives used when normality cannot be assumed,
particularly for cross-architecture comparisons where sample sizes per
architecture may be small.

Key target: Kruskal-Wallis H ~ 28.7 for the 6-architecture comparison.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

from .hypothesis import HypothesisResult

# ---------------------------------------------------------------------------
# Kruskal-Wallis H test
# ---------------------------------------------------------------------------

def kruskal_wallis(
    *groups: np.ndarray,
    alpha: float = 0.05,
) -> HypothesisResult:
    """Kruskal-Wallis H test for independent samples.

    Non-parametric alternative to one-way ANOVA.  Tests whether the
    population medians of the groups are equal.

    Args:
        *groups: Two or more arrays of observations.
        alpha: Significance threshold.

    Returns:
        :class:`HypothesisResult` with the H statistic and p-value.

    Raises:
        ValueError: If fewer than 2 groups are provided.
    """
    if len(groups) < 2:
        raise ValueError("Need at least 2 groups for Kruskal-Wallis")

    arrays = [np.asarray(g, dtype=np.float64) for g in groups]
    h_stat, p_val = stats.kruskal(*arrays)

    return HypothesisResult(
        name="Kruskal-Wallis",
        test_statistic=float(h_stat),
        p_value=float(p_val),
        significant=float(p_val) < alpha,
        alpha=alpha,
        description=(
            f"Kruskal-Wallis H test across {len(groups)} groups: "
            f"H={h_stat:.3f}, p={p_val:.6f}."
        ),
        method="Kruskal-Wallis H test",
    )


# ---------------------------------------------------------------------------
# Mann-Whitney U test
# ---------------------------------------------------------------------------

def mann_whitney_u(
    x: np.ndarray,
    y: np.ndarray,
    alternative: str = "two-sided",
    alpha: float = 0.05,
) -> HypothesisResult:
    """Mann-Whitney U test for two independent samples.

    Non-parametric alternative to the independent-samples t-test.

    Args:
        x: Observations from group 1.
        y: Observations from group 2.
        alternative: ``'two-sided'``, ``'less'``, or ``'greater'``.
        alpha: Significance threshold.

    Returns:
        :class:`HypothesisResult`.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    u_stat, p_val = stats.mannwhitneyu(x_arr, y_arr, alternative=alternative)

    return HypothesisResult(
        name="Mann-Whitney U",
        test_statistic=float(u_stat),
        p_value=float(p_val),
        significant=float(p_val) < alpha,
        alpha=alpha,
        description=(
            f"Mann-Whitney U test ({alternative}): "
            f"U={u_stat:.3f}, p={p_val:.6f}."
        ),
        method=f"Mann-Whitney U ({alternative})",
    )


# ---------------------------------------------------------------------------
# Rank-biserial correlation (effect size for Mann-Whitney)
# ---------------------------------------------------------------------------

def rank_biserial_correlation(
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    """Rank-biserial correlation coefficient.

    Effect size for the Mann-Whitney U test, computed as:

        r = 1 - (2*U) / (n1 * n2)

    where U is the Mann-Whitney U statistic.

    Values range from -1 to 1, with 0 indicating no effect.

    Args:
        x: Observations from group 1.
        y: Observations from group 2.

    Returns:
        Rank-biserial correlation value.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    n1, n2 = len(x_arr), len(y_arr)
    u_stat, _ = stats.mannwhitneyu(x_arr, y_arr, alternative="two-sided")

    return 1.0 - (2.0 * u_stat) / (n1 * n2)


# ---------------------------------------------------------------------------
# Dunn's post-hoc test (after Kruskal-Wallis)
# ---------------------------------------------------------------------------

def dunn_posthoc(
    groups: List[np.ndarray],
    p_value_kruskal: float,
) -> Dict[Tuple[int, int], float]:
    """Pairwise post-hoc comparisons after a significant Kruskal-Wallis.

    Uses Dunn's test with Bonferroni correction.  For each pair of groups,
    computes a z-statistic from the difference of mean ranks and applies
    the Bonferroni-adjusted significance criterion.

    Args:
        groups: List of observation arrays (same as passed to
            :func:`kruskal_wallis`).
        p_value_kruskal: The p-value from the omnibus Kruskal-Wallis test.
            Included for documentation; the post-hoc runs regardless.

    Returns:
        Dictionary mapping ``(i, j)`` group-index pairs to Bonferroni-
        corrected p-values.
    """
    k = len(groups)
    if k < 2:
        return {}

    # Pool all observations and compute ranks
    all_data = np.concatenate([np.asarray(g, dtype=np.float64) for g in groups])
    n_total = len(all_data)
    ranks = stats.rankdata(all_data)

    # Split ranks back into groups
    group_ranks: List[np.ndarray] = []
    idx = 0
    for g in groups:
        n_g = len(g)
        group_ranks.append(ranks[idx : idx + n_g])
        idx += n_g

    group_sizes = np.array([len(g) for g in groups], dtype=np.float64)
    group_mean_ranks = np.array([gr.mean() for gr in group_ranks])

    # Tie correction factor
    _, tie_counts = np.unique(ranks, return_counts=True)
    tie_correction = 1.0 - np.sum(tie_counts ** 3 - tie_counts) / (
        n_total ** 3 - n_total
    )
    if tie_correction == 0.0:
        tie_correction = 1.0  # avoid division by zero when all values tied

    # Variance of rank sums
    sigma2 = (n_total * (n_total + 1.0) / 12.0) * tie_correction

    # Pairwise comparisons
    n_pairs = k * (k - 1) // 2
    result: Dict[Tuple[int, int], float] = {}

    for i, j in combinations(range(k), 2):
        diff = abs(group_mean_ranks[i] - group_mean_ranks[j])
        se = np.sqrt(sigma2 * (1.0 / group_sizes[i] + 1.0 / group_sizes[j]))

        if se == 0.0:
            z = 0.0
        else:
            z = diff / se

        # Two-sided p-value
        p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
        # Bonferroni correction
        p_corrected = min(p_val * n_pairs, 1.0)
        result[(i, j)] = p_corrected

    return result
