"""Comprehensive Taxonomy module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from src.attacks.corpus import AttackCorpus

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

# Derived, never hardcoded.  The previous form read a ``_corpus.attacks``
# attribute that ``AttackCorpus`` does not expose, from inside an
# ``except (ImportError, ModuleNotFoundError, Exception)`` block: the
# derivation always raised and a hardcoded table always won, so the caption's
# corpus size could not track the corpus it names.
_CORPUS = AttackCorpus.generate(seed=42)
_CORPUS_COUNTS: dict[str, int] = dict(_CORPUS.distribution())
_OMEGA_COUNTS = {
    level: sum(sample.omega_level == level for sample in _CORPUS)
    for level in range(1, 6)
}



#: Closed-form detection projections indexed by the corpus's category-derived
#: technique annotations.  These Ω groups are not Part 1's access-based
#: adversary classes, and the projections are not independent measurements.
#: The figure names both limitations next to the bars.
_OMEGA_DR_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "adversarial_training_results.json"
)

#: The artifact's keys, in this figure's column order.
_OMEGA_KEYS = (
    "omega_1_passive",
    "omega_2_injection",
    "omega_3_impersonation",
    "omega_4_belief_manip",
    "omega_5_coordinated",
)


def _omega_detection_rates() -> list[float]:
    """Closed-form projections by technique annotation, in column order."""
    if not _OMEGA_DR_PATH.is_file():
        raise FileNotFoundError(
            f"{_OMEGA_DR_PATH} is missing; run "
            f"scripts/run_adversarial_training.py. This panel reports closed-form "
            f"projections by technique annotation and has no stand-in values."
        )
    payload = json.loads(_OMEGA_DR_PATH.read_text(encoding="utf-8"))
    rates = payload.get("omega_level_dr") or {}
    missing = [k for k in _OMEGA_KEYS if k not in rates]
    if missing:
        raise KeyError(
            f"{_OMEGA_DR_PATH.name} has no omega_level_dr entry for {missing}; "
            f"the ladder and the figure have diverged"
        )
    return [float(rates[k]) for k in _OMEGA_KEYS]


def plot_comprehensive_taxonomy(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate comprehensive attack taxonomy visualization."""
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Apply style
    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Background
    ax.set_facecolor("#FAFAFA")

    # Colorblind-friendly colors (using SEMANTIC mapping)
    colors = {
        "external": SEMANTIC_COLORS["user"],       # Blue (Input/External)
        "peripheral": SEMANTIC_COLORS["peripheral"], # Red (Tools)
        "agent": SEMANTIC_COLORS["agent"],         # Purple (Internal)
        "coordination": SEMANTIC_COLORS["coordination"], # Gold (Network)
        "systemic": SEMANTIC_COLORS["systemic"],   # Green (Orchestrator)
        "header": "#2C3E50",
        "text": "#2D2D2D",
    }

    # Title
    ax.text(
        8,
        9.5,
        "TECHNIQUE-DERIVED Ω ANNOTATIONS",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        8,
        9.0,
        f"Corpus technique groups, not access-based adversary classes "
        f"(n={sum(_CORPUS_COUNTS.values())} attacks)",
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color=colors["text"],
    )

    # Column positions and widths
    col_width = 2.8
    col_gap = 0.3
    start_x = 0.8

    # Static technique descriptions plus measured corpus counts and the
    # artifact's separately qualified closed-form projection for each Ω key.
    detection_rates = _omega_detection_rates()
    classes: list[Any] = [
        {
            "symbol": "Ω₁",
            "name": "PASSIVE",
            "color": colors["external"],
            "icon": "↓",
            "attacks": ["No attack-corpus\nentries", "—", "—"],
            "complexity": "Low",
            "impact": "No attack samples",
        },
        {
            "symbol": "Ω₂",
            "name": "INJECTION",
            "color": colors["peripheral"],
            "icon": "⚡",
            "attacks": [
                "Direct / Indirect\nInjection",
                "Nested\nInjection",
                "Sandbox\nEscape",
            ],
            "complexity": "Medium",
            "impact": "Action Execution",
        },
        {
            "symbol": "Ω₃",
            "name": "IMPERSONATION",
            "color": colors["agent"],
            "icon": "◉",
            "attacks": [
                "Identity\nImpersonation",
                "Trust\nInflation",
                "Delegation\nAbuse",
            ],
            "complexity": "High",
            "impact": "Trust / Goal Exploitation",
        },
        {
            "symbol": "Ω₄",
            "name": "BELIEF MANIP.",
            "color": colors["coordination"],
            "icon": "⬡",
            "attacks": [
                "Belief Drift /\nFabrication",
                "Belief\nInjection",
                "Provenance\nLaundering",
            ],
            "complexity": "High",
            "impact": "Belief-State Corruption",
        },
        {
            "symbol": "Ω₅",
            "name": "COORDINATED",
            "color": colors["systemic"],
            "icon": "⚠",
            "attacks": [
                "Sybil / Consensus\nAttacks",
                "Timing\nAttacks",
                "Byzantine\nManipulation",
            ],
            "complexity": "Critical",
            "impact": "Coordination Abuse",
        },
    ]

    for level, (_column, _rate) in enumerate(zip(classes, detection_rates), start=1):
        _column["detection"] = _rate
        _column["corpus_n"] = _OMEGA_COUNTS[level]

    # Draw each class column
    for i, cls in enumerate(classes):
        x = start_x + i * (col_width + col_gap)

        # Main column background with increasing intensity
        alpha = 0.15 + i * 0.05
        col_box = FancyBboxPatch(
            (x, 0.8),
            col_width,
            7.6,
            boxstyle="round,pad=0.02",
            facecolor=cls["color"],
            edgecolor=cls["color"],
            linewidth=2 + i * 0.5,
            alpha=alpha,
        )
        ax.add_patch(col_box)

        # Header box
        header_box = FancyBboxPatch(
            (x + 0.1, 7.4),
            col_width - 0.2,
            0.9,
            boxstyle="round,pad=0.02",
            facecolor=cls["color"],
            edgecolor="black",
            linewidth=1.5,
        )
        ax.add_patch(header_box)

        # Symbol (Ω with subscript)
        ax.text(
            x + col_width / 2,
            8.0,
            cls["symbol"],
            ha="center",
            va="center",
            fontsize=22,
            fontweight="bold",
            color="white",
        )
        ax.text(
            x + col_width / 2,
            7.6,
            f"{cls['name']}\nn={cls['corpus_n']}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )

        # Icon
        ax.text(
            x + col_width / 2,
            6.9,
            cls["icon"],
            ha="center",
            va="center",
            fontsize=24,
            color=cls["color"],
        )

        # Attack types
        for j, attack in enumerate(cls["attacks"]):
            y = 5.8 - j * 1.2
            attack_box = FancyBboxPatch(
                (x + 0.15, y - 0.4),
                col_width - 0.3,
                0.9,
                boxstyle="round,pad=0.01",
                facecolor="white",
                edgecolor=cls["color"],
                linewidth=1,
            )
            ax.add_patch(attack_box)
            ax.text(
                x + col_width / 2,
                y,
                attack,
                ha="center",
                va="center",
                fontsize=FONTSIZE["small"],
                color=colors["text"],
            )

        # Colorblind-friendly complexity indicator (IBM Design)
        complexity_colors = {
            "Low": SEMANTIC_COLORS["baseline"], # Gray/Low
            "Medium": SEMANTIC_COLORS["invariants"], # Gold/Medium
            "High": SEMANTIC_COLORS["full_cif"], # Orange/High
            "Critical": SEMANTIC_COLORS["tripwire"], # Magenta/Critical
        }
        ax.text(
            x + col_width / 2,
            2.3,
            f"Complexity: {cls['complexity']}",
            ha="center",
            va="center",
            fontsize=FONTSIZE["base"],
            fontweight="bold",
            color=complexity_colors[cls["complexity"]],
        )

        # Detection rate bar
        bar_width = (col_width - 0.4) * cls["detection"]
        bar_bg = Rectangle(
            (x + 0.2, 1.6), col_width - 0.4, 0.3, facecolor="#E0E0E0", edgecolor="none"
        )
        ax.add_patch(bar_bg)

        # Colorblind-friendly bar colors
        bar_color = (
            SEMANTIC_COLORS["firewall"] # Blue (Good)
            if cls["detection"] >= 0.8
            else SEMANTIC_COLORS["invariants"] # Yellow (Med)
            if cls["detection"] >= 0.6
            else SEMANTIC_COLORS["tripwire"] # Magenta (Bad)
        )
        bar_fill = Rectangle(
            (x + 0.2, 1.6), bar_width, 0.3, facecolor=bar_color, edgecolor="none"
        )
        ax.add_patch(bar_fill)
        ax.text(
            x + col_width / 2,
            1.75,
            f"Model projection: {cls['detection']:.0%}\u2020",
            ha="center",
            va="center",
            fontsize=FONTSIZE["small"],
            fontweight="bold",
            color="white" if cls["detection"] >= 0.5 else colors["text"],
        )

        # Impact label
        ax.text(
            x + col_width / 2,
            1.1,
            cls["impact"],
            ha="center",
            va="center",
            fontsize=FONTSIZE["small"],
            style="italic",
            color=cls["color"],
        )

    # Severity progression arrow (placed in the gap between rows so it does
    # not strike through the middle row of attack-type boxes)
    ax.annotate(
        "",
        xy=(16.0, 4.05),
        xytext=(0.3, 4.05),
        arrowprops=dict(arrowstyle="-|>", color="#7F8C8D", lw=2, mutation_scale=20),
    )
    ax.text(
        7.85,
        4.32,
        "Increasing Severity & Stealth →",
        ha="center",
        va="center",
        fontsize=10,
        style="italic",
        color="#7F8C8D",
    )

    # Colorblind-friendly legend (IBM Design)
    ax.text(
        0.5,
        0.4,
        "Projected detection (closed-form): ",
        ha="left",
        va="center",
        fontsize=FONTSIZE["base"],
        color=colors["text"],
    )
    legend_items = [
        ("High (≥80%)", SEMANTIC_COLORS["firewall"]),
        ("Medium (60-79%)", SEMANTIC_COLORS["invariants"]),
        ("Low (<60%)", SEMANTIC_COLORS["tripwire"]),
    ]
    for j, (label, color) in enumerate(legend_items):
        ax.add_patch(
            Rectangle(
                (3.5 + j * 3.5, 0.3),
                0.4,
                0.25,
                facecolor=color,
                edgecolor="black",
                linewidth=0.5,
            )
        )
        ax.text(
            4.0 + j * 3.5,
            0.42,
            label,
            ha="left",
            va="center",
            fontsize=FONTSIZE["small"],
            color=colors["text"],
        )
    # The Ω values are category-derived technique annotations, not a second
    # access taxonomy.  Their rates are closed-form scenario projections, not
    # per-class measurements (and Ω₁ has no attack-corpus denominator).
    ax.text(
        0.5, 0.015,
        "\u2020 Closed-form projections from adversarial_training_results.json; "
        "Ω groups are technique annotations, not access classes or independent measurements.",
        transform=fig.transFigure, ha="center", va="bottom",
        fontsize=7, color="#5A6472", style="italic",
    )


    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/comprehensive_taxonomy.py")

    save_figure(fig, "comprehensive_taxonomy", output_dir=output_dir)
    return fig
