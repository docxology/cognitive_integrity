#!/usr/bin/env python3
"""Generate false positive mitigation figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def create_fp_mitigation_figure(output_dir: Path) -> Path:
    """
    Create false positive mitigation visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: FPR by verification stage
    ax1 = axes[0]

    stages = [
        "Raw\nDetection",
        "After Pattern\nFiltering",
        "After Context\nAnalysis",
        "After Multi-\nDetector Vote",
        "After Human\nReview Queue",
    ]
    fpr_values = [0.15, 0.09, 0.06, 0.04, 0.02]
    tpr_values = [0.98, 0.96, 0.94, 0.93, 0.92]

    x = np.arange(len(stages))
    width = 0.35

    # Colorblind-friendly colors (IBM Design)
    bars1 = ax1.bar(
        x - width / 2,
        fpr_values,
        width,
        label="FPR",
        color="#DC267F",
        edgecolor="black",
    )  # Magenta
    bars2 = ax1.bar(
        x + width / 2,
        tpr_values,
        width,
        label="TPR (retained)",
        color="#648FFF",
        edgecolor="black",
    )  # Blue

    # Add value labels
    for bar, val in zip(bars1, fpr_values):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    for bar, val in zip(bars2, tpr_values):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax1.set_ylabel("Rate", fontsize=12)
    ax1.set_title(
        "A. FPR Reduction Through Verification Pipeline", fontsize=12, fontweight="bold"
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(stages, fontsize=9)
    ax1.legend(loc="center right", fontsize=10)
    ax1.set_ylim(0, 1.15)
    ax1.grid(True, alpha=0.3, axis="y")

    # Draw arrows showing reduction
    for i in range(len(fpr_values) - 1):
        reduction = (fpr_values[i] - fpr_values[i + 1]) / fpr_values[i] * 100
        ax1.annotate(
            f"−{reduction:.0f}%",
            xy=(i + 0.5, max(fpr_values[i], fpr_values[i + 1]) + 0.03),
            fontsize=8,
            ha="center",
            color="#DC267F",
        )  # Colorblind-friendly magenta

    # Panel B: Threshold sensitivity analysis
    ax2 = axes[1]

    thresholds = np.linspace(0.3, 0.9, 7)
    tpr_curve = [0.98, 0.96, 0.94, 0.91, 0.87, 0.79, 0.72]
    fpr_curve = [0.18, 0.12, 0.06, 0.04, 0.02, 0.01, 0.01]

    ax2_twin = ax2.twinx()

    # Colorblind-friendly colors (IBM Design)
    (line1,) = ax2.plot(
        thresholds,
        tpr_curve,
        "o-",
        color="#648FFF",
        linewidth=2,
        markersize=8,
        label="TPR",
    )  # Blue
    (line2,) = ax2_twin.plot(
        thresholds,
        fpr_curve,
        "s-",
        color="#DC267F",
        linewidth=2,
        markersize=8,
        label="FPR",
    )  # Magenta

    # Mark optimal threshold (colorblind-friendly)
    optimal_idx = 2  # threshold = 0.5
    ax2.axvline(
        x=thresholds[optimal_idx],
        color="#785EF0",
        linestyle="--",
        linewidth=2,
        alpha=0.7,
    )  # Purple
    ax2.annotate(
        f"Optimal τ = {thresholds[optimal_idx]:.1f}\nTPR={tpr_curve[optimal_idx]:.2f}, FPR={fpr_curve[optimal_idx]:.2f}",
        xy=(thresholds[optimal_idx], tpr_curve[optimal_idx]),
        xytext=(0.65, 0.85),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="#785EF0"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#785EF0"),
    )

    ax2.set_xlabel("Detection Threshold (τ)", fontsize=12)
    ax2.set_ylabel("True Positive Rate", fontsize=12, color="#648FFF")
    ax2_twin.set_ylabel("False Positive Rate", fontsize=12, color="#DC267F")
    ax2.set_title("B. Threshold Sensitivity Analysis", fontsize=12, fontweight="bold")

    ax2.tick_params(axis="y", labelcolor="#648FFF")
    ax2_twin.tick_params(axis="y", labelcolor="#DC267F")

    ax2.set_ylim(0.6, 1.05)
    ax2_twin.set_ylim(0, 0.25)
    ax2.grid(True, alpha=0.3)

    # Combined legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="center right", fontsize=10)

    plt.tight_layout()

    # Save both PNG and PDF
    output_path_png = output_dir / "fp_mitigation.png"
    output_path_pdf = output_dir / "fp_mitigation.pdf"

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
    create_fp_mitigation_figure(output_dir)
