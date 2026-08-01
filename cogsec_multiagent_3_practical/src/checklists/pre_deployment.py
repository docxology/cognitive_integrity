from __future__ import annotations

from .. import AssessmentResult, ChecklistItem, RiskLevel
from .models import (
    ChecklistCategory,
    ChecklistPhase,
    EnhancedChecklistItem,
)


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
