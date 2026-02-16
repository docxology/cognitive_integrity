"""MetaGPT architecture: SOP-driven role-based collaboration.

Models the MetaGPT framework where agents follow a Standard Operating
Procedure with well-defined roles (Product Manager, Architect, Engineer,
QA Engineer, Designer).  The SOP defines a strict ordering and trust
chain that constrains agent interactions.

Trust characteristics:
- Self-trust: 1.0
- SOP-adjacent roles (e.g. PM -> Architect): 0.85
- SOP-separated by 1 hop: 0.65
- SOP-separated by 2+ hops: 0.45
"""

from __future__ import annotations

from typing import List

import numpy as np

from .base import ArchitectureAdapter, ArchitectureProfile

# SOP role chain -- strict ordering
_SOP_ROLES = [
    "product_manager",
    "architect",
    "engineer",
    "qa_engineer",
    "designer",
    "project_lead",
    "tech_writer",
    "devops",
]


class MetaGPTAdapter(ArchitectureAdapter):
    """Adapter for the MetaGPT SOP-driven architecture."""

    _PROFILE = ArchitectureProfile(
        name="MetaGPT",
        agent_count_range=(5, 8),
        trust_topology="sop",
        has_central_orchestrator=True,
        communication_pattern="chain",
        delegation_depth=3,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        """SOP-ordered trust: adjacent roles trust each other highly.

        Trust decays with SOP distance.  The Product Manager (agent 0)
        acts as the central orchestrator.
        """
        self._validate_n(n_agents)
        T = np.zeros((n_agents, n_agents), dtype=np.float64)

        for i in range(n_agents):
            for j in range(n_agents):
                if i == j:
                    T[i, j] = 1.0
                else:
                    sop_distance = abs(i - j)
                    if sop_distance == 1:
                        T[i, j] = 0.85
                    elif sop_distance == 2:
                        T[i, j] = 0.65
                    else:
                        T[i, j] = 0.45

        return T

    def get_agent_roles(self, n_agents: int) -> List[str]:
        """Assign roles from the SOP chain."""
        self._validate_n(n_agents)
        return [_SOP_ROLES[i % len(_SOP_ROLES)] for i in range(n_agents)]

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        """SOP chain: each role communicates with its SOP neighbors.

        The product manager (agent 0) also has direct lines to all
        roles as the central orchestrator.
        """
        self._validate_n(n_agents)
        G = np.zeros((n_agents, n_agents), dtype=np.float64)

        # Chain edges
        for i in range(n_agents - 1):
            G[i, i + 1] = 1.0
            G[i + 1, i] = 1.0

        # Orchestrator (PM) connects to all
        for i in range(1, n_agents):
            G[0, i] = 1.0
            G[i, 0] = 1.0

        return G

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        """SOP delegation: trust decays by 0.78 per SOP hop, max depth 3."""
        if source == target:
            return 1.0
        max_depth = min(depth, self.profile.delegation_depth)
        sop_distance = abs(target - source)
        effective_hops = min(sop_distance, max_depth)
        if effective_hops == 0:
            return 0.0

        # Base trust from SOP adjacency
        if sop_distance == 1:
            base = 0.85
        elif sop_distance == 2:
            base = 0.65
        else:
            base = 0.45

        decay = 0.78
        return float(base * (decay ** (effective_hops - 1)))

    def get_attack_surface_multiplier(self) -> float:
        """SOP constraints significantly reduce attack surface."""
        return 0.8
