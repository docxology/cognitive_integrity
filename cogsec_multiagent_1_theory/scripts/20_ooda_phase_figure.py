"""
Figure 20: OODA Phase Diagram (v2.0)

Generates a visualization of the OODA (Observe-Orient-Decide-Act) loop
showing CIF defense coverage at each phase and attack vectors.
"""

import sys
from pathlib import Path

_this = Path(__file__).resolve()
for _p in _this.parents:
    if (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        break

import json
import math

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = _this.parent.parent / "output" / "figures"
DATA_DIR = _this.parent.parent / "output" / "figures" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# OODA phase data
OODA_PHASES = ["Observe", "Orient", "Decide", "Act"]
PHASE_COLORS = ["#264653", "#2a9d8f", "#e9c46a", "#e76f51"]
PHASE_POSITIONS = [
    (0.5, 0.85),  # Observe (top)
    (0.15, 0.45),  # Orient (left)
    (0.50, 0.10),  # Decide (bottom)
    (0.85, 0.45),  # Act (right)
]

PHASE_ATTACKS = {
    "Observe": ["Sensor Spoofing", "Tool Injection"],
    "Orient": ["Belief Injection", "Semantic Drift"],
    "Decide": ["Goal Hijacking", "Constraint Removal"],
    "Act": ["Permission Escalation", "Side-Effect Abuse"],
}

PHASE_DEFENSES = {
    "Observe": ("Provenance Verification", "#264653"),
    "Orient": ("Belief Sandbox + Drift Detection", "#2a9d8f"),
    "Decide": ("Invariant Checking", "#e9c46a"),
    "Act": ("Permission Boundaries", "#e76f51"),
}

#: Design-level coverage assigned to each OODA phase by the mapping above --
#: which CIF mechanisms are *intended* to act at that phase, scored by how
#: completely they cover it. Not measured, and no experiment in this series
#: produces a per-phase detection rate: the corpus carries no OODA label.
#:
#: Panel B plotted these as a "CIF Coverage Score (assigned, not measured)" bar chart with two-decimal
#: labels against a threshold line, which is how a design assignment comes to
#: look like a result. The values are unchanged; what changed is that the
#: figure now says what they are.
PHASE_COVERAGE_IS_MEASURED = False

PHASE_COVERAGE = {
    "Observe": 0.90,
    "Orient": 0.85,
    "Decide": 0.90,
    "Act": 0.90,
}


def generate_ooda_phase_diagram() -> dict:
    """Generate OODA phase diagram with CIF defense annotations."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # ── Panel A: OODA loop with attack vectors ───────────────────────────────
    ax = axes[0]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("OODA Loop: Attack Vectors by Phase", fontsize=13, fontweight="bold", pad=15)

    # Draw circular background
    circle = plt.Circle((0.5, 0.5), 0.38, color="#f8f9fa", zorder=0)
    ax.add_patch(circle)
    circle_border = plt.Circle((0.5, 0.5), 0.38, color="#dee2e6", fill=False, linewidth=2, zorder=1)
    ax.add_patch(circle_border)

    # Draw phase nodes
    for i, (phase, color, pos) in enumerate(zip(OODA_PHASES, PHASE_COLORS, PHASE_POSITIONS)):
        x, y = pos
        circle = plt.Circle((x, y), 0.09, color=color, zorder=3, alpha=0.9)
        ax.add_patch(circle)
        ax.text(
            x,
            y,
            phase,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white",
            zorder=4,
        )

    # Draw arrows between phases (clockwise)
    arrow_pairs = [
        (PHASE_POSITIONS[0], PHASE_POSITIONS[1]),  # Observe → Orient
        (PHASE_POSITIONS[1], PHASE_POSITIONS[2]),  # Orient → Decide
        (PHASE_POSITIONS[2], PHASE_POSITIONS[3]),  # Decide → Act
        (PHASE_POSITIONS[3], PHASE_POSITIONS[0]),  # Act → Observe (cycle)
    ]
    arrow_labels = ["Belief update", "Goal formation", "Action selection", "New observation"]

    for (x1, y1), (x2, y2), label in zip(
        [p for p, _ in arrow_pairs], [p for _, p in arrow_pairs], arrow_labels
    ):
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx**2 + dy**2)
        # Shorten arrow to not overlap with circles
        shrink = 0.10
        x1s = x1 + shrink * dx / dist
        y1s = y1 + shrink * dy / dist
        x2s = x2 - shrink * dx / dist
        y2s = y2 - shrink * dy / dist
        ax.annotate(
            "",
            xy=(x2s, y2s),
            xytext=(x1s, y1s),
            arrowprops=dict(arrowstyle="->", color="#495057", lw=1.5),
        )
        mx, my = (x1s + x2s) / 2, (y1s + y2s) / 2
        ax.text(
            mx,
            my,
            label,
            ha="center",
            va="center",
            fontsize=7.5,
            style="italic",
            color="#6c757d",
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7),
        )

    # Attack vectors as red annotations
    attack_offsets = [
        (0.00, 0.14),  # Observe: above
        (-0.18, 0.00),  # Orient: left
        (0.00, -0.14),  # Decide: below
        (0.18, 0.00),  # Act: right
    ]
    for phase, color, pos, offset in zip(
        OODA_PHASES, PHASE_COLORS, PHASE_POSITIONS, attack_offsets
    ):
        attacks = PHASE_ATTACKS[phase]
        x, y = pos
        ox, oy = offset
        ax.text(
            x + ox,
            y + oy,
            "\n".join(attacks),
            ha="center",
            va="center",
            fontsize=8,
            color="#e63946",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="#fff5f5",
                edgecolor="#e63946",
                linewidth=1,
                alpha=0.85,
            ),
        )

    ax.text(
        0.5,
        0.5,
        "CIF\nMonitor",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#495057",
        style="italic",
    )

    # ── Panel B: Coverage bar chart ──────────────────────────────────────────
    ax2 = axes[1]

    phases = list(PHASE_COVERAGE.keys())
    coverage = list(PHASE_COVERAGE.values())
    colors_bar = PHASE_COLORS

    bars = ax2.barh(
        phases, coverage, color=colors_bar, edgecolor="white", linewidth=0.5, alpha=0.9, height=0.5
    )

    ax2.axvline(
        x=0.50,
        color="#e63946",
        linestyle="--",
        linewidth=1.5,
        label="Min. coverage threshold (0.50)",
    )
    ax2.set_xlim(0, 1.05)
    ax2.set_xlabel("CIF Coverage Score (assigned, not measured)", fontsize=12)
    ax2.set_title("CIF Defense Coverage\nby OODA Phase", fontsize=13, fontweight="bold")

    for bar, val in zip(bars, coverage):
        ax2.text(
            val + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}",
            va="center",
            fontsize=11,
            fontweight="bold",
        )

    # Defense names
    defense_text = "\n".join([f"{ph}: {PHASE_DEFENSES[ph][0]}" for ph in phases])
    ax2.text(
        0.02,
        0.02,
        defense_text,
        transform=ax2.transAxes,
        fontsize=8,
        verticalalignment="bottom",
        color="#6c757d",
        bbox=dict(boxstyle="round", facecolor="#f8f9fa", alpha=0.8),
    )

    ax2.legend(fontsize=10)
    ax2.grid(axis="x", alpha=0.3)

    fig.suptitle("OODA Phase Security Analysis — CIF v2.0", fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()

    # Save
    for ext in ["pdf", "png"]:
        fig.savefig(OUTPUT_DIR / f"ooda_phase_diagram.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Save data
    data = {
        "phases": OODA_PHASES,
        "phase_attacks": PHASE_ATTACKS,
        "phase_defenses": {k: v[0] for k, v in PHASE_DEFENSES.items()},
        "phase_coverage": PHASE_COVERAGE,
        "mean_coverage": float(np.mean(coverage)),
    }
    with open(DATA_DIR / "ooda_phase_diagram.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Saved: ooda_phase_diagram.pdf/png, ooda_phase_diagram.json")
    print(f"Mean phase coverage: {data['mean_coverage']:.3f}")
    return data


if __name__ == "__main__":
    generate_ooda_phase_diagram()
