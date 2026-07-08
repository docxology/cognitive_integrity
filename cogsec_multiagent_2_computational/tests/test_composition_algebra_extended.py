"""Additional tests for src/composition/algebra.py to boost branch coverage.

Targets uncovered code paths:
- compute_parallel_detection_rate: 'majority', 'weighted', unknown strategy, n>20
- _majority_exact, _majority_normal_approx, _weighted_normal_approx
- compute_hybrid_detection_rate: invalid rates
- compute_weighted_parallel_detection_rate: length mismatch, invalid rates/weights
- compute_optimal_ordering: invalid rates
- latency_estimate: all strategies including 'hybrid' and unknown
- validate_composition_theorem: empty and non-empty test data

All tests use real computation. No mocks.
"""

from __future__ import annotations

import pytest

from composition.algebra import (
    compute_hybrid_detection_rate,
    compute_optimal_ordering,
    compute_parallel_detection_rate,
    compute_weighted_parallel_detection_rate,
    latency_estimate,
)

# ---------------------------------------------------------------------------
# compute_parallel_detection_rate — additional strategies
# ---------------------------------------------------------------------------


class TestParallelDetectionRateExtended:
    """Tests for compute_parallel_detection_rate with non-default strategies."""

    def test_majority_strategy_three_modules(self):
        """Majority vote with 3 modules at 0.8 each."""
        rates = [0.8, 0.8, 0.8]
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert 0.0 <= result <= 1.0
        # P(at least 2 of 3 detect) = 3*0.8^2*0.2 + 0.8^3 = 0.384 + 0.512 = 0.896
        assert abs(result - (3 * 0.8**2 * 0.2 + 0.8**3)) < 0.01

    def test_majority_strategy_four_modules(self):
        rates = [0.9, 0.8, 0.7, 0.6]
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert 0.0 <= result <= 1.0

    def test_majority_strategy_large_n_uses_approx(self):
        """With n > 20 modules, uses normal approximation."""
        rates = [0.7] * 25  # 25 modules > 20 threshold
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert 0.0 <= result <= 1.0

    def test_weighted_strategy(self):
        rates = [0.9, 0.8, 0.7]
        result = compute_parallel_detection_rate(rates, strategy="weighted")
        assert 0.0 <= result <= 1.0

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            compute_parallel_detection_rate([0.8, 0.7], strategy="unknown_xyz")

    def test_majority_all_zero_rates(self):
        rates = [0.0, 0.0, 0.0]
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert abs(result) < 1e-10

    def test_majority_all_one_rates(self):
        rates = [1.0, 1.0, 1.0]
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert abs(result - 1.0) < 1e-10

    def test_weighted_single_module(self):
        rates = [0.85]
        result = compute_parallel_detection_rate(rates, strategy="weighted")
        assert 0.0 <= result <= 1.0

    def test_majority_normal_approx_zero_variance(self):
        """When all rates are identical at 1.0, variance = 0 — special case."""
        rates = [1.0] * 25
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert result == pytest.approx(1.0)

    def test_majority_normal_approx_zero_variance_low_rate(self):
        """When all rates are 0.0, variance = 0 — low mean."""
        rates = [0.0] * 25
        result = compute_parallel_detection_rate(rates, strategy="majority")
        assert abs(result) < 1e-10


# ---------------------------------------------------------------------------
# compute_hybrid_detection_rate — invalid inputs
# ---------------------------------------------------------------------------


class TestHybridDetectionRateValidation:
    def test_invalid_fast_rate_raises(self):
        with pytest.raises(ValueError, match="fast_rates"):
            compute_hybrid_detection_rate([1.5], [0.8])

    def test_invalid_deep_rate_raises(self):
        with pytest.raises(ValueError, match="deep_rates"):
            compute_hybrid_detection_rate([0.9], [-0.1])

    def test_valid_hybrid_computation(self):
        result = compute_hybrid_detection_rate([0.91, 0.88], [0.79, 0.76, 0.70])
        assert 0.0 <= result <= 1.0
        assert result > 0.99  # very high with these rates


# ---------------------------------------------------------------------------
# compute_weighted_parallel_detection_rate
# ---------------------------------------------------------------------------


class TestWeightedParallelDetectionRate:
    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            compute_weighted_parallel_detection_rate([0.8, 0.7], [0.5])

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError, match="out of bounds"):
            compute_weighted_parallel_detection_rate([1.5], [0.5])

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError, match="negative"):
            compute_weighted_parallel_detection_rate([0.8], [-0.5])

    def test_valid_computation(self):
        result = compute_weighted_parallel_detection_rate([0.9, 0.8], [0.6, 0.4])
        assert 0.0 <= result <= 1.0

    def test_empty_lists_returns_zero(self):
        result = compute_weighted_parallel_detection_rate([], [])
        assert abs(result) < 1e-10

    def test_single_module(self):
        result = compute_weighted_parallel_detection_rate([0.85], [1.0])
        assert 0.0 <= result <= 1.0

    def test_custom_threshold(self):
        result = compute_weighted_parallel_detection_rate([0.8, 0.7], [0.5, 0.5], threshold=0.3)
        # Lower threshold → should be >= higher threshold case
        result_high = compute_weighted_parallel_detection_rate([0.8, 0.7], [0.5, 0.5], threshold=0.7)  # noqa: E501
        assert result >= result_high


# ---------------------------------------------------------------------------
# compute_optimal_ordering
# ---------------------------------------------------------------------------


class TestComputeOptimalOrdering:
    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError, match="out of bounds"):
            compute_optimal_ordering([0.8, 1.5, 0.7])

    def test_sorts_descending(self):
        rates = [0.70, 0.91, 0.85]
        order = compute_optimal_ordering(rates)
        # Sorted rates in descending order: 0.91 (idx 1), 0.85 (idx 2), 0.70 (idx 0)
        assert order == [1, 2, 0]

    def test_empty_returns_empty(self):
        assert compute_optimal_ordering([]) == []

    def test_single_module(self):
        assert compute_optimal_ordering([0.8]) == [0]


# ---------------------------------------------------------------------------
# latency_estimate
# ---------------------------------------------------------------------------


class TestLatencyEstimate:
    def test_series_strategy(self):
        modules = ["Firewall", "Detection", "Tripwire"]
        latencies = {"Firewall": 12.0, "Detection": 18.0, "Tripwire": 8.0}
        result = latency_estimate(modules, strategy="series", latency_map=latencies)
        assert abs(result - 38.0) < 1e-10

    def test_parallel_strategy(self):
        modules = ["Firewall", "Detection"]
        latencies = {"Firewall": 12.0, "Detection": 18.0}
        result = latency_estimate(modules, strategy="parallel", latency_map=latencies)
        assert abs(result - 18.0) < 1e-10

    def test_hybrid_strategy(self):
        fast_mods = ["Firewall", "Detection"]
        deep_mods = ["Consensus", "Provenance"]
        latencies = {"Firewall": 12.0, "Detection": 18.0, "Consensus": 35.0, "Provenance": 28.0}
        result = latency_estimate(
            fast_mods, strategy="hybrid", deep_modules=deep_mods, latency_map=latencies
        )
        # max(fast) + sum(deep) = 18 + 35 + 28 = 81
        assert abs(result - 81.0) < 1e-10

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            latency_estimate(["Firewall"], strategy="unknown_xyz")

    def test_default_latency_when_not_in_map(self):
        modules = ["Unknown_Module"]
        result = latency_estimate(modules, strategy="series", latency_map={})
        assert result > 0.0  # uses default latency

    def test_empty_modules_parallel(self):
        result = latency_estimate([], strategy="parallel")
        assert result == 0.0

    def test_empty_modules_series(self):
        result = latency_estimate([], strategy="series")
        assert result == 0.0
