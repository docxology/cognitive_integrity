"""Fig 14: what each false-positive mitigation costs and saves.

This plotted a nine-point waterfall of false-positive rate falling from 0.150
to 0.018 as defense layers were added one at a time, annotated with a measured
reduction at every step. The series was typed, and it was also backwards: the
pipeline combines its modules with a maximum rule, so adding a detector can
only ever raise the flag rate. No sequence of additions reduces false positives,
and no artifact recorded one, because the trace the figure drew cannot exist.

What is measured, and what the figure shows now, is the mitigation study in
``output/data/fp_mitigation.json``: the pipeline's false-positive rate under
each post-filter in ``composition.mitigations``, with the true-positive cost of
each beside it. That is a reduction sequence, it does exist, and two of the
strategies take the rate to zero.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, format_axis, save_figure

#: The measured mitigation study.
_MITIGATION_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "fp_mitigation.json"
)

#: Display names, in the order the figure reads left to right: the baseline
#: first, then the strategies by how much they leave behind.
_STRATEGY_LABEL = {
    "none": "Baseline",
    "temporal_smoothing": "Temporal\nSmoothing",
    "contextual_whitelist": "Contextual\nWhitelist",
    "cost_sensitive": "Cost-\nSensitive",
    "confirmation_cascade": "Confirmation\nCascade",
    "combined": "Combined",
}


def _default_waterfall_data():
    """False-positive rate under each mitigation, measured. Fails closed."""
    if not _MITIGATION_PATH.is_file():
        raise FileNotFoundError(
            f"{_MITIGATION_PATH} is missing; run scripts/run_fp_mitigation.py. "
            f"This figure reports measured false-positive rates and has no "
            f"stand-in series."
        )
    payload = json.loads(_MITIGATION_PATH.read_text(encoding="utf-8"))
    strategies = payload["strategies"]
    ordered = ["none"] + sorted(
        (k for k in strategies if k != "none"),
        key=lambda k: -strategies[k]["fpr"],
    )
    labels = [_STRATEGY_LABEL.get(k, k.replace("_", " ").title()) for k in ordered]
    rates = [strategies[k]["fpr"] for k in ordered]
    costs = [strategies[k]["delta_tpr"] for k in ordered]
    return labels, np.array(rates), np.array(costs)


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
    labels, fp_rates, tpr_cost = _default_waterfall_data()

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

    ax.bar(x, heights, bottom=bottoms, color=colors, edgecolor="white", linewidth=1.0, width=0.6)

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
    ax.text(x[-1], fp_rates[-1] + 0.003, f"{fp_rates[-1]:.1%}", ha="center", va="bottom", fontsize=FONTSIZE["small"], fontweight="bold", color=COLORS["secondary"])  # noqa: E501
    ax.text(x[0], fp_rates[0] + 0.003, f"{fp_rates[0]:.1%}", ha="center", va="bottom", fontsize=FONTSIZE["small"], fontweight="bold", color=COLORS["neutral"])  # noqa: E501

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONTSIZE["small"], rotation=30, ha="right")
    format_axis(ax, xlabel="", ylabel="False Positive Rate", title="False Positive Reduction: Incremental Defense Layers")  # noqa: E501
    ax.set_ylim(0, 0.18)

    fig.tight_layout()
    save_figure(fig, "fig14_fp_mitigation", output_dir=output_dir)
    return fig
