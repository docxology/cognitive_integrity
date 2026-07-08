"""
from __future__ import annotations

Attack Surface Visualization Logic.

Moves logic from script 01 to a reusable module.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .utils import save_figure, setup_plotting


def generate_attack_surface_figure(output_dir: Path) -> Path:
    """
    Generate the attack surface visualization.

    Args:
        output_dir: Directory to save output files

    Returns:
        Path to generated PDF
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    setup_plotting()

    fig, ax = plt.subplots(1, 1, figsize=(14, 12))  # Larger canvas
    # Enable LaTeX rendering for proper omega symbols
    plt.rcParams["text.usetex"] = False  # Use mathtext instead of full LaTeX
    plt.rcParams["font.size"] = 14  # Larger base font
    plt.rcParams["font.family"] = "sans-serif"

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colors - High Contrast
    colors = {
        "user": "#4A90D9",  # Blue
        "firewall": "#E67E22",  # Orange
        "orchestrator": "#27AE60",  # Green
        "agent": "#8E44AD",  # Purple
        "external": "#C0392B",  # Red
        "shared": "#2C3E50",  # Dark Blue-Grey
    }

    # User input (top)
    _draw_box(ax, (4, 9), 2, 0.7, colors["user"], "User Input\n(Prompts)", fontsize=13)
    ax.text(6.1, 9.35, r"$\Omega_1$", fontsize=16, color="black", weight="bold")

    # Firewall
    _draw_box(
        ax, (3.5, 7.5), 3, 0.9, colors["firewall"], "Cognitive Firewall\n(Filter)", fontsize=13
    )

    # Orchestrator
    _draw_box(
        ax, (3.5, 5.3), 3, 1.4, colors["orchestrator"], "Orchestrator\n(Coordinator)", fontsize=13
    )
    ax.text(
        6.6, 6.0, r"$\Omega_5$", ha="center", va="center", fontsize=16, color="black", weight="bold"
    )

    # Agents (bottom row)
    agent_positions = [(1.5, 3), (3.5, 3), (5.5, 3), (7.5, 3)]
    for i, (x, y) in enumerate(agent_positions):
        _draw_box(ax, (x, y), 1.5, 1.2, colors["agent"], f"Agent {i + 1}", fontsize=12)
        if i in [0, 3]:  # Mark compromisable agents
            ax.text(
                x + 1.3,
                y + 1.0,
                r"$\Omega_3$",
                ha="center",
                va="center",
                fontsize=14,
                color="black",
                weight="bold",
            )

    # External services (right side)
    _draw_box(ax, (8.5, 6), 1.4, 2.8, colors["external"], "External\nServices", fontsize=12)
    ax.text(
        9.2, 6.9, "• Web APIs", ha="center", va="center", fontsize=11, color="white", weight="bold"
    )
    ax.text(
        9.2, 6.5, "• Tools", ha="center", va="center", fontsize=11, color="white", weight="bold"
    )
    ax.text(
        9.2, 6.1, "• RAG DBs", ha="center", va="center", fontsize=11, color="white", weight="bold"
    )
    ax.text(
        9.2, 8.9, r"$\Omega_2$", ha="center", va="center", fontsize=16, color="black", weight="bold"
    )

    # Shared state (bottom)
    _draw_box(
        ax,
        (2, 0.8),
        6,
        1.0,
        colors["shared"],
        r"Shared Belief State / Memory ($\Omega_4$)",
        fontsize=14,
    )

    # Arrows - Thicker and clearer
    # User -> Firewall
    _draw_arrow(ax, (5, 9), (5, 8.4), lw=2)
    # Firewall -> Orchestrator
    _draw_arrow(ax, (5, 7.5), (5, 6.7), lw=2)

    # Orchestrator -> Agents
    for x, y in agent_positions:
        _draw_arrow(ax, (5, 5.3), (x + 0.75, 4.2), lw=1.5)

    # Agents -> Shared state
    for x, y in agent_positions:
        _draw_arrow(ax, (x + 0.75, 3), (x + 0.75, 1.8), style="<->", color="#34495E", lw=2)

    # External -> Orchestrator
    ax.annotate(
        "",
        xy=(6.5, 6.0),
        xytext=(8.5, 6.8),
        arrowprops=dict(
            arrowstyle="->",
            color=colors["external"],
            lw=3,
            connectionstyle="arc3,rad=-0.2",
        ),
    )

    # Inter-agent communication (Ω₄)
    # Decorative arrows between agents
    ax.annotate(
        "",
        xy=(3.5, 3.6),
        xytext=(3, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=2, linestyle="--"),
    )
    ax.annotate(
        "",
        xy=(5.5, 3.6),
        xytext=(5, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=2, linestyle="--"),
    )
    ax.annotate(
        "",
        xy=(7.5, 3.6),
        xytext=(7, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=2, linestyle="--"),
    )

    # Add coordination flow label
    ax.text(
        5,
        3.8,
        r"Inter-agent Coordination ($\Omega_4$)",
        fontsize=11,
        ha="center",
        color="#666",
        style="italic",
        backgroundcolor="#f0f0f0",
    )

    # Legend - improved placement and formatting
    legend_items = [
        (colors["user"], r"$\Omega_1$: External (Input)"),
        (colors["external"], r"$\Omega_2$: Peripheral (Tools/Data)"),
        (colors["agent"], r"$\Omega_3$: Agent (Internal)"),
        (colors["shared"], r"$\Omega_4$: Coordination (State)"),
        (colors["orchestrator"], r"$\Omega_5$: Systemic (Control)"),
    ]

    for i, (color, label) in enumerate(legend_items):
        ax.add_patch(
            plt.Rectangle((0.2, 9.5 - i * 0.6), 0.4, 0.4, facecolor=color, edgecolor="black")
        )
        ax.text(0.7, 9.7 - i * 0.6, label, fontsize=12, va="center", weight="bold")

    ax.set_title(
        "Multiagent Operator Attack Surface Taxonomy", fontsize=20, fontweight="bold", pad=20
    )

    save_figure(fig, output_dir, "attack_surface")
    return output_dir / "attack_surface.pdf"


def _draw_box(ax, pos, width, height, color, text, fontsize=12):
    box = FancyBboxPatch(
        pos,
        width,
        height,
        boxstyle="round,pad=0.05",
        facecolor=color,
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(box)

    # Split text for better centering if needed, but original used single string mostly
    # except External Services which I manually split in call
    ax.text(
        pos[0] + width / 2,
        pos[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold",
        color="white",
    )


def _draw_arrow(ax, start, end, style="->", color="black", lw=2):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle=style, color=color, lw=lw),
    )
