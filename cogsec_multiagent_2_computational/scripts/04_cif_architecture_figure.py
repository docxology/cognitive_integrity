#!/usr/bin/env python3
"""Generate CIF architecture visualization figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle


def create_cif_architecture_figure(output_dir: Path) -> Path:
    """
    Create Cognitive Integrity Framework architecture diagram.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colorblind-friendly layer colors (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "defense": "#DC267F",  # Magenta for defense
        "detection": "#FE6100",  # Orange for detection
        "agent": "#648FFF",  # Blue for agent
        "coordination": "#785EF0",  # Purple for coordination
        "component": "#F5F5F5",  # Light gray for components
        "header": "#2C3E50",  # Dark for headers
    }

    # Main frame
    main_frame = FancyBboxPatch(
        (0.5, 0.5),
        13,
        9,
        boxstyle="round,pad=0.02",
        facecolor="white",
        edgecolor=colors["header"],
        linewidth=3,
    )
    ax.add_patch(main_frame)

    # Title
    ax.text(
        7,
        9.7,
        "COGNITIVE INTEGRITY FRAMEWORK (CIF)",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=colors["header"],
    )

    def draw_layer(y_start, height, color, title, components):
        """Draw a layer with components."""
        # Layer background
        layer = FancyBboxPatch(
            (1, y_start),
            12,
            height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="black",
            linewidth=2,
            alpha=0.3,
        )
        ax.add_patch(layer)

        # Layer title
        ax.text(
            1.3,
            y_start + height - 0.35,
            title,
            fontsize=11,
            fontweight="bold",
            color=colors["header"],
        )

        # Components
        n_components = len(components)
        comp_width = 3.2
        total_width = n_components * comp_width + (n_components - 1) * 0.3
        start_x = (14 - total_width) / 2

        for i, (name, desc) in enumerate(components):
            x = start_x + i * (comp_width + 0.3)
            comp_box = FancyBboxPatch(
                (x, y_start + 0.3),
                comp_width,
                height - 0.7,
                boxstyle="round,pad=0.02",
                facecolor=colors["component"],
                edgecolor=color,
                linewidth=2,
            )
            ax.add_patch(comp_box)

            ax.text(
                x + comp_width / 2,
                y_start + height - 0.7,
                name,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
            )
            ax.text(
                x + comp_width / 2,
                y_start + 0.65,
                desc,
                ha="center",
                va="center",
                fontsize=8,
                style="italic",
                wrap=True,
            )

    # Defense Layer
    draw_layer(
        7.2,
        1.8,
        colors["defense"],
        "DEFENSE LAYER",
        [
            ("Cognitive Firewall", "Input classification"),
            ("Belief Sandbox", "Provisional beliefs"),
            ("Behavioral Invariants", "Action constraints"),
        ],
    )

    # Detection Layer
    draw_layer(
        5.2,
        1.8,
        colors["detection"],
        "DETECTION LAYER",
        [
            ("Anomaly Detection", "Drift scoring"),
            ("Tripwire Monitor", "Canary checking"),
            ("Provenance Tracker", "Source attribution"),
        ],
    )

    # Agent Layer
    draw_layer(
        2.8,
        2.2,
        colors["agent"],
        "AGENT LAYER",
        [
            ("Beliefs (B)", "Propositions"),
            ("Goals (G)", "Objectives"),
            ("Intentions (I)", "Actions"),
            ("History (H)", "Trace"),
        ],
    )

    # Coordination Layer
    draw_layer(
        0.8,
        1.8,
        colors["coordination"],
        "COORDINATION LAYER",
        [
            ("Trust Calculus", "Bounded delegation"),
            ("Quorum Verification", "Multi-agent approval"),
            ("Byzantine Tolerance", "n ≥ 3f + 1"),
        ],
    )

    # Add arrows between layers
    arrow_props = dict(
        arrowstyle="->", color=colors["header"], connectionstyle="arc3,rad=0", lw=2
    )

    # Defense -> Detection
    ax.annotate("", xy=(7, 7.0), xytext=(7, 7.2), arrowprops=arrow_props)

    # Detection -> Agent
    ax.annotate("", xy=(7, 5.0), xytext=(7, 5.2), arrowprops=arrow_props)

    # Agent -> Coordination
    ax.annotate("", xy=(7, 2.6), xytext=(7, 2.8), arrowprops=arrow_props)

    # Add data flow annotation
    ax.text(
        13.3,
        5,
        "Data\nFlow",
        ha="center",
        va="center",
        fontsize=9,
        color=colors["header"],
        rotation=-90,
    )
    ax.annotate(
        "",
        xy=(13.1, 3),
        xytext=(13.1, 7),
        arrowprops=dict(arrowstyle="->", color=colors["header"], lw=2),
    )

    output_path_png = output_dir / "cif_architecture.png"
    output_path_pdf = output_dir / "cif_architecture.pdf"

    plt.savefig(
        output_path_png,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf


if __name__ == "__main__":
    # Derive base_dir from the script's actual location
    # Script is at: projects/{project_name}/scripts/{script}.py
    script_dir = Path(__file__).resolve().parent  # scripts/
    base_dir = script_dir.parent  # projects/{project_name}/
    
    output_dir = base_dir / "output" / "figures"
    create_cif_architecture_figure(output_dir)
