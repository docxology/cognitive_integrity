"""Tests for trust calculus."""

import numpy as np
import pytest

from src import TrustCalculus, TrustConfig, TrustMatrix


class TestTrustConfig:
    """Tests for TrustConfig validation."""

    def test_valid_config(self):
        """Config with weights summing to 1.0 is valid."""
        config = TrustConfig(alpha=0.3, beta=0.4, gamma=0.3, decay=0.9)
        assert np.isclose(config.alpha + config.beta + config.gamma, 1.0)

    def test_invalid_weights_raises(self):
        """Config with weights not summing to 1.0 raises."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            TrustConfig(alpha=0.5, beta=0.5, gamma=0.5)

    def test_invalid_decay_raises(self):
        """Decay outside (0,1) raises."""
        with pytest.raises(ValueError, match="Decay"):
            TrustConfig(alpha=0.3, beta=0.4, gamma=0.3, decay=1.5)


class TestTrustCalculus:
    """Tests for TrustCalculus."""

    def test_compute_trust_weighted(self):
        """Trust is weighted sum of components."""
        calc = TrustCalculus(TrustConfig(alpha=0.5, beta=0.3, gamma=0.2))
        trust = calc.compute_trust(base_trust=1.0, reputation=0.5, context_trust=0.0)
        expected = 0.5 * 1.0 + 0.3 * 0.5 + 0.2 * 0.0
        assert np.isclose(trust, expected)

    def test_delegate_trust_bounded(self):
        """Delegated trust cannot exceed min of inputs."""
        calc = TrustCalculus()
        delegated = calc.delegate_trust(source_trust=0.9, target_trust=0.7, depth=1)
        # min(0.9, 0.7) * 0.8^1 = 0.7 * 0.8 = 0.56 (δ=0.8 per paper)
        assert delegated <= 0.7
        assert np.isclose(delegated, 0.56)

    def test_delegate_trust_decays_with_depth(self):
        """Trust decays exponentially with depth."""
        calc = TrustCalculus(TrustConfig(decay=0.9))
        depth_1 = calc.delegate_trust(1.0, 1.0, depth=1)
        depth_2 = calc.delegate_trust(1.0, 1.0, depth=2)
        depth_3 = calc.delegate_trust(1.0, 1.0, depth=3)

        assert np.isclose(depth_1, 0.9)
        assert np.isclose(depth_2, 0.81)
        assert np.isclose(depth_3, 0.729)

    def test_path_trust_composition(self):
        """Path trust is bounded by minimum link."""
        calc = TrustCalculus(TrustConfig(decay=0.9))
        path = [0.9, 0.8, 0.7]  # Trust along path
        result = calc.compute_path_trust(path)

        # Should be bounded by min(path) and decay
        assert result <= min(path)
        assert result > 0
        # Exact value: T = min(path) * delta**d = 0.7 * 0.9**3
        assert result == pytest.approx(0.7 * 0.9**3)

    def test_path_trust_decay_applied_once_for_total_depth(self):
        """A k-hop uniform chain decays as delta**k, not delta**(k(k+1)/2)
        from per-hop compounding (Definition 4.4, P2-35)."""
        calc = TrustCalculus(TrustConfig(decay=0.9))
        result = calc.compute_path_trust([1.0, 1.0, 1.0, 1.0])
        # 4 edges -> delta**4 = 0.9**4 = 0.6561 (per-hop compounding would
        # give delta**(1+2+3) = delta**6 = 0.5314).
        assert result == pytest.approx(0.9**4)

    def test_empty_path_returns_zero(self):
        """Empty path returns zero trust."""
        calc = TrustCalculus()
        assert calc.compute_path_trust([]) == 0.0


class TestTrustMatrix:
    """Tests for TrustMatrix."""

    def test_self_trust_maximal(self):
        """Self-trust is always 1.0."""
        matrix = TrustMatrix(n_agents=5)
        for i in range(5):
            assert matrix.get_trust(i, i) == 1.0

    def test_initial_trust_neutral(self):
        """Initial inter-agent trust is neutral (0.5)."""
        matrix = TrustMatrix(n_agents=3)
        # With equal weights 0.33 each and all components 0.5
        trust = matrix.get_trust(0, 1)
        assert 0.4 < trust < 0.6  # Approximately 0.5

    def test_reputation_update(self):
        """Reputation updates affect trust."""
        matrix = TrustMatrix(n_agents=2)
        initial = matrix.get_trust(0, 1)

        # Update with positive outcome
        matrix.update_reputation(0, 1, outcome=1.0, learning_rate=0.5)
        after = matrix.get_trust(0, 1)

        assert after > initial

    def test_delegation_path(self):
        """Delegation path computes correct trust."""
        matrix = TrustMatrix(n_agents=4)
        # Set up known trust values
        matrix._base[0, 1] = 0.9
        matrix._base[1, 2] = 0.8
        matrix._base[2, 3] = 0.7

        # Path trust should decay
        path_trust = matrix.get_delegation_trust([0, 1, 2, 3])
        direct_trust = matrix.get_trust(0, 1)

        assert path_trust < direct_trust

    def test_delegation_short_path_yields_zero(self):
        """A degenerate single-node path must not claim maximal trust; it
        returns 0.0 (P2-35, mirrors Part 1 P1-20)."""
        matrix = TrustMatrix(n_agents=4)
        assert matrix.get_delegation_trust([0]) == 0.0
        assert matrix.get_delegation_trust([]) == 0.0

    def test_to_matrix(self):
        """to_matrix returns correct shape."""
        matrix = TrustMatrix(n_agents=5)
        result = matrix.to_matrix()

        assert result.shape == (5, 5)
        # Diagonal should be 1.0
        assert np.allclose(np.diag(result), 1.0)


class TestTrustBoundedness:
    """Tests for Theorem 3.1: Trust Boundedness."""

    def test_trust_never_amplifies(self):
        """Trust cannot amplify through delegation."""
        calc = TrustCalculus(TrustConfig(decay=0.95))

        # Even with high trust values
        for _ in range(100):
            t1 = np.random.uniform(0, 1)
            t2 = np.random.uniform(0, 1)
            delegated = calc.delegate_trust(t1, t2, depth=1)

            assert delegated <= min(t1, t2)

    def test_deep_delegation_converges_to_zero(self):
        """Deep delegation chains converge to zero trust."""
        calc = TrustCalculus(TrustConfig(decay=0.9))

        # Even with perfect trust at each hop
        trust_d10 = calc.delegate_trust(1.0, 1.0, depth=10)
        trust_d50 = calc.delegate_trust(1.0, 1.0, depth=50)
        trust_d100 = calc.delegate_trust(1.0, 1.0, depth=100)

        assert trust_d10 < 0.35  # 0.9^10 ≈ 0.349
        assert trust_d50 < 0.01  # 0.9^50 ≈ 0.005
        assert trust_d100 < 0.0001  # Effectively zero


class TestReputationDecay:
    """Tests for reputation decay over time."""

    def test_reputation_decays_with_time(self):
        """Reputation decay causes recent interactions to dominate."""
        from src import ReputationTracker

        # With decay, recent interactions should have more weight than old ones
        tracker = ReputationTracker(decay_rate=0.5)  # Higher decay rate

        # Old good interaction
        tracker.record_interaction("a", "b", outcome=1.0, timestamp=0.0)
        # Recent bad interaction
        tracker.record_interaction("a", "b", outcome=0.0, timestamp=10.0)

        # At time 10, the recent bad should dominate due to decay of old
        rep_at_10 = tracker.get_reputation("a", "b", current_time=10.0)
        # Old interaction weight: exp(-0.5 * 10) = exp(-5) ~= 0.007
        # New interaction weight: exp(-0.5 * 0) = 1.0
        # Weighted average ~= (0.007 * 1.0 + 1.0 * 0.0) / (0.007 + 1.0) ~= 0.007
        # So recent 0.0 should dominate
        assert rep_at_10 < 0.1

        # Compare with no decay - both should have equal weight
        tracker_no_decay = ReputationTracker(decay_rate=0.0)
        tracker_no_decay.record_interaction("a", "b", outcome=1.0, timestamp=0.0)
        tracker_no_decay.record_interaction("a", "b", outcome=0.0, timestamp=10.0)

        rep_no_decay = tracker_no_decay.get_reputation("a", "b", current_time=10.0)
        # With no decay, should be average of 1.0 and 0.0 = 0.5
        assert abs(rep_no_decay - 0.5) < 0.01

    def test_recent_interactions_weighted_more(self):
        """Recent interactions have more weight than old ones."""
        from src import ReputationTracker

        tracker = ReputationTracker(decay_rate=0.1)

        # Old positive interaction
        tracker.record_interaction("a", "b", outcome=1.0, timestamp=0.0)
        # Recent negative interaction
        tracker.record_interaction("a", "b", outcome=0.0, timestamp=9.0)

        # At time 10, recent negative should dominate
        rep = tracker.get_reputation("a", "b", current_time=10.0)
        assert rep < 0.5  # Should be closer to recent 0.0 than old 1.0

    def test_no_interactions_returns_default(self):
        """No recorded interactions returns default reputation."""
        from src import ReputationTracker

        tracker = ReputationTracker()
        rep = tracker.get_reputation("unknown", "unknown", current_time=0.0)

        assert rep == 0.5  # Neutral default

    def test_decay_rate_zero_no_decay(self):
        """Zero decay rate means no decay."""
        from src import ReputationTracker

        tracker = ReputationTracker(decay_rate=0.0)
        tracker.record_interaction("a", "b", outcome=0.8, timestamp=0.0)

        early = tracker.get_reputation("a", "b", current_time=1.0)
        late = tracker.get_reputation("a", "b", current_time=100.0)

        assert np.isclose(early, late)


class TestContextAwareTrustBoosting:
    """Tests for context-aware trust boosting."""

    def test_context_boost_increases_trust(self):
        """Relevant context boosts trust."""
        from src import ContextAwareTrust

        cat = ContextAwareTrust()

        # Register expertise
        cat.register_expertise("agent-1", "security", level=0.9)

        # Boost for security context
        base_trust = 0.5
        boosted = cat.boost_for_context(
            agent_id="agent-1", base_trust=base_trust, context="security"
        )

        assert boosted > base_trust

    def test_no_expertise_no_boost(self):
        """Unknown context provides no boost."""
        from src import ContextAwareTrust

        cat = ContextAwareTrust()
        cat.register_expertise("agent-1", "security", level=0.9)

        base_trust = 0.5
        boosted = cat.boost_for_context(
            agent_id="agent-1",
            base_trust=base_trust,
            context="cooking",  # No expertise registered
        )

        assert boosted == base_trust

    def test_boost_is_bounded(self):
        """Trust boost cannot exceed 1.0."""
        from src import ContextAwareTrust

        cat = ContextAwareTrust()
        cat.register_expertise("agent-1", "security", level=1.0)

        boosted = cat.boost_for_context(
            agent_id="agent-1", base_trust=0.95, context="security"
        )

        assert boosted <= 1.0

    def test_multiple_contexts(self):
        """Agents can have expertise in multiple contexts."""
        from src import ContextAwareTrust

        cat = ContextAwareTrust()
        cat.register_expertise("agent-1", "security", level=0.9)
        cat.register_expertise("agent-1", "networking", level=0.7)

        security_boost = cat.boost_for_context("agent-1", 0.5, "security")
        network_boost = cat.boost_for_context("agent-1", 0.5, "networking")

        # Higher expertise should give higher boost
        assert security_boost > network_boost

    def test_context_similarity(self):
        """Similar contexts can provide partial boost."""
        from src import ContextAwareTrust

        cat = ContextAwareTrust()
        cat.register_expertise("agent-1", "security", level=0.9)
        cat.register_context_similarity("cybersecurity", "security", similarity=0.8)

        # Related context gets partial boost
        boosted = cat.boost_for_context("agent-1", 0.5, "cybersecurity")

        assert boosted > 0.5  # Some boost
        assert boosted < cat.boost_for_context(
            "agent-1", 0.5, "security"
        )  # Less than exact match


class TestTrustMatrixWithDecay:
    """Tests for TrustMatrix with time-based decay."""

    def test_matrix_reputation_decay(self):
        """TrustMatrix integrates with reputation decay."""
        from src import TrustMatrixWithDecay

        matrix = TrustMatrixWithDecay(n_agents=3, decay_rate=0.5)

        # Record old good interaction
        matrix.record_interaction(0, 1, outcome=1.0, timestamp=0.0)
        # Record recent bad interaction
        matrix.record_interaction(0, 1, outcome=0.0, timestamp=10.0)

        # At time 10, the recent bad interaction should dominate
        trust_t10 = matrix.get_trust_at_time(0, 1, current_time=10.0)

        # With decay rate 0.5:
        # Old interaction (t=0): weight = exp(-0.5 * 10) = exp(-5) ~= 0.007
        # New interaction (t=10): weight = exp(-0.5 * 0) = 1.0
        # Reputation ~= (0.007 * 1.0 + 1.0 * 0.0) / (0.007 + 1.0) ~= 0.007

        # Trust uses reputation component, so should be lower than with good reputation
        # Compare to trust with all defaults (0.5 reputation)
        default_trust = matrix.get_trust(0, 1)

        # The bad reputation (near 0) should result in lower trust
        assert trust_t10 < default_trust

    def test_matrix_context_boosting(self):
        """TrustMatrix integrates with context boosting."""
        from src import TrustMatrixWithDecay

        matrix = TrustMatrixWithDecay(n_agents=3, decay_rate=0.0)
        matrix.register_agent_expertise(1, "security", 0.9)

        # Trust without context
        base_trust = matrix.get_trust(0, 1)

        # Trust with security context
        context_trust = matrix.get_trust_with_context(0, 1, context="security")

        assert context_trust > base_trust
