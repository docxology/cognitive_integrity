"""Wilson score confidence intervals for binomial proportions.

Shared by the LaTeX table generators so that every ``±`` printed in a
table is *computed from the recorded counts* rather than typed in by
hand.  Historically ``ablation_tables.py`` printed two invented constants
(``±0.008`` for the full pipeline and ``±0.015`` for every ablated
configuration); those numbers came from nowhere and could not move when
the underlying measurement moved.

The Wilson interval is used rather than the normal (Wald) approximation
because the measurements here routinely sit at ``p = 1.0`` or very close
to it, where Wald collapses to a zero-width interval.
"""

from __future__ import annotations

import math

# Two-sided 95% normal quantile.
Z_95 = 1.959963984540054


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Return the Wilson score interval ``(lo, hi)`` for ``successes / n``.

    Parameters
    ----------
    successes:
        Number of successes observed.  Must satisfy ``0 <= successes <= n``.
    n:
        Number of trials.  Must be positive.
    z:
        Normal quantile for the desired coverage (default: 95%).

    Raises
    ------
    ValueError
        If ``n <= 0`` or ``successes`` is outside ``[0, n]``.  Returning a
        silent ``(0.0, 0.0)`` for a degenerate input would print a
        zero-width interval into a published table, so this fails closed.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= successes <= n:
        raise ValueError(f"successes must lie in [0, {n}], got {successes}")

    p_hat = successes / n
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * n)) / n) / denom
    return (center - margin, center + margin)


def wilson_half_width(successes: int, n: int, z: float = Z_95) -> float:
    """Return the Wilson interval's half-width -- the value printed after ``±``.

    Note that the Wilson interval is asymmetric about ``successes / n``, so
    this half-width describes the interval's width, not a symmetric band
    around the point estimate.  Table captions must say ``95% CI`` (the
    interval), never ``p ± half-width`` as an exact reconstruction.
    """
    lo, hi = wilson_interval(successes, n, z=z)
    return (hi - lo) / 2.0


def rate_to_successes(rate: float, n: int) -> int:
    """Recover the integer success count from a recorded rate and ``n``.

    The result JSONs store ``tpr`` as a float rather than the underlying
    ``k``.  ``round`` recovers ``k`` exactly whenever the rate really was
    ``k / n``; a rate that is *not* a multiple of ``1 / n`` indicates the
    recorded ``n`` does not belong to the recorded rate, which is a data
    defect worth failing on rather than silently rounding away.

    Raises
    ------
    ValueError
        If ``rate * n`` is not an integer to within ``1e-6``.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    exact = rate * n
    k = round(exact)
    if abs(exact - k) > 1e-6:
        raise ValueError(
            f"rate {rate!r} is not a multiple of 1/{n} "
            f"(rate * n = {exact!r}); the recorded sample size does not "
            f"match the recorded rate"
        )
    return int(k)


__all__ = ["Z_95", "rate_to_successes", "wilson_half_width", "wilson_interval"]
