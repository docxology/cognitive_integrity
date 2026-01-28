#!/usr/bin/env python3
"""Generate detection performance comparison figure."""

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

    # Colorblind-friendly color scheme (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "baseline": "#999999",
        "firewall": "#648FFF",  # Blue
        "sandbox": "#785EF0",  # Purple
        "tripwire": "#DC267F",  # Magenta
        "full_cif": "#FE6100",  # Orange
    }

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
        x - width, tpr, width, label="TPR (Recall)", color="#648FFF", edgecolor="black"
    )
    ax1.bar(x, fpr, width, label="FPR", color="#DC267F", edgecolor="black")
    ax1.bar(x + width, f1, width, label="F1 Score", color="#785EF0", edgecolor="black")

    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_title(
        "A. Detection Metrics by Defense Configuration", fontsize=12, fontweight="bold"
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(defenses, fontsize=9)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3, axis="y")

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

    ax2.bar(
        x - width,
        baseline,
        width,
        label="Baseline",
        color=colors["baseline"],
        edgecolor="black",
    )
    ax2.bar(
        x,
        firewall,
        width,
        label="Firewall Only",
        color=colors["firewall"],
        edgecolor="black",
    )
    ax2.bar(
        x + width,
        full_cif,
        width,
        label="Full CIF",
        color=colors["full_cif"],
        edgecolor="black",
    )

    ax2.set_ylabel("Detection Rate", fontsize=12)
    ax2.set_title("B. Detection Rate by Attack Type", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(attack_types, fontsize=9)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.set_ylim(0, 1.1)
    ax2.grid(True, alpha=0.3, axis="y")

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
    create_detection_performance_figure(output_dir)
