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

try:
    from ablation.minimal_config import MinimalConfigSearch
except (ImportError, ModuleNotFoundError):
    MinimalConfigSearch = None  # type: ignore[assignment,misc]

def _load_ablation_data(output_dir: Path) -> tuple:
    """Load ablation results from ablation_results.json."""
    data_path = output_dir.parent / "data" / "ablation_results.json"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "ablation_results.json"  # noqa: E501
    with open(data_path, "r") as f:
        data = json.load(f)

    if "component_removal" in data:
        removal_list = data["component_removal"]
        if removal_list:
            full_tpr = removal_list[0]["tpr"] + removal_list[0]["delta_tpr"]
        else:
            full_tpr = 0.965

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
        ax.text(det + 0.005, i, f"{det:.2f}", va="center", fontsize=10, fontweight="bold")
        if d != 0:
            ax.text(0.72, i, f"Δ = {d:+.2f}", va="center", fontsize=10, color="#7F8C8D", style="italic")  # noqa: E501

    ax.set_yticks(y_pos)
    ax.set_yticklabels(components, fontsize=11)
    ax.set_xlabel("Detection Rate", fontsize=12)
    ax.set_title("Ablation Study: Defense Component Contribution", fontsize=14, fontweight="bold", pad=15)  # noqa: E501
    ax.set_xlim(0.70, 1.0)
    ax.axvline(x=0.94, color=SEMANTIC_COLORS["firewall"], linestyle="--", alpha=0.5, linewidth=1.5)
    ax.grid(True, alpha=0.3, axis="x")

    legend_elements = [
        Patch(facecolor=SEMANTIC_COLORS["tripwire"], edgecolor="black", label="Critical (Δ ≤ −0.10)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["full_cif"], edgecolor="black", label="Major (−0.10 < Δ ≤ −0.07)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["invariants"], edgecolor="black", label="Moderate (−0.07 < Δ ≤ −0.04)"),  # noqa: E501
        Patch(facecolor=SEMANTIC_COLORS["sandbox"], edgecolor="black", label="Minor (Δ > −0.04)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=FONTSIZE["base"], title="Impact Severity")  # noqa: E501

    add_source_annotation(fig, "src/visualization/figures/ablation_study.py")
    save_figure(fig, "ablation_study", output_dir=output_dir)
    return fig
