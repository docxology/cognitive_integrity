"""Detection Performance module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Detection performance visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def create_detection_performance_figure(output_dir: Path) -> Path:
    """
    Create detection performance comparison visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Colorblind-friendly color scheme (IBM Design) - Standardized
    colors = {
        "baseline": "#999999",
        "firewall": "#648FFF",  # Blue
        "sandbox": "#785EF0",  # Purple
        "tripwire": "#DC267F",  # Magenta
        "full_cif": "#FE6100",  # Orange
    }

    # Increase font sizes globally for this figure
    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.labelsize": 14,
            "axes.titlesize": 14,
            "xtick.labelsize": 11,
            "ytick.labelsize": 12,
            "legend.fontsize": 11,
        }
    )

    # Panel A: Overall detection by defense configuration
    ax1 = axes[0]
    defenses = [
        "Baseline",
        "Firewall\nOnly",
        "Sandbox\nOnly",
        "Tripwires\nOnly",
        "Invariants\nOnly",
        "Full CIF",
    ]
    tpr = [0.00, 0.78, 0.65, 0.82, 0.71, 0.94]
    fpr = [0.00, 0.12, 0.05, 0.08, 0.03, 0.06]
    f1 = [0.00, 0.82, 0.77, 0.86, 0.82, 0.94]

    x = np.arange(len(defenses))
    width = 0.25

    ax1.bar(
        x - width,
        tpr,
        width,
        label="Recall (TPR)",
        color="#648FFF",
        edgecolor="black",
        linewidth=0.8,
    )
    ax1.bar(
        x,
        fpr,
        width,
        label="False Positive Rate",
        color="#DC267F",
        edgecolor="black",
        linewidth=0.8,
    )
    ax1.bar(
        x + width, f1, width, label="F1 Score", color="#785EF0", edgecolor="black", linewidth=0.8
    )

    ax1.set_ylabel("Metric Score (0-1)", fontweight="bold")
    ax1.set_title("A. Detection Metrics by Defense Configuration", fontweight="bold", pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(defenses, rotation=0)
    ax1.legend(loc="upper left", frameon=True, framealpha=0.9)
    ax1.set_ylim(0, 1.15)
    ax1.grid(True, alpha=0.2, axis="y")

    # Panel B: Detection rate by attack type
    ax2 = axes[1]
    attack_types = [
        "Prompt\nInjection",
        "Trust\nExploit",
        "Belief\nManip.",
        "Coordination",
        "Temporal",
    ]
    baseline = [0.0, 0.0, 0.0, 0.0, 0.0]
    firewall = [0.85, 0.62, 0.71, 0.58, 0.45]
    full_cif = [0.96, 0.91, 0.93, 0.89, 0.87]

    x = np.arange(len(attack_types))
    width = 0.25

    # Phantom bars for baseline to show it was tested but resulted in 0
    ax2.bar(
        x - width,
        baseline,
        width,
        label="Baseline (No Defense)",
        color=colors["baseline"],
        edgecolor="black",
        hatch="//",
        alpha=0.3,
    )
    # Add annotation for baseline = 0
    ax2.text(0 - width, 0.02, "0.0", ha="center", va="bottom", fontsize=8, color="#666")

    ax2.bar(
        x,
        firewall,
        width,
        label="Firewall Only",
        color=colors["firewall"],
        edgecolor="black",
        linewidth=0.8,
    )
    ax2.bar(
        x + width,
        full_cif,
        width,
        label="Full CIF",
        color=colors["full_cif"],
        edgecolor="black",
        linewidth=0.8,
    )

    ax2.set_ylabel("Detection Rate", fontweight="bold")
    ax2.set_title("B. Detection Rate by Attack Type", fontweight="bold", pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(attack_types, rotation=0)
    ax2.legend(loc="upper right", frameon=True, framealpha=0.9)
    ax2.set_ylim(0, 1.15)
    ax2.grid(True, alpha=0.2, axis="y")

    plt.tight_layout()

    # Save both PNG and PDF
    output_path_png = output_dir / "detection_performance.png"
    output_path_pdf = output_dir / "detection_performance.pdf"

    plt.savefig(
        output_path_png,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf
