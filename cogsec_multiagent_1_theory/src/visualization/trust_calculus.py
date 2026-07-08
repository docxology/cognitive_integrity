"""Trust Calculus module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Trust calculus visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch


def create_trust_calculus_figure(output_dir: Path) -> Path:
    """
    Create trust calculus and delegation visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Set up styling
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 12,
            "axes.linewidth": 1.5,
        }
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    colors = {
        "header": "#2C3E50",
        "agent": "#3498DB",
        "attack": "#E74C3C",
        "trust_high": "#27AE60",
        "trust_med": "#F39C12",
        "trust_low": "#E74C3C",
        "delegated": "#9B59B6",
    }

    # Panel A: Trust Decay Function
    ax1 = axes[0, 0]
    depths = np.arange(0, 8)
    delta_values = [0.95, 0.9, 0.85, 0.8]

    for delta in delta_values:
        trust = [delta**d for d in depths]
        ax1.plot(depths, trust, "o-", linewidth=2.5, markersize=10, label=f"δ = {delta}")

    ax1.axhline(y=0.5, color="#DC267F", linestyle="--", linewidth=2, label="Trust threshold τ")
    ax1.fill_between(depths, 0, 0.5, color="#DC267F", alpha=0.1)
    ax1.set_xlabel("Delegation Depth (d)", fontsize=14)
    ax1.set_ylabel("Trust Level T(a→c)", fontsize=14)
    ax1.set_title("A. Trust Decay: T(a→c) ≤ δᵈ · T(a→b)", fontsize=14, fontweight="bold", pad=12)
    ax1.legend(loc="upper right", fontsize=12)
    ax1.set_xlim(-0.2, 7.2)
    ax1.set_ylim(0, 1.05)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(depths)
    ax1.annotate(
        "Untrusted\nzone", xy=(5, 0.25), fontsize=12, ha="center", color="#DC267F", style="italic"
    )

    # Panel B: Trust Update Mechanism
    ax2 = axes[0, 1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis("off")
    ax2.set_title("B. Trust Update Mechanism", fontsize=14, fontweight="bold", pad=12)

    formula_box = FancyBboxPatch(
        (0.5, 7),
        9,
        2.5,
        boxstyle="round,pad=0.05",
        facecolor="#F8F9FA",
        edgecolor=colors["header"],
        linewidth=2,
    )
    ax2.add_patch(formula_box)
    ax2.text(
        5,
        8.8,
        "T'(a→b) = α·T(a→b) + β·outcome + γ·consensus",
        ha="center",
        va="center",
        fontsize=13,
        fontfamily="monospace",
        fontweight="bold",
        color=colors["header"],
    )
    ax2.text(
        5,
        8.0,
        "where: α + β + γ = 1 (normalization)",
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color="#5D6D7E",
    )

    components = [
        ("Historical\nTrust", "α·T(a→b)", colors["agent"], 1.5, 4.5),
        ("Outcome\nVerification", "β·outcome", colors["trust_high"], 5, 4.5),
        ("Peer\nConsensus", "γ·consensus", colors["delegated"], 8.5, 4.5),
    ]
    for name, formula, color, x, y in components:
        box = FancyBboxPatch(
            (x - 1.2, y - 0.8),
            2.4,
            2,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="black",
            linewidth=1.5,
            alpha=0.8,
        )
        ax2.add_patch(box)
        ax2.text(
            x,
            y + 0.4,
            name,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color="white",
        )
        ax2.text(
            x,
            y - 0.3,
            formula,
            ha="center",
            va="center",
            fontsize=11,
            fontfamily="monospace",
            color="white",
        )

    result_box = FancyBboxPatch(
        (3, 0.8),
        4,
        1.2,
        boxstyle="round,pad=0.02",
        facecolor=colors["trust_high"],
        edgecolor="black",
        linewidth=2,
    )
    ax2.add_patch(result_box)
    ax2.text(
        5,
        1.4,
        "Updated Trust T'(a→b)",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color="white",
    )

    # Panel C: Delegation Chain Bounds
    ax3 = axes[1, 0]
    ax3.set_xlim(0, 14)
    ax3.set_ylim(0, 8)
    ax3.axis("off")
    ax3.set_title(
        "C. Bounded Delegation Chain (Theorem 3.1)", fontsize=14, fontweight="bold", pad=12
    )

    agents = ["A", "B", "C", "D", "E"]
    trust_values = [1.0, 0.9, 0.81, 0.73, 0.66]
    positions = [(1.5, 5), (4, 5), (6.5, 5), (9, 5), (11.5, 5)]

    for i, (agent, trust, (x, y)) in enumerate(zip(agents, trust_values, positions)):
        color = (
            colors["trust_high"]
            if trust >= 0.8
            else colors["trust_med"]
            if trust >= 0.6
            else colors["trust_low"]
        )
        circle = Circle((x, y), 0.8, facecolor=color, edgecolor="black", linewidth=2)
        ax3.add_patch(circle)
        ax3.text(
            x,
            y + 0.1,
            agent,
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color="white",
        )
        ax3.text(
            x, y - 0.35, f"T={trust:.2f}", ha="center", va="center", fontsize=11, color="white"
        )
        if i < len(agents) - 1:
            ax3.annotate(
                "",
                xy=(positions[i + 1][0] - 0.9, y),
                xytext=(x + 0.9, y),
                arrowprops=dict(
                    arrowstyle="-|>", color=colors["header"], lw=2.5, mutation_scale=18
                ),
            )
            ax3.text(
                (x + positions[i + 1][0]) / 2,
                y + 0.6,
                "δ=0.9",
                ha="center",
                va="center",
                fontsize=10,
                color="#7F8C8D",
                style="italic",
            )

    ax3.text(
        7,
        3,
        "T(A→E) ≤ δ⁴·T(A→B) = 0.9⁴ × 1.0 = 0.66",
        ha="center",
        va="center",
        fontsize=13,
        fontfamily="monospace",
        color=colors["header"],
    )
    ax3.text(
        7,
        2,
        "Trust bounded exponentially: prevents trust amplification",
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color="#5D6D7E",
    )

    # Panel D: Trust Laundering Prevention
    ax4 = axes[1, 1]
    ax4.set_xlim(0, 14)
    ax4.set_ylim(0, 8)
    ax4.axis("off")
    ax4.set_title("D. Trust Laundering Prevention", fontsize=14, fontweight="bold", pad=12)

    ax4.text(
        7,
        7,
        "Attack Attempt: Malicious → Trusted → Target",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=colors["attack"],
    )

    mal_circle = Circle((2, 4.5), 0.9, facecolor=colors["attack"], edgecolor="black", linewidth=2)
    ax4.add_patch(mal_circle)
    ax4.text(2, 4.7, "M", ha="center", va="center", fontsize=16, fontweight="bold", color="white")
    ax4.text(2, 4.1, "Malicious", ha="center", va="center", fontsize=10, color="white")

    trust_circle = Circle((7, 4.5), 0.9, facecolor=colors["agent"], edgecolor="black", linewidth=2)
    ax4.add_patch(trust_circle)
    ax4.text(7, 4.7, "T", ha="center", va="center", fontsize=16, fontweight="bold", color="white")
    ax4.text(7, 4.1, "Trusted", ha="center", va="center", fontsize=10, color="white")

    target_circle = Circle(
        (12, 4.5), 0.9, facecolor=colors["trust_high"], edgecolor="black", linewidth=2
    )
    ax4.add_patch(target_circle)
    ax4.text(12, 4.7, "V", ha="center", va="center", fontsize=16, fontweight="bold", color="white")
    ax4.text(12, 4.1, "Victim", ha="center", va="center", fontsize=10, color="white")

    ax4.annotate(
        "",
        xy=(6, 4.5),
        xytext=(3, 4.5),
        arrowprops=dict(arrowstyle="-|>", color=colors["attack"], lw=2.5, mutation_scale=18),
    )
    ax4.text(4.5, 5.2, "T(M→T)=0.3", ha="center", va="center", fontsize=11, color=colors["attack"])

    ax4.annotate(
        "",
        xy=(11, 4.5),
        xytext=(8, 4.5),
        arrowprops=dict(arrowstyle="-|>", color=colors["agent"], lw=2.5, mutation_scale=18),
    )
    ax4.text(9.5, 5.2, "T(T→V)=0.9", ha="center", va="center", fontsize=11, color=colors["agent"])

    # Block X
    ax4.plot([6.8, 8.2], [3, 2], color=colors["attack"], linewidth=3.5)
    ax4.plot([6.8, 8.2], [2, 3], color=colors["attack"], linewidth=3.5)

    result_box = FancyBboxPatch(
        (2, 0.5),
        10,
        1.5,
        boxstyle="round,pad=0.02",
        facecolor=colors["trust_high"],
        edgecolor="black",
        linewidth=2,
        alpha=0.9,
    )
    ax4.add_patch(result_box)
    ax4.text(
        7,
        1.5,
        "T(M→V) ≤ δ · T(M→T) = 0.9 × 0.3 = 0.27 < τ",
        ha="center",
        va="center",
        fontsize=13,
        fontfamily="monospace",
        fontweight="bold",
        color="white",
    )
    ax4.text(
        7,
        0.9,
        "Delegated trust BLOCKED - below threshold",
        ha="center",
        va="center",
        fontsize=12,
        color="white",
    )

    plt.tight_layout()

    # Save outputs
    output_path_png = output_dir / "trust_calculus_comprehensive.png"
    output_path_pdf = output_dir / "trust_calculus_comprehensive.pdf"
    plt.savefig(output_path_png, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf
