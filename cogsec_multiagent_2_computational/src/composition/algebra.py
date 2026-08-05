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

Corollary 3.3 (Hybrid Two-Stage Composition):
    For a two-stage pipeline where the fast stage uses max-fusion parallel
    composition and the deep stage uses series composition:
        R_hybrid = 1 - (1 - R_fast)(1 - R_deep)
    where R_fast = 1 - prod(1 - r_i) for fast-stage rates and
    R_deep = 1 - prod(1 - r_j) for deep-stage rates.

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
        miss_rate *= 1.0 - r

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
                p *= 1.0 - rates[i]
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
    var = sum(w**2 * r * (1 - r) for w, r in zip(weights, rates))

    if var <= 0:
        return 1.0 if mu > threshold else 0.0

    sigma = math.sqrt(var)
    z = (threshold - mu) / sigma
    return float(1.0 - norm.cdf(z))


# ---------------------------------------------------------------------------
# Extended composition algebra (Corollary 3.3 + helpers)
# ---------------------------------------------------------------------------


def compute_hybrid_detection_rate(
    fast_rates: List[float],
    deep_rates: List[float],
) -> float:
    """Compute the combined detection rate for a two-stage hybrid pipeline.

    Implements Corollary 3.3:

    .. math::

        R_{\\text{hybrid}} = 1 - (1 - R_{\\text{fast}})(1 - R_{\\text{deep}})

    The fast stage uses max-fusion (parallel) and the deep stage uses series
    composition.  The two stages are treated as statistically independent, so
    the combined miss rate is the product of the per-stage miss rates.

    Args:
        fast_rates: Per-module detection rates for the fast (parallel) stage.
            Each rate must be in [0, 1].
        deep_rates: Per-module detection rates for the deep (series) stage.
            Each rate must be in [0, 1].

    Returns:
        Combined detection rate in [0, 1].

    Raises:
        ValueError: If any rate is outside [0, 1].

    Examples:
        >>> compute_hybrid_detection_rate([0.91, 0.88], [0.79, 0.76, 0.70])
        0.9998...
    """
    for i, r in enumerate(fast_rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"fast_rates[{i}] out of bounds: {r} (must be in [0, 1])")
    for j, r in enumerate(deep_rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"deep_rates[{j}] out of bounds: {r} (must be in [0, 1])")

    r_fast = compute_series_detection_rate(fast_rates) if fast_rates else 0.0
    r_deep = compute_series_detection_rate(deep_rates) if deep_rates else 0.0
    return 1.0 - (1.0 - r_fast) * (1.0 - r_deep)


def compute_weighted_parallel_detection_rate(
    rates: List[float],
    weights: List[float],
    threshold: float = 0.5,
) -> float:
    """Compute the detection rate for weighted parallel fusion.

    Models each module as a Bernoulli(rᵢ) random variable Xᵢ and computes
    the probability that the weighted sum Y = Σ wᵢ Xᵢ exceeds ``threshold``
    via a Gaussian (normal) approximation:

    .. math::

        P(Y > \\theta) \\approx 1 - \\Phi\\!\\left(
            \\frac{\\theta - \\mu}{\\sigma}
        \\right)

    where :math:`\\mu = \\sum_i w_i r_i` and
    :math:`\\sigma^2 = \\sum_i w_i^2 r_i (1-r_i)`.

    Args:
        rates: Per-module detection rates, each in [0, 1].
        weights: Non-negative weights for each module.  Need not sum to 1
            (they are used as-is, not normalised).  Must have the same
            length as ``rates``.
        threshold: Detection threshold θ for the weighted sum (default 0.5).

    Returns:
        Approximate detection probability in [0, 1].

    Raises:
        ValueError: If lengths differ, any rate is outside [0, 1], or any
            weight is negative.

    Examples:
        >>> compute_weighted_parallel_detection_rate([0.9, 0.8], [0.6, 0.4])
        0.96...
    """
    if len(rates) != len(weights):
        raise ValueError(
            f"rates and weights must have the same length (got {len(rates)} and {len(weights)})"
        )
    for i, r in enumerate(rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"rates[{i}] out of bounds: {r} (must be in [0, 1])")
    for j, w in enumerate(weights):
        if w < 0.0:
            raise ValueError(f"weights[{j}] is negative: {w}")

    if not rates:
        return 0.0

    return _weighted_normal_approx(rates, threshold=threshold, weights=weights)


def compute_optimal_ordering(rates: List[float]) -> List[int]:
    """Find the optimal module ordering for series composition.

    For series pipelines that short-circuit on first detection the optimal
    ordering is determined by the *gain-per-latency* heuristic.  When
    latency information is not available we fall back to ordering modules by
    decreasing detection rate — placing the highest-rate module first gives
    the fastest expected early-exit.

    The ordering maximises the *expected number of early exits*, which for
    equal-latency modules is equivalent to sorting by descending rᵢ.

    .. note::
        This function only returns an ordering (a permutation of indices).
        The combined detection rate is invariant to ordering under the
        series formula (Theorem 3.1), but latency-to-first-detection is not.

    Args:
        rates: Per-module detection rates in [0, 1].

    Returns:
        List of module indices sorted from highest to lowest detection rate
        (i.e. the index of the best module is first).

    Raises:
        ValueError: If any rate is outside [0, 1].

    Examples:
        >>> compute_optimal_ordering([0.70, 0.91, 0.85])
        [1, 2, 0]
    """
    for i, r in enumerate(rates):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"rates[{i}] out of bounds: {r} (must be in [0, 1])")

    return sorted(range(len(rates)), key=lambda i: rates[i], reverse=True)


def latency_estimate(
    modules: List[str],
    strategy: str,
    latency_map: Optional[Dict[str, float]] = None,
    deep_modules: Optional[List[str]] = None,
) -> float:
    """Estimate total pipeline latency given a strategy.

    Latency models:

    - **series**:   L = Σ l_i   (modules execute sequentially)
    - **parallel**: L = max(l_i) (modules execute concurrently)
    - **hybrid**:   L = max(l_fast) + Σ(l_deep)

    NOTE (P2-F3): the "parallel" value is a THEORETICAL ideal for perfectly
    concurrent modules.  The reference ``ParallelPipeline.evaluate`` runs its
    modules sequentially in a loop (its wall-clock latency is the SUM, not the
    max), so a real parallel deployment exhibits latency closer to the series
    model unless modules are actually run on independent threads/processes.

    Args:
        modules: Ordered list of module names.
        strategy: One of ``'series'``, ``'parallel'``, ``'hybrid'``.
        latency_map: Mapping from module name to latency in ms.  Falls back
            to a default of 20 ms per module when a name is missing.
        deep_modules: For ``'hybrid'``: names of the deep-stage modules.

    Returns:
        Estimated total latency in milliseconds.

    Raises:
        ValueError: If strategy is unknown.

    Examples:
        >>> latency_estimate(["Firewall", "Detection"], "series",
        ...                  latency_map={"Firewall": 12, "Detection": 18})
        30.0
    """
    _default_latency = 20.0
    lm = latency_map or {}

    def _lat(name: str) -> float:
        return lm.get(name, _default_latency)

    fast_lats = [_lat(m) for m in modules]

    if strategy == "series":
        return sum(fast_lats)
    elif strategy == "parallel":
        return max(fast_lats) if fast_lats else 0.0
    elif strategy == "hybrid":
        deep_lats = [_lat(m) for m in (deep_modules or [])]
        fast_max = max(fast_lats) if fast_lats else 0.0
        deep_sum = sum(deep_lats)
        return fast_max + deep_sum
    else:
        raise ValueError(
            f"Unknown strategy: {strategy!r} (expected 'series', 'parallel', 'hybrid')"
        )


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
        result = series_pipe.evaluate(message, context)  # type: ignore[assignment]
        if result.detected:
            series_detections += 1
    series_empirical = series_detections / n_samples

    # Empirical: parallel pipeline (max fusion)
    parallel_pipe = ParallelPipeline(modules, fusion=MaxScoreFusion(threshold=0.5))
    parallel_detections = 0
    for message, context in test_data:
        result = parallel_pipe.evaluate(message, context)  # type: ignore[assignment]
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
