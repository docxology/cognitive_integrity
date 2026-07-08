"""Fig 5: 4-category attack taxonomy tree.

Draws a tree diagram showing the attack taxonomy root branching into
4 categories, each with 3 subcategories and associated counts.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from ..style import FONTSIZE, PALETTE, create_figure, save_figure

_TAXONOMY = {
    "Injection\n(500)": [
        "Direct Injection (200)",
        "Indirect Injection (180)",
        "Nested Injection (120)",
    ],
    "Trust Exploitation\n(200)": [
        "Impersonation (80)",
        "Trust Inflation (70)",
        "Delegation Abuse (50)",
    ],
    "Belief Manipulation\n(150)": [
        "Belief Drift (60)",
        "Belief Fabrication (50)",
        "Belief Injection (40)",
    ],
    "Coordination\n(100)": [
        "Sybil Attack (40)",
        "Consensus Poisoning (35)",
        "Timing Attack (25)",
    ],
}


def _draw_node(ax, x, y, text, color, fontsize=FONTSIZE["small"], width=0.14, height=0.06):
    """Draw a rounded box with text."""
    rect = mpatches.FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.01",
        facecolor=color,
        edgecolor="white",
        linewidth=1.2,
        alpha=0.9,
    )
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, fontweight="bold", color="white")  # noqa: E501


def plot_threat_taxonomy(output_dir: str = "output/figures") -> Figure:
    """Create the 4-category attack taxonomy tree (Fig 5).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=12, height=6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Root node
    root_x, root_y = 0.50, 0.90
    _draw_node(ax, root_x, root_y, "Attack Taxonomy\n(950 total)", "#333333", fontsize=10, width=0.18, height=0.08)  # noqa: E501

    categories = list(_TAXONOMY.keys())
    cat_colors = [PALETTE[0], PALETTE[1], PALETTE[3], PALETTE[4]]
    n_cats = len(categories)
    cat_xs = [0.125 + i * 0.25 for i in range(n_cats)]
    cat_y = 0.65

    for i, (cat_name, subs) in enumerate(_TAXONOMY.items()):
        cx = cat_xs[i]
        color = cat_colors[i]

        # Arrow from root to category
        ax.annotate(
            "", xy=(cx, cat_y + 0.04), xytext=(root_x, root_y - 0.04),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8),
        )
        _draw_node(ax, cx, cat_y, cat_name, color, fontsize=FONTSIZE["base"], width=0.18, height=0.08)  # noqa: E501

        # Subcategories
        sub_y_start = 0.42
        for j, sub_name in enumerate(subs):
            sy = sub_y_start - j * 0.12
            ax.annotate(
                "", xy=(cx, sy + 0.025), xytext=(cx, cat_y - 0.04),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, alpha=0.6),
            )
            _draw_node(ax, cx, sy, sub_name, color, fontsize=7, width=0.18, height=0.05)

    ax.set_title("Attack Taxonomy: 4 Categories, 12 Subcategories, 950 Attacks", fontsize=13, pad=10)  # noqa: E501
    fig.tight_layout()
    save_figure(fig, "fig05_threat_taxonomy", output_dir=output_dir)
    return fig
