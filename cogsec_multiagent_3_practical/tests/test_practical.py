"""Tests for the practical implementation modules.

Tests cover:
- OperatorPostureAssessment functionality
- DeploymentReadinessCheck validation
- RiskAssessmentTool calculations
- ChecklistItem and AssessmentResult data classes
"""

from src import (
    AssessmentResult,
    ChecklistItem,
    DeploymentReadinessCheck,
    OperatorPostureAssessment,
    PostureLevel,
    RiskAssessmentTool,
    RiskLevel,
)


class TestChecklistItem:
    """Tests for ChecklistItem dataclass."""

    def test_create_checklist_item(self):
        """Test basic checklist item creation."""
        item = ChecklistItem(
            id="test-001",
            category="testing",
            description="Test item description",
        )
        assert item.id == "test-001"
        assert item.category == "testing"
        assert item.description == "Test item description"
        assert item.required is True
        assert item.completed is False
        assert item.notes == ""

    def test_optional_checklist_item(self):
        """Test optional checklist item."""
        item = ChecklistItem(
            id="opt-001",
            category="optional",
            description="Optional item",
            required=False,
        )
        assert item.required is False


class TestOperatorPostureAssessment:
    """Tests for OperatorPostureAssessment."""

    def test_empty_checklist_evaluation(self):
        """Test evaluation with empty checklist."""
        assessment = OperatorPostureAssessment()
        result = assessment.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW

    def test_full_compliance(self, sample_checklist_items):
        """Test full compliance scenario."""
        assessment = OperatorPostureAssessment(PostureLevel.STANDARD)
        for item in sample_checklist_items:
            item.completed = True
            assessment.add_check(item)
        result = assessment.evaluate()
        assert result.passed is True
        assert result.score == 1.0
        assert result.risk_level == RiskLevel.LOW
        assert len(result.findings) == 0

    def test_partial_compliance(self, sample_checklist_items):
        """Test partial compliance scenario."""
        assessment = OperatorPostureAssessment()
        # Complete only first required item
        sample_checklist_items[0].completed = True
        for item in sample_checklist_items:
            assessment.add_check(item)
        result = assessment.evaluate()
        # 1 out of 2 required items = 0.5, which is < 0.6 = CRITICAL
        assert result.score == 0.5
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL

    def test_high_compliance_passes(self, sample_checklist_items):
        """Test that 80%+ compliance passes."""
        assessment = OperatorPostureAssessment()
        # Complete all required items
        sample_checklist_items[0].completed = True
        sample_checklist_items[1].completed = True
        for item in sample_checklist_items:
            assessment.add_check(item)
        result = assessment.evaluate()
        assert result.passed is True
        assert result.score == 1.0

    def test_posture_level_initialization(self):
        """Test posture level initialization."""
        minimal = OperatorPostureAssessment(PostureLevel.MINIMAL)
        assert minimal.posture_level == PostureLevel.MINIMAL

        maximum = OperatorPostureAssessment(PostureLevel.MAXIMUM)
        assert maximum.posture_level == PostureLevel.MAXIMUM


class TestDeploymentReadinessCheck:
    """Tests for DeploymentReadinessCheck."""

    def test_empty_checks_not_ready(self):
        """Test empty checks returns not ready."""
        checker = DeploymentReadinessCheck()
        assert checker.is_ready() is False

    def test_all_passed_is_ready(self):
        """Test all passed checks returns ready."""
        checker = DeploymentReadinessCheck()
        checker.add_check("trust_configured", True)
        checker.add_check("firewall_enabled", True)
        checker.add_check("monitoring_active", True)
        assert checker.is_ready() is True
        assert len(checker.get_failures()) == 0

    def test_partial_failure(self):
        """Test partial failures."""
        checker = DeploymentReadinessCheck()
        checker.add_check("trust_configured", True)
        checker.add_check("firewall_enabled", False)
        checker.add_check("monitoring_active", True)
        assert checker.is_ready() is False
        failures = checker.get_failures()
        assert len(failures) == 1
        assert "firewall_enabled" in failures


class TestRiskAssessmentTool:
    """Tests for RiskAssessmentTool."""

    def test_empty_assessment_low_risk(self):
        """Test empty assessment returns low risk."""
        tool = RiskAssessmentTool()
        assert tool.calculate_overall_risk() == RiskLevel.LOW

    def test_low_severity_low_likelihood(self):
        """Test low severity and likelihood."""
        tool = RiskAssessmentTool()
        tool.add_risk_factor("minor_issue", RiskLevel.LOW, 0.1)
        assert tool.calculate_overall_risk() == RiskLevel.LOW

    def test_critical_severity_high_likelihood(self):
        """Test critical severity and high likelihood."""
        tool = RiskAssessmentTool()
        tool.add_risk_factor("critical_vulnerability", RiskLevel.CRITICAL, 0.9)
        assert tool.calculate_overall_risk() == RiskLevel.CRITICAL

    def test_mixed_risk_factors(self):
        """Test mixed risk factors calculation."""
        tool = RiskAssessmentTool()
        tool.add_risk_factor("low_issue", RiskLevel.LOW, 0.3)
        tool.add_risk_factor("medium_issue", RiskLevel.MEDIUM, 0.5)
        tool.add_risk_factor("high_issue", RiskLevel.HIGH, 0.2)
        result = tool.calculate_overall_risk()
        assert result in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_risk_factor_with_description(self):
        """Test adding risk factor with description."""
        tool = RiskAssessmentTool()
        tool.add_risk_factor(
            "privilege_escalation",
            RiskLevel.HIGH,
            0.4,
            "Agent may gain unauthorized access",
        )
        assert len(tool.risk_factors) == 1
        assert tool.risk_factors[0]["description"] == "Agent may gain unauthorized access"


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test risk level enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestPostureLevel:
    """Tests for PostureLevel enum."""

    def test_posture_level_values(self):
        """Test posture level enum values."""
        assert PostureLevel.MINIMAL.value == "minimal"
        assert PostureLevel.STANDARD.value == "standard"
        assert PostureLevel.ELEVATED.value == "elevated"
        assert PostureLevel.MAXIMUM.value == "maximum"


class TestAssessmentResult:
    """Tests for AssessmentResult dataclass."""

    def test_assessment_result_defaults(self):
        """Test assessment result default values."""
        result = AssessmentResult(passed=True, score=0.95, risk_level=RiskLevel.LOW)
        assert result.findings == []
        assert result.recommendations == []

    def test_assessment_result_with_findings(self):
        """Test assessment result with findings."""
        result = AssessmentResult(
            passed=False,
            score=0.6,
            risk_level=RiskLevel.HIGH,
            findings=["Missing firewall", "No monitoring"],
            recommendations=["Enable firewall", "Setup monitoring"],
        )
        assert len(result.findings) == 2
        assert len(result.recommendations) == 2
