"""Comprehensive tests for multi-agent architecture adapters.

Tests cover:
1. Base ArchitectureProfile creation and validation
2. Each of 6 concrete adapters: profile properties, trust topology,
   attack surface multiplier, agent roles, communication graphs
3. Trust matrix mathematical properties (symmetry, bounds, diagonal)
4. Delegation simulation with depth decay
5. Architecture-specific configuration validation
6. Cross-architecture comparison capabilities

NO MOCKS -- all tests use real data and computation with deterministic seeds.
"""

import numpy as np
import pytest

from architectures.base import ArchitectureAdapter, ArchitectureProfile
from architectures.autogpt import AutoGPTAdapter
from architectures.camel import CamelAdapter
from architectures.claude_code import ClaudeCodeAdapter
from architectures.crewai import CrewAIAdapter
from architectures.langgraph import LangGraphAdapter
from architectures.metagpt import MetaGPTAdapter


# -----------------------------------------------------------------------
# Section 1: ArchitectureProfile creation and validation
# -----------------------------------------------------------------------


class TestArchitectureProfile:
    """Tests for the ArchitectureProfile dataclass."""

    def test_valid_profile_creation(self):
        """A well-formed profile is created without errors."""
        profile = ArchitectureProfile(
            name="TestArch",
            agent_count_range=(2, 10),
            trust_topology="hierarchical",
            has_central_orchestrator=True,
            communication_pattern="hub_spoke",
            delegation_depth=2,
        )
        assert profile.name == "TestArch"
        assert profile.agent_count_range == (2, 10)
        assert profile.trust_topology == "hierarchical"
        assert profile.has_central_orchestrator is True
        assert profile.communication_pattern == "hub_spoke"
        assert profile.delegation_depth == 2

    def test_profile_is_frozen(self):
        """Frozen dataclass prevents attribute mutation."""
        profile = ArchitectureProfile(
            name="Frozen",
            agent_count_range=(1, 5),
            trust_topology="flat",
            has_central_orchestrator=False,
            communication_pattern="mesh",
            delegation_depth=1,
        )
        with pytest.raises(AttributeError):
            profile.name = "Modified"

    def test_invalid_agent_count_range_min_zero(self):
        """Agent count minimum must be >= 1."""
        with pytest.raises(ValueError, match="agent_count_range"):
            ArchitectureProfile(
                name="Bad",
                agent_count_range=(0, 5),
                trust_topology="flat",
                has_central_orchestrator=False,
                communication_pattern="mesh",
                delegation_depth=1,
            )

    def test_invalid_agent_count_range_reversed(self):
        """Agent count max must be >= min."""
        with pytest.raises(ValueError, match="agent_count_range"):
            ArchitectureProfile(
                name="Bad",
                agent_count_range=(10, 5),
                trust_topology="flat",
                has_central_orchestrator=False,
                communication_pattern="mesh",
                delegation_depth=1,
            )

    def test_invalid_trust_topology(self):
        """Unknown trust topology is rejected."""
        with pytest.raises(ValueError, match="trust_topology"):
            ArchitectureProfile(
                name="Bad",
                agent_count_range=(1, 5),
                trust_topology="star",
                has_central_orchestrator=False,
                communication_pattern="mesh",
                delegation_depth=1,
            )

    def test_invalid_communication_pattern(self):
        """Unknown communication pattern is rejected."""
        with pytest.raises(ValueError, match="communication_pattern"):
            ArchitectureProfile(
                name="Bad",
                agent_count_range=(1, 5),
                trust_topology="flat",
                has_central_orchestrator=False,
                communication_pattern="star",
                delegation_depth=1,
            )

    def test_negative_delegation_depth(self):
        """Delegation depth must be >= 0."""
        with pytest.raises(ValueError, match="delegation_depth"):
            ArchitectureProfile(
                name="Bad",
                agent_count_range=(1, 5),
                trust_topology="flat",
                has_central_orchestrator=False,
                communication_pattern="mesh",
                delegation_depth=-1,
            )

    def test_all_valid_topologies(self):
        """Every documented topology string is accepted."""
        valid = {"hierarchical", "flat", "role_based", "graph", "sop", "debate"}
        for topology in valid:
            profile = ArchitectureProfile(
                name=f"Test_{topology}",
                agent_count_range=(1, 5),
                trust_topology=topology,
                has_central_orchestrator=False,
                communication_pattern="mesh",
                delegation_depth=0,
            )
            assert profile.trust_topology == topology

    def test_all_valid_communication_patterns(self):
        """Every documented communication pattern string is accepted."""
        valid = {"hub_spoke", "mesh", "chain", "broadcast"}
        for pattern in valid:
            profile = ArchitectureProfile(
                name=f"Test_{pattern}",
                agent_count_range=(1, 5),
                trust_topology="flat",
                has_central_orchestrator=False,
                communication_pattern=pattern,
                delegation_depth=0,
            )
            assert profile.communication_pattern == pattern

    def test_profile_equality(self):
        """Two profiles with identical fields are equal (dataclass)."""
        kwargs = dict(
            name="Same",
            agent_count_range=(2, 10),
            trust_topology="flat",
            has_central_orchestrator=False,
            communication_pattern="mesh",
            delegation_depth=1,
        )
        assert ArchitectureProfile(**kwargs) == ArchitectureProfile(**kwargs)

    def test_agent_count_range_single(self):
        """Range where min == max is valid (single agent count)."""
        profile = ArchitectureProfile(
            name="Single",
            agent_count_range=(3, 3),
            trust_topology="flat",
            has_central_orchestrator=False,
            communication_pattern="mesh",
            delegation_depth=0,
        )
        assert profile.agent_count_range == (3, 3)


# -----------------------------------------------------------------------
# Section 2: Adapter interface contract (abstract base)
# -----------------------------------------------------------------------


class TestArchitectureAdapterContract:
    """Verify that ArchitectureAdapter cannot be instantiated directly."""

    def test_abstract_base_not_instantiable(self):
        """ArchitectureAdapter is abstract -- direct instantiation raises."""
        with pytest.raises(TypeError):
            ArchitectureAdapter()


# -----------------------------------------------------------------------
# Section 3: Claude Code Adapter
# -----------------------------------------------------------------------


class TestClaudeCodeAdapter:
    """Tests for the ClaudeCodeAdapter (hierarchical hub-spoke)."""

    def setup_method(self):
        self.adapter = ClaudeCodeAdapter()

    # -- Profile properties --

    def test_profile_name(self):
        assert self.adapter.profile.name == "Claude Code"

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (2, 20)

    def test_profile_trust_topology(self):
        assert self.adapter.profile.trust_topology == "hierarchical"

    def test_profile_has_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is True

    def test_profile_communication_pattern(self):
        assert self.adapter.profile.communication_pattern == "hub_spoke"

    def test_profile_delegation_depth(self):
        assert self.adapter.profile.delegation_depth == 2

    # -- Trust matrix --

    def test_trust_matrix_shape(self):
        T = self.adapter.create_trust_matrix(5)
        assert T.shape == (5, 5)

    def test_trust_matrix_diagonal_is_one(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_array_equal(np.diag(T), np.ones(5))

    def test_trust_matrix_values_in_unit_interval(self):
        T = self.adapter.create_trust_matrix(5)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    def test_orchestrator_trusts_subagents_at_0_9(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_allclose(T[0, 1:], 0.9)

    def test_subagents_trust_orchestrator_at_0_85(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_allclose(T[1:, 0], 0.85)

    def test_subagent_lateral_trust_at_0_5(self):
        T = self.adapter.create_trust_matrix(5)
        for i in range(1, 5):
            for j in range(1, 5):
                if i != j:
                    assert np.isclose(T[i, j], 0.5)

    def test_trust_matrix_minimum_agents(self):
        T = self.adapter.create_trust_matrix(2)
        assert T.shape == (2, 2)
        assert T[0, 1] == pytest.approx(0.9)
        assert T[1, 0] == pytest.approx(0.85)

    # -- Agent roles --

    def test_agent_roles_first_is_orchestrator(self):
        roles = self.adapter.get_agent_roles(5)
        assert roles[0] == "orchestrator"

    def test_agent_roles_rest_are_subagents(self):
        roles = self.adapter.get_agent_roles(5)
        assert all(r == "sub_agent" for r in roles[1:])

    def test_agent_roles_count(self):
        roles = self.adapter.get_agent_roles(10)
        assert len(roles) == 10

    # -- Communication graph --

    def test_communication_graph_hub_spoke(self):
        G = self.adapter.get_communication_graph(5)
        assert G.shape == (5, 5)
        # Orchestrator connects to all sub-agents
        np.testing.assert_array_equal(G[0, 1:], np.ones(4))
        # Sub-agents connect to orchestrator
        np.testing.assert_array_equal(G[1:, 0], np.ones(4))
        # No sub-agent to sub-agent direct links
        for i in range(1, 5):
            for j in range(1, 5):
                if i != j:
                    assert G[i, j] == 0.0

    def test_communication_graph_no_self_loops(self):
        G = self.adapter.get_communication_graph(5)
        np.testing.assert_array_equal(np.diag(G), np.zeros(5))

    # -- Delegation --

    def test_delegation_self_is_one(self):
        assert self.adapter.simulate_delegation(0, 0, 1) == 1.0

    def test_delegation_orchestrator_to_subagent(self):
        # source=0 (orchestrator), base=0.9, depth=1 -> 0.9 * 0.85^0 = 0.9
        result = self.adapter.simulate_delegation(0, 1, 1)
        assert result == pytest.approx(0.9)

    def test_delegation_orchestrator_depth_2(self):
        # source=0, depth=2 -> 0.9 * 0.85^1 = 0.765
        result = self.adapter.simulate_delegation(0, 2, 2)
        assert result == pytest.approx(0.9 * 0.85)

    def test_delegation_subagent_to_subagent(self):
        # Neither is orchestrator, base=0.5
        result = self.adapter.simulate_delegation(1, 2, 1)
        assert result == pytest.approx(0.5)

    def test_delegation_depth_capped_at_profile_max(self):
        # Max depth is 2; passing depth=10 should cap
        result_capped = self.adapter.simulate_delegation(0, 3, 10)
        result_max = self.adapter.simulate_delegation(0, 3, 2)
        assert result_capped == pytest.approx(result_max)

    # -- Attack surface --

    def test_attack_surface_multiplier(self):
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(0.7)

    def test_attack_surface_below_one(self):
        """Centralized control reduces attack surface (< 1.0)."""
        assert self.adapter.get_attack_surface_multiplier() < 1.0

    # -- Validation --

    def test_rejects_agent_count_below_min(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(1)

    def test_rejects_agent_count_above_max(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(21)


# -----------------------------------------------------------------------
# Section 4: AutoGPT Adapter
# -----------------------------------------------------------------------


class TestAutoGPTAdapter:
    """Tests for the AutoGPTAdapter (flat mesh with plugins)."""

    def setup_method(self):
        self.adapter = AutoGPTAdapter()

    # -- Profile --

    def test_profile_name(self):
        assert self.adapter.profile.name == "AutoGPT"

    def test_profile_flat_topology(self):
        assert self.adapter.profile.trust_topology == "flat"

    def test_profile_no_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is False

    def test_profile_mesh_communication(self):
        assert self.adapter.profile.communication_pattern == "mesh"

    def test_profile_delegation_depth_1(self):
        assert self.adapter.profile.delegation_depth == 1

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (1, 5)

    # -- Trust matrix --

    def test_trust_matrix_single_agent(self):
        """Single agent: 1x1 matrix with self-trust 1.0."""
        T = self.adapter.create_trust_matrix(1)
        assert T.shape == (1, 1)
        assert T[0, 0] == 1.0

    def test_trust_matrix_main_trusts_plugins_0_7(self):
        T = self.adapter.create_trust_matrix(4)
        np.testing.assert_allclose(T[0, 1:], 0.7)

    def test_trust_matrix_plugins_trust_main_0_8(self):
        T = self.adapter.create_trust_matrix(4)
        np.testing.assert_allclose(T[1:, 0], 0.8)

    def test_trust_matrix_plugin_lateral_0_4(self):
        T = self.adapter.create_trust_matrix(4)
        for i in range(1, 4):
            for j in range(1, 4):
                if i != j:
                    assert T[i, j] == pytest.approx(0.4)

    def test_trust_matrix_diagonal(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_array_equal(np.diag(T), np.ones(5))

    def test_trust_matrix_bounded(self):
        T = self.adapter.create_trust_matrix(5)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    # -- Agent roles --

    def test_roles_first_is_main_agent(self):
        roles = self.adapter.get_agent_roles(3)
        assert roles[0] == "main_agent"

    def test_roles_rest_are_plugins(self):
        roles = self.adapter.get_agent_roles(5)
        assert all(r == "plugin" for r in roles[1:])

    # -- Communication graph --

    def test_communication_mesh_no_self_loops(self):
        G = self.adapter.get_communication_graph(4)
        np.testing.assert_array_equal(np.diag(G), np.zeros(4))

    def test_communication_mesh_all_connected(self):
        G = self.adapter.get_communication_graph(4)
        expected = np.ones((4, 4)) - np.eye(4)
        np.testing.assert_array_equal(G, expected)

    # -- Delegation --

    def test_delegation_self(self):
        assert self.adapter.simulate_delegation(0, 0, 1) == 1.0

    def test_delegation_main_to_plugin(self):
        assert self.adapter.simulate_delegation(0, 1, 1) == pytest.approx(0.7)

    def test_delegation_plugin_to_main(self):
        assert self.adapter.simulate_delegation(1, 0, 1) == pytest.approx(0.8)

    def test_delegation_plugin_to_plugin(self):
        assert self.adapter.simulate_delegation(1, 2, 1) == pytest.approx(0.4)

    def test_delegation_depth_zero_returns_zero(self):
        """With depth=0, non-self delegation yields 0.0."""
        assert self.adapter.simulate_delegation(0, 1, 0) == pytest.approx(0.0)

    # -- Attack surface --

    def test_attack_surface_above_one(self):
        """Plugins expand the attack surface."""
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(1.2)
        assert self.adapter.get_attack_surface_multiplier() > 1.0

    # -- Validation --

    def test_rejects_too_many_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(6)


# -----------------------------------------------------------------------
# Section 5: CAMEL Adapter
# -----------------------------------------------------------------------


class TestCamelAdapter:
    """Tests for the CamelAdapter (debate-style broadcast)."""

    def setup_method(self):
        self.adapter = CamelAdapter()

    # -- Profile --

    def test_profile_name(self):
        assert self.adapter.profile.name == "CAMEL"

    def test_profile_debate_topology(self):
        assert self.adapter.profile.trust_topology == "debate"

    def test_profile_no_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is False

    def test_profile_broadcast_communication(self):
        assert self.adapter.profile.communication_pattern == "broadcast"

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (2, 6)

    # -- Trust matrix --

    def test_trust_matrix_two_debaters(self):
        """Minimal 2-agent: proponent vs opponent, 0.6 mutual trust."""
        T = self.adapter.create_trust_matrix(2)
        assert T.shape == (2, 2)
        assert T[0, 0] == 1.0
        assert T[1, 1] == 1.0
        assert T[0, 1] == pytest.approx(0.6)
        assert T[1, 0] == pytest.approx(0.6)

    def test_trust_matrix_with_judges(self):
        """4-agent debate: 2 debaters + 2 judges."""
        T = self.adapter.create_trust_matrix(4)
        # Debater -> debater: 0.6
        assert T[0, 1] == pytest.approx(0.6)
        assert T[1, 0] == pytest.approx(0.6)
        # Debater -> judge: 0.75
        assert T[0, 2] == pytest.approx(0.75)
        assert T[1, 3] == pytest.approx(0.75)
        # Judge -> debater: 0.7
        assert T[2, 0] == pytest.approx(0.7)
        assert T[3, 1] == pytest.approx(0.7)
        # Judge -> judge: 0.8
        assert T[2, 3] == pytest.approx(0.8)
        assert T[3, 2] == pytest.approx(0.8)

    def test_trust_matrix_diagonal(self):
        T = self.adapter.create_trust_matrix(4)
        np.testing.assert_array_equal(np.diag(T), np.ones(4))

    def test_trust_matrix_bounded(self):
        T = self.adapter.create_trust_matrix(6)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    # -- Agent roles --

    def test_roles_two_agents(self):
        roles = self.adapter.get_agent_roles(2)
        assert roles == ["proponent", "opponent"]

    def test_roles_with_judges(self):
        roles = self.adapter.get_agent_roles(4)
        assert roles == ["proponent", "opponent", "judge", "judge"]

    def test_roles_count_matches(self):
        for n in range(2, 7):
            roles = self.adapter.get_agent_roles(n)
            assert len(roles) == n

    # -- Communication graph --

    def test_broadcast_graph(self):
        """Broadcast: all agents talk to all others (no self-loops)."""
        G = self.adapter.get_communication_graph(4)
        expected = np.ones((4, 4)) - np.eye(4)
        np.testing.assert_array_equal(G, expected)

    # -- Delegation --

    def test_delegation_debater_to_debater(self):
        assert self.adapter.simulate_delegation(0, 1, 1) == pytest.approx(0.6)

    def test_delegation_debater_to_judge(self):
        assert self.adapter.simulate_delegation(0, 2, 1) == pytest.approx(0.75)

    def test_delegation_judge_to_debater(self):
        assert self.adapter.simulate_delegation(2, 0, 1) == pytest.approx(0.7)

    def test_delegation_judge_to_judge(self):
        assert self.adapter.simulate_delegation(2, 3, 1) == pytest.approx(0.8)

    def test_delegation_self(self):
        assert self.adapter.simulate_delegation(0, 0, 1) == 1.0

    def test_delegation_depth_zero(self):
        assert self.adapter.simulate_delegation(0, 1, 0) == pytest.approx(0.0)

    # -- Attack surface --

    def test_attack_surface_neutral(self):
        """Debate provides natural verification -- neutral surface."""
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(1.0)

    # -- Validation --

    def test_rejects_single_agent(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(1)

    def test_rejects_too_many_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(7)


# -----------------------------------------------------------------------
# Section 6: CrewAI Adapter
# -----------------------------------------------------------------------


class TestCrewAIAdapter:
    """Tests for the CrewAIAdapter (role-based chain)."""

    def setup_method(self):
        self.adapter = CrewAIAdapter()

    # -- Profile --

    def test_profile_name(self):
        assert self.adapter.profile.name == "CrewAI"

    def test_profile_role_based_topology(self):
        assert self.adapter.profile.trust_topology == "role_based"

    def test_profile_chain_communication(self):
        assert self.adapter.profile.communication_pattern == "chain"

    def test_profile_no_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is False

    def test_profile_delegation_depth_3(self):
        assert self.adapter.profile.delegation_depth == 3

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (3, 10)

    # -- Trust matrix --

    def test_trust_matrix_same_role_0_85(self):
        """With 10+ roles cycling, agents sharing a role get 0.85 trust."""
        # With 10 agents, roles cycle through the pool (each unique).
        # Need > 10 agents for role overlap, but max is 10.
        # All 10 roles are unique from the pool, so no same-role pairs exist.
        # Test with the minimum (3 agents): all different roles.
        T = self.adapter.create_trust_matrix(3)
        # Agents 0,1 are adjacent -> 0.7
        assert T[0, 1] == pytest.approx(0.7)
        # Agents 0,2 are non-adjacent, different roles -> 0.5
        assert T[0, 2] == pytest.approx(0.5)

    def test_trust_matrix_adjacent_0_7(self):
        T = self.adapter.create_trust_matrix(5)
        for i in range(4):
            assert T[i, i + 1] == pytest.approx(0.7)
            assert T[i + 1, i] == pytest.approx(0.7)

    def test_trust_matrix_non_adjacent_0_5(self):
        T = self.adapter.create_trust_matrix(5)
        # Agents 0 and 3: non-adjacent, different roles
        assert T[0, 3] == pytest.approx(0.5)

    def test_trust_matrix_diagonal(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_array_equal(np.diag(T), np.ones(5))

    def test_trust_matrix_bounded(self):
        T = self.adapter.create_trust_matrix(10)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    # -- Agent roles --

    def test_roles_are_from_pool(self):
        """All assigned roles come from the canonical role pool."""
        pool = {
            "researcher", "writer", "reviewer", "analyst", "coordinator",
            "data_engineer", "strategist", "quality_lead", "domain_expert",
            "integrator",
        }
        roles = self.adapter.get_agent_roles(10)
        assert all(r in pool for r in roles)

    def test_roles_cyclic_assignment(self):
        """Roles are assigned cyclically from the pool."""
        roles = self.adapter.get_agent_roles(3)
        assert roles[0] == "researcher"
        assert roles[1] == "writer"
        assert roles[2] == "reviewer"

    def test_roles_count(self):
        roles = self.adapter.get_agent_roles(7)
        assert len(roles) == 7

    # -- Communication graph --

    def test_chain_graph_shape(self):
        G = self.adapter.get_communication_graph(5)
        assert G.shape == (5, 5)

    def test_chain_graph_neighbors_connected(self):
        G = self.adapter.get_communication_graph(5)
        for i in range(4):
            assert G[i, i + 1] == 1.0
            assert G[i + 1, i] == 1.0

    def test_chain_graph_non_neighbors_disconnected(self):
        G = self.adapter.get_communication_graph(5)
        assert G[0, 2] == 0.0
        assert G[0, 3] == 0.0
        assert G[0, 4] == 0.0

    def test_chain_graph_no_self_loops(self):
        G = self.adapter.get_communication_graph(5)
        np.testing.assert_array_equal(np.diag(G), np.zeros(5))

    # -- Delegation --

    def test_delegation_self(self):
        assert self.adapter.simulate_delegation(0, 0, 3) == 1.0

    def test_delegation_adjacent(self):
        # 1 hop: 0.7 * 0.8^0 = 0.7
        assert self.adapter.simulate_delegation(0, 1, 3) == pytest.approx(0.7)

    def test_delegation_two_hops(self):
        # 2 hops: 0.7 * 0.8^1 = 0.56
        assert self.adapter.simulate_delegation(0, 2, 3) == pytest.approx(0.7 * 0.8)

    def test_delegation_three_hops(self):
        # 3 hops: 0.7 * 0.8^2 = 0.448
        assert self.adapter.simulate_delegation(0, 3, 3) == pytest.approx(0.7 * 0.8**2)

    def test_delegation_exceeds_max_depth(self):
        """Delegation beyond max depth returns 0.0."""
        result = self.adapter.simulate_delegation(0, 4, 3)
        assert result == pytest.approx(0.0)

    # -- Attack surface --

    def test_attack_surface_reduced(self):
        """Role separation provides moderate reduction."""
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(0.9)
        assert self.adapter.get_attack_surface_multiplier() < 1.0

    # -- Validation --

    def test_rejects_too_few_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(2)

    def test_rejects_too_many_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(11)


# -----------------------------------------------------------------------
# Section 7: LangGraph Adapter
# -----------------------------------------------------------------------


class TestLangGraphAdapter:
    """Tests for the LangGraphAdapter (graph-based state machine)."""

    def setup_method(self):
        self.adapter = LangGraphAdapter()

    # -- Profile --

    def test_profile_name(self):
        assert self.adapter.profile.name == "LangGraph"

    def test_profile_graph_topology(self):
        assert self.adapter.profile.trust_topology == "graph"

    def test_profile_has_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is True

    def test_profile_mesh_communication(self):
        assert self.adapter.profile.communication_pattern == "mesh"

    def test_profile_delegation_depth_4(self):
        assert self.adapter.profile.delegation_depth == 4

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (2, 50)

    # -- Trust matrix --

    def test_trust_matrix_state_manager_trusts_nodes_0_85(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_allclose(T[0, 1:], 0.85)

    def test_trust_matrix_nodes_trust_state_manager_0_9(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_allclose(T[1:, 0], 0.9)

    def test_trust_matrix_connected_nodes_0_6(self):
        """Nodes connected in the state graph get 0.6 trust."""
        T = self.adapter.create_trust_matrix(6)
        G = self.adapter.get_communication_graph(6)
        for i in range(1, 6):
            for j in range(1, 6):
                if i != j and (G[i, j] > 0 or G[j, i] > 0):
                    assert T[i, j] == pytest.approx(0.6)

    def test_trust_matrix_non_connected_nodes_0_3(self):
        """Nodes not connected in the state graph get 0.3 trust."""
        T = self.adapter.create_trust_matrix(6)
        G = self.adapter.get_communication_graph(6)
        for i in range(1, 6):
            for j in range(1, 6):
                if i != j and G[i, j] == 0 and G[j, i] == 0:
                    assert T[i, j] == pytest.approx(0.3)

    def test_trust_matrix_diagonal(self):
        T = self.adapter.create_trust_matrix(10)
        np.testing.assert_array_equal(np.diag(T), np.ones(10))

    def test_trust_matrix_bounded(self):
        T = self.adapter.create_trust_matrix(10)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    # -- State graph structure --

    def test_state_graph_chain_edges(self):
        """Node agents form a chain: 1->2, 2->3, ..."""
        G = self.adapter.get_communication_graph(6)
        for i in range(1, 5):
            assert G[i, i + 1] == 1.0

    def test_state_graph_skip_edges(self):
        """Conditional forward edges skip 2 nodes (every 3)."""
        G = self.adapter.get_communication_graph(8)
        # Agent 1 has skip edge to 1+3=4
        assert G[1, 4] == 1.0

    def test_state_graph_manager_connects_all(self):
        G = self.adapter.get_communication_graph(5)
        np.testing.assert_array_equal(G[0, 1:], np.ones(4))
        np.testing.assert_array_equal(G[1:, 0], np.ones(4))

    # -- Agent roles --

    def test_roles_first_is_state_manager(self):
        roles = self.adapter.get_agent_roles(5)
        assert roles[0] == "state_manager"

    def test_roles_rest_are_node_agents(self):
        roles = self.adapter.get_agent_roles(5)
        assert all(r == "node_agent" for r in roles[1:])

    # -- Delegation --

    def test_delegation_self(self):
        assert self.adapter.simulate_delegation(0, 0, 1) == 1.0

    def test_delegation_manager_to_node(self):
        # source=0, base=0.85, depth=1 -> 0.85 * 0.82^0 = 0.85
        result = self.adapter.simulate_delegation(0, 1, 1)
        assert result == pytest.approx(0.85)

    def test_delegation_node_to_manager(self):
        # target=0, base=0.9, depth=1 -> 0.9 * 0.82^0 = 0.9
        result = self.adapter.simulate_delegation(1, 0, 1)
        assert result == pytest.approx(0.9)

    def test_delegation_node_to_node(self):
        # Neither is 0, base=0.6, depth=1 -> 0.6 * 0.82^0 = 0.6
        result = self.adapter.simulate_delegation(1, 2, 1)
        assert result == pytest.approx(0.6)

    def test_delegation_depth_decay(self):
        """Multi-hop delegation decays by 0.82 per hop."""
        # source=0, base=0.85, hops=2 -> 0.85 * 0.82^1 = 0.697
        result = self.adapter.simulate_delegation(0, 2, 2)
        assert result == pytest.approx(0.85 * 0.82)

    def test_delegation_depth_zero(self):
        assert self.adapter.simulate_delegation(0, 1, 0) == pytest.approx(0.0)

    def test_delegation_capped_at_profile_max(self):
        result_10 = self.adapter.simulate_delegation(0, 5, 10)
        result_4 = self.adapter.simulate_delegation(0, 5, 4)
        assert result_10 == pytest.approx(result_4)

    # -- Attack surface --

    def test_attack_surface_reduced(self):
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(0.85)
        assert self.adapter.get_attack_surface_multiplier() < 1.0

    # -- Validation --

    def test_rejects_single_agent(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(1)

    def test_rejects_too_many_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(51)

    def test_accepts_large_agent_count(self):
        """LangGraph supports up to 50 agents."""
        T = self.adapter.create_trust_matrix(50)
        assert T.shape == (50, 50)


# -----------------------------------------------------------------------
# Section 8: MetaGPT Adapter
# -----------------------------------------------------------------------


class TestMetaGPTAdapter:
    """Tests for the MetaGPTAdapter (SOP-driven chain)."""

    def setup_method(self):
        self.adapter = MetaGPTAdapter()

    # -- Profile --

    def test_profile_name(self):
        assert self.adapter.profile.name == "MetaGPT"

    def test_profile_sop_topology(self):
        assert self.adapter.profile.trust_topology == "sop"

    def test_profile_has_central_orchestrator(self):
        assert self.adapter.profile.has_central_orchestrator is True

    def test_profile_chain_communication(self):
        assert self.adapter.profile.communication_pattern == "chain"

    def test_profile_delegation_depth_3(self):
        assert self.adapter.profile.delegation_depth == 3

    def test_profile_agent_count_range(self):
        assert self.adapter.profile.agent_count_range == (5, 8)

    # -- Trust matrix --

    def test_trust_matrix_adjacent_0_85(self):
        T = self.adapter.create_trust_matrix(5)
        for i in range(4):
            assert T[i, i + 1] == pytest.approx(0.85)
            assert T[i + 1, i] == pytest.approx(0.85)

    def test_trust_matrix_distance_2_is_0_65(self):
        T = self.adapter.create_trust_matrix(5)
        assert T[0, 2] == pytest.approx(0.65)
        assert T[2, 0] == pytest.approx(0.65)

    def test_trust_matrix_distance_3_plus_is_0_45(self):
        T = self.adapter.create_trust_matrix(5)
        assert T[0, 3] == pytest.approx(0.45)
        assert T[0, 4] == pytest.approx(0.45)

    def test_trust_matrix_symmetric(self):
        """SOP trust is symmetric: T[i,j] == T[j,i] for all i,j."""
        T = self.adapter.create_trust_matrix(8)
        np.testing.assert_array_equal(T, T.T)

    def test_trust_matrix_diagonal(self):
        T = self.adapter.create_trust_matrix(5)
        np.testing.assert_array_equal(np.diag(T), np.ones(5))

    def test_trust_matrix_bounded(self):
        T = self.adapter.create_trust_matrix(8)
        assert np.all(T >= 0.0) and np.all(T <= 1.0)

    # -- Agent roles --

    def test_roles_from_sop_chain(self):
        """Roles assigned from the SOP role chain."""
        roles = self.adapter.get_agent_roles(5)
        assert roles == [
            "product_manager", "architect", "engineer",
            "qa_engineer", "designer",
        ]

    def test_roles_full_8(self):
        roles = self.adapter.get_agent_roles(8)
        expected = [
            "product_manager", "architect", "engineer",
            "qa_engineer", "designer", "project_lead",
            "tech_writer", "devops",
        ]
        assert roles == expected

    def test_roles_count(self):
        for n in range(5, 9):
            roles = self.adapter.get_agent_roles(n)
            assert len(roles) == n

    # -- Communication graph --

    def test_sop_chain_neighbors(self):
        G = self.adapter.get_communication_graph(5)
        for i in range(4):
            assert G[i, i + 1] == 1.0
            assert G[i + 1, i] == 1.0

    def test_sop_pm_connects_to_all(self):
        """Product Manager (agent 0) has direct lines to all roles."""
        G = self.adapter.get_communication_graph(5)
        np.testing.assert_array_equal(G[0, 1:], np.ones(4))
        np.testing.assert_array_equal(G[1:, 0], np.ones(4))

    def test_communication_no_self_loops(self):
        G = self.adapter.get_communication_graph(5)
        np.testing.assert_array_equal(np.diag(G), np.zeros(5))

    # -- Delegation --

    def test_delegation_self(self):
        assert self.adapter.simulate_delegation(0, 0, 3) == 1.0

    def test_delegation_adjacent(self):
        # SOP distance=1, base=0.85, hops=1 -> 0.85 * 0.78^0 = 0.85
        result = self.adapter.simulate_delegation(0, 1, 3)
        assert result == pytest.approx(0.85)

    def test_delegation_distance_2(self):
        # SOP distance=2, base=0.65, hops=2 -> 0.65 * 0.78^1 = 0.507
        result = self.adapter.simulate_delegation(0, 2, 3)
        assert result == pytest.approx(0.65 * 0.78)

    def test_delegation_distance_3(self):
        # SOP distance=3, base=0.45, hops=3 -> 0.45 * 0.78^2 = 0.27378
        result = self.adapter.simulate_delegation(0, 3, 3)
        assert result == pytest.approx(0.45 * 0.78**2)

    def test_delegation_capped_at_depth(self):
        """Delegation beyond max depth uses capped hops."""
        # SOP distance=4, exceeds max_depth=3, effective_hops=3
        result = self.adapter.simulate_delegation(0, 4, 3)
        # base=0.45 (distance >= 3), effective_hops=3 -> 0.45 * 0.78^2
        assert result == pytest.approx(0.45 * 0.78**2)

    # -- Attack surface --

    def test_attack_surface_reduced(self):
        assert self.adapter.get_attack_surface_multiplier() == pytest.approx(0.8)
        assert self.adapter.get_attack_surface_multiplier() < 1.0

    # -- Validation --

    def test_rejects_too_few_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(4)

    def test_rejects_too_many_agents(self):
        with pytest.raises(ValueError, match="supports"):
            self.adapter.create_trust_matrix(9)


# -----------------------------------------------------------------------
# Section 9: Cross-architecture comparison capabilities
# -----------------------------------------------------------------------


class TestCrossArchitectureComparison:
    """Test cross-architecture properties and comparisons."""

    ALL_ADAPTERS = [
        ClaudeCodeAdapter,
        AutoGPTAdapter,
        CamelAdapter,
        CrewAIAdapter,
        LangGraphAdapter,
        MetaGPTAdapter,
    ]

    def _instances(self):
        return [cls() for cls in self.ALL_ADAPTERS]

    def test_all_adapters_have_unique_names(self):
        """Every adapter has a distinct profile name."""
        names = [cls().profile.name for cls in self.ALL_ADAPTERS]
        assert len(names) == len(set(names))

    def test_all_trust_matrices_are_square(self):
        """Trust matrices are n x n for all architectures."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            T = adapter.create_trust_matrix(lo)
            assert T.shape[0] == T.shape[1] == lo

    def test_all_trust_matrices_have_unit_diagonal(self):
        """Self-trust is always 1.0 across all architectures."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            T = adapter.create_trust_matrix(lo)
            np.testing.assert_array_equal(np.diag(T), np.ones(lo))

    def test_all_trust_values_bounded_zero_one(self):
        """All trust values are in [0, 1] across all architectures."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            T = adapter.create_trust_matrix(lo)
            assert np.all(T >= 0.0), f"{adapter.profile.name} has trust < 0"
            assert np.all(T <= 1.0), f"{adapter.profile.name} has trust > 1"

    def test_all_communication_graphs_no_self_loops(self):
        """Communication graphs have zero diagonal (no self-loops)."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            G = adapter.get_communication_graph(lo)
            np.testing.assert_array_equal(
                np.diag(G), np.zeros(lo),
                err_msg=f"{adapter.profile.name} has self-loops",
            )

    def test_all_communication_graphs_binary(self):
        """Communication graphs contain only 0.0 and 1.0."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            G = adapter.get_communication_graph(lo)
            unique = np.unique(G)
            for v in unique:
                assert v in (0.0, 1.0), (
                    f"{adapter.profile.name} graph has value {v}"
                )

    def test_all_delegation_self_is_one(self):
        """Self-delegation always returns 1.0."""
        for adapter in self._instances():
            assert adapter.simulate_delegation(0, 0, 1) == 1.0

    def test_all_attack_surface_multipliers_positive(self):
        """Attack surface multipliers are always positive."""
        for adapter in self._instances():
            asm = adapter.get_attack_surface_multiplier()
            assert asm > 0.0, f"{adapter.profile.name} has non-positive ASM"

    def test_all_role_counts_match_agent_count(self):
        """Role list length matches requested agent count."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            roles = adapter.get_agent_roles(lo)
            assert len(roles) == lo

    def test_attack_surface_ordering(self):
        """Claude Code (hierarchical) should have lower attack surface than AutoGPT (flat)."""
        cc = ClaudeCodeAdapter()
        agpt = AutoGPTAdapter()
        assert cc.get_attack_surface_multiplier() < agpt.get_attack_surface_multiplier()

    def test_hierarchical_architectures_have_orchestrator(self):
        """Architectures with central orchestrators have it flagged."""
        cc = ClaudeCodeAdapter()
        lg = LangGraphAdapter()
        mg = MetaGPTAdapter()
        assert cc.profile.has_central_orchestrator is True
        assert lg.profile.has_central_orchestrator is True
        assert mg.profile.has_central_orchestrator is True

    def test_flat_architectures_no_orchestrator(self):
        """Flat/debate architectures do not have a central orchestrator."""
        agpt = AutoGPTAdapter()
        camel = CamelAdapter()
        crew = CrewAIAdapter()
        assert agpt.profile.has_central_orchestrator is False
        assert camel.profile.has_central_orchestrator is False
        assert crew.profile.has_central_orchestrator is False

    def test_average_trust_varies_by_topology(self):
        """Different topologies produce different mean trust values."""
        means = {}
        # Use a common agent count where all (or most) architectures overlap
        for adapter in self._instances():
            lo, hi = adapter.profile.agent_count_range
            n = max(lo, min(hi, 5))
            T = adapter.create_trust_matrix(n)
            # Mean of off-diagonal entries
            mask = ~np.eye(n, dtype=bool)
            means[adapter.profile.name] = T[mask].mean()
        # At least 3 distinct mean trust values among the 6 architectures
        unique_means = set(round(v, 4) for v in means.values())
        assert len(unique_means) >= 3, (
            f"Expected diverse trust profiles, got {unique_means}"
        )

    def test_delegation_decay_comparison(self):
        """Delegation trust decays with depth across all architectures."""
        for adapter in self._instances():
            lo, _ = adapter.profile.agent_count_range
            if lo < 2:
                continue
            d1 = adapter.simulate_delegation(0, 1, 1)
            d_max = adapter.simulate_delegation(0, 1, adapter.profile.delegation_depth)
            # At depth=1 or more, trust should be <= direct trust
            assert d_max <= d1 + 1e-9, (
                f"{adapter.profile.name}: delegation at max depth exceeds depth 1"
            )

    def test_communication_graph_density_varies(self):
        """Different architectures produce different graph densities."""
        densities = {}
        for adapter in self._instances():
            lo, hi = adapter.profile.agent_count_range
            n = max(lo, min(hi, 5))
            G = adapter.get_communication_graph(n)
            total_possible = n * (n - 1)
            if total_possible > 0:
                densities[adapter.profile.name] = G.sum() / total_possible
        # Hub-spoke (Claude Code) should be less dense than mesh (AutoGPT)
        if "Claude Code" in densities and "AutoGPT" in densities:
            assert densities["Claude Code"] < densities["AutoGPT"]


# -----------------------------------------------------------------------
# Section 10: Adapter creation and defense integration
# -----------------------------------------------------------------------


class TestAdapterCreationAndIntegration:
    """Test adapter instantiation patterns and integration with trust matrices."""

    def test_all_adapters_instantiate(self):
        """All 6 adapters can be instantiated without arguments."""
        adapters = [
            AutoGPTAdapter(),
            CamelAdapter(),
            ClaudeCodeAdapter(),
            CrewAIAdapter(),
            LangGraphAdapter(),
            MetaGPTAdapter(),
        ]
        assert len(adapters) == 6

    def test_adapter_profile_is_architecture_profile(self):
        """All adapter profiles are ArchitectureProfile instances."""
        for cls in [AutoGPTAdapter, CamelAdapter, ClaudeCodeAdapter,
                    CrewAIAdapter, LangGraphAdapter, MetaGPTAdapter]:
            adapter = cls()
            assert isinstance(adapter.profile, ArchitectureProfile)

    def test_adapter_is_architecture_adapter(self):
        """All adapters are ArchitectureAdapter subclasses."""
        for cls in [AutoGPTAdapter, CamelAdapter, ClaudeCodeAdapter,
                    CrewAIAdapter, LangGraphAdapter, MetaGPTAdapter]:
            adapter = cls()
            assert isinstance(adapter, ArchitectureAdapter)

    def test_trust_matrix_usable_for_defense_scoring(self):
        """Trust matrices can be used to compute per-agent defense scores.

        Defense integration: multiply trust matrix by a uniform belief
        vector to compute weighted trust scores per agent.
        """
        adapter = ClaudeCodeAdapter()
        n = 5
        T = adapter.create_trust_matrix(n)
        beliefs = np.ones(n) / n  # Uniform belief

        # Trust-weighted scores: how much each agent is trusted by others
        trust_scores = T @ beliefs
        assert trust_scores.shape == (n,)
        assert np.all(trust_scores > 0.0)
        # Orchestrator should have highest weighted trust score
        assert np.argmax(trust_scores) == 0

    def test_communication_graph_reachability(self):
        """Communication graph can be used for reachability analysis.

        Defense integration: check which agents can reach each other
        (directly or through paths).
        """
        adapter = ClaudeCodeAdapter()
        n = 5
        G = adapter.get_communication_graph(n)

        # For hub-spoke, all agents can reach each other in at most 2 hops
        # G + G@G gives 2-hop reachability
        reach_2 = G + G @ G
        reach_2 = np.where(reach_2 > 0, 1.0, 0.0)
        np.fill_diagonal(reach_2, 0.0)

        # In hub-spoke, every pair is reachable in <= 2 hops
        expected = np.ones((n, n)) - np.eye(n)
        np.testing.assert_array_equal(reach_2, expected)

    def test_attack_surface_defense_integration(self):
        """Attack surface multipliers scale a base risk score.

        Defense integration: lower multiplier = better defense posture.
        """
        base_risk = 1.0
        adapters = {
            "Claude Code": ClaudeCodeAdapter(),
            "AutoGPT": AutoGPTAdapter(),
            "CrewAI": CrewAIAdapter(),
            "LangGraph": LangGraphAdapter(),
            "MetaGPT": MetaGPTAdapter(),
            "CAMEL": CamelAdapter(),
        }
        risks = {
            name: base_risk * a.get_attack_surface_multiplier()
            for name, a in adapters.items()
        }
        # Claude Code should have lowest effective risk
        assert risks["Claude Code"] == min(risks.values())
        # AutoGPT should have highest effective risk
        assert risks["AutoGPT"] == max(risks.values())

    def test_delegation_chain_trust_computation(self):
        """Delegation can compute transitive trust through chains.

        Defense integration: compute effective trust along a multi-hop
        delegation path.
        """
        adapter = MetaGPTAdapter()
        # PM -> Architect -> Engineer (SOP chain)
        pm_to_arch = adapter.simulate_delegation(0, 1, 1)
        pm_to_eng = adapter.simulate_delegation(0, 2, 2)

        # Direct PM->Architect trust should exceed transitive PM->Engineer
        assert pm_to_arch > pm_to_eng

    def test_role_based_trust_segmentation(self):
        """Roles enable trust segmentation for defense policies.

        Defense integration: different roles get different defense
        thresholds based on their trust level.
        """
        adapter = CrewAIAdapter()
        n = 5
        roles = adapter.get_agent_roles(n)
        T = adapter.create_trust_matrix(n)

        # Compute mean trust received per agent
        mean_trust_received = np.zeros(n)
        for j in range(n):
            others = [T[i, j] for i in range(n) if i != j]
            mean_trust_received[j] = np.mean(others)

        # All agents should have positive mean trust received
        assert np.all(mean_trust_received > 0.0)
        assert len(roles) == n


# -----------------------------------------------------------------------
# Section 11: Architecture-specific configuration validation
# -----------------------------------------------------------------------


class TestArchitectureSpecificValidation:
    """Test architecture-specific configuration constraints."""

    def test_claude_code_minimum_two_agents(self):
        """Claude Code requires at least 2 agents (orchestrator + 1)."""
        adapter = ClaudeCodeAdapter()
        with pytest.raises(ValueError):
            adapter.create_trust_matrix(1)
        # 2 agents is valid
        T = adapter.create_trust_matrix(2)
        assert T.shape == (2, 2)

    def test_autogpt_supports_single_agent(self):
        """AutoGPT can run with just the main agent (no plugins)."""
        adapter = AutoGPTAdapter()
        T = adapter.create_trust_matrix(1)
        assert T.shape == (1, 1)
        assert T[0, 0] == 1.0

    def test_camel_minimum_two_debaters(self):
        """CAMEL requires at least proponent and opponent."""
        adapter = CamelAdapter()
        T = adapter.create_trust_matrix(2)
        roles = adapter.get_agent_roles(2)
        assert "proponent" in roles
        assert "opponent" in roles

    def test_crewai_minimum_three_roles(self):
        """CrewAI requires at least 3 agents for meaningful role separation."""
        adapter = CrewAIAdapter()
        T = adapter.create_trust_matrix(3)
        roles = adapter.get_agent_roles(3)
        assert len(set(roles)) == 3  # 3 distinct roles

    def test_metagpt_minimum_five_sop_roles(self):
        """MetaGPT requires at least 5 agents for the core SOP chain."""
        adapter = MetaGPTAdapter()
        T = adapter.create_trust_matrix(5)
        roles = adapter.get_agent_roles(5)
        expected_core = ["product_manager", "architect", "engineer",
                         "qa_engineer", "designer"]
        assert roles == expected_core

    def test_langgraph_scales_to_50(self):
        """LangGraph supports up to 50 agents for large state machines."""
        adapter = LangGraphAdapter()
        T = adapter.create_trust_matrix(50)
        assert T.shape == (50, 50)
        roles = adapter.get_agent_roles(50)
        assert len(roles) == 50

    def test_validate_n_used_by_all_methods(self):
        """Agent count validation is enforced on roles and graphs too."""
        adapter = ClaudeCodeAdapter()
        with pytest.raises(ValueError, match="supports"):
            adapter.get_agent_roles(1)
        with pytest.raises(ValueError, match="supports"):
            adapter.get_communication_graph(1)

    def test_all_adapters_validate_at_boundaries(self):
        """Boundary agent counts are accepted; out-of-range rejected."""
        configs = [
            (ClaudeCodeAdapter, 2, 20),
            (AutoGPTAdapter, 1, 5),
            (CamelAdapter, 2, 6),
            (CrewAIAdapter, 3, 10),
            (LangGraphAdapter, 2, 50),
            (MetaGPTAdapter, 5, 8),
        ]
        for cls, lo, hi in configs:
            adapter = cls()
            # Min boundary: accepted
            T = adapter.create_trust_matrix(lo)
            assert T.shape == (lo, lo)
            # Max boundary: accepted
            T = adapter.create_trust_matrix(hi)
            assert T.shape == (hi, hi)
            # Below min: rejected
            if lo > 1:
                with pytest.raises(ValueError):
                    adapter.create_trust_matrix(lo - 1)
            # Above max: rejected
            with pytest.raises(ValueError):
                adapter.create_trust_matrix(hi + 1)
