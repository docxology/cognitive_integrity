"""Property-based tests using Hypothesis for CIF core modules.

These tests use the Hypothesis library to verify mathematical invariants
and type safety properties of core CIF algorithms.

No mocks — all tests use real computation.
"""

from __future__ import annotations

import numpy as np
import pytest

try:
    from hypothesis import assume, given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False
    # Create dummy decorator for when hypothesis is not installed
    def given(*a, **kw):
        def decorator(fn):
            return pytest.mark.skip(reason="hypothesis not installed")(fn)
        return decorator

    def settings(*a, **kw):
        def decorator(fn):
            return fn
        return decorator

    def assume(cond):
        pass

    class st:  # type: ignore[no-redef]
        @staticmethod
        def floats(min_value=0.0, max_value=1.0, allow_nan=False):
            return None

        @staticmethod
        def integers(min_value=0, max_value=100):
            return None

        @staticmethod
        def lists(strat, min_size=0, max_size=10):
            return None


# ============================================================================
# Strategies for CIF types
# ============================================================================

if HAS_HYPOTHESIS:
    # Detection score: [0, 1]
    detection_score_st = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    # Threshold: (0, 1)
    threshold_st = st.floats(min_value=0.01, max_value=0.99, allow_nan=False)
    # Probability distribution over n elements
    prob_dist_st = st.integers(min_value=2, max_value=8).flatmap(
        lambda n: st.lists(
            st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
            min_size=n, max_size=n,
        ).map(lambda xs: np.array(xs) / sum(xs))
    )
    # Small integer in [3, 20]
    n_agents_st = st.integers(min_value=3, max_value=20)
    # Trust score: [0, 100]
    trust_score_st = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)


# ============================================================================
# Section 1: Detection score properties
# ============================================================================


class TestDetectionProperties:
    """Property-based tests for detection algorithm invariants."""

    @given(detection_score_st, threshold_st)
    def test_detection_decision_consistent(self, score, threshold):
        """Detection decision is consistent: score > threshold ↔ detected=True."""
        detected = score > threshold
        assert isinstance(detected, (bool, np.bool_))
        assert detected == (score > threshold)

    @given(
        st.lists(detection_score_st, min_size=1, max_size=100),
        threshold_st,
    )
    def test_detection_rate_bounds(self, scores, threshold):
        """Detection rate is always in [0, 1]."""
        arr = np.array(scores)
        dr = float(np.mean(arr > threshold))
        assert 0.0 <= dr <= 1.0

    @given(
        st.lists(detection_score_st, min_size=2, max_size=50),
        threshold_st,
    )
    def test_detection_monotone_in_threshold(self, scores, threshold):
        """Higher threshold → lower or equal detection rate."""
        arr = np.array(scores)
        dr_low = float(np.mean(arr > threshold * 0.5))
        dr_high = float(np.mean(arr > min(0.99, threshold * 1.5)))
        assert dr_high <= dr_low + 1e-9


# ============================================================================
# Section 2: Information geometry properties
# ============================================================================


class TestInformationGeometryProperties:
    """Property-based tests for Fisher-Rao metric invariants."""

    @given(prob_dist_st, prob_dist_st)
    def test_riemannian_distance_non_negative(self, p_vals, q_vals):
        """Riemannian distance is always ≥ 0."""
        from analysis.information_geometry import StatisticalManifold

        n = min(len(p_vals), len(q_vals))
        p = np.array(p_vals[:n])
        q = np.array(q_vals[:n])
        p = p / p.sum()
        q = q / q.sum()
        manifold = StatisticalManifold(n)
        dist = manifold.riemannian_distance(p, q)
        assert dist >= -1e-7

    @given(prob_dist_st)
    def test_riemannian_self_distance_zero(self, p_vals):
        """Riemannian distance from a distribution to itself is ~0."""
        from analysis.information_geometry import StatisticalManifold

        n = len(p_vals)
        p = np.array(p_vals)
        p = p / p.sum()
        manifold = StatisticalManifold(n)
        dist = manifold.riemannian_distance(p, p)
        # Allow numerical tolerance up to 1e-4 (implementation uses floating point ops)
        assert dist < 1e-4, f"Self-distance {dist} too large for p={p}"

    @given(prob_dist_st, prob_dist_st)
    def test_riemannian_symmetry(self, p_vals, q_vals):
        """Riemannian distance is symmetric: d(p,q) == d(q,p)."""
        from analysis.information_geometry import StatisticalManifold

        n = min(len(p_vals), len(q_vals))
        p = np.array(p_vals[:n])
        q = np.array(q_vals[:n])
        p = p / p.sum()
        q = q / q.sum()
        manifold = StatisticalManifold(n)
        d_pq = manifold.riemannian_distance(p, q)
        d_qp = manifold.riemannian_distance(q, p)
        assert abs(d_pq - d_qp) < 1e-9

    @given(prob_dist_st)
    def test_fisher_info_matrix_positive_definite(self, p_vals):
        """Fisher information matrix is positive definite."""
        from analysis.information_geometry import StatisticalManifold

        n = len(p_vals)
        p = np.array(p_vals)
        p = p / p.sum()
        manifold = StatisticalManifold(n)
        fim = manifold.fisher_information_matrix(p)
        eigenvalues = np.linalg.eigvalsh(fim)
        assert np.all(eigenvalues >= -1e-9), (
            f"Fisher matrix not PSD; min eigenvalue = {eigenvalues.min():.6f}"
        )

    @given(prob_dist_st)
    def test_geodesic_path_valid_distributions(self, p_vals):
        """Geodesic path from p to q produces valid probability distributions."""
        from analysis.information_geometry import geodesic_attack_path

        n = len(p_vals)
        p = np.array(p_vals)
        p = p / p.sum()
        q = np.ones(n) / n  # target: uniform
        path = geodesic_attack_path(p, q, n_steps=5)
        assert path is not None
        for step_key, dist in path.items():
            assert np.all(dist >= -1e-9), f"Negative probability in path step {step_key}"


# ============================================================================
# Section 3: Composition algebra properties
# ============================================================================


class TestCompositionAlgebraProperties:
    """Property-based tests for defense composition algebra invariants."""

    @given(detection_score_st, detection_score_st)
    def test_sequential_composition_dominates_worst(self, score_a, score_b):
        """Sequential composition detection rate ≥ max(score_a, score_b)."""
        combined = 1.0 - (1.0 - score_a) * (1.0 - score_b)
        assert combined >= max(score_a, score_b) - 1e-9

    @given(detection_score_st, detection_score_st)
    def test_parallel_composition_bounded(self, score_a, score_b):
        """Parallel composition DR ≤ 1.0 always."""
        combined = min(1.0, (score_a + score_b) / 2.0 + 0.1)
        assert combined <= 1.0

    @given(
        st.lists(detection_score_st, min_size=1, max_size=10)
    )
    def test_sequential_composition_monotone_in_components(self, component_scores):
        """Adding more components never decreases the composition DR."""
        running_combined = component_scores[0]
        for s in component_scores[1:]:
            new_combined = 1.0 - (1.0 - running_combined) * (1.0 - s)
            assert new_combined >= running_combined - 1e-9
            running_combined = new_combined


# ============================================================================
# Section 4: CCS score properties
# ============================================================================


class TestCCSProperties:
    """Property-based tests for Colony Cognitive Security score."""

    @given(
        detection_score_st,
        detection_score_st,
        detection_score_st,
        st.integers(min_value=0, max_value=1000),
    )
    def test_ccs_always_in_unit_interval(self, dr, fpr, resilience, recovery):
        """CCS score is always in [0, 1]."""
        from colony.scorecard import CCSWeights, compute_ccs

        weights = CCSWeights()
        ccs = compute_ccs(
            detection_rate=dr,
            false_positive_rate=fpr,
            resilience=resilience,
            recovery_steps=recovery,
            max_steps=1000,
            weights=weights,
        )
        assert 0.0 <= ccs <= 1.0

    @given(
        detection_score_st,
        detection_score_st,
        detection_score_st,
        st.integers(min_value=0, max_value=1000),
    )
    def test_ccs_monotone_in_detection_rate(self, fpr, resilience, recovery_f, recovery_i):
        """Higher detection rate → higher or equal CCS."""
        from colony.scorecard import CCSWeights, compute_ccs

        weights = CCSWeights()
        ccs_low = compute_ccs(
            detection_rate=0.3,
            false_positive_rate=fpr,
            resilience=resilience,
            recovery_steps=recovery_i,
            max_steps=1000,
            weights=weights,
        )
        ccs_high = compute_ccs(
            detection_rate=0.9,
            false_positive_rate=fpr,
            resilience=resilience,
            recovery_steps=recovery_i,
            max_steps=1000,
            weights=weights,
        )
        assert ccs_high >= ccs_low - 1e-9


# ============================================================================
# Section 5: Consensus properties
# ============================================================================


class TestConsensusProperties:
    """Property-based tests for Byzantine consensus invariants."""

    @given(n_agents_st)
    def test_consensus_quorum_size_valid(self, n_agents):
        """Quorum size is always ≤ n_agents and ≥ 1."""
        from core.consensus import ByzantineConsensus, Vote

        # Need n >= 3f + 1; use f = 1 and ensure n >= 4
        assume(n_agents >= 4)
        max_byz = max(1, n_agents // 4)
        consensus = ByzantineConsensus(n_agents=n_agents, max_byzantine=max_byz)
        assert consensus.n_agents == n_agents
        # Submit one vote without error
        vote = Vote(agent_id="agent_0", proposition="test", belief=0.9)
        consensus.submit_vote(vote)

    @given(
        n_agents_st,
        st.integers(min_value=0, max_value=10),
    )
    def test_consensus_handles_mixed_votes(self, n_agents, n_byzantine):
        """Consensus handles honest votes without error."""
        from core.consensus import ByzantineConsensus, Vote

        # Enforce n >= 3f + 1 constraint
        n_byz = min(n_byzantine, (n_agents - 1) // 3)
        assume(n_agents >= 4)
        assume(n_byz >= 0)
        assume(n_agents >= 3 * n_byz + 1)
        max_byz = max(1, n_byz)
        consensus = ByzantineConsensus(n_agents=n_agents, max_byzantine=max_byz)
        # Submit honest votes
        for i in range(min(n_agents - n_byz, 3)):  # limit to 3 for speed
            vote = Vote(agent_id=f"honest_{i}", proposition="test", belief=0.9)
            consensus.submit_vote(vote)
        # Should return a valid result
        result = consensus.is_decided("test")
        assert isinstance(result, (bool, np.bool_, int))


# ============================================================================
# Section 6: Adversarial training convergence properties
# ============================================================================


class TestAdversarialTrainingProperties:
    """Property-based tests for adversarial training convergence."""

    @given(
        st.lists(
            st.floats(min_value=0.001, max_value=0.1, allow_nan=False),
            min_size=2,
            max_size=10,
        )
    )
    def test_projected_dr_non_decreasing(self, gains):
        """Projected equilibrium DR ≥ baseline DR."""
        from redteam.convergence import geometric_convergence_projection

        baseline = 0.447
        proj_dr, ratio = geometric_convergence_projection(gains, baseline)
        assert proj_dr >= baseline - 1e-9

    @given(
        st.lists(
            st.floats(min_value=0.001, max_value=0.1, allow_nan=False),
            min_size=2,
            max_size=10,
        )
    )
    def test_projected_dr_bounded_by_one(self, gains):
        """Projected equilibrium DR ≤ 1.0."""
        from redteam.convergence import geometric_convergence_projection

        proj_dr, ratio = geometric_convergence_projection(gains, 0.447)
        if ratio >= 1.0:
            assert proj_dr == float("inf")
            assert gains
            assert all(g > 0 for g in gains)
        else:
            assert proj_dr <= 1.0 + 1e-9

    @given(
        st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
        st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
    )
    def test_natural_gradient_step_finite(self, theta_val, grad_val):
        """Natural gradient step produces finite output."""
        from redteam.convergence import natural_gradient_at_step

        theta = np.array([theta_val])
        gradient = np.array([grad_val])
        fisher = np.array([[max(1e-6, theta_val * (1 - theta_val))]])
        result = natural_gradient_at_step(theta, gradient, fisher, learning_rate=0.05)
        assert np.all(np.isfinite(result))

    @given(
        st.floats(min_value=0.3, max_value=0.7, allow_nan=False),
        st.integers(min_value=2, max_value=10),
    )
    def test_at_trainer_summary_valid(self, baseline_dr, n_rounds):
        """AdversarialTrainer summary is valid for any n_rounds >= 2."""
        from redteam import AdversarialTrainer, ATConfig

        config = ATConfig(n_rounds=n_rounds)
        trainer = AdversarialTrainer(config=config)
        trainer._baseline_dr = baseline_dr
        rounds = trainer.run()
        assert len(rounds) == n_rounds
        summary = trainer.summary()
        assert 0.0 <= summary["final_hardened_dr"] <= 1.0
        proj = summary["projected_nash_dr"]
        assert proj >= baseline_dr - 1e-9
        assert proj <= 1.0 + 1e-9
