"""Fig 10: Trust graph visualization (no networkx, pure matplotlib).

Places agent nodes in a circular layout and draws trust-weighted edges
between them with color encoding.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..style import FONTSIZE, PALETTE, create_figure, save_figure


def _circular_layout(n: int) -> np.ndarray:
    """Return (n, 2) array of positions on a unit circle."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False) - np.pi / 2
    return np.column_stack([np.cos(angles), np.sin(angles)])


def _trust_matrix(n: int, seed: int = 42) -> np.ndarray:
    """Generate a random trust matrix in [0.3, 1.0]."""
    rng = np.random.default_rng(seed)
    mat = rng.uniform(0.3, 1.0, (n, n))
    np.fill_diagonal(mat, 1.0)
    # Make it somewhat symmetric
    mat = (mat + mat.T) / 2
    return mat


def plot_trust_network(
    n_agents: int = 8,
    output_dir: str = "output/figures",
) -> Figure:
    """Create the trust graph visualization (Fig 10).

    Parameters
    ----------
    n_agents : int
        Number of agents in the network.
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=7, height=7)
    ax.set_aspect("equal")
    ax.axis("off")

    pos = _circular_layout(n_agents) * 0.8
    trust = _trust_matrix(n_agents)

    # Draw edges
    for i in range(n_agents):
        for j in range(i + 1, n_agents):
            t = trust[i, j]
            if t < 0.4:
                continue  # skip very low trust edges
            # Color: green (high) to red (low)
            r = max(0, min(1, 2 * (1 - t)))
            g = max(0, min(1, 2 * t - 0.4))
            color = (r, g, 0.1, 0.3 + 0.5 * t)
            lw = 0.5 + 3.5 * t
            ax.plot(
                [pos[i, 0], pos[j, 0]],
                [pos[i, 1], pos[j, 1]],
                color=color,
                linewidth=lw,
                zorder=1,
            )

    # Draw nodes
    for i in range(n_agents):
        circle = plt.Circle(
            pos[i], 0.08,
            fc=PALETTE[i % len(PALETTE)],
            ec="white",
            lw=2.5,
            zorder=5,
        )
        ax.add_patch(circle)
        ax.text(
            pos[i, 0], pos[i, 1],
            f"A{i}",
            ha="center", va="center",
            fontsize=10, fontweight="bold",
            color="white", zorder=6,
        )

    # Manual color legend
    import matplotlib.patches as mpatches
    high = mpatches.Patch(color=(0.0, 0.8, 0.1, 0.8), label="High trust")
    med = mpatches.Patch(color=(0.6, 0.5, 0.1, 0.6), label="Medium trust")
    low = mpatches.Patch(color=(1.0, 0.1, 0.1, 0.5), label="Low trust")
    ax.legend(handles=[high, med, low], loc="lower right", fontsize=FONTSIZE["base"])

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_title("Agent Trust Network", fontsize=14, pad=12)

    fig.tight_layout()
    save_figure(fig, "fig10_trust_network", output_dir=output_dir)
    return fig
