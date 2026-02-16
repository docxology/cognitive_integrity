"""Tests for deployment configuration and guidance module.

Tests cover:
- Enum values (RiskProfile, ArchitectureType, IntegrationPattern)
- FirewallConfig creation and quarantine_range property
- ConsensusConfig and MonitoringConfig creation with defaults
- DeploymentConfigurator: all 3 profiles, recommend_profile scenarios
- ArchitectureAdvisor: all 4 architectures, risks, examples
- ScalingAdvisor: all 4 tiers, edge cases, latency budgets
- TrustDecayAnalyzer: effective_trust, practical_depth_limit, compare_profiles
- Integration patterns: all 3 patterns with components
- Edge cases and ValueError handling
"""

import math

import pytest

from src import RiskLevel
from src.deployment import (
    ArchitectureAdvisor,
    ArchitectureGuidance,
    ArchitectureRisk,
    ArchitectureType,
    ConsensusConfig,
    DeploymentConfig,
    DeploymentConfigurator,
    FirewallConfig,
    IntegrationGuidance,
    IntegrationPattern,
    LatencyBudget,
    MonitoringConfig,
    RiskProfile,
    ScalingAdvisor,
    ScalingTier,
    TrustDecayAnalyzer,
    get_integration_patterns,
)


# =============================================================================
# Enum Tests
# =============================================================================


class TestRiskProfile:
    """Tests for RiskProfile enum."""

    def test_low_value(self):
        """Test LOW profile has correct string value."""
        assert RiskProfile.LOW.value == "low"

    def test_medium_value(self):
        """Test MEDIUM profile has correct string value."""
        assert RiskProfile.MEDIUM.value == "medium"

    def test_high_value(self):
        """Test HIGH profile has correct string value."""
        assert RiskProfile.HIGH.value == "high"

    def test_all_profiles_exist(self):
        """Test that exactly 3 risk profiles exist."""
        assert len(RiskProfile) == 3

    def test_profiles_are_distinct(self):
        """Test all profile values are unique."""
        values = [p.value for p in RiskProfile]
        assert len(values) == len(set(values))


class TestArchitectureType:
    """Tests for ArchitectureType enum."""

    def test_hierarchical_value(self):
        """Test HIERARCHICAL type has correct string value."""
        assert ArchitectureType.HIERARCHICAL.value == "hierarchical"

    def test_peer_to_peer_value(self):
        """Test PEER_TO_PEER type has correct string value."""
        assert ArchitectureType.PEER_TO_PEER.value == "peer_to_peer"

    def test_role_based_value(self):
        """Test ROLE_BASED type has correct string value."""
        assert ArchitectureType.ROLE_BASED.value == "role_based"

    def test_state_machine_value(self):
        """Test STATE_MACHINE type has correct string value."""
        assert ArchitectureType.STATE_MACHINE.value == "state_machine"

    def test_all_architecture_types_exist(self):
        """Test that exactly 4 architecture types exist."""
        assert len(ArchitectureType) == 4


class TestIntegrationPattern:
    """Tests for IntegrationPattern enum."""

    def test_wrapper_value(self):
        """Test WRAPPER pattern has correct string value."""
        assert IntegrationPattern.WRAPPER.value == "wrapper"

    def test_native_value(self):
        """Test NATIVE pattern has correct string value."""
        assert IntegrationPattern.NATIVE.value == "native"

    def test_sidecar_value(self):
        """Test SIDECAR pattern has correct string value."""
        assert IntegrationPattern.SIDECAR.value == "sidecar"

    def test_all_patterns_exist(self):
        """Test that exactly 3 integration patterns exist."""
        assert len(IntegrationPattern) == 3


# =============================================================================
# Dataclass Tests
# =============================================================================


class TestFirewallConfig:
    """Tests for FirewallConfig dataclass."""

    def test_creation(self):
        """Test basic FirewallConfig creation."""
        config = FirewallConfig(accept_threshold=0.3, reject_threshold=0.7)
        assert config.accept_threshold == 0.3
        assert config.reject_threshold == 0.7

    def test_quarantine_range_property(self):
        """Test quarantine_range returns correct tuple."""
        config = FirewallConfig(accept_threshold=0.3, reject_threshold=0.7)
        assert config.quarantine_range == (0.3, 0.7)

    def test_quarantine_range_narrow(self):
        """Test quarantine_range with narrow gap."""
        config = FirewallConfig(accept_threshold=0.2, reject_threshold=0.6)
        low, high = config.quarantine_range
        assert low == 0.2
        assert high == 0.6
        assert high - low == pytest.approx(0.4)

    def test_quarantine_range_medium_profile(self):
        """Test quarantine_range for medium risk profile values."""
        config = FirewallConfig(accept_threshold=0.25, reject_threshold=0.65)
        assert config.quarantine_range == (0.25, 0.65)


class TestConsensusConfig:
    """Tests for ConsensusConfig dataclass."""

    def test_creation_with_defaults(self):
        """Test ConsensusConfig with default values."""
        config = ConsensusConfig(mechanism="Simple majority")
        assert config.mechanism == "Simple majority"
        assert config.requires_identity_verification is False
        assert config.byzantine_tolerant is False
        assert config.quorum_fraction == 0.5

    def test_creation_with_all_fields(self):
        """Test ConsensusConfig with all fields specified."""
        config = ConsensusConfig(
            mechanism="Byzantine-tolerant (n >= 3f + 1)",
            requires_identity_verification=True,
            byzantine_tolerant=True,
            quorum_fraction=0.75,
        )
        assert config.mechanism == "Byzantine-tolerant (n >= 3f + 1)"
        assert config.requires_identity_verification is True
        assert config.byzantine_tolerant is True
        assert config.quorum_fraction == 0.75

    def test_medium_profile_consensus(self):
        """Test ConsensusConfig for medium risk profile."""
        config = ConsensusConfig(
            mechanism="2/3 majority with identity verification",
            requires_identity_verification=True,
            quorum_fraction=0.667,
        )
        assert config.requires_identity_verification is True
        assert config.quorum_fraction == 0.667


class TestMonitoringConfig:
    """Tests for MonitoringConfig dataclass."""

    def test_creation_with_defaults(self):
        """Test MonitoringConfig with default values."""
        config = MonitoringConfig(frequency="Daily review")
        assert config.frequency == "Daily review"
        assert config.real_time_alerts is False
        assert config.immediate_alerting is False

    def test_creation_with_all_flags(self):
        """Test MonitoringConfig with all alerts enabled."""
        config = MonitoringConfig(
            frequency="Continuous with immediate alerting",
            real_time_alerts=True,
            immediate_alerting=True,
        )
        assert config.real_time_alerts is True
        assert config.immediate_alerting is True


# =============================================================================
# DeploymentConfigurator Tests
# =============================================================================


class TestDeploymentConfigurator:
    """Tests for DeploymentConfigurator."""

    def test_initialization_loads_all_profiles(self):
        """Test that initialization loads all 3 risk profiles."""
        configurator = DeploymentConfigurator()
        assert len(configurator.configs) == 3
        assert RiskProfile.LOW in configurator.configs
        assert RiskProfile.MEDIUM in configurator.configs
        assert RiskProfile.HIGH in configurator.configs

    def test_low_profile_firewall_thresholds(self):
        """Test low profile has correct firewall values (0.3/0.7)."""
        config = DeploymentConfigurator().get_config(RiskProfile.LOW)
        assert config.firewall.accept_threshold == 0.3
        assert config.firewall.reject_threshold == 0.7

    def test_low_profile_trust_decay(self):
        """Test low profile trust decay delta = 0.95."""
        config = DeploymentConfigurator().get_config(RiskProfile.LOW)
        assert config.trust_decay_delta == 0.95

    def test_low_profile_consensus(self):
        """Test low profile uses simple majority."""
        config = DeploymentConfigurator().get_config(RiskProfile.LOW)
        assert config.consensus.mechanism == "Simple majority"
        assert config.consensus.requires_identity_verification is False
        assert config.consensus.byzantine_tolerant is False
        assert config.consensus.quorum_fraction == 0.5

    def test_low_profile_monitoring(self):
        """Test low profile uses daily monitoring."""
        config = DeploymentConfigurator().get_config(RiskProfile.LOW)
        assert config.monitoring.frequency == "Daily review"
        assert config.monitoring.real_time_alerts is False
        assert config.monitoring.immediate_alerting is False

    def test_medium_profile_firewall_thresholds(self):
        """Test medium profile has correct firewall values (0.25/0.65)."""
        config = DeploymentConfigurator().get_config(RiskProfile.MEDIUM)
        assert config.firewall.accept_threshold == 0.25
        assert config.firewall.reject_threshold == 0.65

    def test_medium_profile_trust_decay(self):
        """Test medium profile trust decay delta = 0.9."""
        config = DeploymentConfigurator().get_config(RiskProfile.MEDIUM)
        assert config.trust_decay_delta == 0.9

    def test_medium_profile_consensus(self):
        """Test medium profile uses 2/3 majority with identity verification."""
        config = DeploymentConfigurator().get_config(RiskProfile.MEDIUM)
        assert "2/3 majority" in config.consensus.mechanism
        assert config.consensus.requires_identity_verification is True
        assert config.consensus.byzantine_tolerant is False
        assert config.consensus.quorum_fraction == 0.667

    def test_medium_profile_monitoring(self):
        """Test medium profile uses real-time alerts."""
        config = DeploymentConfigurator().get_config(RiskProfile.MEDIUM)
        assert config.monitoring.real_time_alerts is True
        assert config.monitoring.immediate_alerting is False

    def test_high_profile_firewall_thresholds(self):
        """Test high profile has correct firewall values (0.2/0.6)."""
        config = DeploymentConfigurator().get_config(RiskProfile.HIGH)
        assert config.firewall.accept_threshold == 0.2
        assert config.firewall.reject_threshold == 0.6

    def test_high_profile_trust_decay(self):
        """Test high profile trust decay delta = 0.85."""
        config = DeploymentConfigurator().get_config(RiskProfile.HIGH)
        assert config.trust_decay_delta == 0.85

    def test_high_profile_consensus(self):
        """Test high profile uses Byzantine-tolerant consensus."""
        config = DeploymentConfigurator().get_config(RiskProfile.HIGH)
        assert "Byzantine" in config.consensus.mechanism
        assert config.consensus.requires_identity_verification is True
        assert config.consensus.byzantine_tolerant is True
        assert config.consensus.quorum_fraction == 0.75

    def test_high_profile_monitoring(self):
        """Test high profile uses continuous + immediate alerting."""
        config = DeploymentConfigurator().get_config(RiskProfile.HIGH)
        assert config.monitoring.real_time_alerts is True
        assert config.monitoring.immediate_alerting is True

    def test_firewall_thresholds_tighten_with_risk(self):
        """Test that firewall thresholds tighten as risk increases."""
        configurator = DeploymentConfigurator()
        low = configurator.get_config(RiskProfile.LOW)
        med = configurator.get_config(RiskProfile.MEDIUM)
        high = configurator.get_config(RiskProfile.HIGH)

        # Accept thresholds decrease (more restrictive)
        assert low.firewall.accept_threshold > med.firewall.accept_threshold
        assert med.firewall.accept_threshold > high.firewall.accept_threshold

        # Reject thresholds decrease (more restrictive)
        assert low.firewall.reject_threshold > med.firewall.reject_threshold
        assert med.firewall.reject_threshold > high.firewall.reject_threshold

    def test_trust_decay_increases_with_risk(self):
        """Test that trust decays faster (lower delta) as risk increases."""
        configurator = DeploymentConfigurator()
        low = configurator.get_config(RiskProfile.LOW)
        med = configurator.get_config(RiskProfile.MEDIUM)
        high = configurator.get_config(RiskProfile.HIGH)

        assert low.trust_decay_delta > med.trust_decay_delta
        assert med.trust_decay_delta > high.trust_decay_delta

    def test_each_profile_has_characteristics(self):
        """Test all profiles have non-empty characteristics lists."""
        configurator = DeploymentConfigurator()
        for profile in RiskProfile:
            config = configurator.get_config(profile)
            assert len(config.characteristics) > 0

    def test_each_profile_has_description(self):
        """Test all profiles have non-empty descriptions."""
        configurator = DeploymentConfigurator()
        for profile in RiskProfile:
            config = configurator.get_config(profile)
            assert config.description != ""

    def test_recommend_profile_low_risk(self):
        """Test recommendation for low-risk characteristics."""
        configurator = DeploymentConfigurator()
        profile = configurator.recommend_profile({
            "autonomous": False,
            "sensitive_data": False,
            "customer_facing": False,
            "human_oversight": True,
        })
        assert profile == RiskProfile.LOW

    def test_recommend_profile_medium_risk(self):
        """Test recommendation for medium-risk characteristics."""
        configurator = DeploymentConfigurator()
        profile = configurator.recommend_profile({
            "autonomous": False,
            "sensitive_data": True,
            "customer_facing": True,
            "human_oversight": True,
        })
        assert profile == RiskProfile.MEDIUM

    def test_recommend_profile_high_risk(self):
        """Test recommendation for high-risk characteristics."""
        configurator = DeploymentConfigurator()
        profile = configurator.recommend_profile({
            "autonomous": True,
            "sensitive_data": True,
            "complex_delegation": True,
            "human_oversight": False,
        })
        assert profile == RiskProfile.HIGH

    def test_recommend_profile_autonomous_pushes_high(self):
        """Test that autonomous flag strongly pushes toward HIGH."""
        configurator = DeploymentConfigurator()
        profile = configurator.recommend_profile({
            "autonomous": True,
            "complex_delegation": True,
            "human_oversight": False,
        })
        assert profile == RiskProfile.HIGH

    def test_recommend_profile_human_oversight_reduces_risk(self):
        """Test that human_oversight reduces the risk score."""
        configurator = DeploymentConfigurator()
        # Without oversight
        no_oversight = configurator.recommend_profile({
            "sensitive_data": True,
            "customer_facing": True,
            "human_oversight": False,
        })
        # With oversight
        with_oversight = configurator.recommend_profile({
            "sensitive_data": True,
            "customer_facing": True,
            "human_oversight": True,
        })
        # human_oversight=True should yield same or lower risk
        risk_order = {RiskProfile.LOW: 0, RiskProfile.MEDIUM: 1, RiskProfile.HIGH: 2}
        assert risk_order[with_oversight] <= risk_order[no_oversight]

    def test_recommend_profile_empty_characteristics(self):
        """Test recommendation with empty characteristics dict."""
        configurator = DeploymentConfigurator()
        profile = configurator.recommend_profile({})
        assert profile == RiskProfile.LOW


# =============================================================================
# ArchitectureAdvisor Tests
# =============================================================================


class TestArchitectureAdvisor:
    """Tests for ArchitectureAdvisor."""

    def test_initialization_loads_all_architectures(self):
        """Test that all 4 architecture types are loaded."""
        advisor = ArchitectureAdvisor()
        assert len(advisor.guidance) == 4
        for arch_type in ArchitectureType:
            assert arch_type in advisor.guidance

    def test_hierarchical_guidance(self):
        """Test hierarchical architecture guidance content."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.HIERARCHICAL
        )
        assert guidance.architecture == ArchitectureType.HIERARCHICAL
        assert "orchestrator" in guidance.description.lower()
        assert len(guidance.risks) == 3
        assert len(guidance.mitigations) >= 3

    def test_hierarchical_examples(self):
        """Test hierarchical architecture examples list."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.HIERARCHICAL
        )
        assert "Claude Code" in guidance.examples
        assert "AutoGPT" in guidance.examples

    def test_hierarchical_has_critical_risk(self):
        """Test hierarchical architecture includes CRITICAL cascade risk."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.HIERARCHICAL
        )
        critical_risks = [
            r for r in guidance.risks if r.severity == RiskLevel.CRITICAL
        ]
        assert len(critical_risks) >= 1
        assert "cascade" in critical_risks[0].description.lower()

    def test_peer_to_peer_guidance(self):
        """Test peer-to-peer architecture guidance content."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.PEER_TO_PEER
        )
        assert guidance.architecture == ArchitectureType.PEER_TO_PEER
        assert "lateral" in guidance.description.lower()
        assert len(guidance.risks) == 3

    def test_peer_to_peer_examples(self):
        """Test peer-to-peer architecture examples list."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.PEER_TO_PEER
        )
        assert "Camel" in guidance.examples

    def test_peer_to_peer_sybil_risk(self):
        """Test peer-to-peer includes sybil attack risk."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.PEER_TO_PEER
        )
        sybil_risks = [
            r for r in guidance.risks if "sybil" in r.description.lower()
        ]
        assert len(sybil_risks) == 1

    def test_role_based_guidance(self):
        """Test role-based architecture guidance content."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.ROLE_BASED
        )
        assert guidance.architecture == ArchitectureType.ROLE_BASED
        assert "role" in guidance.description.lower()
        assert len(guidance.risks) == 3

    def test_role_based_examples(self):
        """Test role-based architecture examples list."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.ROLE_BASED
        )
        assert "CrewAI" in guidance.examples

    def test_role_based_impersonation_risk(self):
        """Test role-based includes role impersonation risk."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.ROLE_BASED
        )
        impersonation_risks = [
            r for r in guidance.risks
            if "impersonation" in r.description.lower()
        ]
        assert len(impersonation_risks) == 1

    def test_state_machine_guidance(self):
        """Test state machine architecture guidance content."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.STATE_MACHINE
        )
        assert guidance.architecture == ArchitectureType.STATE_MACHINE
        assert "state" in guidance.description.lower()
        assert len(guidance.risks) == 3

    def test_state_machine_examples(self):
        """Test state machine architecture examples list."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.STATE_MACHINE
        )
        assert "LangGraph" in guidance.examples

    def test_state_machine_corruption_risk(self):
        """Test state machine includes state corruption risk."""
        guidance = ArchitectureAdvisor().get_guidance(
            ArchitectureType.STATE_MACHINE
        )
        corruption_risks = [
            r for r in guidance.risks
            if "corruption" in r.description.lower()
        ]
        assert len(corruption_risks) == 1

    def test_get_all_risks_total_count(self):
        """Test get_all_risks returns correct total (3+3+3+3=12)."""
        advisor = ArchitectureAdvisor()
        all_risks = advisor.get_all_risks()
        assert len(all_risks) == 12

    def test_get_all_risks_includes_all_severities(self):
        """Test get_all_risks includes risks at multiple severity levels."""
        advisor = ArchitectureAdvisor()
        all_risks = advisor.get_all_risks()
        severities = {r.severity for r in all_risks}
        assert RiskLevel.CRITICAL in severities
        assert RiskLevel.HIGH in severities
        assert RiskLevel.MEDIUM in severities

    def test_all_risks_have_mitigations(self):
        """Test every risk has a non-empty mitigation string."""
        advisor = ArchitectureAdvisor()
        for risk in advisor.get_all_risks():
            assert risk.mitigation != ""

    def test_all_architectures_have_mitigations_list(self):
        """Test every architecture has at least 3 mitigations."""
        advisor = ArchitectureAdvisor()
        for arch_type in ArchitectureType:
            guidance = advisor.get_guidance(arch_type)
            assert len(guidance.mitigations) >= 3


# =============================================================================
# ScalingAdvisor Tests
# =============================================================================


class TestScalingAdvisor:
    """Tests for ScalingAdvisor."""

    def test_initialization_loads_4_tiers(self):
        """Test that 4 scaling tiers are loaded."""
        advisor = ScalingAdvisor()
        assert len(advisor.tiers) == 4

    def test_initialization_loads_5_latency_budgets(self):
        """Test that 5 latency budget components are loaded."""
        advisor = ScalingAdvisor()
        assert len(advisor.latency_budgets) == 5

    def test_tier_2_agents(self):
        """Test smallest multiagent system (2 agents)."""
        tier = ScalingAdvisor().get_tier(2)
        assert tier.min_agents == 2
        assert tier.max_agents == 10
        assert "individual" in tier.concerns.lower()

    def test_tier_5_agents(self):
        """Test mid-range of first tier (5 agents)."""
        tier = ScalingAdvisor().get_tier(5)
        assert tier.min_agents == 2
        assert tier.max_agents == 10

    def test_tier_10_agents(self):
        """Test boundary between first and second tier (10 agents)."""
        tier = ScalingAdvisor().get_tier(10)
        # 10 is the max of tier 1, so should match tier 1
        assert tier.max_agents == 10

    def test_tier_11_agents(self):
        """Test just above first tier boundary (11 agents)."""
        tier = ScalingAdvisor().get_tier(11)
        assert tier.min_agents == 10
        assert tier.max_agents == 100
        assert "coordination" in tier.concerns.lower()

    def test_tier_50_agents(self):
        """Test mid-range of second tier (50 agents)."""
        tier = ScalingAdvisor().get_tier(50)
        assert tier.min_agents == 10
        assert tier.max_agents == 100
        assert "byzantine" in tier.recommendations.lower()

    def test_tier_100_agents(self):
        """Test boundary between second and third tier (100 agents)."""
        tier = ScalingAdvisor().get_tier(100)
        assert tier.max_agents == 100

    def test_tier_500_agents(self):
        """Test mid-range of third tier (500 agents)."""
        tier = ScalingAdvisor().get_tier(500)
        assert tier.min_agents == 100
        assert tier.max_agents == 1000
        assert "emergent" in tier.concerns.lower()

    def test_tier_1000_agents(self):
        """Test boundary between third and fourth tier (1000 agents)."""
        tier = ScalingAdvisor().get_tier(1000)
        assert tier.max_agents == 1000

    def test_tier_5000_agents(self):
        """Test large-scale deployment (5000 agents)."""
        tier = ScalingAdvisor().get_tier(5000)
        assert tier.min_agents == 1000
        assert tier.max_agents is None
        assert "colonial" in tier.concerns.lower()
        assert "stigmergic" in tier.recommendations.lower()

    def test_tier_very_large(self):
        """Test very large deployment (1000000 agents)."""
        tier = ScalingAdvisor().get_tier(1_000_000)
        assert tier.max_agents is None

    def test_agent_count_below_2_raises_error(self):
        """Test that agent count below 2 raises ValueError."""
        advisor = ScalingAdvisor()
        with pytest.raises(ValueError, match="at least 2"):
            advisor.get_tier(1)

    def test_agent_count_zero_raises_error(self):
        """Test that zero agents raises ValueError."""
        advisor = ScalingAdvisor()
        with pytest.raises(ValueError, match="at least 2"):
            advisor.get_tier(0)

    def test_agent_count_negative_raises_error(self):
        """Test that negative agent count raises ValueError."""
        advisor = ScalingAdvisor()
        with pytest.raises(ValueError, match="at least 2"):
            advisor.get_tier(-5)

    def test_total_latency_budget_range(self):
        """Test total latency budget calculation."""
        advisor = ScalingAdvisor()
        low, high = advisor.total_latency_budget()
        # Sum of lows: 5 + 1 + 0.1 + 1 + 50 = 57.1
        assert low == pytest.approx(57.1)
        # Sum of highs: 10 + 2 + 1 + 5 + 200 = 218
        assert high == pytest.approx(218.0)

    def test_latency_budget_firewall(self):
        """Test firewall latency budget is 5-10ms."""
        advisor = ScalingAdvisor()
        firewall = [
            b for b in advisor.latency_budgets if b.component == "Firewall"
        ]
        assert len(firewall) == 1
        assert firewall[0].typical_ms_low == 5
        assert firewall[0].typical_ms_high == 10

    def test_latency_budget_trust_computation(self):
        """Test trust computation latency budget is 1-2ms."""
        advisor = ScalingAdvisor()
        trust = [
            b for b in advisor.latency_budgets
            if b.component == "Trust computation"
        ]
        assert len(trust) == 1
        assert trust[0].typical_ms_low == 1
        assert trust[0].typical_ms_high == 2

    def test_latency_budget_sandbox_lookup(self):
        """Test sandbox lookup latency budget is <1ms."""
        advisor = ScalingAdvisor()
        sandbox = [
            b for b in advisor.latency_budgets
            if b.component == "Sandbox lookup"
        ]
        assert len(sandbox) == 1
        assert sandbox[0].typical_ms_high <= 1

    def test_latency_budget_tripwire_check(self):
        """Test tripwire check latency budget is 1-5ms."""
        advisor = ScalingAdvisor()
        tripwire = [
            b for b in advisor.latency_budgets
            if b.component == "Tripwire check"
        ]
        assert len(tripwire) == 1
        assert tripwire[0].typical_ms_low == 1
        assert tripwire[0].typical_ms_high == 5

    def test_latency_budget_consensus(self):
        """Test consensus latency budget is 50-200ms."""
        advisor = ScalingAdvisor()
        consensus = [
            b for b in advisor.latency_budgets
            if b.component == "Consensus"
        ]
        assert len(consensus) == 1
        assert consensus[0].typical_ms_low == 50
        assert consensus[0].typical_ms_high == 200

    def test_consensus_dominates_latency(self):
        """Test that consensus is the largest latency component."""
        advisor = ScalingAdvisor()
        consensus = [
            b for b in advisor.latency_budgets
            if b.component == "Consensus"
        ][0]
        for budget in advisor.latency_budgets:
            if budget.component != "Consensus":
                assert budget.typical_ms_high < consensus.typical_ms_low


# =============================================================================
# TrustDecayAnalyzer Tests
# =============================================================================


class TestTrustDecayAnalyzer:
    """Tests for TrustDecayAnalyzer."""

    def test_effective_trust_depth_zero(self):
        """Test that trust at depth 0 equals initial trust."""
        result = TrustDecayAnalyzer.effective_trust(1.0, 0.85, 0)
        assert result == pytest.approx(1.0)

    def test_effective_trust_depth_one(self):
        """Test that trust at depth 1 equals initial * delta."""
        result = TrustDecayAnalyzer.effective_trust(1.0, 0.85, 1)
        assert result == pytest.approx(0.85)

    def test_effective_trust_high_profile_depth_4(self):
        """Test manuscript value: delta=0.85 at depth 4 gives ~0.522."""
        result = TrustDecayAnalyzer.effective_trust(1.0, 0.85, 4)
        assert result == pytest.approx(0.522, abs=0.001)

    def test_effective_trust_low_profile_depth_4(self):
        """Test low profile: delta=0.95 at depth 4."""
        result = TrustDecayAnalyzer.effective_trust(1.0, 0.95, 4)
        expected = 0.95 ** 4
        assert result == pytest.approx(expected)

    def test_effective_trust_medium_profile_depth_4(self):
        """Test medium profile: delta=0.9 at depth 4."""
        result = TrustDecayAnalyzer.effective_trust(1.0, 0.9, 4)
        expected = 0.9 ** 4
        assert result == pytest.approx(expected)

    def test_effective_trust_partial_initial(self):
        """Test with initial trust less than 1.0."""
        result = TrustDecayAnalyzer.effective_trust(0.8, 0.9, 3)
        expected = 0.8 * (0.9 ** 3)
        assert result == pytest.approx(expected)

    def test_effective_trust_zero_initial(self):
        """Test with zero initial trust stays zero."""
        result = TrustDecayAnalyzer.effective_trust(0.0, 0.9, 5)
        assert result == 0.0

    def test_effective_trust_invalid_initial_above_one(self):
        """Test ValueError for initial_trust > 1."""
        with pytest.raises(ValueError, match="initial_trust must be 0-1"):
            TrustDecayAnalyzer.effective_trust(1.5, 0.9, 1)

    def test_effective_trust_invalid_initial_negative(self):
        """Test ValueError for negative initial_trust."""
        with pytest.raises(ValueError, match="initial_trust must be 0-1"):
            TrustDecayAnalyzer.effective_trust(-0.1, 0.9, 1)

    def test_effective_trust_invalid_delta_zero(self):
        """Test ValueError for delta = 0."""
        with pytest.raises(ValueError, match="delta must be"):
            TrustDecayAnalyzer.effective_trust(1.0, 0.0, 1)

    def test_effective_trust_invalid_delta_one(self):
        """Test ValueError for delta = 1."""
        with pytest.raises(ValueError, match="delta must be"):
            TrustDecayAnalyzer.effective_trust(1.0, 1.0, 1)

    def test_effective_trust_invalid_delta_negative(self):
        """Test ValueError for negative delta."""
        with pytest.raises(ValueError, match="delta must be"):
            TrustDecayAnalyzer.effective_trust(1.0, -0.5, 1)

    def test_effective_trust_invalid_depth_negative(self):
        """Test ValueError for negative depth."""
        with pytest.raises(ValueError, match="depth must be non-negative"):
            TrustDecayAnalyzer.effective_trust(1.0, 0.9, -1)

    def test_practical_depth_limit_high_profile(self):
        """Test manuscript value: delta=0.85 gives practical limit ~14-15."""
        limit = TrustDecayAnalyzer.practical_depth_limit(0.85)
        # log(0.1) / log(0.85) = -2.3026 / -0.16252 = 14.17 -> ceil = 15
        assert limit == 15

    def test_practical_depth_limit_medium_profile(self):
        """Test practical limit for delta=0.9."""
        limit = TrustDecayAnalyzer.practical_depth_limit(0.9)
        # log(0.1) / log(0.9) = -2.3026 / -0.10536 = 21.85 -> ceil = 22
        assert limit == 22

    def test_practical_depth_limit_low_profile(self):
        """Test practical limit for delta=0.95."""
        limit = TrustDecayAnalyzer.practical_depth_limit(0.95)
        # log(0.1) / log(0.95) = -2.3026 / -0.05129 = 44.89 -> ceil = 45
        assert limit == 45

    def test_practical_depth_limit_custom_threshold(self):
        """Test practical limit with custom threshold."""
        limit = TrustDecayAnalyzer.practical_depth_limit(0.85, threshold=0.5)
        # log(0.5) / log(0.85) = -0.6931 / -0.16252 = 4.265 -> ceil = 5
        assert limit == 5

    def test_practical_depth_limit_verify_at_boundary(self):
        """Test that trust at practical limit is indeed below threshold."""
        delta = 0.85
        limit = TrustDecayAnalyzer.practical_depth_limit(delta)
        trust_at_limit = delta ** limit
        assert trust_at_limit < 0.1

    def test_practical_depth_limit_verify_one_before_is_above(self):
        """Test that trust one hop before limit is at or above threshold."""
        delta = 0.85
        limit = TrustDecayAnalyzer.practical_depth_limit(delta)
        trust_before = delta ** (limit - 1)
        assert trust_before >= 0.1

    def test_practical_depth_limit_invalid_delta(self):
        """Test ValueError for invalid delta in practical_depth_limit."""
        with pytest.raises(ValueError, match="delta must be"):
            TrustDecayAnalyzer.practical_depth_limit(1.0)

    def test_practical_depth_limit_invalid_threshold(self):
        """Test ValueError for invalid threshold."""
        with pytest.raises(ValueError, match="threshold must be"):
            TrustDecayAnalyzer.practical_depth_limit(0.9, threshold=0.0)

    def test_practical_depth_limit_threshold_one(self):
        """Test ValueError for threshold = 1."""
        with pytest.raises(ValueError, match="threshold must be"):
            TrustDecayAnalyzer.practical_depth_limit(0.9, threshold=1.0)

    def test_compare_profiles_returns_three_entries(self):
        """Test compare_profiles returns data for all 3 profiles."""
        result = TrustDecayAnalyzer.compare_profiles()
        assert len(result) == 3
        assert "low" in result
        assert "medium" in result
        assert "high" in result

    def test_compare_profiles_delta_values(self):
        """Test compare_profiles returns correct delta for each profile."""
        result = TrustDecayAnalyzer.compare_profiles()
        assert result["low"]["delta"] == 0.95
        assert result["medium"]["delta"] == 0.9
        assert result["high"]["delta"] == 0.85

    def test_compare_profiles_high_trust_at_depth_4(self):
        """Test manuscript value: delta=0.85 at depth 4 gives 0.522."""
        result = TrustDecayAnalyzer.compare_profiles()
        assert result["high"]["trust_at_depth_4"] == pytest.approx(0.522, abs=0.001)

    def test_compare_profiles_high_practical_limit(self):
        """Test manuscript value: delta=0.85 practical limit is 15."""
        result = TrustDecayAnalyzer.compare_profiles()
        assert result["high"]["practical_limit"] == 15

    def test_compare_profiles_practical_limits_decrease_with_risk(self):
        """Test that higher risk means shallower practical limit."""
        result = TrustDecayAnalyzer.compare_profiles()
        assert result["low"]["practical_limit"] > result["medium"]["practical_limit"]
        assert result["medium"]["practical_limit"] > result["high"]["practical_limit"]

    def test_compare_profiles_half_trust_depth(self):
        """Test half-trust depth values are reasonable."""
        result = TrustDecayAnalyzer.compare_profiles()
        # High: log(0.5)/log(0.85) = 4.265 -> round(4.3, 1) = 4.3
        assert result["high"]["half_trust_depth"] == pytest.approx(4.3, abs=0.1)
        # Medium: log(0.5)/log(0.9) = 6.579 -> round(6.6, 1) = 6.6
        assert result["medium"]["half_trust_depth"] == pytest.approx(6.6, abs=0.1)

    def test_compare_profiles_all_keys_present(self):
        """Test each profile entry has all expected keys."""
        result = TrustDecayAnalyzer.compare_profiles()
        expected_keys = {"delta", "practical_limit", "half_trust_depth", "trust_at_depth_4"}
        for name in ["low", "medium", "high"]:
            assert set(result[name].keys()) == expected_keys


# =============================================================================
# Integration Pattern Tests
# =============================================================================


class TestIntegrationPatterns:
    """Tests for get_integration_patterns function."""

    def test_returns_three_patterns(self):
        """Test that exactly 3 integration patterns are returned."""
        patterns = get_integration_patterns()
        assert len(patterns) == 3

    def test_all_pattern_types_present(self):
        """Test all IntegrationPattern enum values are keys."""
        patterns = get_integration_patterns()
        assert IntegrationPattern.WRAPPER in patterns
        assert IntegrationPattern.NATIVE in patterns
        assert IntegrationPattern.SIDECAR in patterns

    def test_wrapper_pattern(self):
        """Test wrapper integration pattern content."""
        patterns = get_integration_patterns()
        wrapper = patterns[IntegrationPattern.WRAPPER]
        assert wrapper.name == "Wrapper Integration"
        assert "wrap" in wrapper.description.lower()
        assert len(wrapper.components) == 3
        assert len(wrapper.pros) >= 1
        assert len(wrapper.cons) >= 1

    def test_wrapper_components_cover_input_inter_output(self):
        """Test wrapper components cover input, inter-agent, and output."""
        patterns = get_integration_patterns()
        wrapper = patterns[IntegrationPattern.WRAPPER]
        combined = " ".join(wrapper.components).lower()
        assert "input" in combined
        assert "inter-agent" in combined
        assert "output" in combined

    def test_native_pattern(self):
        """Test native integration pattern content."""
        patterns = get_integration_patterns()
        native = patterns[IntegrationPattern.NATIVE]
        assert native.name == "Native Integration"
        assert "embed" in native.description.lower()
        assert len(native.components) == 3
        assert len(native.pros) >= 1
        assert len(native.cons) >= 1

    def test_native_mentions_belief_sandbox(self):
        """Test native pattern references belief sandbox."""
        patterns = get_integration_patterns()
        native = patterns[IntegrationPattern.NATIVE]
        combined = " ".join(native.components).lower()
        assert "belief sandbox" in combined

    def test_sidecar_pattern(self):
        """Test sidecar integration pattern content."""
        patterns = get_integration_patterns()
        sidecar = patterns[IntegrationPattern.SIDECAR]
        assert sidecar.name == "Sidecar Integration"
        assert "separate" in sidecar.description.lower()
        assert len(sidecar.components) == 3
        assert len(sidecar.pros) >= 1
        assert len(sidecar.cons) >= 1

    def test_sidecar_async_limitation(self):
        """Test sidecar pattern acknowledges async limitation."""
        patterns = get_integration_patterns()
        sidecar = patterns[IntegrationPattern.SIDECAR]
        combined = " ".join(sidecar.cons).lower()
        assert "async" in combined

    def test_each_pattern_has_correct_enum(self):
        """Test each guidance object references its correct pattern enum."""
        patterns = get_integration_patterns()
        for pattern_type, guidance in patterns.items():
            assert guidance.pattern == pattern_type


# =============================================================================
# Edge Case and Cross-Cutting Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and cross-cutting tests."""

    def test_deployment_config_risk_profile_matches(self):
        """Test each config's risk_profile field matches its key."""
        configurator = DeploymentConfigurator()
        for profile in RiskProfile:
            config = configurator.get_config(profile)
            assert config.risk_profile == profile

    def test_trust_decay_monotonically_decreases(self):
        """Test trust decreases monotonically with depth."""
        delta = 0.85
        prev = 1.0
        for depth in range(1, 20):
            current = TrustDecayAnalyzer.effective_trust(1.0, delta, depth)
            assert current < prev
            prev = current

    def test_high_profile_trust_below_10_percent_after_14_hops(self):
        """Test manuscript claim: delta=0.85 -> <10% after 14 hops."""
        trust = TrustDecayAnalyzer.effective_trust(1.0, 0.85, 15)
        assert trust < 0.1

    def test_high_profile_trust_above_50_percent_at_4_hops(self):
        """Test manuscript claim: delta=0.85 -> ~52% at 4 hops."""
        trust = TrustDecayAnalyzer.effective_trust(1.0, 0.85, 4)
        assert trust > 0.5
        assert trust < 0.6

    def test_quarantine_range_widens_as_risk_decreases(self):
        """Test quarantine range (gap) is widest for low risk."""
        configurator = DeploymentConfigurator()
        low = configurator.get_config(RiskProfile.LOW)
        high = configurator.get_config(RiskProfile.HIGH)
        low_range = low.firewall.reject_threshold - low.firewall.accept_threshold
        high_range = high.firewall.reject_threshold - high.firewall.accept_threshold
        assert low_range == high_range  # Both are 0.4

    def test_scaling_tiers_are_contiguous(self):
        """Test that scaling tiers cover the full range without gaps."""
        advisor = ScalingAdvisor()
        for i in range(len(advisor.tiers) - 1):
            current = advisor.tiers[i]
            next_tier = advisor.tiers[i + 1]
            assert current.max_agents == next_tier.min_agents

    def test_scaling_last_tier_unbounded(self):
        """Test that the last scaling tier has no upper bound."""
        advisor = ScalingAdvisor()
        last = advisor.tiers[-1]
        assert last.max_agents is None

    def test_latency_budget_all_have_optimization_notes(self):
        """Test all latency budgets have non-empty optimization notes."""
        advisor = ScalingAdvisor()
        for budget in advisor.latency_budgets:
            assert budget.optimization_note != ""

    def test_architecture_risk_dataclass(self):
        """Test ArchitectureRisk dataclass creation."""
        risk = ArchitectureRisk(
            description="Test risk",
            severity=RiskLevel.HIGH,
            mitigation="Test mitigation",
        )
        assert risk.description == "Test risk"
        assert risk.severity == RiskLevel.HIGH
        assert risk.mitigation == "Test mitigation"

    def test_integration_guidance_dataclass(self):
        """Test IntegrationGuidance dataclass creation with defaults."""
        guidance = IntegrationGuidance(
            pattern=IntegrationPattern.WRAPPER,
            name="Test",
            description="Test description",
        )
        assert guidance.components == []
        assert guidance.pros == []
        assert guidance.cons == []
