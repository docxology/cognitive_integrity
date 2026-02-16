"""Confidence interval computation: Wilson score, bootstrap.

Provides robust interval estimates for proportions (Wilson score) and
arbitrary statistics (bootstrap percentile method), with specialised
helpers for mean and difference-of-means CIs.
"""

from __future__ import annotations

import math
from typing import Callable, Tuple

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Wilson score interval
# ---------------------------------------------------------------------------

def wilson_ci(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Preferred over the Wald interval when the proportion is near 0 or 1,
    which is common for high-accuracy defense systems.

    Args:
        successes: Number of successes (e.g. detected attacks).
        total: Total number of trials.
        confidence: Desired confidence level.

    Returns:
        ``(proportion, lower, upper)`` tuple.

    Raises:
        ValueError: If *total* < 1 or *successes* out of range.
    """
    if total < 1:
        raise ValueError("total must be >= 1")
    if successes < 0 or successes > total:
        raise ValueError(
            f"successes must be in [0, total], got {successes} / {total}"
        )

    p_hat = successes / total
    z = stats.norm.ppf((1.0 + confidence) / 2.0)
    z2 = z * z

    denom = 1.0 + z2 / total
    centre = p_hat + z2 / (2.0 * total)
    margin = z * math.sqrt(
        (p_hat * (1.0 - p_hat) + z2 / (4.0 * total)) / total
    )

    lower = (centre - margin) / denom
    upper = (centre + margin) / denom

    # Clamp to [0, 1]
    lower = max(0.0, lower)
    upper = min(1.0, upper)

    return (p_hat, lower, upper)


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def bootstrap_ci(
    data: np.ndarray,
    statistic_fn: Callable[[np.ndarray], float],
    n_bootstrap: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap percentile confidence interval for an arbitrary statistic.

    Resamples *data* with replacement *n_bootstrap* times, computes the
    statistic each time, and returns percentile-based bounds.

    Args:
        data: 1-D array of observations.
        statistic_fn: Function mapping an array to a scalar.
        n_bootstrap: Number of bootstrap resamples.
        confidence: Desired confidence level.
        seed: RNG seed for reproducibility.

    Returns:
        ``(point_estimate, lower, upper)`` tuple.
    """
    data = np.asarray(data, dtype=np.float64)
    rng = np.random.default_rng(seed)

    point_estimate = float(statistic_fn(data))

    n = len(data)
    boot_stats = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        sample = rng.choice(data, size=n, replace=True)
        boot_stats[i] = statistic_fn(sample)

    alpha = 1.0 - confidence
    lower = float(np.percentile(boot_stats, 100.0 * alpha / 2.0))
    upper = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha / 2.0)))

    return (point_estimate, lower, upper)


def bootstrap_mean_ci(
    data: np.ndarray,
    n_bootstrap: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap CI specifically for the mean.

    Convenience wrapper around :func:`bootstrap_ci` with ``np.mean``.

    Args:
        data: 1-D array of observations.
        n_bootstrap: Number of bootstrap resamples.
        confidence: Desired confidence level.
        seed: RNG seed.

    Returns:
        ``(mean_estimate, lower, upper)`` tuple.
    """
    return bootstrap_ci(
        data,
        statistic_fn=lambda x: float(np.mean(x)),
        n_bootstrap=n_bootstrap,
        confidence=confidence,
        seed=seed,
    )


def bootstrap_diff_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap CI for the difference of means (mean(x) - mean(y)).

    Resamples each group independently and computes the difference in
    each bootstrap iteration.

    Args:
        x: 1-D array for group 1.
        y: 1-D array for group 2.
        n_bootstrap: Number of bootstrap resamples.
        confidence: Desired confidence level.
        seed: RNG seed.

    Returns:
        ``(diff_estimate, lower, upper)`` tuple.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    rng = np.random.default_rng(seed)

    point_estimate = float(np.mean(x) - np.mean(y))

    nx, ny = len(x), len(y)
    boot_diffs = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        sx = rng.choice(x, size=nx, replace=True)
        sy = rng.choice(y, size=ny, replace=True)
        boot_diffs[i] = np.mean(sx) - np.mean(sy)

    alpha = 1.0 - confidence
    lower = float(np.percentile(boot_diffs, 100.0 * alpha / 2.0))
    upper = float(np.percentile(boot_diffs, 100.0 * (1.0 - alpha / 2.0)))

    return (point_estimate, lower, upper)
