"""Abstract base for multi-agent architecture adapters.

Defines the ``ArchitectureProfile`` descriptor and ``ArchitectureAdapter``
abstract base class that every concrete adapter must implement.  The adapter
contract provides trust-matrix generation, communication-graph construction,
role assignment, delegation simulation, and attack-surface estimation for
each architecture topology.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Architecture profile descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArchitectureProfile:
    """Immutable descriptor for a multi-agent architecture topology.

    Attributes:
        name: Human-readable architecture name.
        agent_count_range: ``(min, max)`` supported agent count.
        trust_topology: Topology label (``hierarchical``, ``flat``,
            ``role_based``, ``graph``, ``sop``, ``debate``).
        has_central_orchestrator: Whether a single orchestrator coordinates.
        communication_pattern: Message-passing pattern (``hub_spoke``,
            ``mesh``, ``chain``, ``broadcast``).
        delegation_depth: Maximum delegation chain length.
    """

    name: str
    agent_count_range: Tuple[int, int]
    trust_topology: str
    has_central_orchestrator: bool
    communication_pattern: str
    delegation_depth: int

    def __post_init__(self) -> None:
        lo, hi = self.agent_count_range
        if lo < 1 or hi < lo:
            raise ValueError(
                f"agent_count_range must satisfy 1 <= min <= max, got ({lo}, {hi})"
            )
        valid_topologies = {"hierarchical", "flat", "role_based", "graph", "sop", "debate"}
        if self.trust_topology not in valid_topologies:
            raise ValueError(
                f"trust_topology must be one of {valid_topologies}, got '{self.trust_topology}'"
            )
        valid_patterns = {"hub_spoke", "mesh", "chain", "broadcast"}
        if self.communication_pattern not in valid_patterns:
            raise ValueError(
                f"communication_pattern must be one of {valid_patterns}, "
                f"got '{self.communication_pattern}'"
            )
        if self.delegation_depth < 0:
            raise ValueError(
                f"delegation_depth must be >= 0, got {self.delegation_depth}"
            )


# ---------------------------------------------------------------------------
# Abstract architecture adapter
# ---------------------------------------------------------------------------

class ArchitectureAdapter(ABC):
    """Abstract base class for multi-agent architecture adapters.

    Concrete subclasses model real production frameworks (Claude Code,
    AutoGPT, CrewAI, LangGraph, MetaGPT, CAMEL) and expose their
    trust topology, communication graph, and attack-surface
    characteristics to the evaluation framework.
    """

    @property
    @abstractmethod
    def profile(self) -> ArchitectureProfile:
        """Return the immutable architecture profile."""
        ...

    def _validate_n(self, n_agents: int) -> None:
        """Raise if *n_agents* is outside the supported range."""
        lo, hi = self.profile.agent_count_range
        if n_agents < lo or n_agents > hi:
            raise ValueError(
                f"{self.profile.name} supports {lo}-{hi} agents, got {n_agents}"
            )

    @abstractmethod
    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Return an *n x n* trust matrix reflecting the topology.

        Entry ``[i, j]`` represents the trust that agent *i* places in
        agent *j*.  Values are in ``[0, 1]`` with the diagonal
        typically equal to ``1.0`` (self-trust).
        """
        ...

    @abstractmethod
    def get_agent_roles(self, n_agents: int) -> List[str]:
        """Return role labels for each of the *n_agents* agents."""
        ...

    @abstractmethod
    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Return an *n x n* binary adjacency matrix.

        Entry ``[i, j] = 1`` means agent *i* can send messages to agent *j*.
        """
        ...

    @abstractmethod
    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Simulate trust delegation from *source* to *target*.

        Returns the effective trust after delegation through *depth*
        intermediate hops, applying the architecture's trust-decay model.
        """
        ...

    @abstractmethod
    def get_attack_surface_multiplier(self) -> float:
        """Return the architecture-specific attack surface modifier.

        Values < 1.0 indicate a topology that inherently reduces
        attack surface; values > 1.0 indicate expanded surface.
        """
        ...
