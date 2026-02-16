"""Parametric assumption tests: normality and homogeneity of variance.

Provides Shapiro-Wilk normality tests and Levene's test for
equality of variances, used to decide between parametric and
non-parametric analysis paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from scipy import stats


@dataclass
class AssumptionCheckResult:
    """Result of a single distributional assumption test.

    Attributes:
        test_name: Name of the statistical test.
        group_name: Identifier for the data group tested.
        statistic: Test statistic value.
        p_value: p-value for the null hypothesis.
        alpha: Significance threshold.
        passed: Whether the assumption holds (p >= alpha).
    """

    test_name: str
    group_name: str
    statistic: float
    p_value: float
    alpha: float
    passed: bool


def shapiro_wilk_normality(
    data: np.ndarray,
    group_name: str = "group",
    alpha: float = 0.05,
) -> AssumptionCheckResult:
    """Run the Shapiro-Wilk normality test.

    Parameters
    ----------
    data : ndarray
        1-D array of observations.
    group_name : str
        Label used in the result.
    alpha : float
        Significance level.

    Returns
    -------
    AssumptionCheckResult
    """
    data = np.asarray(data).ravel()
    if len(data) < 3:
        return AssumptionCheckResult(
            test_name="Shapiro-Wilk",
            group_name=group_name,
            statistic=float("nan"),
            p_value=float("nan"),
            alpha=alpha,
            passed=False,
        )
    stat, p = stats.shapiro(data)
    return AssumptionCheckResult(
        test_name="Shapiro-Wilk",
        group_name=group_name,
        statistic=float(stat),
        p_value=float(p),
        alpha=alpha,
        passed=p >= alpha,
    )


def levene_homogeneity(
    *groups: np.ndarray,
    alpha: float = 0.05,
) -> AssumptionCheckResult:
    """Run Levene's test for equality of variances.

    Parameters
    ----------
    *groups : ndarray
        Two or more 1-D arrays of observations.
    alpha : float
        Significance level.

    Returns
    -------
    AssumptionCheckResult
    """
    arrays = [np.asarray(g).ravel() for g in groups]
    if len(arrays) < 2:
        return AssumptionCheckResult(
            test_name="Levene",
            group_name="all_groups",
            statistic=float("nan"),
            p_value=float("nan"),
            alpha=alpha,
            passed=False,
        )
    stat, p = stats.levene(*arrays)
    return AssumptionCheckResult(
        test_name="Levene",
        group_name="all_groups",
        statistic=float(stat),
        p_value=float(p),
        alpha=alpha,
        passed=p >= alpha,
    )


def check_parametric_assumptions(
    group1: np.ndarray,
    group2: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[List[AssumptionCheckResult], bool]:
    """Check both normality (per group) and homogeneity of variances.

    Parameters
    ----------
    group1, group2 : ndarray
        Samples to compare.
    alpha : float
        Significance level.

    Returns
    -------
    results : list of AssumptionCheckResult
        Individual test results.
    all_met : bool
        True when all assumptions are satisfied.
    """
    results = [
        shapiro_wilk_normality(group1, group_name="group_1", alpha=alpha),
        shapiro_wilk_normality(group2, group_name="group_2", alpha=alpha),
        levene_homogeneity(group1, group2, alpha=alpha),
    ]
    all_met = all(r.passed for r in results)
    return results, all_met


__all__ = [
    "AssumptionCheckResult",
    "shapiro_wilk_normality",
    "levene_homogeneity",
    "check_parametric_assumptions",
]
