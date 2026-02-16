"""Composition operators implementing Theorems 3.1-3.2 from Paper 1.

Theorem 3.1 (Series Composition):
    For a series composition of n independent defense modules with
    individual detection rates r_1, ..., r_n, the combined miss rate is:
        P_miss = product_{i=1}^{n} (1 - r_i)
    and the combined detection rate is 1 - P_miss.

Theorem 3.2 (Parallel Composition):
    For a parallel composition with fusion strategy F, the combined
    detection rate depends on the fusion method:
        max:       1 - product(1 - r_i)  (same as series)
        majority:  sum of terms where >n/2 modules detect
        weighted:  depends on weight vector and threshold

This module provides constructor functions for building composed
pipelines and helper functions for computing theoretical detection rates.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .fusion import (
    FusionStrategy,
    MaxScoreFusion,
)
from .pipeline import (
    DefenseModule,
    ParallelPipeline,
    SeriesPipeline,
)

# ---------------------------------------------------------------------------
# Composition constructors
# ---------------------------------------------------------------------------

def series_compose(*modules: DefenseModule) -> SeriesPipeline:
    """Create a series pipeline from one or more defense modules.

    Modules are evaluated left-to-right; the first detection triggers
    an early return.

    Args:
        *modules: Defense module instances.

    Returns:
        A :class:`SeriesPipeline` that evaluates modules sequentially.

    Raises:
        ValueError: If no modules are provided.
    """
    if not modules:
        raise ValueError("series_compose requires at least one module")
    return SeriesPipeline(list(modules))


def parallel_compose(
    *modules: DefenseModule,
    fusion: Optional[FusionStrategy] = None,
    threshold: float = 0.5,
) -> ParallelPipeline:
    """Create a parallel pipeline from one or more defense modules.

    Args:
        *modules: Defense module instances.
        fusion: Fusion strategy (default :class:`MaxScoreFusion`).
        threshold: Detection threshold for the default fusion strategy.

    Returns:
        A :class:`ParallelPipeline` that evaluates all modules and fuses.

    Raises:
        ValueError: If no modules are provided.
    """
    if not modules:
        raise ValueError("parallel_compose requires at least one module")
    return ParallelPipeline(list(modules), fusion=fusion, threshold=threshold)


# ---------------------------------------------------------------------------
# Theoretical detection rate computations
# ---------------------------------------------------------------------------

def compute_series_detection_rate(rates: List[float]) -> float:
    """Compute the combined detection rate for series composition.

    Implements Theorem 3.1:
        detection_rate = 1 - product(1 - r_i)

    Each rate r_i is the probability that module i independently detects
    an attack.  Rates must be in [0, 1].

    Args:
        rates: Per-module detection rates.

    Returns:
        Combined detection rate.

    Raises:
        ValueError: If any rate is outside [0, 1].
    """
    for i, r in enumerate(rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"Rate {i} out of bounds: {r} (must be in [0, 1])")

    if not rates:
        return 0.0

    miss_rate = 1.0
    for r in rates:
        miss_rate *= (1.0 - r)

    return 1.0 - miss_rate


def compute_parallel_detection_rate(
    rates: List[float],
    strategy: str = "max",
) -> float:
    """Compute the combined detection rate for parallel composition.

    Implements Theorem 3.2 for different fusion strategies.

    Strategies:
        - ``"max"``: At least one module detects.
            detection = 1 - product(1 - r_i)
        - ``"majority"``: Strict majority (>50%) of modules detect.
            detection = sum over k > n/2 of C(n,k) * product(r_i^a * (1-r_i)^b)
        - ``"weighted"``: Weighted average exceeds threshold.  Approximated
            as the probability that a Gaussian-distributed weighted sum
            exceeds 0.5, where each module's contribution is Bernoulli(r_i).

    Args:
        rates: Per-module detection rates in [0, 1].
        strategy: One of ``'max'``, ``'majority'``, ``'weighted'``.

    Returns:
        Combined detection rate.

    Raises:
        ValueError: If strategy is unknown or rates are invalid.
    """
    for i, r in enumerate(rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"Rate {i} out of bounds: {r} (must be in [0, 1])")

    if not rates:
        return 0.0

    n = len(rates)

    if strategy == "max":
        # Same formula as series (at least one detects)
        return compute_series_detection_rate(rates)

    elif strategy == "majority":
        # Exact computation via enumeration of all 2^n subsets
        # Feasible for moderate n; for n > 20 use normal approximation
        if n > 20:
            return _majority_normal_approx(rates)
        return _majority_exact(rates)

    elif strategy == "weighted":
        # Normal approximation for weighted Bernoulli sum
        return _weighted_normal_approx(rates, threshold=0.5)

    else:
        raise ValueError(f"Unknown strategy: {strategy!r} (expected 'max', 'majority', 'weighted')")


def _majority_exact(rates: List[float]) -> float:
    """Exact majority detection probability via binary enumeration."""
    n = len(rates)
    threshold = n / 2.0
    total_prob = 0.0

    for mask in range(1 << n):
        detectors = bin(mask).count("1")
        if detectors <= threshold:
            continue

        p = 1.0
        for i in range(n):
            if mask & (1 << i):
                p *= rates[i]
            else:
                p *= (1.0 - rates[i])
        total_prob += p

    return total_prob


def _majority_normal_approx(rates: List[float]) -> float:
    """Normal approximation for majority detection (large n)."""
    from scipy.stats import norm  # type: ignore

    n = len(rates)
    # Sum of independent Bernoulli: mean = sum(r_i), var = sum(r_i*(1-r_i))
    mu = sum(rates)
    var = sum(r * (1 - r) for r in rates)
    if var <= 0:
        return 1.0 if mu > n / 2.0 else 0.0

    sigma = math.sqrt(var)
    # P(X > n/2) with continuity correction
    z = (n / 2.0 + 0.5 - mu) / sigma
    return float(1.0 - norm.cdf(z))


def _weighted_normal_approx(
    rates: List[float],
    threshold: float = 0.5,
    weights: Optional[List[float]] = None,
) -> float:
    """Normal approximation for P(weighted_avg > threshold)."""
    from scipy.stats import norm  # type: ignore

    n = len(rates)
    if weights is None:
        weights = [1.0 / n] * n

    # Weighted sum of Bernoulli: Y = sum(w_i * X_i), X_i ~ Bernoulli(r_i)
    mu = sum(w * r for w, r in zip(weights, rates))
    var = sum(w ** 2 * r * (1 - r) for w, r in zip(weights, rates))

    if var <= 0:
        return 1.0 if mu > threshold else 0.0

    sigma = math.sqrt(var)
    z = (threshold - mu) / sigma
    return float(1.0 - norm.cdf(z))


# ---------------------------------------------------------------------------
# Empirical validation
# ---------------------------------------------------------------------------

def validate_composition_theorem(
    modules: List[DefenseModule],
    test_data: List[Tuple[str, Dict[str, Any]]],
    n_trials: int = 100,
    seed: int = 42,
    tolerance: float = 0.15,
) -> Dict[str, Any]:
    """Validate that empirical detection rate matches theoretical prediction.

    Runs both a series and parallel pipeline on the test data and compares
    empirical detection rates against the theoretical formulas.

    Args:
        modules: Defense modules to compose.
        test_data: List of (message, context) tuples. Each should be an
            attack that *should* be detected.
        n_trials: Number of evaluation trials (for statistical stability).
        seed: Random seed.
        tolerance: Acceptable absolute difference between empirical and
            theoretical rates.

    Returns:
        A dict with keys:
            - ``series_empirical``: Observed series detection rate.
            - ``series_theoretical``: Predicted series detection rate.
            - ``series_valid``: Whether the difference is within tolerance.
            - ``parallel_empirical``: Observed parallel detection rate (max fusion).
            - ``parallel_theoretical``: Predicted parallel detection rate.
            - ``parallel_valid``: Whether the difference is within tolerance.
            - ``individual_rates``: Per-module empirical detection rates.
    """
    n_samples = len(test_data)
    if n_samples == 0:
        return {
            "series_empirical": 0.0,
            "series_theoretical": 0.0,
            "series_valid": True,
            "parallel_empirical": 0.0,
            "parallel_theoretical": 0.0,
            "parallel_valid": True,
            "individual_rates": [],
        }

    # Measure individual detection rates
    individual_rates: List[float] = []
    for module in modules:
        detections = 0
        for message, context in test_data:
            result = module.evaluate(message, context)
            if result.detected:
                detections += 1
        individual_rates.append(detections / n_samples)

    # Theoretical
    series_theoretical = compute_series_detection_rate(individual_rates)
    parallel_theoretical = compute_parallel_detection_rate(individual_rates, strategy="max")

    # Empirical: series pipeline
    series_pipe = SeriesPipeline(modules)
    series_detections = 0
    for message, context in test_data:
        result = series_pipe.evaluate(message, context)
        if result.detected:
            series_detections += 1
    series_empirical = series_detections / n_samples

    # Empirical: parallel pipeline (max fusion)
    parallel_pipe = ParallelPipeline(modules, fusion=MaxScoreFusion(threshold=0.5))
    parallel_detections = 0
    for message, context in test_data:
        result = parallel_pipe.evaluate(message, context)
        if result.detected:
            parallel_detections += 1
    parallel_empirical = parallel_detections / n_samples

    return {
        "series_empirical": series_empirical,
        "series_theoretical": series_theoretical,
        "series_valid": abs(series_empirical - series_theoretical) <= tolerance,
        "parallel_empirical": parallel_empirical,
        "parallel_theoretical": parallel_theoretical,
        "parallel_valid": abs(parallel_empirical - parallel_theoretical) <= tolerance,
        "individual_rates": individual_rates,
    }
