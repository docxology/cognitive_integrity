"""Claude Code architecture: hierarchical (1+n) with hub-spoke communication.

Models the Claude Code multi-agent setup where a single orchestrator
delegates to sub-agents.  The orchestrator maintains high trust to all
sub-agents and controls the communication flow in a hub-spoke pattern.

Trust characteristics:
- Orchestrator self-trust: 1.0
- Orchestrator -> sub-agent: 0.9
- Sub-agent -> orchestrator: 0.85
- Sub-agent -> sub-agent: 0.5 (indirect via orchestrator)
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile


class ClaudeCodeAdapter(ArchitectureAdapter):
    """Adapter for the Claude Code hierarchical (1+n) architecture."""

    _PROFILE = ArchitectureProfile(
        name="Claude Code",
        agent_count_range=(2, 20),
        trust_topology="hierarchical",
        has_central_orchestrator=True,
        communication_pattern="hub_spoke",
        delegation_depth=2,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Build a hierarchical trust matrix with orchestrator at index 0.

        - Diagonal (self-trust): 1.0
        - Orchestrator -> sub-agent: 0.9
        - Sub-agent -> orchestrator: 0.85
        - Sub-agent -> sub-agent: 0.5 (mediated)
        """
        self._validate_n(n_agents)
        T = np.full((n_agents, n_agents), 0.5, dtype=np.float64)
        np.fill_diagonal(T, 1.0)

        # Orchestrator trusts sub-agents highly
        T[0, 1:] = 0.9
        # Sub-agents trust orchestrator
        T[1:, 0] = 0.85

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        self._validate_n(n_agents)
        return ["orchestrator"] + ["sub_agent"] * (n_agents - 1)

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Hub-spoke: orchestrator connects to all; sub-agents only to orchestrator."""
        self._validate_n(n_agents)
        G = np.zeros((n_agents, n_agents), dtype=np.float64)

        # Orchestrator -> all sub-agents
        G[0, 1:] = 1.0
        # Sub-agents -> orchestrator
        G[1:, 0] = 1.0

        return G

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Delegation decays by 0.85 per hop; capped at delegation_depth=2."""
        max_depth = min(depth, self.profile.delegation_depth)
        if source == target:
            return 1.0
        # Base trust depends on whether orchestrator is involved
        base = 0.9 if source == 0 or target == 0 else 0.5
        decay = 0.85
        return float(base * (decay ** max(0, max_depth - 1)))

    def get_attack_surface_multiplier(self) -> float:
        """Centralized control reduces attack surface."""
        return 0.7
