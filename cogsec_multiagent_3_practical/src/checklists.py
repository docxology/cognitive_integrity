"""
from __future__ import annotations

Human-Actionable Checklists for Cognitive Security.

Implements Section 03 of the Practical Implementation Guide:
Pre-deployment, operational, and incident response checklists
with configuration reference validation.

This module provides three checklist types aligned to the manuscript:

1. **PreDeploymentChecklist** - 4 categories x 4 items = 16 items
   covering architecture review, defense configuration, monitoring
   setup, and incident response preparation.

2. **OperationalChecklist** - Daily (4 items) and weekly (4 items)
   operational security tasks with reset cycles.

3. **IncidentResponseChecklist** - 4 time-phased sections x 4 items
   = 16 items covering immediate through post-incident response.

Additionally, **ConfigurationReference** validates trust calculus
parameters, firewall thresholds, and tripwire configurations against
manuscript-specified recommended values and ranges.
"""

from dataclasses import dataclass
from enum import Enum

from . import AssessmentResult, ChecklistItem, RiskLevel

# =============================================================================
# Enums
# =============================================================================


class ChecklistPhase(Enum):
    """Top-level checklist phases.

    Maps to the three major sections of manuscript Section 03:
    pre-deployment preparation, ongoing operations, and incident response.
    """

    PRE_DEPLOYMENT = "pre_deployment"
    OPERATIONAL = "operational"
    INCIDENT_RESPONSE = "incident_response"


class ChecklistCategory(Enum):
    """Pre-deployment checklist categories.

    The four categories that must each be completed before
    a system can be considered deployment-ready.
    """

    ARCHITECTURE_REVIEW = "architecture_review"
    DEFENSE_CONFIGURATION = "defense_configuration"
    MONITORING_SETUP = "monitoring_setup"
    INCIDENT_RESPONSE_PREP = "incident_response_prep"


class OperationalFrequency(Enum):
    """Operational checklist frequencies.

    Operational tasks are divided into daily and weekly cadences
    to maintain ongoing cognitive security hygiene.
    """

    DAILY = "daily"
    WEEKLY = "weekly"


class IncidentSeverity(Enum):
    """Incident response time windows.

    Each severity level corresponds to a time window during
    incident response, from immediate triage through post-incident
    analysis.
    """

    IMMEDIATE = "immediate"  # First 15 minutes
    INVESTIGATION = "investigation"  # First hour
    RECOVERY = "recovery"  # Following hours
    POST_INCIDENT = "post_incident"  # Following days


# =============================================================================
# Enhanced Checklist Item
# =============================================================================


@dataclass
class EnhancedChecklistItem:
    """Extended checklist item with phase and evidence tracking.

    Wraps a base ChecklistItem with additional metadata for tracking
    which phase the item belongs to, who verified it, and what evidence
    supports its completion.

    Args:
        item: Base checklist item containing id, category, description.
        phase: Which top-level phase this item belongs to.
        category: Specific category within the phase (string form).
        evidence: Evidence of completion (e.g., screenshot path, log ref).
        verified_by: Who verified completion (e.g., operator name).
        verification_date: When verification occurred (ISO date string).
    """

    item: ChecklistItem
    phase: ChecklistPhase
    category: str = ""
    evidence: str = ""
    verified_by: str = ""
    verification_date: str = ""

    @property
    def completed(self) -> bool:
        """Whether the underlying item is completed.

        Returns:
            True if the base ChecklistItem is marked completed.
        """
        return self.item.completed

    @completed.setter
    def completed(self, value: bool) -> None:
        """Set completion on underlying item.

        Args:
            value: New completion status.
        """
        self.item.completed = value


# =============================================================================
# Pre-Deployment Checklist
# =============================================================================


class PreDeploymentChecklist:
    """Pre-deployment security checklist with 4 categories, 16 items.

    Implements the pre-deployment section of manuscript Section 03.
    Phase gating ensures all items in a category should be completed
    before moving to the next deployment phase.

    Categories:
        1. Architecture Review (4 items): trust boundaries, delegation
           limits, agent authentication, permission boundaries.
        2. Defense Configuration (4 items): cognitive firewall, belief
           sandboxing, tripwires, invariants.
        3. Monitoring Setup (4 items): drift detection, alert thresholds,
           logging, dashboards.
        4. Incident Response Prep (4 items): response procedures,
           quarantine capability, rollback mechanism, escalation path.
    """

    def __init__(self) -> None:
        """Initialize with default checklist items from manuscript."""
        self.items: list[EnhancedChecklistItem] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load the 16 default pre-deployment items from manuscript.

        Items are organized into 4 categories with 4 items each,
        matching the pre-deployment checklist in Section 03.
        """
        # Architecture Review
        arch_items = [
            (
                "arch-001",
                "Trust boundaries documented: All points where trust is "
                "assumed vs. verified are explicitly mapped",
            ),
            (
                "arch-002",
                "Delegation limits configured: Trust decay factor set "
                "(recommended: delta = 0.85-0.95)",
            ),
            (
                "arch-003",
                "Agent authentication implemented: All agents have verifiable identity",
            ),
            (
                "arch-004",
                "Permission boundaries defined: Each agent has explicit action restrictions",
            ),
        ]
        for id_, desc in arch_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(
                        id=id_,
                        category="architecture_review",
                        description=desc,
                    ),
                    phase=ChecklistPhase.PRE_DEPLOYMENT,
                    category=ChecklistCategory.ARCHITECTURE_REVIEW.value,
                )
            )

        # Defense Configuration
        defense_items = [
            (
                "def-001",
                "Cognitive firewall enabled: Input classification active for all external content",
            ),
            (
                "def-002",
                "Belief sandboxing configured: Unverified beliefs "
                "quarantined pending corroboration",
            ),
            (
                "def-003",
                "Tripwires planted: Canary beliefs placed to detect manipulation",
            ),
            (
                "def-004",
                "Invariants defined: Core security constraints specified and monitored",
            ),
        ]
        for id_, desc in defense_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(
                        id=id_,
                        category="defense_configuration",
                        description=desc,
                    ),
                    phase=ChecklistPhase.PRE_DEPLOYMENT,
                    category=ChecklistCategory.DEFENSE_CONFIGURATION.value,
                )
            )

        # Monitoring Setup
        monitor_items = [
            (
                "mon-001",
                "Drift detection active: Belief distribution monitoring enabled",
            ),
            (
                "mon-002",
                "Alert thresholds configured: Warning and critical levels set appropriately",
            ),
            (
                "mon-003",
                "Logging comprehensive: All agent decisions and belief updates recorded",
            ),
            (
                "mon-004",
                "Dashboards available: Real-time visibility into cognitive state",
            ),
        ]
        for id_, desc in monitor_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(
                        id=id_,
                        category="monitoring_setup",
                        description=desc,
                    ),
                    phase=ChecklistPhase.PRE_DEPLOYMENT,
                    category=ChecklistCategory.MONITORING_SETUP.value,
                )
            )

        # Incident Response Prepared
        ir_items = [
            (
                "ir-001",
                "Response procedures documented: Steps for cognitive attack response defined",
            ),
            (
                "ir-002",
                "Quarantine capability ready: Ability to isolate compromised agents",
            ),
            (
                "ir-003",
                "Rollback mechanism tested: Can restore to known-good cognitive state",
            ),
            (
                "ir-004",
                "Escalation path clear: Who to contact for cognitive security incidents",
            ),
        ]
        for id_, desc in ir_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(
                        id=id_,
                        category="incident_response_prep",
                        description=desc,
                    ),
                    phase=ChecklistPhase.PRE_DEPLOYMENT,
                    category=ChecklistCategory.INCIDENT_RESPONSE_PREP.value,
                )
            )

    def get_category_items(self, category: ChecklistCategory) -> list[EnhancedChecklistItem]:
        """Get all items for a specific category.

        Args:
            category: Category to filter by.

        Returns:
            List of enhanced checklist items in that category.
        """
        return [i for i in self.items if i.category == category.value]

    def complete_item(
        self,
        item_id: str,
        evidence: str = "",
        verified_by: str = "",
    ) -> None:
        """Mark an item as completed with optional evidence.

        Args:
            item_id: The checklist item ID (e.g., "arch-001").
            evidence: Evidence of completion (optional).
            verified_by: Who verified completion (optional).

        Raises:
            ValueError: If item_id is not found in the checklist.
        """
        for enhanced in self.items:
            if enhanced.item.id == item_id:
                enhanced.completed = True
                enhanced.evidence = evidence
                enhanced.verified_by = verified_by
                return
        raise ValueError(f"Item '{item_id}' not found")

    def category_complete(self, category: ChecklistCategory) -> bool:
        """Check if all required items in a category are complete.

        This is the phase gate check for a single category. All required
        items must be marked as completed for the gate to pass.

        Args:
            category: Category to check.

        Returns:
            True if all required items in the category are completed.
        """
        items = self.get_category_items(category)
        required = [i for i in items if i.item.required]
        return all(i.completed for i in required)

    def phase_gate_check(self) -> dict[ChecklistCategory, bool]:
        """Check completion status of each category (phase gate).

        Returns a dictionary mapping each ChecklistCategory to whether
        all its required items are complete. All categories must pass
        for the system to be deployment-ready.

        Returns:
            Dictionary mapping categories to completion status.
        """
        return {cat: self.category_complete(cat) for cat in ChecklistCategory}

    def is_ready(self) -> bool:
        """Check if pre-deployment is fully ready.

        All four categories must pass their phase gate checks for the
        system to be considered ready for deployment.

        Returns:
            True if all categories pass their phase gate.
        """
        return all(self.phase_gate_check().values())

    def evaluate(self) -> AssessmentResult:
        """Evaluate the pre-deployment checklist.

        Calculates a score based on the ratio of completed required items
        to total required items, determines risk level, and generates
        findings for incomplete items and recommendations for incomplete
        categories.

        Scoring thresholds:
            - >= 0.95: LOW risk
            - >= 0.80: MEDIUM risk (passes)
            - >= 0.60: HIGH risk (fails)
            - < 0.60: CRITICAL risk (fails)

        Returns:
            AssessmentResult with pass/fail, score, risk level, findings,
            and recommendations.
        """
        required = [i for i in self.items if i.item.required]
        completed = [i for i in required if i.completed]

        score = len(completed) / len(required) if required else 0.0

        if score >= 0.95:
            risk_level = RiskLevel.LOW
        elif score >= 0.8:
            risk_level = RiskLevel.MEDIUM
        elif score >= 0.6:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        findings = [f"Incomplete: {i.item.description}" for i in required if not i.completed]

        recommendations: list[str] = []
        gate = self.phase_gate_check()
        for cat, complete in gate.items():
            if not complete:
                recommendations.append(f"Complete all items in {cat.value}")

        return AssessmentResult(
            passed=score >= 0.8,
            score=score,
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations,
        )


# =============================================================================
# Operational Checklist
# =============================================================================


class OperationalChecklist:
    """Daily and weekly operational checklist.

    Implements the operational section of manuscript Section 03.
    Supports daily and weekly reset cycles for ongoing cognitive
    security hygiene.

    Daily items (4):
        1. Review drift alerts
        2. Verify tripwire integrity
        3. Check trust metrics
        4. Review failed consensus

    Weekly items (4):
        1. Analyze attack patterns
        2. Audit delegation chains
        3. Verify invariant compliance
        4. Update threat intel
    """

    def __init__(self) -> None:
        """Initialize with default operational items from manuscript."""
        self.items: list[EnhancedChecklistItem] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default daily and weekly items from manuscript."""
        # Daily items
        daily_items = [
            (
                "daily-001",
                "Review drift alerts: Check for unusual belief changes",
            ),
            (
                "daily-002",
                "Verify tripwire integrity: Confirm canary beliefs unchanged",
            ),
            (
                "daily-003",
                "Check trust metrics: Monitor for unexpected trust score changes",
            ),
            (
                "daily-004",
                "Review failed consensus: Investigate any Byzantine fault indications",
            ),
        ]
        for id_, desc in daily_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="daily", description=desc),
                    phase=ChecklistPhase.OPERATIONAL,
                    category=OperationalFrequency.DAILY.value,
                )
            )

        # Weekly items
        weekly_items = [
            (
                "weekly-001",
                "Analyze attack patterns: Review blocked injection attempts",
            ),
            (
                "weekly-002",
                "Audit delegation chains: Check for unusual delegation patterns",
            ),
            (
                "weekly-003",
                "Verify invariant compliance: Confirm no invariant violations",
            ),
            (
                "weekly-004",
                "Update threat intel: Incorporate new attack techniques into defenses",
            ),
        ]
        for id_, desc in weekly_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="weekly", description=desc),
                    phase=ChecklistPhase.OPERATIONAL,
                    category=OperationalFrequency.WEEKLY.value,
                )
            )

    def get_daily_items(self) -> list[EnhancedChecklistItem]:
        """Get all daily checklist items.

        Returns:
            List of items with daily frequency.
        """
        return [i for i in self.items if i.category == OperationalFrequency.DAILY.value]

    def get_weekly_items(self) -> list[EnhancedChecklistItem]:
        """Get all weekly checklist items.

        Returns:
            List of items with weekly frequency.
        """
        return [i for i in self.items if i.category == OperationalFrequency.WEEKLY.value]

    def complete_item(self, item_id: str) -> None:
        """Mark an operational item as completed.

        Args:
            item_id: Item ID to complete (e.g., "daily-001").

        Raises:
            ValueError: If item_id is not found in the checklist.
        """
        for enhanced in self.items:
            if enhanced.item.id == item_id:
                enhanced.completed = True
                return
        raise ValueError(f"Item '{item_id}' not found")

    def reset_daily(self) -> None:
        """Reset all daily items to incomplete for a new cycle.

        Called at the start of each day to begin a fresh daily
        checklist cycle. Does not affect weekly items.
        """
        for item in self.get_daily_items():
            item.completed = False

    def reset_weekly(self) -> None:
        """Reset all weekly items to incomplete for a new cycle.

        Called at the start of each week to begin a fresh weekly
        checklist cycle. Does not affect daily items.
        """
        for item in self.get_weekly_items():
            item.completed = False

    def daily_complete(self) -> bool:
        """Check if all daily items are complete.

        Returns:
            True if every daily item has been marked completed.
            False if the daily list is empty or any item is incomplete.
        """
        daily = self.get_daily_items()
        return all(i.completed for i in daily) if daily else False

    def weekly_complete(self) -> bool:
        """Check if all weekly items are complete.

        Returns:
            True if every weekly item has been marked completed.
            False if the weekly list is empty or any item is incomplete.
        """
        weekly = self.get_weekly_items()
        return all(i.completed for i in weekly) if weekly else False


# =============================================================================
# Incident Response Checklist
# =============================================================================


class IncidentResponseChecklist:
    """Incident response checklist with 4 time-phased sections.

    Implements the incident response section of manuscript Section 03.
    The checklist is activated when a cognitive security incident is
    suspected, then worked through in time-phased order.

    Time windows:
        1. Immediate (First 15 minutes): preserve evidence, assess scope,
           contain spread, notify stakeholders.
        2. Investigation (First hour): trace provenance, identify vector,
           assess impact, check persistence.
        3. Recovery (Following hours): restore state, strengthen defenses,
           verify integrity, document incident.
        4. Post-Incident (Following days): root cause analysis, defense
           improvements, team debrief, update procedures.
    """

    def __init__(self) -> None:
        """Initialize with default incident response items from manuscript."""
        self.items: list[EnhancedChecklistItem] = []
        self.activated: bool = False
        self.activation_reason: str = ""
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default incident response items from manuscript.

        Items are organized into 4 severity/time phases with 4 items each,
        matching the incident response checklist in Section 03.
        """
        # Immediate (First 15 Minutes)
        immediate_items = [
            (
                "imm-001",
                "Preserve evidence: Capture current cognitive state before any changes",
            ),
            (
                "imm-002",
                "Assess scope: Identify which agents and beliefs may be affected",
            ),
            (
                "imm-003",
                "Contain spread: Isolate affected agents from propagating beliefs",
            ),
            (
                "imm-004",
                "Notify stakeholders: Alert security team and relevant operators",
            ),
        ]
        for id_, desc in immediate_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="immediate", description=desc),
                    phase=ChecklistPhase.INCIDENT_RESPONSE,
                    category=IncidentSeverity.IMMEDIATE.value,
                )
            )

        # Investigation (First Hour)
        investigation_items = [
            (
                "inv-001",
                "Trace provenance: Follow belief origins to identify injection point",
            ),
            (
                "inv-002",
                "Identify attack vector: Determine how adversarial content entered",
            ),
            (
                "inv-003",
                "Assess impact: Evaluate what decisions were influenced",
            ),
            (
                "inv-004",
                "Check for persistence: Verify attack does not survive agent restart",
            ),
        ]
        for id_, desc in investigation_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="investigation", description=desc),
                    phase=ChecklistPhase.INCIDENT_RESPONSE,
                    category=IncidentSeverity.INVESTIGATION.value,
                )
            )

        # Recovery (Following Hours)
        recovery_items = [
            (
                "rec-001",
                "Restore clean state: Reset affected beliefs to verified baseline",
            ),
            (
                "rec-002",
                "Strengthen defenses: Update detection patterns based on attack",
            ),
            (
                "rec-003",
                "Verify integrity: Confirm cognitive state passes all tripwires",
            ),
            (
                "rec-004",
                "Document incident: Record details for future reference",
            ),
        ]
        for id_, desc in recovery_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="recovery", description=desc),
                    phase=ChecklistPhase.INCIDENT_RESPONSE,
                    category=IncidentSeverity.RECOVERY.value,
                )
            )

        # Post-Incident (Following Days)
        post_items = [
            (
                "post-001",
                "Root cause analysis: Complete investigation of attack chain",
            ),
            (
                "post-002",
                "Defense improvements: Implement countermeasures for attack type",
            ),
            (
                "post-003",
                "Team debrief: Share lessons learned with all operators",
            ),
            (
                "post-004",
                "Update procedures: Revise checklists based on incident learnings",
            ),
        ]
        for id_, desc in post_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="post_incident", description=desc),
                    phase=ChecklistPhase.INCIDENT_RESPONSE,
                    category=IncidentSeverity.POST_INCIDENT.value,
                )
            )

    def activate(self, reason: str) -> None:
        """Activate the incident response checklist.

        Should be called when a cognitive security incident is suspected.
        Records the activation reason for audit trail.

        Args:
            reason: Description of the suspected incident.
        """
        self.activated = True
        self.activation_reason = reason

    def get_phase_items(self, severity: IncidentSeverity) -> list[EnhancedChecklistItem]:
        """Get items for a specific incident phase.

        Args:
            severity: The incident phase/time window to filter by.

        Returns:
            List of enhanced checklist items for that phase.
        """
        return [i for i in self.items if i.category == severity.value]

    def complete_item(self, item_id: str, evidence: str = "") -> None:
        """Mark an incident response item as completed.

        Args:
            item_id: Item ID to complete (e.g., "imm-001").
            evidence: Evidence of completion (optional).

        Raises:
            ValueError: If item_id is not found in the checklist.
        """
        for enhanced in self.items:
            if enhanced.item.id == item_id:
                enhanced.completed = True
                enhanced.evidence = evidence
                return
        raise ValueError(f"Item '{item_id}' not found")

    def phase_complete(self, severity: IncidentSeverity) -> bool:
        """Check if all items in a phase are complete.

        Args:
            severity: Phase to check.

        Returns:
            True if all items in the phase are completed.
            False if the phase has no items or any are incomplete.
        """
        items = self.get_phase_items(severity)
        return all(i.completed for i in items) if items else False

    def get_timeline(self) -> list[dict[str, str | bool]]:
        """Get incident response timeline status.

        Returns a list of dictionaries summarizing each phase with
        its name, expected time window, and current completion status.
        Phases are returned in chronological order.

        Returns:
            List of phase status dicts with keys:
                - "phase": phase value string
                - "time_window": human-readable time expectation
                - "complete": boolean completion status
        """
        time_windows = {
            IncidentSeverity.IMMEDIATE: "First 15 minutes",
            IncidentSeverity.INVESTIGATION: "First hour",
            IncidentSeverity.RECOVERY: "Following hours",
            IncidentSeverity.POST_INCIDENT: "Following days",
        }
        return [
            {
                "phase": sev.value,
                "time_window": time_windows[sev],
                "complete": self.phase_complete(sev),
            }
            for sev in IncidentSeverity
        ]


# =============================================================================
# Configuration Reference
# =============================================================================


@dataclass
class TrustParameter:
    """A trust calculus parameter with recommended value and guidance.

    Represents one of the four trust calculus parameters (alpha, beta,
    gamma, delta) from the manuscript with its recommended value,
    valid range, and adjustment guidance.

    Args:
        name: Human-readable parameter name.
        symbol: Mathematical symbol (Greek letter).
        recommended: Recommended default value.
        range_min: Minimum valid value.
        range_max: Maximum valid value.
        adjustment_guidance: When and how to adjust this parameter.
    """

    name: str
    symbol: str
    recommended: float
    range_min: float
    range_max: float
    adjustment_guidance: str


@dataclass
class FirewallThreshold:
    """Firewall classification threshold.

    Defines a threshold used by the cognitive firewall to classify
    incoming content as accepted, rejected, or quarantined.

    Args:
        name: Threshold name (e.g., "Accept threshold").
        recommended: Recommended threshold value.
        risk_tradeoff: Description of the risk trade-off when adjusting.
    """

    name: str
    recommended: float
    risk_tradeoff: str


@dataclass
class TripwireConfig:
    """Tripwire configuration recommendation.

    Specifies the recommended minimum count and placement strategy
    for a category of canary beliefs used as tripwires.

    Args:
        category: Canary category name.
        recommended_count: Minimum recommended count of canaries.
        placement_strategy: Where to place canaries of this type.
    """

    category: str
    recommended_count: int
    placement_strategy: str


class ConfigurationReference:
    """Configuration quick reference from manuscript Section 03.

    Validates trust calculus, firewall, and tripwire parameters against
    the recommended ranges specified in the manuscript. Provides
    validation methods that return (valid, issues) tuples for each
    configuration area.

    Default values from manuscript:
        Trust Calculus: alpha=0.3, beta=0.4, gamma=0.3, delta=0.9
        Firewall: accept=0.3, reject=0.7, quarantine=0.3-0.7
        Tripwires: identity=3+, boundary=5+, principal=2+, temporal=1
    """

    def __init__(self) -> None:
        """Initialize with default configuration references from manuscript."""
        self.trust_params: list[TrustParameter] = []
        self.firewall_thresholds: list[FirewallThreshold] = []
        self.tripwire_configs: list[TripwireConfig] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load configuration reference from manuscript Section 03.

        Populates trust parameters, firewall thresholds, and tripwire
        configurations with the values specified in the manuscript.
        """
        self.trust_params = [
            TrustParameter(
                name="Base weight",
                symbol="\u03b1",
                recommended=0.3,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Increase for stable architectures",
            ),
            TrustParameter(
                name="Reputation weight",
                symbol="\u03b2",
                recommended=0.4,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Decrease for new deployments",
            ),
            TrustParameter(
                name="Context weight",
                symbol="\u03b3",
                recommended=0.3,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Increase for specialized tasks",
            ),
            TrustParameter(
                name="Decay factor",
                symbol="\u03b4",
                recommended=0.9,
                range_min=0.5,
                range_max=0.99,
                adjustment_guidance="Decrease for security-critical systems",
            ),
        ]

        self.firewall_thresholds = [
            FirewallThreshold(
                name="Accept threshold",
                recommended=0.3,
                risk_tradeoff="Lower = more strict, more false positives",
            ),
            FirewallThreshold(
                name="Reject threshold",
                recommended=0.7,
                risk_tradeoff="Higher = more permissive, more risk",
            ),
            FirewallThreshold(
                name="Quarantine lower",
                recommended=0.3,
                risk_tradeoff=("Narrower range = faster decisions, less nuance"),
            ),
            FirewallThreshold(
                name="Quarantine upper",
                recommended=0.7,
                risk_tradeoff=("Narrower range = faster decisions, less nuance"),
            ),
        ]

        self.tripwire_configs = [
            TripwireConfig(
                category="Identity canaries",
                recommended_count=3,
                placement_strategy="Core identity beliefs",
            ),
            TripwireConfig(
                category="Boundary canaries",
                recommended_count=5,
                placement_strategy="Permission boundaries",
            ),
            TripwireConfig(
                category="Principal canaries",
                recommended_count=2,
                placement_strategy="Trust relationships",
            ),
            TripwireConfig(
                category="Temporal canaries",
                recommended_count=1,
                placement_strategy="Session continuity",
            ),
        ]

    def validate_trust_weights(
        self, alpha: float, beta: float, gamma: float
    ) -> tuple[bool, list[str]]:
        """Validate that trust weights sum to 1.0 and are in range.

        Checks two conditions:
        1. The three weights must sum to 1.0 (within 0.01 tolerance).
        2. Each weight must fall within its recommended range.

        Args:
            alpha: Base weight (recommended range: 0.1-0.6).
            beta: Reputation weight (recommended range: 0.1-0.6).
            gamma: Context weight (recommended range: 0.1-0.6).

        Returns:
            Tuple of (valid, issues) where valid is True if all checks
            pass, and issues is a list of human-readable issue strings.
        """
        issues: list[str] = []

        if abs(alpha + beta + gamma - 1.0) > 0.01:
            issues.append(f"Weights must sum to 1.0, got {alpha + beta + gamma:.2f}")

        for name, value, param in [
            ("alpha", alpha, self.trust_params[0]),
            ("beta", beta, self.trust_params[1]),
            ("gamma", gamma, self.trust_params[2]),
        ]:
            if not param.range_min <= value <= param.range_max:
                issues.append(
                    f"{name}={value} outside recommended range "
                    f"[{param.range_min}, {param.range_max}]"
                )

        return len(issues) == 0, issues

    def validate_decay(self, delta: float) -> tuple[bool, list[str]]:
        """Validate decay factor against recommended range.

        The decay factor controls how quickly trust degrades over
        delegation hops. Must fall within [0.5, 0.99].

        Args:
            delta: Decay factor to validate.

        Returns:
            Tuple of (valid, issues) where valid is True if delta
            is within the recommended range.
        """
        param = self.trust_params[3]  # Decay factor
        issues: list[str] = []

        if not param.range_min <= delta <= param.range_max:
            issues.append(
                f"delta={delta} outside recommended range [{param.range_min}, {param.range_max}]"
            )

        return len(issues) == 0, issues

    def validate_firewall(self, accept: float, reject: float) -> tuple[bool, list[str]]:
        """Validate firewall thresholds.

        Checks three conditions:
        1. Accept threshold must be in [0, 1].
        2. Reject threshold must be in [0, 1].
        3. Accept must be strictly less than reject (to create a
           valid quarantine zone between them).

        Args:
            accept: Accept threshold (content scoring below this is accepted).
            reject: Reject threshold (content scoring above this is rejected).

        Returns:
            Tuple of (valid, issues) where valid is True if all checks
            pass, and issues is a list of human-readable issue strings.
        """
        issues: list[str] = []

        if not 0 <= accept <= 1:
            issues.append(f"Accept threshold must be 0-1, got {accept}")
        if not 0 <= reject <= 1:
            issues.append(f"Reject threshold must be 0-1, got {reject}")
        if accept >= reject:
            issues.append(f"Accept ({accept}) must be less than reject ({reject})")

        return len(issues) == 0, issues

    def validate_tripwire_counts(self, counts: dict[str, int]) -> tuple[bool, list[str]]:
        """Validate tripwire canary counts against recommendations.

        Each canary category has a minimum recommended count. Missing
        categories are treated as having zero canaries deployed.

        Args:
            counts: Dictionary mapping category name to actual count
                of deployed canaries.

        Returns:
            Tuple of (valid, issues) where valid is True if all
            categories meet their minimum recommended counts.
        """
        issues: list[str] = []

        for config in self.tripwire_configs:
            actual = counts.get(config.category, 0)
            if actual < config.recommended_count:
                issues.append(
                    f"{config.category}: {actual} < {config.recommended_count} recommended"
                )

        return len(issues) == 0, issues


# =============================================================================
# Module Exports
# =============================================================================


__all__ = [
    "ChecklistPhase",
    "ChecklistCategory",
    "OperationalFrequency",
    "IncidentSeverity",
    "EnhancedChecklistItem",
    "PreDeploymentChecklist",
    "OperationalChecklist",
    "IncidentResponseChecklist",
    "TrustParameter",
    "FirewallThreshold",
    "TripwireConfig",
    "ConfigurationReference",
]
