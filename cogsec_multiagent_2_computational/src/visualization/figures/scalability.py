"""Fig 7: Agent count vs latency and memory (dual y-axis).

Plots scalability data with a quadratic regression overlay on latency
and a secondary y-axis for memory consumption.
Reads the measured timings in scalability_results.json.
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


#: The measured scalability artifact, written by scripts/run_scalability.py.
#: It records real per-round latency samples and peak traced memory on a named
#: platform, with the workload definition beside them.
_SCALABILITY_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "scalability_results.json"
)


def _load_measured_scalability():
    """Agent counts, median latency in ms, and peak memory in MB, measured.

    This read ``scalability_data.json`` until now, which is a
    :class:`~data.generate.DataGenerator` placeholder: an ``agent_counts`` list
    with ``latency_ms`` and ``memory_mb`` arrays generated from a closed-form
    model with noise, no ``data_origin``, and no script that produces it. A
    real measurement of the same quantities has been sitting beside it in
    ``scalability_results.json`` -- fifteen timed rounds per agent count, peak
    traced bytes, the interpreter and processor recorded -- and nothing read it.

    The median is used rather than the mean because the samples are wall-clock
    timings on a shared machine, where the mean is the statistic a single
    scheduling hiccup moves.

    Fails closed: no placeholder fallback, because falling back to the
    placeholder is precisely the defect.
    """
    if not _SCALABILITY_PATH.is_file():
        raise FileNotFoundError(
            f"{_SCALABILITY_PATH} is missing; run scripts/run_scalability.py. "
            f"There is no stand-in: scalability_data.json is generated, not measured."
        )
    payload = json.loads(_SCALABILITY_PATH.read_text(encoding="utf-8"))
    track = payload.get("framework_track")
    if not track:
        raise ValueError(f"{_SCALABILITY_PATH} records no framework_track")

    rows = sorted(track, key=lambda r: r["n_agents"])
    # Agent counts are counts. The placeholder artifact stored them as
    # floats and the table formats them with "d", so keeping the int
    # dtype here is what lets the row read "20" rather than "20.0".
    agents = np.array([r["n_agents"] for r in rows], dtype=int)
    latency = np.array([r["latency_ms_median"] for r in rows], dtype=float)
    memory = np.array([r["peak_traced_bytes"] / (1024 * 1024) for r in rows], dtype=float)
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
    agents, latency, memory = _load_measured_scalability()

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
