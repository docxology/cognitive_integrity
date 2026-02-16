"""CAMEL architecture: debate-style with 2+ agents.

Models the CAMEL (Communicative Agents for Mind Exploration of Large-scale
tasks) framework where agents engage in structured debate.  A proponent
and opponent exchange arguments while optional judge agents evaluate.

Trust characteristics:
- Self-trust: 1.0
- Debater -> debater: 0.6 (adversarial by design)
- Debater -> judge: 0.75
- Judge -> debater: 0.7
- Judge -> judge: 0.8
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile


class CamelAdapter(ArchitectureAdapter):
    """Adapter for the CAMEL debate-style architecture."""

    _PROFILE = ArchitectureProfile(
        name="CAMEL",
        agent_count_range=(2, 6),
        trust_topology="debate",
        has_central_orchestrator=False,
        communication_pattern="broadcast",
        delegation_depth=1,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """Debate-symmetric trust: adversarial between debaters, higher with judges.

        Agents 0 and 1 are the proponent and opponent (debaters).
        Agents 2..n-1 are judges (if present).
        """
        self._validate_n(n_agents)
        roles = self.get_agent_roles(n_agents)
        T = np.zeros((n_agents, n_agents), dtype=np.float64)

        for i in range(n_agents):
            for j in range(n_agents):
                if i == j:
                    T[i, j] = 1.0
                    continue

                ri = roles[i]
                rj = roles[j]

                if ri in ("proponent", "opponent") and rj in ("proponent", "opponent"):
                    # Debater <-> debater: adversarial moderate trust
                    T[i, j] = 0.6
                elif ri in ("proponent", "opponent") and rj == "judge":
                    # Debater -> judge
                    T[i, j] = 0.75
                elif ri == "judge" and rj in ("proponent", "opponent"):
                    # Judge -> debater
                    T[i, j] = 0.7
                else:
                    # Judge -> judge
                    T[i, j] = 0.8

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        """Proponent (0), opponent (1), judges (2..n-1)."""
        self._validate_n(n_agents)
        if n_agents == 2:
            return ["proponent", "opponent"]
        return ["proponent", "opponent"] + ["judge"] * (n_agents - 2)

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """Broadcast: every agent can communicate with every other agent."""
        self._validate_n(n_agents)
        G = np.ones((n_agents, n_agents), dtype=np.float64)
        np.fill_diagonal(G, 0.0)
        return G

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """Debate delegation is flat (max depth 1), direct trust only."""
        if source == target:
            return 1.0
        max_depth = min(depth, self.profile.delegation_depth)
        if max_depth == 0:
            return 0.0

        # Direct trust based on role pairing
        roles = ["proponent", "opponent"] + ["judge"] * max(0, max(source, target) - 1)
        rs = roles[source] if source < len(roles) else "judge"
        rt = roles[target] if target < len(roles) else "judge"

        if rs in ("proponent", "opponent") and rt in ("proponent", "opponent"):
            return 0.6
        if rs in ("proponent", "opponent") and rt == "judge":
            return 0.75
        if rs == "judge" and rt in ("proponent", "opponent"):
            return 0.7
        return 0.8  # judge <-> judge

    def get_attack_surface_multiplier(self) -> float:
        """Debate provides natural verification -- neutral surface."""
        return 1.0
