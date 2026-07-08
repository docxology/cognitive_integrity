#!/usr/bin/env python3
"""
Script 07: CIF-AD-OODA Domain Coverage Figure
==============================================

Generates two figures summarizing the cross-domain analysis from the
merged Part 3+4 paper:

  1. Attack pattern distribution across 10 domains (stacked bar chart)
  2. CIF mechanism coverage matrix (heatmap)

These figures correspond to the cross-domain synthesis in §10
(10_cross_domain_discussion.md).

Usage:
    uv run python scripts/07_domain_coverage_figure.py

Output:
    output/figures/domain_coverage.png
    output/figures/domain_coverage.pdf
    output/figures/cif_mechanism_coverage.png
    output/figures/cif_mechanism_coverage.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Data: Attack Pattern Distribution (from §10, Table 4.1)
# ---------------------------------------------------------------------------
DOMAINS = [
    "1. Rare Earth Mining",
    "2. Nation-State Alliances",
    "3. Cyber-Security",
    "4. Drone Wars",
    "5. Supply Chain",
    "6. Biowarfare",
    "7. Food Security",
    "8. Trade Wars",
    "9. Infrastructure",
    "10. Fake News",
]
DOMAINS_SHORT = ["RE", "NS", "Cy", "Dr", "SC", "Bio", "FS", "TW", "Inf", "FN"]

# FR Polarity Inversion, Constraint Relaxation, Context Boundary Violation
ATTACK_PATTERNS = np.array(
    [
        [1, 0, 0],  # Rare Earth
        [0, 0, 1],  # Nation-State
        [0, 1, 0],  # Cyber
        [0, 0, 1],  # Drones
        [0, 1, 0],  # Supply Chain
        [1, 0, 0],  # Biowarfare
        [1, 0, 0],  # Food Security
        [1, 0, 0],  # Trade Wars
        [1, 0, 0],  # Infrastructure
        [0, 0, 1],  # Fake News
    ],
    dtype=float,
)

PATTERN_LABELS = [
    "FR Polarity Inversion",
    "Constraint Relaxation",
    "Context Boundary Violation",
]
PATTERN_COLORS = ["#E63946", "#457B9D", "#2A9D8F"]

# ---------------------------------------------------------------------------
# Data: CIF Mechanism Coverage Matrix (from §10, Table 4.4)
# ---------------------------------------------------------------------------
MECHANISMS = [
    "Cognitive\nFirewall",
    "Belief\nSandboxing",
    "Behavioral\nInvariants",
    "Drift\nDetection",
    "Byzantine\nConsensus",
]

# Rows = mechanisms, Cols = domains (RE, NS, Cy, Dr, SC, Bio, FS, TW, Inf, FN)
COVERAGE_MATRIX = np.array(
    [
        [0, 0, 0, 1, 0, 1, 0, 0, 0, 1],  # Cognitive Firewall
        [0, 1, 0, 0, 0, 1, 1, 0, 1, 0],  # Belief Sandboxing
        [1, 0, 0, 0, 1, 1, 0, 1, 1, 0],  # Behavioral Invariants
        [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],  # Drift Detection
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0],  # Byzantine Consensus
    ],
    dtype=float,
)


def plot_attack_patterns() -> None:
    """Figure 1: Attack pattern distribution across 10 domains."""
    fig, ax = plt.subplots(figsize=(16, 7))

    x = np.arange(len(DOMAINS_SHORT))
    width = 0.6

    bottom = np.zeros(len(DOMAINS_SHORT))
    for i, (pattern, color) in enumerate(zip(PATTERN_LABELS, PATTERN_COLORS)):
        values = ATTACK_PATTERNS[:, i]
        ax.bar(
            x,
            values,
            width,
            bottom=bottom,
            label=pattern,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        bottom += values

    ax.set_xlabel("Domain", fontsize=12)
    ax.set_ylabel("Attack Pattern Present", fontsize=12)
    ax.set_title(
        "Goal Hijacking Attack Pattern Distribution Across Ten Critical Domains\n"
        "(CIF-AD-OODA Cross-Domain Analysis, §10)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS_SHORT, fontsize=10)
    ax.set_yticks([0, 1])
    ax.set_ylim(0, 1.4)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)

    # Annotate with domain full names
    for i, name in enumerate(DOMAINS_SHORT):
        ax.text(
            i,
            -0.18,
            DOMAINS[i].split(". ")[1],
            ha="center",
            va="top",
            fontsize=8,
            rotation=30,
            transform=ax.get_xaxis_transform(),
        )

    # Summary totals
    totals = ATTACK_PATTERNS.sum(axis=0)
    for i, (label, total) in enumerate(zip(PATTERN_LABELS, totals)):
        ax.text(
            len(DOMAINS_SHORT) + 0.1 + i * 0.01,
            0.97 - i * 0.12,
            f"{label}: {int(total)}/10",
            transform=ax.transAxes,
            fontsize=9,
            ha="right",
            va="top",
            color=PATTERN_COLORS[i],
            fontweight="bold",
        )

    fig.tight_layout(rect=(0, 0.12, 1, 1))

    for ext in ["png", "pdf"]:
        path = OUTPUT_DIR / f"domain_coverage.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Saved: {path}")

    plt.close(fig)


def plot_cif_mechanism_coverage() -> None:
    """Figure 2: CIF mechanism coverage matrix heatmap."""
    fig, ax = plt.subplots(figsize=(13, 5))

    # Use a masked colormap: 0 = grey, 1 = teal
    from matplotlib.colors import ListedColormap

    cmap = ListedColormap(["#EEEEEE", "#2A9D8F"])

    ax.imshow(COVERAGE_MATRIX, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    # Grid lines
    ax.set_xticks(np.arange(-0.5, len(DOMAINS_SHORT), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(MECHANISMS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Labels
    ax.set_xticks(range(len(DOMAINS_SHORT)))
    ax.set_xticklabels(DOMAINS_SHORT, fontsize=11)
    ax.set_yticks(range(len(MECHANISMS)))
    ax.set_yticklabels(MECHANISMS, fontsize=11)

    ax.set_title(
        "CIF Defense Mechanism Coverage Across Ten Critical Domains\n"
        "(Primary defense assignment per domain, §10.4)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    # Checkmarks inside cells
    for i in range(COVERAGE_MATRIX.shape[0]):
        for j in range(COVERAGE_MATRIX.shape[1]):
            if COVERAGE_MATRIX[i, j] == 1:
                ax.text(
                    j,
                    i,
                    "✓",
                    ha="center",
                    va="center",
                    fontsize=16,
                    color="white",
                    fontweight="bold",
                )

    # Row totals
    row_totals = COVERAGE_MATRIX.sum(axis=1)
    for i, total in enumerate(row_totals):
        ax.text(
            len(DOMAINS_SHORT) + 0.2,
            i,
            f"({int(total)})",
            ha="left",
            va="center",
            fontsize=10,
            color="#2A9D8F",
            fontweight="bold",
        )

    # Legend
    legend_handles = [
        mpatches.Patch(color="#2A9D8F", label="Primary defense"),
        mpatches.Patch(color="#EEEEEE", label="Not primary"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        bbox_to_anchor=(1.0, -0.18),
        fontsize=9,
        framealpha=0.9,
        ncol=2,
    )

    ax.set_xlabel("Domain", fontsize=12, labelpad=8)
    ax.set_ylabel("CIF Mechanism", fontsize=12)

    fig.tight_layout(rect=(0, 0.05, 0.97, 1))

    for ext in ["png", "pdf"]:
        path = OUTPUT_DIR / f"cif_mechanism_coverage.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Saved: {path}")

    plt.close(fig)


def main() -> None:
    print("Generating CIF-AD-OODA domain coverage figures...")
    plot_attack_patterns()
    plot_cif_mechanism_coverage()
    print("Done.")


if __name__ == "__main__":
    main()
