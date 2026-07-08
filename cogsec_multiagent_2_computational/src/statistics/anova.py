"""Two-way ANOVA for parameter interaction effects.

Implements Type I (sequential) sum-of-squares decomposition entirely
with numpy -- no statsmodels dependency.  Used to test whether defense
parameters (e.g. threshold and window size) have main or interaction
effects on detection performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class AnovaResult:
    """Single row from a two-way ANOVA table.

    Attributes:
        source: Name of the variance source (``'factor1'``, ``'factor2'``,
            ``'interaction'``, ``'residual'``).
        ss: Sum of squares.
        df: Degrees of freedom.
        ms: Mean square (``ss / df``).
        f_statistic: F ratio (``ms_effect / ms_residual``).
        p_value: Achieved significance level from the F distribution.
    """

    source: str
    ss: float
    df: int
    ms: float
    f_statistic: float
    p_value: float


# ---------------------------------------------------------------------------
# Effect size helpers
# ---------------------------------------------------------------------------

def eta_squared(ss_effect: float, ss_total: float) -> float:
    """Eta-squared effect size for ANOVA.

    ``eta^2 = SS_effect / SS_total``

    Args:
        ss_effect: Sum of squares for the effect.
        ss_total: Total sum of squares.

    Returns:
        Eta-squared (proportion of total variance explained).
    """
    if ss_total == 0.0:
        return 0.0
    return ss_effect / ss_total


def partial_eta_squared(ss_effect: float, ss_error: float) -> float:
    """Partial eta-squared effect size.

    ``partial_eta^2 = SS_effect / (SS_effect + SS_error)``

    Args:
        ss_effect: Sum of squares for the effect.
        ss_error: Sum of squares for residual error.

    Returns:
        Partial eta-squared.
    """
    denom = ss_effect + ss_error
    if denom == 0.0:
        return 0.0
    return ss_effect / denom


# ---------------------------------------------------------------------------
# Two-way ANOVA (Type I SS, balanced or unbalanced)
# ---------------------------------------------------------------------------

def two_way_anova(
    data: np.ndarray,
    factor1_levels: int,
    factor2_levels: int,
) -> List[AnovaResult]:
    """Two-way ANOVA with Type I sequential sum-of-squares.

    Expects *data* shaped as ``(factor1_levels, factor2_levels, n_replicates)``
    where each cell ``[i, j, :]`` contains the replicate observations for
    level *i* of factor 1 and level *j* of factor 2.

    Args:
        data: 3-D array of shape ``(a, b, n)`` where ``a = factor1_levels``,
            ``b = factor2_levels``, ``n`` = replicates per cell.
        factor1_levels: Number of levels for factor 1 (must match
            ``data.shape[0]``).
        factor2_levels: Number of levels for factor 2 (must match
            ``data.shape[1]``).

    Returns:
        List of 4 :class:`AnovaResult` objects:
        ``[factor1, factor2, interaction, residual]``.

    Raises:
        ValueError: If *data* shape does not match the stated factor levels.
    """
    data = np.asarray(data, dtype=np.float64)

    if data.ndim != 3:
        raise ValueError(
            f"data must be 3-D (a, b, n), got {data.ndim}-D array"
        )

    a, b, n = data.shape
    if a != factor1_levels or b != factor2_levels:
        raise ValueError(
            f"Shape mismatch: data has ({a}, {b}) but expected "
            f"({factor1_levels}, {factor2_levels})"
        )

    a * b * n  # total observations
    grand_mean = data.mean()

    # SS total
    ss_total = np.sum((data - grand_mean) ** 2)

    # Factor 1 (rows): marginal means across factor 2 and replicates
    row_means = data.mean(axis=(1, 2))  # shape (a,)
    ss_factor1 = b * n * np.sum((row_means - grand_mean) ** 2)

    # Factor 2 (columns): marginal means across factor 1 and replicates
    col_means = data.mean(axis=(0, 2))  # shape (b,)
    ss_factor2 = a * n * np.sum((col_means - grand_mean) ** 2)

    # Interaction: cell means minus row/column effects minus grand mean
    cell_means = data.mean(axis=2)  # shape (a, b)
    interaction_deviations = (
        cell_means
        - row_means[:, np.newaxis]
        - col_means[np.newaxis, :]
        + grand_mean
    )
    ss_interaction = n * np.sum(interaction_deviations ** 2)

    # Residual (within-cell): total - factor1 - factor2 - interaction
    ss_residual = ss_total - ss_factor1 - ss_factor2 - ss_interaction

    # Degrees of freedom
    df_factor1 = a - 1
    df_factor2 = b - 1
    df_interaction = df_factor1 * df_factor2
    df_residual = a * b * (n - 1)

    # Mean squares
    ms_factor1 = ss_factor1 / df_factor1 if df_factor1 > 0 else 0.0
    ms_factor2 = ss_factor2 / df_factor2 if df_factor2 > 0 else 0.0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0.0
    ms_residual = ss_residual / df_residual if df_residual > 0 else 0.0

    # F statistics and p-values
    if ms_residual > 0.0:
        f1 = ms_factor1 / ms_residual
        f2 = ms_factor2 / ms_residual
        f_int = ms_interaction / ms_residual

        p1 = float(1.0 - stats.f.cdf(f1, df_factor1, df_residual))
        p2 = float(1.0 - stats.f.cdf(f2, df_factor2, df_residual))
        p_int = float(1.0 - stats.f.cdf(f_int, df_interaction, df_residual))
    else:
        f1 = f2 = f_int = 0.0
        p1 = p2 = p_int = 1.0

    return [
        AnovaResult(
            source="factor1",
            ss=float(ss_factor1),
            df=df_factor1,
            ms=float(ms_factor1),
            f_statistic=float(f1),
            p_value=p1,
        ),
        AnovaResult(
            source="factor2",
            ss=float(ss_factor2),
            df=df_factor2,
            ms=float(ms_factor2),
            f_statistic=float(f2),
            p_value=p2,
        ),
        AnovaResult(
            source="interaction",
            ss=float(ss_interaction),
            df=df_interaction,
            ms=float(ms_interaction),
            f_statistic=float(f_int),
            p_value=p_int,
        ),
        AnovaResult(
            source="residual",
            ss=float(ss_residual),
            df=df_residual,
            ms=float(ms_residual),
            f_statistic=0.0,
            p_value=1.0,
        ),
    ]
