"""
from __future__ import annotations

Operator Posture Assessment for Cognitive Security.

Implements Section 02 of the Practical Implementation Guide:
Five Pillars assessment, maturity scoring, and capability validation.
"""

from dataclasses import dataclass, field
from enum import Enum

# Import shared types from package
from . import RiskLevel, PostureLevel, AssessmentResult


class PillarType(Enum):
    """The Five Pillars of Cognitive Security Posture."""
    TRUST_BOUNDARY = "trust_boundary"
    BELIEF_PROVENANCE = "belief_provenance"
    DELEGATION_HYGIENE = "delegation_hygiene"
    COORDINATION_INTEGRITY = "coordination_integrity"
    CONTINUOUS_MONITORING = "continuous_monitoring"


@dataclass
class AssessmentQuestion:
    """A single assessment question for a pillar.

    Args:
        id: Unique question identifier (e.g., "TB-1")
        pillar: Which pillar this question assesses
        text: The assessment question text
        weight: Relative importance weight (default 1.0)
        score: Response score 0-5 (0=not assessed)
        notes: Optional assessor notes
    """
    id: str
    pillar: PillarType
    text: str
    weight: float = 1.0
    score: int = 0
    notes: str = ""


@dataclass
class PillarAssessment:
    """Assessment result for a single pillar.

    Args:
        pillar: Which pillar was assessed
        score: Normalized pillar score (0.0-1.0)
        max_score: Maximum possible score
        raw_score: Sum of question scores
        gaps: Identified gaps (questions scoring below threshold)
        recommendations: Specific recommendations for improvement
    """
    pillar: PillarType
    score: float
    max_score: float
    raw_score: float
    gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class FivePillarsAssessment:
    """Full 20-question Five Pillars posture assessment.

    Implements the Five Pillars framework from Section 02:
    - Trust Boundary Awareness (4 questions)
    - Belief Provenance (4 questions)
    - Delegation Hygiene (4 questions)
    - Coordination Integrity (4 questions)
    - Continuous Monitoring (4 questions)

    Each question scored 0-5. Pillar scores normalized to 0-1.
    """

    def __init__(self) -> None:
        """Initialize with default assessment questions."""
        self.questions: list[AssessmentQuestion] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load the 20 default assessment questions from manuscript."""
        # Trust Boundary Awareness
        self.questions.extend([
            AssessmentQuestion(
                id="TB-1", pillar=PillarType.TRUST_BOUNDARY,
                text="Have you documented all trust relationships in your architecture, including implicit assumptions?"
            ),
            AssessmentQuestion(
                id="TB-2", pillar=PillarType.TRUST_BOUNDARY,
                text="For each trust assumption, what would happen if it were violated? Could an attacker escalate privileges, corrupt beliefs, or damage high-value assets?"
            ),
            AssessmentQuestion(
                id="TB-3", pillar=PillarType.TRUST_BOUNDARY,
                text="How would you detect a trust violation? Do you have monitoring in place, or would violations be invisible until damage manifests?"
            ),
            AssessmentQuestion(
                id="TB-4", pillar=PillarType.TRUST_BOUNDARY,
                text="What mechanisms limit damage from trust exploitation? Can a compromised trust relationship cascade through the system, or is blast radius contained?"
            ),
        ])

        # Belief Provenance
        self.questions.extend([
            AssessmentQuestion(
                id="BP-1", pillar=PillarType.BELIEF_PROVENANCE,
                text="Can you trace the origin of any belief an agent holds? Given a statement an agent makes or an action it takes, can you identify the inputs that led to that conclusion?"
            ),
            AssessmentQuestion(
                id="BP-2", pillar=PillarType.BELIEF_PROVENANCE,
                text="How trustworthy is each upstream source? Do you distinguish between beliefs derived from verified databases, unverified web content, user assertions, and other agent outputs?"
            ),
            AssessmentQuestion(
                id="BP-3", pillar=PillarType.BELIEF_PROVENANCE,
                text="Could an adversary have influenced the belief chain? What would an attack path look like, and would your monitoring detect it?"
            ),
            AssessmentQuestion(
                id="BP-4", pillar=PillarType.BELIEF_PROVENANCE,
                text="Do you discount multi-hop information appropriately? Beliefs that have passed through multiple summarization steps should carry less weight than direct observations."
            ),
        ])

        # Delegation Hygiene
        self.questions.extend([
            AssessmentQuestion(
                id="DH-1", pillar=PillarType.DELEGATION_HYGIENE,
                text="Do you implement trust decay across delegation hops? The trust associated with information or requests should diminish as they pass through intermediaries."
            ),
            AssessmentQuestion(
                id="DH-2", pillar=PillarType.DELEGATION_HYGIENE,
                text="Is there a maximum delegation depth? Can an agent delegate to an agent that delegates to another agent indefinitely, or is recursion bounded?"
            ),
            AssessmentQuestion(
                id="DH-3", pillar=PillarType.DELEGATION_HYGIENE,
                text="Can delegated authority exceed direct authority? If Agent A can only perform read operations, can it delegate a write operation to Agent B?"
            ),
            AssessmentQuestion(
                id="DH-4", pillar=PillarType.DELEGATION_HYGIENE,
                text="Do you verify delegation chains? Can you audit who originated a delegated task and what transformations occurred along the way?"
            ),
        ])

        # Coordination Integrity
        self.questions.extend([
            AssessmentQuestion(
                id="CI-1", pillar=PillarType.COORDINATION_INTEGRITY,
                text="Do critical decisions require Byzantine-tolerant consensus? Protocols that tolerate up to f failures require n >= 3f + 1 agents."
            ),
            AssessmentQuestion(
                id="CI-2", pillar=PillarType.COORDINATION_INTEGRITY,
                text="Is agent identity verified before counting votes? Can an attacker trivially create additional voting agents?"
            ),
            AssessmentQuestion(
                id="CI-3", pillar=PillarType.COORDINATION_INTEGRITY,
                text="Do quorum requirements account for potential adversaries? If you assume 10% of agents might be compromised, is your quorum threshold set accordingly?"
            ),
            AssessmentQuestion(
                id="CI-4", pillar=PillarType.COORDINATION_INTEGRITY,
                text="Are coordination protocols time-bounded appropriately? Can an attacker delay messages to manipulate outcomes?"
            ),
        ])

        # Continuous Monitoring
        self.questions.extend([
            AssessmentQuestion(
                id="CM-1", pillar=PillarType.CONTINUOUS_MONITORING,
                text="Do you monitor cognitive integrity metrics continuously? Metrics such as belief consistency, trust relationship stability, and delegation patterns should be tracked."
            ),
            AssessmentQuestion(
                id="CM-2", pillar=PillarType.CONTINUOUS_MONITORING,
                text="Can you detect drift from baseline behavior? Gradual manipulation that stays below individual-event thresholds may be visible as aggregate drift."
            ),
            AssessmentQuestion(
                id="CM-3", pillar=PillarType.CONTINUOUS_MONITORING,
                text="Do you have incident response procedures for cognitive attacks? When manipulation is detected, do your teams know how to contain, investigate, and remediate?"
            ),
            AssessmentQuestion(
                id="CM-4", pillar=PillarType.CONTINUOUS_MONITORING,
                text="Do you conduct regular adversarial testing? Red team exercises that specifically target cognitive attack surfaces reveal gaps that theoretical analysis misses."
            ),
        ])

    def set_score(self, question_id: str, score: int, notes: str = "") -> None:
        """Set score for a specific question.

        Args:
            question_id: The question ID (e.g., "TB-1")
            score: Score value 0-5
            notes: Optional assessor notes

        Raises:
            ValueError: If question_id not found or score out of range
        """
        if not 0 <= score <= 5:
            raise ValueError(f"Score must be 0-5, got {score}")

        for q in self.questions:
            if q.id == question_id:
                q.score = score
                q.notes = notes
                return
        raise ValueError(f"Question '{question_id}' not found")

    def get_pillar_questions(self, pillar: PillarType) -> list[AssessmentQuestion]:
        """Get all questions for a specific pillar.

        Args:
            pillar: The pillar to filter by

        Returns:
            List of questions for the specified pillar
        """
        return [q for q in self.questions if q.pillar == pillar]

    def assess_pillar(self, pillar: PillarType) -> PillarAssessment:
        """Assess a single pillar.

        Args:
            pillar: The pillar to assess

        Returns:
            PillarAssessment with normalized score and gaps
        """
        questions = self.get_pillar_questions(pillar)
        if not questions:
            return PillarAssessment(
                pillar=pillar, score=0.0, max_score=0.0, raw_score=0.0
            )

        weighted_score = sum(q.score * q.weight for q in questions)
        max_possible = sum(5.0 * q.weight for q in questions)
        normalized = weighted_score / max_possible if max_possible > 0 else 0.0

        gaps = [
            f"{q.id}: {q.text}" for q in questions if q.score < 3
        ]

        recommendations = []
        if normalized < 0.5:
            recommendations.append(f"Critical: {pillar.value} requires immediate attention")
        elif normalized < 0.75:
            recommendations.append(f"Improvement needed in {pillar.value}")

        return PillarAssessment(
            pillar=pillar,
            score=normalized,
            max_score=max_possible,
            raw_score=weighted_score,
            gaps=gaps,
            recommendations=recommendations,
        )

    def assess_all(self) -> dict[PillarType, PillarAssessment]:
        """Assess all five pillars.

        Returns:
            Dictionary mapping each pillar to its assessment
        """
        return {pillar: self.assess_pillar(pillar) for pillar in PillarType}

    def overall_score(self) -> float:
        """Calculate overall posture score (0.0-1.0).

        Returns:
            Average of all pillar scores
        """
        assessments = self.assess_all()
        scores = [a.score for a in assessments.values()]
        return sum(scores) / len(scores) if scores else 0.0

    def identify_gaps(self, threshold: float = 0.6) -> list[str]:
        """Identify pillars scoring below threshold.

        Args:
            threshold: Minimum acceptable pillar score (default 0.6)

        Returns:
            List of gap descriptions
        """
        assessments = self.assess_all()
        gaps = []
        for pillar, assessment in assessments.items():
            if assessment.score < threshold:
                gaps.append(
                    f"{pillar.value}: score {assessment.score:.1%} "
                    f"(below {threshold:.0%} threshold)"
                )
        return gaps

    def route_to_sections(self) -> dict[str, str]:
        """Route assessment results to relevant manuscript sections.

        Based on manuscript guidance:
        - Low trust mapping -> Section 03 (Human Checklist)
        - Low detection -> Section 04 (Agent Guidelines)
        - Low bounding -> Section 05 (Deployment)
        - Low consensus/monitoring -> Section 06 (Risk Assessment)
        - Anti-patterns identified -> Section 07 (Common Pitfalls)

        Returns:
            Dictionary mapping section numbers to reasons
        """
        assessments = self.assess_all()
        routes: dict[str, str] = {}

        if assessments[PillarType.TRUST_BOUNDARY].score < 0.6:
            routes["03"] = "Trust mapping scored low - systematic deployment guidance needed"
        if assessments[PillarType.BELIEF_PROVENANCE].score < 0.6:
            routes["04"] = "Detection scored low - cognitive tripwire implementations needed"
        if assessments[PillarType.DELEGATION_HYGIENE].score < 0.6:
            routes["05"] = "Bounding scored low - delegation parameter configuration needed"
        if (assessments[PillarType.COORDINATION_INTEGRITY].score < 0.6 or
            assessments[PillarType.CONTINUOUS_MONITORING].score < 0.6):
            routes["06"] = "Consensus/monitoring scored low - threat modeling methodology needed"

        # Always recommend pitfalls review
        routes["07"] = "Common pitfalls review recommended for all deployments"

        return routes


# =============================================================================
# Maturity Assessment
# =============================================================================


class MaturityDimension(Enum):
    """Six dimensions for maturity assessment."""
    TRUST_MAPPING = "trust_mapping"
    DETECTION = "detection"
    BOUNDING = "bounding"
    CONSENSUS = "consensus"
    MONITORING = "monitoring"
    RESPONSE = "response"


class MaturityLevel(Enum):
    """Organizational maturity levels."""
    REACTIVE = "reactive"          # Below 12
    DEVELOPING = "developing"      # 12-17
    MANAGED = "managed"            # 18-23
    PROACTIVE = "proactive"        # 24-30


@dataclass
class MaturityAssessment:
    """Complete maturity assessment result.

    Args:
        dimension_scores: Score per dimension (1-5 each)
        total_score: Sum of all dimensions (max 30)
        maturity_level: Determined maturity level
        interpretation: Text interpretation of the score
        priority_dimensions: Dimensions needing most attention
    """
    dimension_scores: dict[MaturityDimension, int]
    total_score: int
    maturity_level: MaturityLevel
    interpretation: str
    priority_dimensions: list[MaturityDimension] = field(default_factory=list)

    @staticmethod
    def dimension_question(dimension: MaturityDimension) -> str:
        """Get the assessment question for a dimension.

        Args:
            dimension: The dimension to get the question for

        Returns:
            Question text for the dimension
        """
        questions = {
            MaturityDimension.TRUST_MAPPING: "Are trust assumptions documented and reviewed?",
            MaturityDimension.DETECTION: "Could you detect belief manipulation in production?",
            MaturityDimension.BOUNDING: "Do delegation limits prevent trust amplification?",
            MaturityDimension.CONSENSUS: "Are collective decisions manipulation-resistant?",
            MaturityDimension.MONITORING: "Is cognitive integrity monitored continuously?",
            MaturityDimension.RESPONSE: "Do you have cognitive attack response procedures?",
        }
        return questions[dimension]


def compute_maturity(scores: dict[MaturityDimension, int]) -> MaturityAssessment:
    """Compute maturity assessment from dimension scores.

    Args:
        scores: Dictionary mapping each dimension to a 1-5 score

    Returns:
        Complete maturity assessment with level and interpretation

    Raises:
        ValueError: If any score is outside 1-5 or dimensions are missing
    """
    # Validate all dimensions present
    for dim in MaturityDimension:
        if dim not in scores:
            raise ValueError(f"Missing dimension: {dim.value}")
        if not 1 <= scores[dim] <= 5:
            raise ValueError(f"Score for {dim.value} must be 1-5, got {scores[dim]}")

    total = sum(scores.values())

    if total >= 24:
        level = MaturityLevel.PROACTIVE
        interpretation = (
            "Strong posture. Maintain vigilance and pursue continuous improvement. "
            "Share your practices with the community."
        )
    elif total >= 18:
        level = MaturityLevel.MANAGED
        interpretation = (
            "Solid foundation with identified gaps. "
            "Prioritize addressing the lowest-scoring dimensions."
        )
    elif total >= 12:
        level = MaturityLevel.DEVELOPING
        interpretation = (
            "Basic awareness established. Systematic improvement program needed; "
            "consider external assessment."
        )
    else:
        level = MaturityLevel.REACTIVE
        interpretation = (
            "Significant risk exposure. Begin immediately with trust mapping "
            "and basic monitoring."
        )

    # Identify priority dimensions (scoring 2 or below)
    priority = [dim for dim, score in scores.items() if score <= 2]

    return MaturityAssessment(
        dimension_scores=scores,
        total_score=total,
        maturity_level=level,
        interpretation=interpretation,
        priority_dimensions=priority,
    )


# =============================================================================
# Posture Report
# =============================================================================


@dataclass
class PostureReport:
    """Complete posture assessment report.

    Combines Five Pillars assessment, maturity assessment,
    and capability validation into a single report.

    Args:
        pillar_assessments: Results from Five Pillars assessment
        maturity: Results from maturity assessment
        overall_score: Combined overall score (0.0-1.0)
        posture_level: Determined posture level
        gaps: All identified gaps
        recommended_sections: Manuscript sections to review
        capabilities_present: Operational capabilities present
        capabilities_missing: Operational capabilities missing
    """
    pillar_assessments: dict[PillarType, PillarAssessment]
    maturity: MaturityAssessment
    overall_score: float
    posture_level: PostureLevel
    gaps: list[str] = field(default_factory=list)
    recommended_sections: dict[str, str] = field(default_factory=dict)
    capabilities_present: list[str] = field(default_factory=list)
    capabilities_missing: list[str] = field(default_factory=list)


def determine_posture_level(score: float) -> PostureLevel:
    """Determine posture level from overall score.

    Args:
        score: Overall score (0.0-1.0)

    Returns:
        PostureLevel corresponding to the score
    """
    if score >= 0.9:
        return PostureLevel.MAXIMUM
    elif score >= 0.75:
        return PostureLevel.ELEVATED
    elif score >= 0.5:
        return PostureLevel.STANDARD
    else:
        return PostureLevel.MINIMAL


# =============================================================================
# Capability Checker
# =============================================================================


class CapabilityName(Enum):
    """Operational capabilities from manuscript."""
    STIGMERGIC_AUDIT = "stigmergic_audit_trail"
    QUORUM_GATES = "quorum_gates"
    COLLECTIVE_ANOMALY = "collective_anomaly_detection"
    SYBIL_RESISTANCE = "sybil_resistance"
    BELIEF_PROVENANCE = "belief_provenance_tracking"
    RESILIENCE_TESTING = "resilience_testing"
    INCIDENT_PLAYBOOKS = "incident_response_playbooks"


@dataclass
class CapabilityDefinition:
    """Definition of an operational capability.

    Args:
        name: Capability identifier
        purpose: What the capability does
        guidance: How to implement it
        present: Whether the capability is present
    """
    name: CapabilityName
    purpose: str
    guidance: str
    present: bool = False


class CapabilityChecker:
    """Validates operational capabilities against manuscript requirements.

    Checks the 7 operational capabilities from Section 02.
    """

    def __init__(self) -> None:
        """Initialize with default capability definitions."""
        self.capabilities: list[CapabilityDefinition] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load the 7 operational capabilities from manuscript."""
        self.capabilities = [
            CapabilityDefinition(
                name=CapabilityName.STIGMERGIC_AUDIT,
                purpose="Track modifications to shared state with attribution",
                guidance="Log all writes to shared caches, queues, and files with agent ID, timestamp, and operation context",
            ),
            CapabilityDefinition(
                name=CapabilityName.QUORUM_GATES,
                purpose="Require multi-agent agreement for consequential actions",
                guidance="Implement voting or approval workflows for high-risk operations; configure thresholds based on risk profile",
            ),
            CapabilityDefinition(
                name=CapabilityName.COLLECTIVE_ANOMALY,
                purpose="Identify coordinated attacks or emergent pathology",
                guidance="Monitor aggregate metrics (success rates, latencies, output distributions) alongside individual agent health",
            ),
            CapabilityDefinition(
                name=CapabilityName.SYBIL_RESISTANCE,
                purpose="Prevent fake agent injection",
                guidance="Bind agent identity to verified credentials; rate-limit new agent integration; require human approval for capability grants",
            ),
            CapabilityDefinition(
                name=CapabilityName.BELIEF_PROVENANCE,
                purpose="Maintain information origin chains",
                guidance="Structured message formats with provenance metadata; trust scores that decay through hops",
            ),
            CapabilityDefinition(
                name=CapabilityName.RESILIENCE_TESTING,
                purpose="Validate recovery from adversarial conditions",
                guidance="Regular injection of faulty or adversarial agents in staging; chaos engineering for cognitive systems",
            ),
            CapabilityDefinition(
                name=CapabilityName.INCIDENT_PLAYBOOKS,
                purpose="Enable rapid response to detected attacks",
                guidance="Documented procedures for cognitive attack containment, investigation, and remediation",
            ),
        ]

    def set_capability(self, name: CapabilityName, present: bool) -> None:
        """Set whether a capability is present.

        Args:
            name: Capability to set
            present: Whether it is present

        Raises:
            ValueError: If capability name not found
        """
        for cap in self.capabilities:
            if cap.name == name:
                cap.present = present
                return
        raise ValueError(f"Capability '{name}' not found")

    def get_present(self) -> list[CapabilityDefinition]:
        """Get all present capabilities.

        Returns:
            List of capabilities marked as present
        """
        return [c for c in self.capabilities if c.present]

    def get_missing(self) -> list[CapabilityDefinition]:
        """Get all missing capabilities.

        Returns:
            List of capabilities not yet present
        """
        return [c for c in self.capabilities if not c.present]

    def completeness_score(self) -> float:
        """Calculate capability completeness score.

        Returns:
            Fraction of capabilities present (0.0-1.0)
        """
        if not self.capabilities:
            return 0.0
        return len(self.get_present()) / len(self.capabilities)

    def evaluate(self) -> AssessmentResult:
        """Evaluate capabilities against requirements.

        Returns:
            AssessmentResult with capability evaluation
        """
        score = self.completeness_score()
        missing = self.get_missing()

        if score >= 0.95:
            risk_level = RiskLevel.LOW
        elif score >= 0.7:
            risk_level = RiskLevel.MEDIUM
        elif score >= 0.4:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        findings = [
            f"Missing: {cap.name.value} - {cap.purpose}" for cap in missing
        ]
        recommendations = [
            f"Implement {cap.name.value}: {cap.guidance}" for cap in missing
        ]

        return AssessmentResult(
            passed=score >= 0.7,
            score=score,
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations,
        )


# =============================================================================
# Full Posture Assessment Orchestrator
# =============================================================================


def generate_posture_report(
    pillars: FivePillarsAssessment,
    maturity_scores: dict[MaturityDimension, int],
    capability_checker: CapabilityChecker,
) -> PostureReport:
    """Generate a complete posture assessment report.

    Combines all three assessment components into a unified report
    with overall scoring and section routing.

    Args:
        pillars: Completed Five Pillars assessment
        maturity_scores: Scores for each maturity dimension (1-5)
        capability_checker: Populated capability checker

    Returns:
        Complete PostureReport combining all assessments
    """
    pillar_assessments = pillars.assess_all()
    maturity = compute_maturity(maturity_scores)

    # Overall score is weighted average: 50% pillars, 30% maturity, 20% capabilities
    pillar_score = pillars.overall_score()
    maturity_score = maturity.total_score / 30.0
    capability_score = capability_checker.completeness_score()
    overall = 0.5 * pillar_score + 0.3 * maturity_score + 0.2 * capability_score

    posture_level = determine_posture_level(overall)

    # Collect all gaps
    gaps = pillars.identify_gaps()
    for dim in maturity.priority_dimensions:
        gaps.append(f"Maturity: {dim.value} needs improvement")
    for cap in capability_checker.get_missing():
        gaps.append(f"Capability: {cap.name.value} not implemented")

    return PostureReport(
        pillar_assessments=pillar_assessments,
        maturity=maturity,
        overall_score=overall,
        posture_level=posture_level,
        gaps=gaps,
        recommended_sections=pillars.route_to_sections(),
        capabilities_present=[c.name.value for c in capability_checker.get_present()],
        capabilities_missing=[c.name.value for c in capability_checker.get_missing()],
    )


__all__ = [
    "PillarType",
    "AssessmentQuestion",
    "PillarAssessment",
    "FivePillarsAssessment",
    "MaturityDimension",
    "MaturityLevel",
    "MaturityAssessment",
    "compute_maturity",
    "PostureReport",
    "determine_posture_level",
    "CapabilityName",
    "CapabilityDefinition",
    "CapabilityChecker",
    "generate_posture_report",
]
