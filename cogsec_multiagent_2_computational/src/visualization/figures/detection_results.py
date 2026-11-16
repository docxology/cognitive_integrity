"""Fig 3: 4x4 detection heatmap (architectures x attack categories).

Displays detection rates for each architecture-category pair as a
color-annotated heatmap.  Reads data from full_evaluation_results.json.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from matplotlib.figure import Figure

from ..style import create_figure, save_figure

logger = __import__('logging').getLogger(__name__)

_ARCHITECTURES = [
    "Claude Code",
    "AutoGPT",
    "CrewAI",
    "LangGraph",
]

_CATEGORIES = [
    "Injection",
    "Trust Exploit.",
    "Belief Manip.",
    "Coordination",
]

#: Display labels for the actual subcategory keys in the artifact.  Unknown
#: future keys remain visible via a readable transformation rather than being
#: silently assigned another category's heading.
_CATEGORY_LABEL = {
    "direct_injection": "Direct Injection",
    "indirect_injection": "Indirect Injection",
    "impersonation": "Impersonation",
    "belief_drift": "Belief Drift",
    "sybil_attack": "Sybil Attack",
}


def _load_data() -> tuple[list[str], list[str], np.ndarray]:
    """Load matrix dimensions and values from full_evaluation_results.json."""
    from src.data.result_loaders import evaluation_to_detection_matrix

    archs, cats, matrix = evaluation_to_detection_matrix()
    logger.info("Loaded detection matrix from full_evaluation_results.json: %s", matrix.shape)
    return archs, cats, matrix


def plot_detection_heatmap(
    results: Optional[np.ndarray] = None,
    output_dir: str = "output/figures",
) -> Figure:
    """Create the 4x4 detection heatmap (Fig 3).

    Parameters
    ----------
    results : ndarray, shape (4, 4), optional
        Detection rate matrix.  Loaded from output data if *None*.
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    if results is None:
        architectures, category_keys, results = _load_data()
        categories = [
            _CATEGORY_LABEL.get(key, key.replace("_", " ").title())
            for key in category_keys
        ]
    else:
        architectures = _ARCHITECTURES
        categories = _CATEGORIES

    fig, ax = create_figure(width=7, height=5)

    im = ax.imshow(results, cmap="RdYlGn", vmin=0.80, vmax=1.0, aspect="auto")

    # Annotate cells
    for i in range(results.shape[0]):
        for j in range(results.shape[1]):
            val = results[i, j]
            text_color = "white" if val < 0.88 else "black"
            ax.text(
                j, i, f"{val:.1%}",
                ha="center", va="center",
                fontsize=10, fontweight="bold",
                color=text_color,
            )

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_yticks(range(len(architectures)))
    ax.set_yticklabels(architectures, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Detection Rate", fontsize=11)

    ax.set_title("Detection Rates by Architecture and Attack Category", fontsize=13, pad=10)
    fig.tight_layout()
    save_figure(fig, "fig03_detection_heatmap", output_dir=output_dir)
    return fig
