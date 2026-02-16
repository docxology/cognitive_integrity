from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

try:
    from attacks.corpus import AttackCorpus
    _corpus = AttackCorpus.generate(seed=42)
    _CORPUS_COUNTS = {
        "injection": sum(1 for a in _corpus.attacks if a.category == "injection"),
        "trust_exploitation": sum(1 for a in _corpus.attacks if a.category == "trust_exploitation"),
        "belief_manipulation": sum(1 for a in _corpus.attacks if a.category == "belief_manipulation"),
        "coordination": sum(1 for a in _corpus.attacks if a.category == "coordination"),
    }
except (ImportError, ModuleNotFoundError, Exception):
    _CORPUS_COUNTS = {
        "injection": 500, "trust_exploitation": 200,
        "belief_manipulation": 150, "coordination": 100
    }


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

    # Data for each adversary class
    classes = [
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
            "detection": 0.85,
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
            "detection": 0.78,
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
            "detection": 0.71,
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
            "detection": 0.65,
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
            "detection": 0.45,
            "impact": "Total Compromise",
        },
    ]

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
            f"Detection: {cls['detection']:.0%}",
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

    # Severity progression arrow
    ax.annotate(
        "",
        xy=(15.2, 4.5),
        xytext=(0.5, 4.5),
        arrowprops=dict(arrowstyle="-|>", color="#7F8C8D", lw=2, mutation_scale=20),
    )
    ax.text(
        7.85,
        4.1,
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

    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/comprehensive_taxonomy.py")

    save_figure(fig, "comprehensive_taxonomy", output_dir=output_dir)
    return fig
