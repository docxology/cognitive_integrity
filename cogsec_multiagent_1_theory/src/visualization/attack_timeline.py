"""Attack Timeline module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Attack timeline visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


def create_attack_timeline_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Create attack timeline visualization.
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

    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Colorblind-friendly phase colors (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "normal": "#648FFF",  # Blue
        "attack": "#DC267F",  # Magenta
        "detection": "#FFB000",  # Yellow
        "response": "#785EF0",  # Purple
        "recovery": "#FE6100",  # Orange
        "timeline": "#2C3E50",
        "metric_high": "#648FFF",  # Blue
        "metric_low": "#DC267F",  # Magenta
    }

    # Timeline base
    timeline_y = 5
    ax.annotate(
        "",
        xy=(95, timeline_y),
        xytext=(5, timeline_y),
        arrowprops=dict(arrowstyle="->", color=colors["timeline"], lw=3),
    )

    # Phase definitions (start, end, color, label)
    phases = [
        (5, 30, colors["normal"], "Normal\nOperation", "T0-T25"),
        (30, 40, colors["attack"], "Attack\nInjection", "T25-T35"),
        (40, 55, colors["detection"], "Detection\n& Analysis", "T35-T50"),
        (55, 72, colors["response"], "Response\nExecution", "T50-T65"),
        (72, 92, colors["recovery"], "Recovery\n& Hardening", "T65-T87"),
    ]

    # Draw phase blocks
    for start, end, color, label, time_label in phases:
        width = end - start
        rect = FancyBboxPatch(
            (start, timeline_y - 1.2),
            width,
            2.4,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="black",
            linewidth=1.5,
            alpha=0.7,
        )
        ax.add_patch(rect)

        # Phase label (above)
        ax.text(
            (start + end) / 2,
            timeline_y + 1.8,
            label,
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

        # Time label (below)
        ax.text(
            (start + end) / 2,
            timeline_y - 1.6,
            time_label,
            ha="center",
            va="top",
            fontsize=11,
            color="gray",
        )

    # Add key events as markers
    events = [
        (30, "Attack\nInjected", colors["attack"]),
        (42, "Tripwire\nTriggered", colors["detection"]),
        (48, "Anomaly\nConfirmed", colors["detection"]),
        (55, "Quarantine\nActivated", colors["response"]),
        (62, "Trust\nReset", colors["response"]),
        (72, "System\nRestored", colors["recovery"]),
    ]

    for x, label, color in events:
        ax.plot(
            [x, x],
            [timeline_y - 1.5, timeline_y + 1.5],
            "--",
            color=color,
            linewidth=2,
            alpha=0.8,
        )
        ax.scatter(
            [x],
            [timeline_y + 1.5],
            s=100,
            c=color,
            edgecolors="black",
            linewidth=1.5,
            zorder=5,
        )
        ax.text(
            x,
            timeline_y + 2.5,
            label,
            ha="center",
            va="bottom",
            fontsize=10,
            style="italic",
        )

    # Add metrics subplot (belief integrity)
    np.random.seed(42)
    time_points = np.linspace(5, 92, 200)

    # Belief integrity over time
    integrity = np.ones_like(time_points)

    # Normal operation: stable high
    normal_mask = time_points < 30
    integrity[normal_mask] = 0.95 + np.random.normal(0, 0.02, np.sum(normal_mask))

    # Attack: integrity drops
    attack_mask = (time_points >= 30) & (time_points < 40)
    t_attack = time_points[attack_mask] - 30
    integrity[attack_mask] = (
        0.95 - 0.5 * (t_attack / 10) + np.random.normal(0, 0.03, np.sum(attack_mask))
    )

    # Detection: stabilizes at low
    detect_mask = (time_points >= 40) & (time_points < 55)
    integrity[detect_mask] = 0.45 + np.random.normal(0, 0.03, np.sum(detect_mask))

    # Response: starts recovering
    response_mask = (time_points >= 55) & (time_points < 72)
    t_response = time_points[response_mask] - 55
    integrity[response_mask] = (
        0.45
        + 0.4 * (t_response / 17)
        + np.random.normal(0, 0.02, np.sum(response_mask))
    )

    # Recovery: back to normal
    recovery_mask = time_points >= 72
    t_recovery = time_points[recovery_mask] - 72
    integrity[recovery_mask] = (
        0.85
        + 0.1 * (1 - np.exp(-t_recovery / 5))
        + np.random.normal(0, 0.01, np.sum(recovery_mask))
    )

    integrity = np.clip(integrity, 0, 1)

    # Scale to plot area
    metric_y_base = 1.5
    metric_height = 2.5
    scaled_integrity = metric_y_base + integrity * metric_height

    ax.fill_between(
        time_points,
        metric_y_base,
        scaled_integrity,
        alpha=0.3,
        color=colors["metric_high"],
    )
    ax.plot(time_points, scaled_integrity, "-", color=colors["timeline"], linewidth=2)

    # Add threshold line
    threshold_y = metric_y_base + 0.7 * metric_height
    ax.axhline(
        y=threshold_y,
        xmin=0.05,
        xmax=0.95,
        color="red",
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
    )
    ax.text(
        97,
        threshold_y,
        "Alert\nThreshold",
        ha="left",
        va="center",
        fontsize=8,
        color="red",
    )

    # Metric labels
    ax.text(
        2,
        metric_y_base + metric_height / 2,
        "Belief\nIntegrity",
        ha="right",
        va="center",
        fontsize=10,
        fontweight="bold",
        rotation=0,
    )
    ax.text(2, metric_y_base, "0.0", ha="right", va="center", fontsize=9)
    ax.text(
        2, metric_y_base + metric_height, "1.0", ha="right", va="center", fontsize=9
    )

    # Add second metric: Trust level
    trust_y_base = 7
    trust_height = 1.5

    trust = np.ones_like(time_points)
    trust[normal_mask] = 0.9 + np.random.normal(0, 0.02, np.sum(normal_mask))
    trust[attack_mask] = (
        0.9 - 0.3 * (t_attack / 10) + np.random.normal(0, 0.02, np.sum(attack_mask))
    )
    trust[detect_mask] = 0.6 + np.random.normal(0, 0.02, np.sum(detect_mask))
    trust[(time_points >= 55) & (time_points < 62)] = 0.1 + np.random.normal(
        0, 0.02, np.sum((time_points >= 55) & (time_points < 62))
    )
    trust[(time_points >= 62) & (time_points < 72)] = (
        0.5
        + 0.3 * ((time_points[(time_points >= 62) & (time_points < 72)] - 62) / 10)
        + np.random.normal(0, 0.02, np.sum((time_points >= 62) & (time_points < 72)))
    )
    trust[recovery_mask] = (
        0.8
        + 0.15 * (1 - np.exp(-t_recovery / 8))
        + np.random.normal(0, 0.01, np.sum(recovery_mask))
    )
    trust = np.clip(trust, 0, 1)

    scaled_trust = trust_y_base + trust * trust_height

    ax.fill_between(
        time_points, trust_y_base, scaled_trust, alpha=0.3, color=colors["response"]
    )
    ax.plot(time_points, scaled_trust, "-", color=colors["response"], linewidth=2)

    ax.text(
        2,
        trust_y_base + trust_height / 2,
        "Inter-Agent\nTrust",
        ha="right",
        va="center",
        fontsize=10,
        fontweight="bold",
        rotation=0,
    )

    ax.text(
        50,
        9.6,
        "ATTACK LIFECYCLE: DETECTION THROUGH RECOVERY",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
    )
    ax.text(
        50,
        9.1,
        "Example Trace — Illustrative simulation of CIF defense mechanisms",
        ha="center",
        va="center",
        fontsize=14,
        style="italic",
        color="#555555",
    )

    # Legend
    legend_elements = [
        mpatches.Patch(
            facecolor=colors["normal"], edgecolor="black", label="Normal Operation"
        ),
        mpatches.Patch(
            facecolor=colors["attack"], edgecolor="black", label="Attack Phase"
        ),
        mpatches.Patch(
            facecolor=colors["detection"],
            edgecolor="black",
            label="Detection & Analysis",
        ),
        mpatches.Patch(
            facecolor=colors["response"], edgecolor="black", label="Response Execution"
        ),
        mpatches.Patch(
            facecolor=colors["recovery"],
            edgecolor="black",
            label="Recovery & Hardening",
        ),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper right",
        fontsize=9,
        ncol=2,
        frameon=True,
        fancybox=True,
        framealpha=0.95,
    )

    plt.tight_layout()

    # Save as both PNG and PDF
    output_png = output_dir / "attack_timeline.png"
    output_pdf = output_dir / "attack_timeline.pdf"

    plt.savefig(
        output_png, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.savefig(output_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_png))
    print(str(output_pdf))
    return output_png, output_pdf
