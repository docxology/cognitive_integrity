"""
Deployment Configuration and Guidance for Cognitive Security.

Implements Section 05 of the Practical Implementation Guide:
Risk profiles, architecture-specific guidance, scaling considerations,
and trust decay analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from . import RiskLevel, AssessmentResult


# =============================================================================
# Risk Profiles
# =============================================================================


class RiskProfile(Enum):
    """Deployment risk profile levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArchitectureType(Enum):
    """Multiagent architecture types."""

    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"
    ROLE_BASED = "role_based"
    STATE_MACHINE = "state_machine"


class IntegrationPattern(Enum):
    """CIF integration patterns."""

    WRAPPER = "wrapper"
    NATIVE = "native"
    SIDECAR = "sidecar"


@dataclass
class FirewallConfig:
    """Firewall threshold configuration.

    Args:
        accept_threshold: Below this = accept (0-1)
        reject_threshold: Above this = reject (0-1)
    """

    accept_threshold: float
    reject_threshold: float

    @property
    def quarantine_range(self) -> tuple[float, float]:
        """Get the quarantine range (between accept and reject)."""
        return (self.accept_threshold, self.reject_threshold)


@dataclass
class ConsensusConfig:
    """Consensus mechanism configuration.

    Args:
        mechanism: Description of consensus type
        requires_identity_verification: Whether agent identity must be verified
        byzantine_tolerant: Whether Byzantine faults are tolerated
        quorum_fraction: Fraction of agents needed for quorum (0-1)
    """

    mechanism: str
    requires_identity_verification: bool = False
    byzantine_tolerant: bool = False
    quorum_fraction: float = 0.5


@dataclass
class MonitoringConfig:
    """Monitoring configuration.

    Args:
        frequency: Monitoring frequency description
        real_time_alerts: Whether real-time alerting is enabled
        immediate_alerting: Whether immediate alerting for critical events
    """

    frequency: str
    real_time_alerts: bool = False
    immediate_alerting: bool = False


@dataclass
class DeploymentConfig:
    """Complete deployment configuration for a risk profile.

    Args:
        risk_profile: The risk profile this configures
        firewall: Firewall settings
        trust_decay_delta: Trust decay factor delta
        consensus: Consensus mechanism settings
        monitoring: Monitoring settings
        description: Human-readable description
        characteristics: List of deployment characteristics
    """

    risk_profile: RiskProfile
    firewall: FirewallConfig
    trust_decay_delta: float
    consensus: ConsensusConfig
    monitoring: MonitoringConfig
    description: str = ""
    characteristics: list[str] = field(default_factory=list)


class DeploymentConfigurator:
    """Maps risk profiles to exact parameter values from manuscript.

    Provides deployment configurations for Low, Medium, and High
    risk profiles as specified in Section 05.
    """

    def __init__(self) -> None:
        """Initialize with manuscript configurations."""
        self.configs: dict[RiskProfile, DeploymentConfig] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load configurations from manuscript Section 05."""
        self.configs = {
            RiskProfile.LOW: DeploymentConfig(
                risk_profile=RiskProfile.LOW,
                firewall=FirewallConfig(
                    accept_threshold=0.3,
                    reject_threshold=0.7,
                ),
                trust_decay_delta=0.95,
                consensus=ConsensusConfig(
                    mechanism="Simple majority",
                    requires_identity_verification=False,
                    byzantine_tolerant=False,
                    quorum_fraction=0.5,
                ),
                monitoring=MonitoringConfig(
                    frequency="Daily review",
                    real_time_alerts=False,
                    immediate_alerting=False,
                ),
                description="Internal-only, non-sensitive, human-in-the-loop",
                characteristics=[
                    "Internal-only deployment",
                    "Non-sensitive data handling",
                    "Human-in-the-loop for all significant actions",
                    "Limited inter-agent communication",
                ],
            ),
            RiskProfile.MEDIUM: DeploymentConfig(
                risk_profile=RiskProfile.MEDIUM,
                firewall=FirewallConfig(
                    accept_threshold=0.25,
                    reject_threshold=0.65,
                ),
                trust_decay_delta=0.9,
                consensus=ConsensusConfig(
                    mechanism="2/3 majority with identity verification",
                    requires_identity_verification=True,
                    byzantine_tolerant=False,
                    quorum_fraction=0.667,
                ),
                monitoring=MonitoringConfig(
                    frequency="Real-time alerts for critical events",
                    real_time_alerts=True,
                    immediate_alerting=False,
                ),
                description="Customer-facing, limited autonomy, periodic oversight",
                characteristics=[
                    "Customer-facing but limited autonomy",
                    "Some sensitive data handling",
                    "Periodic human oversight",
                    "Moderate delegation chains",
                ],
            ),
            RiskProfile.HIGH: DeploymentConfig(
                risk_profile=RiskProfile.HIGH,
                firewall=FirewallConfig(
                    accept_threshold=0.2,
                    reject_threshold=0.6,
                ),
                trust_decay_delta=0.85,
                consensus=ConsensusConfig(
                    mechanism="Byzantine-tolerant (n >= 3f + 1)",
                    requires_identity_verification=True,
                    byzantine_tolerant=True,
                    quorum_fraction=0.75,
                ),
                monitoring=MonitoringConfig(
                    frequency="Continuous with immediate alerting",
                    real_time_alerts=True,
                    immediate_alerting=True,
                ),
                description="Autonomous, sensitive/regulated, complex delegation",
                characteristics=[
                    "Autonomous actions with significant impact",
                    "Sensitive/regulated data handling",
                    "Extended periods without human oversight",
                    "Complex delegation hierarchies",
                ],
            ),
        }

    def get_config(self, profile: RiskProfile) -> DeploymentConfig:
        """Get deployment configuration for a risk profile.

        Args:
            profile: Risk profile to configure for

        Returns:
            Complete DeploymentConfig for the profile
        """
        return self.configs[profile]

    def recommend_profile(self, characteristics: dict[str, bool]) -> RiskProfile:
        """Recommend a risk profile based on deployment characteristics.

        Uses a weighted scoring system to map deployment characteristics
        to the appropriate risk profile. Higher scores indicate greater
        security requirements.

        Args:
            characteristics: Dict of characteristic flags:
                - "autonomous": Has autonomous actions
                - "sensitive_data": Handles sensitive data
                - "customer_facing": Customer-facing deployment
                - "complex_delegation": Has complex delegation chains
                - "human_oversight": Has regular human oversight

        Returns:
            Recommended RiskProfile
        """
        score = 0
        if characteristics.get("autonomous", False):
            score += 3
        if characteristics.get("sensitive_data", False):
            score += 2
        if characteristics.get("customer_facing", False):
            score += 1
        if characteristics.get("complex_delegation", False):
            score += 2
        if characteristics.get("human_oversight", True):
            score -= 1

        if score >= 5:
            return RiskProfile.HIGH
        elif score >= 2:
            return RiskProfile.MEDIUM
        else:
            return RiskProfile.LOW


# =============================================================================
# Architecture-Specific Guidance
# =============================================================================


@dataclass
class ArchitectureRisk:
    """A risk specific to an architecture type.

    Args:
        description: Risk description
        severity: Severity level
        mitigation: Recommended mitigation
    """

    description: str
    severity: RiskLevel
    mitigation: str


@dataclass
class ArchitectureGuidance:
    """Architecture-specific deployment guidance.

    Args:
        architecture: Architecture type
        description: Architecture characteristics
        examples: Example systems using this architecture
        risks: Architecture-specific risks
        mitigations: Recommended mitigations (summary)
    """

    architecture: ArchitectureType
    description: str
    examples: list[str] = field(default_factory=list)
    risks: list[ArchitectureRisk] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)


class ArchitectureAdvisor:
    """Provides architecture-specific risks and mitigations.

    Covers the 4 architecture types from Section 05:
    Hierarchical, Peer-to-Peer, Role-Based, and State Machine.
    """

    def __init__(self) -> None:
        """Initialize with manuscript guidance."""
        self.guidance: dict[ArchitectureType, ArchitectureGuidance] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load architecture guidance from manuscript."""
        self.guidance = {
            ArchitectureType.HIERARCHICAL: ArchitectureGuidance(
                architecture=ArchitectureType.HIERARCHICAL,
                description="Central orchestrator delegates to specialized workers",
                examples=["Claude Code", "AutoGPT"],
                risks=[
                    ArchitectureRisk(
                        "Orchestrator compromise cascades to all workers",
                        RiskLevel.CRITICAL,
                        "Strong orchestrator protection with strictest thresholds",
                    ),
                    ArchitectureRisk(
                        "Worker escalation can influence orchestrator",
                        RiskLevel.HIGH,
                        "Bounded upward influence from workers",
                    ),
                    ArchitectureRisk(
                        "Single point of failure",
                        RiskLevel.HIGH,
                        "Consider multi-orchestrator redundancy for critical deployments",
                    ),
                ],
                mitigations=[
                    "Strong orchestrator protection (strictest thresholds)",
                    "Bounded upward influence from workers",
                    "Orchestrator tripwires for identity canaries",
                    "Consider multi-orchestrator redundancy for critical deployments",
                ],
            ),
            ArchitectureType.PEER_TO_PEER: ArchitectureGuidance(
                architecture=ArchitectureType.PEER_TO_PEER,
                description="Equal-authority agents with lateral communication",
                examples=["Camel"],
                risks=[
                    ArchitectureRisk(
                        "Lateral movement attacks (compromise spreads horizontally)",
                        RiskLevel.HIGH,
                        "Network topology monitoring",
                    ),
                    ArchitectureRisk(
                        "Sybil attacks (injected fake agents)",
                        RiskLevel.HIGH,
                        "Strong agent authentication",
                    ),
                    ArchitectureRisk(
                        "Consensus manipulation",
                        RiskLevel.HIGH,
                        "Byzantine consensus for all multi-agent decisions",
                    ),
                ],
                mitigations=[
                    "Byzantine consensus for all multi-agent decisions",
                    "Strong agent authentication",
                    "Network topology monitoring",
                    "Reputation systems with slow trust building",
                ],
            ),
            ArchitectureType.ROLE_BASED: ArchitectureGuidance(
                architecture=ArchitectureType.ROLE_BASED,
                description="Agents have defined roles with boundaries",
                examples=["CrewAI"],
                risks=[
                    ArchitectureRisk(
                        "Role impersonation",
                        RiskLevel.HIGH,
                        "Challenge-response for role verification",
                    ),
                    ArchitectureRisk(
                        "Boundary violation",
                        RiskLevel.MEDIUM,
                        "Cross-role action validation",
                    ),
                    ArchitectureRisk(
                        "Role privilege escalation",
                        RiskLevel.HIGH,
                        "Role-based permission boundaries",
                    ),
                ],
                mitigations=[
                    "Role-based permission boundaries",
                    "Challenge-response for role verification",
                    "Cross-role action validation",
                    "Audit trails for role-based actions",
                ],
            ),
            ArchitectureType.STATE_MACHINE: ArchitectureGuidance(
                architecture=ArchitectureType.STATE_MACHINE,
                description="Explicit state transitions govern behavior",
                examples=["LangGraph"],
                risks=[
                    ArchitectureRisk(
                        "State corruption",
                        RiskLevel.HIGH,
                        "State integrity verification (hashing)",
                    ),
                    ArchitectureRisk(
                        "Invalid transition injection",
                        RiskLevel.MEDIUM,
                        "Transition validation against allowed graph",
                    ),
                    ArchitectureRisk(
                        "State history manipulation",
                        RiskLevel.MEDIUM,
                        "History immutability enforcement",
                    ),
                ],
                mitigations=[
                    "State integrity verification (hashing)",
                    "Transition validation against allowed graph",
                    "History immutability enforcement",
                    "Rollback capability to known-good states",
                ],
            ),
        }

    def get_guidance(self, architecture: ArchitectureType) -> ArchitectureGuidance:
        """Get guidance for an architecture type.

        Args:
            architecture: Architecture type

        Returns:
            ArchitectureGuidance for the type
        """
        return self.guidance[architecture]

    def get_all_risks(self) -> list[ArchitectureRisk]:
        """Get all risks across all architectures.

        Returns:
            List of all architecture risks
        """
        risks = []
        for guidance in self.guidance.values():
            risks.extend(guidance.risks)
        return risks


# =============================================================================
# Scaling Guidance
# =============================================================================


@dataclass
class ScalingTier:
    """Scaling guidance for an agent count range.

    Args:
        min_agents: Minimum agent count
        max_agents: Maximum agent count (None = unlimited)
        concerns: Primary security concerns
        recommendations: Recommended practices
    """

    min_agents: int
    max_agents: int | None
    concerns: str
    recommendations: str


@dataclass
class LatencyBudget:
    """Latency budget for a CIF component.

    Args:
        component: CIF component name
        typical_ms_low: Low end of typical latency (ms)
        typical_ms_high: High end of typical latency (ms)
        optimization_note: When to optimize
    """

    component: str
    typical_ms_low: float
    typical_ms_high: float
    optimization_note: str


class ScalingAdvisor:
    """Provides scaling guidance based on agent count.

    Implements the scaling considerations table from Section 05.
    """

    def __init__(self) -> None:
        """Initialize with manuscript scaling tiers."""
        self.tiers: list[ScalingTier] = []
        self.latency_budgets: list[LatencyBudget] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load scaling tiers and latency budgets from manuscript."""
        self.tiers = [
            ScalingTier(
                min_agents=2,
                max_agents=10,
                concerns="Individual agent security dominates",
                recommendations="Standard CIF deployment",
            ),
            ScalingTier(
                min_agents=10,
                max_agents=100,
                concerns="Coordination attacks become viable",
                recommendations="Byzantine consensus required",
            ),
            ScalingTier(
                min_agents=100,
                max_agents=1000,
                concerns="Emergent behavior security",
                recommendations="Collective monitoring, quorum scaling",
            ),
            ScalingTier(
                min_agents=1000,
                max_agents=None,
                concerns="Colonial cognitive security",
                recommendations="Stigmergic defense patterns (see Part 1 Appendix)",
            ),
        ]

        self.latency_budgets = [
            LatencyBudget(
                "Firewall", 5, 10,
                "Batch classification for bulk inputs",
            ),
            LatencyBudget(
                "Trust computation", 1, 2,
                "Cache trust scores for stable relationships",
            ),
            LatencyBudget(
                "Sandbox lookup", 0.1, 1,
                "Rarely a bottleneck",
            ),
            LatencyBudget(
                "Tripwire check", 1, 5,
                "Sample rather than check all beliefs",
            ),
            LatencyBudget(
                "Consensus", 50, 200,
                "Reserve for critical decisions only",
            ),
        ]

    def get_tier(self, agent_count: int) -> ScalingTier:
        """Get scaling tier for an agent count.

        Args:
            agent_count: Number of agents in deployment

        Returns:
            Appropriate ScalingTier

        Raises:
            ValueError: If agent_count < 2
        """
        if agent_count < 2:
            raise ValueError(
                "Agent count must be at least 2 for multiagent system"
            )

        for tier in self.tiers:
            if tier.max_agents is None or agent_count <= tier.max_agents:
                if agent_count >= tier.min_agents:
                    return tier

        # Fallback to largest tier
        return self.tiers[-1]

    def total_latency_budget(self) -> tuple[float, float]:
        """Calculate total CIF latency budget range.

        Returns:
            Tuple of (min_total_ms, max_total_ms)
        """
        low = sum(b.typical_ms_low for b in self.latency_budgets)
        high = sum(b.typical_ms_high for b in self.latency_budgets)
        return (low, high)


# =============================================================================
# Trust Decay Analysis
# =============================================================================


class TrustDecayAnalyzer:
    """Analyzes trust decay across delegation depths.

    Implements the trust decay analysis from Section 05,
    including practical limits and profile comparison.

    The core formula is T_effective = T_initial * delta^depth,
    where delta is the per-hop decay factor (0 < delta < 1).
    """

    @staticmethod
    def effective_trust(
        initial_trust: float,
        delta: float,
        depth: int,
    ) -> float:
        """Calculate effective trust at delegation depth.

        T_effective = T_initial x delta^d

        Args:
            initial_trust: Starting trust level (0-1)
            delta: Decay factor (0 < delta < 1)
            depth: Delegation depth

        Returns:
            Effective trust at the given depth

        Raises:
            ValueError: If parameters out of range
        """
        if not 0 <= initial_trust <= 1:
            raise ValueError(
                f"initial_trust must be 0-1, got {initial_trust}"
            )
        if not 0 < delta < 1:
            raise ValueError(f"delta must be (0,1), got {delta}")
        if depth < 0:
            raise ValueError(f"depth must be non-negative, got {depth}")

        return initial_trust * (delta ** depth)

    @staticmethod
    def practical_depth_limit(
        delta: float,
        threshold: float = 0.1,
    ) -> int:
        """Calculate the depth where trust drops below threshold.

        Solves: delta^d < threshold -> d > log(threshold) / log(delta)

        Args:
            delta: Decay factor
            threshold: Trust threshold (default 0.1 = 10%)

        Returns:
            First depth where trust is below threshold

        Raises:
            ValueError: If parameters out of range
        """
        if not 0 < delta < 1:
            raise ValueError(f"delta must be (0,1), got {delta}")
        if not 0 < threshold < 1:
            raise ValueError(
                f"threshold must be (0,1), got {threshold}"
            )

        import math

        return int(math.ceil(math.log(threshold) / math.log(delta)))

    @staticmethod
    def compare_profiles() -> dict[str, dict[str, Any]]:
        """Compare trust decay across the 3 risk profiles.

        Computes practical depth limit, half-trust depth, and trust
        at depth 4 for each profile's delta value.

        Returns:
            Dict mapping profile name to decay characteristics:
                - delta: The decay factor
                - practical_limit: Depth where trust < 10%
                - half_trust_depth: Depth where trust = 50%
                - trust_at_depth_4: Trust remaining after 4 hops
        """
        profiles = {
            "low": 0.95,
            "medium": 0.9,
            "high": 0.85,
        }

        import math

        result: dict[str, dict[str, Any]] = {}
        for name, delta in profiles.items():
            practical_limit = int(
                math.ceil(math.log(0.1) / math.log(delta))
            )
            half_trust_depth = math.log(0.5) / math.log(delta)
            trust_at_4 = delta ** 4

            result[name] = {
                "delta": delta,
                "practical_limit": practical_limit,
                "half_trust_depth": round(half_trust_depth, 1),
                "trust_at_depth_4": round(trust_at_4, 3),
            }

        return result


# =============================================================================
# Integration Pattern Guidance
# =============================================================================


@dataclass
class IntegrationGuidance:
    """Guidance for a CIF integration pattern.

    Args:
        pattern: Integration pattern type
        name: Human-readable name
        description: How it works
        components: What CIF components are integrated and how
        pros: Advantages
        cons: Disadvantages
    """

    pattern: IntegrationPattern
    name: str
    description: str
    components: list[str] = field(default_factory=list)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)


def get_integration_patterns() -> dict[IntegrationPattern, IntegrationGuidance]:
    """Get all integration pattern guidance from manuscript.

    Returns:
        Dictionary mapping patterns to their guidance
    """
    return {
        IntegrationPattern.WRAPPER: IntegrationGuidance(
            pattern=IntegrationPattern.WRAPPER,
            name="Wrapper Integration",
            description="Wrap existing agent framework with CIF layer",
            components=[
                "Input: Firewall classification before agent processing",
                "Inter-agent: Trust verification on message passing",
                "Output: Invariant checking before action execution",
            ],
            pros=[
                "No changes to existing agents",
                "Quick deployment",
            ],
            cons=[
                "Limited visibility into internal state",
                "Higher latency",
            ],
        ),
        IntegrationPattern.NATIVE: IntegrationGuidance(
            pattern=IntegrationPattern.NATIVE,
            name="Native Integration",
            description="Embed CIF into agent architecture",
            components=[
                "Agent maintains own belief sandbox",
                "Trust calculus integrated with delegation logic",
                "Tripwires planted during agent initialization",
            ],
            pros=[
                "Deep visibility",
                "Lower latency",
                "Tighter security",
            ],
            cons=[
                "Requires agent modification",
                "More complex deployment",
            ],
        ),
        IntegrationPattern.SIDECAR: IntegrationGuidance(
            pattern=IntegrationPattern.SIDECAR,
            name="Sidecar Integration",
            description="Run CIF as separate monitoring service",
            components=[
                "Asynchronous belief drift detection",
                "Centralized trust matrix management",
                "Aggregated alert dashboard",
            ],
            pros=[
                "Non-intrusive",
                "Centralized monitoring",
                "Independent scaling",
            ],
            cons=[
                "Async only",
                "Cannot block in real-time",
                "Network dependency",
            ],
        ),
    }


__all__ = [
    "RiskProfile",
    "ArchitectureType",
    "IntegrationPattern",
    "FirewallConfig",
    "ConsensusConfig",
    "MonitoringConfig",
    "DeploymentConfig",
    "DeploymentConfigurator",
    "ArchitectureRisk",
    "ArchitectureGuidance",
    "ArchitectureAdvisor",
    "ScalingTier",
    "LatencyBudget",
    "ScalingAdvisor",
    "TrustDecayAnalyzer",
    "IntegrationGuidance",
    "get_integration_patterns",
]
