"""What each false-positive mitigation costs, drawn as the trade it is.

A table of paired deltas asks a reader to hold two numbers per row and compare
across rows. The comparison is two-dimensional and belongs on two axes: false
positives against true positives, with the unmitigated pipeline as the origin
of the comparison and Youden's J as the contour a point sits on.

Drawn this way one fact is immediate that the table makes you compute. Two
strategies sit directly above the baseline --- the same detection at none of
the cost --- and the strategy the original table rated second-best sits far to
the lower left, having bought a zero false-positive rate by discarding
two-thirds of the detections.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..artifact import annotate_provenance, load_artifact
from ..style import FONTSIZE, SEMANTIC_COLORS, create_figure, save_figure

_LABEL = {
    "none": "no mitigation",
    "confirmation_cascade": "confirmation cascade",
    "temporal_smoothing": "temporal smoothing",
    "contextual_whitelist": "contextual whitelist",
    "cost_sensitive": "cost-sensitive",
    "combined": "combined",
}

#: Coordinates are rounded to this before points are grouped. Strategies that
#: land on the same operating point get one label between them: two labels at
#: the same coordinate overlap into unreadability, and offsetting them implies
#: a separation the measurement does not have.
_COINCIDENT_TOLERANCE = 3


def plot_mitigation_tradeoff(output_dir: str | Path = "output/figures") -> Figure:
    """Each mitigation as a point in false-positive / true-positive space."""
    payload = load_artifact("fp_mitigation", required=("strategies", "baseline"))
    strategies = payload["strategies"]

    fig, axis = create_figure(width=7.5, height=5.0)

    # Group strategies that share an operating point, so each point carries one
    # label naming everything that lands on it.
    groups: dict[tuple[float, float], list[str]] = {}
    for name, row in strategies.items():
        key = (round(row["fpr"], _COINCIDENT_TOLERANCE), round(row["tpr"], _COINCIDENT_TOLERANCE))
        groups.setdefault(key, []).append(name)

    tprs = [row["tpr"] for row in strategies.values()]
    fprs = [row["fpr"] for row in strategies.values()]
    x_limit = max(0.22, max(fprs) * 1.5)
    y_low, y_high = max(0.0, min(tprs) - 0.12), min(1.02, max(tprs) + 0.14)

    # Iso-J contours: every point on one is the same distance from chance, so
    # strategies can be ranked by eye rather than by subtraction. Labelled at
    # the right edge, clear of the points, which cluster on the left.
    grid = np.linspace(0, x_limit, 200)
    for j in (0.2, 0.4, 0.6, 0.8, 0.9):
        axis.plot(grid, grid + j, color="#D5DBDB", linewidth=0.9, zorder=0)
        edge = x_limit + j
        if y_low < edge < y_high:
            axis.text(x_limit * 0.995, edge, f"J={j:g}", fontsize=FONTSIZE["small"] - 1,
                      color="#95A5A6", va="center", ha="right")

    for (fpr, tpr), names in groups.items():
        is_baseline = "none" in names
        axis.scatter(
            fpr, tpr,
            s=150 if is_baseline else 100,
            marker="s" if is_baseline else "o",
            color=SEMANTIC_COLORS["attack"] if is_baseline else SEMANTIC_COLORS["firewall"],
            edgecolor="black", zorder=4,
        )
        j = strategies[names[0]]["youden_j"]
        label = "\n".join(_LABEL.get(n, n) for n in sorted(names)) + f"\nJ={j:+.3f}"
        # Labels are wider than the points they name, so two points that are
        # merely close still collide. A near neighbour to the left sends this
        # label below its point; everything else sits above.
        crowded = any(
            other != (fpr, tpr)
            and abs(other[0] - fpr) < x_limit * 0.35
            and abs(other[1] - tpr) < 0.08
            and other[0] < fpr
            for other in groups
        )
        near_right = fpr > x_limit * 0.6
        axis.annotate(
            label,
            xy=(fpr, tpr),
            xytext=(12 if not near_right else -10, -34 if crowded else 10),
            textcoords="offset points",
            ha="right" if near_right else "left",
            fontsize=FONTSIZE["small"],
        )

    axis.set_xlabel("False-positive rate", fontsize=FONTSIZE["base"])
    axis.set_ylabel("True-positive rate", fontsize=FONTSIZE["base"])
    axis.set_xlim(-x_limit * 0.06, x_limit)
    axis.set_ylim(y_low, y_high)
    axis.grid(True, alpha=0.3)
    axis.set_axisbelow(True)
    axis.set_title(
        "Two mitigations are free; one is not",
        fontsize=FONTSIZE["base"] + 2, fontweight="bold",
    )

    not_implemented = payload.get("not_implemented") or {}
    if not_implemented:
        fig.text(
            0.5, 0.028,
            "Not plotted: " + ", ".join(sorted(not_implemented))
            + " — no model in this framework updates on feedback.",
            ha="center", fontsize=FONTSIZE["small"], style="italic", color="#5A6472",
        )

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    annotate_provenance(fig, payload, "fp_mitigation.json")
    save_figure(fig, "mitigation_tradeoff", output_dir=output_dir)
    return fig
