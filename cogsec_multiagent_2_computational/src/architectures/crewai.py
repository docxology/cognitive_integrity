"""CrewAI architecture: role-based crews of 3-10 agents.

Models the CrewAI framework where agents are assigned distinct roles
(researcher, writer, reviewer, etc.) and collaborate in a chain pattern.
Same-role trust is high, cross-role trust is moderate, and role
separation provides natural security boundaries.

Trust characteristics:
- Self-trust: 1.0
- Same-role: 0.85
- Adjacent role in chain: 0.7
- Non-adjacent cross-role: 0.5
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile

# Canonical role pool -- agents cycle through this list
_ROLE_POOL = [
    "researcher",
    "writer",
    "reviewer",
    "analyst",
    "coordinator",
    "data_engineer",
    "strategist",
    "quality_lead",
    "domain_expert",
    "integrator",
]


class CrewAIAdapter(ArchitectureAdapter):
    """Adapter for the CrewAI role-based crew architecture."""

    _PROFILE = ArchitectureProfile(
        name="CrewAI",
        agent_count_range=(3, 10),
        trust_topology="role_based",
        has_central_orchestrator=False,
        communication_pattern="chain",
        delegation_depth=3,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Role-aware trust: high within role, moderate across adjacent roles.

        Agents are assigned roles from ``_ROLE_POOL`` in order.  Trust
        between agents i and j depends on whether they share a role
        and their positional distance in the chain.
        """
        self._validate_n(n_agents)
        roles = self.get_agent_roles(n_agents)
        T = np.zeros((n_agents, n_agents), dtype=np.float64)

        for i in range(n_agents):
            for j in range(n_agents):
                if i == j:
                    T[i, j] = 1.0
                elif roles[i] == roles[j]:
                    # Same-role trust
                    T[i, j] = 0.85
                elif abs(i - j) == 1:
                    # Adjacent in chain
                    T[i, j] = 0.7
                else:
                    # Non-adjacent cross-role
                    T[i, j] = 0.5

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        """Assign roles cyclically from the role pool."""
        self._validate_n(n_agents)
        return [_ROLE_POOL[i % len(_ROLE_POOL)] for i in range(n_agents)]

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Chain topology: each agent communicates with its neighbors."""
        self._validate_n(n_agents)
        G = np.zeros((n_agents, n_agents), dtype=np.float64)

        for i in range(n_agents - 1):
            G[i, i + 1] = 1.0
            G[i + 1, i] = 1.0

        return G

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Chain delegation with 0.8 decay per hop, max depth 3."""
        if source == target:
            return 1.0
        max_depth = min(depth, self.profile.delegation_depth)
        hops = abs(target - source)
        if hops > max_depth:
            return 0.0
        decay = 0.8
        return float(0.7 * (decay ** (hops - 1)))

    def get_attack_surface_multiplier(self) -> float:
        """Role separation provides moderate security boundaries."""
        return 0.9
