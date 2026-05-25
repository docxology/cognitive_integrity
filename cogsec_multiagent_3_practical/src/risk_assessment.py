"""
from __future__ import annotations

Risk Assessment Framework for Cognitive Security.

Implements Section 06 of the Practical Implementation Guide:
Attack surface mapping, threat modeling, worked examples,
and common attack scenario analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from . import RiskLevel, AssessmentResult


# =============================================================================
# Enums
# =============================================================================


class EntryPointType(Enum):
    """Types of system entry points.

    Represents the five categories of entry points identified in
    the attack surface mapping process (Step 1).
    """

    USER_INPUT = "user_input"
    TOOL_OUTPUT = "tool_output"
    AGENT_COMMUNICATION = "agent_communication"
    PERSISTENT_MEMORY = "persistent_memory"
    EXTERNAL_TRIGGER = "external_trigger"


class InfluencePath(Enum):
    """Types of influence paths from entry points.

    Represents the four influence propagation modes traced
    in the attack surface mapping process (Step 2).
    """

    DIRECT = "direct"
    DELEGATED = "delegated"
    STORED = "stored"
    EMERGENT = "emergent"


class ImpactLevel(Enum):
    """Attack impact levels (1-4).

    Used in Step 3 of attack surface mapping to rate the
    potential impact of a successful attack.

    Args:
        value: String label for the impact level.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def numeric(self) -> int:
        """Numeric score for the impact level.

        Returns:
            Integer from 1 (low) to 4 (critical).
        """
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class LikelihoodLevel(Enum):
    """Attack likelihood levels (1-4).

    Used in Step 4 of attack surface mapping to assess the
    probability of an attack occurring, based on adversary profiles.

    Args:
        value: String label for the likelihood level.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @property
    def numeric(self) -> int:
        """Numeric score for the likelihood level.

        Returns:
            Integer from 1 (low) to 4 (very high).
        """
        return {"low": 1, "medium": 2, "high": 3, "very_high": 4}[self.value]


class MitigationPriority(Enum):
    """Mitigation priority levels.

    Derived from the risk matrix (Impact x Likelihood) to determine
    the urgency of remediation actions.
    """

    IMMEDIATE = "immediate"
    NEAR_TERM = "near_term"
    MONITORING = "monitoring"
    NORMAL_CYCLE = "normal_cycle"


# =============================================================================
# Entry Point Analysis
# =============================================================================


@dataclass
class EntryPoint:
    """A system entry point in the attack surface.

    Represents a single point where external input enters the system,
    as identified in Step 1 of the attack surface mapping process.

    Args:
        type: Entry point type classification.
        name: Specific name or description of this entry point.
        example: Example of input through this entry point.
        attack_vector: Primary attack vector exploiting this entry point.
        trust_level: Trust level assigned to input from this source (0-1).
        cif_defense: CIF defense mechanism applied to this entry point.
        residual_risk: Remaining risk after defense mechanisms are applied.
    """

    type: EntryPointType
    name: str
    example: str = ""
    attack_vector: str = ""
    trust_level: float = 0.5
    cif_defense: str = ""
    residual_risk: RiskLevel = RiskLevel.MEDIUM


@dataclass
class InfluenceAnalysis:
    """Analysis of an influence path from an entry point.

    Represents the tracing of how influence propagates from an entry
    point through the system (Step 2 of attack surface mapping).

    Args:
        entry_point: Source entry point where influence originates.
        path_type: Type of influence propagation.
        description: How influence propagates through this path.
        affected_agents: Which agents are affected by this influence.
        detection_mechanism: How to detect influence through this path.
    """

    entry_point: EntryPoint
    path_type: InfluencePath
    description: str
    affected_agents: list[str] = field(default_factory=list)
    detection_mechanism: str = ""


# =============================================================================
# Risk Scoring
# =============================================================================


@dataclass
class RiskScore:
    """Computed risk score for a threat.

    Implements the Step 5 risk formula: Risk = Impact x Likelihood.
    Priority is automatically derived from the impact/likelihood matrix.

    Args:
        impact: Impact level of the threat.
        likelihood: Likelihood level of the threat.
        score: Computed risk score (impact.numeric * likelihood.numeric).
            Auto-computed in __post_init__.
        priority: Mitigation priority derived from the risk matrix.
            Auto-computed in __post_init__.
    """

    impact: ImpactLevel
    likelihood: LikelihoodLevel
    score: int = 0
    priority: MitigationPriority = MitigationPriority.NORMAL_CYCLE

    def __post_init__(self) -> None:
        """Compute score and priority from impact/likelihood."""
        self.score = self.impact.numeric * self.likelihood.numeric
        self.priority = self._compute_priority()

    def _compute_priority(self) -> MitigationPriority:
        """Determine priority from impact and likelihood.

        Priority matrix:
        - IMMEDIATE: Critical impact + High/Very High likelihood
        - NEAR_TERM: High/Critical impact + High/Very High likelihood
          (except Critical+High which is IMMEDIATE)
        - MONITORING: Critical impact + Low/Medium likelihood
        - NORMAL_CYCLE: Everything else

        Returns:
            Computed MitigationPriority.
        """
        if self.impact == ImpactLevel.CRITICAL and self.likelihood in (
            LikelihoodLevel.HIGH,
            LikelihoodLevel.VERY_HIGH,
        ):
            return MitigationPriority.IMMEDIATE
        elif self.impact in (ImpactLevel.HIGH, ImpactLevel.CRITICAL) and self.likelihood in (
            LikelihoodLevel.HIGH,
            LikelihoodLevel.VERY_HIGH,
        ):
            return MitigationPriority.NEAR_TERM
        elif self.impact == ImpactLevel.CRITICAL and self.likelihood in (
            LikelihoodLevel.LOW,
            LikelihoodLevel.MEDIUM,
        ):
            return MitigationPriority.MONITORING
        else:
            return MitigationPriority.NORMAL_CYCLE


# =============================================================================
# Threat Modeling
# =============================================================================


@dataclass
class SystemDescription:
    """Description of the system being assessed.

    Captures the top-level attributes of a multi-agent system
    for the threat modeling worksheet.

    Args:
        name: System name.
        architecture_type: Architecture classification (e.g., hierarchical, mesh).
        agent_count: Number of agents in the system.
        risk_profile: Overall risk profile description.
        agents: List of agent names/roles in the system.
    """

    name: str
    architecture_type: str
    agent_count: int
    risk_profile: str
    agents: list[str] = field(default_factory=list)


@dataclass
class DetectionPoint:
    """A point where an attack could be detected.

    Represents a detection opportunity within an attack scenario,
    mapping to specific CIF defense mechanisms.

    Args:
        mechanism: Detection mechanism type (firewall, tripwire, invariant, drift).
        step_number: At which attack step detection occurs.
        description: How detection works at this point.
        effective: Whether detection would actually work against this attack.
    """

    mechanism: str
    step_number: int
    description: str
    effective: bool = True


@dataclass
class ThreatScenario:
    """A complete threat scenario for analysis.

    Represents a single attack scenario with its attack chain,
    detection opportunities, impact assessment, and identified gaps.

    Args:
        name: Scenario name.
        description: Brief description of the attack.
        attack_steps: Ordered list of attack steps.
        detection_points: Points where the attack could be detected.
        impact_description: What happens if the attack succeeds.
        impact_level: Impact severity rating.
        likelihood_level: Likelihood assessment rating.
        mitigation_gaps: Identified gaps in current defenses.
        risk_score: Computed risk score (populated by compute_risk).
    """

    name: str
    description: str
    attack_steps: list[str] = field(default_factory=list)
    detection_points: list[DetectionPoint] = field(default_factory=list)
    impact_description: str = ""
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    likelihood_level: LikelihoodLevel = LikelihoodLevel.MEDIUM
    mitigation_gaps: list[str] = field(default_factory=list)
    risk_score: RiskScore | None = None

    def compute_risk(self) -> RiskScore:
        """Compute and store risk score from impact and likelihood.

        Returns:
            Computed RiskScore with score and priority.
        """
        self.risk_score = RiskScore(
            impact=self.impact_level,
            likelihood=self.likelihood_level,
        )
        return self.risk_score


# =============================================================================
# Attack Surface Mapper
# =============================================================================


class AttackSurfaceMapper:
    """Implements the 5-step attack surface mapping process.

    The five steps are:
    1. Identify entry points (add_entry_point)
    2. Trace influence paths (add_influence_path)
    3. Rate attack impact (via ThreatScenario.impact_level)
    4. Assess likelihood (via ThreatScenario.likelihood_level)
    5. Prioritize mitigations (prioritize)

    The evaluate method produces an overall AssessmentResult.
    """

    def __init__(self) -> None:
        """Initialize empty mapper with no entry points, paths, or scenarios."""
        self.entry_points: list[EntryPoint] = []
        self.influence_paths: list[InfluenceAnalysis] = []
        self.threat_scenarios: list[ThreatScenario] = []

    def add_entry_point(self, entry_point: EntryPoint) -> None:
        """Step 1: Add an entry point to the attack surface.

        Args:
            entry_point: Entry point to register.
        """
        self.entry_points.append(entry_point)

    def add_influence_path(self, analysis: InfluenceAnalysis) -> None:
        """Step 2: Add an influence path analysis.

        Args:
            analysis: Influence path to register.
        """
        self.influence_paths.append(analysis)

    def add_threat_scenario(self, scenario: ThreatScenario) -> None:
        """Steps 3-4: Add a threat scenario with impact and likelihood.

        Automatically computes the risk score upon addition.

        Args:
            scenario: Threat scenario to analyze and register.
        """
        scenario.compute_risk()
        self.threat_scenarios.append(scenario)

    def prioritize(self) -> list[ThreatScenario]:
        """Step 5: Return scenarios sorted by risk score (highest first).

        Returns:
            List of threat scenarios in descending order of risk score.
        """
        return sorted(
            self.threat_scenarios,
            key=lambda s: s.risk_score.score if s.risk_score else 0,
            reverse=True,
        )

    def get_immediate_priorities(self) -> list[ThreatScenario]:
        """Get scenarios requiring immediate mitigation.

        Returns:
            List of scenarios with IMMEDIATE mitigation priority.
        """
        return [
            s
            for s in self.threat_scenarios
            if s.risk_score and s.risk_score.priority == MitigationPriority.IMMEDIATE
        ]

    def evaluate(self) -> AssessmentResult:
        """Evaluate the overall attack surface.

        Produces an AssessmentResult summarizing:
        - Whether the assessment passes (no immediate priorities)
        - Normalized score (1.0 = no risk, 0.0 = maximum risk)
        - Overall risk level based on highest scenario score
        - Top findings (up to 5)
        - Recommendations (up to 10)

        Returns:
            AssessmentResult summarizing the attack surface assessment.
        """
        if not self.threat_scenarios:
            return AssessmentResult(
                passed=True,
                score=1.0,
                risk_level=RiskLevel.LOW,
                findings=["No threat scenarios identified"],
                recommendations=["Conduct threat modeling to identify scenarios"],
            )

        immediate = self.get_immediate_priorities()
        prioritized = self.prioritize()
        max_score = max(
            (s.risk_score.score for s in self.threat_scenarios if s.risk_score),
            default=0,
        )

        # Determine overall risk level from highest individual score
        if max_score >= 12:
            risk_level = RiskLevel.CRITICAL
        elif max_score >= 8:
            risk_level = RiskLevel.HIGH
        elif max_score >= 4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build findings from top 5 scenarios
        findings = [
            f"{s.name}: risk score {s.risk_score.score} ({s.risk_score.priority.value})"
            for s in prioritized[:5]
            if s.risk_score
        ]

        # Build recommendations: immediate actions first, then gaps
        recommendations: list[str] = []
        for s in immediate:
            recommendations.append(f"IMMEDIATE: Mitigate {s.name}")
        for s in prioritized:
            for gap in s.mitigation_gaps:
                recommendations.append(f"{s.name}: {gap}")

        # Normalize score: 0 = worst (16/16), 1.0 = best (0/16)
        normalized_score = 1.0 - (max_score / 16.0)

        return AssessmentResult(
            passed=len(immediate) == 0,
            score=max(0.0, normalized_score),
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations[:10],
        )


# =============================================================================
# Threat Model Worksheet
# =============================================================================


@dataclass
class ThreatModelWorksheet:
    """Structured threat modeling worksheet from Section 06.

    Provides a complete framework for documenting the threat model
    of a multi-agent system, including system description, entry
    point analysis, attack scenarios, and post-assessment actions.

    Args:
        system: System being assessed.
        entry_points: Identified entry points.
        scenarios: Attack scenarios analyzed.
        post_actions: Post-assessment action items.
    """

    system: SystemDescription
    entry_points: list[EntryPoint] = field(default_factory=list)
    scenarios: list[ThreatScenario] = field(default_factory=list)
    post_actions: list[str] = field(default_factory=list)

    def add_entry_point(self, entry_point: EntryPoint) -> None:
        """Add entry point to worksheet.

        Args:
            entry_point: Entry point to register.
        """
        self.entry_points.append(entry_point)

    def add_scenario(self, scenario: ThreatScenario) -> None:
        """Add and score a threat scenario.

        Automatically computes the risk score upon addition.

        Args:
            scenario: Threat scenario to analyze and register.
        """
        scenario.compute_risk()
        self.scenarios.append(scenario)

    def highest_risk_scenario(self) -> ThreatScenario | None:
        """Get the highest-risk scenario.

        Returns:
            Highest-risk ThreatScenario, or None if no scenarios exist.
        """
        if not self.scenarios:
            return None
        return max(
            self.scenarios,
            key=lambda s: s.risk_score.score if s.risk_score else 0,
        )

    def summary(self) -> dict[str, Any]:
        """Generate worksheet summary.

        Returns:
            Dictionary with summary statistics including system name,
            agent count, entry point count, scenario count,
            immediate-priority count, and total mitigation gaps.
        """
        return {
            "system_name": self.system.name,
            "agent_count": self.system.agent_count,
            "entry_point_count": len(self.entry_points),
            "scenario_count": len(self.scenarios),
            "immediate_count": sum(
                1
                for s in self.scenarios
                if s.risk_score
                and s.risk_score.priority == MitigationPriority.IMMEDIATE
            ),
            "total_gaps": sum(len(s.mitigation_gaps) for s in self.scenarios),
        }


# =============================================================================
# Common Attack Scenarios (Pre-built)
# =============================================================================


class CommonAttackScenarios:
    """Pre-built common attack scenarios from Section 06.

    Provides ready-to-use threat scenarios for the most common
    cognitive security attack patterns:
    - Trust Laundering
    - Sybil Consensus Manipulation
    - Progressive Belief Drift
    - Orchestrator Identity Theft

    Also includes a complete worked example (e-commerce CustomerBot).
    """

    @staticmethod
    def trust_laundering() -> ThreatScenario:
        """Trust laundering via delegation chain.

        An adversary exploits the delegation chain to amplify low trust
        into high influence, eventually triggering actions that should
        require higher authorization.

        Returns:
            Pre-configured ThreatScenario with computed risk score.
        """
        scenario = ThreatScenario(
            name="Trust Laundering",
            description="Adversary exploits delegation chain to amplify low trust into high influence",
            attack_steps=[
                "Attacker compromises low-trust agent via external input",
                "Compromised agent sends plausible request to medium-trust agent",
                "Medium-trust agent incorporates request and delegates to high-trust agent",
                "High-trust agent executes action attacker should not have triggered",
            ],
            detection_points=[
                DetectionPoint(
                    "Trust calculus",
                    3,
                    "delta^d bound prevents amplification",
                ),
                DetectionPoint(
                    "Delegation monitoring",
                    2,
                    "Unusual delegation depth detected",
                ),
                DetectionPoint(
                    "Trust anomaly",
                    3,
                    "Unexpected trust score changes",
                ),
            ],
            impact_description="Unauthorized actions via trust escalation",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.MEDIUM,
            mitigation_gaps=[
                "Ensure delegation decay is configured",
                "Monitor for deep delegation chains",
            ],
        )
        scenario.compute_risk()
        return scenario

    @staticmethod
    def sybil_consensus() -> ThreatScenario:
        """Sybil attack on consensus mechanism.

        An adversary creates multiple fake agent identities to influence
        multi-agent decision-making processes through numerical superiority.

        Returns:
            Pre-configured ThreatScenario with computed risk score.
        """
        scenario = ThreatScenario(
            name="Sybil Consensus Manipulation",
            description="Adversary creates fake agents to influence multi-agent decisions",
            attack_steps=[
                "Adversary creates multiple fake agent identities",
                "Fake agents join consensus process",
                "Fake agents vote together to skew outcome",
                "Legitimate agents outnumbered in quorum",
            ],
            detection_points=[
                DetectionPoint(
                    "Agent authentication",
                    1,
                    "Identity verification rejects fakes",
                ),
                DetectionPoint(
                    "Voting pattern analysis",
                    3,
                    "Unusual voting patterns detected",
                ),
                DetectionPoint(
                    "Byzantine threshold",
                    4,
                    "Threshold violation triggers alert",
                ),
            ],
            impact_description="Consensus manipulation leading to wrong collective decisions",
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.MEDIUM,
            mitigation_gaps=[
                "Require strong agent authentication",
                "Implement Byzantine consensus",
            ],
        )
        scenario.compute_risk()
        return scenario

    @staticmethod
    def progressive_belief_drift() -> ThreatScenario:
        """Progressive sub-threshold belief manipulation.

        An adversary makes small, sub-threshold belief changes over time,
        each below the detection threshold, but cumulatively significant.

        Returns:
            Pre-configured ThreatScenario with computed risk score.
        """
        scenario = ThreatScenario(
            name="Progressive Belief Drift",
            description="Adversary makes small, sub-threshold belief changes over time",
            attack_steps=[
                "Adversary identifies belief drift detection threshold",
                "Small belief modifications introduced per interaction",
                "Individual changes stay below alert threshold",
                "Cumulative drift significantly alters agent behavior",
            ],
            detection_points=[
                DetectionPoint(
                    "Long-term drift monitoring",
                    3,
                    "Sliding window detects cumulative change",
                ),
                DetectionPoint(
                    "Baseline comparison",
                    4,
                    "Periodic full audit catches drift",
                ),
                DetectionPoint(
                    "Tripwire",
                    4,
                    "Eventual canary detection",
                ),
            ],
            impact_description="Gradual corruption of agent reasoning without triggering alerts",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.LOW,
            mitigation_gaps=[
                "Use sliding window drift detection",
                "Periodic full belief audit",
            ],
        )
        scenario.compute_risk()
        return scenario

    @staticmethod
    def orchestrator_identity_theft() -> ThreatScenario:
        """Orchestrator identity impersonation.

        An adversary convinces worker agents they are communicating with
        the legitimate orchestrator, gaining control over the entire
        worker agent pool.

        Returns:
            Pre-configured ThreatScenario with computed risk score.
        """
        scenario = ThreatScenario(
            name="Orchestrator Identity Theft",
            description="Adversary convinces worker agents they are communicating with orchestrator",
            attack_steps=[
                "Adversary intercepts or spoofs orchestrator communication channel",
                "Workers receive instructions from fake orchestrator",
                "Workers execute malicious instructions believing them legitimate",
                "Real orchestrator loses control of worker agents",
            ],
            detection_points=[
                DetectionPoint(
                    "Identity canary",
                    1,
                    "Canary verification rejects fake",
                ),
                DetectionPoint(
                    "Challenge-response",
                    2,
                    "Authentication challenge fails",
                ),
                DetectionPoint(
                    "Behavioral anomaly",
                    3,
                    "Orchestrator behavior pattern differs",
                ),
            ],
            impact_description="Complete system compromise through orchestrator impersonation",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.LOW,
            mitigation_gaps=[
                "Plant identity canaries",
                "Require mutual authentication for sensitive operations",
            ],
        )
        scenario.compute_risk()
        return scenario

    @staticmethod
    def ecommerce_worked_example() -> ThreatModelWorksheet:
        """Worked example: E-Commerce CustomerBot from manuscript.

        Implements the complete worked example from Section 06,
        modeling a 5-agent e-commerce customer support system with
        entry point analysis and a shipping API trust laundering
        attack scenario.

        Returns:
            Complete ThreatModelWorksheet for the e-commerce scenario.
        """
        system = SystemDescription(
            name="CustomerBot Multi-Agent System",
            architecture_type="hierarchical",
            agent_count=5,
            risk_profile="medium_high",
            agents=[
                "Orchestrator",
                "OrderAgent",
                "ShippingAgent",
                "RefundAgent",
                "CustomerAgent",
            ],
        )

        worksheet = ThreatModelWorksheet(system=system)

        # Entry points from manuscript
        worksheet.add_entry_point(
            EntryPoint(
                type=EntryPointType.USER_INPUT,
                name="Customer chat input",
                trust_level=0.3,
                cif_defense="Firewall + Sandbox",
                residual_risk=RiskLevel.LOW,
            )
        )
        worksheet.add_entry_point(
            EntryPoint(
                type=EntryPointType.TOOL_OUTPUT,
                name="Order database queries",
                trust_level=0.8,
                cif_defense="Invariant checks (read-only)",
                residual_risk=RiskLevel.LOW,
            )
        )
        worksheet.add_entry_point(
            EntryPoint(
                type=EntryPointType.EXTERNAL_TRIGGER,
                name="Shipping API responses",
                trust_level=0.5,
                cif_defense="Quarantine + schema validation",
                residual_risk=RiskLevel.MEDIUM,
            )
        )
        worksheet.add_entry_point(
            EntryPoint(
                type=EntryPointType.EXTERNAL_TRIGGER,
                name="Payment gateway webhooks",
                trust_level=0.7,
                cif_defense="Signature verification + tripwire",
                residual_risk=RiskLevel.LOW,
            )
        )
        worksheet.add_entry_point(
            EntryPoint(
                type=EntryPointType.TOOL_OUTPUT,
                name="Product catalog API",
                trust_level=0.6,
                cif_defense="Rate limiting + format validation",
                residual_risk=RiskLevel.LOW,
            )
        )

        # Shipping API trust laundering scenario from manuscript
        shipping_scenario = ThreatScenario(
            name="Shipping API Trust Laundering",
            description="Shipping API compromise leading to credential phishing",
            attack_steps=[
                "Attacker compromises shipping provider API endpoint",
                "Malicious JSON payload injected in tracking response",
                "ShippingAgent processes response, forms belief about urgent security requirement",
                "ShippingAgent communicates urgency to Orchestrator with elevated priority",
                "Orchestrator routes security-flagged task to CustomerAgent",
                "CustomerAgent requests customer re-authentication",
                "Customer provides credentials to fake security verification",
            ],
            detection_points=[
                DetectionPoint(
                    "Firewall",
                    2,
                    "Instruction-like content triggers elevated threat score",
                    True,
                ),
                DetectionPoint(
                    "Sandbox",
                    3,
                    "Belief about security requirement enters sandbox",
                    True,
                ),
                DetectionPoint(
                    "Tripwire",
                    4,
                    "Identity canary: ShippingAgent claiming security authority",
                    True,
                ),
                DetectionPoint(
                    "Invariant",
                    6,
                    "INV-CRED-1: No agent may request credentials except designated flows",
                    True,
                ),
            ],
            impact_description="Customer credential theft, PII exposure, regulatory violation",
            impact_level=ImpactLevel.CRITICAL,
            likelihood_level=LikelihoodLevel.MEDIUM,
            mitigation_gaps=[
                "Shipping API responses not validated against expected schema",
                "ShippingAgent has no authority boundary preventing security claims",
                "Orchestrator passes priority flags without verifying source authority",
            ],
        )
        worksheet.add_scenario(shipping_scenario)

        worksheet.post_actions = [
            "Immediate: Add shipping API response schema validation",
            "Short-term: Implement role-based authority constraints for security claims",
            "Medium-term: Deploy canary beliefs for credential-related instruction propagation",
            "Ongoing: Add shipping API patterns to red team testing corpus",
        ]

        return worksheet

    @staticmethod
    def get_all() -> list[ThreatScenario]:
        """Get all common attack scenarios.

        Returns:
            List of all four pre-built threat scenarios with computed
            risk scores.
        """
        return [
            CommonAttackScenarios.trust_laundering(),
            CommonAttackScenarios.sybil_consensus(),
            CommonAttackScenarios.progressive_belief_drift(),
            CommonAttackScenarios.orchestrator_identity_theft(),
        ]


__all__ = [
    "EntryPointType",
    "InfluencePath",
    "ImpactLevel",
    "LikelihoodLevel",
    "MitigationPriority",
    "EntryPoint",
    "InfluenceAnalysis",
    "RiskScore",
    "SystemDescription",
    "DetectionPoint",
    "ThreatScenario",
    "AttackSurfaceMapper",
    "ThreatModelWorksheet",
    "CommonAttackScenarios",
]
