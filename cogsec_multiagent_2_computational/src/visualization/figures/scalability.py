"""Fig 7: Agent count vs latency and memory (dual y-axis).

Plots scalability data with a quadratic regression overlay on latency
and a secondary y-axis for memory consumption.
Reads data from scalability_data.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..style import (
    COLORS,
    FONTSIZE,
    create_figure,
    save_figure,
)

logger = __import__('logging').getLogger(__name__)


def _load_data():
    """Load scalability data from scalability_data.json."""
    data_path = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "scalability_data.json"  # noqa: E501
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    agents = np.array(data["agent_counts"])
    latency = np.array(data["latency_ms"])
    memory = np.array(data["memory_mb"])
    logger.info("Loaded scalability data: %d agent counts", len(agents))
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
    agents, latency, memory = _load_data()

    # Latency on left axis
    color_lat = COLORS["primary"]
    ax1.plot(agents, latency, "o-", color=color_lat, linewidth=2, markersize=6, label="Latency (ms)")  # noqa: E501
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
