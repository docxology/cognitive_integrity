"""
Trust Calculus for Multiagent Systems.

Implements bounded trust delegation with decay guarantees.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

# Module logger for tracking trust computation
logger = logging.getLogger(__name__)

def _require_unit_interval(name: str, value: float) -> None:
    """Raise if *value* is not a finite number in [0, 1]."""
    if not np.isfinite(value) or not (0.0 <= float(value) <= 1.0):
        raise ValueError(f"{name} must be a finite value in [0, 1], got {value!r}")


def _require_nonnegative_depth(depth: int) -> None:
    """Raise if *depth* is not an integer >= 0.

    d=0 is the identity hop (delta**0 == 1) used by decay-curve figures.
    """
    if isinstance(depth, bool) or not isinstance(depth, (int, np.integer)) or int(depth) < 0:
        raise ValueError(f"depth must be an integer >= 0, got {depth!r}")



@dataclass
class TrustConfig:
    """Configuration for trust computation."""

    alpha: float = 0.3  # Base trust weight
    beta: float = 0.4  # Reputation weight
    gamma: float = 0.3  # Context weight
    decay: float = 0.9  # Delegation decay factor

    def __post_init__(self):
        if not np.isclose(self.alpha + self.beta + self.gamma, 1.0):
            raise ValueError("Weights must sum to 1.0")
        if not 0 < self.decay < 1:
            raise ValueError("Decay must be in (0, 1)")


class TrustCalculus:
    """
    Computes trust scores between agents.

    Trust = α·T_base + β·T_rep + γ·T_ctx

    Delegation: T_delegated = min(T_i→j, T_j→k) · δ^d
    """

    def __init__(self, config: Optional[TrustConfig] = None):
        self.config = config or TrustConfig()

    def compute_trust(self, base_trust: float, reputation: float, context_trust: float) -> float:
        """
        Compute composite trust score.

        Args:
            base_trust: Architectural/role-based trust [0,1]
            reputation: Historical accuracy [0,1]
            context_trust: Task-specific trust [0,1]

        Returns:
            Weighted trust score [0,1]
        """
        _require_unit_interval("base_trust", base_trust)
        _require_unit_interval("reputation", reputation)
        _require_unit_interval("context_trust", context_trust)
        return (
            self.config.alpha * base_trust
            + self.config.beta * reputation
            + self.config.gamma * context_trust
        )

    def delegate_trust(self, source_trust: float, target_trust: float, depth: int = 1) -> float:
        """
        Compute delegated trust with decay.

        Trust cannot amplify through delegation chains.

        Args:
            source_trust: Trust from delegator to intermediary
            target_trust: Trust from intermediary to target
            depth: Delegation chain depth

        Returns:
            Bounded delegated trust
        """
        _require_unit_interval("source_trust", source_trust)
        _require_unit_interval("target_trust", target_trust)
        _require_nonnegative_depth(depth)
        return min(source_trust, target_trust) * (self.config.decay ** int(depth))

    def compute_path_trust(self, path_trusts: List[float]) -> float:
        """
        Compute trust along a delegation path.

        Implements Definition 4.4: end-to-end delegated trust is the
        minimum edge trust scaled by a single decay factor raised to the
        total path depth (number of hops):

            T_path = min_i T_i * delta^d

        Args:
            path_trusts: Trust values along path [T_0→1, T_1→2, ...]

        Returns:
            End-to-end delegated trust
        """
        if not path_trusts:
            return 0.0
        for i, edge in enumerate(path_trusts):
            _require_unit_interval(f"path_trusts[{i}]", edge)

        # delta applied once for the total depth, not compounded per hop
        # (per-hop compounding over-decays: a 4-hop chain of 1.0s would
        # give delta^6 instead of the manuscript's delta^4).
        return min(path_trusts) * (self.config.decay ** len(path_trusts))


class TrustMatrix:
    """
    Manages pairwise trust between agents.

    Supports efficient updates and queries.
    """

    def __init__(self, n_agents: int, config: Optional[TrustConfig] = None):
        if n_agents < 1:
            raise ValueError("n_agents must be positive")
        self.n_agents = n_agents
        self.config = config or TrustConfig()
        self.calculus = TrustCalculus(self.config)

        # Initialize with neutral trust
        self._base = np.ones((n_agents, n_agents)) * 0.5
        self._reputation = np.ones((n_agents, n_agents)) * 0.5
        self._context = np.ones((n_agents, n_agents)) * 0.5

        # Self-trust is maximal
        np.fill_diagonal(self._base, 1.0)
        np.fill_diagonal(self._reputation, 1.0)
        np.fill_diagonal(self._context, 1.0)

    def get_trust(self, source: int, target: int) -> float:
        """Get trust from source to target agent."""
        return self.calculus.compute_trust(
            self._base[source, target],
            self._reputation[source, target],
            self._context[source, target],
        )

    def update_reputation(
        self, source: int, target: int, outcome: float, learning_rate: float = 0.1
    ) -> None:
        """
        Update reputation based on observed outcome.

        Args:
            source: Observing agent
            target: Observed agent
            outcome: Accuracy of target's claim [0,1]
            learning_rate: Update weight
        """
        current = self._reputation[source, target]
        self._reputation[source, target] = (1 - learning_rate) * current + learning_rate * outcome

    def set_context_trust(self, source: int, target: int, context_trust: float) -> None:
        """Set task-specific context trust."""
        self._context[source, target] = np.clip(context_trust, 0.0, 1.0)

    def get_delegation_trust(self, path: List[int]) -> float:
        """
        Get trust along delegation path.

        Args:
            path: Agent indices [source, ..., target]

        Returns:
            End-to-end trust with decay
        """
        if len(path) < 2:
            # A path needs at least a source and a target.  Returning 1.0
            # (maximal trust) for a degenerate single-node "path" would
            # let an empty delegation claim full trust.
            return 0.0

        trusts = [self.get_trust(path[i], path[i + 1]) for i in range(len(path) - 1)]
        return self.calculus.compute_path_trust(trusts)

    def to_matrix(self) -> np.ndarray:
        """Return composite trust matrix."""
        result = np.zeros((self.n_agents, self.n_agents))
        for i in range(self.n_agents):
            for j in range(self.n_agents):
                result[i, j] = self.get_trust(i, j)
        return result


@dataclass
class InteractionRecord:
    """Record of an interaction for reputation tracking."""

    outcome: float
    timestamp: float


class ReputationTracker:
    """
    Tracks reputation with time-based decay.

    Reputation decays exponentially based on time since interaction.
    Recent interactions have more weight than older ones.
    """

    def __init__(self, decay_rate: float = 0.1, default_reputation: float = 0.5):
        """
        Initialize reputation tracker.

        Args:
            decay_rate: Exponential decay rate (higher = faster decay)
            default_reputation: Default reputation for unknown pairs
        """
        self.decay_rate = decay_rate
        self.default_reputation = default_reputation
        self._interactions: Dict[Tuple[str, str], List[InteractionRecord]] = {}

    def record_interaction(
        self, source_id: str, target_id: str, outcome: float, timestamp: float
    ) -> None:
        """
        Record an interaction outcome.

        Args:
            source_id: Observing agent
            target_id: Observed agent
            outcome: Interaction outcome [0, 1]
            timestamp: Time of interaction
        """
        key = (source_id, target_id)
        if key not in self._interactions:
            self._interactions[key] = []

        self._interactions[key].append(InteractionRecord(outcome=outcome, timestamp=timestamp))

    def get_reputation(self, source_id: str, target_id: str, current_time: float) -> float:
        """
        Get time-decayed reputation.

        Uses exponential decay: weight = exp(-decay_rate * time_delta)

        Args:
            source_id: Observing agent
            target_id: Observed agent
            current_time: Current timestamp

        Returns:
            Time-weighted reputation [0, 1]
        """
        key = (source_id, target_id)
        if key not in self._interactions or not self._interactions[key]:
            return self.default_reputation

        interactions = self._interactions[key]

        total_weight = 0.0
        weighted_sum = 0.0

        for record in interactions:
            time_delta = current_time - record.timestamp
            weight = np.exp(-self.decay_rate * time_delta)
            weighted_sum += weight * record.outcome
            total_weight += weight

        if total_weight == 0:
            return self.default_reputation

        return weighted_sum / total_weight


class ContextAwareTrust:
    """
    Context-aware trust boosting based on expertise.

    Agents can have registered expertise in domains, which
    boosts their trust when operating in those contexts.
    """

    def __init__(self, max_boost: float = 0.3):
        """
        Initialize context-aware trust.

        Args:
            max_boost: Maximum trust boost from expertise
        """
        self.max_boost = max_boost
        self._expertise: Dict[str, Dict[str, float]] = {}  # agent -> context -> level
        self._context_similarity: Dict[str, Dict[str, float]] = {}  # context -> similar -> score

    def register_expertise(self, agent_id: str, context: str, level: float) -> None:
        """
        Register an agent's expertise in a context.

        Args:
            agent_id: The agent
            context: Domain/context name
            level: Expertise level [0, 1]
        """
        if agent_id not in self._expertise:
            self._expertise[agent_id] = {}
        self._expertise[agent_id][context] = np.clip(level, 0.0, 1.0)

    def register_context_similarity(self, context1: str, context2: str, similarity: float) -> None:
        """
        Register similarity between contexts.

        Args:
            context1: First context
            context2: Second context
            similarity: Similarity score [0, 1]
        """
        if context1 not in self._context_similarity:
            self._context_similarity[context1] = {}
        self._context_similarity[context1][context2] = np.clip(similarity, 0.0, 1.0)

    def get_expertise(self, agent_id: str, context: str) -> float:
        """
        Get agent's expertise in context (with similarity fallback).

        Args:
            agent_id: The agent
            context: The context

        Returns:
            Expertise level (0 if none registered)
        """
        if agent_id not in self._expertise:
            return 0.0

        agent_expertise = self._expertise[agent_id]

        # Direct match
        if context in agent_expertise:
            return agent_expertise[context]

        # Check similar contexts
        if context in self._context_similarity:
            best_match = 0.0
            for similar_ctx, similarity in self._context_similarity[context].items():
                if similar_ctx in agent_expertise:
                    match = similarity * agent_expertise[similar_ctx]
                    best_match = max(best_match, match)
            return best_match

        return 0.0

    def boost_for_context(self, agent_id: str, base_trust: float, context: str) -> float:
        """
        Boost trust based on context expertise.

        Args:
            agent_id: The agent
            base_trust: Base trust level
            context: Current context

        Returns:
            Boosted trust (bounded by 1.0)
        """
        expertise = self.get_expertise(agent_id, context)
        boost = self.max_boost * expertise

        return min(1.0, base_trust + boost)


class TrustMatrixWithDecay(TrustMatrix):
    """
    TrustMatrix with integrated reputation decay and context boosting.

    Extends base TrustMatrix with time-aware reputation and
    context-specific trust adjustments.
    """

    def __init__(
        self,
        n_agents: int,
        config: Optional[TrustConfig] = None,
        decay_rate: float = 0.1,
    ):
        """
        Initialize trust matrix with decay.

        Args:
            n_agents: Number of agents
            config: Trust configuration
            decay_rate: Reputation decay rate
        """
        super().__init__(n_agents, config)
        self.reputation_tracker = ReputationTracker(decay_rate=decay_rate)
        self.context_trust = ContextAwareTrust()
        self._agent_id_map: Dict[int, str] = {}  # index -> agent_id

        # Initialize agent IDs
        for i in range(n_agents):
            self._agent_id_map[i] = f"agent-{i}"

    def record_interaction(
        self, source: int, target: int, outcome: float, timestamp: float
    ) -> None:
        """
        Record an interaction for reputation tracking.

        Args:
            source: Source agent index
            target: Target agent index
            outcome: Interaction outcome [0, 1]
            timestamp: Time of interaction
        """
        source_id = self._agent_id_map.get(source, f"agent-{source}")
        target_id = self._agent_id_map.get(target, f"agent-{target}")

        self.reputation_tracker.record_interaction(source_id, target_id, outcome, timestamp)

    def get_trust_at_time(self, source: int, target: int, current_time: float) -> float:
        """
        Get trust with time-decayed reputation.

        Args:
            source: Source agent index
            target: Target agent index
            current_time: Current timestamp

        Returns:
            Trust score with decayed reputation
        """
        source_id = self._agent_id_map.get(source, f"agent-{source}")
        target_id = self._agent_id_map.get(target, f"agent-{target}")

        # Get time-decayed reputation
        reputation = self.reputation_tracker.get_reputation(source_id, target_id, current_time)

        return self.calculus.compute_trust(
            self._base[source, target], reputation, self._context[source, target]
        )

    def register_agent_expertise(self, agent: int, context: str, level: float) -> None:
        """
        Register agent expertise for context boosting.

        Args:
            agent: Agent index
            context: Expertise domain
            level: Expertise level [0, 1]
        """
        agent_id = self._agent_id_map.get(agent, f"agent-{agent}")
        self.context_trust.register_expertise(agent_id, context, level)

    def get_trust_with_context(self, source: int, target: int, context: str) -> float:
        """
        Get trust with context-aware boosting.

        Args:
            source: Source agent index
            target: Target agent index
            context: Current context

        Returns:
            Context-boosted trust
        """
        base_trust = self.get_trust(source, target)
        target_id = self._agent_id_map.get(target, f"agent-{target}")

        return self.context_trust.boost_for_context(target_id, base_trust, context)
