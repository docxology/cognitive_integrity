#!/usr/bin/env python3
"""Generate attack surface visualization figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def create_attack_surface_figure(output_dir: Path) -> Path:
    """
    Create multiagent operator attack surface diagram.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
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
    user_box = FancyBboxPatch(
        (4, 9),
        2,
        0.6,
        boxstyle="round,pad=0.05",
        facecolor=colors["user"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(user_box)
    ax.text(
        5,
        9.3,
        "User Input",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="white",
    )
    ax.text(5.8, 9.1, "(Ω₁)", fontsize=8, color="white")

    # Firewall
    firewall_box = FancyBboxPatch(
        (3.5, 7.5),
        3,
        0.8,
        boxstyle="round,pad=0.05",
        facecolor=colors["firewall"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(firewall_box)
    ax.text(
        5,
        7.9,
        "Cognitive Firewall",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="white",
    )

    # Orchestrator
    orch_box = FancyBboxPatch(
        (3.5, 5.5),
        3,
        1.2,
        boxstyle="round,pad=0.05",
        facecolor=colors["orchestrator"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(orch_box)
    ax.text(
        5,
        6.2,
        "Orchestrator",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="white",
    )
    ax.text(5, 5.8, "(Ω₅)", ha="center", va="center", fontsize=9, color="white")

    # Agents (bottom row)
    agent_positions = [(1.5, 3), (3.5, 3), (5.5, 3), (7.5, 3)]
    for i, (x, y) in enumerate(agent_positions):
        box = FancyBboxPatch(
            (x, y),
            1.5,
            1.2,
            boxstyle="round,pad=0.05",
            facecolor=colors["agent"],
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(box)
        ax.text(
            x + 0.75,
            y + 0.7,
            f"Agent {i+1}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )
        if i in [0, 3]:  # Mark compromisable agents
            ax.text(
                x + 0.75,
                y + 0.35,
                "(Ω₃)",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
            )

    # External services (right side)
    ext_box = FancyBboxPatch(
        (8.5, 6),
        1.3,
        2.5,
        boxstyle="round,pad=0.05",
        facecolor=colors["external"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(ext_box)
    ax.text(
        9.15,
        7.8,
        "External",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
    )
    ax.text(
        9.15,
        7.4,
        "Services",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
    )
    ax.text(
        9.15, 6.8, "• Web APIs", ha="center", va="center", fontsize=8, color="white"
    )
    ax.text(9.15, 6.4, "• Tools", ha="center", va="center", fontsize=8, color="white")
    ax.text(9.15, 6.0, "(Ω₂)", ha="center", va="center", fontsize=8, color="white")

    # Shared state (bottom)
    state_box = FancyBboxPatch(
        (2, 1),
        6,
        0.8,
        boxstyle="round,pad=0.05",
        facecolor="#34495E",
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(state_box)
    ax.text(
        5,
        1.4,
        "Shared State (Ω₄)",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="white",
    )

    # Arrows
    arrow_style = "Simple, tail_width=0.5, head_width=4, head_length=8"

    # User -> Firewall
    ax.annotate(
        "",
        xy=(5, 8.3),
        xytext=(5, 9),
        arrowprops=dict(arrowstyle="->", color="black", lw=2),
    )

    # Firewall -> Orchestrator
    ax.annotate(
        "",
        xy=(5, 6.7),
        xytext=(5, 7.5),
        arrowprops=dict(arrowstyle="->", color="black", lw=2),
    )

    # Orchestrator -> Agents
    for x, y in agent_positions:
        ax.annotate(
            "",
            xy=(x + 0.75, 4.2),
            xytext=(5, 5.5),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        )

    # Agents -> Shared state
    for x, y in agent_positions:
        ax.annotate(
            "",
            xy=(x + 0.75, 1.8),
            xytext=(x + 0.75, 3),
            arrowprops=dict(arrowstyle="<->", color="#34495E", lw=1.5),
        )

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
    ax.annotate(
        "",
        xy=(3.5, 3.6),
        xytext=(3, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5),
    )
    ax.annotate(
        "",
        xy=(5.5, 3.6),
        xytext=(5, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5),
    )
    ax.annotate(
        "",
        xy=(7.5, 3.6),
        xytext=(7, 3.6),
        arrowprops=dict(arrowstyle="<->", color="#9B59B6", lw=1.5),
    )

    # Legend
    legend_items = [
        (colors["user"], "Ω₁: External input"),
        (colors["external"], "Ω₂: Peripheral (tools/APIs)"),
        (colors["agent"], "Ω₃: Agent-level compromise"),
        ("#34495E", "Ω₄: Coordination channels"),
        (colors["orchestrator"], "Ω₅: Systemic (orchestrator)"),
    ]

    for i, (color, label) in enumerate(legend_items):
        ax.add_patch(
            plt.Rectangle(
                (0.2, 8.5 - i * 0.5), 0.3, 0.3, facecolor=color, edgecolor="black"
            )
        )
        ax.text(0.6, 8.65 - i * 0.5, label, fontsize=9, va="center")

    ax.set_title(
        "Multiagent Operator Attack Surface", fontsize=14, fontweight="bold", pad=20
    )

    output_path_png = output_dir / "attack_surface.png"
    output_path_pdf = output_dir / "attack_surface.pdf"

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
    create_attack_surface_figure(output_dir)
