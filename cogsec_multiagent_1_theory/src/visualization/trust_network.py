"""
Trust Network Visualization Logic.

Moves logic from script 11 to a reusable module.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from .utils import save_figure, setup_plotting


def generate_trust_network_figure(output_dir: Path) -> list[Path]:
    """
    Generate the trust network visualization.

    Args:
        output_dir: Directory to save output files

    Returns:
        List of generated file paths
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Set up styling
    setup_plotting()

    # Use the color dictionary from the original script patterns
    colors = {
        "base": "#648FFF",  # Architectural trust (blue)
        "reputation": "#785EF0",  # Reputation trust (purple)
        "context": "#DC267F",  # Context trust (pink)
        "high_trust": "#2ECC71",  # High trust node
        "medium_trust": "#F39C12",  # Medium trust node
        "low_trust": "#E74C3C",  # Low/compromised node
        "orchestrator": "#2C3E50",  # Orchestrator
    }

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    # Common layout settings
    for ax in axes:
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_aspect("equal")
        ax.axis("off")

    # --- Panel A: Normal Trust Network ---
    ax1 = axes[0]
    ax1.set_title("A. Normal Trust Network (illustrative)", fontsize=13, fontweight="bold", pad=10)

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

    # Trust connections: (src, dst, trust_score, category)
    #
    # Illustrative topology, not a simulation output. Thirty-two two-decimal
    # trust scores are typed below across the normal and attacked panels, and
    # the figure draws a numeric label on every edge above 0.5, which is how a
    # worked example comes to read as a measured before-and-after. No
    # simulation in this series produces per-edge trust for a named nine-agent
    # topology; what is measured is the decay law itself, in Part 2's trust
    # calculus tests. The panel titles carry the qualifier.
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

    _draw_network(ax1, agents_normal, trust_normal, colors)

    # --- Panel B: Trust Network Under Attack ---
    ax2 = axes[1]
    ax2.set_title("B. Trust Network Under Attack (illustrative)", fontsize=13, fontweight="bold", pad=10)

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

    # Special node colors for attack scenario
    node_colors_attack = {
        "A3": colors["low_trust"],  # Compromised
        "A8": colors["medium_trust"],  # Affected
    }

    _draw_network(ax2, agents_normal, trust_attack, colors, node_colors_override=node_colors_attack)

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
        mpatches.Patch(facecolor=colors["base"], edgecolor="black", label="Base Trust", alpha=0.6),
        mpatches.Patch(
            facecolor=colors["reputation"], edgecolor="black", label="Reputation Trust", alpha=0.6
        ),
        mpatches.Patch(
            facecolor=colors["context"], edgecolor="black", label="Context Trust", alpha=0.6
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["high_trust"],
            markersize=10,
            label="High Trust",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["medium_trust"],
            markersize=10,
            label="Medium Trust",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["low_trust"],
            markersize=10,
            label="Low/Compromised",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors["orchestrator"],
            markersize=10,
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

    # Add simplified trust formula (focus on clarity)
    fig.text(
        0.5,
        0.95,
        r"$T = \alpha T_{base} + \beta T_{rep} + \gamma T_{ctx}$",
        ha="center",
        fontsize=12,
        style="italic",
    )

    plt.tight_layout(rect=[0, 0.1, 1, 0.93])

    return [save_figure(fig, output_dir, "trust_network")]


def _draw_network(ax, positions, connections, colors, node_colors_override=None):
    """Helper to draw the network components on an axis."""
    node_colors_override = node_colors_override or {}

    # Draw edges
    for src, dst, trust, category in connections:
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        width = trust * 3  # Scale line width

        # Dim low trust lines more in visualization
        alpha = 0.3 if trust < 0.4 else 0.6

        ax.plot(
            [x1, x2],
            [y1, y2],
            "-",
            color=colors[category],
            linewidth=width,
            alpha=alpha,
            zorder=1,
        )
        # Add trust score label at edge midpoint for educational clarity
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        if trust >= 0.5:  # Only label significant trust edges
            ax.text(
                mid_x,
                mid_y + 0.08,
                f"{trust:.2f}",
                fontsize=6,
                ha="center",
                va="bottom",
                color="#555",
                zorder=2,
            )

    # Draw nodes
    for agent, (x, y) in positions.items():
        if agent == "O":
            color = colors["orchestrator"]
        else:
            color = node_colors_override.get(agent, colors["high_trust"])

        circle = Circle((x, y), 0.12, facecolor=color, edgecolor="black", linewidth=2, zorder=5)
        ax.add_patch(circle)
        ax.text(
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
