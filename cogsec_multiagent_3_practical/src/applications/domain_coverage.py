"""Cross-domain CIF-AD-OODA coverage data and figure rendering (Part 3+4 §10)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

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

ATTACK_PATTERNS = np.array(
    [
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [1, 0, 0],
        [1, 0, 0],
        [1, 0, 0],
        [0, 0, 1],
    ],
    dtype=float,
)

PATTERN_LABELS = [
    "FR Polarity Inversion",
    "Constraint Relaxation",
    "Context Boundary Violation",
]
PATTERN_COLORS = ["#E63946", "#457B9D", "#2A9D8F"]

MECHANISMS = [
    "Cognitive\nFirewall",
    "Belief\nSandboxing",
    "Behavioral\nInvariants",
    "Drift\nDetection",
    "Byzantine\nConsensus",
]

COVERAGE_MATRIX = np.array(
    [
        [0, 0, 0, 1, 0, 1, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 1, 1, 0, 1, 0],
        [1, 0, 0, 0, 1, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    ],
    dtype=float,
)


def domain_coverage_payload() -> dict[str, object]:
    """Return canonical cross-domain matrices for tests and visualization."""
    return {
        "domains": list(DOMAINS),
        "domains_short": list(DOMAINS_SHORT),
        "attack_patterns": ATTACK_PATTERNS.tolist(),
        "pattern_labels": list(PATTERN_LABELS),
        "mechanisms": [m.replace("\n", " ") for m in MECHANISMS],
        "coverage_matrix": COVERAGE_MATRIX.tolist(),
    }


def plot_attack_patterns(output_dir: Path) -> list[Path]:
    """Figure 1: attack pattern distribution across ten domains."""
    output_dir.mkdir(parents=True, exist_ok=True)
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
    paths: list[Path] = []
    for ext in ("png", "pdf"):
        path = output_dir / f"domain_coverage.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def plot_cif_mechanism_coverage(output_dir: Path) -> list[Path]:
    """Figure 2: CIF mechanism coverage matrix heatmap."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 5))
    cmap = ListedColormap(["#EEEEEE", "#2A9D8F"])
    ax.imshow(COVERAGE_MATRIX, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(np.arange(-0.5, len(DOMAINS_SHORT), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(MECHANISMS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

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
    paths: list[Path] = []
    for ext in ("png", "pdf"):
        path = output_dir / f"cif_mechanism_coverage.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def render_domain_coverage_figures(output_dir: Path) -> list[Path]:
    """Render both Part 4 cross-domain figures."""
    return plot_attack_patterns(output_dir) + plot_cif_mechanism_coverage(output_dir)
