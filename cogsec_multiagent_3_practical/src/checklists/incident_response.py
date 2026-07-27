from __future__ import annotations

from .. import AssessmentResult, ChecklistItem, RiskLevel
from .models import ChecklistPhase, EnhancedChecklistItem, IncidentSeverity


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
