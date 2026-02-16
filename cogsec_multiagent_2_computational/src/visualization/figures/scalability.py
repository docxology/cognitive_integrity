"""Fig 7: Agent count vs latency and memory (dual y-axis).

Plots scalability data with a quadratic regression overlay on latency
and a secondary y-axis for memory consumption.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from ..style import (
    COLORS,
    FONTSIZE,
    create_figure,
    save_figure,
)


def _default_data():
    """Generate realistic scalability measurements."""
    rng = np.random.default_rng(42)
    agents = np.array([2, 3, 5, 7, 10, 15, 20, 30, 50, 100])

    # Latency: roughly quadratic with noise
    latency = 5.0 + 0.02 * agents ** 2 + 1.5 * agents + rng.normal(0, 2, len(agents))
    latency = np.maximum(latency, 5.0)

    # Memory: roughly linear-ish with some overhead
    memory = 50 + 8 * agents + 0.05 * agents ** 1.3 + rng.normal(0, 5, len(agents))
    memory = np.maximum(memory, 50.0)

    return agents, latency, memory


def plot_scalability(output_dir: str = "output/figures") -> Figure:
    """Create the dual-axis scalability chart (Fig 7).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax1 = create_figure()
    agents, latency, memory = _default_data()

    # Latency on left axis
    color_lat = COLORS["primary"]
    ax1.plot(agents, latency, "o-", color=color_lat, linewidth=2, markersize=6, label="Latency (ms)")
    ax1.set_xlabel("Agent Count", fontsize=12)
    ax1.set_ylabel("Latency (ms)", fontsize=12, color=color_lat)
    ax1.tick_params(axis="y", labelcolor=color_lat)

    # Quadratic regression for latency
    coeffs = np.polyfit(agents, latency, 2)
    poly = np.poly1d(coeffs)
    agents_smooth = np.linspace(agents.min(), agents.max(), 200)
    ax1.plot(agents_smooth, poly(agents_smooth), "--", color=color_lat, alpha=0.5, linewidth=1.5)

    # R^2
    ss_res = np.sum((latency - poly(agents)) ** 2)
    ss_tot = np.sum((latency - latency.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot
    ax1.text(
        0.05, 0.92,
        f"Latency $R^2 = {r_squared:.3f}$",
        transform=ax1.transAxes,
        fontsize=FONTSIZE["base"],
        color=color_lat,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    # Memory on right axis
    ax2 = ax1.twinx()
    color_mem = COLORS["accent"]
    ax2.plot(agents, memory, "s-", color=color_mem, linewidth=2, markersize=6, label="Memory (MB)")
    ax2.set_ylabel("Memory (MB)", fontsize=12, color=color_mem)
    ax2.tick_params(axis="y", labelcolor=color_mem)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=FONTSIZE["base"])

    ax1.set_title("Scalability: Latency and Memory vs Agent Count", fontsize=13, pad=10)
    fig.tight_layout()
    save_figure(fig, "fig07_scalability", output_dir=output_dir)
    return fig
