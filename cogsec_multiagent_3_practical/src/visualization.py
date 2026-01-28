"""
Visualization module for Cognitive Security Practical Implementation Guide.

Provides figure generation logic for the Paper 3 manuscript.
Scripts in scripts/ call these methods following thin orchestrator pattern.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


class FigureType(Enum):
    """Types of figures supported by this module."""

    RADAR = "radar"
    FLOWCHART = "flowchart"
    HEATMAP = "heatmap"
    CURVE = "curve"
    BAR = "bar"
    TIMELINE = "timeline"


@dataclass
class FigureData:
    """Container for figure data and metadata."""

    figure_type: FigureType
    title: str
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Five Pillars Posture Radar Chart
# =============================================================================


def get_five_pillars_data(
    firewall_score: float = 0.0,
    sandbox_score: float = 0.0,
    tripwire_score: float = 0.0,
    invariant_score: float = 0.0,
    provenance_score: float = 0.0,
) -> FigureData:
    """Generate data for Five Pillars posture radar chart.

    The Five Pillars of the Cognitive Immunity Framework (CIF):
    1. Cognitive Firewall (F) - filters malicious inputs
    2. Belief Sandbox (W) - isolates uncertain beliefs
    3. Identity Tripwire (T) - detects identity deception
    4. Behavioral Invariants (I) - enforces constraints
    5. Epistemic Provenance (P) - tracks information sources

    Args:
        firewall_score: Cognitive Firewall implementation score (0-1)
        sandbox_score: Belief Sandbox implementation score (0-1)
        tripwire_score: Identity Tripwire implementation score (0-1)
        invariant_score: Behavioral Invariant implementation score (0-1)
        provenance_score: Epistemic Provenance implementation score (0-1)

    Returns:
        FigureData with radar chart configuration

    Raises:
        ValueError: If any score is outside [0, 1] range
    """
    scores = {
        "firewall": firewall_score,
        "sandbox": sandbox_score,
        "tripwire": tripwire_score,
        "invariant": invariant_score,
        "provenance": provenance_score,
    }

    for name, score in scores.items():
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"{name}_score must be between 0 and 1, got {score}")

    pillars = [
        "Cognitive\nFirewall (F)",
        "Belief\nSandbox (W)",
        "Identity\nTripwire (T)",
        "Behavioral\nInvariants (I)",
        "Epistemic\nProvenance (P)",
    ]

    values = [
        firewall_score,
        sandbox_score,
        tripwire_score,
        invariant_score,
        provenance_score,
    ]

    return FigureData(
        figure_type=FigureType.RADAR,
        title="Five Pillars Security Posture Assessment",
        data={
            "pillars": pillars,
            "values": values,
            "thresholds": {
                "minimal": 0.25,
                "standard": 0.50,
                "elevated": 0.75,
                "maximum": 0.90,
            },
        },
        metadata={
            "overall_score": sum(values) / len(values),
            "weakest_pillar": pillars[values.index(min(values))],
            "strongest_pillar": pillars[values.index(max(values))],
        },
    )


def render_posture_radar(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render Five Pillars posture radar chart.

    Args:
        data: FigureData from get_five_pillars_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    pillars = data.data["pillars"]
    values = data.data["values"]
    thresholds = data.data["thresholds"]

    # Number of variables
    num_vars = len(pillars)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    # Close the radar chart
    values_closed = values + values[:1]

    # Create figure if no axes provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection="polar"))
    else:
        fig = ax.figure

    # Draw threshold circles
    threshold_colors = ["#ffcccc", "#ffffcc", "#ccffcc", "#ccccff"]
    threshold_names = list(thresholds.keys())
    threshold_values = list(thresholds.values())

    for i, (name, val) in enumerate(zip(threshold_names, threshold_values)):
        circle = plt.Circle(
            (0, 0), val, transform=ax.transData + ax.transAxes, alpha=0.1, color=threshold_colors[i]
        )
        # Use fill_between for radar
        ax.fill(angles, [val] * (num_vars + 1), alpha=0.1, color=threshold_colors[i], label=f"{name.title()} ({val:.0%})")

    # Plot data
    ax.plot(angles, values_closed, "o-", linewidth=2, color="#1f77b4", markersize=8)
    ax.fill(angles, values_closed, alpha=0.25, color="#1f77b4")

    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(pillars, fontsize=10)

    # Set y-axis limits
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=8)

    # Add title
    ax.set_title(data.title, fontsize=14, fontweight="bold", pad=20)

    # Add legend
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

    return fig


# =============================================================================
# Deployment Checklist Flowchart
# =============================================================================


@dataclass
class DeploymentPhase:
    """A deployment phase with associated checks."""

    name: str
    checks: list[str]
    status: str = "pending"  # pending, in_progress, complete


def get_deployment_phases_data() -> FigureData:
    """Generate data for deployment phases flowchart.

    Returns:
        FigureData with deployment phases configuration
    """
    phases = [
        DeploymentPhase(
            name="Pre-Deployment",
            checks=[
                "Threat model complete",
                "CIF components selected",
                "Trust boundaries defined",
                "Invariants specified",
            ],
        ),
        DeploymentPhase(
            name="Integration",
            checks=[
                "Firewall rules configured",
                "Sandbox policies set",
                "Tripwire canaries placed",
                "Provenance tracking enabled",
            ],
        ),
        DeploymentPhase(
            name="Testing",
            checks=[
                "Red team assessment",
                "Penetration testing",
                "Failure mode analysis",
                "Recovery procedures tested",
            ],
        ),
        DeploymentPhase(
            name="Operational",
            checks=[
                "Monitoring active",
                "Alerting configured",
                "Incident response ready",
                "Continuous assessment",
            ],
        ),
    ]

    return FigureData(
        figure_type=FigureType.FLOWCHART,
        title="Deployment Readiness Checklist",
        data={
            "phases": phases,
            "total_checks": sum(len(p.checks) for p in phases),
        },
    )


def render_checklist_flowchart(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render deployment checklist flowchart.

    Args:
        data: FigureData from get_deployment_phases_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    phases: list[DeploymentPhase] = data.data["phases"]

    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 8))
    else:
        fig = ax.figure

    # Colors for phases
    colors = ["#e3f2fd", "#e8f5e9", "#fff3e0", "#fce4ec"]
    border_colors = ["#1976d2", "#388e3c", "#f57c00", "#c2185b"]

    # Layout parameters
    box_width = 2.5
    box_height = 0.6
    phase_spacing = 3.5
    check_spacing = 0.8

    for i, phase in enumerate(phases):
        x_center = i * phase_spacing + 1.5

        # Draw phase header box
        header_rect = plt.Rectangle(
            (x_center - box_width / 2, 6),
            box_width,
            1.0,
            facecolor=colors[i],
            edgecolor=border_colors[i],
            linewidth=2,
        )
        ax.add_patch(header_rect)
        ax.text(
            x_center,
            6.5,
            phase.name,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=border_colors[i],
        )

        # Draw check items
        for j, check in enumerate(phase.checks):
            y_pos = 5 - j * check_spacing
            check_rect = plt.Rectangle(
                (x_center - box_width / 2, y_pos - box_height / 2),
                box_width,
                box_height,
                facecolor="white",
                edgecolor=border_colors[i],
                linewidth=1,
            )
            ax.add_patch(check_rect)

            # Checkbox symbol
            ax.text(
                x_center - box_width / 2 + 0.15,
                y_pos,
                "☐",
                ha="left",
                va="center",
                fontsize=12,
            )

            # Check text
            ax.text(
                x_center - box_width / 2 + 0.4,
                y_pos,
                check,
                ha="left",
                va="center",
                fontsize=9,
            )

        # Draw arrow to next phase
        if i < len(phases) - 1:
            ax.annotate(
                "",
                xy=(x_center + phase_spacing / 2 + 0.3, 6.5),
                xytext=(x_center + box_width / 2 + 0.1, 6.5),
                arrowprops=dict(arrowstyle="->", color="gray", lw=2),
            )

    ax.set_xlim(-0.5, len(phases) * phase_spacing)
    ax.set_ylim(1.5, 7.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(data.title, fontsize=14, fontweight="bold", pad=20)

    return fig


# =============================================================================
# Risk Assessment Matrix (Impact × Likelihood Heatmap)
# =============================================================================


def get_risk_matrix_data(
    risks: list[dict[str, Any]] | None = None,
) -> FigureData:
    """Generate data for risk assessment matrix.

    Args:
        risks: Optional list of risk dictionaries with 'name', 'impact', 'likelihood'

    Returns:
        FigureData with risk matrix configuration
    """
    if risks is None:
        # Default example risks
        risks = [
            {"name": "Direct Injection", "impact": 4, "likelihood": 3},
            {"name": "Indirect Injection", "impact": 4, "likelihood": 4},
            {"name": "Trust Laundering", "impact": 5, "likelihood": 2},
            {"name": "Belief Manipulation", "impact": 3, "likelihood": 3},
            {"name": "Goal Hijacking", "impact": 5, "likelihood": 2},
            {"name": "Context Poisoning", "impact": 4, "likelihood": 3},
            {"name": "Multi-turn Attacks", "impact": 4, "likelihood": 4},
            {"name": "Consensus Subversion", "impact": 5, "likelihood": 1},
        ]

    # Validate risks
    for risk in risks:
        if not 1 <= risk["impact"] <= 5:
            raise ValueError(f"Impact must be 1-5, got {risk['impact']}")
        if not 1 <= risk["likelihood"] <= 5:
            raise ValueError(f"Likelihood must be 1-5, got {risk['likelihood']}")

    return FigureData(
        figure_type=FigureType.HEATMAP,
        title="Cognitive Security Risk Matrix",
        data={
            "risks": risks,
            "impact_labels": ["Minimal", "Minor", "Moderate", "Major", "Severe"],
            "likelihood_labels": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
        },
    )


def render_risk_matrix(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render risk assessment matrix heatmap.

    Args:
        data: FigureData from get_risk_matrix_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    risks = data.data["risks"]
    impact_labels = data.data["impact_labels"]
    likelihood_labels = data.data["likelihood_labels"]

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 10))
    else:
        fig = ax.figure

    # Create base matrix (5x5 risk severity)
    risk_colors = np.array(
        [
            [1, 2, 2, 3, 3],  # Impact 1 (Minimal)
            [2, 2, 3, 3, 4],  # Impact 2 (Minor)
            [2, 3, 3, 4, 4],  # Impact 3 (Moderate)
            [3, 3, 4, 4, 5],  # Impact 4 (Major)
            [3, 4, 4, 5, 5],  # Impact 5 (Severe)
        ]
    )

    # Color mapping
    cmap = plt.cm.RdYlGn_r  # Red = high risk, Green = low risk
    norm = plt.Normalize(vmin=1, vmax=5)

    # Draw heatmap
    im = ax.imshow(risk_colors, cmap=cmap, norm=norm, aspect="auto")

    # Add grid lines
    ax.set_xticks(np.arange(-0.5, 5, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2)

    # Set axis labels
    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(likelihood_labels, fontsize=10)
    ax.set_yticklabels(impact_labels, fontsize=10)
    ax.set_xlabel("Likelihood", fontsize=12, fontweight="bold")
    ax.set_ylabel("Impact", fontsize=12, fontweight="bold")

    # Plot risk points
    for risk in risks:
        x = risk["likelihood"] - 1  # Convert to 0-indexed
        y = risk["impact"] - 1
        ax.plot(x, y, "ko", markersize=12, markeredgewidth=2, markerfacecolor="white")
        ax.annotate(
            risk["name"],
            (x, y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    # Add risk level legend
    legend_elements = [
        Patch(facecolor=cmap(norm(1)), label="Low (1-2)"),
        Patch(facecolor=cmap(norm(2.5)), label="Medium (2-3)"),
        Patch(facecolor=cmap(norm(3.5)), label="High (3-4)"),
        Patch(facecolor=cmap(norm(5)), label="Critical (4-5)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.02, 1))

    ax.set_title(data.title, fontsize=14, fontweight="bold", pad=10)

    return fig


# =============================================================================
# Trust Decay Curve
# =============================================================================


def get_trust_decay_data(
    delta: float = 0.85,
    max_depth: int = 10,
) -> FigureData:
    """Generate data for trust decay visualization.

    Demonstrates how trust decays exponentially with delegation depth:
    T_effective = T_initial × δ^d

    Args:
        delta: Trust decay factor (0 < δ < 1)
        max_depth: Maximum delegation depth to show

    Returns:
        FigureData with trust decay curve configuration

    Raises:
        ValueError: If delta is not in (0, 1)
    """
    if not 0 < delta < 1:
        raise ValueError(f"delta must be between 0 and 1, got {delta}")

    depths = np.arange(0, max_depth + 1)
    trust_values = delta**depths

    # Calculate practical depth (where trust < 0.1)
    practical_depth = int(np.ceil(np.log(0.1) / np.log(delta)))

    return FigureData(
        figure_type=FigureType.CURVE,
        title=f"Trust Decay with Delegation Depth (δ = {delta})",
        data={
            "depths": depths.tolist(),
            "trust_values": trust_values.tolist(),
            "delta": delta,
        },
        metadata={
            "practical_depth": practical_depth,
            "half_life_depth": np.log(0.5) / np.log(delta),
        },
    )


def render_trust_decay(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render trust decay curve.

    Args:
        data: FigureData from get_trust_decay_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    depths = data.data["depths"]
    trust_values = data.data["trust_values"]
    delta = data.data["delta"]
    practical_depth = data.metadata.get("practical_depth", 10)

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    # Plot trust decay curve
    ax.plot(depths, trust_values, "b-", linewidth=2, label=f"T × δ^d (δ={delta})")
    ax.fill_between(depths, trust_values, alpha=0.2)

    # Mark key thresholds
    ax.axhline(y=0.5, color="orange", linestyle="--", alpha=0.7, label="50% threshold")
    ax.axhline(y=0.1, color="red", linestyle="--", alpha=0.7, label="10% threshold")

    # Mark practical depth
    if practical_depth <= max(depths):
        ax.axvline(x=practical_depth, color="red", linestyle=":", alpha=0.7)
        ax.annotate(
            f"Practical limit\n(d={practical_depth})",
            (practical_depth, 0.15),
            fontsize=9,
            ha="center",
        )

    # Add formula annotation
    ax.annotate(
        r"$T_{effective} = T_{initial} \times \delta^d$",
        (0.95, 0.95),
        xycoords="axes fraction",
        fontsize=12,
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    ax.set_xlabel("Delegation Depth (d)", fontsize=12)
    ax.set_ylabel("Effective Trust", fontsize=12)
    ax.set_title(data.title, fontsize=14, fontweight="bold")
    ax.set_xlim(0, max(depths))
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    return fig


# =============================================================================
# Common Pitfalls Severity Bar Chart
# =============================================================================


@dataclass
class Pitfall:
    """A common deployment pitfall."""

    name: str
    severity: int  # 1-5
    description: str
    category: str  # security, operational, design


def get_pitfalls_data() -> FigureData:
    """Generate data for common pitfalls severity chart.

    Returns:
        FigureData with pitfall severity rankings
    """
    pitfalls = [
        Pitfall(
            name="Implicit Trust in Outputs",
            severity=5,
            description="Treating agent outputs as verified without validation",
            category="security",
        ),
        Pitfall(
            name="Missing Input Validation",
            severity=5,
            description="No cognitive firewall on external inputs",
            category="security",
        ),
        Pitfall(
            name="Flat Trust Architecture",
            severity=4,
            description="All agents at same trust level regardless of role",
            category="design",
        ),
        Pitfall(
            name="No Behavioral Invariants",
            severity=4,
            description="Missing hard constraints on agent actions",
            category="security",
        ),
        Pitfall(
            name="Single Point of Failure",
            severity=4,
            description="Critical decisions without redundancy",
            category="operational",
        ),
        Pitfall(
            name="Insufficient Monitoring",
            severity=3,
            description="No visibility into agent decision-making",
            category="operational",
        ),
        Pitfall(
            name="Over-Privileged Agents",
            severity=3,
            description="Agents with more capabilities than needed",
            category="design",
        ),
        Pitfall(
            name="Static Trust Levels",
            severity=2,
            description="Trust never updated based on behavior",
            category="design",
        ),
    ]

    return FigureData(
        figure_type=FigureType.BAR,
        title="Common Deployment Pitfalls by Severity",
        data={
            "pitfalls": pitfalls,
            "severity_labels": {
                5: "Critical",
                4: "High",
                3: "Medium",
                2: "Low",
                1: "Minimal",
            },
        },
    )


def render_pitfall_severity(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render pitfall severity bar chart.

    Args:
        data: FigureData from get_pitfalls_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    pitfalls: list[Pitfall] = data.data["pitfalls"]

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    # Sort by severity (descending)
    sorted_pitfalls = sorted(pitfalls, key=lambda p: p.severity, reverse=True)

    names = [p.name for p in sorted_pitfalls]
    severities = [p.severity for p in sorted_pitfalls]
    categories = [p.category for p in sorted_pitfalls]

    # Color by category
    category_colors = {
        "security": "#e53935",  # Red
        "operational": "#fb8c00",  # Orange
        "design": "#1e88e5",  # Blue
    }
    colors = [category_colors[c] for c in categories]

    # Create horizontal bar chart
    y_pos = range(len(names))
    bars = ax.barh(y_pos, severities, color=colors, edgecolor="white", linewidth=1)

    # Add severity labels on bars
    for bar, pitfall in zip(bars, sorted_pitfalls):
        width = bar.get_width()
        ax.text(
            width - 0.1,
            bar.get_y() + bar.get_height() / 2,
            f"{pitfall.severity}",
            ha="right",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Severity (1-5)", fontsize=12)
    ax.set_xlim(0, 5.5)
    ax.set_title(data.title, fontsize=14, fontweight="bold")

    # Add category legend
    legend_elements = [
        Patch(facecolor=category_colors["security"], label="Security"),
        Patch(facecolor=category_colors["operational"], label="Operational"),
        Patch(facecolor=category_colors["design"], label="Design"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    ax.invert_yaxis()  # Highest severity at top

    return fig


# =============================================================================
# Deployment Timeline
# =============================================================================


@dataclass
class TimelinePhase:
    """A phase in the deployment timeline."""

    name: str
    start: float  # Relative position 0-1
    end: float
    color: str
    activities: list[str]


def get_timeline_data() -> FigureData:
    """Generate data for deployment timeline visualization.

    Returns:
        FigureData with timeline phases
    """
    phases = [
        TimelinePhase(
            name="Pre-Deployment",
            start=0.0,
            end=0.3,
            color="#1976d2",
            activities=[
                "Threat modeling",
                "CIF component selection",
                "Trust boundary definition",
                "Invariant specification",
            ],
        ),
        TimelinePhase(
            name="Operational",
            start=0.3,
            end=0.8,
            color="#388e3c",
            activities=[
                "Continuous monitoring",
                "Trust recalibration",
                "Anomaly detection",
                "Performance optimization",
            ],
        ),
        TimelinePhase(
            name="Incident Response",
            start=0.8,
            end=1.0,
            color="#c2185b",
            activities=[
                "Quarantine compromised agents",
                "Belief state rollback",
                "Forensic analysis",
                "Recovery and hardening",
            ],
        ),
    ]

    return FigureData(
        figure_type=FigureType.TIMELINE,
        title="Cognitive Security Lifecycle Phases",
        data={"phases": phases},
    )


def render_timeline(data: FigureData, ax: plt.Axes | None = None) -> plt.Figure:
    """Render deployment timeline.

    Args:
        data: FigureData from get_timeline_data()
        ax: Optional matplotlib axes to render on

    Returns:
        Matplotlib figure
    """
    phases: list[TimelinePhase] = data.data["phases"]

    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 6))
    else:
        fig = ax.figure

    timeline_y = 0.5
    bar_height = 0.15

    for phase in phases:
        # Draw phase bar
        width = phase.end - phase.start
        rect = plt.Rectangle(
            (phase.start, timeline_y - bar_height / 2),
            width,
            bar_height,
            facecolor=phase.color,
            edgecolor="white",
            linewidth=2,
            alpha=0.8,
        )
        ax.add_patch(rect)

        # Phase name above bar
        ax.text(
            phase.start + width / 2,
            timeline_y + bar_height / 2 + 0.05,
            phase.name,
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=phase.color,
        )

        # Activities below bar
        for i, activity in enumerate(phase.activities):
            y_offset = -0.08 - (i * 0.06)
            ax.text(
                phase.start + width / 2,
                timeline_y - bar_height / 2 + y_offset,
                f"• {activity}",
                ha="center",
                va="top",
                fontsize=8,
                color="gray",
            )

    # Add time arrow
    ax.annotate(
        "",
        xy=(1.05, timeline_y),
        xytext=(-0.05, timeline_y),
        arrowprops=dict(arrowstyle="->", color="gray", lw=1.5),
    )
    ax.text(0.5, -0.15, "Time →", ha="center", fontsize=10, color="gray")

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 0.9)
    ax.axis("off")
    ax.set_title(data.title, fontsize=14, fontweight="bold", pad=20)

    return fig


# =============================================================================
# Module Exports
# =============================================================================


__all__ = [
    # Types
    "FigureType",
    "FigureData",
    "DeploymentPhase",
    "Pitfall",
    "TimelinePhase",
    # Data generators
    "get_five_pillars_data",
    "get_deployment_phases_data",
    "get_risk_matrix_data",
    "get_trust_decay_data",
    "get_pitfalls_data",
    "get_timeline_data",
    # Renderers
    "render_posture_radar",
    "render_checklist_flowchart",
    "render_risk_matrix",
    "render_trust_decay",
    "render_pitfall_severity",
    "render_timeline",
]
