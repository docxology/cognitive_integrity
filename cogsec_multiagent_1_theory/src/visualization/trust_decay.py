"""
Trust Decay Visualization Logic.

Moves logic from script 02 to a reusable module.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from .utils import setup_plotting, save_figure, get_color_palette
from ..trust import TrustCalculus, TrustConfig

def generate_trust_decay_figure(output_dir: Path) -> Path:
    """
    Generate the trust decay visualization.

    Args:
        output_dir: Directory to save output files

    Returns:
        Path to generated PDF
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        
    setup_plotting()
    colors = get_color_palette()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel A: Trust decay curves for different delta values
    ax1 = axes[0]
    depths = np.arange(0, 21)
    decay_factors = [0.95, 0.9, 0.85, 0.8, 0.7]

    for i, delta in enumerate(decay_factors):
        config = TrustConfig(decay=delta)
        calculus = TrustCalculus(config)
        trust = [calculus.delegate_trust(1.0, 1.0, int(d)) for d in depths]
        ax1.plot(
            depths,
            trust,
            "-o",
            markersize=4,
            color=colors[i % len(colors)],
            label=f"$\delta$ = {delta}",
            linewidth=2,
        )

    ax1.axhline(
        y=0.1,
        color="gray",
        linestyle="--",
        alpha=0.7,
        label="Practical threshold (0.1)",
    )
    ax1.set_xlabel("Delegation Depth (d)")
    ax1.set_ylabel("Trust (T)")
    ax1.set_title("A. Trust Decay Over Delegation Depth")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.05, 1.05)

    # Add annotation
    ax1.annotate(
        "Trust bounded by $\delta^d$",
        xy=(10, 0.9**10),
        xytext=(12, 0.5),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=10,
        ha="center",
    )

    # Panel B: Trust preservation under attack scenarios
    ax2 = axes[1]

    scenarios = ["No Defense", "Firewall Only", "Trust Decay\n($\delta$=0.9)", "Full CIF"]
    initial_trust = [1.0, 1.0, 1.0, 1.0]
    after_attack = [0.15, 0.45, 0.72, 0.94]

    x = np.arange(len(scenarios))
    width = 0.35

    bars1 = ax2.bar(
        x - width / 2,
        initial_trust,
        width,
        label="Initial Trust",
        color=colors[0],
        alpha=0.8,
    )
    bars2 = ax2.bar(
        x + width / 2,
        after_attack,
        width,
        label="After Attack",
        color=colors[1],
        alpha=0.8,
    )

    ax2.set_ylabel("Trust Integrity")
    ax2.set_title("B. Trust Preservation Under Attack")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios)
    ax2.legend(loc="upper left", frameon=True)
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
            fontsize=9,
        )

    # Ensure professional rendering
    import matplotlib
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    save_figure(fig, output_dir, "trust_decay")
    plt.close()
    
    return output_dir / "trust_decay.pdf"
