#!/usr/bin/env python3
"""Generate defense composition Venn diagram visualization."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch


def create_defense_composition_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Create Venn diagram showing overlapping detection capabilities.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # Set up professional styling
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 11,
            "axes.linewidth": 1.5,
        }
    )

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colorblind-friendly palette
    colors = {
        "firewall": "#648FFF",
        "sandbox": "#785EF0",
        "tripwire": "#DC267F",
        "anomaly": "#FE6100",
    }

    # Circle positions for 4-way Venn (approximate)
    circles = [
        ((-0.7, 0.6), 1.3, colors["firewall"], "Cognitive\nFirewall"),
        ((0.7, 0.6), 1.3, colors["sandbox"], "Belief\nSandbox"),
        ((-0.7, -0.5), 1.3, colors["tripwire"], "Tripwire\nMonitor"),
        ((0.7, -0.5), 1.3, colors["anomaly"], "Anomaly\nDetection"),
    ]

    # Draw circles with transparency
    for (x, y), radius, color, label in circles:
        circle = Circle(
            (x, y), radius, facecolor=color, edgecolor="black", linewidth=2, alpha=0.4
        )
        ax.add_patch(circle)

    # Add labels for each defense (outside circles)
    label_positions = [
        (-1.8, 1.8, "Cognitive\nFirewall", colors["firewall"]),
        (1.8, 1.8, "Belief\nSandbox", colors["sandbox"]),
        (-1.8, -1.8, "Tripwire\nMonitor", colors["tripwire"]),
        (1.8, -1.8, "Anomaly\nDetection", colors["anomaly"]),
    ]

    for x, y, label, color in label_positions:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=color,
        )

    # Attack types in each region
    # Unique to each defense
    unique_attacks = [
        (-1.6, 0.6, "Prompt\nInjection", 10),  # Firewall only
        (1.6, 0.6, "Belief\nPoisoning", 10),  # Sandbox only
        (-1.6, -0.5, "Identity\nSpoof", 10),  # Tripwire only
        (1.6, -0.5, "Behavioral\nDrift", 10),  # Anomaly only
    ]

    for x, y, label, size in unique_attacks:
        ax.text(
            x, y, label, ha="center", va="center", fontsize=9, style="italic", alpha=0.9
        )

    # Pairwise overlaps
    overlap_attacks = [
        (0, 1.2, "Input\nManipulation"),  # Firewall + Sandbox
        (-1.1, 0, "Authority\nExploits"),  # Firewall + Tripwire
        (1.1, 0, "State\nCorruption"),  # Sandbox + Anomaly
        (0, -1.1, "Covert\nChannels"),  # Tripwire + Anomaly
        (-0.3, 0.1, "Coordinated\nAttacks"),  # Firewall + Tripwire + Anomaly
        (0.3, 0.1, "Gradual\nDrift"),  # Sandbox + Tripwire + Anomaly
    ]

    for x, y, label in overlap_attacks:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            color="#2C3E50",
        )

    # Center: All four overlap
    ax.text(
        0,
        0.05,
        "Full\nCIF",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#2C3E50",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="black"),
    )

    # Title
    ax.text(
        0,
        3.2,
        "Defense Mechanism Detection Overlap",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    # Detection statistics table
    stats_data = [
        ("Defense", "Unique", "Shared", "Total"),
        ("Firewall", "23%", "35%", "58%"),
        ("Sandbox", "18%", "42%", "60%"),
        ("Tripwire", "15%", "53%", "68%"),
        ("Anomaly", "12%", "48%", "60%"),
        ("Full CIF", "-", "94%", "94%"),
    ]

    table_x, table_y = 2.2, -2.5
    cell_width, cell_height = 0.55, 0.3

    for i, row in enumerate(stats_data):
        for j, cell in enumerate(row):
            x = table_x - 1.1 + j * cell_width
            y = table_y - i * cell_height

            if i == 0:  # Header
                ax.text(
                    x, y, cell, ha="center", va="center", fontsize=9, fontweight="bold"
                )
            elif i == len(stats_data) - 1:  # Full CIF row
                ax.text(
                    x,
                    y,
                    cell,
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color="#648FFF",
                )  # Colorblind-friendly blue
            else:
                ax.text(x, y, cell, ha="center", va="center", fontsize=9)

    # Add legend for attack categories
    legend_y = 2.5
    legend_items = [
        (colors["firewall"], "Input-layer attacks"),
        (colors["sandbox"], "Belief-layer attacks"),
        (colors["tripwire"], "Identity-layer attacks"),
        (colors["anomaly"], "Behavioral attacks"),
    ]

    for i, (color, label) in enumerate(legend_items):
        rect = mpatches.Rectangle(
            (-2.8 + i * 1.6, legend_y),
            0.2,
            0.2,
            facecolor=color,
            edgecolor="black",
            alpha=0.7,
        )
        ax.add_patch(rect)
        ax.text(
            -2.55 + i * 1.6, legend_y + 0.1, label, ha="left", va="center", fontsize=9
        )

    plt.tight_layout()

    # Save as both PNG and PDF
    output_png = output_dir / "defense_composition.png"
    output_pdf = output_dir / "defense_composition.pdf"

    plt.savefig(
        output_png, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.savefig(output_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_png))
    print(str(output_pdf))
    return output_png, output_pdf


if __name__ == "__main__":
    # Derive base_dir from the script's actual location
    # Script is at: projects/{project_name}/scripts/{script}.py
    script_dir = Path(__file__).resolve().parent  # scripts/
    base_dir = script_dir.parent  # projects/{project_name}/
    
    output_dir = base_dir / "output" / "figures"
    create_defense_composition_figure(output_dir)
