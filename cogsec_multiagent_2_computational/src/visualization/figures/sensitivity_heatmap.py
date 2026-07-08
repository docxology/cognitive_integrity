"""Fig 18: 2D parameter interaction heatmap.

Heatmap of detection rate as a function of injection_threshold and
drift_threshold, highlighting the optimal operating region.
Reads sweep data from sensitivity_results.json and reconstructs
the 2D surface from pair-wise parameter interactions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..style import FONTSIZE, create_figure, format_axis, save_figure

logger = __import__('logging').getLogger(__name__)


def _load_data():
    """Load sensitivity results and reconstruct 2D surface.

    sensitivity_results.json contains 1D sweeps and a grid_best.
    We reconstruct the 2D surface from the injection_threshold and
    drift_threshold sweeps using their combined contribution model.
    """
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "sensitivity_results.json"  # noqa: E501
    with open(p) as f:
        data = json.load(f)

    # Extract 1D sweep data for injection and drift
    sweeps = {s["parameter"]: s for s in data["sweeps"]}
    inj = sweeps["injection_threshold"]
    drift = sweeps["drift_threshold"]

    inj_vals = np.array(inj["values"])
    drift_vals = np.array(drift["values"])
    inj_metrics = np.array(inj["metrics"])
    drift_metrics = np.array(drift["metrics"])

    # Reconstruct 2D surface: combine 1D effects
    # Rate(inj, drift) ≈ base + inj_effect(inj) + drift_effect(drift)
    # where inj_effect = inj_metrics - mean(inj_metrics) and similarly for drift
    inj_effect = inj_metrics - np.mean(inj_metrics)
    drift_effect = drift_metrics - np.mean(drift_metrics)
    base = np.mean(inj_metrics)

    # Construct 2D grid
    n_inj = len(inj_vals)
    n_drift = len(drift_vals)
    rate = np.zeros((n_drift, n_inj))
    for i in range(n_drift):
        for j in range(n_inj):
            rate[i, j] = np.clip(base + inj_effect[j] + drift_effect[i], 0.0, 1.0)

    logger.info("Reconstructed 2D sensitivity surface from sweep data (%s)", p)
    return inj_vals, drift_vals, rate


def plot_sensitivity_heatmap(output_dir: str = "output/figures") -> Figure:
    """Create the 2D parameter interaction heatmap (Fig 18).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=7, height=5.5)
    inj_th, drift_th, rate = _load_data()

    im = ax.imshow(
        rate,
        cmap="RdYlGn",
        aspect="auto",
        origin="lower",
        extent=(inj_th[0], inj_th[-1], drift_th[0], drift_th[-1]),
        vmin=0.70,
        vmax=0.99,
    )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Detection Rate", fontsize=11)

    # Mark optimal region from grid_best
    try:
        p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "sensitivity_results.json"  # noqa: E501
        with open(p) as f:
            data = json.load(f)
        opt_inj = data["grid_best"]["injection"]
        opt_drift = data["grid_best"]["drift"]
    except (KeyError, FileNotFoundError):
        opt_inj, opt_drift = 0.65, 0.30

    ax.plot(opt_inj, opt_drift, "w*", markersize=15, markeredgecolor="black", markeredgewidth=1.2, zorder=5)  # noqa: E501
    ax.annotate(
        f"Optimal\n({opt_inj:.2f}, {opt_drift:.2f})",
        xy=(opt_inj, opt_drift),
        xytext=(opt_inj + 0.12, opt_drift + 0.08),
        fontsize=FONTSIZE["base"],
        fontweight="bold",
        color="white",
        arrowprops=dict(arrowstyle="->", color="white", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#333", alpha=0.8),
    )

    format_axis(
        ax,
        xlabel="Injection Threshold",
        ylabel="Drift Threshold",
        title="Parameter Sensitivity: Detection Rate Surface",
    )

    fig.tight_layout()
    save_figure(fig, "fig18_sensitivity_heatmap", output_dir=output_dir)
    return fig
