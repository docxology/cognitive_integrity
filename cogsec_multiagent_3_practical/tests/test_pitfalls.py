"""
Tests for the Pitfall Catalog module (Section 07).

Covers all enums, dataclasses, catalog, detector, checklist,
remediation planning, and edge cases.
"""

import pytest

from src import AssessmentResult, RiskLevel
from src.pitfalls import (
    PitfallCatalog,
    PitfallCategory,
    PitfallChecklist,
    PitfallChecklistEntry,
    PitfallDefinition,
    PitfallDetector,
    PitfallID,
    PitfallIndicator,
    PitfallMitigation,
    RemediationPlan,
    RemediationStep,
    generate_remediation_plan,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestPitfallID:
    """Tests for PitfallID enum values."""

    def test_all_eight_ids_exist(self) -> None:
        """All 8 pitfall IDs are defined."""
        assert len(PitfallID) == 8

    def test_id_values(self) -> None:
        """Each ID has the correct PIT-N value."""
        expected = {
            PitfallID.IMPLICIT_TRUST: "PIT-1",
            PitfallID.SECURITY_AFTERTHOUGHT: "PIT-2",
            PitfallID.UNCALIBRATED_THRESHOLDS: "PIT-3",
            PitfallID.INDIVIDUAL_ONLY: "PIT-4",
            PitfallID.STATIC_TRIPWIRES: "PIT-5",
            PitfallID.IGNORING_DRIFT: "PIT-6",
            PitfallID.INSUFFICIENT_LOGGING: "PIT-7",
            PitfallID.SINGLE_ORCHESTRATOR: "PIT-8",
        }
        for pid, val in expected.items():
            assert pid.value == val

    def test_enum_from_value(self) -> None:
        """Can construct from string value."""
        assert PitfallID("PIT-1") == PitfallID.IMPLICIT_TRUST
        assert PitfallID("PIT-8") == PitfallID.SINGLE_ORCHESTRATOR


class TestPitfallCategory:
    """Tests for PitfallCategory enum values."""

    def test_all_categories_exist(self) -> None:
        """Three categories are defined."""
        assert len(PitfallCategory) == 3

    def test_category_values(self) -> None:
        """Categories have correct string values."""
        assert PitfallCategory.SECURITY.value == "security"
        assert PitfallCategory.OPERATIONAL.value == "operational"
        assert PitfallCategory.DESIGN.value == "design"


# =============================================================================
# Dataclass Tests
# =============================================================================


class TestPitfallIndicator:
    """Tests for PitfallIndicator dataclass."""

    def test_defaults(self) -> None:
        """Default present=False and notes=''."""
        ind = PitfallIndicator(description="Test indicator")
        assert ind.description == "Test indicator"
        assert ind.present is False
        assert ind.notes == ""

    def test_custom_values(self) -> None:
        """Can set all fields."""
        ind = PitfallIndicator(
            description="Observed something",
            present=True,
            notes="Found during audit",
        )
        assert ind.present is True
        assert ind.notes == "Found during audit"


class TestPitfallMitigation:
    """Tests for PitfallMitigation dataclass."""

    def test_defaults(self) -> None:
        """Default implemented=False and notes=''."""
        mit = PitfallMitigation(description="Apply fix")
        assert mit.description == "Apply fix"
        assert mit.implemented is False
        assert mit.notes == ""

    def test_custom_values(self) -> None:
        """Can set all fields."""
        mit = PitfallMitigation(
            description="Deploy rotation",
            implemented=True,
            notes="Deployed 2026-01-15",
        )
        assert mit.implemented is True
        assert mit.notes == "Deployed 2026-01-15"


class TestPitfallDefinition:
    """Tests for PitfallDefinition dataclass."""

    def test_minimal_definition(self) -> None:
        """Can create with required fields only."""
        defn = PitfallDefinition(
            id=PitfallID.IMPLICIT_TRUST,
            name="Implicit Trust",
            pattern="Trust everything",
            category=PitfallCategory.SECURITY,
            severity=5,
        )
        assert defn.id == PitfallID.IMPLICIT_TRUST
        assert defn.name == "Implicit Trust"
        assert defn.severity == 5
        assert defn.indicators == []
        assert defn.mitigations == []
        assert defn.manuscript_reference == ""

    def test_full_definition(self) -> None:
        """Can create with all fields populated."""
        defn = PitfallDefinition(
            id=PitfallID.STATIC_TRIPWIRES,
            name="Static Tripwires",
            pattern="No rotation",
            category=PitfallCategory.DESIGN,
            severity=4,
            indicators=[PitfallIndicator("No rotation schedule")],
            mitigations=[PitfallMitigation("Add rotation")],
            manuscript_reference="Section 07, Pitfall 5",
        )
        assert len(defn.indicators) == 1
        assert len(defn.mitigations) == 1
        assert defn.manuscript_reference == "Section 07, Pitfall 5"


# =============================================================================
# PitfallCatalog Tests
# =============================================================================


class TestPitfallCatalog:
    """Tests for PitfallCatalog registry."""

    def setup_method(self) -> None:
        """Create a fresh catalog for each test."""
        self.catalog = PitfallCatalog()

    def test_loads_eight_pitfalls(self) -> None:
        """Catalog loads all 8 pitfall definitions."""
        assert len(self.catalog.pitfalls) == 8

    def test_all_ids_present(self) -> None:
        """Every PitfallID is represented in catalog."""
        loaded_ids = {p.id for p in self.catalog.pitfalls}
        for pid in PitfallID:
            assert pid in loaded_ids, f"Missing {pid}"

    def test_pitfall_severities(self) -> None:
        """Each pitfall has the correct severity from manuscript."""
        expected_severities = {
            PitfallID.IMPLICIT_TRUST: 5,
            PitfallID.SECURITY_AFTERTHOUGHT: 5,
            PitfallID.UNCALIBRATED_THRESHOLDS: 4,
            PitfallID.INDIVIDUAL_ONLY: 4,
            PitfallID.STATIC_TRIPWIRES: 4,
            PitfallID.IGNORING_DRIFT: 3,
            PitfallID.INSUFFICIENT_LOGGING: 3,
            PitfallID.SINGLE_ORCHESTRATOR: 2,
        }
        for pid, severity in expected_severities.items():
            pitfall = self.catalog.get_by_id(pid)
            assert pitfall.severity == severity, (
                f"{pid.value} expected severity {severity}, got {pitfall.severity}"
            )

    def test_pitfall_categories(self) -> None:
        """Each pitfall has the correct category from manuscript."""
        expected_categories = {
            PitfallID.IMPLICIT_TRUST: PitfallCategory.SECURITY,
            PitfallID.SECURITY_AFTERTHOUGHT: PitfallCategory.SECURITY,
            PitfallID.UNCALIBRATED_THRESHOLDS: PitfallCategory.OPERATIONAL,
            PitfallID.INDIVIDUAL_ONLY: PitfallCategory.SECURITY,
            PitfallID.STATIC_TRIPWIRES: PitfallCategory.DESIGN,
            PitfallID.IGNORING_DRIFT: PitfallCategory.OPERATIONAL,
            PitfallID.INSUFFICIENT_LOGGING: PitfallCategory.OPERATIONAL,
            PitfallID.SINGLE_ORCHESTRATOR: PitfallCategory.DESIGN,
        }
        for pid, category in expected_categories.items():
            pitfall = self.catalog.get_by_id(pid)
            assert pitfall.category == category

    def test_each_pitfall_has_indicators(self) -> None:
        """Every pitfall has at least one indicator."""
        for p in self.catalog.pitfalls:
            assert len(p.indicators) >= 1, f"{p.id.value} has no indicators"

    def test_each_pitfall_has_mitigations(self) -> None:
        """Every pitfall has at least one mitigation."""
        for p in self.catalog.pitfalls:
            assert len(p.mitigations) >= 1, f"{p.id.value} has no mitigations"

    def test_each_pitfall_has_manuscript_reference(self) -> None:
        """Every pitfall references the manuscript."""
        for p in self.catalog.pitfalls:
            assert p.manuscript_reference.startswith("Section 07")

    def test_get_by_id_valid(self) -> None:
        """get_by_id returns correct pitfall."""
        p = self.catalog.get_by_id(PitfallID.IMPLICIT_TRUST)
        assert p.name == "Implicit Trust"

    def test_get_by_id_all_ids(self) -> None:
        """get_by_id works for every PitfallID."""
        for pid in PitfallID:
            p = self.catalog.get_by_id(pid)
            assert p.id == pid

    def test_get_by_id_invalid_raises(self) -> None:
        """get_by_id raises ValueError for unknown ID."""
        # Remove all pitfalls to force failure
        self.catalog.pitfalls.clear()
        with pytest.raises(ValueError, match="not found"):
            self.catalog.get_by_id(PitfallID.IMPLICIT_TRUST)

    def test_get_by_category_security(self) -> None:
        """get_by_category returns all security pitfalls."""
        security = self.catalog.get_by_category(PitfallCategory.SECURITY)
        assert len(security) == 3
        for p in security:
            assert p.category == PitfallCategory.SECURITY

    def test_get_by_category_operational(self) -> None:
        """get_by_category returns all operational pitfalls."""
        operational = self.catalog.get_by_category(PitfallCategory.OPERATIONAL)
        assert len(operational) == 3
        for p in operational:
            assert p.category == PitfallCategory.OPERATIONAL

    def test_get_by_category_design(self) -> None:
        """get_by_category returns all design pitfalls."""
        design = self.catalog.get_by_category(PitfallCategory.DESIGN)
        assert len(design) == 2
        for p in design:
            assert p.category == PitfallCategory.DESIGN

    def test_get_by_severity_all(self) -> None:
        """get_by_severity(1) returns all pitfalls sorted by severity desc."""
        result = self.catalog.get_by_severity(1)
        assert len(result) == 8
        severities = [p.severity for p in result]
        assert severities == sorted(severities, reverse=True)

    def test_get_by_severity_threshold_4(self) -> None:
        """get_by_severity(4) returns severity 4 and 5 only."""
        result = self.catalog.get_by_severity(4)
        assert len(result) == 5
        for p in result:
            assert p.severity >= 4

    def test_get_by_severity_threshold_5(self) -> None:
        """get_by_severity(5) returns only severity-5 pitfalls."""
        result = self.catalog.get_by_severity(5)
        assert len(result) == 2
        for p in result:
            assert p.severity == 5

    def test_get_by_severity_threshold_too_high(self) -> None:
        """get_by_severity(6) returns empty list."""
        result = self.catalog.get_by_severity(6)
        assert result == []

    def test_get_critical(self) -> None:
        """get_critical returns severity-5 pitfalls."""
        critical = self.catalog.get_critical()
        assert len(critical) == 2
        ids = {p.id for p in critical}
        assert PitfallID.IMPLICIT_TRUST in ids
        assert PitfallID.SECURITY_AFTERTHOUGHT in ids


# =============================================================================
# PitfallDetector Tests
# =============================================================================


class TestPitfallDetector:
    """Tests for PitfallDetector."""

    def setup_method(self) -> None:
        """Create a fresh detector for each test."""
        self.detector = PitfallDetector()

    def test_default_catalog(self) -> None:
        """Detector creates its own catalog by default."""
        assert len(self.detector.catalog.pitfalls) == 8

    def test_custom_catalog(self) -> None:
        """Detector accepts a custom catalog."""
        custom = PitfallCatalog()
        custom.pitfalls = custom.pitfalls[:3]
        detector = PitfallDetector(catalog=custom)
        assert len(detector.catalog.pitfalls) == 3

    def test_check_indicators_valid(self) -> None:
        """check_indicators sets indicator status correctly."""
        result = self.detector.check_indicators(
            PitfallID.IMPLICIT_TRUST,
            {0: True, 2: True},
        )
        assert result.indicators[0].present is True
        assert result.indicators[1].present is False
        assert result.indicators[2].present is True

    def test_check_indicators_all_false(self) -> None:
        """check_indicators can set all to False."""
        result = self.detector.check_indicators(
            PitfallID.IMPLICIT_TRUST,
            {0: False, 1: False, 2: False},
        )
        for ind in result.indicators:
            assert ind.present is False

    def test_check_indicators_invalid_index_negative(self) -> None:
        """check_indicators raises on negative index."""
        with pytest.raises(ValueError, match="out of range"):
            self.detector.check_indicators(
                PitfallID.IMPLICIT_TRUST,
                {-1: True},
            )

    def test_check_indicators_invalid_index_too_high(self) -> None:
        """check_indicators raises on index beyond indicator count."""
        with pytest.raises(ValueError, match="out of range"):
            self.detector.check_indicators(
                PitfallID.IMPLICIT_TRUST,
                {99: True},
            )

    def test_detect_pitfall_present(self) -> None:
        """detect_pitfall returns True when any indicator is present."""
        pitfall = self.detector.check_indicators(
            PitfallID.IMPLICIT_TRUST,
            {1: True},
        )
        assert self.detector.detect_pitfall(pitfall) is True

    def test_detect_pitfall_absent(self) -> None:
        """detect_pitfall returns False when no indicators present."""
        pitfall = self.detector.catalog.get_by_id(PitfallID.IMPLICIT_TRUST)
        assert self.detector.detect_pitfall(pitfall) is False

    def test_detect_pitfall_all_present(self) -> None:
        """detect_pitfall returns True when all indicators present."""
        pitfall = self.detector.check_indicators(
            PitfallID.IMPLICIT_TRUST,
            {0: True, 1: True, 2: True},
        )
        assert self.detector.detect_pitfall(pitfall) is True

    def test_scan_all_empty(self) -> None:
        """scan_all returns empty list when nothing is detected."""
        result = self.detector.scan_all()
        assert result == []

    def test_scan_all_with_detections(self) -> None:
        """scan_all returns pitfalls with indicators set."""
        self.detector.check_indicators(PitfallID.IMPLICIT_TRUST, {0: True})
        self.detector.check_indicators(PitfallID.STATIC_TRIPWIRES, {1: True})
        result = self.detector.scan_all()
        assert len(result) == 2
        detected_ids = {p.id for p in result}
        assert PitfallID.IMPLICIT_TRUST in detected_ids
        assert PitfallID.STATIC_TRIPWIRES in detected_ids

    def test_scan_all_only_flagged(self) -> None:
        """scan_all excludes pitfalls with no indicators set."""
        self.detector.check_indicators(PitfallID.IGNORING_DRIFT, {0: True})
        result = self.detector.scan_all()
        assert len(result) == 1
        assert result[0].id == PitfallID.IGNORING_DRIFT


# =============================================================================
# PitfallChecklistEntry Tests
# =============================================================================


class TestPitfallChecklistEntry:
    """Tests for PitfallChecklistEntry dataclass."""

    def test_defaults(self) -> None:
        """Default flags are all False."""
        entry = PitfallChecklistEntry(
            pitfall_id=PitfallID.IMPLICIT_TRUST,
            pitfall_name="Implicit Trust",
        )
        assert entry.assessed is False
        assert entry.detected is False
        assert entry.mitigated is False

    def test_custom_values(self) -> None:
        """Can set all flags."""
        entry = PitfallChecklistEntry(
            pitfall_id=PitfallID.IMPLICIT_TRUST,
            pitfall_name="Implicit Trust",
            assessed=True,
            detected=True,
            mitigated=True,
        )
        assert entry.assessed is True
        assert entry.detected is True
        assert entry.mitigated is True


# =============================================================================
# PitfallChecklist Tests
# =============================================================================


class TestPitfallChecklist:
    """Tests for PitfallChecklist."""

    def setup_method(self) -> None:
        """Create a fresh checklist for each test."""
        self.checklist = PitfallChecklist()

    def test_entries_created_for_all_pitfalls(self) -> None:
        """Checklist creates entries for all 8 pitfalls."""
        assert len(self.checklist.entries) == 8

    def test_entries_initially_unassessed(self) -> None:
        """All entries start as unassessed."""
        for entry in self.checklist.entries:
            assert entry.assessed is False
            assert entry.detected is False
            assert entry.mitigated is False

    def test_assess_valid_pitfall(self) -> None:
        """assess() marks pitfall as assessed and detected."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        entry = next(e for e in self.checklist.entries if e.pitfall_id == PitfallID.IMPLICIT_TRUST)
        assert entry.assessed is True
        assert entry.detected is True
        assert entry.mitigated is False

    def test_assess_with_mitigation(self) -> None:
        """assess() can mark pitfall as mitigated."""
        self.checklist.assess(
            PitfallID.STATIC_TRIPWIRES,
            detected=True,
            mitigated=True,
        )
        entry = next(
            e for e in self.checklist.entries if e.pitfall_id == PitfallID.STATIC_TRIPWIRES
        )
        assert entry.assessed is True
        assert entry.detected is True
        assert entry.mitigated is True

    def test_assess_not_detected(self) -> None:
        """assess() can mark pitfall as not detected."""
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=False)
        entry = next(e for e in self.checklist.entries if e.pitfall_id == PitfallID.IGNORING_DRIFT)
        assert entry.assessed is True
        assert entry.detected is False

    def test_assess_invalid_pitfall_raises(self) -> None:
        """assess() raises ValueError for unknown pitfall."""
        # Clear entries to force failure
        self.checklist.entries.clear()
        with pytest.raises(ValueError, match="not in checklist"):
            self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)

    def test_get_unassessed_initially_all(self) -> None:
        """get_unassessed returns all 8 when none assessed."""
        assert len(self.checklist.get_unassessed()) == 8

    def test_get_unassessed_after_some_assessed(self) -> None:
        """get_unassessed returns only unassessed after partial assessment."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=False)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=False)
        unassessed = self.checklist.get_unassessed()
        assert len(unassessed) == 6

    def test_get_unassessed_after_all_assessed(self) -> None:
        """get_unassessed returns empty when all assessed."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        assert self.checklist.get_unassessed() == []

    def test_get_detected_unmitigated_empty(self) -> None:
        """get_detected_unmitigated is empty when nothing detected."""
        assert self.checklist.get_detected_unmitigated() == []

    def test_get_detected_unmitigated_with_detections(self) -> None:
        """get_detected_unmitigated returns detected-but-unmitigated."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True, mitigated=True)
        result = self.checklist.get_detected_unmitigated()
        assert len(result) == 1
        assert result[0].pitfall_id == PitfallID.IMPLICIT_TRUST

    def test_get_detected_unmitigated_all_mitigated(self) -> None:
        """get_detected_unmitigated is empty when all detected are mitigated."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True, mitigated=True)
        self.checklist.assess(PitfallID.STATIC_TRIPWIRES, detected=True, mitigated=True)
        assert self.checklist.get_detected_unmitigated() == []

    def test_all_assessed_false_initially(self) -> None:
        """all_assessed is False when nothing assessed."""
        assert self.checklist.all_assessed() is False

    def test_all_assessed_partial(self) -> None:
        """all_assessed is False with partial assessment."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=False)
        assert self.checklist.all_assessed() is False

    def test_all_assessed_complete(self) -> None:
        """all_assessed is True when all are assessed."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        assert self.checklist.all_assessed() is True

    def test_all_mitigated_no_detections(self) -> None:
        """all_mitigated is True when nothing is detected."""
        assert self.checklist.all_mitigated() is True

    def test_all_mitigated_with_unmitigated(self) -> None:
        """all_mitigated is False with unmitigated detections."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        assert self.checklist.all_mitigated() is False

    def test_all_mitigated_all_handled(self) -> None:
        """all_mitigated is True when all detected pitfalls are mitigated."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True, mitigated=True)
        self.checklist.assess(PitfallID.STATIC_TRIPWIRES, detected=True, mitigated=True)
        assert self.checklist.all_mitigated() is True


# =============================================================================
# PitfallChecklist.evaluate() Tests
# =============================================================================


class TestPitfallChecklistEvaluate:
    """Tests for PitfallChecklist.evaluate() method."""

    def setup_method(self) -> None:
        """Create a fresh checklist for each test."""
        self.checklist = PitfallChecklist()

    def test_evaluate_all_clean(self) -> None:
        """All assessed, none detected: passed=True, LOW risk."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        result = self.checklist.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
        assert result.findings == []

    def test_evaluate_critical_unmitigated(self) -> None:
        """Severity-5 unmitigated: risk=CRITICAL."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        result = self.checklist.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL

    def test_evaluate_high_unmitigated(self) -> None:
        """Severity-4 unmitigated: risk=HIGH."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        # Reset one as detected
        self.checklist.assess(PitfallID.UNCALIBRATED_THRESHOLDS, detected=True)
        result = self.checklist.evaluate()
        assert result.risk_level == RiskLevel.HIGH

    def test_evaluate_medium_unmitigated(self) -> None:
        """Severity-3 unmitigated: risk=MEDIUM."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)
        result = self.checklist.evaluate()
        assert result.risk_level == RiskLevel.MEDIUM

    def test_evaluate_low_unmitigated(self) -> None:
        """Severity-2 unmitigated: risk=LOW."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        self.checklist.assess(PitfallID.SINGLE_ORCHESTRATOR, detected=True)
        result = self.checklist.evaluate()
        assert result.risk_level == RiskLevel.LOW

    def test_evaluate_score_reflects_assessment_coverage(self) -> None:
        """Score = assessed_count / total_count."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=False)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=False)
        result = self.checklist.evaluate()
        assert result.score == pytest.approx(2.0 / 8.0)

    def test_evaluate_findings_include_detected(self) -> None:
        """Findings list detected unmitigated pitfalls."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        result = self.checklist.evaluate()
        assert any("Implicit Trust" in f for f in result.findings)

    def test_evaluate_findings_include_unassessed(self) -> None:
        """Findings list unassessed pitfalls."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=False)
        result = self.checklist.evaluate()
        assert any("Not assessed" in f for f in result.findings)

    def test_evaluate_recommendations_from_mitigations(self) -> None:
        """Recommendations come from unimplemented mitigations."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        result = self.checklist.evaluate()
        assert len(result.recommendations) > 0
        assert any("Implicit Trust" in r for r in result.recommendations)

    def test_evaluate_passed_requires_all_assessed(self) -> None:
        """passed=False if not all assessed, even if no detections."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=False)
        result = self.checklist.evaluate()
        assert result.passed is False

    def test_evaluate_passed_requires_no_unmitigated(self) -> None:
        """passed=False if detected pitfalls are unmitigated."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        self.checklist.assess(PitfallID.SINGLE_ORCHESTRATOR, detected=True)
        result = self.checklist.evaluate()
        assert result.passed is False

    def test_evaluate_empty_entries(self) -> None:
        """Edge case: empty entries list returns clean result."""
        self.checklist.entries.clear()
        result = self.checklist.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW

    def test_evaluate_returns_assessment_result_type(self) -> None:
        """evaluate() returns an AssessmentResult instance."""
        result = self.checklist.evaluate()
        assert isinstance(result, AssessmentResult)


# =============================================================================
# RemediationPlan Tests
# =============================================================================


class TestRemediationStep:
    """Tests for RemediationStep dataclass."""

    def test_defaults(self) -> None:
        """Default completed=False."""
        step = RemediationStep(
            pitfall_id=PitfallID.IMPLICIT_TRUST,
            action="Add trust scoring",
            priority=1,
        )
        assert step.completed is False

    def test_custom_values(self) -> None:
        """Can set completed=True."""
        step = RemediationStep(
            pitfall_id=PitfallID.IMPLICIT_TRUST,
            action="Add trust scoring",
            priority=1,
            completed=True,
        )
        assert step.completed is True


class TestRemediationPlan:
    """Tests for RemediationPlan dataclass."""

    def test_defaults(self) -> None:
        """Default is empty plan."""
        plan = RemediationPlan()
        assert plan.steps == []
        assert plan.total_pitfalls == 0
        assert plan.critical_count == 0

    def test_completed_steps_none(self) -> None:
        """completed_steps returns 0 when none completed."""
        plan = RemediationPlan(
            steps=[
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 1", 1),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 2", 2),
            ]
        )
        assert plan.completed_steps() == 0

    def test_completed_steps_some(self) -> None:
        """completed_steps counts completed steps."""
        plan = RemediationPlan(
            steps=[
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 1", 1, completed=True),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 2", 2),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 3", 3, completed=True),
            ]
        )
        assert plan.completed_steps() == 2

    def test_progress_empty(self) -> None:
        """progress returns 1.0 for empty plan."""
        plan = RemediationPlan()
        assert plan.progress() == 1.0

    def test_progress_none_done(self) -> None:
        """progress returns 0.0 when nothing completed."""
        plan = RemediationPlan(
            steps=[
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 1", 1),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 2", 2),
            ]
        )
        assert plan.progress() == pytest.approx(0.0)

    def test_progress_half_done(self) -> None:
        """progress returns 0.5 when half completed."""
        plan = RemediationPlan(
            steps=[
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 1", 1, completed=True),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 2", 2),
            ]
        )
        assert plan.progress() == pytest.approx(0.5)

    def test_progress_all_done(self) -> None:
        """progress returns 1.0 when all completed."""
        plan = RemediationPlan(
            steps=[
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 1", 1, completed=True),
                RemediationStep(PitfallID.IMPLICIT_TRUST, "Step 2", 2, completed=True),
            ]
        )
        assert plan.progress() == pytest.approx(1.0)


# =============================================================================
# generate_remediation_plan Tests
# =============================================================================


class TestGenerateRemediationPlan:
    """Tests for generate_remediation_plan function."""

    def setup_method(self) -> None:
        """Create a fresh checklist for each test."""
        self.checklist = PitfallChecklist()

    def test_no_detections(self) -> None:
        """No detected pitfalls produces empty plan."""
        for pid in PitfallID:
            self.checklist.assess(pid, detected=False)
        plan = generate_remediation_plan(self.checklist)
        assert plan.steps == []
        assert plan.total_pitfalls == 0
        assert plan.critical_count == 0

    def test_single_detection(self) -> None:
        """Single detection produces steps from its mitigations."""
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)
        plan = generate_remediation_plan(self.checklist)
        assert plan.total_pitfalls == 1
        assert plan.critical_count == 0
        # Ignoring Drift has 4 mitigations
        assert len(plan.steps) == 4
        for step in plan.steps:
            assert step.pitfall_id == PitfallID.IGNORING_DRIFT

    def test_critical_count(self) -> None:
        """Critical count reflects severity-5 pitfalls."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        self.checklist.assess(PitfallID.SECURITY_AFTERTHOUGHT, detected=True)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)
        plan = generate_remediation_plan(self.checklist)
        assert plan.critical_count == 2
        assert plan.total_pitfalls == 3

    def test_priority_ordering(self) -> None:
        """Steps are ordered by severity (highest first)."""
        self.checklist.assess(PitfallID.SINGLE_ORCHESTRATOR, detected=True)  # sev 2
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)  # sev 5
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)  # sev 3
        plan = generate_remediation_plan(self.checklist)
        # First steps should be from IMPLICIT_TRUST (severity 5)
        assert plan.steps[0].pitfall_id == PitfallID.IMPLICIT_TRUST
        # Last steps should be from SINGLE_ORCHESTRATOR (severity 2)
        assert plan.steps[-1].pitfall_id == PitfallID.SINGLE_ORCHESTRATOR

    def test_priorities_are_sequential(self) -> None:
        """Priority numbers increment from 1."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)
        plan = generate_remediation_plan(self.checklist)
        priorities = [s.priority for s in plan.steps]
        assert priorities == list(range(1, len(plan.steps) + 1))

    def test_steps_initially_not_completed(self) -> None:
        """Generated steps start as not completed."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        plan = generate_remediation_plan(self.checklist)
        for step in plan.steps:
            assert step.completed is False

    def test_mitigated_pitfalls_excluded(self) -> None:
        """Mitigated pitfalls do not generate remediation steps."""
        self.checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True, mitigated=True)
        self.checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)
        plan = generate_remediation_plan(self.checklist)
        pitfall_ids_in_plan = {s.pitfall_id for s in plan.steps}
        assert PitfallID.IMPLICIT_TRUST not in pitfall_ids_in_plan
        assert PitfallID.IGNORING_DRIFT in pitfall_ids_in_plan

    def test_all_mitigations_become_steps(self) -> None:
        """Each unimplemented mitigation becomes a remediation step."""
        self.checklist.assess(PitfallID.STATIC_TRIPWIRES, detected=True)
        plan = generate_remediation_plan(self.checklist)
        pitfall = self.checklist.catalog.get_by_id(PitfallID.STATIC_TRIPWIRES)
        expected_count = sum(1 for m in pitfall.mitigations if not m.implemented)
        assert len(plan.steps) == expected_count


# =============================================================================
# Edge Case & Integration Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and integration tests."""

    def test_catalog_pitfalls_have_unique_ids(self) -> None:
        """No duplicate IDs in catalog."""
        catalog = PitfallCatalog()
        ids = [p.id for p in catalog.pitfalls]
        assert len(ids) == len(set(ids))

    def test_catalog_pitfalls_have_unique_names(self) -> None:
        """No duplicate names in catalog."""
        catalog = PitfallCatalog()
        names = [p.name for p in catalog.pitfalls]
        assert len(names) == len(set(names))

    def test_detector_shares_catalog_state(self) -> None:
        """Detector mutations affect the shared catalog."""
        catalog = PitfallCatalog()
        detector = PitfallDetector(catalog=catalog)
        detector.check_indicators(PitfallID.IMPLICIT_TRUST, {0: True})
        pitfall = catalog.get_by_id(PitfallID.IMPLICIT_TRUST)
        assert pitfall.indicators[0].present is True

    def test_full_workflow(self) -> None:
        """End-to-end: detect -> assess -> remediate."""
        # Step 1: Detect pitfalls
        detector = PitfallDetector()
        detector.check_indicators(PitfallID.IMPLICIT_TRUST, {0: True, 1: True})
        detector.check_indicators(PitfallID.STATIC_TRIPWIRES, {0: True})
        detected = detector.scan_all()
        assert len(detected) == 2

        # Step 2: Assess via checklist
        checklist = PitfallChecklist(catalog=detector.catalog)
        for pitfall in detected:
            checklist.assess(pitfall.id, detected=True)
        for pid in PitfallID:
            entry = next((e for e in checklist.entries if e.pitfall_id == pid), None)
            if entry and not entry.assessed:
                checklist.assess(pid, detected=False)
        assert checklist.all_assessed() is True
        assert checklist.all_mitigated() is False

        # Step 3: Evaluate
        result = checklist.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL  # IMPLICIT_TRUST is sev 5

        # Step 4: Generate remediation plan
        plan = generate_remediation_plan(checklist)
        assert plan.total_pitfalls == 2
        assert plan.critical_count == 1
        assert len(plan.steps) > 0
        # Highest severity steps come first
        assert plan.steps[0].pitfall_id == PitfallID.IMPLICIT_TRUST

    def test_checklist_with_custom_catalog(self) -> None:
        """Checklist works with a custom (reduced) catalog."""
        catalog = PitfallCatalog()
        catalog.pitfalls = catalog.pitfalls[:2]
        checklist = PitfallChecklist(catalog=catalog)
        assert len(checklist.entries) == 2

    def test_severity_boundary_values(self) -> None:
        """Severity boundaries map correctly in evaluate."""
        checklist = PitfallChecklist()
        # Only severity-2 detected -> LOW
        for pid in PitfallID:
            checklist.assess(pid, detected=False)
        checklist.assess(PitfallID.SINGLE_ORCHESTRATOR, detected=True)  # sev 2
        result = checklist.evaluate()
        assert result.risk_level == RiskLevel.LOW

    def test_multiple_categories_detected(self) -> None:
        """Detect pitfalls from all three categories simultaneously."""
        checklist = PitfallChecklist()
        checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)  # security
        checklist.assess(PitfallID.IGNORING_DRIFT, detected=True)  # operational
        checklist.assess(PitfallID.STATIC_TRIPWIRES, detected=True)  # design
        result = checklist.evaluate()
        assert result.risk_level == RiskLevel.CRITICAL
        assert len(result.findings) >= 3  # at least 3 detected + unassessed
