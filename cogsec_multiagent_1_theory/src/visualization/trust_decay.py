"""
from __future__ import annotations

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

    # Increase default font sizes for manuscript readability
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11
    })

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))  # Wider figure

    # Panel A: Trust decay curves for different delta values
    ax1 = axes[0]
    depths = np.arange(0, 21)
    decay_factors = [0.95, 0.9, 0.85, 0.8, 0.7]

    # Use a sequential palette for decay factors
    # Gradient from blue to purple
    decay_colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(decay_factors)))

    for i, delta in enumerate(decay_factors):
        config = TrustConfig(decay=delta)
        calculus = TrustCalculus(config)
        trust = [calculus.delegate_trust(1.0, 1.0, int(d)) for d in depths]
        ax1.plot(
            depths,
            trust,
            "-o",
            markersize=6,
            color=decay_colors[i],
            label=f"$\delta$ = {delta}",
            linewidth=2.5,
            alpha=0.9
        )

    # Shaded region for "Low Trust"
    ax1.fill_between(depths, 0, 0.1, color='gray', alpha=0.1, label="Untrusted Region (<0.1)")
    
    ax1.axhline(
        y=0.1,
        color="gray",
        linestyle="--",
        alpha=0.8,
        linewidth=1.5,
    )
    
    ax1.set_xlabel("Delegation Depth (d)", fontweight='bold')
    ax1.set_ylabel("Trust Score (T)", fontweight='bold')
    ax1.set_title("A. Trust Decay Over Delegation Depth", fontweight='bold', pad=15)
    ax1.legend(loc="upper right", frameon=True, framealpha=0.9)
    ax1.grid(True, alpha=0.2, linestyle='-')
    ax1.set_ylim(-0.02, 1.05)
    ax1.set_xlim(0, 20)

    # Add mathematical annotation
    ax1.text(
        10, 0.6, 
        r"$T(d) = T_0 \cdot \delta^d$", 
        fontsize=14, 
        color="#333",
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=5)
    )

    # Panel B: Trust preservation under attack scenarios
    ax2 = axes[1]

    scenarios = ["No Defense", "Firewall\nOnly", "Trust Decay\n($\delta$=0.9)", "Full CIF"]
    initial_trust = [1.0, 1.0, 1.0, 1.0]
    after_attack = [0.15, 0.45, 0.72, 0.94]

    x = np.arange(len(scenarios))
    width = 0.35

    # IBM Design Colors (Colorblind safe)
    # Blue for Initial, Magenta for After Attack
    c_initial = "#648FFF" 
    c_after = "#DC267F"

    bars1 = ax2.bar(
        x - width / 2,
        initial_trust,
        width,
        label="Initial Trust",
        color=c_initial,
        alpha=0.9,
        edgecolor='black',
        linewidth=1
    )
    bars2 = ax2.bar(
        x + width / 2,
        after_attack,
        width,
        label="After Attack",
        color=c_after,
        alpha=0.9,
        edgecolor='black',
        linewidth=1
    )

    ax2.set_ylabel("Trust Integrity Score", fontweight='bold')
    ax2.set_title("B. Trust Preservation Under Attack", fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, fontweight='bold')
    ax2.legend(loc="upper left", frameon=True, framealpha=0.9)
    ax2.set_ylim(0, 1.15)
    ax2.grid(True, alpha=0.2, axis="y")

    # Add percentage labels with background for readability
    for bar, val in zip(bars2, after_attack):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.02,
            f"{val*100:.0f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight='bold',
            color="#333"
        )

    # Ensure professional rendering
    import matplotlib
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    plt.tight_layout(pad=3.0)
    
    save_figure(fig, output_dir, "trust_decay")
    plt.close()
    
    return output_dir / "trust_decay.pdf"
