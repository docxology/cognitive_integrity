"""
from __future__ import annotations

Common Pitfall Catalog for Cognitive Security Deployments.

Implements Section 07 of the Practical Implementation Guide:
Eight documented anti-patterns with detection, assessment, and remediation.
"""

from dataclasses import dataclass, field
from enum import Enum

from . import RiskLevel, AssessmentResult


class PitfallID(Enum):
    """Identifiers for the eight common pitfalls.

    Each value corresponds to the manuscript's PIT-N numbering scheme
    from Section 07.
    """

    IMPLICIT_TRUST = "PIT-1"
    SECURITY_AFTERTHOUGHT = "PIT-2"
    UNCALIBRATED_THRESHOLDS = "PIT-3"
    INDIVIDUAL_ONLY = "PIT-4"
    STATIC_TRIPWIRES = "PIT-5"
    IGNORING_DRIFT = "PIT-6"
    INSUFFICIENT_LOGGING = "PIT-7"
    SINGLE_ORCHESTRATOR = "PIT-8"


class PitfallCategory(Enum):
    """Pitfall categories from Section 07.

    Categories group pitfalls by the nature of the anti-pattern:
    security design flaws, operational oversights, or architectural
    design shortcomings.
    """

    SECURITY = "security"
    OPERATIONAL = "operational"
    DESIGN = "design"


@dataclass
class PitfallIndicator:
    """An indicator that a pitfall may be present.

    Indicators are observable signs in a deployment that suggest
    a particular anti-pattern is in effect. Each pitfall has
    multiple indicators; any one being present is sufficient
    to flag the pitfall.

    Args:
        description: What to look for
        present: Whether this indicator was observed
        notes: Assessment notes
    """

    description: str
    present: bool = False
    notes: str = ""


@dataclass
class PitfallMitigation:
    """A mitigation action for a pitfall.

    Mitigations are concrete steps that address the anti-pattern.
    Each pitfall has multiple mitigations ordered from most
    impactful to supplementary.

    Args:
        description: What to do
        implemented: Whether this mitigation is in place
        notes: Implementation notes
    """

    description: str
    implemented: bool = False
    notes: str = ""


@dataclass
class PitfallDefinition:
    """Complete definition of a deployment pitfall.

    Encapsulates the full specification of an anti-pattern from
    the manuscript: identity, classification, indicators for
    detection, and mitigations for remediation.

    Args:
        id: Pitfall identifier
        name: Short name
        pattern: Description of the anti-pattern
        category: Pitfall category (security/operational/design)
        severity: Severity rating (1-5)
        indicators: Signs this pitfall is present
        mitigations: Actions to address the pitfall
        manuscript_reference: Where in manuscript this is discussed
    """

    id: PitfallID
    name: str
    pattern: str
    category: PitfallCategory
    severity: int
    indicators: list[PitfallIndicator] = field(default_factory=list)
    mitigations: list[PitfallMitigation] = field(default_factory=list)
    manuscript_reference: str = ""


class PitfallCatalog:
    """Registry of all 8 documented pitfalls with detection logic.

    Provides lookup, filtering, and assessment capabilities
    for the pitfall catalog from Section 07. The catalog is
    initialized with the complete set of pitfall definitions
    from the manuscript.
    """

    def __init__(self) -> None:
        """Initialize with all 8 pitfalls from manuscript."""
        self.pitfalls: list[PitfallDefinition] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load the 8 pitfall definitions from manuscript.

        Each definition includes the anti-pattern description,
        category, severity, indicators, mitigations, and
        manuscript cross-reference.
        """
        self.pitfalls = [
            PitfallDefinition(
                id=PitfallID.IMPLICIT_TRUST,
                name="Implicit Trust",
                pattern=(
                    "Treating all inter-agent communication as trusted by default"
                ),
                category=PitfallCategory.SECURITY,
                severity=5,
                indicators=[
                    PitfallIndicator(
                        "No source verification on agent messages"
                    ),
                    PitfallIndicator(
                        "All agents have equal authority regardless of role"
                    ),
                    PitfallIndicator(
                        "Delegation without bounds or decay"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Implement explicit trust scoring on inter-agent channels"
                    ),
                    PitfallMitigation(
                        "Require minimum trust thresholds for consequential actions"
                    ),
                    PitfallMitigation(
                        "Apply delegation decay (delta < 1 per hop)"
                    ),
                    PitfallMitigation(
                        "Verify source on every inter-agent message"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 1",
            ),
            PitfallDefinition(
                id=PitfallID.SECURITY_AFTERTHOUGHT,
                name="Security as Afterthought",
                pattern=(
                    "Adding cognitive security after architecture is finalized"
                ),
                category=PitfallCategory.SECURITY,
                severity=5,
                indicators=[
                    PitfallIndicator(
                        "Security checks only at external interfaces"
                    ),
                    PitfallIndicator(
                        "Core agent logic has no security awareness"
                    ),
                    PitfallIndicator(
                        "Belief provenance untracked"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Design cognitive security into architecture from the start"
                    ),
                    PitfallMitigation(
                        "Embed trust checks in delegation logic"
                    ),
                    PitfallMitigation(
                        "Build provenance tracking into belief management"
                    ),
                    PitfallMitigation(
                        "Include security constraints in agent system prompts"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 2",
            ),
            PitfallDefinition(
                id=PitfallID.UNCALIBRATED_THRESHOLDS,
                name="Uncalibrated Thresholds",
                pattern=(
                    "Setting security thresholds without understanding tradeoffs"
                ),
                category=PitfallCategory.OPERATIONAL,
                severity=4,
                indicators=[
                    PitfallIndicator(
                        "Thresholds copied from examples without adjustment"
                    ),
                    PitfallIndicator(
                        "Same thresholds for all contexts"
                    ),
                    PitfallIndicator(
                        "No testing against representative attacks"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Assess risk profile before configuring (see Section 6)"
                    ),
                    PitfallMitigation(
                        "Test thresholds against representative attack samples"
                    ),
                    PitfallMitigation(
                        "Monitor false positive/negative rates in production"
                    ),
                    PitfallMitigation(
                        "Adjust based on operational feedback"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 3",
            ),
            PitfallDefinition(
                id=PitfallID.INDIVIDUAL_ONLY,
                name="Individual-Only Security",
                pattern=(
                    "Focusing on single-agent security while ignoring "
                    "multi-agent attack surfaces"
                ),
                category=PitfallCategory.SECURITY,
                severity=4,
                indicators=[
                    PitfallIndicator(
                        "No consensus mechanism for critical decisions"
                    ),
                    PitfallIndicator(
                        "Agent count changes without verification"
                    ),
                    PitfallIndicator(
                        "No Sybil resistance"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Implement Byzantine consensus for critical "
                        "collective decisions"
                    ),
                    PitfallMitigation(
                        "Require agent authentication before vote counting"
                    ),
                    PitfallMitigation(
                        "Monitor for unusual coordination patterns"
                    ),
                    PitfallMitigation(
                        "Apply quorum requirements assuming adversarial presence"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 4",
            ),
            PitfallDefinition(
                id=PitfallID.STATIC_TRIPWIRES,
                name="Static Tripwires",
                pattern=(
                    "Deploying canary tripwires once without rotation"
                ),
                category=PitfallCategory.DESIGN,
                severity=4,
                indicators=[
                    PitfallIndicator(
                        "Same canary values since deployment"
                    ),
                    PitfallIndicator(
                        "No rotation schedule"
                    ),
                    PitfallIndicator(
                        "Predictable canary locations"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Implement automated canary rotation"
                    ),
                    PitfallMitigation(
                        "Vary placement across agents and belief categories"
                    ),
                    PitfallMitigation(
                        "Monitor canary check patterns, not just modifications"
                    ),
                    PitfallMitigation(
                        "Include non-obvious canaries"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 5",
            ),
            PitfallDefinition(
                id=PitfallID.IGNORING_DRIFT,
                name="Ignoring Progressive Drift",
                pattern=(
                    "Only alerting on large, sudden belief changes"
                ),
                category=PitfallCategory.OPERATIONAL,
                severity=3,
                indicators=[
                    PitfallIndicator(
                        "High threshold for drift alerts"
                    ),
                    PitfallIndicator(
                        "No long-term drift tracking"
                    ),
                    PitfallIndicator(
                        "Static baseline"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Use sliding window drift detection"
                    ),
                    PitfallMitigation(
                        "Track cumulative drift, not just per-update delta"
                    ),
                    PitfallMitigation(
                        "Periodic baseline comparison"
                    ),
                    PitfallMitigation(
                        "Alert on trend as well as absolute magnitude"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 6",
            ),
            PitfallDefinition(
                id=PitfallID.INSUFFICIENT_LOGGING,
                name="Insufficient Logging",
                pattern=(
                    "Retaining insufficient information for "
                    "post-incident analysis"
                ),
                category=PitfallCategory.OPERATIONAL,
                severity=3,
                indicators=[
                    PitfallIndicator(
                        "Only final decisions logged"
                    ),
                    PitfallIndicator(
                        "No belief state history"
                    ),
                    PitfallIndicator(
                        "Inter-agent messages disposed after processing"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Log all belief updates with provenance tags"
                    ),
                    PitfallMitigation(
                        "Retain inter-agent message history"
                    ),
                    PitfallMitigation(
                        "Periodic cognitive state snapshots"
                    ),
                    PitfallMitigation(
                        "Structured logging for causal analysis"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 7",
            ),
            PitfallDefinition(
                id=PitfallID.SINGLE_ORCHESTRATOR,
                name="Single-Orchestrator Reliance",
                pattern=(
                    "Relying entirely on orchestrator integrity without backup"
                ),
                category=PitfallCategory.DESIGN,
                severity=2,
                indicators=[
                    PitfallIndicator(
                        "Single orchestrator for entire system"
                    ),
                    PitfallIndicator(
                        "No orchestrator monitoring"
                    ),
                    PitfallIndicator(
                        "Workers unconditionally trust orchestrator"
                    ),
                ],
                mitigations=[
                    PitfallMitigation(
                        "Consider multi-orchestrator architectures "
                        "for critical decisions"
                    ),
                    PitfallMitigation(
                        "Monitor orchestrator behavior with same rigor as agents"
                    ),
                    PitfallMitigation(
                        "Workers verify orchestrator identity on critical commands"
                    ),
                    PitfallMitigation(
                        "Implement orchestrator-specific tripwires"
                    ),
                ],
                manuscript_reference="Section 07, Pitfall 8",
            ),
        ]

    def get_by_id(self, pitfall_id: PitfallID) -> PitfallDefinition:
        """Get a pitfall definition by ID.

        Args:
            pitfall_id: The pitfall to retrieve

        Returns:
            PitfallDefinition for the specified pitfall

        Raises:
            ValueError: If pitfall not found
        """
        for p in self.pitfalls:
            if p.id == pitfall_id:
                return p
        raise ValueError(f"Pitfall '{pitfall_id}' not found")

    def get_by_category(
        self, category: PitfallCategory
    ) -> list[PitfallDefinition]:
        """Get all pitfalls in a category.

        Args:
            category: Category to filter by

        Returns:
            List of pitfalls in that category
        """
        return [p for p in self.pitfalls if p.category == category]

    def get_by_severity(
        self, min_severity: int = 1
    ) -> list[PitfallDefinition]:
        """Get pitfalls at or above a severity level.

        Args:
            min_severity: Minimum severity (1-5)

        Returns:
            List of pitfalls at or above the threshold, sorted by
            severity descending
        """
        filtered = [p for p in self.pitfalls if p.severity >= min_severity]
        return sorted(filtered, key=lambda p: p.severity, reverse=True)

    def get_critical(self) -> list[PitfallDefinition]:
        """Get all critical (severity 5) pitfalls.

        Returns:
            List of severity-5 pitfalls
        """
        return self.get_by_severity(5)


class PitfallDetector:
    """Analyzes deployment descriptions against known pitfall patterns.

    Takes a set of deployment characteristics and checks for
    indicators of each pitfall. The detector operates on the
    catalog's pitfall definitions, setting indicator status
    based on observed characteristics.
    """

    def __init__(self, catalog: PitfallCatalog | None = None) -> None:
        """Initialize detector with pitfall catalog.

        Args:
            catalog: Pitfall catalog to check against (default: new catalog)
        """
        self.catalog = catalog or PitfallCatalog()

    def check_indicators(
        self,
        pitfall_id: PitfallID,
        indicator_status: dict[int, bool],
    ) -> PitfallDefinition:
        """Check specific indicators for a pitfall.

        Sets the ``present`` flag on each referenced indicator
        within the catalog's pitfall definition. Indicator indices
        are zero-based and must be within range.

        Args:
            pitfall_id: Which pitfall to check
            indicator_status: Map of indicator index to observed status

        Returns:
            Updated PitfallDefinition with indicator status set

        Raises:
            ValueError: If indicator index out of range
        """
        pitfall = self.catalog.get_by_id(pitfall_id)

        for idx, present in indicator_status.items():
            if idx < 0 or idx >= len(pitfall.indicators):
                raise ValueError(
                    f"Indicator index {idx} out of range for "
                    f"{pitfall_id.value} "
                    f"(has {len(pitfall.indicators)} indicators)"
                )
            pitfall.indicators[idx].present = present

        return pitfall

    def detect_pitfall(self, pitfall: PitfallDefinition) -> bool:
        """Determine if a pitfall is present based on indicators.

        A pitfall is considered present if ANY indicator is observed.
        This follows the manuscript's conservative detection approach:
        a single indicator is sufficient grounds for flagging.

        Args:
            pitfall: Pitfall with indicator status set

        Returns:
            True if any indicator is present
        """
        return any(ind.present for ind in pitfall.indicators)

    def scan_all(self) -> list[PitfallDefinition]:
        """Return all pitfalls that have indicators present.

        Scans every pitfall in the catalog and returns those
        with at least one indicator flagged as present.

        Returns:
            List of detected pitfalls (with at least one indicator present)
        """
        return [
            p for p in self.catalog.pitfalls if self.detect_pitfall(p)
        ]


@dataclass
class PitfallChecklistEntry:
    """A single entry in the pitfall assessment checklist.

    Tracks whether a pitfall has been assessed, whether it was
    detected during assessment, and whether mitigations have
    been applied.

    Args:
        pitfall_id: Which pitfall
        pitfall_name: Human-readable name
        assessed: Whether this pitfall has been assessed
        detected: Whether this pitfall was detected
        mitigated: Whether mitigations are in place
    """

    pitfall_id: PitfallID
    pitfall_name: str
    assessed: bool = False
    detected: bool = False
    mitigated: bool = False


class PitfallChecklist:
    """Assessment checklist tracking pitfall review status.

    Matches the Summary Checklist table in Section 07 of the
    manuscript. Provides workflow methods for assessing each
    pitfall, tracking mitigation status, and evaluating overall
    deployment readiness.
    """

    def __init__(self, catalog: PitfallCatalog | None = None) -> None:
        """Initialize from catalog.

        Creates one checklist entry per pitfall in the catalog,
        all starting as unassessed.

        Args:
            catalog: Pitfall catalog (default: new catalog)
        """
        self.catalog = catalog or PitfallCatalog()
        self.entries: list[PitfallChecklistEntry] = [
            PitfallChecklistEntry(
                pitfall_id=p.id,
                pitfall_name=p.name,
            )
            for p in self.catalog.pitfalls
        ]

    def assess(
        self,
        pitfall_id: PitfallID,
        detected: bool,
        mitigated: bool = False,
    ) -> None:
        """Record assessment result for a pitfall.

        Marks the pitfall as assessed and records whether it was
        detected and whether mitigations are in place.

        Args:
            pitfall_id: Which pitfall was assessed
            detected: Whether the pitfall was detected
            mitigated: Whether mitigations are in place

        Raises:
            ValueError: If pitfall_id not found in checklist
        """
        for entry in self.entries:
            if entry.pitfall_id == pitfall_id:
                entry.assessed = True
                entry.detected = detected
                entry.mitigated = mitigated
                return
        raise ValueError(f"Pitfall '{pitfall_id}' not in checklist")

    def get_unassessed(self) -> list[PitfallChecklistEntry]:
        """Get pitfalls not yet assessed.

        Returns:
            List of unassessed entries
        """
        return [e for e in self.entries if not e.assessed]

    def get_detected_unmitigated(self) -> list[PitfallChecklistEntry]:
        """Get pitfalls detected but not yet mitigated.

        These represent active risks that require remediation.

        Returns:
            List of detected-but-unmitigated entries
        """
        return [
            e for e in self.entries if e.detected and not e.mitigated
        ]

    def all_assessed(self) -> bool:
        """Check if all pitfalls have been assessed.

        Returns:
            True if all entries are assessed
        """
        return all(e.assessed for e in self.entries)

    def all_mitigated(self) -> bool:
        """Check if all detected pitfalls are mitigated.

        Returns:
            True if no detected-but-unmitigated entries remain
        """
        return len(self.get_detected_unmitigated()) == 0

    def evaluate(self) -> AssessmentResult:
        """Evaluate the pitfall assessment status.

        Produces an AssessmentResult that reflects:
        - Score: fraction of pitfalls that have been assessed
        - Risk level: based on the highest-severity unmitigated pitfall
        - Findings: detected-unmitigated and unassessed pitfalls
        - Recommendations: unimplemented mitigations for detected pitfalls
        - Passed: True only if all assessed AND none detected-unmitigated

        Returns:
            AssessmentResult with scoring and findings
        """
        if not self.entries:
            return AssessmentResult(
                passed=True, score=1.0, risk_level=RiskLevel.LOW
            )

        assessed_count = sum(1 for e in self.entries if e.assessed)
        assessment_score = assessed_count / len(self.entries)

        detected_unmitigated = self.get_detected_unmitigated()

        # Risk based on the highest-severity unmitigated pitfall
        max_unmitigated_severity = 0
        for entry in detected_unmitigated:
            pitfall = self.catalog.get_by_id(entry.pitfall_id)
            max_unmitigated_severity = max(
                max_unmitigated_severity, pitfall.severity
            )

        if max_unmitigated_severity >= 5:
            risk_level = RiskLevel.CRITICAL
        elif max_unmitigated_severity >= 4:
            risk_level = RiskLevel.HIGH
        elif max_unmitigated_severity >= 3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        findings = [
            f"Detected: {e.pitfall_name} (unmitigated)"
            for e in detected_unmitigated
        ]
        unassessed = self.get_unassessed()
        if unassessed:
            findings.extend(
                [f"Not assessed: {e.pitfall_name}" for e in unassessed]
            )

        recommendations: list[str] = []
        for entry in detected_unmitigated:
            pitfall = self.catalog.get_by_id(entry.pitfall_id)
            for mit in pitfall.mitigations:
                if not mit.implemented:
                    recommendations.append(
                        f"{pitfall.name}: {mit.description}"
                    )

        return AssessmentResult(
            passed=(
                len(detected_unmitigated) == 0 and self.all_assessed()
            ),
            score=assessment_score,
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations,
        )


# =============================================================================
# Remediation Planning
# =============================================================================


@dataclass
class RemediationStep:
    """A single remediation step.

    Represents one concrete action to address a detected pitfall.
    Steps are generated from unimplemented mitigations and ordered
    by severity priority.

    Args:
        pitfall_id: Which pitfall this remediates
        action: Description of the remediation action
        priority: Priority level (1=highest)
        completed: Whether this step is done
    """

    pitfall_id: PitfallID
    action: str
    priority: int
    completed: bool = False


@dataclass
class RemediationPlan:
    """Complete remediation plan for detected pitfalls.

    Aggregates all remediation steps into a single plan with
    progress tracking. Steps are ordered by priority (derived
    from pitfall severity).

    Args:
        steps: Ordered remediation steps
        total_pitfalls: Number of pitfalls being addressed
        critical_count: Number of critical severity pitfalls
    """

    steps: list[RemediationStep] = field(default_factory=list)
    total_pitfalls: int = 0
    critical_count: int = 0

    def completed_steps(self) -> int:
        """Count completed remediation steps.

        Returns:
            Number of steps marked as completed
        """
        return sum(1 for s in self.steps if s.completed)

    def progress(self) -> float:
        """Calculate remediation progress as a fraction.

        Returns:
            Float between 0.0 and 1.0. Returns 1.0 for empty plans
            (nothing to remediate).
        """
        if not self.steps:
            return 1.0
        return self.completed_steps() / len(self.steps)


def generate_remediation_plan(
    checklist: PitfallChecklist,
) -> RemediationPlan:
    """Generate a prioritized remediation plan from assessment results.

    Steps are ordered by pitfall severity (highest first), then
    by mitigation order within each pitfall. Only detected-but-
    unmitigated pitfalls are included.

    Args:
        checklist: Completed pitfall assessment checklist

    Returns:
        RemediationPlan with prioritized steps
    """
    detected = checklist.get_detected_unmitigated()

    # Resolve pitfall definitions and sort by severity (highest first)
    pitfall_defs: list[PitfallDefinition] = []
    for entry in detected:
        pitfall = checklist.catalog.get_by_id(entry.pitfall_id)
        pitfall_defs.append(pitfall)
    pitfall_defs.sort(key=lambda p: p.severity, reverse=True)

    steps: list[RemediationStep] = []
    priority = 1
    critical_count = 0

    for pitfall in pitfall_defs:
        if pitfall.severity >= 5:
            critical_count += 1
        for mitigation in pitfall.mitigations:
            if not mitigation.implemented:
                steps.append(
                    RemediationStep(
                        pitfall_id=pitfall.id,
                        action=mitigation.description,
                        priority=priority,
                    )
                )
                priority += 1

    return RemediationPlan(
        steps=steps,
        total_pitfalls=len(detected),
        critical_count=critical_count,
    )


__all__ = [
    "PitfallID",
    "PitfallCategory",
    "PitfallIndicator",
    "PitfallMitigation",
    "PitfallDefinition",
    "PitfallCatalog",
    "PitfallDetector",
    "PitfallChecklistEntry",
    "PitfallChecklist",
    "RemediationStep",
    "RemediationPlan",
    "generate_remediation_plan",
]
