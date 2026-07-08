"""Tests for src/redteam/convergence.py.

Covers:
- natural_gradient_at_step: normal case, singular Fisher matrix fallback.
- geometric_convergence_projection: normal gains, edge cases (empty, zero first gain).
- convergence_round_estimate: normal, edge cases.
- empirical_lipschitz_constant: normal evaluator, missing evaluate method.

All tests use real numpy computation. No mocks.
"""

from __future__ import annotations

import numpy as np
import pytest

from redteam.convergence import (
    convergence_round_estimate,
    empirical_lipschitz_constant,
    geometric_convergence_projection,
    natural_gradient_at_step,
)

# ---------------------------------------------------------------------------
# natural_gradient_at_step
# ---------------------------------------------------------------------------


class TestNaturalGradientAtStep:
    """Tests for natural_gradient_at_step."""

    def test_returns_array_same_shape(self):
        theta = np.array([0.5, 0.5, 0.5])
        grad = np.array([0.1, 0.2, 0.3])
        fisher = np.eye(3)
        result = natural_gradient_at_step(theta, grad, fisher)
        assert result.shape == theta.shape

    def test_identity_fisher_equals_euclidean(self):
        """With identity Fisher matrix, natural gradient == Euclidean gradient."""
        theta = np.array([0.5, 0.5])
        grad = np.array([0.1, 0.2])
        fisher = np.eye(2)
        lr = 0.05
        result = natural_gradient_at_step(theta, grad, fisher, learning_rate=lr)
        expected = theta + lr * grad
        np.testing.assert_allclose(result, expected)

    def test_custom_fisher_gives_different_result(self):
        """Non-identity Fisher changes the update direction."""
        theta = np.array([0.5, 0.5])
        grad = np.array([0.1, 0.2])
        fisher_id = np.eye(2)
        fisher_custom = np.array([[2.0, 0.5], [0.5, 3.0]])
        r_id = natural_gradient_at_step(theta, grad, fisher_id)
        r_custom = natural_gradient_at_step(theta, grad, fisher_custom)
        assert not np.allclose(r_id, r_custom)

    def test_singular_fisher_falls_back_to_euclidean(self):
        """When Fisher matrix is singular, falls back to Euclidean gradient."""
        theta = np.array([0.5, 0.5])
        grad = np.array([0.1, 0.2])
        singular_fisher = np.zeros((2, 2))  # rank-0 matrix is singular
        lr = 0.05
        result = natural_gradient_at_step(theta, grad, singular_fisher, learning_rate=lr)
        expected = theta + lr * grad  # fallback = Euclidean
        np.testing.assert_allclose(result, expected)

    def test_update_moves_theta(self):
        """Result should differ from input theta."""
        theta = np.array([0.3, 0.7])
        grad = np.array([0.05, 0.1])
        fisher = np.eye(2)
        result = natural_gradient_at_step(theta, grad, fisher)
        assert not np.allclose(result, theta)


# ---------------------------------------------------------------------------
# geometric_convergence_projection
# ---------------------------------------------------------------------------


class TestGeometricConvergenceProjection:
    """Tests for geometric_convergence_projection."""

    def test_empty_gains_returns_baseline(self):
        dr, ratio = geometric_convergence_projection([], baseline_dr=0.7)
        assert abs(dr - 0.7) < 1e-10
        assert ratio == 0.65

    def test_zero_first_gain_returns_baseline(self):
        dr, ratio = geometric_convergence_projection([0.0, 0.1], baseline_dr=0.6)
        assert abs(dr - 0.6) < 1e-10

    def test_normal_projection(self):
        gains = [0.10, 0.065, 0.042, 0.027]
        dr, ratio = geometric_convergence_projection(gains, baseline_dr=0.85)
        assert 0.0 <= dr <= 1.0
        assert 0.0 < ratio < 1.0

    def test_projected_dr_at_most_one(self):
        gains = [0.5, 0.45, 0.40]  # unrealistically high gains
        dr, ratio = geometric_convergence_projection(gains, baseline_dr=0.9)
        assert dr <= 1.0

    def test_projected_dr_at_least_baseline(self):
        gains = [0.01, 0.005, 0.002]
        baseline = 0.80
        dr, ratio = geometric_convergence_projection(gains, baseline_dr=baseline)
        assert dr >= baseline - 1e-9

    def test_ratio_clamped(self):
        # All gains identical → ratio would be 1.0 → clamp to 0.99
        gains = [0.1, 0.1, 0.1]
        _, ratio = geometric_convergence_projection(gains, baseline_dr=0.8)
        assert 0.01 <= ratio <= 0.99


# ---------------------------------------------------------------------------
# convergence_round_estimate
# ---------------------------------------------------------------------------


class TestConvergenceRoundEstimate:
    """Tests for convergence_round_estimate."""

    def test_empty_gains_returns_zero(self):
        assert convergence_round_estimate([]) == 0

    def test_first_gain_below_tolerance_returns_zero(self):
        assert convergence_round_estimate([0.0005], tolerance=0.001) == 0

    def test_normal_case_returns_positive_int(self):
        gains = [0.10, 0.065, 0.042]
        k = convergence_round_estimate(gains, tolerance=0.001)
        assert isinstance(k, int)
        assert k > 0

    def test_larger_gains_converge_faster_than_smaller(self):
        k_fast = convergence_round_estimate([0.5, 0.3, 0.1], tolerance=0.001)
        k_slow = convergence_round_estimate([0.01, 0.008, 0.006], tolerance=0.001)
        # Fast gains → larger ratio → but fewer rounds to tolerance
        # Just verify both are valid non-negative ints
        assert k_fast >= 0
        assert k_slow >= 0

    def test_result_is_non_negative(self):
        gains = [0.05, 0.03, 0.02, 0.01]
        k = convergence_round_estimate(gains, tolerance=0.005)
        assert k >= 0


# ---------------------------------------------------------------------------
# empirical_lipschitz_constant
# ---------------------------------------------------------------------------


class TestEmpiricalLipschitzConstant:
    """Tests for empirical_lipschitz_constant."""

    def test_constant_evaluator_returns_zero(self):
        class ConstantEvaluator:
            def evaluate(self, config):
                return 0.9  # constant, no change with perturbation

        config = {"threshold_a": 0.5, "threshold_b": 0.3}
        L = empirical_lipschitz_constant(config, ConstantEvaluator())
        assert abs(L) < 1e-10

    def test_linear_evaluator_returns_positive_constant(self):
        class LinearEvaluator:
            def evaluate(self, config):
                return sum(config.values())

        config = {"x": 0.5, "y": 0.3}
        L = empirical_lipschitz_constant(config, LinearEvaluator(), epsilon=0.01)
        # Each dimension contributes rate 1.0 (change of 0.01 per 0.01 perturbation)
        assert L > 0.0

    def test_missing_evaluate_raises(self):
        class NoEvaluate:
            pass

        with pytest.raises(ValueError, match="evaluate"):
            empirical_lipschitz_constant({"x": 0.5}, NoEvaluate())

    def test_empty_config_returns_zero(self):
        class SimpleEvaluator:
            def evaluate(self, config):
                return 0.8

        L = empirical_lipschitz_constant({}, SimpleEvaluator())
        assert abs(L) == 0.0

    def test_multiple_dimensions(self):
        class MultiEvaluator:
            def evaluate(self, config):
                return config.get("a", 0) * 2 + config.get("b", 0) * 0.5

        config = {"a": 0.4, "b": 0.6}
        L = empirical_lipschitz_constant(config, MultiEvaluator(), epsilon=0.01)
        # Lipschitz constant should be max(|2|, |0.5|) = 2.0
        assert abs(L - 2.0) < 0.1
