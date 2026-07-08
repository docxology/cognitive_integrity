"""Tests for human-actionable checklists module.

Tests cover:
- All enum values (ChecklistPhase, ChecklistCategory, OperationalFrequency, IncidentSeverity)
- EnhancedChecklistItem: creation, completed property get/set
- PreDeploymentChecklist: 16 items loaded, category items, complete/invalid, phase gates, evaluate
- OperationalChecklist: daily/weekly items, complete, reset cycles, completeness checks
- IncidentResponseChecklist: activation, phase items, complete, timeline
- ConfigurationReference: trust weights, decay, firewall, tripwire counts
- Edge cases and error handling
"""

import pytest

from src import AssessmentResult, ChecklistItem, RiskLevel
from src.checklists import (
    ChecklistCategory,
    ChecklistPhase,
    ConfigurationReference,
    EnhancedChecklistItem,
    FirewallThreshold,
    IncidentResponseChecklist,
    IncidentSeverity,
    OperationalChecklist,
    OperationalFrequency,
    PreDeploymentChecklist,
    TripwireConfig,
    TrustParameter,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestChecklistPhase:
    """Tests for ChecklistPhase enum."""

    def test_all_values(self):
        """Test all phase enum values exist and are correct."""
        assert ChecklistPhase.PRE_DEPLOYMENT.value == "pre_deployment"
        assert ChecklistPhase.OPERATIONAL.value == "operational"
        assert ChecklistPhase.INCIDENT_RESPONSE.value == "incident_response"

    def test_member_count(self):
        """Test there are exactly 3 phases."""
        assert len(ChecklistPhase) == 3


class TestChecklistCategory:
    """Tests for ChecklistCategory enum."""

    def test_all_values(self):
        """Test all category enum values."""
        assert ChecklistCategory.ARCHITECTURE_REVIEW.value == "architecture_review"
        assert ChecklistCategory.DEFENSE_CONFIGURATION.value == "defense_configuration"
        assert ChecklistCategory.MONITORING_SETUP.value == "monitoring_setup"
        assert ChecklistCategory.INCIDENT_RESPONSE_PREP.value == "incident_response_prep"

    def test_member_count(self):
        """Test there are exactly 4 categories."""
        assert len(ChecklistCategory) == 4


class TestOperationalFrequency:
    """Tests for OperationalFrequency enum."""

    def test_all_values(self):
        """Test all frequency enum values."""
        assert OperationalFrequency.DAILY.value == "daily"
        assert OperationalFrequency.WEEKLY.value == "weekly"

    def test_member_count(self):
        """Test there are exactly 2 frequencies."""
        assert len(OperationalFrequency) == 2


class TestIncidentSeverity:
    """Tests for IncidentSeverity enum."""

    def test_all_values(self):
        """Test all severity enum values."""
        assert IncidentSeverity.IMMEDIATE.value == "immediate"
        assert IncidentSeverity.INVESTIGATION.value == "investigation"
        assert IncidentSeverity.RECOVERY.value == "recovery"
        assert IncidentSeverity.POST_INCIDENT.value == "post_incident"

    def test_member_count(self):
        """Test there are exactly 4 severity levels."""
        assert len(IncidentSeverity) == 4


# =============================================================================
# EnhancedChecklistItem Tests
# =============================================================================


class TestEnhancedChecklistItem:
    """Tests for EnhancedChecklistItem dataclass."""

    def test_creation_with_defaults(self):
        """Test creating an enhanced item with default values."""
        base = ChecklistItem(id="test-001", category="testing", description="A test item")
        enhanced = EnhancedChecklistItem(item=base, phase=ChecklistPhase.PRE_DEPLOYMENT)
        assert enhanced.item is base
        assert enhanced.phase == ChecklistPhase.PRE_DEPLOYMENT
        assert enhanced.category == ""
        assert enhanced.evidence == ""
        assert enhanced.verified_by == ""
        assert enhanced.verification_date == ""

    def test_creation_with_all_fields(self):
        """Test creating an enhanced item with all fields populated."""
        base = ChecklistItem(id="test-002", category="testing", description="Full item")
        enhanced = EnhancedChecklistItem(
            item=base,
            phase=ChecklistPhase.OPERATIONAL,
            category="daily",
            evidence="Screenshot attached",
            verified_by="admin",
            verification_date="2026-01-29",
        )
        assert enhanced.category == "daily"
        assert enhanced.evidence == "Screenshot attached"
        assert enhanced.verified_by == "admin"
        assert enhanced.verification_date == "2026-01-29"

    def test_completed_property_getter(self):
        """Test that completed property delegates to underlying item."""
        base = ChecklistItem(id="test-003", category="testing", description="Getter test")
        enhanced = EnhancedChecklistItem(item=base, phase=ChecklistPhase.PRE_DEPLOYMENT)
        assert enhanced.completed is False
        base.completed = True
        assert enhanced.completed is True

    def test_completed_property_setter(self):
        """Test that setting completed propagates to underlying item."""
        base = ChecklistItem(id="test-004", category="testing", description="Setter test")
        enhanced = EnhancedChecklistItem(item=base, phase=ChecklistPhase.PRE_DEPLOYMENT)
        enhanced.completed = True
        assert base.completed is True
        assert enhanced.completed is True

    def test_completed_setter_false(self):
        """Test setting completed back to false."""
        base = ChecklistItem(
            id="test-005",
            category="testing",
            description="Reset test",
            completed=True,
        )
        enhanced = EnhancedChecklistItem(item=base, phase=ChecklistPhase.PRE_DEPLOYMENT)
        assert enhanced.completed is True
        enhanced.completed = False
        assert base.completed is False


# =============================================================================
# PreDeploymentChecklist Tests
# =============================================================================


class TestPreDeploymentChecklist:
    """Tests for PreDeploymentChecklist."""

    def test_loads_16_items(self):
        """Test that default initialization loads exactly 16 items."""
        checklist = PreDeploymentChecklist()
        assert len(checklist.items) == 16

    def test_all_items_are_pre_deployment_phase(self):
        """Test all items belong to the pre-deployment phase."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items:
            assert item.phase == ChecklistPhase.PRE_DEPLOYMENT

    def test_four_items_per_category(self):
        """Test each category has exactly 4 items."""
        checklist = PreDeploymentChecklist()
        for category in ChecklistCategory:
            items = checklist.get_category_items(category)
            assert len(items) == 4, f"{category.value} should have 4 items"

    def test_architecture_review_items(self):
        """Test architecture review category contains expected items."""
        checklist = PreDeploymentChecklist()
        items = checklist.get_category_items(ChecklistCategory.ARCHITECTURE_REVIEW)
        ids = [i.item.id for i in items]
        assert ids == ["arch-001", "arch-002", "arch-003", "arch-004"]

    def test_defense_configuration_items(self):
        """Test defense configuration category contains expected items."""
        checklist = PreDeploymentChecklist()
        items = checklist.get_category_items(ChecklistCategory.DEFENSE_CONFIGURATION)
        ids = [i.item.id for i in items]
        assert ids == ["def-001", "def-002", "def-003", "def-004"]

    def test_monitoring_setup_items(self):
        """Test monitoring setup category contains expected items."""
        checklist = PreDeploymentChecklist()
        items = checklist.get_category_items(ChecklistCategory.MONITORING_SETUP)
        ids = [i.item.id for i in items]
        assert ids == ["mon-001", "mon-002", "mon-003", "mon-004"]

    def test_incident_response_prep_items(self):
        """Test incident response prep category contains expected items."""
        checklist = PreDeploymentChecklist()
        items = checklist.get_category_items(ChecklistCategory.INCIDENT_RESPONSE_PREP)
        ids = [i.item.id for i in items]
        assert ids == ["ir-001", "ir-002", "ir-003", "ir-004"]

    def test_all_items_required_by_default(self):
        """Test all pre-deployment items are required by default."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items:
            assert item.item.required is True

    def test_complete_item_valid(self):
        """Test completing a valid item."""
        checklist = PreDeploymentChecklist()
        checklist.complete_item("arch-001", evidence="Documented in wiki", verified_by="admin")
        item = next(i for i in checklist.items if i.item.id == "arch-001")
        assert item.completed is True
        assert item.evidence == "Documented in wiki"
        assert item.verified_by == "admin"

    def test_complete_item_without_evidence(self):
        """Test completing an item without optional evidence."""
        checklist = PreDeploymentChecklist()
        checklist.complete_item("def-001")
        item = next(i for i in checklist.items if i.item.id == "def-001")
        assert item.completed is True
        assert item.evidence == ""

    def test_complete_item_invalid_id(self):
        """Test completing a nonexistent item raises ValueError."""
        checklist = PreDeploymentChecklist()
        with pytest.raises(ValueError, match="Item 'nonexistent' not found"):
            checklist.complete_item("nonexistent")

    def test_category_complete_when_all_done(self):
        """Test category reports complete when all required items done."""
        checklist = PreDeploymentChecklist()
        for item in checklist.get_category_items(ChecklistCategory.ARCHITECTURE_REVIEW):
            checklist.complete_item(item.item.id)
        assert checklist.category_complete(ChecklistCategory.ARCHITECTURE_REVIEW) is True

    def test_category_incomplete_when_missing(self):
        """Test category reports incomplete with missing items."""
        checklist = PreDeploymentChecklist()
        checklist.complete_item("arch-001")
        checklist.complete_item("arch-002")
        # arch-003 and arch-004 not completed
        assert checklist.category_complete(ChecklistCategory.ARCHITECTURE_REVIEW) is False

    def test_category_complete_no_items_done(self):
        """Test category incomplete when nothing is done."""
        checklist = PreDeploymentChecklist()
        assert checklist.category_complete(ChecklistCategory.MONITORING_SETUP) is False

    def test_phase_gate_check_all_incomplete(self):
        """Test phase gate returns all false when nothing completed."""
        checklist = PreDeploymentChecklist()
        gate = checklist.phase_gate_check()
        assert len(gate) == 4
        for category, complete in gate.items():
            assert complete is False

    def test_phase_gate_check_partial(self):
        """Test phase gate with one category complete."""
        checklist = PreDeploymentChecklist()
        for item in checklist.get_category_items(ChecklistCategory.ARCHITECTURE_REVIEW):
            checklist.complete_item(item.item.id)
        gate = checklist.phase_gate_check()
        assert gate[ChecklistCategory.ARCHITECTURE_REVIEW] is True
        assert gate[ChecklistCategory.DEFENSE_CONFIGURATION] is False
        assert gate[ChecklistCategory.MONITORING_SETUP] is False
        assert gate[ChecklistCategory.INCIDENT_RESPONSE_PREP] is False

    def test_phase_gate_check_all_complete(self):
        """Test phase gate with all categories complete."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items:
            checklist.complete_item(item.item.id)
        gate = checklist.phase_gate_check()
        assert all(gate.values())

    def test_is_ready_false_initially(self):
        """Test is_ready returns false with no items completed."""
        checklist = PreDeploymentChecklist()
        assert checklist.is_ready() is False

    def test_is_ready_true_when_all_complete(self):
        """Test is_ready returns true when all items completed."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items:
            checklist.complete_item(item.item.id)
        assert checklist.is_ready() is True

    def test_is_ready_false_with_partial_completion(self):
        """Test is_ready false when only some categories complete."""
        checklist = PreDeploymentChecklist()
        for item in checklist.get_category_items(ChecklistCategory.ARCHITECTURE_REVIEW):
            checklist.complete_item(item.item.id)
        for item in checklist.get_category_items(ChecklistCategory.DEFENSE_CONFIGURATION):
            checklist.complete_item(item.item.id)
        assert checklist.is_ready() is False

    def test_evaluate_all_complete(self):
        """Test evaluation with all items completed."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items:
            checklist.complete_item(item.item.id)
        result = checklist.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
        assert len(result.findings) == 0
        assert len(result.recommendations) == 0

    def test_evaluate_none_complete(self):
        """Test evaluation with no items completed."""
        checklist = PreDeploymentChecklist()
        result = checklist.evaluate()
        assert result.passed is False
        assert result.score == 0.0
        assert result.risk_level == RiskLevel.CRITICAL
        assert len(result.findings) == 16
        assert len(result.recommendations) == 4

    def test_evaluate_high_compliance(self):
        """Test evaluation at ~81% compliance (13/16)."""
        checklist = PreDeploymentChecklist()
        # Complete 13 out of 16
        for item in checklist.items[:13]:
            checklist.complete_item(item.item.id)
        result = checklist.evaluate()
        assert result.passed is True
        assert result.score == pytest.approx(13 / 16)
        assert result.risk_level == RiskLevel.MEDIUM

    def test_evaluate_medium_compliance(self):
        """Test evaluation at ~69% compliance (11/16)."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items[:11]:
            checklist.complete_item(item.item.id)
        result = checklist.evaluate()
        assert result.passed is False
        assert result.score == pytest.approx(11 / 16)
        assert result.risk_level == RiskLevel.HIGH

    def test_evaluate_low_compliance(self):
        """Test evaluation at ~25% compliance (4/16)."""
        checklist = PreDeploymentChecklist()
        for item in checklist.items[:4]:
            checklist.complete_item(item.item.id)
        result = checklist.evaluate()
        assert result.passed is False
        assert result.score == pytest.approx(4 / 16)
        assert result.risk_level == RiskLevel.CRITICAL

    def test_evaluate_returns_assessment_result(self):
        """Test evaluate returns proper AssessmentResult type."""
        checklist = PreDeploymentChecklist()
        result = checklist.evaluate()
        assert isinstance(result, AssessmentResult)

    def test_evaluate_findings_list_incomplete(self):
        """Test findings contain descriptions of incomplete items."""
        checklist = PreDeploymentChecklist()
        checklist.complete_item("arch-001")
        result = checklist.evaluate()
        # 15 incomplete findings
        assert len(result.findings) == 15
        # arch-001 should NOT be in findings
        assert not any("arch-001" in f for f in result.findings)

    def test_evaluate_recommendations_for_incomplete_categories(self):
        """Test recommendations reference incomplete categories."""
        checklist = PreDeploymentChecklist()
        # Complete only architecture review
        for item in checklist.get_category_items(ChecklistCategory.ARCHITECTURE_REVIEW):
            checklist.complete_item(item.item.id)
        result = checklist.evaluate()
        # 3 categories still incomplete
        assert len(result.recommendations) == 3


# =============================================================================
# OperationalChecklist Tests
# =============================================================================


class TestOperationalChecklist:
    """Tests for OperationalChecklist."""

    def test_loads_8_items_total(self):
        """Test default initialization loads 8 items."""
        checklist = OperationalChecklist()
        assert len(checklist.items) == 8

    def test_4_daily_items(self):
        """Test there are exactly 4 daily items."""
        checklist = OperationalChecklist()
        assert len(checklist.get_daily_items()) == 4

    def test_4_weekly_items(self):
        """Test there are exactly 4 weekly items."""
        checklist = OperationalChecklist()
        assert len(checklist.get_weekly_items()) == 4

    def test_daily_item_ids(self):
        """Test daily items have correct IDs."""
        checklist = OperationalChecklist()
        ids = [i.item.id for i in checklist.get_daily_items()]
        assert ids == ["daily-001", "daily-002", "daily-003", "daily-004"]

    def test_weekly_item_ids(self):
        """Test weekly items have correct IDs."""
        checklist = OperationalChecklist()
        ids = [i.item.id for i in checklist.get_weekly_items()]
        assert ids == ["weekly-001", "weekly-002", "weekly-003", "weekly-004"]

    def test_all_items_operational_phase(self):
        """Test all items belong to operational phase."""
        checklist = OperationalChecklist()
        for item in checklist.items:
            assert item.phase == ChecklistPhase.OPERATIONAL

    def test_complete_daily_item(self):
        """Test completing a daily item."""
        checklist = OperationalChecklist()
        checklist.complete_item("daily-001")
        item = next(i for i in checklist.items if i.item.id == "daily-001")
        assert item.completed is True

    def test_complete_weekly_item(self):
        """Test completing a weekly item."""
        checklist = OperationalChecklist()
        checklist.complete_item("weekly-003")
        item = next(i for i in checklist.items if i.item.id == "weekly-003")
        assert item.completed is True

    def test_complete_invalid_item(self):
        """Test completing a nonexistent item raises ValueError."""
        checklist = OperationalChecklist()
        with pytest.raises(ValueError, match="Item 'invalid-999' not found"):
            checklist.complete_item("invalid-999")

    def test_daily_complete_false_initially(self):
        """Test daily_complete returns false when nothing done."""
        checklist = OperationalChecklist()
        assert checklist.daily_complete() is False

    def test_daily_complete_partial(self):
        """Test daily_complete false with partial completion."""
        checklist = OperationalChecklist()
        checklist.complete_item("daily-001")
        checklist.complete_item("daily-002")
        assert checklist.daily_complete() is False

    def test_daily_complete_all(self):
        """Test daily_complete true when all daily items done."""
        checklist = OperationalChecklist()
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        assert checklist.daily_complete() is True

    def test_weekly_complete_false_initially(self):
        """Test weekly_complete returns false when nothing done."""
        checklist = OperationalChecklist()
        assert checklist.weekly_complete() is False

    def test_weekly_complete_all(self):
        """Test weekly_complete true when all weekly items done."""
        checklist = OperationalChecklist()
        for item in checklist.get_weekly_items():
            checklist.complete_item(item.item.id)
        assert checklist.weekly_complete() is True

    def test_daily_complete_independent_of_weekly(self):
        """Test daily completion does not affect weekly status."""
        checklist = OperationalChecklist()
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        assert checklist.daily_complete() is True
        assert checklist.weekly_complete() is False

    def test_reset_daily(self):
        """Test resetting daily items to incomplete."""
        checklist = OperationalChecklist()
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        assert checklist.daily_complete() is True
        checklist.reset_daily()
        assert checklist.daily_complete() is False
        for item in checklist.get_daily_items():
            assert item.completed is False

    def test_reset_daily_preserves_weekly(self):
        """Test that resetting daily does not touch weekly items."""
        checklist = OperationalChecklist()
        for item in checklist.get_weekly_items():
            checklist.complete_item(item.item.id)
        checklist.reset_daily()
        assert checklist.weekly_complete() is True

    def test_reset_weekly(self):
        """Test resetting weekly items to incomplete."""
        checklist = OperationalChecklist()
        for item in checklist.get_weekly_items():
            checklist.complete_item(item.item.id)
        assert checklist.weekly_complete() is True
        checklist.reset_weekly()
        assert checklist.weekly_complete() is False

    def test_reset_weekly_preserves_daily(self):
        """Test that resetting weekly does not touch daily items."""
        checklist = OperationalChecklist()
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        checklist.reset_weekly()
        assert checklist.daily_complete() is True

    def test_full_cycle_daily_reset_recomplete(self):
        """Test a full daily cycle: complete, reset, re-complete."""
        checklist = OperationalChecklist()
        # First cycle
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        assert checklist.daily_complete() is True
        # Reset
        checklist.reset_daily()
        assert checklist.daily_complete() is False
        # Second cycle
        for item in checklist.get_daily_items():
            checklist.complete_item(item.item.id)
        assert checklist.daily_complete() is True


# =============================================================================
# IncidentResponseChecklist Tests
# =============================================================================


class TestIncidentResponseChecklist:
    """Tests for IncidentResponseChecklist."""

    def test_loads_16_items(self):
        """Test default initialization loads exactly 16 items."""
        checklist = IncidentResponseChecklist()
        assert len(checklist.items) == 16

    def test_not_activated_by_default(self):
        """Test checklist is not activated on creation."""
        checklist = IncidentResponseChecklist()
        assert checklist.activated is False
        assert checklist.activation_reason == ""

    def test_activate(self):
        """Test activating the incident response checklist."""
        checklist = IncidentResponseChecklist()
        checklist.activate("Suspicious belief drift detected in agent-7")
        assert checklist.activated is True
        assert checklist.activation_reason == "Suspicious belief drift detected in agent-7"

    def test_all_items_incident_response_phase(self):
        """Test all items belong to incident response phase."""
        checklist = IncidentResponseChecklist()
        for item in checklist.items:
            assert item.phase == ChecklistPhase.INCIDENT_RESPONSE

    def test_four_items_per_severity(self):
        """Test each severity phase has exactly 4 items."""
        checklist = IncidentResponseChecklist()
        for severity in IncidentSeverity:
            items = checklist.get_phase_items(severity)
            assert len(items) == 4, f"{severity.value} should have 4 items"

    def test_immediate_item_ids(self):
        """Test immediate phase item IDs."""
        checklist = IncidentResponseChecklist()
        items = checklist.get_phase_items(IncidentSeverity.IMMEDIATE)
        ids = [i.item.id for i in items]
        assert ids == ["imm-001", "imm-002", "imm-003", "imm-004"]

    def test_investigation_item_ids(self):
        """Test investigation phase item IDs."""
        checklist = IncidentResponseChecklist()
        items = checklist.get_phase_items(IncidentSeverity.INVESTIGATION)
        ids = [i.item.id for i in items]
        assert ids == ["inv-001", "inv-002", "inv-003", "inv-004"]

    def test_recovery_item_ids(self):
        """Test recovery phase item IDs."""
        checklist = IncidentResponseChecklist()
        items = checklist.get_phase_items(IncidentSeverity.RECOVERY)
        ids = [i.item.id for i in items]
        assert ids == ["rec-001", "rec-002", "rec-003", "rec-004"]

    def test_post_incident_item_ids(self):
        """Test post-incident phase item IDs."""
        checklist = IncidentResponseChecklist()
        items = checklist.get_phase_items(IncidentSeverity.POST_INCIDENT)
        ids = [i.item.id for i in items]
        assert ids == ["post-001", "post-002", "post-003", "post-004"]

    def test_complete_item_with_evidence(self):
        """Test completing an item with evidence."""
        checklist = IncidentResponseChecklist()
        checklist.complete_item("imm-001", evidence="State snapshot saved to /var/log/cogsec")
        item = next(i for i in checklist.items if i.item.id == "imm-001")
        assert item.completed is True
        assert item.evidence == "State snapshot saved to /var/log/cogsec"

    def test_complete_item_without_evidence(self):
        """Test completing an item without evidence."""
        checklist = IncidentResponseChecklist()
        checklist.complete_item("inv-002")
        item = next(i for i in checklist.items if i.item.id == "inv-002")
        assert item.completed is True
        assert item.evidence == ""

    def test_complete_invalid_item(self):
        """Test completing nonexistent item raises ValueError."""
        checklist = IncidentResponseChecklist()
        with pytest.raises(ValueError, match="Item 'bad-id' not found"):
            checklist.complete_item("bad-id")

    def test_phase_complete_false_initially(self):
        """Test phase_complete returns false with no items done."""
        checklist = IncidentResponseChecklist()
        assert checklist.phase_complete(IncidentSeverity.IMMEDIATE) is False

    def test_phase_complete_partial(self):
        """Test phase_complete false with partial completion."""
        checklist = IncidentResponseChecklist()
        checklist.complete_item("imm-001")
        checklist.complete_item("imm-002")
        assert checklist.phase_complete(IncidentSeverity.IMMEDIATE) is False

    def test_phase_complete_all(self):
        """Test phase_complete true when all items in phase done."""
        checklist = IncidentResponseChecklist()
        for item in checklist.get_phase_items(IncidentSeverity.IMMEDIATE):
            checklist.complete_item(item.item.id)
        assert checklist.phase_complete(IncidentSeverity.IMMEDIATE) is True

    def test_phase_complete_independent(self):
        """Test completing one phase does not affect others."""
        checklist = IncidentResponseChecklist()
        for item in checklist.get_phase_items(IncidentSeverity.IMMEDIATE):
            checklist.complete_item(item.item.id)
        assert checklist.phase_complete(IncidentSeverity.IMMEDIATE) is True
        assert checklist.phase_complete(IncidentSeverity.INVESTIGATION) is False
        assert checklist.phase_complete(IncidentSeverity.RECOVERY) is False
        assert checklist.phase_complete(IncidentSeverity.POST_INCIDENT) is False

    def test_timeline_structure(self):
        """Test timeline returns correct structure."""
        checklist = IncidentResponseChecklist()
        timeline = checklist.get_timeline()
        assert len(timeline) == 4
        for entry in timeline:
            assert "phase" in entry
            assert "time_window" in entry
            assert "complete" in entry

    def test_timeline_phases_in_order(self):
        """Test timeline phases appear in correct order."""
        checklist = IncidentResponseChecklist()
        timeline = checklist.get_timeline()
        phases = [entry["phase"] for entry in timeline]
        assert phases == ["immediate", "investigation", "recovery", "post_incident"]

    def test_timeline_time_windows(self):
        """Test timeline contains correct time windows."""
        checklist = IncidentResponseChecklist()
        timeline = checklist.get_timeline()
        windows = [entry["time_window"] for entry in timeline]
        assert windows == [
            "First 15 minutes",
            "First hour",
            "Following hours",
            "Following days",
        ]

    def test_timeline_all_incomplete_initially(self):
        """Test timeline shows all phases incomplete initially."""
        checklist = IncidentResponseChecklist()
        timeline = checklist.get_timeline()
        for entry in timeline:
            assert entry["complete"] is False

    def test_timeline_reflects_completion(self):
        """Test timeline updates when phases are completed."""
        checklist = IncidentResponseChecklist()
        for item in checklist.get_phase_items(IncidentSeverity.IMMEDIATE):
            checklist.complete_item(item.item.id)
        for item in checklist.get_phase_items(IncidentSeverity.RECOVERY):
            checklist.complete_item(item.item.id)
        timeline = checklist.get_timeline()
        assert timeline[0]["complete"] is True  # immediate
        assert timeline[1]["complete"] is False  # investigation
        assert timeline[2]["complete"] is True  # recovery
        assert timeline[3]["complete"] is False  # post_incident


# =============================================================================
# ConfigurationReference Tests
# =============================================================================


class TestTrustParameter:
    """Tests for TrustParameter dataclass."""

    def test_creation(self):
        """Test creating a trust parameter."""
        param = TrustParameter(
            name="Test weight",
            symbol="t",
            recommended=0.5,
            range_min=0.1,
            range_max=0.9,
            adjustment_guidance="Adjust as needed",
        )
        assert param.name == "Test weight"
        assert param.symbol == "t"
        assert param.recommended == 0.5
        assert param.range_min == 0.1
        assert param.range_max == 0.9


class TestFirewallThreshold:
    """Tests for FirewallThreshold dataclass."""

    def test_creation(self):
        """Test creating a firewall threshold."""
        threshold = FirewallThreshold(
            name="Accept",
            recommended=0.3,
            risk_tradeoff="Lower = more strict",
        )
        assert threshold.name == "Accept"
        assert threshold.recommended == 0.3
        assert threshold.risk_tradeoff == "Lower = more strict"


class TestTripwireConfig:
    """Tests for TripwireConfig dataclass."""

    def test_creation(self):
        """Test creating a tripwire config."""
        config = TripwireConfig(
            category="Identity canaries",
            recommended_count=3,
            placement_strategy="Core identity beliefs",
        )
        assert config.category == "Identity canaries"
        assert config.recommended_count == 3
        assert config.placement_strategy == "Core identity beliefs"


class TestConfigurationReference:
    """Tests for ConfigurationReference."""

    def test_loads_4_trust_params(self):
        """Test default initialization loads 4 trust parameters."""
        ref = ConfigurationReference()
        assert len(ref.trust_params) == 4

    def test_trust_param_symbols(self):
        """Test trust parameters have correct symbols."""
        ref = ConfigurationReference()
        symbols = [p.symbol for p in ref.trust_params]
        assert symbols == ["\u03b1", "\u03b2", "\u03b3", "\u03b4"]

    def test_trust_param_recommended_values(self):
        """Test trust parameters have manuscript-specified defaults."""
        ref = ConfigurationReference()
        values = [p.recommended for p in ref.trust_params]
        assert values == [0.3, 0.4, 0.3, 0.9]

    def test_loads_4_firewall_thresholds(self):
        """Test default initialization loads 4 firewall thresholds."""
        ref = ConfigurationReference()
        assert len(ref.firewall_thresholds) == 4

    def test_firewall_recommended_values(self):
        """Test firewall thresholds have manuscript-specified defaults."""
        ref = ConfigurationReference()
        values = [t.recommended for t in ref.firewall_thresholds]
        assert values == [0.3, 0.7, 0.3, 0.7]

    def test_loads_4_tripwire_configs(self):
        """Test default initialization loads 4 tripwire configurations."""
        ref = ConfigurationReference()
        assert len(ref.tripwire_configs) == 4

    def test_tripwire_recommended_counts(self):
        """Test tripwire configs have manuscript-specified counts."""
        ref = ConfigurationReference()
        counts = [c.recommended_count for c in ref.tripwire_configs]
        assert counts == [3, 5, 2, 1]

    # --- Trust Weight Validation ---

    def test_validate_trust_weights_valid_default(self):
        """Test validation passes with default recommended values."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_trust_weights(0.3, 0.4, 0.3)
        assert valid is True
        assert len(issues) == 0

    def test_validate_trust_weights_valid_custom(self):
        """Test validation passes with custom valid weights."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_trust_weights(0.2, 0.5, 0.3)
        assert valid is True
        assert len(issues) == 0

    def test_validate_trust_weights_bad_sum(self):
        """Test validation fails when weights do not sum to 1.0."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_trust_weights(0.3, 0.3, 0.3)
        assert valid is False
        assert any("sum to 1.0" in issue for issue in issues)

    def test_validate_trust_weights_sum_too_high(self):
        """Test validation fails when weights sum exceeds 1.0."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_trust_weights(0.5, 0.5, 0.5)
        assert valid is False

    def test_validate_trust_weights_alpha_out_of_range(self):
        """Test validation fails when alpha is outside range."""
        ref = ConfigurationReference()
        # alpha=0.05 is below min 0.1; adjust beta/gamma to still sum to 1.0
        valid, issues = ref.validate_trust_weights(0.05, 0.55, 0.4)
        assert valid is False
        assert any("alpha" in issue for issue in issues)

    def test_validate_trust_weights_beta_out_of_range(self):
        """Test validation fails when beta is outside range."""
        ref = ConfigurationReference()
        # beta=0.05 below min 0.1
        valid, issues = ref.validate_trust_weights(0.55, 0.05, 0.4)
        assert valid is False
        assert any("beta" in issue for issue in issues)

    def test_validate_trust_weights_gamma_out_of_range(self):
        """Test validation fails when gamma is outside range."""
        ref = ConfigurationReference()
        # gamma=0.05 below min 0.1
        valid, issues = ref.validate_trust_weights(0.55, 0.4, 0.05)
        assert valid is False
        assert any("gamma" in issue for issue in issues)

    def test_validate_trust_weights_multiple_issues(self):
        """Test validation reports multiple issues at once."""
        ref = ConfigurationReference()
        # Bad sum AND out of range
        valid, issues = ref.validate_trust_weights(0.05, 0.05, 0.05)
        assert valid is False
        assert len(issues) >= 2  # Sum issue + at least one range issue

    def test_validate_trust_weights_boundary_tolerance(self):
        """Test sum validation has 0.01 tolerance."""
        ref = ConfigurationReference()
        # 0.33 + 0.34 + 0.33 = 1.00 (within tolerance)
        valid, issues = ref.validate_trust_weights(0.33, 0.34, 0.33)
        assert valid is True

    # --- Decay Validation ---

    def test_validate_decay_valid_default(self):
        """Test decay validation passes with recommended value."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(0.9)
        assert valid is True
        assert len(issues) == 0

    def test_validate_decay_valid_low_end(self):
        """Test decay validation at lower boundary."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(0.5)
        assert valid is True

    def test_validate_decay_valid_high_end(self):
        """Test decay validation at upper boundary."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(0.99)
        assert valid is True

    def test_validate_decay_too_low(self):
        """Test decay validation fails below minimum."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(0.3)
        assert valid is False
        assert any("delta" in issue for issue in issues)

    def test_validate_decay_too_high(self):
        """Test decay validation fails above maximum."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(1.0)
        assert valid is False
        assert any("delta" in issue for issue in issues)

    def test_validate_decay_zero(self):
        """Test decay validation fails at zero."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_decay(0.0)
        assert valid is False

    # --- Firewall Validation ---

    def test_validate_firewall_valid_default(self):
        """Test firewall validation with manuscript defaults."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.3, 0.7)
        assert valid is True
        assert len(issues) == 0

    def test_validate_firewall_valid_custom(self):
        """Test firewall validation with custom valid thresholds."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.2, 0.8)
        assert valid is True

    def test_validate_firewall_accept_equals_reject(self):
        """Test firewall fails when accept equals reject."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.5, 0.5)
        assert valid is False
        assert any("less than" in issue for issue in issues)

    def test_validate_firewall_accept_greater_than_reject(self):
        """Test firewall fails when accept > reject."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.8, 0.3)
        assert valid is False

    def test_validate_firewall_accept_negative(self):
        """Test firewall fails with negative accept threshold."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(-0.1, 0.7)
        assert valid is False
        assert any("Accept" in issue for issue in issues)

    def test_validate_firewall_reject_above_one(self):
        """Test firewall fails with reject threshold above 1."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.3, 1.5)
        assert valid is False
        assert any("Reject" in issue for issue in issues)

    def test_validate_firewall_both_invalid(self):
        """Test firewall reports multiple issues."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(-0.1, 1.5)
        assert valid is False
        assert len(issues) >= 2

    def test_validate_firewall_boundary_values(self):
        """Test firewall accepts exact boundary values 0.0 and 1.0."""
        ref = ConfigurationReference()
        valid, issues = ref.validate_firewall(0.0, 1.0)
        assert valid is True

    # --- Tripwire Validation ---

    def test_validate_tripwire_counts_valid(self):
        """Test tripwire validation with sufficient counts."""
        ref = ConfigurationReference()
        counts = {
            "Identity canaries": 3,
            "Boundary canaries": 5,
            "Principal canaries": 2,
            "Temporal canaries": 1,
        }
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is True
        assert len(issues) == 0

    def test_validate_tripwire_counts_exceeding(self):
        """Test tripwire validation with more than recommended counts."""
        ref = ConfigurationReference()
        counts = {
            "Identity canaries": 10,
            "Boundary canaries": 10,
            "Principal canaries": 10,
            "Temporal canaries": 10,
        }
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is True

    def test_validate_tripwire_counts_insufficient(self):
        """Test tripwire validation with insufficient counts."""
        ref = ConfigurationReference()
        counts = {
            "Identity canaries": 1,
            "Boundary canaries": 2,
            "Principal canaries": 0,
            "Temporal canaries": 0,
        }
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is False
        assert len(issues) == 4

    def test_validate_tripwire_counts_partial_insufficient(self):
        """Test tripwire with some categories below threshold."""
        ref = ConfigurationReference()
        counts = {
            "Identity canaries": 3,
            "Boundary canaries": 5,
            "Principal canaries": 1,  # Below 2
            "Temporal canaries": 1,
        }
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is False
        assert len(issues) == 1
        assert "Principal canaries" in issues[0]

    def test_validate_tripwire_counts_missing_categories(self):
        """Test tripwire with missing categories defaults to 0."""
        ref = ConfigurationReference()
        counts = {}  # All missing
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is False
        assert len(issues) == 4

    def test_validate_tripwire_counts_partial_missing(self):
        """Test tripwire with some categories missing."""
        ref = ConfigurationReference()
        counts = {
            "Identity canaries": 5,
            "Boundary canaries": 7,
        }
        valid, issues = ref.validate_tripwire_counts(counts)
        assert valid is False
        # Principal canaries and Temporal canaries missing (default to 0)
        assert len(issues) == 2
