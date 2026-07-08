"""Attack Surface module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure


def plot_attack_surface(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Create the attack surface node-link diagram (Fig 1)."""
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Apply publication styles
    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    # Facecolor needs to be set on fig for dark mode compatibility if defined in style
    # but strictly white for papers usually

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Colors from shared palette
    colors = SEMANTIC_COLORS

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
    ax.text(5.8, 9.1, "(Ω₁)", fontsize=FONTSIZE["small"], color="white")

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
    ax.text(5, 5.8, "(Ω₅)", ha="center", va="center", fontsize=FONTSIZE["base"], color="white")

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
            fontsize=FONTSIZE["base"],
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
                fontsize=FONTSIZE["small"],
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
        fontsize=FONTSIZE["base"],
        fontweight="bold",
        color="white",
    )
    ax.text(
        9.15,
        7.4,
        "Services",
        ha="center",
        va="center",
        fontsize=FONTSIZE["base"],
        fontweight="bold",
        color="white",
    )
    ax.text(
        9.15, 6.8, "• Web APIs", ha="center", va="center", fontsize=FONTSIZE["small"], color="white"
    )
    ax.text(9.15, 6.4, "• Tools", ha="center", va="center", fontsize=FONTSIZE["small"], color="white")  # noqa: E501
    ax.text(9.15, 6.0, "(Ω₂)", ha="center", va="center", fontsize=FONTSIZE["small"], color="white")

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
        ax.text(0.6, 8.65 - i * 0.5, label, fontsize=FONTSIZE["base"], va="center")

    ax.set_title(
        "Multiagent Operator Attack Surface", fontsize=14, fontweight="bold", pad=20
    )

    # CIF defense annotations at each tier
    cif_annotations = [
        (9.2, 7.65, "Defense: CognitiveFirewall.classify()", SEMANTIC_COLORS["firewall"]),
        (9.2, 5.7, "Defense: InvariantChecker.check_all()", SEMANTIC_COLORS["invariants"]),
        (9.2, 3.4, "Defense: CognitiveTripwire.check()", SEMANTIC_COLORS["tripwire"]),
        (6.5, 1.0, "Defense: ProvenanceChain.get_effective_taint()", SEMANTIC_COLORS["anomaly"]),
    ]
    for x, y, label, color in cif_annotations:  # type: ignore[assignment]
        ax.text(
            x, y, label,
            fontsize=FONTSIZE["small"], fontstyle="italic",
            color=color, alpha=0.9,
        )

    add_source_annotation(fig, "src/visualization/figures/attack_surface.py")
    save_figure(fig, "attack_surface", output_dir=output_dir)
    return fig
