#!/usr/bin/env python3
"""Generate comprehensive CIF architecture visualization."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                Rectangle)


def create_cif_comprehensive_figure(output_dir: Path) -> Path:
    """
    Create comprehensive CIF architecture diagram.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis("off")

    # Colorblind-friendly colors (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "defense": "#DC267F",  # Magenta
        "detection": "#FFB000",  # Yellow
        "agent": "#648FFF",  # Blue
        "coordination": "#785EF0",  # Purple
        "input": "#FE6100",  # Orange
        "external": "#999999",  # Gray
        "header": "#2C3E50",
        "flow": "#7F8C8D",
    }

    # Title
    ax.text(
        8,
        11.5,
        "COGNITIVE INTEGRITY FRAMEWORK (CIF)",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        8,
        11.0,
        "Layered Defense Architecture for Multiagent AI Systems",
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color="#5D6D7E",
    )

    # Main frame
    frame = FancyBboxPatch(
        (0.5, 0.5),
        15,
        10,
        boxstyle="round,pad=0.02",
        facecolor="white",
        edgecolor=colors["header"],
        linewidth=3,
    )
    ax.add_patch(frame)

    # Input sources (left side)
    input_box = FancyBboxPatch(
        (0.7, 6.5),
        2,
        3,
        boxstyle="round,pad=0.02",
        facecolor=colors["input"],
        edgecolor="black",
        linewidth=2,
        alpha=0.9,
    )
    ax.add_patch(input_box)
    ax.text(
        1.7,
        8.6,
        "INPUT",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="white",
    )
    ax.text(
        1.7,
        8.2,
        "SOURCES",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="white",
    )
    ax.text(
        1.7, 7.6, "• User Prompts", ha="center", va="center", fontsize=9, color="white"
    )
    ax.text(
        1.7,
        7.2,
        "• Tool Responses",
        ha="center",
        va="center",
        fontsize=9,
        color="white",
    )
    ax.text(
        1.7,
        6.8,
        "• Agent Messages",
        ha="center",
        va="center",
        fontsize=9,
        color="white",
    )

    # Layer definitions
    layers = [
        {
            "name": "DEFENSE LAYER",
            "y": 8.0,
            "height": 1.8,
            "color": colors["defense"],
            "components": [
                ("Cognitive Firewall", "Pattern-based\nclassification", "τ_f = 0.5"),
                ("Belief Sandbox", "Provisional\nisolation", "γ → promotion"),
                ("Behavioral Invariants", "Action\nconstraints", "I ⊆ permitted"),
            ],
        },
        {
            "name": "DETECTION LAYER",
            "y": 5.8,
            "height": 1.8,
            "color": colors["detection"],
            "components": [
                ("Anomaly Detection", "Drift scoring\n& sliding window", "σ(Δb) > τ_d"),
                ("Tripwire Monitor", "Canary belief\nverification", "c_i ∈ B?"),
                ("Provenance Tracker", "Source chain\nattribution", "P: B → sources"),
            ],
        },
        {
            "name": "AGENT LAYER",
            "y": 3.2,
            "height": 2.2,
            "color": colors["agent"],
            "components": [
                ("Beliefs (B)", "Propositions\nP(b) ∈ [0,1]", "verified/provisional"),
                ("Goals (G)", "Objectives\n⟨G, ≺⟩ ordered", "priority queue"),
                ("Intentions (I)", "Actions\nπ: S → A", "policy mapping"),
                ("History (H)", "Trace\n[(a,o,r)...]", "audit log"),
            ],
        },
        {
            "name": "COORDINATION LAYER",
            "y": 0.8,
            "height": 2.0,
            "color": colors["coordination"],
            "components": [
                ("Trust Calculus", "T: A×A → [0,1]\nδ-bounded decay", "T(a→c) ≤ δ^d"),
                (
                    "Quorum Verification",
                    "k-of-n approval\nconsensus protocol",
                    "BFT: n≥3f+1",
                ),
                ("State Consistency", "Cross-agent\nvalidation", "Byzantine tolerance"),
            ],
        },
    ]

    # Draw layers
    for layer in layers:
        # Layer background
        layer_box = FancyBboxPatch(
            (3.0, layer["y"]),
            12.3,
            layer["height"],
            boxstyle="round,pad=0.02",
            facecolor=layer["color"],
            edgecolor="black",
            linewidth=2,
            alpha=0.2,
        )
        ax.add_patch(layer_box)

        # Layer label
        ax.text(
            3.3,
            layer["y"] + layer["height"] - 0.25,
            layer["name"],
            fontsize=11,
            fontweight="bold",
            color=colors["header"],
        )

        # Components
        n_comp = len(layer["components"])
        comp_width = 3.6 if n_comp <= 3 else 2.7
        gap = 0.3
        start_x = 3.3

        for i, (name, desc, formula) in enumerate(layer["components"]):
            x = start_x + i * (comp_width + gap)

            # Component box
            comp_box = FancyBboxPatch(
                (x, layer["y"] + 0.15),
                comp_width,
                layer["height"] - 0.45,
                boxstyle="round,pad=0.02",
                facecolor="white",
                edgecolor=layer["color"],
                linewidth=1.5,
            )
            ax.add_patch(comp_box)

            # Component content
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] - 0.6,
                name,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color=colors["header"],
            )
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] / 2 - 0.1,
                desc,
                ha="center",
                va="center",
                fontsize=8,
                color="#5D6D7E",
            )
            ax.text(
                x + comp_width / 2,
                layer["y"] + 0.4,
                formula,
                ha="center",
                va="center",
                fontsize=8,
                style="italic",
                color=layer["color"],
                fontfamily="monospace",
            )

    # Data flow arrows (vertical)
    arrow_x = 2.85
    flows = [
        (9.6, 9.8, "Raw\nInput"),
        (8.0, 5.8, "Filtered"),
        (5.8, 3.2, "Verified"),
        (3.2, 0.8, "Coordinated"),
    ]

    for y_end, y_start, label in flows:
        ax.annotate(
            "",
            xy=(arrow_x, y_end),
            xytext=(arrow_x, y_start + 0.1),
            arrowprops=dict(
                arrowstyle="-|>", color=colors["flow"], lw=2, mutation_scale=15
            ),
        )

    # Input arrow
    ax.annotate(
        "",
        xy=(2.9, 7.5),
        xytext=(2.7, 7.5),
        arrowprops=dict(
            arrowstyle="-|>", color=colors["input"], lw=2, mutation_scale=15
        ),
    )

    # External services (right side)
    ext_box = FancyBboxPatch(
        (13.5, 4),
        1.8,
        3,
        boxstyle="round,pad=0.02",
        facecolor=colors["external"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(ext_box)
    ax.text(
        14.4,
        6.5,
        "EXTERNAL",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="white",
    )
    ax.text(
        14.4,
        6.1,
        "SERVICES",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="white",
    )
    ax.text(
        14.4, 5.5, "• Web APIs", ha="center", va="center", fontsize=8, color="white"
    )
    ax.text(14.4, 5.1, "• Tools", ha="center", va="center", fontsize=8, color="white")
    ax.text(
        14.4, 4.7, "• Databases", ha="center", va="center", fontsize=8, color="white"
    )
    ax.text(
        14.4,
        4.3,
        "(Sandboxed)",
        ha="center",
        va="center",
        fontsize=8,
        style="italic",
        color="white",
    )

    # External connection arrow
    ax.annotate(
        "",
        xy=(13.5, 5.5),
        xytext=(15.0, 5.5),
        arrowprops=dict(
            arrowstyle="<->",
            color=colors["external"],
            lw=2,
            connectionstyle="arc3,rad=0",
        ),
    )

    # Key metrics box
    metrics_box = FancyBboxPatch(
        (0.7, 1),
        2,
        2.5,
        boxstyle="round,pad=0.02",
        facecolor="#F8F9FA",
        edgecolor=colors["header"],
        linewidth=1.5,
    )
    ax.add_patch(metrics_box)
    ax.text(
        1.7,
        3.2,
        "KEY METRICS",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        1.7,
        2.7,
        "Detection: 94%",
        ha="center",
        va="center",
        fontsize=9,
        color="#648FFF",
        fontweight="bold",
    )  # Colorblind-friendly blue
    ax.text(
        1.7,
        2.3,
        "FPR: 6%",
        ha="center",
        va="center",
        fontsize=9,
        color=colors["defense"],
    )
    ax.text(
        1.7,
        1.9,
        "Latency: +23%",
        ha="center",
        va="center",
        fontsize=9,
        color=colors["detection"],
    )
    ax.text(
        1.7,
        1.5,
        "Integrity: +127%",
        ha="center",
        va="center",
        fontsize=9,
        color=colors["coordination"],
    )

    # Properties box
    props_box = FancyBboxPatch(
        (0.7, 3.8),
        2,
        2.3,
        boxstyle="round,pad=0.02",
        facecolor="#F8F9FA",
        edgecolor=colors["header"],
        linewidth=1.5,
    )
    ax.add_patch(props_box)
    ax.text(
        1.7,
        5.8,
        "PROPERTIES",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        1.7,
        5.35,
        "• Belief Integrity",
        ha="center",
        va="center",
        fontsize=8,
        color=colors["defense"],
    )
    ax.text(
        1.7,
        5.0,
        "• Trust Boundedness",
        ha="center",
        va="center",
        fontsize=8,
        color=colors["coordination"],
    )
    ax.text(
        1.7,
        4.65,
        "• Goal Alignment",
        ha="center",
        va="center",
        fontsize=8,
        color=colors["agent"],
    )
    ax.text(
        1.7,
        4.3,
        "• Provenance",
        ha="center",
        va="center",
        fontsize=8,
        color=colors["detection"],
    )

    plt.tight_layout()

    # Save outputs
    output_path_png = output_dir / "cif_comprehensive.png"
    output_path_pdf = output_dir / "cif_comprehensive.pdf"

    plt.savefig(
        output_path_png,
        dpi=200,
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
    create_cif_comprehensive_figure(output_dir)
