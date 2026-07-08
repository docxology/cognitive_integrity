"""
Figure 19: CIF-AD Coupling Matrix Visualization (v2.0)

Generates a heatmap visualization of the CIF-AD coupling matrix showing
defense mechanism coverage across Action-Delegation cycle phases.
"""

import sys
from pathlib import Path

# Locate repo root and add project to path
_this = Path(__file__).resolve()
_project_root = _this.parent.parent  # cogsec_multiagent_1_theory/
sys.path.insert(0, str(_project_root))
for _p in _this.parents:
    if (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        break

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from src.cif_ad_coupling import (
    ADPhase,
    CIFADCouplingDetector,
)

OUTPUT_DIR = _this.parent.parent / "output" / "figures"
DATA_DIR = _this.parent.parent / "output" / "figures" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_cif_ad_coupling_figure() -> dict:
    """Generate CIF-AD coupling matrix heatmap."""
    detector = CIFADCouplingDetector()
    defense_names, phase_names, matrix = detector.coverage_heatmap_data()

    # Human-readable labels
    defense_labels = [
        "Cognitive\nFirewall",
        "Belief\nSandbox",
        "Trust\nCalculus",
        "Tripwires +\nInvariants",
        "Byzantine\nConsensus",
    ]
    phase_labels = ["Plan", "Delegate", "Execute", "Observe", "Update"]

    # Custom colormap: white → light blue → deep blue
    colors = ["#f8f9fa", "#a8c7e8", "#2c6fad"]
    cmap = LinearSegmentedColormap.from_list("cif_coverage", colors, N=256)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2, 1]})

    # ── Panel A: Coupling matrix heatmap ─────────────────────────────────────
    ax = axes[0]
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0.0, vmax=1.0)

    # Annotate cells with values
    for i in range(len(defense_labels)):
        for j in range(len(phase_labels)):
            val = matrix[i, j]
            color = "white" if val > 0.7 else "black"
            ax.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=color,
            )

    ax.set_xticks(range(len(phase_labels)))
    ax.set_xticklabels(phase_labels, fontsize=11)
    ax.set_yticks(range(len(defense_labels)))
    ax.set_yticklabels(defense_labels, fontsize=10)
    ax.set_xlabel("Action-Delegation (AD) Phase", fontsize=12)
    ax.set_ylabel("CIF Defense Mechanism", fontsize=12)
    ax.set_title("CIF-AD Coupling Matrix\n$M_{AD}$: Coverage(Defense$_i$, Phase$_j$)", fontsize=13)

    cbar = plt.colorbar(im, ax=ax, shrink=0.9)
    cbar.set_label("Coverage Score", fontsize=11)

    # Highlight column maxima (best defense per phase)
    for j in range(len(phase_labels)):
        col = matrix[:, j]
        best_i = int(np.argmax(col))
        rect = plt.Rectangle(
            (j - 0.5, best_i - 0.5), 1, 1, linewidth=2.5, edgecolor="#e63946", facecolor="none"
        )
        ax.add_patch(rect)

    # ── Panel B: Per-phase combined coverage (product formula) ───────────────
    ax2 = axes[1]
    combined_coverage = [detector.get_combined_coverage(phase) for phase in ADPhase]
    max_coverage = [detector.get_phase_coverage(phase) for phase in ADPhase]

    x = np.arange(len(phase_labels))
    width = 0.35

    ax2.bar(
        x - width / 2,
        max_coverage,
        width,
        label="Best Single Defense",
        color="#a8c7e8",
        edgecolor="white",
        linewidth=0.5,
    )
    bars2 = ax2.bar(
        x + width / 2,
        combined_coverage,
        width,
        label="Full Stack (Combined)",
        color="#2c6fad",
        edgecolor="white",
        linewidth=0.5,
    )

    # Threshold line
    ax2.axhline(
        y=0.50, color="#e63946", linestyle="--", linewidth=1.5, label="Min. Coverage τ = 0.50"
    )

    ax2.set_xticks(x)
    ax2.set_xticklabels(phase_labels, fontsize=10)
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("Coverage Score", fontsize=11)
    ax2.set_title("Phase Coverage:\nBest Single vs. Full Stack", fontsize=12)
    ax2.legend(fontsize=9, loc="lower right")

    for bar in bars2:
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{bar.get_height():.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.suptitle(
        "CIF-AD Coupling Analysis (Second Edition, v2.0)", fontsize=14, fontweight="bold", y=1.02
    )

    plt.tight_layout()

    # Save
    for ext in ["pdf", "png"]:
        fig.savefig(OUTPUT_DIR / f"cif_ad_coupling.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Save data
    data = {
        "defense_names": defense_names,
        "phase_names": phase_names,
        "coupling_matrix": matrix.tolist(),
        "combined_coverage": {p.value: detector.get_combined_coverage(p) for p in ADPhase},
        "max_coverage": {p.value: detector.get_phase_coverage(p) for p in ADPhase},
        "full_coverage_theorem_holds": detector.verify_full_coverage_theorem(),
        "minimum_viable_portfolio": [
            d.value for d in detector.minimum_viable_portfolio(min_phase_coverage=0.80)
        ],
    }
    with open(DATA_DIR / "cif_ad_coupling.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Saved: cif_ad_coupling.pdf/png, cif_ad_coupling.json")
    print(f"Full coverage theorem holds: {data['full_coverage_theorem_holds']}")
    print(f"Combined coverage by phase: {data['combined_coverage']}")
    return data


if __name__ == "__main__":
    generate_cif_ad_coupling_figure()
