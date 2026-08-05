"""Tests for belief sandboxing."""

import time
from datetime import datetime, timedelta

import pytest

from src import (
    Belief,
    BeliefPartition,
    BeliefState,
    PromotionCriteria,
    SandboxConfig,
    SandboxManager,
)


class TestBelief:
    """Tests for Belief dataclass."""

    def test_belief_creation(self):
        """Beliefs have id, content, confidence, and timestamp."""
        belief = Belief(belief_id="b1", content="The sky is blue", confidence=0.9)
        assert belief.belief_id == "b1"
        assert belief.content == "The sky is blue"
        assert belief.confidence == 0.9
        assert isinstance(belief.created_at, datetime)

    def test_belief_with_source(self):
        """Beliefs can track their source."""
        belief = Belief(
            belief_id="b1", content="Fact", confidence=0.8, source_agent="agent-1"
        )
        assert belief.source_agent == "agent-1"


class TestBeliefState:
    """Tests for BeliefState with partitions."""

    def test_initial_state_empty(self):
        """Initial state has empty partitions."""
        state = BeliefState()
        assert len(state.verified) == 0
        assert len(state.provisional) == 0

    def test_add_verified_belief(self):
        """Verified beliefs go to verified partition."""
        state = BeliefState()
        belief = Belief("b1", "Verified fact", 0.95)

        state.add_verified(belief)

        assert "b1" in state.verified
        assert state.get_partition("b1") == BeliefPartition.VERIFIED

    def test_add_provisional_belief(self):
        """Provisional beliefs go to provisional partition."""
        state = BeliefState()
        belief = Belief("b1", "Unverified claim", 0.6)

        state.add_provisional(belief)

        assert "b1" in state.provisional
        assert state.get_partition("b1") == BeliefPartition.PROVISIONAL

    def test_get_belief(self):
        """Can retrieve beliefs from either partition."""
        state = BeliefState()

        verified = Belief("v1", "Verified", 0.9)
        provisional = Belief("p1", "Provisional", 0.5)

        state.add_verified(verified)
        state.add_provisional(provisional)

        assert state.get_belief("v1") is not None
        assert state.get_belief("p1") is not None
        assert state.get_belief("unknown") is None

    def test_remove_belief(self):
        """Beliefs can be removed from state."""
        state = BeliefState()
        belief = Belief("b1", "Temporary", 0.5)

        state.add_provisional(belief)
        assert "b1" in state.provisional

        state.remove("b1")
        assert "b1" not in state.provisional

    def test_promote_belief(self):
        """Beliefs can be promoted from provisional to verified."""
        state = BeliefState()
        belief = Belief("b1", "Promotable", 0.6)

        state.add_provisional(belief)
        assert state.get_partition("b1") == BeliefPartition.PROVISIONAL

        state.promote("b1")
        assert state.get_partition("b1") == BeliefPartition.VERIFIED
        assert "b1" not in state.provisional
        assert "b1" in state.verified

    def test_demote_belief(self):
        """Beliefs can be demoted from verified to provisional."""
        state = BeliefState()
        belief = Belief("b1", "Demotable", 0.9)

        state.add_verified(belief)
        state.demote("b1")

        assert state.get_partition("b1") == BeliefPartition.PROVISIONAL

    def test_get_partition_nonexistent_returns_none(self):
        """get_partition on an unknown belief_id returns None."""
        state = BeliefState()
        assert state.get_partition("nonexistent") is None

    def test_remove_nonexistent_returns_false_and_no_op(self):
        """remove() on an unknown belief_id returns False and leaves partitions unchanged."""
        state = BeliefState()
        belief = Belief("b1", "Kept", 0.5)
        state.add_verified(belief)

        assert state.remove("nonexistent") is False
        assert "b1" in state.verified

    def test_promote_nonexistent_returns_false_and_no_op(self):
        """promote() on a belief_id not in provisional returns False and mutates nothing."""
        state = BeliefState()
        belief = Belief("b1", "Untouched", 0.9)
        state.add_verified(belief)

        assert state.promote("nonexistent") is False
        assert "b1" in state.verified
        assert state.provisional == {}

    def test_demote_nonexistent_returns_false_and_no_op(self):
        """demote() on a belief_id not in verified returns False and mutates nothing."""
        state = BeliefState()
        belief = Belief("b1", "Untouched", 0.5)
        state.add_provisional(belief)

        assert state.demote("nonexistent") is False
        assert "b1" in state.provisional
        assert state.verified == {}


class TestPromotionCriteria:
    """Tests for PromotionCriteria evaluation."""

    def test_confidence_threshold(self):
        """Promotion requires minimum confidence."""
        criteria = PromotionCriteria(min_confidence=0.8)

        high_conf = Belief("b1", "High", 0.9, corroboration_count=1)
        low_conf = Belief("b2", "Low", 0.5, corroboration_count=1)

        assert criteria.evaluate(high_conf) is True
        assert criteria.evaluate(low_conf) is False

    def test_corroboration_requirement(self):
        """Promotion can require corroborating sources."""
        criteria = PromotionCriteria(min_confidence=0.5, min_corroborations=2)

        belief = Belief("b1", "Claim", 0.7, corroboration_count=1)
        assert criteria.evaluate(belief) is False

        belief.corroboration_count = 3
        assert criteria.evaluate(belief) is True

    def test_age_requirement(self):
        """Promotion can require minimum belief age."""
        criteria = PromotionCriteria(min_confidence=0.5, min_age_seconds=10)

        # New belief should not meet criteria
        new_belief = Belief("b1", "New", 0.8, corroboration_count=1)
        assert criteria.evaluate(new_belief) is False

        # Old belief should meet criteria
        old_belief = Belief(
            "b2", "Old", 0.8, corroboration_count=1,
            created_at=datetime.now() - timedelta(seconds=20),
        )
        assert criteria.evaluate(old_belief) is True

    def test_custom_predicate(self):
        """Custom predicates can be added."""

        def must_have_source(belief: Belief) -> bool:
            return belief.source_agent is not None

        criteria = PromotionCriteria(
            min_confidence=0.5, custom_predicates=[must_have_source]
        )

        no_source = Belief("b1", "Anonymous", 0.9)
        with_source = Belief("b2", "Sourced", 0.9, source_agent="agent-1",
                             corroboration_count=1)

        assert criteria.evaluate(no_source) is False
        assert criteria.evaluate(with_source) is True

    def test_combined_criteria(self):
        """All criteria must be met for promotion."""
        criteria = PromotionCriteria(min_confidence=0.8, min_corroborations=2)

        # Meets confidence but not corroboration
        high_conf_low_corr = Belief("b1", "Test", 0.9, corroboration_count=1)
        assert criteria.evaluate(high_conf_low_corr) is False

        # Meets corroboration but not confidence
        low_conf_high_corr = Belief("b2", "Test", 0.5, corroboration_count=3)
        assert criteria.evaluate(low_conf_high_corr) is False

        # Meets both
        meets_all = Belief("b3", "Test", 0.9, corroboration_count=3)
        assert criteria.evaluate(meets_all) is True


class TestSandboxManager:
    """Tests for SandboxManager with TTL expiry."""

    def test_add_provisional_with_ttl(self):
        """Provisional beliefs have TTL."""
        manager = SandboxManager(SandboxConfig(default_ttl_seconds=60))

        belief = Belief("b1", "Temporary", 0.5)
        manager.add_provisional(belief)

        assert manager.state.get_partition("b1") == BeliefPartition.PROVISIONAL

    def test_ttl_expiry(self):
        """Expired beliefs are cleaned up."""
        manager = SandboxManager(SandboxConfig(default_ttl_seconds=0.1))

        belief = Belief("b1", "Expiring", 0.5)
        manager.add_provisional(belief)

        # Wait for expiry
        time.sleep(0.15)
        manager.cleanup_expired()

        assert manager.state.get_belief("b1") is None

    def test_manual_promotion(self):
        """Beliefs can be manually promoted."""
        manager = SandboxManager()

        belief = Belief("b1", "To promote", 0.9)
        manager.add_provisional(belief)

        manager.promote("b1")

        assert manager.state.get_partition("b1") == BeliefPartition.VERIFIED

    def test_auto_promotion_on_criteria(self):
        """Beliefs auto-promote when meeting criteria."""
        criteria = PromotionCriteria(min_confidence=0.8)
        manager = SandboxManager(
            SandboxConfig(default_ttl_seconds=60), promotion_criteria=criteria
        )

        # High confidence belief
        high = Belief("high", "High confidence", 0.95)
        manager.add_provisional(high)
        manager.add_corroboration("high", "agent-a")

        # Check for promotions
        promoted = manager.check_promotions()

        assert "high" in promoted
        assert manager.state.get_partition("high") == BeliefPartition.VERIFIED

    def test_no_auto_promote_below_threshold(self):
        """Low confidence beliefs stay provisional."""
        criteria = PromotionCriteria(min_confidence=0.8)
        manager = SandboxManager(
            SandboxConfig(default_ttl_seconds=60), promotion_criteria=criteria
        )

        low = Belief("low", "Low confidence", 0.5)
        manager.add_provisional(low)

        promoted = manager.check_promotions()

        assert "low" not in promoted
        assert manager.state.get_partition("low") == BeliefPartition.PROVISIONAL

    def test_default_criteria_require_corroboration(self):
        """The default PromotionCriteria requires >=1 corroboration, so a
        fresh single-source belief is NOT promoted (P2-36)."""
        manager = SandboxManager(SandboxConfig(default_ttl_seconds=60))
        high = Belief("h", "High", 0.95)
        manager.add_provisional(high)
        assert manager.check_promotions() == []
        assert manager.state.get_partition("h") == BeliefPartition.PROVISIONAL

    def test_provisional_cap_enforced(self):
        """add_provisional raises once the provisional store reaches
        max_provisional_beliefs (P2-36)."""
        cfg = SandboxConfig(max_provisional_beliefs=2)
        manager = SandboxManager(cfg)
        manager.add_provisional(Belief("x1", "a", 0.9))
        manager.add_provisional(Belief("x2", "b", 0.9))
        with pytest.raises(ValueError):
            manager.add_provisional(Belief("x3", "c", 0.9))

    def test_update_belief_confidence(self):
        """Belief confidence can be updated."""
        manager = SandboxManager()

        belief = Belief("b1", "Evolving", 0.5)
        manager.add_provisional(belief)

        manager.update_confidence("b1", 0.9)

        updated = manager.state.get_belief("b1")
        assert updated.confidence == 0.9

    def test_add_corroboration(self):
        """Corroboration can be added to beliefs."""
        manager = SandboxManager()

        belief = Belief("b1", "Claim", 0.7, corroboration_count=0)
        manager.add_provisional(belief)

        manager.add_corroboration("b1", "agent-2")

        updated = manager.state.get_belief("b1")
        assert updated.corroboration_count == 1

    def test_get_stats(self):
        """Manager reports statistics."""
        manager = SandboxManager()

        for i in range(3):
            manager.add_provisional(Belief(f"p{i}", "Provisional", 0.5))
        for i in range(2):
            manager.state.add_verified(Belief(f"v{i}", "Verified", 0.9))

        stats = manager.get_stats()

        assert stats["verified_count"] == 2
        assert stats["provisional_count"] == 3

    def test_verified_beliefs_no_ttl(self):
        """Verified beliefs are not subject to TTL."""
        manager = SandboxManager(SandboxConfig(default_ttl_seconds=0.1))

        belief = Belief("b1", "Verified", 0.9)
        manager.state.add_verified(belief)

        time.sleep(0.15)
        manager.cleanup_expired()

        # Verified belief should still exist
        assert manager.state.get_belief("b1") is not None


class TestBeliefPartition:
    """Tests for BeliefPartition enum."""

    def test_partition_values(self):
        """Partitions have expected values."""
        assert BeliefPartition.VERIFIED.value == "verified"
        assert BeliefPartition.PROVISIONAL.value == "provisional"


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_default_config(self):
        """Default config has reasonable values."""
        config = SandboxConfig()
        assert config.default_ttl_seconds > 0
        assert config.max_provisional_beliefs > 0

    def test_custom_config(self):
        """Config can be customized."""
        config = SandboxConfig(default_ttl_seconds=120, max_provisional_beliefs=500)
        assert config.default_ttl_seconds == 120
        assert config.max_provisional_beliefs == 500
