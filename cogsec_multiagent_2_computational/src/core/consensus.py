"""
Byzantine-Tolerant Consensus for Multiagent Systems.

Implements cognitive Byzantine agreement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

# Module logger for tracking consensus decisions
logger = logging.getLogger(__name__)


class ConsensusResult(Enum):
    """Result of consensus attempt."""

    ACCEPT = "accept"  # Consensus: belief accepted
    REJECT = "reject"  # Consensus: belief rejected
    UNDECIDED = "undecided"  # No consensus reached


@dataclass
class Vote:
    """Single agent's vote on a proposition."""

    agent_id: str
    proposition: str
    belief: float  # [0, 1]
    timestamp: float = 0.0


@dataclass
class ConsensusConfig:
    """Configuration for Byzantine consensus."""

    acceptance_threshold: float = 0.7  # τ for accepting belief
    rejection_threshold: float = 0.3  # 1-τ for rejecting
    quorum_fraction: float = 2 / 3  # Required agreement fraction


class ByzantineConsensus:
    """
    Byzantine-tolerant belief consensus.

    For n agents with at most f Byzantine:
    - Requires n >= 3f + 1
    - Consensus when > 2n/3 agents agree
    """

    def __init__(
        self,
        n_agents: int,
        max_byzantine: Optional[int] = None,
        config: Optional[ConsensusConfig] = None,
    ) -> None:
        """Initialize Byzantine-tolerant consensus mechanism.

        BFT Requirement:
            n >= 3f + 1

        where n is the total agent count and f is the maximum number
        of Byzantine (arbitrarily faulty) agents. This ensures honest
        agents always form a supermajority.

        Default max_byzantine = floor((n-1)/3) if not specified.

        Args:
            n_agents: Total number of agents (n)
            max_byzantine: Maximum Byzantine agents (f); default floor((n-1)/3)
            config: Consensus configuration (thresholds, quorum fraction)

        Raises:
            ValueError: If n < 3f + 1
        """
        self.n_agents = n_agents
        self.config = config or ConsensusConfig()

        # Default max Byzantine
        if max_byzantine is None:
            self.max_byzantine = (n_agents - 1) // 3
        else:
            self.max_byzantine = max_byzantine

        # Verify Byzantine tolerance
        if n_agents < 3 * self.max_byzantine + 1:
            raise ValueError(f"Need n >= 3f + 1: {n_agents} < 3*{self.max_byzantine}+1")

        self._votes: Dict[str, List[Vote]] = {}
        self._decided: Dict[str, ConsensusResult] = {}

    def submit_vote(self, vote: Vote) -> None:
        """
        Submit agent's vote on proposition.

        Args:
            vote: Agent's vote
        """
        if vote.proposition not in self._votes:
            self._votes[vote.proposition] = []

        # Update or add vote
        existing = [
            v for v in self._votes[vote.proposition] if v.agent_id == vote.agent_id
        ]
        if existing:
            self._votes[vote.proposition].remove(existing[0])

        self._votes[vote.proposition].append(vote)

    def compute_consensus(self, proposition: str) -> Tuple[ConsensusResult, float]:
        """
        Compute consensus for proposition.

        Args:
            proposition: The proposition to decide

        Returns:
            Tuple of (result, confidence)
        """
        if proposition not in self._votes:
            return ConsensusResult.UNDECIDED, 0.0

        votes = self._votes[proposition]
        n_votes = len(votes)

        # Need enough votes
        min_votes = int(np.ceil(self.n_agents * self.config.quorum_fraction))
        if n_votes < min_votes:
            return ConsensusResult.UNDECIDED, n_votes / self.n_agents

        # Count accepting and rejecting votes
        accept_count = sum(
            1 for v in votes if v.belief > self.config.acceptance_threshold
        )
        reject_count = sum(
            1 for v in votes if v.belief < self.config.rejection_threshold
        )

        # Check for consensus
        threshold = self.n_agents * self.config.quorum_fraction

        if accept_count > threshold:
            self._decided[proposition] = ConsensusResult.ACCEPT
            return ConsensusResult.ACCEPT, accept_count / self.n_agents

        if reject_count > threshold:
            self._decided[proposition] = ConsensusResult.REJECT
            return ConsensusResult.REJECT, reject_count / self.n_agents

        return (
            ConsensusResult.UNDECIDED,
            max(accept_count, reject_count) / self.n_agents,
        )

    def get_belief(self, proposition: str) -> Optional[float]:
        """
        Get consensus belief value.

        Returns:
            Average belief if consensus reached, None otherwise
        """
        result, _ = self.compute_consensus(proposition)

        if result == ConsensusResult.UNDECIDED:
            return None

        votes = self._votes.get(proposition, [])
        if not votes:
            return None

        if result == ConsensusResult.ACCEPT:
            # Average of accepting votes
            accepting = [
                v.belief for v in votes if v.belief > self.config.acceptance_threshold
            ]
            return float(np.mean(accepting)) if accepting else None

        if result == ConsensusResult.REJECT:
            # Average of rejecting votes
            rejecting = [
                v.belief for v in votes if v.belief < self.config.rejection_threshold
            ]
            return float(np.mean(rejecting)) if rejecting else None

        return None

    def is_decided(self, proposition: str) -> bool:
        """Check if proposition has been decided."""
        return proposition in self._decided

    def get_vote_distribution(self, proposition: str) -> Dict[str, int]:
        """
        Get vote distribution for proposition.

        Returns:
            Dict with accept/reject/uncertain counts
        """
        if proposition not in self._votes:
            return {"accept": 0, "reject": 0, "uncertain": 0}

        votes = self._votes[proposition]

        return {
            "accept": sum(
                1 for v in votes if v.belief > self.config.acceptance_threshold
            ),
            "reject": sum(
                1 for v in votes if v.belief < self.config.rejection_threshold
            ),
            "uncertain": sum(
                1
                for v in votes
                if self.config.rejection_threshold
                <= v.belief
                <= self.config.acceptance_threshold
            ),
        }

    def reset(self, proposition: Optional[str] = None) -> None:
        """Reset votes and decisions."""
        if proposition:
            self._votes.pop(proposition, None)
            self._decided.pop(proposition, None)
        else:
            self._votes.clear()
            self._decided.clear()


class QuorumVerification:
    """Quorum-based action verification for critical operations.

    Quorum threshold:
        q = ceil((n + f + 1) / 2)

    This guarantees that any two quorums overlap by at least one
    honest agent, preventing conflicting approvals even with f
    Byzantine agents.
    """

    def __init__(self, n_agents: int, max_byzantine: Optional[int] = None) -> None:
        self.n_agents = n_agents
        self.max_byzantine = max_byzantine or (n_agents - 1) // 3

        # Quorum threshold: ceil((n + f + 1) / 2)
        self.quorum = int(np.ceil((n_agents + self.max_byzantine + 1) / 2))

        self._pending: Dict[str, Set[str]] = {}  # action -> approving agents

    def request_approval(self, action_id: str) -> None:
        """Initialize approval request for action."""
        self._pending[action_id] = set()

    def approve(self, action_id: str, agent_id: str) -> bool:
        """
        Submit approval for action.

        Args:
            action_id: Action identifier
            agent_id: Approving agent

        Returns:
            True if quorum reached
        """
        if action_id not in self._pending:
            self.request_approval(action_id)

        self._pending[action_id].add(agent_id)
        return len(self._pending[action_id]) >= self.quorum

    def is_approved(self, action_id: str) -> bool:
        """Check if action has quorum approval."""
        return len(self._pending.get(action_id, set())) >= self.quorum

    def get_approval_count(self, action_id: str) -> int:
        """Get current approval count."""
        return len(self._pending.get(action_id, set()))

    def get_missing_approvals(self, action_id: str) -> int:
        """Get number of approvals still needed."""
        current = self.get_approval_count(action_id)
        return max(0, self.quorum - current)

    def cancel(self, action_id: str) -> None:
        """Cancel pending approval request."""
        self._pending.pop(action_id, None)


@dataclass
class WeightedVote:
    """Vote with trust-based weight."""

    agent_id: str
    proposition: str
    belief: float  # [0, 1]
    trust_weight: float = 1.0  # [0, 1]
    timestamp: float = 0.0


class WeightedByzantineConsensus(ByzantineConsensus):
    """
    Byzantine consensus with trust-weighted voting.

    Votes are weighted by agent trust scores.
    """

    def __init__(
        self,
        n_agents: int,
        max_byzantine: Optional[int] = None,
        config: Optional[ConsensusConfig] = None,
    ) -> None:
        """Initialize weighted consensus."""
        super().__init__(n_agents, max_byzantine, config)
        self._weighted_votes: Dict[str, List[WeightedVote]] = {}

    def submit_vote(self, vote: WeightedVote) -> None:  # type: ignore[override]
        """
        Submit weighted vote.

        Args:
            vote: Weighted vote with trust score
        """
        # Also submit to parent for compatibility
        base_vote = Vote(
            agent_id=vote.agent_id,
            proposition=vote.proposition,
            belief=vote.belief,
            timestamp=vote.timestamp,
        )
        super().submit_vote(base_vote)

        # Store weighted vote
        if vote.proposition not in self._weighted_votes:
            self._weighted_votes[vote.proposition] = []

        # Update or add
        existing = [
            v
            for v in self._weighted_votes[vote.proposition]
            if v.agent_id == vote.agent_id
        ]
        if existing:
            self._weighted_votes[vote.proposition].remove(existing[0])

        self._weighted_votes[vote.proposition].append(vote)

    def get_weighted_average(self, proposition: str) -> float:
        """
        Get trust-weighted average belief.

        Args:
            proposition: The proposition

        Returns:
            Weighted average belief [0, 1]
        """
        if proposition not in self._weighted_votes:
            return 0.5

        votes = self._weighted_votes[proposition]
        if not votes:
            return 0.5

        total_weight = sum(v.trust_weight for v in votes)
        if total_weight == 0:
            return 0.5

        weighted_sum = sum(v.belief * v.trust_weight for v in votes)
        return weighted_sum / total_weight


@dataclass
class ConfidenceVote:
    """Vote with confidence level."""

    agent_id: str
    proposition: str
    belief: float  # [0, 1]
    confidence: float = 1.0  # [0, 1] - how confident agent is
    timestamp: float = 0.0


class ConfidenceByzantineConsensus(ByzantineConsensus):
    """
    Byzantine consensus with confidence-weighted voting.

    High confidence votes carry more weight.
    """

    def __init__(
        self,
        n_agents: int,
        max_byzantine: Optional[int] = None,
        config: Optional[ConsensusConfig] = None,
        min_aggregate_confidence: float = 0.0,
    ) -> None:
        """
        Initialize confidence-based consensus.

        Args:
            n_agents: Number of agents
            max_byzantine: Max Byzantine agents
            config: Consensus configuration
            min_aggregate_confidence: Minimum aggregate confidence for decision
        """
        super().__init__(n_agents, max_byzantine, config)
        self._confidence_votes: Dict[str, List[ConfidenceVote]] = {}
        self.min_aggregate_confidence = min_aggregate_confidence

    def submit_vote(self, vote: ConfidenceVote) -> None:  # type: ignore[override]
        """
        Submit confidence vote.

        Args:
            vote: Vote with confidence level
        """
        # Also submit to parent
        base_vote = Vote(
            agent_id=vote.agent_id,
            proposition=vote.proposition,
            belief=vote.belief,
            timestamp=vote.timestamp,
        )
        super().submit_vote(base_vote)

        # Store confidence vote
        if vote.proposition not in self._confidence_votes:
            self._confidence_votes[vote.proposition] = []

        # Update or add
        existing = [
            v
            for v in self._confidence_votes[vote.proposition]
            if v.agent_id == vote.agent_id
        ]
        if existing:
            self._confidence_votes[vote.proposition].remove(existing[0])

        self._confidence_votes[vote.proposition].append(vote)

    def get_confidence_weighted_average(self, proposition: str) -> float:
        """
        Get confidence-weighted average belief.

        Args:
            proposition: The proposition

        Returns:
            Confidence-weighted average belief [0, 1]
        """
        if proposition not in self._confidence_votes:
            return 0.5

        votes = self._confidence_votes[proposition]
        if not votes:
            return 0.5

        total_confidence = sum(v.confidence for v in votes)
        if total_confidence == 0:
            return 0.5

        weighted_sum = sum(v.belief * v.confidence for v in votes)
        return weighted_sum / total_confidence

    def get_aggregate_confidence(self, proposition: str) -> float:
        """Compute aggregate confidence via root-mean-square.

        Formula:
            C_agg = sqrt(Sum_i c_i^2 / n)

        where c_i is the confidence of voter i and n is the vote count.
        RMS is used rather than arithmetic mean to give higher weight
        to confident voters while remaining bounded in [0, 1].

        Args:
            proposition: The proposition identifier

        Returns:
            Aggregate confidence in [0, 1], or 0.0 if no votes
        """
        if proposition not in self._confidence_votes:
            return 0.0

        votes = self._confidence_votes[proposition]
        if not votes:
            return 0.0

        # Root mean square of confidences
        sum_sq = sum(v.confidence**2 for v in votes)
        return np.sqrt(sum_sq / len(votes))

    def compute_consensus(self, proposition: str) -> Tuple[ConsensusResult, float]:
        """
        Compute consensus with confidence consideration.

        Args:
            proposition: The proposition

        Returns:
            Tuple of (result, confidence)
        """
        # Check aggregate confidence
        agg_confidence = self.get_aggregate_confidence(proposition)
        if agg_confidence < self.min_aggregate_confidence:
            # Too uncertain to decide
            return ConsensusResult.UNDECIDED, agg_confidence

        # Use parent's consensus logic
        return super().compute_consensus(proposition)


@dataclass
class CombinedVote:
    """Vote with both trust weight and confidence."""

    agent_id: str
    proposition: str
    belief: float  # [0, 1]
    trust_weight: float = 1.0  # [0, 1]
    confidence: float = 1.0  # [0, 1]
    timestamp: float = 0.0

    @property
    def effective_weight(self) -> float:
        """Compute effective weight = trust * confidence."""
        return self.trust_weight * self.confidence


class CombinedByzantineConsensus(ByzantineConsensus):
    """
    Byzantine consensus with combined trust and confidence weighting.

    Effective weight = trust_weight * confidence
    """

    def __init__(
        self,
        n_agents: int,
        max_byzantine: Optional[int] = None,
        config: Optional[ConsensusConfig] = None,
    ) -> None:
        """Initialize combined consensus."""
        super().__init__(n_agents, max_byzantine, config)
        self._combined_votes: Dict[str, List[CombinedVote]] = {}

    def submit_vote(self, vote: CombinedVote) -> None:  # type: ignore[override]
        """
        Submit combined vote.

        Args:
            vote: Vote with trust and confidence
        """
        # Also submit to parent
        base_vote = Vote(
            agent_id=vote.agent_id,
            proposition=vote.proposition,
            belief=vote.belief,
            timestamp=vote.timestamp,
        )
        super().submit_vote(base_vote)

        # Store combined vote
        if vote.proposition not in self._combined_votes:
            self._combined_votes[vote.proposition] = []

        # Update or add
        existing = [
            v
            for v in self._combined_votes[vote.proposition]
            if v.agent_id == vote.agent_id
        ]
        if existing:
            self._combined_votes[vote.proposition].remove(existing[0])

        self._combined_votes[vote.proposition].append(vote)

    def get_combined_weighted_average(self, proposition: str) -> float:
        """
        Get average weighted by effective weight (trust * confidence).

        Args:
            proposition: The proposition

        Returns:
            Combined-weighted average belief [0, 1]
        """
        if proposition not in self._combined_votes:
            return 0.5

        votes = self._combined_votes[proposition]
        if not votes:
            return 0.5

        total_weight = sum(v.effective_weight for v in votes)
        if total_weight == 0:
            return 0.5

        weighted_sum = sum(v.belief * v.effective_weight for v in votes)
        return weighted_sum / total_weight
