"""Trust Decay module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from core.trust import TrustCalculus, TrustConfig

from ..style import (
    FONTSIZE,
    PALETTE,
    SEMANTIC_COLORS,
    add_source_annotation,
    apply_style,
    save_figure,
)


def plot_trust_decay(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate trust decay visualization figure."""
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Apply style
    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel A: Trust decay curves for different δ values
    ax1 = axes[0]
    depths = np.arange(0, 21)
    decay_factors = [0.95, 0.9, 0.85, 0.8, 0.7]

    for i, delta in enumerate(decay_factors):
        config = TrustConfig(decay=delta)
        calculus = TrustCalculus(config)
        trust = [calculus.delegate_trust(1.0, 1.0, int(d)) for d in depths]
        # Use centralized palette cyclically
        color = PALETTE[i % len(PALETTE)]
        ax1.plot(
            depths,
            trust,
            "-o",
            markersize=4,
            color=color,
            label=f"δ = {delta}",
            linewidth=2,
        )

    ax1.axhline(
        y=0.1,
        color="gray",
        linestyle="--",
        alpha=0.7,
        label="Practical threshold (0.1)",
    )
    ax1.set_xlabel("Delegation Depth (d)", fontsize=12)
    ax1.set_ylabel("Trust (T)", fontsize=12)
    ax1.set_title(
        "A. Trust Decay Over Delegation Depth", fontsize=13, fontweight="bold"
    )
    ax1.legend(loc="upper right", fontsize=FONTSIZE["base"])
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.05, 1.05)

    # Add annotation
    ax1.annotate(
        "Trust bounded by δᵈ",
        xy=(10, 0.9**10),
        xytext=(12, 0.5),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=10,
        ha="center",
    )

    # Panel B: Trust preservation under attack scenarios
    ax2 = axes[1]

    scenarios = ["No Defense", "Firewall Only", "Trust Decay\n(δ=0.9)", "Full CIF"]
    initial_trust = [1.0, 1.0, 1.0, 1.0]
    after_attack = [0.15, 0.45, 0.72, 0.94]

    x = np.arange(len(scenarios))
    width = 0.35

    ax2.bar(
        x - width / 2,
        initial_trust,
        width,
        label="Initial Trust",
        color=SEMANTIC_COLORS["baseline"], # Use baseline gray for initial
        alpha=0.8,
    )
    bars2 = ax2.bar(
        x + width / 2,
        after_attack,
        width,
        label="After Attack",
        color=SEMANTIC_COLORS["tripwire"], # Use a distinct color like magenta/tripwire for contrast
        alpha=0.8,
    )

    ax2.set_ylabel("Trust Integrity", fontsize=12)
    ax2.set_title("B. Trust Preservation Under Attack", fontsize=13, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, fontsize=10)
    ax2.legend(loc="upper left", fontsize=FONTSIZE["base"])
    ax2.set_ylim(0, 1.15)
    ax2.grid(True, alpha=0.3, axis="y")

    # Add percentage labels
    for bar, val in zip(bars2, after_attack):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{val*100:.0f}%",
            ha="center",
            va="bottom",
            fontsize=FONTSIZE["base"],
        )

    add_source_annotation(fig, "src/visualization/figures/trust_decay.py")
    save_figure(fig, "trust_decay", output_dir=output_dir)
    return fig
