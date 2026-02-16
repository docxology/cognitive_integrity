"""LangGraph architecture: graph-based state machine with conditional edges.

Models the LangGraph framework where agents are nodes in a directed
graph and transitions between them are governed by a central state
manager.  The state machine constrains control flow, limiting
arbitrary agent-to-agent communication.

Trust characteristics:
- State manager self-trust: 1.0
- State manager -> node agent: 0.85
- Node agent -> state manager: 0.9
- Connected node -> node: 0.6
- Non-connected node -> node: 0.3
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile


class LangGraphAdapter(ArchitectureAdapter):
    """Adapter for the LangGraph graph-based state machine architecture."""

    _PROFILE = ArchitectureProfile(
        name="LangGraph",
        agent_count_range=(2, 50),
        trust_topology="graph",
        has_central_orchestrator=True,
        communication_pattern="mesh",
        delegation_depth=4,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def _build_state_graph(self, n_agents: int) -> np.ndarray:
        """Build a directed graph reflecting state transitions.

        Agent 0 is the state manager.  Remaining agents form a
        chain-like graph with additional forward edges every 3 nodes
        to model conditional branching.
        """
        G = np.zeros((n_agents, n_agents), dtype=np.float64)

        # State manager connects to and from all nodes
        for i in range(1, n_agents):
            G[0, i] = 1.0
            G[i, 0] = 1.0

        # Node agents form a chain with skip-ahead edges
        for i in range(1, n_agents - 1):
            G[i, i + 1] = 1.0
            # Conditional forward edge (skip 2) for branching
            if i + 3 < n_agents:
                G[i, i + 3] = 1.0

        return G

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Graph-topology-aware trust matrix.

        Trust is higher along edges in the state graph and lower
        between non-connected nodes.
        """
        self._validate_n(n_agents)
        G = self._build_state_graph(n_agents)
        T = np.full((n_agents, n_agents), 0.3, dtype=np.float64)
        np.fill_diagonal(T, 1.0)

        # State manager trusts and is trusted
        T[0, 1:] = 0.85
        T[1:, 0] = 0.9

        # Connected nodes get elevated trust
        for i in range(1, n_agents):
            for j in range(1, n_agents):
                if i != j and (G[i, j] > 0 or G[j, i] > 0):
                    T[i, j] = 0.6

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        self._validate_n(n_agents)
        return ["state_manager"] + ["node_agent"] * (n_agents - 1)

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Return the state-transition graph as the communication graph."""
        self._validate_n(n_agents)
        return self._build_state_graph(n_agents)

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Graph delegation with 0.82 decay per hop, max depth 4."""
        if source == target:
            return 1.0
        max_depth = min(depth, self.profile.delegation_depth)
        if max_depth == 0:
            return 0.0

        # Base trust depends on state-manager involvement
        if source == 0:
            base = 0.85
        elif target == 0:
            base = 0.9
        else:
            base = 0.6

        decay = 0.82
        hops = min(abs(target - source), max_depth)
        return float(base * (decay ** (hops - 1)))

    def get_attack_surface_multiplier(self) -> float:
        """State machine constrains flow, reducing attack surface."""
        return 0.85
