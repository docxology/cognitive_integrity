"""Fig 4: CIF block diagram showing defense layers.

Draws a three-layer Cognitive Integrity Framework architecture using
matplotlib Rectangle patches and annotated arrows.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, save_figure


def _draw_block(ax, x, y, w, h, label, color, fontsize=FONTSIZE["base"]):
    """Draw a rounded rectangle with centered label."""
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.9,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h / 2, label,
        ha="center", va="center",
        fontsize=fontsize, fontweight="bold",
        color="white",
    )


def _draw_arrow(ax, x0, y0, x1, y1, color="#333333"):
    """Draw a downward arrow between layers."""
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=2,
            connectionstyle="arc3,rad=0",
        ),
    )


def plot_cif_architecture(output_dir: str = "output/figures") -> Figure:
    """Create the CIF block diagram (Fig 4).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=9, height=6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Layer 1 - Input Layer
    layer1_y = 0.78
    _draw_block(ax, 0.30, layer1_y, 0.40, 0.12, "Cognitive Firewall\n(Input Layer)", COLORS["primary"], fontsize=11)  # noqa: E501
    ax.text(0.50, layer1_y + 0.15, "Incoming Messages", ha="center", fontsize=10, style="italic", color=COLORS["neutral"])  # noqa: E501
    _draw_arrow(ax, 0.50, 0.95, 0.50, layer1_y + 0.12, color=COLORS["neutral"])

    # Layer 2 - Reasoning Layer
    layer2_y = 0.52
    _draw_block(ax, 0.12, layer2_y, 0.30, 0.12, "Trust Calculus", PALETTE[0], fontsize=10)
    _draw_block(ax, 0.58, layer2_y, 0.30, 0.12, "Byzantine Consensus", PALETTE[4], fontsize=10)
    ax.text(0.50, layer2_y + 0.14, "Reasoning Layer", ha="center", fontsize=11, fontweight="bold", color="#333")  # noqa: E501

    # Arrows from Layer 1 to Layer 2
    _draw_arrow(ax, 0.40, layer1_y, 0.27, layer2_y + 0.12)
    _draw_arrow(ax, 0.60, layer1_y, 0.73, layer2_y + 0.12)

    # Layer 3 - Monitoring Layer
    layer3_y = 0.18
    modules = [
        ("Tripwire", 0.04, 0.15),
        ("Detection", 0.21, 0.15),
        ("Invariants", 0.38, 0.15),
        ("Provenance", 0.55, 0.15),
        ("Sandbox", 0.72, 0.15),
    ]
    colors = [PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[5], PALETTE[6]]
    for (label, mx, mw), c in zip(modules, colors):
        _draw_block(ax, mx, layer3_y, mw, 0.10, label, c, fontsize=FONTSIZE["base"])

    ax.text(0.50, layer3_y + 0.13, "Monitoring Layer", ha="center", fontsize=11, fontweight="bold", color="#333")  # noqa: E501

    # Arrows from Layer 2 to Layer 3
    _draw_arrow(ax, 0.27, layer2_y, 0.27, layer3_y + 0.10)
    _draw_arrow(ax, 0.73, layer2_y, 0.73, layer3_y + 0.10)
    _draw_arrow(ax, 0.50, layer2_y, 0.50, layer3_y + 0.10)

    # Output arrow
    ax.text(0.50, layer3_y - 0.07, "Secure Agent Response", ha="center", fontsize=10, style="italic", color=COLORS["secondary"])  # noqa: E501
    _draw_arrow(ax, 0.50, layer3_y, 0.50, layer3_y - 0.04, color=COLORS["secondary"])

    ax.set_title("Cognitive Integrity Framework (CIF) Architecture", fontsize=14, pad=15)
    fig.tight_layout()
    save_figure(fig, "fig04_cif_architecture", output_dir=output_dir)
    return fig
