"""Comprehensive Taxonomy module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from attacks.corpus import AttackCorpus

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

# Derived, never hardcoded.  The previous form read a ``_corpus.attacks``
# attribute that ``AttackCorpus`` does not expose, from inside an
# ``except (ImportError, ModuleNotFoundError, Exception)`` block: the
# derivation always raised and a hardcoded table always won, so the caption's
# corpus size could not track the corpus it names.
_CORPUS_COUNTS: dict[str, int] = dict(AttackCorpus.generate(seed=42).distribution())



#: Per-adversary-class detection, measured rather than typed.
#:
#: Five rates were written into the ``classes`` list below -- 0.85, 0.78, 0.71,
#: 0.65, 0.45 -- and drawn as filled progress bars labelled "Detection: 85%"
#: and so on, under a caption that draws a conclusion from the trend. Nothing
#: measured them. ``adversarial_training_results.json`` carries
#: ``omega_level_dr`` keyed ``omega_1_passive`` through ``omega_5_coordinated``,
#: one-for-one with this figure's five columns, and it is used here.
#:
#: That artifact's ``data_origin`` is ``parametric_simulation``, so the panel
#: says so. Replacing a typed number with a simulated one and calling it
#: measured would be the same defect in better clothes.
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
    """Detection per adversary class, in column order. Fails closed."""
    if not _OMEGA_DR_PATH.is_file():
        raise FileNotFoundError(
            f"{_OMEGA_DR_PATH} is missing; run "
            f"scripts/run_adversarial_training.py. This panel reports a rate "
            f"per adversary class and has no stand-in values."
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
        "COGNITIVE ATTACK SURFACE TAXONOMY",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        8,
        9.0,
        f"Classification of Multiagent AI Attack Vectors "
        f"(n={sum(_CORPUS_COUNTS.values())} corpus)",
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

    # Data for each adversary class. The detection rate is attached below from
    # the artifact rather than written into the literal.
    detection_rates = _omega_detection_rates()
    classes: list[Any] = [
        {
            "symbol": "Ω₁",
            "name": "EXTERNAL",
            "color": colors["external"],
            "icon": "↓",  # Input arrow
            "attacks": [
                "Direct Prompt\nInjection",
                "Social\nEngineering",
                "Malicious\nUser Input",
            ],
            "complexity": "Low",
            "impact": "Entry Point",
        },
        {
            "symbol": "Ω₂",
            "name": "PERIPHERAL",
            "color": colors["peripheral"],
            "icon": "⚡",  # Tool/API
            "attacks": [
                "Tool Response\nManipulation",
                "Memory\nPoisoning",
                "API Data\nCorruption",
            ],
            "complexity": "Medium",
            "impact": "Data Injection",
        },
        {
            "symbol": "Ω₃",
            "name": "AGENT-LEVEL",
            "color": colors["agent"],
            "icon": "◉",  # Agent/brain
            "attacks": [
                "Identity\nConfusion",
                "Belief\nInjection",
                "Goal\nManipulation",
            ],
            "complexity": "High",
            "impact": "State Corruption",
        },
        {
            "symbol": "Ω₄",
            "name": "COORDINATION",
            "color": colors["coordination"],
            "icon": "⬡",  # Network
            "attacks": [
                "Trust\nLaundering",
                "Sybil\nAttacks",
                "Consensus\nManipulation",
            ],
            "complexity": "High",
            "impact": "Trust Exploitation",
        },
        {
            "symbol": "Ω₅",
            "name": "SYSTEMIC",
            "color": colors["systemic"],
            "icon": "⚠",  # Warning
            "attacks": [
                "Orchestrator\nCompromise",
                "System-Wide\nCorruption",
                "Cascading\nFailure",
            ],
            "complexity": "Critical",
            "impact": "Total Compromise",
        },
    ]

    for _column, _rate in zip(classes, detection_rates):
        _column["detection"] = _rate

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
            cls["name"],
            ha="center",
            va="center",
            fontsize=10,
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
            f"Detection: {cls['detection']:.0%}\u2020",
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
        "Detection difficulty: ",
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
    # The dagger on each Detection label. The artifact these come from records
    # data_origin "parametric_simulation", and a bar chart with no qualifier
    # reads as a measurement whatever its source.
    ax.text(
        0.5, 0.015,
        "\u2020 Detection rates from adversarial_training_results.json "
        "(parametric simulation, not a deployed measurement).",
        transform=fig.transFigure, ha="center", va="bottom",
        fontsize=7, color="#5A6472", style="italic",
    )


    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/comprehensive_taxonomy.py")

    save_figure(fig, "comprehensive_taxonomy", output_dir=output_dir)
    return fig
