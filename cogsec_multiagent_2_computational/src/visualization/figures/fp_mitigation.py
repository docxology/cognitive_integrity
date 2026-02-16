"""Fig 14: False positive reduction waterfall chart.

Shows how each defense layer incrementally reduces the false positive
rate from a baseline to the full CIF level.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, format_axis, save_figure


def _default_waterfall_data():
    """Generate FP reduction waterfall data."""
    labels = [
        "Baseline",
        "+ Firewall",
        "+ Trust Calc",
        "+ Consensus",
        "+ Drift Det.",
        "+ Invariants",
        "+ Provenance",
        "+ Sandbox",
        "Full CIF",
    ]
    fp_rates = [0.150, 0.095, 0.070, 0.052, 0.040, 0.032, 0.026, 0.022, 0.018]
    return labels, np.array(fp_rates)


def plot_fp_mitigation(output_dir: str = "output/figures") -> Figure:
    """Create the false positive reduction waterfall chart (Fig 14).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=9, height=5)
    labels, fp_rates = _default_waterfall_data()

    n = len(labels)
    x = np.arange(n)

    # Waterfall bars: each bar starts at current rate and drops to previous
    colors = []
    bottoms = []
    heights = []

    for i in range(n):
        if i == 0:
            # Baseline: full bar from 0
            bottoms.append(0)
            heights.append(fp_rates[i])
            colors.append(COLORS["neutral"])
        elif i == n - 1:
            # Final: full bar from 0
            bottoms.append(0)
            heights.append(fp_rates[i])
            colors.append(COLORS["secondary"])
        else:
            # Incremental reduction
            bottoms.append(fp_rates[i])
            heights.append(fp_rates[i - 1] - fp_rates[i])
            colors.append(PALETTE[i % len(PALETTE)])

    bars = ax.bar(x, heights, bottom=bottoms, color=colors, edgecolor="white", linewidth=1.0, width=0.6)

    # Connection lines between waterfall steps
    for i in range(n - 2):
        ax.plot(
            [x[i] + 0.3, x[i + 1] - 0.3],
            [fp_rates[i], fp_rates[i]],
            color="#999", linewidth=0.8, linestyle="--",
        )

    # Annotate reduction amounts
    for i in range(1, n - 1):
        reduction = fp_rates[i - 1] - fp_rates[i]
        ax.text(
            x[i], fp_rates[i - 1] + 0.003,
            f"-{reduction:.1%}",
            ha="center", va="bottom",
            fontsize=7, color=colors[i], fontweight="bold",
        )

    # Annotate final value
    ax.text(x[-1], fp_rates[-1] + 0.003, f"{fp_rates[-1]:.1%}", ha="center", va="bottom", fontsize=FONTSIZE["small"], fontweight="bold", color=COLORS["secondary"])
    ax.text(x[0], fp_rates[0] + 0.003, f"{fp_rates[0]:.1%}", ha="center", va="bottom", fontsize=FONTSIZE["small"], fontweight="bold", color=COLORS["neutral"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONTSIZE["small"], rotation=30, ha="right")
    format_axis(ax, xlabel="", ylabel="False Positive Rate", title="False Positive Reduction: Incremental Defense Layers")
    ax.set_ylim(0, 0.18)

    fig.tight_layout()
    save_figure(fig, "fig14_fp_mitigation", output_dir=output_dir)
    return fig
