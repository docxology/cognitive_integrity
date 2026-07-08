"""Defense Composition module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from composition.algebra import (
    compute_parallel_detection_rate,
    compute_series_detection_rate,
)

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

logger = logging.getLogger(__name__)


def plot_defense_composition(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate defense composition Venn diagram visualization."""
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Apply style
    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colorblind-friendly palette
    colors = {
        "firewall": SEMANTIC_COLORS["firewall"],
        "sandbox": SEMANTIC_COLORS["sandbox"],
        "tripwire": SEMANTIC_COLORS["tripwire"],
        "anomaly": SEMANTIC_COLORS["anomaly"],
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
            x, y, label, ha="center", va="center", fontsize=FONTSIZE["base"], style="italic", alpha=0.9  # noqa: E501
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
            fontsize=FONTSIZE["small"],
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
    # Compute Full CIF rate dynamically using Theorem 3.1 (series composition)
    individual_totals = [0.58, 0.60, 0.68, 0.60]  # per-mechanism total rates
    full_cif_series = compute_series_detection_rate(individual_totals)
    full_cif_parallel = compute_parallel_detection_rate(individual_totals, strategy="max")
    logger.info(
        "Defense composition rates — series: %.2f%%, parallel (max): %.2f%%",
        full_cif_series * 100,
        full_cif_parallel * 100,
    )

    stats_data = [
        ("Defense", "Unique", "Shared", "Total"),
        ("Firewall", "23%", "35%", "58%"),
        ("Sandbox", "18%", "42%", "60%"),
        ("Tripwire", "15%", "53%", "68%"),
        ("Anomaly", "12%", "48%", "60%"),
        ("Full CIF", "-", f"{full_cif_series * 100:.0f}%", f"{full_cif_series * 100:.0f}%"),
    ]

    table_x, table_y = 2.0, -2.5  # Moved left slightly
    cell_width, cell_height = 0.65, 0.35 # Increased width and height

    for i, row in enumerate(stats_data):
        for j, cell in enumerate(row):
            x = table_x - 1.1 + j * cell_width
            y = table_y - i * cell_height

            if i == 0:  # Header
                ax.text(
                    x, y, cell, ha="center", va="center", fontsize=FONTSIZE["base"], fontweight="bold"  # noqa: E501
                )
            elif i == len(stats_data) - 1:  # Full CIF row
                ax.text(
                    x,
                    y,
                    cell,
                    ha="center",
                    va="center",
                    fontsize=FONTSIZE["base"],
                    fontweight="bold",
                    color=SEMANTIC_COLORS["firewall"], # Use blue for High Perf
                )
            else:
                ax.text(x, y, cell, ha="center", va="center", fontsize=FONTSIZE["base"])

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
            -2.55 + i * 1.6, legend_y + 0.1, label, ha="left", va="center", fontsize=FONTSIZE["base"]  # noqa: E501
        )

    # Show composition formula
    ax.text(
        0,
        -2.6,
        r"Series composition: $P_{detect} = 1 - \prod_{i}(1 - r_i)$"
        f"  →  {full_cif_series * 100:.0f}%",
        ha="center",
        va="center",
        fontsize=FONTSIZE["base"],
        fontstyle="italic",
        color="#2C3E50",
    )

    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/defense_composition.py")

    save_figure(fig, "defense_composition", output_dir=output_dir)
    return fig
