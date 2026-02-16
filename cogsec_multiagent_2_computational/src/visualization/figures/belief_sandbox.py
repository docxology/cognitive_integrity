"""Fig 11: Sandbox state machine diagram.

Illustrates the belief sandboxing lifecycle: Incoming -> Provisional ->
Verified (promoted) or Discarded (expired).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, create_figure, save_figure


def _draw_state(ax, x, y, label, color, radius=0.08):
    """Draw a state circle with label."""
    circle = plt.Circle(
        (x, y), radius,
        fc=color, ec="white", lw=2.5, zorder=5,
    )
    ax.add_patch(circle)
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=FONTSIZE["base"], fontweight="bold",
        color="white", zorder=6,
    )


def _arrow(ax, x0, y0, x1, y1, label="", color="#555", curved=False):
    """Draw a labeled transition arrow."""
    style = "arc3,rad=0.15" if curved else "arc3,rad=0"
    ax.annotate(
        "",
        xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=2,
            connectionstyle=style,
        ),
    )
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        offset = 0.04 if not curved else 0.08
        ax.text(
            mx, my + offset, label,
            ha="center", va="bottom",
            fontsize=FONTSIZE["small"], style="italic",
            color=color,
        )


def plot_belief_sandbox(output_dir: str = "output/figures") -> Figure:
    """Create the sandbox state machine diagram (Fig 11).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=9, height=5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_aspect("equal")

    # States
    states = {
        "Incoming": (0.12, 0.50, COLORS["neutral"]),
        "Provisional": (0.40, 0.50, COLORS["warning"]),
        "Verified": (0.75, 0.75, COLORS["secondary"]),
        "Discarded": (0.75, 0.25, COLORS["accent"]),
    }

    for name, (x, y, color) in states.items():
        _draw_state(ax, x, y, name, color)

    # Transitions
    _arrow(ax, 0.20, 0.50, 0.32, 0.50, "classify", COLORS["primary"])
    _arrow(ax, 0.48, 0.54, 0.67, 0.72, "promote\n(verified)", COLORS["secondary"], curved=True)
    _arrow(ax, 0.48, 0.46, 0.67, 0.28, "expire\n(TTL)", COLORS["accent"], curved=True)

    # Self-loop on provisional (belief updated)
    ax.annotate(
        "",
        xy=(0.40, 0.58),
        xytext=(0.34, 0.58),
        arrowprops=dict(
            arrowstyle="-|>",
            color=COLORS["warning"],
            lw=1.5,
            connectionstyle="arc3,rad=-0.8",
        ),
    )
    ax.text(0.37, 0.66, "update", ha="center", fontsize=FONTSIZE["small"], style="italic", color=COLORS["warning"])

    # Entry arrow
    ax.annotate(
        "",
        xy=(0.04, 0.50),
        xytext=(0.0, 0.50),
        arrowprops=dict(arrowstyle="-|>", color="#333", lw=2),
    )
    ax.text(0.0, 0.55, "Input", ha="center", fontsize=FONTSIZE["small"], color="#333")

    ax.set_title("Belief Sandbox State Machine", fontsize=14, pad=12)
    fig.tight_layout()
    save_figure(fig, "fig11_belief_sandbox", output_dir=output_dir)
    return fig
