"""Fig 17: Delegation chain visualization.

Shows a delegation chain A -> B -> C -> D with trust values on edges
and a bar chart below demonstrating trust never amplifies.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, format_axis, save_figure


def plot_trust_calculus(output_dir: str = "output/figures") -> Figure:
    """Create the delegation chain visualization (Fig 17).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    from typing import cast as _cast

    import numpy as _np
    fig, _axes = create_figure(width=9, height=6, n_rows=2, n_cols=1)
    _axes_arr = _cast("_np.ndarray[tuple[int], _np.dtype[_np.object_]]", _axes)
    ax_chain: Axes = _axes_arr[0]
    ax_bar: Axes = _axes_arr[1]

    agents = ["Agent A", "Agent B", "Agent C", "Agent D"]
    edge_trust = [0.90, 0.85, 0.80]
    cumulative = [1.0]
    for t in edge_trust:
        cumulative.append(cumulative[-1] * t)

    # --- Top panel: chain diagram ---
    ax_chain.set_xlim(-0.1, 1.1)
    ax_chain.set_ylim(0.2, 0.8)
    ax_chain.axis("off")

    n = len(agents)
    xs = np.linspace(0.1, 0.9, n)
    y = 0.5

    for i, (agent, x) in enumerate(zip(agents, xs)):
        circle = plt.Circle((x, y), 0.06, fc=PALETTE[i], ec="white", lw=2, zorder=5)
        ax_chain.add_patch(circle)
        ax_chain.text(x, y, agent.split()[-1], ha="center", va="center", fontsize=10, fontweight="bold", color="white", zorder=6)  # noqa: E501
        ax_chain.text(x, y - 0.12, agent, ha="center", va="top", fontsize=FONTSIZE["small"], color="#333")  # noqa: E501

    for i in range(n - 1):
        x0, x1 = xs[i] + 0.06, xs[i + 1] - 0.06
        ax_chain.annotate(
            "",
            xy=(x1, y), xytext=(x0, y),
            arrowprops=dict(arrowstyle="-|>", color=COLORS["primary"], lw=2.5),
        )
        ax_chain.text(
            (xs[i] + xs[i + 1]) / 2, y + 0.08,
            f"t={edge_trust[i]:.2f}",
            ha="center", fontsize=FONTSIZE["base"], fontweight="bold", color=COLORS["primary"],
        )

    ax_chain.set_title("(a) Delegation Chain with Trust Values", fontsize=12, pad=8)

    # --- Bottom panel: cumulative trust bars ---
    x_pos = np.arange(n)
    colors = [PALETTE[i] for i in range(n)]
    ax_bar.bar(x_pos, cumulative, color=colors, edgecolor="white", width=0.5)

    for i, (xp, val) in enumerate(zip(x_pos, cumulative)):
        ax_bar.text(float(xp), val + 0.02, f"{val:.3f}", ha="center", fontsize=FONTSIZE["base"], fontweight="bold")  # noqa: E501

    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels([f"Hop {i}" for i in range(n)], fontsize=FONTSIZE["base"])
    format_axis(ax_bar, xlabel="Delegation Hop", ylabel="Cumulative Trust", title="(b) Cumulative Trust (Never Amplifies)")  # noqa: E501
    ax_bar.set_ylim(0, 1.15)

    # Decay annotation
    ax_bar.annotate(
        "Trust monotonically\ndecreases with depth",
        xy=(2.5, cumulative[-1] + 0.05),
        xytext=(3.2, 0.80),
        fontsize=FONTSIZE["base"],
        arrowprops=dict(arrowstyle="->", color=COLORS["neutral"]),
        color=COLORS["neutral"],
        ha="center",
    )

    fig.tight_layout()
    save_figure(fig, "fig17_trust_calculus", output_dir=output_dir)
    return fig
