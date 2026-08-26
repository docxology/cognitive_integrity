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

# Row 3 (Cyber-Security) is a Context Boundary Violation, not a Constraint
# Relaxation: its post-attack design matrix introduces off-diagonal A_12/A_21
# into a matrix that was diagonal and leaves the diagonal magnitudes intact,
# which is Pattern 3's signature. See 09e_cyber_security.md.
ATTACK_PATTERNS = np.array(
    [
        [1, 0, 0],
        [0, 0, 1],
        [0, 0, 1],
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

# Dimension guards — fail at import if the matrices drift from their labels so
# a reordered DOMAINS/MECHANISMS cannot silently mislabel a heatmap column.
assert ATTACK_PATTERNS.shape == (len(DOMAINS), len(PATTERN_LABELS)), (
    f"ATTACK_PATTERNS shape {ATTACK_PATTERNS.shape} != "
    f"({len(DOMAINS)} domains, {len(PATTERN_LABELS)} patterns)"
)
assert COVERAGE_MATRIX.shape == (len(MECHANISMS), len(DOMAINS)), (
    f"COVERAGE_MATRIX shape {COVERAGE_MATRIX.shape} != "
    f"({len(MECHANISMS)} mechanisms, {len(DOMAINS)} domains)"
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
    """Figure 1: which goal-hijacking pattern each of the ten domains exhibits.

    ATTACK_PATTERNS is one-hot by row: every domain is assigned exactly one of
    three patterns. Drawing that as stacked bars gave every domain a bar of
    height exactly 1, so the quantitative axis carried no information and the
    y-label ("Attack Pattern Present") read as a measurement that had come out
    identical everywhere. It is a categorical assignment, and it is drawn as
    one: a row per pattern, a marked cell per domain, and the row totals beside
    the row they describe rather than in a right-hand margin the legend
    overlapped.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 5.2))

    n_domains = len(DOMAINS_SHORT)
    n_patterns = len(PATTERN_LABELS)
    assignment = ATTACK_PATTERNS.argmax(axis=1)
    # One-hot is the precondition for reading argmax as "the" pattern; a row
    # with zero or two marks would be silently drawn as one.
    if not np.array_equal(ATTACK_PATTERNS.sum(axis=1), np.ones(n_domains)):
        raise ValueError(
            "ATTACK_PATTERNS is no longer one-hot by row; this figure assigns "
            "exactly one pattern per domain and cannot represent the matrix"
        )

    for row in range(n_patterns):
        ax.axhspan(row - 0.5, row + 0.5, color=PATTERN_COLORS[row], alpha=0.06, zorder=0)

    for domain, row in enumerate(assignment):
        ax.scatter(
            domain,
            row,
            s=520,
            color=PATTERN_COLORS[row],
            edgecolor="white",
            linewidth=1.6,
            zorder=3,
        )
        ax.text(
            domain,
            row,
            DOMAINS_SHORT[domain],
            ha="center",
            va="center",
            fontsize=8.5,
            color="white",
            fontweight="bold",
            zorder=4,
        )

    totals = ATTACK_PATTERNS.sum(axis=0)
    ax.set_xlim(-0.7, n_domains + 1.4)
    ax.set_ylim(n_patterns - 0.5, -0.9)
    ax.set_yticks(range(n_patterns))
    ax.set_yticklabels(PATTERN_LABELS, fontsize=11)
    for row, colour in enumerate(PATTERN_COLORS):
        ax.get_yticklabels()[row].set_color(colour)
        ax.text(
            n_domains + 0.2,
            row,
            f"{int(totals[row])}/{n_domains}",
            ha="left",
            va="center",
            fontsize=11,
            color=colour,
            fontweight="bold",
        )

    ax.set_xticks(range(n_domains))
    ax.set_xticklabels(
        [DOMAINS[i].split(". ")[1] for i in range(n_domains)],
        fontsize=9,
        rotation=25,
        ha="right",
    )
    ax.set_xlabel("Domain", fontsize=12)
    ax.set_title(
        "Goal Hijacking Attack Pattern Distribution Across Ten Critical Domains\n"
        "(CIF-AD-OODA Cross-Domain Analysis, \u00a710; each domain exhibits exactly one pattern)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", alpha=0.25, linestyle=":", zorder=1)

    fig.tight_layout()
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
