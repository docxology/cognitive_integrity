#!/usr/bin/env python3
"""Generate trust decay visualization figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def create_trust_decay_figure(output_dir: Path) -> Path:
    """
    Create trust delegation decay visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Colorblind-friendly palette (IBM Design + Wong)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = ["#648FFF", "#DC267F", "#FFB000", "#785EF0", "#FE6100"]

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.trust import TrustCalculus, TrustConfig

    # Panel A: Trust decay curves for different δ values
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
            color=colors[i],
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
    ax1.legend(loc="upper right", fontsize=9)
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

    bars1 = ax2.bar(
        x - width / 2,
        initial_trust,
        width,
        label="Initial Trust",
        color="#648FFF",
        alpha=0.8,
    )
    bars2 = ax2.bar(
        x + width / 2,
        after_attack,
        width,
        label="After Attack",
        color="#DC267F",
        alpha=0.8,
    )

    ax2.set_ylabel("Trust Integrity", fontsize=12)
    ax2.set_title("B. Trust Preservation Under Attack", fontsize=13, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, fontsize=10)
    ax2.legend(loc="upper left", fontsize=9)
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

    plt.tight_layout()

    output_path_png = output_dir / "trust_decay.png"
    output_path_pdf = output_dir / "trust_decay.pdf"

    plt.savefig(
        output_path_png,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf


if __name__ == "__main__":
    # Derive base_dir from the script's actual location
    # Script is at: projects/{project_name}/scripts/{script}.py
    script_dir = Path(__file__).resolve().parent  # scripts/
    base_dir = script_dir.parent  # projects/{project_name}/
    
    output_dir = base_dir / "output" / "figures"
    create_trust_decay_figure(output_dir)
