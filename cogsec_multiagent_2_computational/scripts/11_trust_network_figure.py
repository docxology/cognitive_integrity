#!/usr/bin/env python3
"""Generate trust network visualization figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch


def create_trust_network_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Create network graph visualization of trust relationships.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # Set up professional styling
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 11,
            "axes.linewidth": 1.5,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    # Colorblind-friendly palette for trust categories
    colors = {
        "base": "#648FFF",  # Architectural trust (blue)
        "reputation": "#785EF0",  # Reputation trust (purple)
        "context": "#DC267F",  # Context trust (pink)
        "high_trust": "#2ECC71",  # High trust node
        "medium_trust": "#F39C12",  # Medium trust node
        "low_trust": "#E74C3C",  # Low/compromised node
        "orchestrator": "#2C3E50",  # Orchestrator
    }

    np.random.seed(42)

    # Panel A: Normal trust network
    ax1 = axes[0]
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-2, 2)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("A. Normal Trust Network", fontsize=13, fontweight="bold", pad=10)

    # Agent positions (arranged in a pattern)
    agents_normal = {
        "O": (0, 0),  # Orchestrator (center)
        "A1": (-1.2, 1),
        "A2": (1.2, 1),
        "A3": (-1.2, -1),
        "A4": (1.2, -1),
        "A5": (0, 1.5),
        "A6": (-1.6, 0),
        "A7": (1.6, 0),
        "A8": (0, -1.5),
    }

    # Agent importance (node sizes)
    importance = {
        "O": 800,
        "A1": 400,
        "A2": 400,
        "A3": 300,
        "A4": 300,
        "A5": 350,
        "A6": 250,
        "A7": 250,
        "A8": 300,
    }

    # Trust levels (edge weights)
    trust_normal = [
        ("O", "A1", 0.95, "base"),
        ("O", "A2", 0.92, "base"),
        ("O", "A3", 0.88, "base"),
        ("O", "A4", 0.90, "base"),
        ("O", "A5", 0.85, "base"),
        ("O", "A6", 0.82, "base"),
        ("O", "A7", 0.87, "base"),
        ("O", "A8", 0.84, "base"),
        ("A1", "A2", 0.75, "reputation"),
        ("A1", "A5", 0.80, "reputation"),
        ("A2", "A5", 0.78, "reputation"),
        ("A3", "A4", 0.72, "reputation"),
        ("A3", "A8", 0.70, "context"),
        ("A4", "A8", 0.68, "context"),
        ("A6", "A1", 0.65, "context"),
        ("A7", "A2", 0.67, "context"),
    ]

    # Draw edges
    for src, dst, trust, category in trust_normal:
        x1, y1 = agents_normal[src]
        x2, y2 = agents_normal[dst]
        width = trust * 3  # Scale line width
        ax1.plot(
            [x1, x2],
            [y1, y2],
            "-",
            color=colors[category],
            linewidth=width,
            alpha=0.6,
            zorder=1,
        )

    # Draw nodes
    for agent, (x, y) in agents_normal.items():
        if agent == "O":
            color = colors["orchestrator"]
        else:
            color = colors["high_trust"]

        circle = Circle(
            (x, y), 0.12, facecolor=color, edgecolor="black", linewidth=2, zorder=5
        )
        ax1.add_patch(circle)
        ax1.text(
            x,
            y,
            agent,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
            zorder=6,
        )

    # Panel B: Trust network under attack (compromised agent)
    ax2 = axes[1]
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2, 2)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title(
        "B. Trust Network Under Attack", fontsize=13, fontweight="bold", pad=10
    )

    # Modified trust levels (A3 is compromised)
    trust_attack = [
        ("O", "A1", 0.95, "base"),
        ("O", "A2", 0.92, "base"),
        ("O", "A3", 0.25, "base"),  # Reduced trust to compromised
        ("O", "A4", 0.90, "base"),
        ("O", "A5", 0.85, "base"),
        ("O", "A6", 0.82, "base"),
        ("O", "A7", 0.87, "base"),
        ("O", "A8", 0.55, "base"),  # Affected by proximity
        ("A1", "A2", 0.75, "reputation"),
        ("A1", "A5", 0.80, "reputation"),
        ("A2", "A5", 0.78, "reputation"),
        ("A3", "A4", 0.20, "reputation"),  # A3 connections degraded
        ("A3", "A8", 0.15, "context"),
        ("A4", "A8", 0.45, "context"),  # Affected
        ("A6", "A1", 0.65, "context"),
        ("A7", "A2", 0.67, "context"),
    ]

    # Draw edges with attack modifications
    for src, dst, trust, category in trust_attack:
        x1, y1 = agents_normal[src]
        x2, y2 = agents_normal[dst]
        width = trust * 3
        alpha = 0.3 if trust < 0.4 else 0.6
        ax2.plot(
            [x1, x2],
            [y1, y2],
            "-",
            color=colors[category],
            linewidth=width,
            alpha=alpha,
            zorder=1,
        )

    # Draw nodes with attack state
    for agent, (x, y) in agents_normal.items():
        if agent == "O":
            color = colors["orchestrator"]
        elif agent == "A3":
            color = colors["low_trust"]  # Compromised
        elif agent == "A8":
            color = colors["medium_trust"]  # Affected
        else:
            color = colors["high_trust"]

        circle = Circle(
            (x, y), 0.12, facecolor=color, edgecolor="black", linewidth=2, zorder=5
        )
        ax2.add_patch(circle)
        ax2.text(
            x,
            y,
            agent,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
            zorder=6,
        )

    # Add attack indicator
    x3, y3 = agents_normal["A3"]
    ax2.annotate(
        "Compromised",
        xy=(x3, y3),
        xytext=(x3 - 0.8, y3 + 0.6),
        fontsize=9,
        color=colors["low_trust"],
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=colors["low_trust"]),
    )

    # Shared legend
    legend_elements = [
        mpatches.Patch(
            facecolor=colors["base"],
            edgecolor="black",
            label="Base Trust (Architectural)",
            alpha=0.6,
        ),
        mpatches.Patch(
            facecolor=colors["reputation"],
            edgecolor="black",
            label="Reputation Trust (Historical)",
            alpha=0.6,
        ),
        mpatches.Patch(
            facecolor=colors["context"],
            edgecolor="black",
            label="Context Trust (Task-specific)",
            alpha=0.6,
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["high_trust"],
            markersize=12,
            label="High Trust Agent",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["medium_trust"],
            markersize=12,
            label="Medium Trust Agent",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["low_trust"],
            markersize=12,
            label="Low/Compromised Agent",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["orchestrator"],
            markersize=12,
            label="Orchestrator",
        ),
    ]

    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=4,
        fontsize=9,
        frameon=True,
        fancybox=True,
        framealpha=0.95,
        bbox_to_anchor=(0.5, 0.02),
    )

    # Add trust formula
    fig.text(
        0.5,
        0.95,
        r"Trust: $T = \alpha \cdot T_{base} + \beta \cdot T_{rep} + \gamma \cdot T_{ctx}$",
        ha="center",
        fontsize=11,
        style="italic",
    )

    plt.tight_layout(rect=[0, 0.1, 1, 0.93])

    # Save as both PNG and PDF
    output_png = output_dir / "trust_network.png"
    output_pdf = output_dir / "trust_network.pdf"

    plt.savefig(
        output_png, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.savefig(output_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_png))
    print(str(output_pdf))
    return output_png, output_pdf


if __name__ == "__main__":
    # Derive base_dir from the script's actual location
    # Script is at: projects/{project_name}/scripts/{script}.py
    script_dir = Path(__file__).resolve().parent  # scripts/
    base_dir = script_dir.parent  # projects/{project_name}/
    
    output_dir = base_dir / "output" / "figures"
    create_trust_network_figure(output_dir)
