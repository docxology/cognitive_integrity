"""
Attack Surface Visualization Logic.

Moves logic from script 01 to a reusable module.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pathlib import Path
from .utils import setup_plotting, save_figure

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
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    # Enable LaTeX rendering for proper omega symbols
    plt.rcParams['text.usetex'] = False  # Use mathtext instead of full LaTeX
    plt.rcParams['font.size'] = 12
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colors
    colors = {
        "user": "#4A90D9",
        "firewall": "#E67E22",
        "orchestrator": "#27AE60",
        "agent": "#9B59B6",
        "external": "#E74C3C",
        "attack": "#C0392B",
    }

    # User input (top)
    _draw_box(ax, (4, 9), 2, 0.6, colors["user"], "User Input", fontsize=12)
    ax.text(5.8, 9.1, r"($\Omega_1$)", fontsize=10, color="white")

    # Firewall
    _draw_box(ax, (3.5, 7.5), 3, 0.8, colors["firewall"], "Cognitive Firewall", fontsize=12)

    # Orchestrator
    _draw_box(ax, (3.5, 5.5), 3, 1.2, colors["orchestrator"], "Orchestrator", fontsize=12)
    ax.text(5, 5.8, r"($\Omega_5$)", ha="center", va="center", fontsize=11, color="white")

    # Agents (bottom row)
    agent_positions = [(1.5, 3), (3.5, 3), (5.5, 3), (7.5, 3)]
    for i, (x, y) in enumerate(agent_positions):
        _draw_box(ax, (x, y), 1.5, 1.2, colors["agent"], f"Agent {i+1}", fontsize=11)
        if i in [0, 3]:  # Mark compromisable agents
            ax.text(
                x + 0.75,
                y + 0.35,
                r"($\Omega_3$)",
                ha="center",
                va="center",
                fontsize=10,
                color="white",
            )

    # External services (right side)
    _draw_box(ax, (8.5, 6), 1.3, 2.5, colors["external"], "External\nServices", fontsize=11)
    ax.text(
        9.15, 6.8, "• Web APIs", ha="center", va="center", fontsize=10, color="white"
    )
    ax.text(9.15, 6.4, "• Tools", ha="center", va="center", fontsize=10, color="white")
    ax.text(9.15, 6.0, r"($\Omega_2$)", ha="center", va="center", fontsize=10, color="white")

    # Shared state (bottom)
    _draw_box(ax, (2, 1), 6, 0.8, "#34495E", r"Shared State ($\Omega_4$)", fontsize=12)

    # Arrows
    # User -> Firewall
    _draw_arrow(ax, (5, 9), (5, 8.3))
    # Firewall -> Orchestrator
    _draw_arrow(ax, (5, 7.5), (5, 6.7))

    # Orchestrator -> Agents
    for x, y in agent_positions:
        _draw_arrow(ax, (5, 5.5), (x + 0.75, 4.2), lw=1.5)

    # Agents -> Shared state
    for x, y in agent_positions:
        _draw_arrow(ax, (x + 0.75, 3), (x + 0.75, 1.8), style="<->", color="#34495E")

    # External -> Orchestrator
    ax.annotate(
        "",
        xy=(6.5, 6.3),
        xytext=(8.5, 6.8),
        arrowprops=dict(
            arrowstyle="->",
            color=colors["external"],
            lw=2,
            connectionstyle="arc3,rad=-0.2",
        ),
    )

    # Inter-agent communication (Ω₄)
    for i in range(len(agent_positions) - 1):
        x1, _ = agent_positions[i]
        x2, _ = agent_positions[i+1]
        mid_x = (x1 + x2) / 2 + 0.75  # approximate
        # Just drawing decorative arrows between agents
        # The original code was hardcoded:
        # (3.5, 3.6) -> (3, 3.6) etc.
    
    # Replicating original arrows precisely
    ax.annotate("", xy=(3.5, 3.6), xytext=(3, 3.6), arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5))
    ax.annotate("", xy=(5.5, 3.6), xytext=(5, 3.6), arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5))
    ax.annotate("", xy=(7.5, 3.6), xytext=(7, 3.6), arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5))
    
    # Add coordination flow label
    ax.text(5, 4.1, r"Inter-agent Coordination ($\Omega_4$)", fontsize=9, ha="center", 
            color="#666", style="italic")

    # Legend
    legend_items = [
        (colors["user"], r"$\Omega_1$: External input"),
        (colors["external"], r"$\Omega_2$: Peripheral (tools/APIs)"),
        (colors["agent"], r"$\Omega_3$: Agent-level compromise"),
        ("#34495E", r"$\Omega_4$: Coordination channels"),
        (colors["orchestrator"], r"$\Omega_5$: Systemic (orchestrator)"),
    ]

    for i, (color, label) in enumerate(legend_items):
        ax.add_patch(
            plt.Rectangle(
                (0.2, 8.5 - i * 0.5), 0.3, 0.3, facecolor=color, edgecolor="black"
            )
        )
        ax.text(0.6, 8.65 - i * 0.5, label, fontsize=11, va="center")

    ax.set_title(
        "Multiagent Operator Attack Surface", fontsize=16, fontweight="bold", pad=20
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
        pos[0] + width/2,
        pos[1] + height/2,
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
