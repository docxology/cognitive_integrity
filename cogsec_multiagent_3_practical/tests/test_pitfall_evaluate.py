"""Tests for PitfallChecklist.evaluate risk surfacing (m7).

Verifies that unassessed pitfalls are surfaced honestly instead of being
ignored (which previously under-reported risk to LOW).
"""

from src import RiskLevel
from src.pitfalls import PitfallChecklist, PitfallID


class TestEvaluateRiskSurfacing:
    """evaluate() must consider unassessed pitfalls (m7)."""

    def test_fresh_checklist_not_passed_and_not_low(self) -> None:
        """A completely unevaluated checklist must not report LOW."""
        checklist = PitfallChecklist()
        result = checklist.evaluate()
        assert result.passed is False
        assert result.score == 0.0
        # Severity-5 pitfalls (Implicit Trust, Security as Afterthought) are
        # unassessed -> the checklist must surface at least HIGH.
        assert result.risk_level == RiskLevel.CRITICAL

    def test_unassessed_critical_severity_surfaced(self) -> None:
        """Leaving a severity-5 pitfall unassessed keeps risk at CRITICAL."""
        checklist = PitfallChecklist()
        for pid in PitfallID:
            if pid != PitfallID.IMPLICIT_TRUST:
                checklist.assess(pid, detected=False)
        result = checklist.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert any("Not assessed" in f for f in result.findings)

    def test_unassessed_medium_severity_raises_from_low(self) -> None:
        """Before m7 an unassessed severity-3 pitfall still reported LOW."""
        checklist = PitfallChecklist()
        for pid in PitfallID:
            if pid != PitfallID.INSUFFICIENT_LOGGING:
                checklist.assess(pid, detected=False)
        result = checklist.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.MEDIUM

    def test_all_assessed_clean_reports_low(self) -> None:
        """A fully assessed, nothing-detected checklist reports LOW and passes."""
        checklist = PitfallChecklist()
        for pid in PitfallID:
            checklist.assess(pid, detected=False)
        result = checklist.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
        assert result.findings == []

    def test_detected_unmitigated_drives_risk(self) -> None:
        """A confirmed unmitigated severity-5 pitfall is CRITICAL."""
        checklist = PitfallChecklist()
        for pid in PitfallID:
            checklist.assess(pid, detected=False)
        checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True)
        result = checklist.evaluate()
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert any("Detected" in f for f in result.findings)
        assert result.recommendations

    def test_detected_mitigated_clean(self) -> None:
        """A detected-but-mitigated pitfall is not an open risk."""
        checklist = PitfallChecklist()
        for pid in PitfallID:
            checklist.assess(pid, detected=False)
        checklist.assess(PitfallID.IMPLICIT_TRUST, detected=True, mitigated=True)
        result = checklist.evaluate()
        assert result.passed is True
        assert result.risk_level == RiskLevel.LOW

    def test_empty_entries_passthrough(self) -> None:
        """Empty checklist short-circuits to passed/LOW (unchanged behaviour)."""
        checklist = PitfallChecklist()
        checklist.entries.clear()
        result = checklist.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
