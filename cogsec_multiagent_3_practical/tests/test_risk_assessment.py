"""Tests for the risk assessment framework (Section 06).

Tests cover:
- All enums: EntryPointType, InfluencePath, ImpactLevel, LikelihoodLevel, MitigationPriority
- RiskScore auto-computation and priority determination across all matrix quadrants
- Dataclass creation with defaults: EntryPoint, InfluenceAnalysis, SystemDescription, DetectionPoint
- ThreatScenario creation and risk computation
- AttackSurfaceMapper: full 5-step workflow, prioritization, evaluation
- ThreatModelWorksheet: entry management, scenario analysis, summary statistics
- CommonAttackScenarios: all 4 pre-built scenarios and e-commerce worked example
- Edge cases and boundary conditions
"""

import pytest

from src import AssessmentResult, RiskLevel
from src.risk_assessment import (
    AttackSurfaceMapper,
    CommonAttackScenarios,
    DetectionPoint,
    EntryPoint,
    EntryPointType,
    ImpactLevel,
    InfluenceAnalysis,
    InfluencePath,
    LikelihoodLevel,
    MitigationPriority,
    RiskScore,
    SystemDescription,
    ThreatModelWorksheet,
    ThreatScenario,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestEntryPointType:
    """Tests for EntryPointType enum."""

    def test_all_values_exist(self):
        """All five entry point types are defined."""
        assert EntryPointType.USER_INPUT.value == "user_input"
        assert EntryPointType.TOOL_OUTPUT.value == "tool_output"
        assert EntryPointType.AGENT_COMMUNICATION.value == "agent_communication"
        assert EntryPointType.PERSISTENT_MEMORY.value == "persistent_memory"
        assert EntryPointType.EXTERNAL_TRIGGER.value == "external_trigger"

    def test_member_count(self):
        """Exactly five entry point types exist."""
        assert len(EntryPointType) == 5

    def test_string_valued(self):
        """Enum values are strings."""
        for member in EntryPointType:
            assert isinstance(member.value, str)


class TestInfluencePath:
    """Tests for InfluencePath enum."""

    def test_all_values_exist(self):
        """All four influence paths are defined."""
        assert InfluencePath.DIRECT.value == "direct"
        assert InfluencePath.DELEGATED.value == "delegated"
        assert InfluencePath.STORED.value == "stored"
        assert InfluencePath.EMERGENT.value == "emergent"

    def test_member_count(self):
        """Exactly four influence path types exist."""
        assert len(InfluencePath) == 4


class TestImpactLevel:
    """Tests for ImpactLevel enum with numeric property."""

    def test_all_values_exist(self):
        """All four impact levels are defined."""
        assert ImpactLevel.LOW.value == "low"
        assert ImpactLevel.MEDIUM.value == "medium"
        assert ImpactLevel.HIGH.value == "high"
        assert ImpactLevel.CRITICAL.value == "critical"

    def test_numeric_property(self):
        """Numeric scores map correctly: low=1, medium=2, high=3, critical=4."""
        assert ImpactLevel.LOW.numeric == 1
        assert ImpactLevel.MEDIUM.numeric == 2
        assert ImpactLevel.HIGH.numeric == 3
        assert ImpactLevel.CRITICAL.numeric == 4

    def test_numeric_ordering(self):
        """Numeric values increase monotonically."""
        levels = [ImpactLevel.LOW, ImpactLevel.MEDIUM, ImpactLevel.HIGH, ImpactLevel.CRITICAL]
        for i in range(len(levels) - 1):
            assert levels[i].numeric < levels[i + 1].numeric


class TestLikelihoodLevel:
    """Tests for LikelihoodLevel enum with numeric property."""

    def test_all_values_exist(self):
        """All four likelihood levels are defined."""
        assert LikelihoodLevel.LOW.value == "low"
        assert LikelihoodLevel.MEDIUM.value == "medium"
        assert LikelihoodLevel.HIGH.value == "high"
        assert LikelihoodLevel.VERY_HIGH.value == "very_high"

    def test_numeric_property(self):
        """Numeric scores map correctly: low=1, medium=2, high=3, very_high=4."""
        assert LikelihoodLevel.LOW.numeric == 1
        assert LikelihoodLevel.MEDIUM.numeric == 2
        assert LikelihoodLevel.HIGH.numeric == 3
        assert LikelihoodLevel.VERY_HIGH.numeric == 4

    def test_numeric_ordering(self):
        """Numeric values increase monotonically."""
        levels = [
            LikelihoodLevel.LOW,
            LikelihoodLevel.MEDIUM,
            LikelihoodLevel.HIGH,
            LikelihoodLevel.VERY_HIGH,
        ]
        for i in range(len(levels) - 1):
            assert levels[i].numeric < levels[i + 1].numeric


class TestMitigationPriority:
    """Tests for MitigationPriority enum."""

    def test_all_values_exist(self):
        """All four mitigation priority levels are defined."""
        assert MitigationPriority.IMMEDIATE.value == "immediate"
        assert MitigationPriority.NEAR_TERM.value == "near_term"
        assert MitigationPriority.MONITORING.value == "monitoring"
        assert MitigationPriority.NORMAL_CYCLE.value == "normal_cycle"

    def test_member_count(self):
        """Exactly four priority levels exist."""
        assert len(MitigationPriority) == 4


# =============================================================================
# Dataclass Tests
# =============================================================================


class TestEntryPoint:
    """Tests for EntryPoint dataclass."""

    def test_creation_with_defaults(self):
        """EntryPoint initializes with correct defaults."""
        ep = EntryPoint(
            type=EntryPointType.USER_INPUT,
            name="Chat input",
        )
        assert ep.type == EntryPointType.USER_INPUT
        assert ep.name == "Chat input"
        assert ep.example == ""
        assert ep.attack_vector == ""
        assert ep.trust_level == 0.5
        assert ep.cif_defense == ""
        assert ep.residual_risk == RiskLevel.MEDIUM

    def test_creation_with_all_fields(self):
        """EntryPoint initializes with all fields specified."""
        ep = EntryPoint(
            type=EntryPointType.EXTERNAL_TRIGGER,
            name="Webhook",
            example="POST /webhook/payment",
            attack_vector="Payload injection",
            trust_level=0.7,
            cif_defense="Schema validation",
            residual_risk=RiskLevel.LOW,
        )
        assert ep.type == EntryPointType.EXTERNAL_TRIGGER
        assert ep.name == "Webhook"
        assert ep.example == "POST /webhook/payment"
        assert ep.attack_vector == "Payload injection"
        assert ep.trust_level == 0.7
        assert ep.cif_defense == "Schema validation"
        assert ep.residual_risk == RiskLevel.LOW

    def test_trust_level_boundary_values(self):
        """EntryPoint accepts trust levels at boundaries."""
        ep_zero = EntryPoint(type=EntryPointType.USER_INPUT, name="Untrusted", trust_level=0.0)
        ep_one = EntryPoint(type=EntryPointType.TOOL_OUTPUT, name="Fully trusted", trust_level=1.0)
        assert ep_zero.trust_level == 0.0
        assert ep_one.trust_level == 1.0


class TestInfluenceAnalysis:
    """Tests for InfluenceAnalysis dataclass."""

    def test_creation_with_defaults(self):
        """InfluenceAnalysis initializes with correct defaults."""
        ep = EntryPoint(type=EntryPointType.USER_INPUT, name="Test")
        ia = InfluenceAnalysis(
            entry_point=ep,
            path_type=InfluencePath.DIRECT,
            description="Direct user influence",
        )
        assert ia.entry_point is ep
        assert ia.path_type == InfluencePath.DIRECT
        assert ia.description == "Direct user influence"
        assert ia.affected_agents == []
        assert ia.detection_mechanism == ""

    def test_creation_with_agents(self):
        """InfluenceAnalysis tracks affected agents."""
        ep = EntryPoint(type=EntryPointType.AGENT_COMMUNICATION, name="Inter-agent")
        ia = InfluenceAnalysis(
            entry_point=ep,
            path_type=InfluencePath.DELEGATED,
            description="Delegated influence through chain",
            affected_agents=["AgentA", "AgentB", "AgentC"],
            detection_mechanism="Trust calculus monitoring",
        )
        assert len(ia.affected_agents) == 3
        assert "AgentB" in ia.affected_agents
        assert ia.detection_mechanism == "Trust calculus monitoring"


class TestSystemDescription:
    """Tests for SystemDescription dataclass."""

    def test_creation_with_defaults(self):
        """SystemDescription initializes with correct defaults."""
        sd = SystemDescription(
            name="TestSystem",
            architecture_type="hierarchical",
            agent_count=3,
            risk_profile="medium",
        )
        assert sd.name == "TestSystem"
        assert sd.architecture_type == "hierarchical"
        assert sd.agent_count == 3
        assert sd.risk_profile == "medium"
        assert sd.agents == []

    def test_creation_with_agents(self):
        """SystemDescription stores agent list."""
        sd = SystemDescription(
            name="MultiBot",
            architecture_type="mesh",
            agent_count=2,
            risk_profile="high",
            agents=["Coordinator", "Worker"],
        )
        assert len(sd.agents) == 2
        assert "Coordinator" in sd.agents


class TestDetectionPoint:
    """Tests for DetectionPoint dataclass."""

    def test_creation_with_defaults(self):
        """DetectionPoint initializes with effective=True by default."""
        dp = DetectionPoint(
            mechanism="Firewall",
            step_number=1,
            description="Blocks instruction-like content",
        )
        assert dp.mechanism == "Firewall"
        assert dp.step_number == 1
        assert dp.description == "Blocks instruction-like content"
        assert dp.effective is True

    def test_creation_ineffective(self):
        """DetectionPoint can be marked as ineffective."""
        dp = DetectionPoint(
            mechanism="Weak heuristic",
            step_number=3,
            description="Rarely triggers",
            effective=False,
        )
        assert dp.effective is False


# =============================================================================
# RiskScore Tests
# =============================================================================


class TestRiskScore:
    """Tests for RiskScore auto-computation and priority matrix."""

    def test_auto_computation(self):
        """Score is computed as impact.numeric * likelihood.numeric."""
        rs = RiskScore(impact=ImpactLevel.HIGH, likelihood=LikelihoodLevel.MEDIUM)
        assert rs.score == 3 * 2  # HIGH(3) * MEDIUM(2) = 6

    def test_max_score(self):
        """Maximum possible score is 16 (CRITICAL * VERY_HIGH)."""
        rs = RiskScore(impact=ImpactLevel.CRITICAL, likelihood=LikelihoodLevel.VERY_HIGH)
        assert rs.score == 16

    def test_min_score(self):
        """Minimum possible score is 1 (LOW * LOW)."""
        rs = RiskScore(impact=ImpactLevel.LOW, likelihood=LikelihoodLevel.LOW)
        assert rs.score == 1

    def test_priority_immediate_critical_high(self):
        """CRITICAL impact + HIGH likelihood yields IMMEDIATE priority."""
        rs = RiskScore(impact=ImpactLevel.CRITICAL, likelihood=LikelihoodLevel.HIGH)
        assert rs.priority == MitigationPriority.IMMEDIATE

    def test_priority_immediate_critical_very_high(self):
        """CRITICAL impact + VERY_HIGH likelihood yields IMMEDIATE priority."""
        rs = RiskScore(impact=ImpactLevel.CRITICAL, likelihood=LikelihoodLevel.VERY_HIGH)
        assert rs.priority == MitigationPriority.IMMEDIATE

    def test_priority_near_term_high_high(self):
        """HIGH impact + HIGH likelihood yields NEAR_TERM priority."""
        rs = RiskScore(impact=ImpactLevel.HIGH, likelihood=LikelihoodLevel.HIGH)
        assert rs.priority == MitigationPriority.NEAR_TERM

    def test_priority_near_term_high_very_high(self):
        """HIGH impact + VERY_HIGH likelihood yields NEAR_TERM priority."""
        rs = RiskScore(impact=ImpactLevel.HIGH, likelihood=LikelihoodLevel.VERY_HIGH)
        assert rs.priority == MitigationPriority.NEAR_TERM

    def test_priority_monitoring_critical_low(self):
        """CRITICAL impact + LOW likelihood yields MONITORING priority."""
        rs = RiskScore(impact=ImpactLevel.CRITICAL, likelihood=LikelihoodLevel.LOW)
        assert rs.priority == MitigationPriority.MONITORING

    def test_priority_monitoring_critical_medium(self):
        """CRITICAL impact + MEDIUM likelihood yields MONITORING priority."""
        rs = RiskScore(impact=ImpactLevel.CRITICAL, likelihood=LikelihoodLevel.MEDIUM)
        assert rs.priority == MitigationPriority.MONITORING

    def test_priority_normal_cycle_medium_medium(self):
        """MEDIUM impact + MEDIUM likelihood yields NORMAL_CYCLE priority."""
        rs = RiskScore(impact=ImpactLevel.MEDIUM, likelihood=LikelihoodLevel.MEDIUM)
        assert rs.priority == MitigationPriority.NORMAL_CYCLE

    def test_priority_normal_cycle_low_low(self):
        """LOW impact + LOW likelihood yields NORMAL_CYCLE priority."""
        rs = RiskScore(impact=ImpactLevel.LOW, likelihood=LikelihoodLevel.LOW)
        assert rs.priority == MitigationPriority.NORMAL_CYCLE

    def test_priority_normal_cycle_medium_high(self):
        """MEDIUM impact + HIGH likelihood yields NORMAL_CYCLE priority."""
        rs = RiskScore(impact=ImpactLevel.MEDIUM, likelihood=LikelihoodLevel.HIGH)
        assert rs.priority == MitigationPriority.NORMAL_CYCLE

    def test_priority_normal_cycle_low_very_high(self):
        """LOW impact + VERY_HIGH likelihood yields NORMAL_CYCLE priority."""
        rs = RiskScore(impact=ImpactLevel.LOW, likelihood=LikelihoodLevel.VERY_HIGH)
        assert rs.priority == MitigationPriority.NORMAL_CYCLE

    def test_priority_normal_cycle_high_low(self):
        """HIGH impact + LOW likelihood yields NORMAL_CYCLE priority."""
        rs = RiskScore(impact=ImpactLevel.HIGH, likelihood=LikelihoodLevel.LOW)
        assert rs.priority == MitigationPriority.NORMAL_CYCLE


# =============================================================================
# ThreatScenario Tests
# =============================================================================


class TestThreatScenario:
    """Tests for ThreatScenario dataclass and risk computation."""

    def test_creation_with_defaults(self):
        """ThreatScenario initializes with correct defaults."""
        ts = ThreatScenario(name="Test Threat", description="A test threat")
        assert ts.name == "Test Threat"
        assert ts.description == "A test threat"
        assert ts.attack_steps == []
        assert ts.detection_points == []
        assert ts.impact_description == ""
        assert ts.impact_level == ImpactLevel.MEDIUM
        assert ts.likelihood_level == LikelihoodLevel.MEDIUM
        assert ts.mitigation_gaps == []
        assert ts.risk_score is None

    def test_compute_risk(self):
        """compute_risk calculates and stores risk score."""
        ts = ThreatScenario(
            name="High Risk Threat",
            description="Should compute correctly",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        result = ts.compute_risk()
        assert isinstance(result, RiskScore)
        assert result.score == 4 * 3  # CRITICAL(4) * HIGH(3) = 12
        assert result.priority == MitigationPriority.IMMEDIATE
        assert ts.risk_score is result

    def test_compute_risk_updates_stored_score(self):
        """Calling compute_risk replaces any previous score."""
        ts = ThreatScenario(
            name="Changing Threat",
            description="Risk changes",
            impact_level=ImpactLevel.LOW,
            likelihood_level=LikelihoodLevel.LOW,
        )
        first = ts.compute_risk()
        assert first.score == 1

        ts.impact_level = ImpactLevel.HIGH
        ts.likelihood_level = LikelihoodLevel.HIGH
        second = ts.compute_risk()
        assert second.score == 9
        assert ts.risk_score is second

    def test_attack_steps_and_detection(self):
        """ThreatScenario stores attack steps and detection points."""
        ts = ThreatScenario(
            name="Multi-step Attack",
            description="Has steps and detection",
            attack_steps=["Step 1", "Step 2", "Step 3"],
            detection_points=[
                DetectionPoint("Firewall", 1, "Blocks at entry"),
                DetectionPoint("Tripwire", 2, "Canary detection"),
            ],
            mitigation_gaps=["Gap A", "Gap B"],
        )
        assert len(ts.attack_steps) == 3
        assert len(ts.detection_points) == 2
        assert len(ts.mitigation_gaps) == 2


# =============================================================================
# AttackSurfaceMapper Tests
# =============================================================================


class TestAttackSurfaceMapper:
    """Tests for AttackSurfaceMapper 5-step workflow."""

    def test_initialization(self):
        """Mapper starts with empty collections."""
        mapper = AttackSurfaceMapper()
        assert mapper.entry_points == []
        assert mapper.influence_paths == []
        assert mapper.threat_scenarios == []

    def test_add_entry_point(self):
        """Step 1: Entry points are added correctly."""
        mapper = AttackSurfaceMapper()
        ep = EntryPoint(type=EntryPointType.USER_INPUT, name="Chat")
        mapper.add_entry_point(ep)
        assert len(mapper.entry_points) == 1
        assert mapper.entry_points[0] is ep

    def test_add_multiple_entry_points(self):
        """Step 1: Multiple entry points accumulate."""
        mapper = AttackSurfaceMapper()
        for ept in EntryPointType:
            mapper.add_entry_point(EntryPoint(type=ept, name=ept.value))
        assert len(mapper.entry_points) == 5

    def test_add_influence_path(self):
        """Step 2: Influence paths are added correctly."""
        mapper = AttackSurfaceMapper()
        ep = EntryPoint(type=EntryPointType.USER_INPUT, name="Chat")
        ia = InfluenceAnalysis(
            entry_point=ep,
            path_type=InfluencePath.DIRECT,
            description="Direct user path",
        )
        mapper.add_influence_path(ia)
        assert len(mapper.influence_paths) == 1

    def test_add_threat_scenario_auto_computes_risk(self):
        """Steps 3-4: Adding a scenario auto-computes its risk score."""
        mapper = AttackSurfaceMapper()
        ts = ThreatScenario(
            name="Test",
            description="Test scenario",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        assert ts.risk_score is None
        mapper.add_threat_scenario(ts)
        assert ts.risk_score is not None
        assert ts.risk_score.score == 9

    def test_prioritize_sorts_by_descending_score(self):
        """Step 5: Prioritize returns scenarios in descending risk order."""
        mapper = AttackSurfaceMapper()
        low = ThreatScenario(
            name="Low",
            description="Low risk",
            impact_level=ImpactLevel.LOW,
            likelihood_level=LikelihoodLevel.LOW,
        )
        high = ThreatScenario(
            name="High",
            description="High risk",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        medium = ThreatScenario(
            name="Medium",
            description="Medium risk",
            impact_level=ImpactLevel.MEDIUM,
            likelihood_level=LikelihoodLevel.MEDIUM,
        )
        mapper.add_threat_scenario(low)
        mapper.add_threat_scenario(high)
        mapper.add_threat_scenario(medium)

        prioritized = mapper.prioritize()
        scores = [s.risk_score.score for s in prioritized]
        assert scores == [9, 4, 1]
        assert prioritized[0].name == "High"
        assert prioritized[1].name == "Medium"
        assert prioritized[2].name == "Low"

    def test_get_immediate_priorities(self):
        """get_immediate_priorities returns only IMMEDIATE-priority scenarios."""
        mapper = AttackSurfaceMapper()
        immediate = ThreatScenario(
            name="Urgent",
            description="Needs immediate action",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        normal = ThreatScenario(
            name="Routine",
            description="Normal cycle",
            impact_level=ImpactLevel.LOW,
            likelihood_level=LikelihoodLevel.LOW,
        )
        mapper.add_threat_scenario(immediate)
        mapper.add_threat_scenario(normal)

        immediates = mapper.get_immediate_priorities()
        assert len(immediates) == 1
        assert immediates[0].name == "Urgent"

    def test_get_immediate_priorities_empty(self):
        """get_immediate_priorities returns empty list when no immediate threats."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Low",
                description="Not urgent",
                impact_level=ImpactLevel.LOW,
                likelihood_level=LikelihoodLevel.LOW,
            )
        )
        assert mapper.get_immediate_priorities() == []

    def test_evaluate_empty_mapper(self):
        """Evaluate with no scenarios returns passing result."""
        mapper = AttackSurfaceMapper()
        result = mapper.evaluate()
        assert isinstance(result, AssessmentResult)
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
        assert len(result.findings) == 1
        assert "No threat scenarios" in result.findings[0]

    def test_evaluate_low_risk(self):
        """Evaluate with only low-risk scenarios passes."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Minor Issue",
                description="Negligible risk",
                impact_level=ImpactLevel.LOW,
                likelihood_level=LikelihoodLevel.LOW,
            )
        )
        result = mapper.evaluate()
        assert result.passed is True
        assert result.risk_level == RiskLevel.LOW
        assert result.score > 0.9

    def test_evaluate_high_risk_with_immediate(self):
        """Evaluate with immediate-priority scenarios fails."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Critical Threat",
                description="Must fix now",
                impact_level=ImpactLevel.CRITICAL,
                likelihood_level=LikelihoodLevel.VERY_HIGH,
                mitigation_gaps=["No defenses deployed"],
            )
        )
        result = mapper.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.score == 0.0  # 1.0 - 16/16 = 0.0
        assert any("IMMEDIATE" in r for r in result.recommendations)

    def test_evaluate_medium_risk(self):
        """Evaluate assigns MEDIUM risk for moderate scores."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Moderate Threat",
                description="Manageable",
                impact_level=ImpactLevel.MEDIUM,
                likelihood_level=LikelihoodLevel.MEDIUM,
            )
        )
        result = mapper.evaluate()
        assert result.risk_level == RiskLevel.MEDIUM
        assert result.passed is True  # No immediate priorities

    def test_evaluate_high_risk_level(self):
        """Evaluate assigns HIGH risk for scores in 8-11 range."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Serious Threat",
                description="High risk but not immediate",
                impact_level=ImpactLevel.CRITICAL,
                likelihood_level=LikelihoodLevel.MEDIUM,
            )
        )
        result = mapper.evaluate()
        # CRITICAL(4) * MEDIUM(2) = 8 -> HIGH risk level
        assert result.risk_level == RiskLevel.HIGH

    def test_evaluate_findings_limited_to_five(self):
        """Evaluate caps findings at top 5 scenarios."""
        mapper = AttackSurfaceMapper()
        for i in range(8):
            mapper.add_threat_scenario(
                ThreatScenario(
                    name=f"Threat {i}",
                    description=f"Scenario {i}",
                    impact_level=ImpactLevel.MEDIUM,
                    likelihood_level=LikelihoodLevel.MEDIUM,
                )
            )
        result = mapper.evaluate()
        assert len(result.findings) <= 5

    def test_evaluate_recommendations_limited_to_ten(self):
        """Evaluate caps recommendations at 10."""
        mapper = AttackSurfaceMapper()
        for i in range(6):
            mapper.add_threat_scenario(
                ThreatScenario(
                    name=f"Threat {i}",
                    description=f"Scenario {i}",
                    impact_level=ImpactLevel.MEDIUM,
                    likelihood_level=LikelihoodLevel.MEDIUM,
                    mitigation_gaps=[f"Gap A-{i}", f"Gap B-{i}", f"Gap C-{i}"],
                )
            )
        result = mapper.evaluate()
        assert len(result.recommendations) <= 10

    def test_evaluate_normalized_score_calculation(self):
        """Evaluate correctly normalizes score from 0-16 range to 0-1."""
        mapper = AttackSurfaceMapper()
        # Score 8: normalized = 1.0 - 8/16 = 0.5
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Half Risk",
                description="Middle score",
                impact_level=ImpactLevel.CRITICAL,
                likelihood_level=LikelihoodLevel.MEDIUM,
            )
        )
        result = mapper.evaluate()
        assert result.score == pytest.approx(0.5)

    def test_evaluate_mitigation_gaps_in_recommendations(self):
        """Evaluate includes mitigation gaps in recommendations."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Gappy Threat",
                description="Has gaps",
                impact_level=ImpactLevel.MEDIUM,
                likelihood_level=LikelihoodLevel.LOW,
                mitigation_gaps=["Fix the firewall", "Add monitoring"],
            )
        )
        result = mapper.evaluate()
        gap_recs = [
            r for r in result.recommendations if "Fix the firewall" in r or "Add monitoring" in r
        ]
        assert len(gap_recs) == 2


# =============================================================================
# ThreatModelWorksheet Tests
# =============================================================================


class TestThreatModelWorksheet:
    """Tests for ThreatModelWorksheet structured modeling."""

    @pytest.fixture
    def sample_system(self) -> SystemDescription:
        """Provide a sample system description."""
        return SystemDescription(
            name="TestBot",
            architecture_type="hierarchical",
            agent_count=3,
            risk_profile="medium",
            agents=["Orchestrator", "Worker", "Reporter"],
        )

    def test_creation(self, sample_system):
        """Worksheet initializes with system and empty collections."""
        ws = ThreatModelWorksheet(system=sample_system)
        assert ws.system.name == "TestBot"
        assert ws.entry_points == []
        assert ws.scenarios == []
        assert ws.post_actions == []

    def test_add_entry_point(self, sample_system):
        """add_entry_point appends to entry_points list."""
        ws = ThreatModelWorksheet(system=sample_system)
        ep = EntryPoint(type=EntryPointType.USER_INPUT, name="Chat")
        ws.add_entry_point(ep)
        assert len(ws.entry_points) == 1
        assert ws.entry_points[0] is ep

    def test_add_scenario_computes_risk(self, sample_system):
        """add_scenario auto-computes risk score."""
        ws = ThreatModelWorksheet(system=sample_system)
        ts = ThreatScenario(
            name="Test Attack",
            description="Should auto-score",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.MEDIUM,
        )
        ws.add_scenario(ts)
        assert ts.risk_score is not None
        assert ts.risk_score.score == 6

    def test_highest_risk_scenario(self, sample_system):
        """highest_risk_scenario returns the most dangerous scenario."""
        ws = ThreatModelWorksheet(system=sample_system)
        low = ThreatScenario(
            name="Low",
            description="Low",
            impact_level=ImpactLevel.LOW,
            likelihood_level=LikelihoodLevel.LOW,
        )
        high = ThreatScenario(
            name="High",
            description="High",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        ws.add_scenario(low)
        ws.add_scenario(high)
        highest = ws.highest_risk_scenario()
        assert highest is not None
        assert highest.name == "High"
        assert highest.risk_score.score == 12

    def test_highest_risk_scenario_empty(self, sample_system):
        """highest_risk_scenario returns None when no scenarios exist."""
        ws = ThreatModelWorksheet(system=sample_system)
        assert ws.highest_risk_scenario() is None

    def test_summary_statistics(self, sample_system):
        """summary returns correct statistics dictionary."""
        ws = ThreatModelWorksheet(system=sample_system)
        ep1 = EntryPoint(type=EntryPointType.USER_INPUT, name="Chat")
        ep2 = EntryPoint(type=EntryPointType.TOOL_OUTPUT, name="DB Query")
        ws.add_entry_point(ep1)
        ws.add_entry_point(ep2)

        ws.add_scenario(
            ThreatScenario(
                name="Immediate Threat",
                description="Urgent",
                impact_level=ImpactLevel.CRITICAL,
                likelihood_level=LikelihoodLevel.HIGH,
                mitigation_gaps=["Gap 1", "Gap 2"],
            )
        )
        ws.add_scenario(
            ThreatScenario(
                name="Normal Threat",
                description="Routine",
                impact_level=ImpactLevel.LOW,
                likelihood_level=LikelihoodLevel.LOW,
                mitigation_gaps=["Gap 3"],
            )
        )

        summary = ws.summary()
        assert summary["system_name"] == "TestBot"
        assert summary["agent_count"] == 3
        assert summary["entry_point_count"] == 2
        assert summary["scenario_count"] == 2
        assert summary["immediate_count"] == 1
        assert summary["total_gaps"] == 3

    def test_summary_empty_worksheet(self, sample_system):
        """summary handles empty worksheet correctly."""
        ws = ThreatModelWorksheet(system=sample_system)
        summary = ws.summary()
        assert summary["entry_point_count"] == 0
        assert summary["scenario_count"] == 0
        assert summary["immediate_count"] == 0
        assert summary["total_gaps"] == 0

    def test_post_actions(self, sample_system):
        """post_actions stores action items."""
        ws = ThreatModelWorksheet(
            system=sample_system,
            post_actions=["Action 1", "Action 2"],
        )
        assert len(ws.post_actions) == 2
        assert "Action 1" in ws.post_actions


# =============================================================================
# CommonAttackScenarios Tests
# =============================================================================


class TestCommonAttackScenarios:
    """Tests for pre-built common attack scenarios."""

    def test_trust_laundering_scenario(self):
        """Trust laundering scenario is correctly configured."""
        scenario = CommonAttackScenarios.trust_laundering()
        assert scenario.name == "Trust Laundering"
        assert "delegation" in scenario.description.lower()
        assert len(scenario.attack_steps) == 4
        assert len(scenario.detection_points) == 3
        assert scenario.impact_level == ImpactLevel.HIGH
        assert scenario.likelihood_level == LikelihoodLevel.MEDIUM
        assert scenario.risk_score is not None
        assert scenario.risk_score.score == 6  # HIGH(3) * MEDIUM(2)
        assert len(scenario.mitigation_gaps) == 2

    def test_sybil_consensus_scenario(self):
        """Sybil consensus scenario is correctly configured."""
        scenario = CommonAttackScenarios.sybil_consensus()
        assert scenario.name == "Sybil Consensus Manipulation"
        assert "fake" in scenario.description.lower() or "sybil" in scenario.description.lower()
        assert len(scenario.attack_steps) == 4
        assert len(scenario.detection_points) == 3
        assert scenario.impact_level == ImpactLevel.HIGH
        assert scenario.likelihood_level == LikelihoodLevel.MEDIUM
        assert scenario.risk_score is not None
        assert scenario.risk_score.score == 6
        assert len(scenario.mitigation_gaps) == 2

    def test_progressive_belief_drift_scenario(self):
        """Progressive belief drift scenario is correctly configured."""
        scenario = CommonAttackScenarios.progressive_belief_drift()
        assert scenario.name == "Progressive Belief Drift"
        assert (
            "threshold" in scenario.description.lower() or "drift" in scenario.description.lower()
        )
        assert len(scenario.attack_steps) == 4
        assert len(scenario.detection_points) == 3
        assert scenario.impact_level == ImpactLevel.CRITICAL
        assert scenario.likelihood_level == LikelihoodLevel.LOW
        assert scenario.risk_score is not None
        assert scenario.risk_score.score == 4  # CRITICAL(4) * LOW(1)
        assert scenario.risk_score.priority == MitigationPriority.MONITORING
        assert len(scenario.mitigation_gaps) == 2

    def test_orchestrator_identity_theft_scenario(self):
        """Orchestrator identity theft scenario is correctly configured."""
        scenario = CommonAttackScenarios.orchestrator_identity_theft()
        assert scenario.name == "Orchestrator Identity Theft"
        assert "orchestrator" in scenario.description.lower()
        assert len(scenario.attack_steps) == 4
        assert len(scenario.detection_points) == 3
        assert scenario.impact_level == ImpactLevel.CRITICAL
        assert scenario.likelihood_level == LikelihoodLevel.LOW
        assert scenario.risk_score is not None
        assert scenario.risk_score.score == 4  # CRITICAL(4) * LOW(1)
        assert scenario.risk_score.priority == MitigationPriority.MONITORING
        assert len(scenario.mitigation_gaps) == 2

    def test_get_all_returns_four_scenarios(self):
        """get_all returns exactly 4 pre-built scenarios."""
        scenarios = CommonAttackScenarios.get_all()
        assert len(scenarios) == 4
        names = {s.name for s in scenarios}
        assert "Trust Laundering" in names
        assert "Sybil Consensus Manipulation" in names
        assert "Progressive Belief Drift" in names
        assert "Orchestrator Identity Theft" in names

    def test_get_all_scenarios_have_risk_scores(self):
        """All scenarios from get_all have computed risk scores."""
        for scenario in CommonAttackScenarios.get_all():
            assert scenario.risk_score is not None
            assert scenario.risk_score.score > 0

    def test_get_all_scenarios_have_detection_points(self):
        """All scenarios from get_all have at least one detection point."""
        for scenario in CommonAttackScenarios.get_all():
            assert len(scenario.detection_points) >= 1

    def test_get_all_scenarios_have_mitigation_gaps(self):
        """All scenarios from get_all have identified mitigation gaps."""
        for scenario in CommonAttackScenarios.get_all():
            assert len(scenario.mitigation_gaps) >= 1


# =============================================================================
# E-Commerce Worked Example Tests
# =============================================================================


class TestEcommerceWorkedExample:
    """Tests for the e-commerce CustomerBot worked example."""

    @pytest.fixture
    def worksheet(self) -> ThreatModelWorksheet:
        """Provide the e-commerce worked example worksheet."""
        return CommonAttackScenarios.ecommerce_worked_example()

    def test_system_description(self, worksheet):
        """System is configured as hierarchical 5-agent CustomerBot."""
        assert worksheet.system.name == "CustomerBot Multi-Agent System"
        assert worksheet.system.architecture_type == "hierarchical"
        assert worksheet.system.agent_count == 5
        assert len(worksheet.system.agents) == 5

    def test_five_agents(self, worksheet):
        """All five expected agents are present."""
        agents = worksheet.system.agents
        assert "Orchestrator" in agents
        assert "OrderAgent" in agents
        assert "ShippingAgent" in agents
        assert "RefundAgent" in agents
        assert "CustomerAgent" in agents

    def test_five_entry_points(self, worksheet):
        """Five entry points are defined."""
        assert len(worksheet.entry_points) == 5

    def test_entry_point_types(self, worksheet):
        """Entry points cover the expected types."""
        types = {ep.type for ep in worksheet.entry_points}
        assert EntryPointType.USER_INPUT in types
        assert EntryPointType.TOOL_OUTPUT in types
        assert EntryPointType.EXTERNAL_TRIGGER in types

    def test_entry_point_trust_levels(self, worksheet):
        """Entry points have varying trust levels."""
        trust_levels = [ep.trust_level for ep in worksheet.entry_points]
        assert min(trust_levels) < max(trust_levels)
        # Customer chat should be lowest trust
        chat_ep = next(ep for ep in worksheet.entry_points if "chat" in ep.name.lower())
        assert chat_ep.trust_level == 0.3

    def test_entry_points_have_cif_defenses(self, worksheet):
        """All entry points have CIF defenses specified."""
        for ep in worksheet.entry_points:
            assert ep.cif_defense != "", f"Entry point '{ep.name}' missing CIF defense"

    def test_shipping_api_scenario(self, worksheet):
        """Shipping API trust laundering scenario is present and scored."""
        assert len(worksheet.scenarios) == 1
        scenario = worksheet.scenarios[0]
        assert "Shipping" in scenario.name
        assert scenario.risk_score is not None
        assert scenario.impact_level == ImpactLevel.CRITICAL
        assert scenario.likelihood_level == LikelihoodLevel.MEDIUM
        assert scenario.risk_score.score == 8  # CRITICAL(4) * MEDIUM(2)

    def test_shipping_scenario_has_seven_steps(self, worksheet):
        """Shipping API scenario has the full 7-step attack chain."""
        scenario = worksheet.scenarios[0]
        assert len(scenario.attack_steps) == 7

    def test_shipping_scenario_has_four_detection_points(self, worksheet):
        """Shipping API scenario has 4 detection points."""
        scenario = worksheet.scenarios[0]
        assert len(scenario.detection_points) == 4
        mechanisms = [dp.mechanism for dp in scenario.detection_points]
        assert "Firewall" in mechanisms
        assert "Sandbox" in mechanisms
        assert "Tripwire" in mechanisms
        assert "Invariant" in mechanisms

    def test_shipping_scenario_has_mitigation_gaps(self, worksheet):
        """Shipping API scenario identifies 3 mitigation gaps."""
        scenario = worksheet.scenarios[0]
        assert len(scenario.mitigation_gaps) == 3

    def test_post_actions(self, worksheet):
        """Post-assessment actions are defined."""
        assert len(worksheet.post_actions) == 4
        assert any("schema validation" in action.lower() for action in worksheet.post_actions)

    def test_summary_stats(self, worksheet):
        """Summary statistics are accurate."""
        summary = worksheet.summary()
        assert summary["system_name"] == "CustomerBot Multi-Agent System"
        assert summary["agent_count"] == 5
        assert summary["entry_point_count"] == 5
        assert summary["scenario_count"] == 1
        assert summary["total_gaps"] == 3


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_risk_score_all_combinations_have_valid_priority(self):
        """Every impact/likelihood combination produces a valid MitigationPriority."""
        for impact in ImpactLevel:
            for likelihood in LikelihoodLevel:
                rs = RiskScore(impact=impact, likelihood=likelihood)
                assert isinstance(rs.priority, MitigationPriority)
                assert rs.score == impact.numeric * likelihood.numeric

    def test_risk_score_all_scores_in_valid_range(self):
        """All possible risk scores fall in range [1, 16]."""
        scores = set()
        for impact in ImpactLevel:
            for likelihood in LikelihoodLevel:
                rs = RiskScore(impact=impact, likelihood=likelihood)
                scores.add(rs.score)
                assert 1 <= rs.score <= 16
        # Verify we get reasonable coverage of the range
        assert min(scores) == 1
        assert max(scores) == 16

    def test_mapper_prioritize_empty(self):
        """Prioritizing empty mapper returns empty list."""
        mapper = AttackSurfaceMapper()
        assert mapper.prioritize() == []

    def test_mapper_prioritize_single_scenario(self):
        """Prioritizing with one scenario returns that scenario."""
        mapper = AttackSurfaceMapper()
        ts = ThreatScenario(name="Solo", description="Only one")
        mapper.add_threat_scenario(ts)
        result = mapper.prioritize()
        assert len(result) == 1
        assert result[0].name == "Solo"

    def test_mapper_prioritize_equal_scores(self):
        """Scenarios with equal scores are both returned."""
        mapper = AttackSurfaceMapper()
        ts1 = ThreatScenario(
            name="A",
            description="First",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.MEDIUM,
        )
        ts2 = ThreatScenario(
            name="B",
            description="Second",
            impact_level=ImpactLevel.MEDIUM,
            likelihood_level=LikelihoodLevel.HIGH,
        )
        mapper.add_threat_scenario(ts1)
        mapper.add_threat_scenario(ts2)
        result = mapper.prioritize()
        assert len(result) == 2
        # Both have score 6, so both should be present
        assert result[0].risk_score.score == result[1].risk_score.score == 6

    def test_influence_analysis_mutable_agents_list(self):
        """InfluenceAnalysis agents list is independently mutable."""
        ep = EntryPoint(type=EntryPointType.USER_INPUT, name="Test")
        ia1 = InfluenceAnalysis(entry_point=ep, path_type=InfluencePath.DIRECT, description="A")
        ia2 = InfluenceAnalysis(entry_point=ep, path_type=InfluencePath.STORED, description="B")
        ia1.affected_agents.append("Agent1")
        assert len(ia2.affected_agents) == 0  # No cross-contamination

    def test_threat_scenario_mutable_lists(self):
        """ThreatScenario lists are independently mutable."""
        ts1 = ThreatScenario(name="A", description="First")
        ts2 = ThreatScenario(name="B", description="Second")
        ts1.attack_steps.append("Step 1")
        ts1.mitigation_gaps.append("Gap 1")
        assert len(ts2.attack_steps) == 0
        assert len(ts2.mitigation_gaps) == 0

    def test_worksheet_mutable_lists(self):
        """ThreatModelWorksheet lists are independently mutable."""
        sd = SystemDescription(
            name="S", architecture_type="flat", agent_count=1, risk_profile="low"
        )
        ws1 = ThreatModelWorksheet(system=sd)
        ws2 = ThreatModelWorksheet(system=sd)
        ws1.add_entry_point(EntryPoint(type=EntryPointType.USER_INPUT, name="EP"))
        assert len(ws2.entry_points) == 0

    def test_common_scenarios_return_independent_instances(self):
        """Each call to a common scenario factory returns a fresh instance."""
        s1 = CommonAttackScenarios.trust_laundering()
        s2 = CommonAttackScenarios.trust_laundering()
        assert s1 is not s2
        s1.name = "Modified"
        assert s2.name == "Trust Laundering"

    def test_evaluate_score_floor_at_zero(self):
        """Evaluate score cannot go below 0.0."""
        mapper = AttackSurfaceMapper()
        mapper.add_threat_scenario(
            ThreatScenario(
                name="Maximum Risk",
                description="Worst case",
                impact_level=ImpactLevel.CRITICAL,
                likelihood_level=LikelihoodLevel.VERY_HIGH,
            )
        )
        result = mapper.evaluate()
        assert result.score >= 0.0
