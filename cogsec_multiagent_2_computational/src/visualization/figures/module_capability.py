"""Capability against contribution: the distinction an ablation cannot draw.

The ablation table reports a marginal contribution of exactly zero for six of
the eight defense modules, and that number has been read three different ways
over this project's life: as "these mechanisms do not work", as "the corpus
does not exercise them", and finally as what it is. A bar chart of Shapley
values cannot separate the three, because all three produce the same bar.

This figure puts the two measurements side by side so the separation is visible
rather than argued. The left panel is what each module detects on its own; the
right is what it adds to a pipeline that already contains the others. A module
tall on the left and flat on the right is not broken --- it is redundant with
something stronger, and it becomes load-bearing the moment that something is
absent, which is the entire argument for defense in depth and is invisible in
the marginal column alone.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..artifact import annotate_provenance, load_artifact
from ..style import FONTSIZE, SEMANTIC_COLORS, create_figure, save_figure

#: Display names for the registry's module keys.
_LABEL = {
    "firewall": "Firewall",
    "detection": "Detection",
    "tripwire": "Tripwire",
    "trust": "Trust",
    "consensus": "Consensus",
    "provenance": "Provenance",
    "sandbox": "Sandbox",
    "invariants": "Invariants",
}


def plot_module_capability(output_dir: str | Path = "output/figures") -> Figure:
    """Solo detection beside marginal contribution, for all eight modules."""
    capability = load_artifact("module_capability_matrix", required=("detection_rate",))
    lattice = load_artifact("taxonomy_evaluation_results", required=("shapley_overall_tpr",))

    solo = capability["detection_rate"]
    shapley = lattice["shapley_overall_tpr"]
    modules = sorted(solo, key=lambda m: -solo[m]["_overall"])

    fig, axes = create_figure(width=10, height=5, n_rows=1, n_cols=2)
    left, right = axes
    y = np.arange(len(modules))
    labels = [_LABEL.get(m, m.title()) for m in modules]

    solo_rates = [solo[m]["_overall"] for m in modules]
    left.barh(y, solo_rates, color=SEMANTIC_COLORS["firewall"], edgecolor="black", height=0.65)
    left.set_yticks(y)
    left.set_yticklabels(labels, fontsize=FONTSIZE["base"])
    left.invert_yaxis()
    left.set_xlabel("Detected alone (fraction of corpus)", fontsize=FONTSIZE["base"])
    left.set_title("A. Capability", fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    # Both panels share one scale. Two panels at different scales invite a
    # reader to compare bar lengths that are not comparable, which is the
    # confusion this figure exists to remove.
    shared_limit = max(max(solo_rates), max(shapley.get(m, 0.0) for m in modules)) * 1.22
    left.set_xlim(0, shared_limit)
    for i, rate in enumerate(solo_rates):
        left.text(rate + shared_limit * 0.015, i, f"{rate:.3f}",
                  va="center", fontsize=FONTSIZE["small"])

    values = [shapley.get(m, 0.0) for m in modules]
    right.barh(y, values, color=SEMANTIC_COLORS["sandbox"], edgecolor="black", height=0.65)
    right.set_yticks(y)
    right.set_yticklabels([])
    right.invert_yaxis()
    right.set_xlabel("Shapley value over 256 coalitions", fontsize=FONTSIZE["base"])
    right.set_title("B. Marginal contribution", fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    right.set_xlim(0, shared_limit)
    for i, value in enumerate(values):
        right.text(value + shared_limit * 0.015, i, f"{value:.3f}",
                   va="center", fontsize=FONTSIZE["small"])

    for axis in (left, right):
        axis.grid(True, alpha=0.3, axis="x")
        axis.set_axisbelow(True)

    # The reading instruction, on the figure rather than only in the caption:
    # a reader who takes panel B alone away from this page has the wrong idea.
    masked = [
        _LABEL.get(m, m.title())
        for m in modules
        # Detects a real share on its own and still adds little. A module
        # barely detecting anything is not masked, it is weak, and naming it
        # here would blunt the point.
        if solo[m]["_overall"] >= 0.03 and shapley.get(m, 0.0) < 0.02
    ]
    if masked:
        fig.text(
            0.5, 0.945,
            f"Detects on its own, adds little to the whole: {', '.join(masked)}",
            ha="center", fontsize=FONTSIZE["small"], style="italic", color="#5A6472",
        )

    fig.suptitle(
        "What each defense catches, and what it adds",
        fontsize=FONTSIZE["base"] + 3, fontweight="bold", y=0.995,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    annotate_provenance(fig, capability, "module_capability_matrix.json")
    save_figure(fig, "module_capability", output_dir=output_dir)
    return fig
