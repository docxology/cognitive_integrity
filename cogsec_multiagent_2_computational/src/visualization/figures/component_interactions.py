"""Fig 22: 8x8 component interaction/synergy heatmap.

Diverging heatmap showing pairwise synergy scores between all 8 CIF
components.  Positive = synergistic, negative = antagonistic.
Reads data from ablation_results.json.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, apply_style, save_figure

logger = __import__('logging').getLogger(__name__)

_COMPONENTS = [
    "Firewall", "Detection", "Tripwire", "Trust",
    "Consensus", "Provenance", "Sandbox", "Invariants",
]


def _load_synergy_data() -> np.ndarray:
    """Load synergy data from ablation_results.json."""
    from data.result_loaders import load_ablation_results
    data = load_ablation_results()
    matrix = np.zeros((8, 8))
    name_map = {c.lower(): i for i, c in enumerate(_COMPONENTS)}
    name_map["trust_calculus"] = 3  # alias

    if "top_synergies" in data:
        for s in data["top_synergies"]:
            a_idx = name_map.get(s["a"], -1)
            b_idx = name_map.get(s["b"], -1)
            if a_idx >= 0 and b_idx >= 0:
                matrix[a_idx, b_idx] = s["synergy"]
                matrix[b_idx, a_idx] = s["synergy"]

    logger.info("Loaded synergy data from ablation_results.json")
    return matrix


def plot_component_interactions(output_dir: str = "output/figures") -> Figure:
    """Create the 8x8 synergy heatmap (Fig 22).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(COLORS["background"])

    matrix = _load_synergy_data()

    # Diverging colormap centered at 0
    vmax = max(abs(matrix.min()), abs(matrix.max()), 0.05)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = ax.imshow(matrix, cmap="RdBu_r", norm=norm, aspect="equal")

    # Annotate cells
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if i == j:
                text = "-"
            else:
                text = f"{val:+.3f}"
            color = "black" if abs(val) < vmax * 0.5 else "white"
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5, color=color)

    ax.set_xticks(range(len(_COMPONENTS)))
    ax.set_xticklabels(_COMPONENTS, fontsize=FONTSIZE["small"], rotation=45, ha="right")
    ax.set_yticks(range(len(_COMPONENTS)))
    ax.set_yticklabels(_COMPONENTS, fontsize=FONTSIZE["small"])

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Synergy Score", fontsize=10)

    ax.set_title("Component Pairwise Synergy/Antagonism", fontsize=13, pad=10)
    fig.tight_layout()
    save_figure(fig, "fig22_component_interactions", output_dir=output_dir)
    return fig
