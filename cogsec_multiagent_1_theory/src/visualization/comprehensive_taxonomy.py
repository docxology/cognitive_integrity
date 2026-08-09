"""Comprehensive Taxonomy module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Comprehensive attack taxonomy visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


def create_comprehensive_taxonomy_figure(output_dir: Path) -> Path:
    """
    Create comprehensive attack surface taxonomy visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Background
    ax.set_facecolor("#FAFAFA")

    # Colorblind-friendly colors (IBM Design)
    colors = {
        "external": "#648FFF",  # Blue
        "peripheral": "#785EF0",  # Purple
        "agent": "#DC267F",  # Magenta
        "coordination": "#FFB000",  # Yellow
        "systemic": "#FE6100",  # Orange
        "header": "#2C3E50",
        "text": "#2D2D2D",
        "bg": "#ECF0F1",
    }

    # Title
    ax.text(
        8,
        9.5,
        "COGNITIVE ATTACK SURFACE TAXONOMY",
        ha="center",
        va="center",
        fontsize=26,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        8,
        9.0,
        "Example Classifications from the CIF Threat Model",
        ha="center",
        va="center",
        fontsize=18,
        style="italic",
        color=colors["text"],
    )

    # Column positions and widths
    col_width = 2.8
    col_gap = 0.3
    start_x = 0.8

    # Data for each adversary class
    classes = [
        {
            "symbol": r"$\Omega_1$",
            "name": "EXTERNAL",
            "color": colors["external"],
            "icon": "↓",
            "attacks": [
                "Direct Prompt\nInjection",
                "Social\nEngineering",
                "Malicious\nUser Input",
            ],
            "complexity": "Low",
            "detection": 0.85,
            "impact": "Entry Point",
        },
        {
            "symbol": r"$\Omega_2$",
            "name": "PERIPHERAL",
            "color": colors["peripheral"],
            "icon": "!",
            "attacks": [
                "Tool Response\nManipulation",
                "Memory\nPoisoning",
                "API Data\nCorruption",
            ],
            "complexity": "Medium",
            "detection": 0.78,
            "impact": "Data Injection",
        },
        {
            "symbol": r"$\Omega_3$",
            "name": "AGENT-LEVEL",
            "color": colors["agent"],
            "icon": "o",
            "attacks": [
                "Identity\nConfusion",
                "Belief\nInjection",
                "Goal\nManipulation",
            ],
            "complexity": "High",
            "detection": 0.71,
            "impact": "State Corruption",
        },
        {
            "symbol": r"$\Omega_4$",
            "name": "COORDINATION",
            "color": colors["coordination"],
            "icon": "#",
            "attacks": [
                "Trust\nLaundering",
                "Sybil\nAttacks",
                "Consensus\nManipulation",
            ],
            "complexity": "High",
            "detection": 0.65,
            "impact": "Trust Exploitation",
        },
        {
            "symbol": r"$\Omega_5$",
            "name": "SYSTEMIC",
            "color": colors["systemic"],
            "icon": "!",
            "attacks": [
                "Orchestrator\nCompromise",
                "System-Wide\nCorruption",
                "Cascading\nFailure",
            ],
            "complexity": "Critical",
            "detection": 0.45,
            "impact": "Total Compromise",
        },
    ]

    # Draw each class column
    for i, cls in enumerate(classes):
        x = start_x + i * (col_width + col_gap)

        # Main column background with increasing intensity
        alpha = 0.15 + i * 0.05
        col_box = FancyBboxPatch(
            (x, 0.8),
            col_width,
            7.6,
            boxstyle="round,pad=0.02",
            facecolor=cls["color"],
            edgecolor=cls["color"],
            linewidth=2 + i * 0.5,
            alpha=alpha,
        )
        ax.add_patch(col_box)

        # Header box
        header_box = FancyBboxPatch(
            (x + 0.1, 7.4),
            col_width - 0.2,
            0.9,
            boxstyle="round,pad=0.02",
            facecolor=cls["color"],
            edgecolor="black",
            linewidth=1.5,
        )
        ax.add_patch(header_box)

        # Symbol
        ax.text(
            x + col_width / 2,
            8.0,
            cls["symbol"],
            ha="center",
            va="center",
            fontsize=28,
            fontweight="bold",
            color="white",
        )
        ax.text(
            x + col_width / 2,
            7.6,
            cls["name"],
            ha="center",
            va="center",
            fontsize=15,
            fontweight="bold",
            color="white",
        )

        # Icon
        ax.text(
            x + col_width / 2,
            6.9,
            cls["icon"],
            ha="center",
            va="center",
            fontsize=26,
            color=cls["color"],
        )

        # Attack types
        for j, attack in enumerate(cls["attacks"]):
            y = 5.8 - j * 1.2
            attack_box = FancyBboxPatch(
                (x + 0.15, y - 0.4),
                col_width - 0.3,
                0.9,
                boxstyle="round,pad=0.01",
                facecolor="white",
                edgecolor=cls["color"],
                linewidth=1,
            )
            ax.add_patch(attack_box)
            ax.text(
                x + col_width / 2,
                y,
                attack,
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=colors["text"],
            )

        # Complexity indicator
        complexity_colors = {
            "Low": "#648FFF",
            "Medium": "#FFB000",
            "High": "#FE6100",
            "Critical": "#DC267F",
        }
        ax.text(
            x + col_width / 2,
            2.3,
            f"Complexity: {cls['complexity']}",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color=complexity_colors[cls["complexity"]],
        )

        # Detection rate bar
        bar_width = (col_width - 0.4) * cls["detection"]
        bar_bg = Rectangle(
            (x + 0.2, 1.6), col_width - 0.4, 0.3, facecolor="#E0E0E0", edgecolor="none"
        )
        ax.add_patch(bar_bg)

        bar_color = (
            "#648FFF"
            if cls["detection"] >= 0.8
            else "#FFB000"
            if cls["detection"] >= 0.6
            else "#DC267F"
        )
        bar_fill = Rectangle((x + 0.2, 1.6), bar_width, 0.3, facecolor=bar_color, edgecolor="none")
        ax.add_patch(bar_fill)
        ax.text(
            x + col_width / 2,
            1.75,
            f"Detection: {cls['detection']:.0%}",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white" if cls["detection"] >= 0.5 else colors["text"],
        )

        # Impact label
        ax.text(
            x + col_width / 2,
            1.1,
            cls["impact"],
            ha="center",
            va="center",
            fontsize=11,
            fontweight="medium",
            style="italic",
            color=cls["color"],
        )

    # Severity progression arrow - positioned below content area for clarity
    arrow_y = 0.65  # Moved much lower to avoid cutting through content
    ax.annotate(
        "",
        xy=(15.2, arrow_y),
        xytext=(0.5, arrow_y),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#95A5A6",  # Lighter grey for subtlety
            lw=1.5,
            mutation_scale=15,
            alpha=0.7,
        ),
    )
    ax.text(
        7.85,
        arrow_y - 0.25,
        "→ Increasing Severity & Stealth",
        ha="center",
        va="center",
        fontsize=11,
        style="italic",
        color="#7F8C8D",
        fontweight="medium",
    )

    # Legend
    ax.text(
        0.5,
        0.4,
        "Detection difficulty: ",
        ha="left",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=colors["text"],
    )
    legend_items = [
        ("High (≥80%)", "#648FFF"),
        ("Medium (60-79%)", "#FFB000"),
        ("Low (<60%)", "#DC267F"),
    ]
    for j, (label, color) in enumerate(legend_items):
        ax.add_patch(
            Rectangle(
                (3.5 + j * 3.5, 0.3),
                0.4,
                0.25,
                facecolor=color,
                edgecolor="black",
                linewidth=0.5,
            )
        )
        ax.text(
            4.0 + j * 3.5,
            0.42,
            label,
            ha="left",
            va="center",
            fontsize=11,
            color=colors["text"],
        )

    plt.tight_layout()

    # Save outputs
    output_path_png = output_dir / "comprehensive_taxonomy.png"
    output_path_pdf = output_dir / "comprehensive_taxonomy.pdf"

    plt.savefig(
        output_path_png,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf
