"""Defense Composition module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import json
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


#: Where the measured overlap lives. Written by scripts/run_defense_overlap.py.
_OVERLAP_PATH = Path(__file__).resolve().parents[3] / "output" / "data" / "defense_overlap.json"

#: How many mechanism rows the figure has room for, strongest first.
_TABLE_ROWS = 4

#: Display names for the modules the artifact measures.
_DISPLAY_NAME = {
    "firewall": "Firewall",
    "sandbox": "Sandbox",
    "tripwire": "Tripwire",
    "detection": "Anomaly",
    "trust": "Trust",
    "consensus": "Consensus",
    "provenance": "Provenance",
    "invariants": "Invariants",
}


def _load_overlap() -> dict:
    """Read the measured overlap, or refuse to draw the figure.

    Failing closed matters more here than anywhere else in this module: the
    whole defect being repaired is a table that looked measured and was not, so
    a fallback to plausible defaults would reintroduce it in a form that is
    harder to see.
    """
    if not _OVERLAP_PATH.is_file():
        raise FileNotFoundError(
            f"{_OVERLAP_PATH} is missing; run scripts/run_defense_overlap.py. "
            f"This figure reports measured detection overlap and has no "
            f"stand-in values to fall back on."
        )
    payload = json.loads(_OVERLAP_PATH.read_text(encoding="utf-8"))
    if not payload.get("per_module"):
        raise ValueError(f"{_OVERLAP_PATH} records no per-module rates")
    return payload


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

    # Detection statistics table, measured.
    #
    # Sixteen of these twenty cells used to be literal percentage strings, and
    # the Full CIF row was computed by feeding the four literal totals through
    # the series-composition rule -- so the one derived number could only ever
    # agree with the numbers it was derived from, and the table read as a
    # measurement of four mechanisms plus a confirmation of a theorem while
    # measuring nothing at all.
    #
    # Every cell now comes from output/data/defense_overlap.json. The union row
    # is the measured fraction of attacks at least one module detects, and the
    # series prediction is annotated beside it rather than substituted for it:
    # the rule assumes the modules are independent, and how far that is from
    # true is a result, not a detail.
    overlap = _load_overlap()
    per_module = overlap["per_module"]
    ranked = sorted(per_module, key=lambda n: per_module[n]["total"], reverse=True)

    stats_data = [("Defense", "Unique", "Shared", "Total")]
    for name in ranked[:_TABLE_ROWS]:
        row = per_module[name]
        stats_data.append(
            (
                _DISPLAY_NAME.get(name, name.replace("_", " ").title()),
                f"{row['unique'] * 100:.1f}%",
                f"{row['shared'] * 100:.1f}%",
                f"{row['total'] * 100:.1f}%",
            )
        )
    union = overlap["union"]["tpr"]
    stats_data.append(("Full CIF", "-", "-", f"{union * 100:.1f}%"))

    composition = overlap["composition"]
    logger.info(
        "Defense composition — measured union %.1f%%, series rule predicts %.1f%% "
        "(error %+.1f points), parallel-max predicts %.1f%%",
        union * 100,
        composition["series_prediction"] * 100,
        composition["series_error"] * 100,
        composition["parallel_max_prediction"] * 100,
    )

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

    # Show the composition rule against the measurement, not in place of it.
    # This line used to print the rule's own output as though it were the
    # pipeline's rate; the two are now printed side by side, because the gap
    # between them is the only thing the comparison can tell a reader.
    ax.text(
        0,
        -2.6,
        r"Series composition: $P_{detect} = 1 - \prod_{i}(1 - r_i)$"
        f"  →  {composition['series_prediction'] * 100:.1f}%"
        f"   (measured union {union * 100:.1f}%,"
        f" error {composition['series_error'] * 100:+.1f} pts)",
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
