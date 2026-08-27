"""Cif Comprehensive module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Comprehensive CIF architecture visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


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
        fontsize=24,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        8,
        11.0,
        "Layered Defense Architecture for Multiagent AI Systems",
        ha="center",
        va="center",
        fontsize=14,
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

    # Input sources
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
        "INPUT\nSOURCES",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="white",
    )
    ax.text(1.7, 7.6, "• User Prompts", ha="center", va="center", fontsize=11, color="white")
    ax.text(1.7, 7.2, "• Tool Responses", ha="center", va="center", fontsize=11, color="white")
    ax.text(1.7, 6.8, "• Agent Messages", ha="center", va="center", fontsize=11, color="white")

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
                ("Tripwire Monitor", "Canary belief\nverification", r"$c_i \in \mathcal{B}$?"),
                ("Provenance Tracker", "Source chain\nattribution", "P: B → sources"),
            ],
        },
        {
            "name": "AGENT LAYER",
            "y": 3.2,
            "height": 2.2,
            "color": colors["agent"],
            "components": [
                ("Beliefs (B)", "Propositions\n" + r"$P(b) \in [0,1]$", "verified/provisional"),
                (
                    "Goals (G)",
                    "Objectives\n" + r"$\langle \mathcal{G}, \prec \rangle$ ordered",
                    "priority queue",
                ),
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
                ("Quorum Verification", "k-of-n approval\nconsensus protocol", "BFT: n≥3f+1"),
                ("State Consistency", "Cross-agent\nvalidation", "Byzantine tolerance"),
            ],
        },
    ]

    # Draw layers
    for layer in layers:
        layer_box = FancyBboxPatch(
            (3.0, layer["y"]),
            12.3,
            layer["height"],
            boxstyle="round,pad=0.02",
            facecolor=layer["color"],
            edgecolor="black",
            linewidth=2,
            alpha=0.15,
        )
        ax.add_patch(layer_box)

        ax.text(
            3.3,
            layer["y"] + layer["height"] - 0.25,
            layer["name"],
            fontsize=12,
            fontweight="bold",
            color=colors["header"],
        )

        n_comp = len(layer["components"])
        comp_width = 3.6 if n_comp <= 3 else 2.7
        gap = 0.3
        start_x = 3.3

        for i, (name, desc, formula) in enumerate(layer["components"]):
            x = start_x + i * (comp_width + gap)
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
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] - 0.6,
                name,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=colors["header"],
            )
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] / 2 - 0.1,
                desc,
                ha="center",
                va="center",
                fontsize=10,
                color="#5D6D7E",
                linespacing=1.2,
            )
            ax.text(
                x + comp_width / 2,
                layer["y"] + 0.4,
                formula,
                ha="center",
                va="center",
                fontsize=10,
                style="italic",
                color=layer["color"],
                fontfamily="monospace",
                weight="bold",
            )

    # No metrics panel.
    #
    # This figure belongs to the theory paper, which measures nothing: it has
    # no evaluation artifacts, no corpus and no pipeline run of its own. A
    # "KEY METRICS" box here can only be transcribed from somewhere else or
    # invented, and both go stale silently because there is no artifact in this
    # project for a gate to compare them against. Detection rates, false
    # positives and latency are reported in Part 2, beside the runs that
    # produced them, and the caption points a reader there.
    ax.text(
        1.7,
        2.2,
        "Detection rates, false-positive\nrates and latency are reported\nin Part 2, with the runs\nthat produced them.",
        ha="center",
        va="center",
        fontsize=9,
        style="italic",
        color=colors["header"],
    )

    plt.tight_layout()

    # Save outputs
    output_path_png = output_dir / "cif_comprehensive.png"
    output_path_pdf = output_dir / "cif_comprehensive.pdf"
    plt.savefig(output_path_png, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf
