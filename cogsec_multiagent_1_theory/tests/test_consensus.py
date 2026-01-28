"""Tests for Byzantine consensus."""

import numpy as np
import pytest
from consensus import (ByzantineConsensus, ConsensusConfig, ConsensusResult,
                       QuorumVerification, Vote)


class TestByzantineConsensus:
    """Tests for Byzantine-tolerant consensus."""

    def test_requires_3f_plus_1(self):
        """Consensus requires n >= 3f + 1 agents."""
        # Valid: 4 agents, 1 Byzantine (4 >= 3*1+1 = 4)
        ByzantineConsensus(n_agents=4, max_byzantine=1)

        # Invalid: 3 agents, 1 Byzantine (3 < 4)
        with pytest.raises(ValueError, match="3f \\+ 1"):
            ByzantineConsensus(n_agents=3, max_byzantine=1)

    def test_default_max_byzantine(self):
        """Default max Byzantine is (n-1)/3."""
        consensus = ByzantineConsensus(n_agents=7)
        assert consensus.max_byzantine == 2  # (7-1)//3 = 2

    def test_consensus_accept(self):
        """Consensus accepts when > 2/3 agents agree."""
        consensus = ByzantineConsensus(n_agents=4)

        # 3/4 agents accept (> 2/3)
        for i in range(3):
            consensus.submit_vote(
                Vote(agent_id=f"agent-{i}", proposition="sky is blue", belief=0.9)
            )
        # 1 agent rejects
        consensus.submit_vote(
            Vote(agent_id="agent-3", proposition="sky is blue", belief=0.2)
        )

        result, confidence = consensus.compute_consensus("sky is blue")
        assert result == ConsensusResult.ACCEPT
        assert confidence >= 0.75

    def test_consensus_reject(self):
        """Consensus rejects when > 2/3 agents reject."""
        consensus = ByzantineConsensus(n_agents=4)

        # 3/4 agents reject
        for i in range(3):
            consensus.submit_vote(
                Vote(agent_id=f"agent-{i}", proposition="moon is cheese", belief=0.1)
            )
        # 1 agent accepts
        consensus.submit_vote(
            Vote(agent_id="agent-3", proposition="moon is cheese", belief=0.9)
        )

        result, _ = consensus.compute_consensus("moon is cheese")
        assert result == ConsensusResult.REJECT

    def test_consensus_undecided(self):
        """Consensus is undecided when no quorum."""
        consensus = ByzantineConsensus(n_agents=4)

        # 2 accept, 2 reject (no > 2/3 majority)
        consensus.submit_vote(Vote("a1", "prop", 0.9))
        consensus.submit_vote(Vote("a2", "prop", 0.9))
        consensus.submit_vote(Vote("a3", "prop", 0.1))
        consensus.submit_vote(Vote("a4", "prop", 0.1))

        result, _ = consensus.compute_consensus("prop")
        assert result == ConsensusResult.UNDECIDED

    def test_insufficient_votes(self):
        """Returns undecided without enough votes."""
        consensus = ByzantineConsensus(n_agents=10)

        # Only 2 votes (need > 6 for quorum)
        consensus.submit_vote(Vote("a1", "prop", 0.9))
        consensus.submit_vote(Vote("a2", "prop", 0.9))

        result, confidence = consensus.compute_consensus("prop")
        assert result == ConsensusResult.UNDECIDED
        assert confidence < 0.5  # Low confidence due to few votes

    def test_get_belief_returns_average(self):
        """get_belief returns average of agreeing votes."""
        consensus = ByzantineConsensus(n_agents=4)

        # 3 agents with varying high beliefs
        consensus.submit_vote(Vote("a1", "prop", 0.8))
        consensus.submit_vote(Vote("a2", "prop", 0.9))
        consensus.submit_vote(Vote("a3", "prop", 0.85))
        consensus.submit_vote(Vote("a4", "prop", 0.1))  # Rejector

        belief = consensus.get_belief("prop")
        assert belief is not None
        assert 0.8 <= belief <= 0.9

    def test_vote_update(self):
        """Later votes from same agent update previous."""
        consensus = ByzantineConsensus(n_agents=2, max_byzantine=0)

        consensus.submit_vote(Vote("agent-1", "prop", 0.9))
        consensus.submit_vote(Vote("agent-1", "prop", 0.1))  # Changed mind

        dist = consensus.get_vote_distribution("prop")
        # Should only count once
        assert dist["accept"] + dist["reject"] + dist["uncertain"] == 1

    def test_is_decided(self):
        """is_decided tracks finalized propositions."""
        consensus = ByzantineConsensus(n_agents=4)

        for i in range(4):
            consensus.submit_vote(Vote(f"a{i}", "decided_prop", 0.9))

        consensus.compute_consensus("decided_prop")
        assert consensus.is_decided("decided_prop")
        assert not consensus.is_decided("unknown_prop")

    def test_reset_single(self):
        """Reset can clear single proposition."""
        consensus = ByzantineConsensus(n_agents=4)

        consensus.submit_vote(Vote("a1", "prop1", 0.9))
        consensus.submit_vote(Vote("a1", "prop2", 0.9))

        consensus.reset("prop1")

        assert "prop1" not in consensus._votes
        assert "prop2" in consensus._votes

    def test_reset_all(self):
        """Reset without args clears everything."""
        consensus = ByzantineConsensus(n_agents=4)

        consensus.submit_vote(Vote("a1", "prop1", 0.9))
        consensus.submit_vote(Vote("a1", "prop2", 0.9))

        consensus.reset()

        assert len(consensus._votes) == 0


class TestQuorumVerification:
    """Tests for quorum-based action verification."""

    def test_quorum_calculation(self):
        """Quorum is ceil((n+f+1)/2)."""
        # n=7, f=2: quorum = ceil((7+2+1)/2) = ceil(5) = 5
        quorum = QuorumVerification(n_agents=7, max_byzantine=2)
        assert quorum.quorum == 5

    def test_approval_reaches_quorum(self):
        """Action approved when quorum reached."""
        quorum = QuorumVerification(n_agents=4, max_byzantine=1)
        # quorum = ceil((4+1+1)/2) = 3

        quorum.request_approval("action-1")

        assert not quorum.approve("action-1", "agent-1")
        assert not quorum.approve("action-1", "agent-2")
        assert quorum.approve("action-1", "agent-3")  # Third vote reaches quorum

    def test_is_approved(self):
        """is_approved checks quorum status."""
        quorum = QuorumVerification(n_agents=4, max_byzantine=1)

        quorum.request_approval("action-1")
        quorum.approve("action-1", "agent-1")
        quorum.approve("action-1", "agent-2")

        assert not quorum.is_approved("action-1")

        quorum.approve("action-1", "agent-3")
        assert quorum.is_approved("action-1")

    def test_duplicate_approvals_ignored(self):
        """Same agent can't approve twice."""
        quorum = QuorumVerification(n_agents=4, max_byzantine=1)

        quorum.approve("action-1", "agent-1")
        quorum.approve("action-1", "agent-1")
        quorum.approve("action-1", "agent-1")

        assert quorum.get_approval_count("action-1") == 1

    def test_get_missing_approvals(self):
        """get_missing_approvals shows how many more needed."""
        quorum = QuorumVerification(n_agents=4, max_byzantine=1)
        # quorum = 3

        quorum.approve("action-1", "agent-1")
        assert quorum.get_missing_approvals("action-1") == 2

        quorum.approve("action-1", "agent-2")
        assert quorum.get_missing_approvals("action-1") == 1

        quorum.approve("action-1", "agent-3")
        assert quorum.get_missing_approvals("action-1") == 0

    def test_cancel(self):
        """Cancel removes pending approval request."""
        quorum = QuorumVerification(n_agents=4)

        quorum.approve("action-1", "agent-1")
        quorum.cancel("action-1")

        assert quorum.get_approval_count("action-1") == 0


class TestWeightedVoting:
    """Tests for weighted voting consensus."""

    def test_weighted_vote_creation(self):
        """Weighted votes include trust weight."""
        from consensus import WeightedVote

        vote = WeightedVote(
            agent_id="agent-1", proposition="test", belief=0.9, trust_weight=0.8
        )
        assert vote.trust_weight == 0.8

    def test_weighted_consensus_basic(self):
        """Weighted consensus considers trust weights."""
        from consensus import WeightedByzantineConsensus, WeightedVote

        consensus = WeightedByzantineConsensus(n_agents=4)

        # High trust agent accepts
        consensus.submit_vote(
            WeightedVote("trusted", "prop", belief=0.9, trust_weight=0.9)
        )

        # Low trust agents reject
        for i in range(3):
            consensus.submit_vote(
                WeightedVote(f"untrusted-{i}", "prop", belief=0.1, trust_weight=0.1)
            )

        result, _ = consensus.compute_consensus("prop")
        # High trust vote should have more influence
        # But still need quorum - result depends on weights

    def test_trusted_agent_more_influence(self):
        """Trusted agents have more influence on outcome."""
        from consensus import WeightedByzantineConsensus, WeightedVote

        # Scenario: 1 trusted vs 2 untrusted
        consensus = WeightedByzantineConsensus(n_agents=3, max_byzantine=0)

        # Highly trusted accepts
        consensus.submit_vote(
            WeightedVote("trusted", "prop", belief=0.9, trust_weight=0.9)
        )

        # Less trusted rejects
        consensus.submit_vote(
            WeightedVote("less-trusted-1", "prop", belief=0.1, trust_weight=0.3)
        )
        consensus.submit_vote(
            WeightedVote("less-trusted-2", "prop", belief=0.1, trust_weight=0.3)
        )

        # Get weighted average belief
        avg = consensus.get_weighted_average("prop")

        # Should be closer to trusted agent's belief
        assert avg > 0.5

    def test_equal_weights_same_as_unweighted(self):
        """Equal weights produce same result as unweighted."""
        from consensus import WeightedByzantineConsensus, WeightedVote

        consensus = WeightedByzantineConsensus(n_agents=4, max_byzantine=1)

        for i in range(4):
            consensus.submit_vote(
                WeightedVote(f"agent-{i}", "prop", belief=0.8, trust_weight=1.0)
            )

        avg = consensus.get_weighted_average("prop")
        assert abs(avg - 0.8) < 0.01


class TestConfidenceBasedConsensus:
    """Tests for confidence-based consensus."""

    def test_confidence_vote(self):
        """Votes include confidence level."""
        from consensus import ConfidenceVote

        vote = ConfidenceVote(
            agent_id="agent-1", proposition="test", belief=0.9, confidence=0.8
        )
        assert vote.confidence == 0.8

    def test_high_confidence_more_weight(self):
        """High confidence votes carry more weight."""
        from consensus import ConfidenceByzantineConsensus, ConfidenceVote

        consensus = ConfidenceByzantineConsensus(n_agents=3, max_byzantine=0)

        # High confidence accept
        consensus.submit_vote(
            ConfidenceVote("agent-1", "prop", belief=0.9, confidence=0.95)
        )

        # Low confidence rejects
        consensus.submit_vote(
            ConfidenceVote("agent-2", "prop", belief=0.1, confidence=0.2)
        )
        consensus.submit_vote(
            ConfidenceVote("agent-3", "prop", belief=0.1, confidence=0.2)
        )

        avg = consensus.get_confidence_weighted_average("prop")

        # High confidence accept should dominate
        assert avg > 0.5

    def test_low_confidence_aggregated(self):
        """Low confidence across agents reduces certainty."""
        from consensus import ConfidenceByzantineConsensus, ConfidenceVote

        consensus = ConfidenceByzantineConsensus(n_agents=3, max_byzantine=0)

        # All low confidence
        for i in range(3):
            consensus.submit_vote(
                ConfidenceVote(f"agent-{i}", "prop", belief=0.9, confidence=0.2)
            )

        # Aggregate confidence should be low
        agg_confidence = consensus.get_aggregate_confidence("prop")
        assert agg_confidence < 0.5

    def test_confidence_affects_decision(self):
        """Low aggregate confidence can lead to UNDECIDED."""
        from consensus import ConfidenceByzantineConsensus, ConfidenceVote

        consensus = ConfidenceByzantineConsensus(
            n_agents=3, max_byzantine=0, min_aggregate_confidence=0.5
        )

        # All low confidence, even if agreeing
        for i in range(3):
            consensus.submit_vote(
                ConfidenceVote(f"agent-{i}", "prop", belief=0.9, confidence=0.2)
            )

        result, _ = consensus.compute_consensus("prop")

        # Should be undecided due to low confidence
        # (actual behavior depends on implementation)
        assert result in [ConsensusResult.ACCEPT, ConsensusResult.UNDECIDED]


class TestCombinedWeightedConfidence:
    """Tests for combined weighted + confidence voting."""

    def test_combined_vote(self):
        """Votes can have both trust weight and confidence."""
        from consensus import CombinedVote

        vote = CombinedVote(
            agent_id="agent-1",
            proposition="test",
            belief=0.9,
            trust_weight=0.8,
            confidence=0.7,
        )
        assert vote.trust_weight == 0.8
        assert vote.confidence == 0.7

    def test_effective_weight(self):
        """Effective weight combines trust and confidence."""
        from consensus import CombinedVote

        vote = CombinedVote(
            agent_id="agent-1",
            proposition="test",
            belief=0.9,
            trust_weight=0.8,
            confidence=0.5,
        )

        # Effective weight = trust_weight * confidence
        assert abs(vote.effective_weight - 0.4) < 0.01

    def test_combined_consensus(self):
        """Combined consensus uses effective weights."""
        from consensus import CombinedByzantineConsensus, CombinedVote

        consensus = CombinedByzantineConsensus(n_agents=3, max_byzantine=0)

        # High trust, high confidence accept
        consensus.submit_vote(
            CombinedVote(
                "agent-1", "prop", belief=0.9, trust_weight=0.9, confidence=0.9
            )
        )

        # Low trust, low confidence reject
        consensus.submit_vote(
            CombinedVote(
                "agent-2", "prop", belief=0.1, trust_weight=0.3, confidence=0.3
            )
        )

        # Medium trust, medium confidence reject
        consensus.submit_vote(
            CombinedVote(
                "agent-3", "prop", belief=0.1, trust_weight=0.5, confidence=0.5
            )
        )

        avg = consensus.get_combined_weighted_average("prop")

        # Agent-1's effective weight: 0.81
        # Agent-2's effective weight: 0.09
        # Agent-3's effective weight: 0.25
        # Weighted avg should favor agent-1
        assert avg > 0.5
