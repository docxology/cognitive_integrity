"""Ablation Study module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

matplotlib.use("Agg")
logger = __import__('logging').getLogger(__name__)



def _load_ablation_data(output_dir: Path) -> tuple:
    """Load ablation results from ablation_results.json."""
    data_path = output_dir.parent / "data" / "ablation_results.json"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "ablation_results.json"  # noqa: E501
    with open(data_path, "r") as f:
        data = json.load(f)

    if "component_removal" in data:
        removal_list = data["component_removal"]
        # Read the declared full-pipeline rate rather than reconstructing it.
        # Reconstructing it as ``tpr + delta_tpr`` had the sign backwards --
        # delta_tpr is the loss from removing a module, so adding it subtracts
        # the loss twice and put the "Full CIF" bar at 0.020 where the artifact
        # says 0.122. A missing key is now loud: generate_all_figures collects
        # generator exceptions and exits 1, which is what should happen when the
        # evidence a figure draws is absent.
        full_tpr = float(data["full_pipeline"]["tpr"])

        components = ["Full CIF"]
        detection = [full_tpr]
        delta = [0.0]

        for entry in removal_list:
            label = f"− {entry['removed'].replace('_', ' ').title()}"
            components.append(label)
            detection.append(entry["tpr"])
            delta.append(-abs(entry["delta_tpr"]))
    else:
        keys = [k for k in data.keys() if k != "metadata"]
        components = []
        detection = []
        delta = []
        for k in keys:
            label = "Full CIF" if k == "full_cif" else f"− {k.replace('minus_', '').replace('_', ' ').title()}"  # noqa: E501
            components.append(label)
            detection.append(data[k]["detection"])
            delta.append(data[k]["delta"])

    logger.info("Loaded ablation data from %s", data_path)
    return components, detection, delta


def plot_ablation_study(output_dir: str | Path = "output/figures") -> Figure:
    """Generate ablation study figure from real ablation results.

    Parameters
    ----------
    output_dir : str | Path
        Directory where figures are saved.

    Returns
    -------
    Figure
        The created matplotlib figure.
    """
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    apply_style()
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    components, detection, delta = _load_ablation_data(output_dir)

    # Colorblind-friendly colors based on impact magnitude
    colors = []
    for d in delta:
        if d == 0:
            colors.append(SEMANTIC_COLORS["firewall"])
        elif d <= -0.10:
            colors.append(SEMANTIC_COLORS["tripwire"])
        elif d <= -0.07:
            colors.append(SEMANTIC_COLORS["full_cif"])
        elif d <= -0.04:
            colors.append(SEMANTIC_COLORS["invariants"])
        else:
            colors.append(SEMANTIC_COLORS["sandbox"])

    y_pos = np.arange(len(components))
    ax.barh(y_pos, detection, color=colors, edgecolor="black", linewidth=1)

    for i, (det, d) in enumerate(zip(detection, delta)):
        ax.text(det + max(detection) * 0.02, i, f"{det:.3f}", va="center", fontsize=10, fontweight="bold")
        if d != 0:
                # Trailing each bar's own value label rather than sharing a fixed
            # column: a fixed column collides with the legend, and the literal
            # it used before assumed the old 0.70--1.00 window.
            ax.text(det + max(detection) * 0.13, i, f"Δ = {d:+.3f}", va="center", fontsize=10, color="#7F8C8D", style="italic")  # noqa: E501

    ax.set_yticks(y_pos)
    ax.set_yticklabels(components, fontsize=11)
    ax.set_xlabel("Detection Rate", fontsize=12)
    ax.set_title("Ablation Study: Defense Component Contribution", fontsize=14, fontweight="bold", pad=15)  # noqa: E501
    # The axis follows the data. A hardcoded 0.70--1.00 window put every bar
    # outside the canvas -- the figure shipped, and was cited, with no bars at
    # all -- because the measured rates are around 0.12.
    ax.set_xlim(0.0, max(detection) * 1.42)
    ax.axvline(
        x=detection[0],
        color=SEMANTIC_COLORS["firewall"],
        linestyle="--",
        alpha=0.5,
        linewidth=1.5,
        label="Full CIF",
    )
    ax.grid(True, alpha=0.3, axis="x")

    legend_elements = [
        Patch(facecolor=SEMANTIC_COLORS["tripwire"], edgecolor="black", label="Critical (Δ ≤ −0.10)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["full_cif"], edgecolor="black", label="Major (−0.10 < Δ ≤ −0.07)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["invariants"], edgecolor="black", label="Moderate (−0.07 < Δ ≤ −0.04)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["sandbox"], edgecolor="black", label="Minor (Δ > −0.04)"),
    ]
    # Outside the axes: every in-axes corner now carries either a bar, a value
    # label or a delta label, and an overlapping legend hides the data it is
    # meant to explain.
    ax.legend(
        handles=legend_elements,
        # Upper right: the zero-delta rows carry no delta label, so that
        # corner is the only region with no data or annotation in it.
        loc="upper right",
        fontsize=FONTSIZE["base"],
        title="Impact Severity",
        framealpha=0.95,
    )

    add_source_annotation(fig, "src/visualization/figures/ablation_study.py")
    save_figure(fig, "ablation_study", output_dir=output_dir)
    return fig
