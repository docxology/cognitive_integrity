"""AutoGPT architecture: autonomous agent with plugin extensions.

Models the AutoGPT autonomous agent pattern where a single main agent
utilises plugin modules.  Trust is flat -- the main agent trusts
plugins moderately but plugins have limited trust in each other.

Trust characteristics:
- Main agent self-trust: 1.0
- Main agent -> plugin: 0.7
- Plugin -> main agent: 0.8
- Plugin -> plugin: 0.4 (low lateral trust)
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile


class AutoGPTAdapter(ArchitectureAdapter):
    """Adapter for the AutoGPT autonomous + plugins architecture."""

    _PROFILE = ArchitectureProfile(
        name="AutoGPT",
        agent_count_range=(1, 5),
        trust_topology="flat",
        has_central_orchestrator=False,
        communication_pattern="mesh",
        delegation_depth=1,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Flat trust: main agent at 0, plugins at 1..n-1.

        - Diagonal: 1.0
        - Main -> plugin: 0.7
        - Plugin -> main: 0.8
        - Plugin -> plugin: 0.4
        """
        self._validate_n(n_agents)
        T = np.full((n_agents, n_agents), 0.4, dtype=np.float64)
        np.fill_diagonal(T, 1.0)

        if n_agents > 1:
            # Main agent trusts plugins moderately
            T[0, 1:] = 0.7
            # Plugins trust main agent more
            T[1:, 0] = 0.8

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        self._validate_n(n_agents)
        return ["main_agent"] + ["plugin"] * (n_agents - 1)

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Mesh: all agents can communicate with all others."""
        self._validate_n(n_agents)
        G = np.ones((n_agents, n_agents), dtype=np.float64)
        np.fill_diagonal(G, 0.0)
        return G

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Shallow delegation (max depth 1), decayed trust."""
        if source == target:
            return 1.0
        max_depth = min(depth, self.profile.delegation_depth)
        if max_depth == 0:
            return 0.0
        # Direct trust only (depth 1)
        if source == 0:
            return 0.7
        if target == 0:
            return 0.8
        return 0.4

    def get_attack_surface_multiplier(self) -> float:
        """Plugins expand the attack surface."""
        return 1.2
