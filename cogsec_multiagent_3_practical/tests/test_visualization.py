#!/usr/bin/env python3
"""Tests for visualization module.

Comprehensive tests targeting 90%+ coverage.
All tests use real data - no mocks.
"""

import pytest
from matplotlib import pyplot as plt

from src.visualization import (
    DeploymentPhase,
    FigureData,
    FigureType,
    Pitfall,
    TimelinePhase,
    get_deployment_phases_data,
    get_five_pillars_data,
    get_pitfalls_data,
    get_risk_matrix_data,
    get_timeline_data,
    get_trust_decay_data,
    render_checklist_flowchart,
    render_pitfall_severity,
    render_posture_radar,
    render_risk_matrix,
    render_timeline,
    render_trust_decay,
)

# =============================================================================
# Data Class Tests
# =============================================================================


class TestFigureData:
    """Tests for FigureData dataclass."""

    def test_figure_data_creation(self) -> None:
        """Test basic FigureData creation."""
        data = FigureData(
            figure_type=FigureType.RADAR,
            title="Test Figure",
            data={"key": "value"},
        )
        assert data.figure_type == FigureType.RADAR
        assert data.title == "Test Figure"
        assert data.data == {"key": "value"}
        assert data.metadata == {}

    def test_figure_data_with_metadata(self) -> None:
        """Test FigureData with metadata."""
        data = FigureData(
            figure_type=FigureType.BAR,
            title="Test",
            data={},
            metadata={"score": 0.85},
        )
        assert data.metadata == {"score": 0.85}


class TestDeploymentPhase:
    """Tests for DeploymentPhase dataclass."""

    def test_deployment_phase_creation(self) -> None:
        """Test basic DeploymentPhase creation."""
        phase = DeploymentPhase(
            name="Testing",
            checks=["Check 1", "Check 2"],
        )
        assert phase.name == "Testing"
        assert phase.checks == ["Check 1", "Check 2"]
        assert phase.status == "pending"

    def test_deployment_phase_with_status(self) -> None:
        """Test DeploymentPhase with custom status."""
        phase = DeploymentPhase(
            name="Integration",
            checks=["Setup"],
            status="complete",
        )
        assert phase.status == "complete"


class TestPitfall:
    """Tests for Pitfall dataclass."""

    def test_pitfall_creation(self) -> None:
        """Test basic Pitfall creation."""
        pitfall = Pitfall(
            name="Test Pitfall",
            severity=4,
            description="A test pitfall",
            category="security",
        )
        assert pitfall.name == "Test Pitfall"
        assert pitfall.severity == 4
        assert pitfall.description == "A test pitfall"
        assert pitfall.category == "security"


class TestTimelinePhase:
    """Tests for TimelinePhase dataclass."""

    def test_timeline_phase_creation(self) -> None:
        """Test basic TimelinePhase creation."""
        phase = TimelinePhase(
            name="Pre-Deployment",
            start=0.0,
            end=0.3,
            color="#1976d2",
            activities=["Plan", "Design"],
        )
        assert phase.name == "Pre-Deployment"
        assert phase.start == 0.0
        assert phase.end == 0.3
        assert phase.color == "#1976d2"
        assert len(phase.activities) == 2


# =============================================================================
# Five Pillars Tests
# =============================================================================


class TestFivePillarsData:
    """Tests for get_five_pillars_data."""

    def test_default_values(self) -> None:
        """Test with all default (zero) values."""
        data = get_five_pillars_data()
        assert data.figure_type == FigureType.RADAR
        assert len(data.data["pillars"]) == 5
        assert len(data.data["values"]) == 5
        assert all(v == 0.0 for v in data.data["values"])

    def test_custom_scores(self) -> None:
        """Test with custom pillar scores."""
        data = get_five_pillars_data(
            firewall_score=0.9,
            sandbox_score=0.8,
            tripwire_score=0.7,
            invariant_score=0.6,
            provenance_score=0.5,
        )
        assert data.data["values"] == [0.9, 0.8, 0.7, 0.6, 0.5]
        assert data.metadata["overall_score"] == 0.7  # (0.9+0.8+0.7+0.6+0.5)/5
        assert "Provenance" in data.metadata["weakest_pillar"]
        assert "Firewall" in data.metadata["strongest_pillar"]

    def test_invalid_score_below_zero(self) -> None:
        """Test that negative scores raise ValueError."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            get_five_pillars_data(firewall_score=-0.1)

    def test_invalid_score_above_one(self) -> None:
        """Test that scores above 1 raise ValueError."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            get_five_pillars_data(sandbox_score=1.5)

    def test_boundary_scores(self) -> None:
        """Test boundary values 0 and 1."""
        data = get_five_pillars_data(
            firewall_score=0.0,
            sandbox_score=1.0,
            tripwire_score=0.0,
            invariant_score=1.0,
            provenance_score=0.0,
        )
        assert data.data["values"] == [0.0, 1.0, 0.0, 1.0, 0.0]

    def test_thresholds_present(self) -> None:
        """Test that thresholds are included in data."""
        data = get_five_pillars_data()
        assert "thresholds" in data.data
        thresholds = data.data["thresholds"]
        assert thresholds["minimal"] == 0.25
        assert thresholds["standard"] == 0.50
        assert thresholds["elevated"] == 0.75
        assert thresholds["maximum"] == 0.90


class TestRenderPostureRadar:
    """Tests for render_posture_radar."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_five_pillars_data(firewall_score=0.5)
        fig = render_posture_radar(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_five_pillars_data(firewall_score=0.7)
        fig, ax = plt.subplots(subplot_kw=dict(projection="polar"))
        result = render_posture_radar(data, ax=ax)
        assert result is fig
        plt.close(fig)

    def test_render_all_scores_high(self) -> None:
        """Test rendering with all high scores."""
        data = get_five_pillars_data(
            firewall_score=0.95,
            sandbox_score=0.90,
            tripwire_score=0.85,
            invariant_score=0.92,
            provenance_score=0.88,
        )
        fig = render_posture_radar(data)
        # Data line + 4 threshold fills + 1 data fill (Polygon patches) (M5).
        assert len(fig.axes[0].lines) == 1
        assert len(fig.axes[0].patches) == 5
        plt.close(fig)


# =============================================================================
# Deployment Phases Tests
# =============================================================================


class TestDeploymentPhasesData:
    """Tests for get_deployment_phases_data."""

    def test_phases_structure(self) -> None:
        """Test that deployment phases have correct structure."""
        data = get_deployment_phases_data()
        assert data.figure_type == FigureType.FLOWCHART
        assert "phases" in data.data
        phases = data.data["phases"]
        assert len(phases) == 4

    def test_phase_names(self) -> None:
        """Test that phases have expected names."""
        data = get_deployment_phases_data()
        phase_names = [p.name for p in data.data["phases"]]
        assert "Pre-Deployment" in phase_names
        assert "Integration" in phase_names
        assert "Testing" in phase_names
        assert "Operational" in phase_names

    def test_each_phase_has_checks(self) -> None:
        """Test that each phase has checklist items."""
        data = get_deployment_phases_data()
        for phase in data.data["phases"]:
            assert len(phase.checks) >= 3

    def test_total_checks_count(self) -> None:
        """Test total checks count in metadata."""
        data = get_deployment_phases_data()
        assert data.data["total_checks"] == sum(len(p.checks) for p in data.data["phases"])


class TestRenderChecklistFlowchart:
    """Tests for render_checklist_flowchart."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_deployment_phases_data()
        fig = render_checklist_flowchart(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_deployment_phases_data()
        fig, ax = plt.subplots(figsize=(14, 8))
        result = render_checklist_flowchart(data, ax=ax)
        assert result is fig
        plt.close(fig)


# =============================================================================
# Risk Matrix Tests
# =============================================================================


class TestRiskMatrixData:
    """Tests for get_risk_matrix_data."""

    def test_default_risks(self) -> None:
        """Test with default risk set."""
        data = get_risk_matrix_data()
        assert data.figure_type == FigureType.HEATMAP
        assert "risks" in data.data
        assert len(data.data["risks"]) == 8

    def test_custom_risks(self) -> None:
        """Test with custom risk set."""
        custom_risks = [
            {"name": "Custom Risk 1", "impact": 3, "likelihood": 2},
            {"name": "Custom Risk 2", "impact": 5, "likelihood": 4},
        ]
        data = get_risk_matrix_data(risks=custom_risks)
        assert len(data.data["risks"]) == 2
        assert data.data["risks"][0]["name"] == "Custom Risk 1"

    def test_invalid_impact(self) -> None:
        """Test that invalid impact raises ValueError."""
        invalid_risks = [{"name": "Bad", "impact": 6, "likelihood": 3}]
        with pytest.raises(ValueError, match="Impact must be 1-5"):
            get_risk_matrix_data(risks=invalid_risks)

    def test_invalid_likelihood(self) -> None:
        """Test that invalid likelihood raises ValueError."""
        invalid_risks = [{"name": "Bad", "impact": 3, "likelihood": 0}]
        with pytest.raises(ValueError, match="Likelihood must be 1-5"):
            get_risk_matrix_data(risks=invalid_risks)

    def test_labels_present(self) -> None:
        """Test that impact and likelihood labels are present."""
        data = get_risk_matrix_data()
        assert len(data.data["impact_labels"]) == 5
        assert len(data.data["likelihood_labels"]) == 5


class TestRenderRiskMatrix:
    """Tests for render_risk_matrix."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_risk_matrix_data()
        fig = render_risk_matrix(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_custom_risks(self) -> None:
        """Test rendering with custom risks."""
        custom_risks = [
            {"name": "Low Risk", "impact": 1, "likelihood": 1},
            {"name": "High Risk", "impact": 5, "likelihood": 5},
        ]
        data = get_risk_matrix_data(risks=custom_risks)
        fig = render_risk_matrix(data)
        ax = fig.axes[0]
        # One marker line + one annotation per risk; one heatmap image (M5).
        assert len(ax.images) == 1
        assert len(ax.lines) == len(custom_risks)
        assert len(ax.texts) == len(custom_risks)
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_risk_matrix_data()
        fig, ax = plt.subplots(figsize=(12, 10))
        result = render_risk_matrix(data, ax=ax)
        assert result is fig
        plt.close(fig)


# =============================================================================
# Trust Decay Tests
# =============================================================================


class TestTrustDecayData:
    """Tests for get_trust_decay_data."""

    def test_default_parameters(self) -> None:
        """Test with default delta and max_depth."""
        data = get_trust_decay_data()
        assert data.figure_type == FigureType.CURVE
        assert data.data["delta"] == 0.85
        assert len(data.data["depths"]) == 11  # 0-10 inclusive

    def test_custom_delta(self) -> None:
        """Test with custom delta value."""
        data = get_trust_decay_data(delta=0.9)
        assert data.data["delta"] == 0.9

    def test_custom_max_depth(self) -> None:
        """Test with custom max depth."""
        data = get_trust_decay_data(max_depth=20)
        assert len(data.data["depths"]) == 21  # 0-20 inclusive

    def test_trust_decay_values(self) -> None:
        """Test that trust values decay correctly."""
        delta = 0.8
        data = get_trust_decay_data(delta=delta, max_depth=5)
        values = data.data["trust_values"]

        # Verify decay: T = δ^d
        for d, val in enumerate(values):
            expected = delta**d
            assert abs(val - expected) < 1e-10

    def test_invalid_delta_zero(self) -> None:
        """Test that delta=0 raises ValueError."""
        with pytest.raises(ValueError, match="delta must be between 0 and 1"):
            get_trust_decay_data(delta=0)

    def test_invalid_delta_one(self) -> None:
        """Test that delta=1 raises ValueError."""
        with pytest.raises(ValueError, match="delta must be between 0 and 1"):
            get_trust_decay_data(delta=1)

    def test_invalid_delta_negative(self) -> None:
        """Test that negative delta raises ValueError."""
        with pytest.raises(ValueError, match="delta must be between 0 and 1"):
            get_trust_decay_data(delta=-0.5)

    def test_metadata_practical_depth(self) -> None:
        """Test that practical depth is calculated correctly."""
        data = get_trust_decay_data(delta=0.85)
        # Practical depth is where trust < 0.1
        # 0.85^d < 0.1 => d > log(0.1)/log(0.85) ≈ 14.2
        assert data.metadata["practical_depth"] == 15

    def test_metadata_half_life(self) -> None:
        """Test that half-life depth is calculated."""
        data = get_trust_decay_data(delta=0.5)
        # Half-life at δ=0.5 should be 1 (0.5^1 = 0.5)
        assert abs(data.metadata["half_life_depth"] - 1.0) < 1e-10


class TestRenderTrustDecay:
    """Tests for render_trust_decay."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_trust_decay_data()
        fig = render_trust_decay(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_aggressive_delta(self) -> None:
        """Test rendering with aggressive (low) delta."""
        data = get_trust_decay_data(delta=0.5)
        fig = render_trust_decay(data)
        # Data line + 50%/10% hlines (plus practical-depth vline) (M5).
        assert len(fig.axes[0].lines) >= 3
        assert len(fig.axes[0].collections) >= 1  # fill_between
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_trust_decay_data()
        fig, ax = plt.subplots(figsize=(10, 6))
        result = render_trust_decay(data, ax=ax)
        assert result is fig
        plt.close(fig)


# =============================================================================
# Pitfall Tests
# =============================================================================


class TestPitfallsData:
    """Tests for get_pitfalls_data."""

    def test_pitfalls_structure(self) -> None:
        """Test that pitfalls have correct structure."""
        data = get_pitfalls_data()
        assert data.figure_type == FigureType.BAR
        assert "pitfalls" in data.data
        assert len(data.data["pitfalls"]) == 8

    def test_pitfall_severities_valid(self) -> None:
        """Test that all pitfall severities are in valid range."""
        data = get_pitfalls_data()
        for pitfall in data.data["pitfalls"]:
            assert 1 <= pitfall.severity <= 5

    def test_pitfall_categories_valid(self) -> None:
        """Test that all pitfall categories are valid."""
        valid_categories = {"security", "operational", "design"}
        data = get_pitfalls_data()
        for pitfall in data.data["pitfalls"]:
            assert pitfall.category in valid_categories

    def test_severity_labels_present(self) -> None:
        """Test that severity labels are present."""
        data = get_pitfalls_data()
        labels = data.data["severity_labels"]
        assert labels[5] == "Critical"
        assert labels[1] == "Minimal"


class TestRenderPitfallSeverity:
    """Tests for render_pitfall_severity."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_pitfalls_data()
        fig = render_pitfall_severity(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_pitfalls_data()
        fig, ax = plt.subplots(figsize=(12, 8))
        result = render_pitfall_severity(data, ax=ax)
        assert result is fig
        plt.close(fig)


# =============================================================================
# Timeline Tests
# =============================================================================


class TestTimelineData:
    """Tests for get_timeline_data."""

    def test_timeline_structure(self) -> None:
        """Test that timeline has correct structure."""
        data = get_timeline_data()
        assert data.figure_type == FigureType.TIMELINE
        assert "phases" in data.data
        assert len(data.data["phases"]) == 3

    def test_timeline_phases_ordered(self) -> None:
        """Test that timeline phases are in chronological order."""
        data = get_timeline_data()
        phases = data.data["phases"]

        # Check phases don't overlap and are sequential
        for i in range(len(phases) - 1):
            assert (
                phases[i].end <= phases[i + 1].start
                or abs(phases[i].end - phases[i + 1].start) < 0.01
            )

    def test_timeline_covers_full_range(self) -> None:
        """Test that timeline phases cover 0 to 1."""
        data = get_timeline_data()
        phases = data.data["phases"]
        assert phases[0].start == 0.0
        assert phases[-1].end == 1.0

    def test_each_phase_has_activities(self) -> None:
        """Test that each phase has activities."""
        data = get_timeline_data()
        for phase in data.data["phases"]:
            assert len(phase.activities) >= 2


class TestRenderTimeline:
    """Tests for render_timeline."""

    def test_render_creates_figure(self) -> None:
        """Test that render creates a matplotlib figure."""
        data = get_timeline_data()
        fig = render_timeline(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_render_with_provided_axes(self) -> None:
        """Test rendering onto provided axes."""
        data = get_timeline_data()
        fig, ax = plt.subplots(figsize=(14, 6))
        result = render_timeline(data, ax=ax)
        assert result is fig
        plt.close(fig)


# =============================================================================
# FigureType Enum Tests
# =============================================================================


class TestFigureType:
    """Tests for FigureType enum."""

    def test_all_figure_types_exist(self) -> None:
        """Test that all expected figure types exist."""
        expected = {"RADAR", "FLOWCHART", "HEATMAP", "CURVE", "BAR", "TIMELINE"}
        actual = {t.name for t in FigureType}
        assert expected == actual

    def test_figure_type_values(self) -> None:
        """Test figure type values."""
        assert FigureType.RADAR.value == "radar"
        assert FigureType.FLOWCHART.value == "flowchart"
        assert FigureType.HEATMAP.value == "heatmap"
        assert FigureType.CURVE.value == "curve"
        assert FigureType.BAR.value == "bar"
        assert FigureType.TIMELINE.value == "timeline"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for full figure generation workflow."""

    def test_full_workflow_posture_radar(self) -> None:
        """Test complete workflow for posture radar."""
        data = get_five_pillars_data(
            firewall_score=0.85,
            sandbox_score=0.70,
            tripwire_score=0.60,
            invariant_score=0.90,
            provenance_score=0.55,
        )
        fig = render_posture_radar(data)

        # Verify figure was created and has content
        assert len(fig.axes) > 0
        plt.close(fig)

    def test_full_workflow_risk_matrix(self) -> None:
        """Test complete workflow for risk matrix."""
        risks = [
            {"name": "Attack A", "impact": 4, "likelihood": 3},
            {"name": "Attack B", "impact": 2, "likelihood": 5},
        ]
        data = get_risk_matrix_data(risks=risks)
        fig = render_risk_matrix(data)

        assert len(fig.axes) > 0
        plt.close(fig)

    def test_full_workflow_trust_decay(self) -> None:
        """Test complete workflow for trust decay."""
        data = get_trust_decay_data(delta=0.85, max_depth=10)
        fig = render_trust_decay(data)

        assert len(fig.axes) > 0
        plt.close(fig)

    def test_multiple_figures_same_session(self) -> None:
        """Test creating multiple figures in same session."""
        figures = []

        # Create all figure types
        figures.append(render_posture_radar(get_five_pillars_data()))
        figures.append(render_checklist_flowchart(get_deployment_phases_data()))
        figures.append(render_risk_matrix(get_risk_matrix_data()))
        figures.append(render_trust_decay(get_trust_decay_data()))
        figures.append(render_pitfall_severity(get_pitfalls_data()))
        figures.append(render_timeline(get_timeline_data()))

        assert len(figures) == 6
        for fig in figures:
            assert isinstance(fig, plt.Figure)
            plt.close(fig)


# =============================================================================
# Render artist assertions (M5): figures must DRAW real artists so a silent
# data-drop (empty inputs rendering nothing) fails these tests.
# =============================================================================


class TestRenderArtistAssertions:
    """Renders must place the expected axes / artists / labels / counts."""

    def test_posture_radar_draws_thresholds_and_data(self) -> None:
        data = get_five_pillars_data(
            firewall_score=0.8,
            sandbox_score=0.6,
            tripwire_score=0.7,
            invariant_score=0.5,
            provenance_score=0.9,
        )
        fig = render_posture_radar(data)
        ax = fig.axes[0]
        assert ax.name == "polar"
        # 4 threshold fills + 1 data fill (Polygon patches); single data line.
        assert len(ax.lines) == 1
        assert len(ax.patches) == 5
        texts = [t.get_text() for t in ax.get_xticklabels()]
        assert len(texts) == 5 and all(texts)
        plt.close(fig)

    def test_checklist_flowchart_draws_all_boxes(self) -> None:
        data = get_deployment_phases_data()
        fig = render_checklist_flowchart(data)
        ax = fig.axes[0]
        # 4 phase headers + 16 checks (4 phases x 4 checks) = 20 rectangles.
        assert len(ax.patches) == 20
        assert all(isinstance(p, plt.Rectangle) for p in ax.patches)
        asserts = [t.get_text() for t in ax.texts]
        assert "Pre-Deployment" in asserts
        plt.close(fig)

    def test_risk_matrix_draws_image_and_points(self) -> None:
        risks = [
            {"name": "Attack A", "impact": 4, "likelihood": 3},
            {"name": "Attack B", "impact": 2, "likelihood": 5},
        ]
        data = get_risk_matrix_data(risks=risks)
        fig = render_risk_matrix(data)
        ax = fig.axes[0]
        assert len(ax.images) == 1  # heatmap
        assert len(ax.lines) == len(risks)  # one marker per risk point
        assert len(ax.texts) == len(risks)  # one annotation per risk point
        plt.close(fig)

    def test_trust_decay_draws_curve_thresholds_fill(self) -> None:
        data = get_trust_decay_data(delta=0.5, max_depth=5)
        fig = render_trust_decay(data)
        ax = fig.axes[0]
        # data line + 50%/10% hlines (practical-depth vline also short delta).
        assert len(ax.lines) >= 3
        assert len(ax.collections) >= 1  # fill_between region
        plt.close(fig)

    def test_pitfall_severity_draws_one_bar_per_pitfall(self) -> None:
        data = get_pitfalls_data()
        fig = render_pitfall_severity(data)
        ax = fig.axes[0]
        containers = [c for c in ax.containers]
        assert len(containers) == 1
        assert len(containers[0]) == len(data.data["pitfalls"])  # 8 bars
        # Highest-severity pitfall is rendered at the top (inverted y).
        plt.close(fig)

    def test_timeline_draws_one_bar_per_phase(self) -> None:
        data = get_timeline_data()
        fig = render_timeline(data)
        ax = fig.axes[0]
        assert len(ax.patches) == len(data.data["phases"])  # 3 bars
        texts = [t.get_text() for t in ax.texts]
        for phase in data.data["phases"]:
            assert phase.name in texts
        plt.close(fig)
