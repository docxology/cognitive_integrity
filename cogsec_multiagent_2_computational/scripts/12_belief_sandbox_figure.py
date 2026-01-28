#!/usr/bin/env python3
"""Generate belief sandbox flow diagram visualization."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                Rectangle)


def create_belief_sandbox_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Create flow diagram showing belief lifecycle.
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

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colorblind-friendly color scheme (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "input": "#648FFF",  # Blue
        "firewall": "#DC267F",  # Magenta
        "sandbox": "#FFB000",  # Yellow
        "verification": "#785EF0",  # Purple
        "verified": "#FE6100",  # Orange (verified)
        "rejected": "#999999",  # Gray
        "arrow": "#2C3E50",
        "box": "#ECF0F1",
    }

    def draw_box(x, y, width, height, label, sublabel, color):
        """Draw a process box with label."""
        box = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="black",
            linewidth=2,
            alpha=0.8,
        )
        ax.add_patch(box)
        ax.text(
            x + width / 2,
            y + height / 2 + 0.15,
            label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=(
                "white" if color not in [colors["box"], colors["rejected"]] else "black"
            ),
        )
        if sublabel:
            ax.text(
                x + width / 2,
                y + height / 2 - 0.25,
                sublabel,
                ha="center",
                va="center",
                fontsize=9,
                style="italic",
                color=(
                    "white"
                    if color not in [colors["box"], colors["rejected"]]
                    else "gray"
                ),
            )

    def draw_arrow(x1, y1, x2, y2, label=None, curved=False):
        """Draw an arrow between points."""
        if curved:
            style = f"arc3,rad=0.3"
        else:
            style = "arc3,rad=0"

        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="->", color=colors["arrow"], connectionstyle=style, lw=2
            ),
        )
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.text(
                mid_x,
                mid_y + 0.2,
                label,
                ha="center",
                va="bottom",
                fontsize=9,
                style="italic",
            )

    # Title
    ax.text(
        7,
        9.5,
        "Belief Sandbox: Provisional to Verified Lifecycle",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    # Stage 1: External Input
    draw_box(0.5, 7, 2, 1.2, "External", "Input", colors["input"])

    # Arrow to Firewall
    draw_arrow(2.5, 7.6, 3.5, 7.6)

    # Stage 2: Cognitive Firewall
    draw_box(3.5, 7, 2.5, 1.2, "Cognitive", "Firewall", colors["firewall"])

    # Decision diamond for firewall
    diamond_x, diamond_y = 7, 7.6
    diamond = plt.Polygon(
        [
            (diamond_x, diamond_y + 0.6),
            (diamond_x + 0.6, diamond_y),
            (diamond_x, diamond_y - 0.6),
            (diamond_x - 0.6, diamond_y),
        ],
        facecolor=colors["firewall"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(diamond)
    ax.text(
        diamond_x,
        diamond_y,
        "Safe?",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
    )

    draw_arrow(6, 7.6, 6.4, 7.6)

    # Reject path (down and out)
    draw_arrow(diamond_x, diamond_y - 0.6, diamond_x, 6)
    draw_box(6, 5.3, 2, 0.8, "REJECT", "", colors["rejected"])
    ax.text(diamond_x - 0.5, 6.5, "No", fontsize=9, color="red")

    # Accept path (right to sandbox)
    draw_arrow(diamond_x + 0.6, diamond_y, 8.5, diamond_y)
    ax.text(8, 7.9, "Yes", fontsize=9, color="green")

    # Stage 3: Belief Sandbox (main focus)
    sandbox_box = FancyBboxPatch(
        (8.5, 5),
        4.5,
        4,
        boxstyle="round,pad=0.02",
        facecolor=colors["sandbox"],
        edgecolor="black",
        linewidth=3,
        alpha=0.3,
    )
    ax.add_patch(sandbox_box)
    ax.text(
        10.75,
        8.7,
        "BELIEF SANDBOX",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=colors["sandbox"],
    )

    # Sandbox components
    draw_box(9, 7, 1.8, 0.8, "Parse", "", colors["box"])
    draw_box(11, 7, 1.8, 0.8, "Tag Source", "", colors["box"])
    draw_box(9, 5.8, 1.8, 0.8, "Create", "Provisional", colors["box"])
    draw_box(11, 5.8, 1.8, 0.8, "Set TTL", "", colors["box"])

    # Arrows within sandbox
    draw_arrow(10.8, 7.4, 11, 7.4)
    draw_arrow(9.9, 7, 9.9, 6.6)
    draw_arrow(10.8, 6.2, 11, 6.2)

    # Stage 4: Verification Queue
    draw_box(9.5, 3.5, 2.5, 1, "Verification", "Queue", colors["verification"])

    draw_arrow(10.75, 5, 10.75, 4.5)

    # Verification checks (parallel)
    checks_y = 2
    check_width = 2
    checks = [
        ("Tripwire\nCheck", 3.5),
        ("Consensus\nVerify", 6.5),
        ("Provenance\nTrace", 9.5),
    ]

    for label, x in checks:
        draw_box(x, checks_y, check_width, 0.9, label, "", colors["verification"])

    # Arrows from queue to checks
    draw_arrow(9.5, 3.5, 4.5, 2.9, curved=True)
    draw_arrow(10.75, 3.5, 7.5, 2.9)
    draw_arrow(12, 3.5, 10.5, 2.9, curved=True)

    # Final decision
    final_diamond_x, final_diamond_y = 7, 0.8
    final_diamond = plt.Polygon(
        [
            (final_diamond_x, final_diamond_y + 0.5),
            (final_diamond_x + 0.5, final_diamond_y),
            (final_diamond_x, final_diamond_y - 0.5),
            (final_diamond_x - 0.5, final_diamond_y),
        ],
        facecolor=colors["verification"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(final_diamond)
    ax.text(
        final_diamond_x,
        final_diamond_y,
        "Valid?",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
    )

    # Arrows from checks to final decision
    for label, x in checks:
        draw_arrow(x + 1, checks_y, final_diamond_x, final_diamond_y + 0.5)

    # Verified state (left)
    draw_box(1, 0.2, 2.5, 1.2, "VERIFIED", "Belief State", colors["verified"])
    draw_arrow(final_diamond_x - 0.5, final_diamond_y, 3.5, 0.8)
    ax.text(4.5, 1.1, "Yes", fontsize=9, color="green")

    # Expired/Rejected (right)
    draw_box(10.5, 0.2, 2.5, 1.2, "EXPIRED", "or Rejected", colors["rejected"])
    draw_arrow(final_diamond_x + 0.5, final_diamond_y, 10.5, 0.8)
    ax.text(9, 1.1, "No", fontsize=9, color="red")

    # Add annotations for key concepts
    annotations = [
        (2.25, 8.5, "Raw input from\nexternal sources"),
        (4.75, 8.5, "Pattern matching\n+ heuristics"),
        (10.75, 9.2, "Provisional beliefs with\nTTL and provenance"),
        (10.75, 2.8, "Multi-stage\nverification"),
        (2.25, -0.5, "Promoted to\ncore belief set"),
    ]

    for x, y, text in annotations:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=8,
            style="italic",
            color="gray",
        )

    # Legend
    legend_elements = [
        mpatches.Patch(
            facecolor=colors["input"], edgecolor="black", label="Input Stage"
        ),
        mpatches.Patch(
            facecolor=colors["firewall"], edgecolor="black", label="Firewall Stage"
        ),
        mpatches.Patch(
            facecolor=colors["sandbox"],
            edgecolor="black",
            label="Sandbox Stage",
            alpha=0.5,
        ),
        mpatches.Patch(
            facecolor=colors["verification"],
            edgecolor="black",
            label="Verification Stage",
        ),
        mpatches.Patch(
            facecolor=colors["verified"], edgecolor="black", label="Verified State"
        ),
        mpatches.Patch(
            facecolor=colors["rejected"], edgecolor="black", label="Rejected/Expired"
        ),
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        fontsize=9,
        frameon=True,
        fancybox=True,
        framealpha=0.95,
        bbox_to_anchor=(0, 1),
    )

    plt.tight_layout()

    # Save as both PNG and PDF
    output_png = output_dir / "belief_sandbox.png"
    output_pdf = output_dir / "belief_sandbox.pdf"

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
    create_belief_sandbox_figure(output_dir)
