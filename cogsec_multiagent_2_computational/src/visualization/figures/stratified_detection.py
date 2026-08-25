"""Where detection fails, grouped by what the attack was aiming at.

An aggregate detection rate hides its own distribution. The pipeline detects
87.3% of the corpus, and that single number is compatible with uniform
competence and with a single catastrophic blind spot; only a breakdown tells
which. Grouped by target, the shortfall is concentrated almost entirely in
belief-state attacks, and the same shortfall appears in the adversary-class
view as the Omega-4 stratum, because the two groupings are re-cuts of the same
categories rather than independent axes.

Both panels carry the aggregate as a reference line, so a bar's distance from
it is readable without arithmetic.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..artifact import annotate_provenance, load_artifact
from ..style import FONTSIZE, SEMANTIC_COLORS, create_figure, save_figure

_TARGET_LABEL = {
    "belief_state": "Belief\nstate",
    "action_execution": "Action\nexecution",
    "trust_relationships": "Trust\nrelationships",
    "temporal_state": "Temporal\nstate",
    "goal_alignment": "Goal\nalignment",
}

_OMEGA_LABEL = {
    "1": r"$\Omega_1$" + "\npassive",
    "2": r"$\Omega_2$" + "\ninjection",
    "3": r"$\Omega_3$" + "\nimpersonation",
    "4": r"$\Omega_4$" + "\nbelief",
    "5": r"$\Omega_5$" + "\ncoordinated",
}

#: Bars at or below this are drawn in the alert colour. Chosen as the point
#: where a defense stops being a defense: it misses more than one attack in
#: four.
_ALERT_BELOW = 0.75


def _panel(axis, bucket: dict, labels: dict, title: str, overall: float) -> None:
    keys = sorted(bucket, key=lambda k: -bucket[k]["n"])
    rates = [bucket[k]["tpr"] for k in keys]
    counts = [bucket[k]["n"] for k in keys]
    colors = [
        SEMANTIC_COLORS["attack"] if r <= _ALERT_BELOW else SEMANTIC_COLORS["firewall"]
        for r in rates
    ]

    x = np.arange(len(keys))
    axis.bar(x, rates, color=colors, edgecolor="black", width=0.65)
    axis.axhline(
        overall, color="#2C3E50", linestyle="--", linewidth=1.2,
        label=f"whole corpus ({overall:.3f})",
    )
    axis.set_xticks(x)
    axis.set_xticklabels(
        [labels.get(k, k.replace("_", "\n")) for k in keys], fontsize=FONTSIZE["small"]
    )
    axis.set_ylim(0, 1.15)
    axis.set_ylabel("Detected", fontsize=FONTSIZE["base"])
    axis.set_title(title, fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    axis.grid(True, alpha=0.3, axis="y")
    axis.set_axisbelow(True)
    axis.legend(loc="lower right", fontsize=FONTSIZE["small"], frameon=False)

    # n beside every bar: a rate without its denominator invites a reader to
    # weight a 30-sample stratum like a 675-sample one.
    for i, (rate, n) in enumerate(zip(rates, counts)):
        axis.text(i, rate + 0.03, f"{rate:.3f}", ha="center", fontsize=FONTSIZE["small"])
        axis.text(i, 0.03, f"n={n:,}", ha="center", fontsize=FONTSIZE["small"] - 1,
                  color="white", fontweight="bold")


def plot_stratified_detection(output_dir: str | Path = "output/figures") -> Figure:
    """Detection by attack target and by adversary class, side by side."""
    payload = load_artifact(
        "stratified_detection", required=("by_target", "by_omega_level", "corpus_size")
    )
    by_target = payload["by_target"]
    overall = sum(r["detected"] for r in by_target.values()) / sum(
        r["n"] for r in by_target.values()
    )

    fig, axes = create_figure(width=11, height=4.6, n_rows=1, n_cols=2)
    _panel(axes[0], by_target, _TARGET_LABEL, "A. By what the attack targets", overall)
    _panel(axes[1], payload["by_omega_level"], _OMEGA_LABEL, "B. By adversary class", overall)

    fig.suptitle(
        "Detection is not uniform: the shortfall is one stratum",
        fontsize=FONTSIZE["base"] + 3, fontweight="bold", y=0.99,
    )
    # Both groupings are category-determined, so they are re-cuts of one
    # breakdown rather than two experiments. Saying so on the figure keeps a
    # reader from treating the agreement between the panels as corroboration.
    fig.text(
        0.5, 0.925,
        "Both groupings are assigned per attack category, so the panels are two cuts "
        "of one breakdown rather than independent measurements.",
        ha="center", fontsize=FONTSIZE["small"], style="italic", color="#5A6472",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.90))
    annotate_provenance(fig, payload, "stratified_detection.json")
    save_figure(fig, "stratified_detection", output_dir=output_dir)
    return fig
