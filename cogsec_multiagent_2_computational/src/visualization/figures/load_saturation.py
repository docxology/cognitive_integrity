"""Where the pipeline stops keeping up, and what it costs to get there.

A throughput ceiling is a claim about a system under load, and the only honest
way to establish one is to ask for more than the system can give and watch it
fail. This drives the pipeline at rising target rates and plots achieved
against target: while the two track, the system is keeping up; where they
separate, it is not, and that separation is the ceiling.

The identity line is what makes the panel readable. A bar chart of achieved
rates rises monotonically and looks like success at every rate; the same data
against ``y = x`` shows the exact point where the curve leaves the line.

Detection is drawn on the same panel because its constancy is a result. Nothing
in the pipeline carries state between messages, so arrival rate cannot change a
verdict, and a flat line here is the visible form of that argument.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from ..artifact import annotate_provenance, load_artifact
from ..style import FONTSIZE, SEMANTIC_COLORS, create_figure, save_figure


def plot_load_saturation(output_dir: str | Path = "output/figures") -> Figure:
    """Achieved versus target rate, with CPU and detection alongside."""
    payload = load_artifact("load_sweep", required=("points", "saturation_msg_per_s"))
    points = sorted(payload["points"], key=lambda p: p["target_msg_per_s"])
    targets = [p["target_msg_per_s"] for p in points]
    achieved = [p["achieved_msg_per_s"] for p in points]
    saturation = payload["saturation_msg_per_s"]

    fig, axes = create_figure(width=11, height=4.4, n_rows=1, n_cols=2)
    rate_axis, cost_axis = axes

    limit = max(targets) * 1.08
    rate_axis.plot([0, limit], [0, limit], "--", color="#95A5A6", linewidth=1.2,
                   label="keeping up (y = x)")
    colors = [
        SEMANTIC_COLORS["firewall"] if p["keeping_up"] else SEMANTIC_COLORS["attack"]
        for p in points
    ]
    rate_axis.plot(targets, achieved, "-", color="#2C3E50", linewidth=1.2, zorder=2)
    rate_axis.scatter(targets, achieved, c=colors, s=70, edgecolor="black", zorder=3)
    if saturation:
        rate_axis.axvline(saturation, color=SEMANTIC_COLORS["attack"],
                          linestyle=":", linewidth=1.4)
        rate_axis.text(
            saturation * 1.03, limit * 0.12,
            f"keeps up to\n{saturation:,.0f} msg/s",
            fontsize=FONTSIZE["small"], color=SEMANTIC_COLORS["attack"],
        )
    rate_axis.set_xlabel("Target rate (messages/s)", fontsize=FONTSIZE["base"])
    rate_axis.set_ylabel("Achieved rate (messages/s)", fontsize=FONTSIZE["base"])
    rate_axis.set_title("A. Where it stops keeping up",
                        fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    rate_axis.set_xlim(0, limit)
    rate_axis.set_ylim(0, limit)
    rate_axis.grid(True, alpha=0.3)
    rate_axis.set_axisbelow(True)
    rate_axis.legend(loc="upper left", fontsize=FONTSIZE["small"], frameon=False)

    cost_axis.plot(targets, [p["cpu_utilisation"] for p in points], "-o",
                   color=SEMANTIC_COLORS["sandbox"], markersize=4,
                   label="CPU s per wall s")
    cost_axis.plot(targets, [p["detection_rate"] for p in points], "-s",
                   color=SEMANTIC_COLORS["firewall"], markersize=4,
                   label="detection rate")
    cost_axis.set_xscale("log")
    cost_axis.set_xlabel("Target rate (messages/s, log scale)", fontsize=FONTSIZE["base"])
    cost_axis.set_ylabel("Fraction", fontsize=FONTSIZE["base"])
    cost_axis.set_title("B. What it costs, and what it does not change",
                        fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    cost_axis.set_ylim(0, 1.15)
    cost_axis.grid(True, alpha=0.3)
    cost_axis.set_axisbelow(True)
    cost_axis.legend(loc="center left", fontsize=FONTSIZE["small"], frameon=False)

    fig.suptitle(
        "Throughput has a ceiling; detection does not move",
        fontsize=FONTSIZE["base"] + 3, fontweight="bold", y=0.99,
    )
    fig.text(
        0.5, 0.925,
        f"{payload['concurrency']}. CPU is process CPU-seconds per wall-second, "
        f"not a percentage: a percentage needs a sampling interval and a core count.",
        ha="center", fontsize=FONTSIZE["small"], style="italic", color="#5A6472",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.90))
    annotate_provenance(fig, payload, "load_sweep.json")
    save_figure(fig, "load_saturation", output_dir=output_dir)
    return fig
