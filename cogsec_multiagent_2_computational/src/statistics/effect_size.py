"""Effect size measures: Cohen's d, odds ratios, NNT.

Provides standardised effect-size computations used throughout the CIF
evaluation to quantify *practical* significance beyond p-values.

Key targets from the manuscript:
- CIF vs. baseline Cohen's d ~ 4.2 (very large).
- Odds ratio for detection vs. miss across conditions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class EffectSizeResult:
    """Structured result of an effect-size computation.

    Attributes:
        measure: Name of the effect-size statistic.
        value: Point estimate.
        ci_lower: Lower bound of the confidence interval.
        ci_upper: Upper bound of the confidence interval.
        interpretation: Human-readable magnitude label.
    """

    measure: str
    value: float
    ci_lower: float
    ci_upper: float
    interpretation: str


# ---------------------------------------------------------------------------
# Cohen's d
# ---------------------------------------------------------------------------

def interpret_cohens_d(d: float) -> str:
    """Return a qualitative interpretation of Cohen's d.

    Thresholds follow standard conventions extended with *very large*:

    - ``|d| < 0.2``  -- negligible
    - ``0.2 <= |d| < 0.5`` -- small
    - ``0.5 <= |d| < 0.8`` -- medium
    - ``0.8 <= |d| < 1.2`` -- large
    - ``|d| >= 1.2`` -- very large

    Args:
        d: Cohen's d value (signed or unsigned).

    Returns:
        Interpretation string.
    """
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    if ad < 0.5:
        return "small"
    if ad < 0.8:
        return "medium"
    if ad < 1.2:
        return "large"
    return "very large"


def cohens_d_ci(
    d: float,
    n1: int,
    n2: int,
    ci: float = 0.95,
) -> Tuple[float, float]:
    """Confidence interval for Cohen's d via non-central t approximation.

    Uses the variance formula for the sampling distribution of d:

        Var(d) ~ (n1+n2)/(n1*n2) + d^2 / (2*(n1+n2))

    Then constructs a symmetric CI using the normal quantile.

    Args:
        d: Point estimate of Cohen's d.
        n1: Sample size of group 1.
        n2: Sample size of group 2.
        ci: Confidence level (default 0.95).

    Returns:
        ``(lower, upper)`` bounds.
    """
    se = math.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2.0 * (n1 + n2)))
    z = stats.norm.ppf((1.0 + ci) / 2.0)
    return (d - z * se, d + z * se)


def cohens_d(
    group1: np.ndarray,
    group2: np.ndarray,
    ci: float = 0.95,
) -> EffectSizeResult:
    """Cohen's d with pooled standard deviation.

    Computes ``d = (mean1 - mean2) / s_pooled`` where the pooled SD uses
    Bessel-corrected variances:

        s_pooled = sqrt(((n1-1)*s1^2 + (n2-1)*s2^2) / (n1+n2-2))

    Args:
        group1: Observations from group 1 (e.g. CIF scores).
        group2: Observations from group 2 (e.g. baseline scores).
        ci: Confidence level for the interval.

    Returns:
        :class:`EffectSizeResult` with interpretation.
    """
    g1 = np.asarray(group1, dtype=np.float64)
    g2 = np.asarray(group2, dtype=np.float64)

    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        raise ValueError("Each group must have at least 2 observations")

    mean1, mean2 = g1.mean(), g2.mean()
    var1, var2 = g1.var(ddof=1), g2.var(ddof=1)

    pooled_sd = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_sd == 0.0:
        d = 0.0
    else:
        d = (mean1 - mean2) / pooled_sd

    lower, upper = cohens_d_ci(d, n1, n2, ci)

    return EffectSizeResult(
        measure="Cohen's d",
        value=d,
        ci_lower=lower,
        ci_upper=upper,
        interpretation=interpret_cohens_d(d),
    )


# ---------------------------------------------------------------------------
# Odds ratio
# ---------------------------------------------------------------------------

def odds_ratio(
    tp: int,
    fp: int,
    fn: int,
    tn: int,
    ci: float = 0.95,
) -> EffectSizeResult:
    """Odds ratio with Woolf's log-method confidence interval.

    Computes OR = (tp * tn) / (fp * fn) and the log-transformed CI:

        ln(OR) +/- z * sqrt(1/tp + 1/fp + 1/fn + 1/tn)

    Applies a 0.5 continuity correction when any cell is zero.

    Args:
        tp: True positives.
        fp: False positives.
        fn: False negatives.
        tn: True negatives.
        ci: Confidence level.

    Returns:
        :class:`EffectSizeResult` with the odds ratio.
    """
    # Continuity correction if any cell is zero
    if any(v == 0 for v in (tp, fp, fn, tn)):
        tp_c = tp + 0.5
        fp_c = fp + 0.5
        fn_c = fn + 0.5
        tn_c = tn + 0.5
    else:
        tp_c = float(tp)
        fp_c = float(fp)
        fn_c = float(fn)
        tn_c = float(tn)

    or_value = (tp_c * tn_c) / (fp_c * fn_c)
    log_or = math.log(or_value)
    se_log_or = math.sqrt(1.0 / tp_c + 1.0 / fp_c + 1.0 / fn_c + 1.0 / tn_c)

    z = stats.norm.ppf((1.0 + ci) / 2.0)
    lower = math.exp(log_or - z * se_log_or)
    upper = math.exp(log_or + z * se_log_or)

    if or_value > 3.0:
        interp = "strong association"
    elif or_value > 1.5:
        interp = "moderate association"
    elif or_value > 1.0:
        interp = "weak association"
    elif or_value == 1.0:
        interp = "no association"
    else:
        interp = "inverse association"

    return EffectSizeResult(
        measure="odds ratio",
        value=or_value,
        ci_lower=lower,
        ci_upper=upper,
        interpretation=interp,
    )


# ---------------------------------------------------------------------------
# Number needed to treat
# ---------------------------------------------------------------------------

def number_needed_to_treat(
    control_rate: float,
    treatment_rate: float,
) -> float:
    """Number needed to treat (NNT).

    ``NNT = 1 / (treatment_rate - control_rate)``

    A lower NNT indicates a more effective treatment (defense).

    Args:
        control_rate: Event rate in the control arm (e.g. baseline detection).
        treatment_rate: Event rate in the treatment arm (e.g. CIF detection).

    Returns:
        NNT value.  Returns ``float('inf')`` when the rates are equal.
    """
    diff = treatment_rate - control_rate
    if diff == 0.0:
        return float("inf")
    return 1.0 / diff
