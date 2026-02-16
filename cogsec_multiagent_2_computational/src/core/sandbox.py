"""
Belief Sandboxing for Multiagent Systems.

Implements verified/provisional partitions with TTL management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional, Set


class BeliefPartition(Enum):
    """Partition types for beliefs."""

    VERIFIED = "verified"
    PROVISIONAL = "provisional"


@dataclass
class Belief:
    """
    A belief held by an agent.

    Attributes:
        belief_id: Unique identifier
        content: The belief content
        confidence: Confidence level [0, 1]
        source_agent: Agent that originated the belief
        corroboration_count: Number of corroborating sources
        created_at: Creation timestamp
        metadata: Additional metadata
    """

    belief_id: str
    content: str
    confidence: float
    source_agent: Optional[str] = None
    corroboration_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SandboxConfig:
    """Configuration for sandbox management."""

    default_ttl_seconds: float = 3600.0  # 1 hour (Paper §2, Table sandbox-params)
    max_provisional_beliefs: int = 1000
    auto_cleanup_interval: float = 60.0


class BeliefState:
    """
    Manages verified and provisional belief partitions.

    Verified beliefs are considered trustworthy.
    Provisional beliefs are sandboxed and may expire.
    """

    def __init__(self):
        self._verified: Dict[str, Belief] = {}
        self._provisional: Dict[str, Belief] = {}

    @property
    def verified(self) -> Dict[str, Belief]:
        """Get verified beliefs."""
        return self._verified

    @property
    def provisional(self) -> Dict[str, Belief]:
        """Get provisional beliefs."""
        return self._provisional

    def add_verified(self, belief: Belief) -> None:
        """Add a belief to the verified partition."""
        self._verified[belief.belief_id] = belief

    def add_provisional(self, belief: Belief) -> None:
        """Add a belief to the provisional partition."""
        self._provisional[belief.belief_id] = belief

    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """Get a belief from either partition."""
        if belief_id in self._verified:
            return self._verified[belief_id]
        if belief_id in self._provisional:
            return self._provisional[belief_id]
        return None

    def get_partition(self, belief_id: str) -> Optional[BeliefPartition]:
        """Get the partition containing a belief."""
        if belief_id in self._verified:
            return BeliefPartition.VERIFIED
        if belief_id in self._provisional:
            return BeliefPartition.PROVISIONAL
        return None

    def remove(self, belief_id: str) -> bool:
        """
        Remove a belief from any partition.

        Returns:
            True if belief was found and removed
        """
        if belief_id in self._verified:
            del self._verified[belief_id]
            return True
        if belief_id in self._provisional:
            del self._provisional[belief_id]
            return True
        return False

    def promote(self, belief_id: str) -> bool:
        """
        Promote a belief from provisional to verified.

        Returns:
            True if promotion succeeded
        """
        if belief_id not in self._provisional:
            return False

        belief = self._provisional.pop(belief_id)
        self._verified[belief_id] = belief
        return True

    def demote(self, belief_id: str) -> bool:
        """
        Demote a belief from verified to provisional.

        Returns:
            True if demotion succeeded
        """
        if belief_id not in self._verified:
            return False

        belief = self._verified.pop(belief_id)
        self._provisional[belief_id] = belief
        return True


@dataclass
class PromotionCriteria:
    """
    Criteria for promoting beliefs from provisional to verified.

    All specified criteria must be met for promotion.
    """

    min_confidence: float = 0.8
    min_corroborations: int = 0
    min_age_seconds: float = 0.0
    custom_predicates: List[Callable[[Belief], bool]] = field(default_factory=list)

    def evaluate(self, belief: Belief) -> bool:
        """
        Evaluate if belief meets promotion criteria.

        Args:
            belief: The belief to evaluate

        Returns:
            True if all criteria are met
        """
        # Check confidence threshold
        if belief.confidence < self.min_confidence:
            return False

        # Check corroboration count
        if belief.corroboration_count < self.min_corroborations:
            return False

        # Check minimum age
        if self.min_age_seconds > 0:
            age = (datetime.now() - belief.created_at).total_seconds()
            if age < self.min_age_seconds:
                return False

        # Check custom predicates
        for predicate in self.custom_predicates:
            if not predicate(belief):
                return False

        return True


class SandboxManager:
    """
    Manages belief sandboxing with TTL expiry.

    Coordinates belief state, promotion criteria, and expiration.
    """

    def __init__(
        self,
        config: Optional[SandboxConfig] = None,
        promotion_criteria: Optional[PromotionCriteria] = None,
    ):
        """
        Initialize sandbox manager.

        Args:
            config: Sandbox configuration
            promotion_criteria: Criteria for automatic promotion
        """
        self.config = config or SandboxConfig()
        self.criteria = promotion_criteria or PromotionCriteria()
        self.state = BeliefState()
        self._ttl_registry: Dict[str, datetime] = {}  # belief_id -> expiry time
        self._corroborators: Dict[str, Set[str]] = {}  # belief_id -> agent IDs

    def add_provisional(
        self, belief: Belief, ttl_seconds: Optional[float] = None
    ) -> None:
        """
        Add a belief to provisional partition with TTL.

        Args:
            belief: The belief to add
            ttl_seconds: Custom TTL (uses config default if None)
        """
        self.state.add_provisional(belief)

        # Set TTL
        ttl = (
            ttl_seconds if ttl_seconds is not None else self.config.default_ttl_seconds
        )
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._ttl_registry[belief.belief_id] = expiry

    def cleanup_expired(self) -> List[str]:
        """
        Remove expired provisional beliefs.

        Returns:
            List of expired belief IDs that were removed
        """
        now = datetime.now()
        expired = []

        for belief_id, expiry in list(self._ttl_registry.items()):
            if now >= expiry:
                if self.state.get_partition(belief_id) == BeliefPartition.PROVISIONAL:
                    self.state.remove(belief_id)
                    expired.append(belief_id)
                del self._ttl_registry[belief_id]

        return expired

    def promote(self, belief_id: str) -> bool:
        """
        Manually promote a belief to verified.

        Args:
            belief_id: The belief to promote

        Returns:
            True if promotion succeeded
        """
        result = self.state.promote(belief_id)
        if result:
            # Remove from TTL registry - verified beliefs don't expire
            self._ttl_registry.pop(belief_id, None)
        return result

    def check_promotions(self) -> List[str]:
        """
        Check all provisional beliefs for automatic promotion.

        Returns:
            List of belief IDs that were promoted
        """
        promoted = []

        for belief_id, belief in list(self.state.provisional.items()):
            if self.criteria.evaluate(belief):
                if self.promote(belief_id):
                    promoted.append(belief_id)

        return promoted

    def update_confidence(self, belief_id: str, new_confidence: float) -> bool:
        """
        Update a belief's confidence level.

        Args:
            belief_id: The belief to update
            new_confidence: New confidence value [0, 1]

        Returns:
            True if update succeeded
        """
        belief = self.state.get_belief(belief_id)
        if belief is None:
            return False

        belief.confidence = new_confidence
        return True

    def add_corroboration(self, belief_id: str, corroborating_agent: str) -> bool:
        """
        Add corroboration to a belief.

        Args:
            belief_id: The belief being corroborated
            corroborating_agent: Agent providing corroboration

        Returns:
            True if corroboration was added
        """
        belief = self.state.get_belief(belief_id)
        if belief is None:
            return False

        # Track unique corroborators
        if belief_id not in self._corroborators:
            self._corroborators[belief_id] = set()

        if corroborating_agent not in self._corroborators[belief_id]:
            self._corroborators[belief_id].add(corroborating_agent)
            belief.corroboration_count += 1

        return True

    def get_stats(self) -> Dict:
        """Get sandbox statistics."""
        now = datetime.now()
        soon_expiring = sum(
            1
            for expiry in self._ttl_registry.values()
            if (expiry - now).total_seconds() < 60
        )

        return {
            "verified_count": len(self.state.verified),
            "provisional_count": len(self.state.provisional),
            "soon_expiring": soon_expiring,
            "total_beliefs": len(self.state.verified) + len(self.state.provisional),
        }

    def extend_ttl(self, belief_id: str, extension_seconds: float) -> bool:
        """
        Extend the TTL of a provisional belief.

        Args:
            belief_id: The belief to extend
            extension_seconds: Seconds to add to TTL

        Returns:
            True if extension succeeded
        """
        if belief_id not in self._ttl_registry:
            return False

        self._ttl_registry[belief_id] += timedelta(seconds=extension_seconds)
        return True

    def get_expiry(self, belief_id: str) -> Optional[datetime]:
        """Get the expiry time for a belief."""
        return self._ttl_registry.get(belief_id)
