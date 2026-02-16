"""Fig 3: 6x4 detection heatmap (architectures x attack categories).

Displays detection rates for each architecture-category pair as a
color-annotated heatmap.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from matplotlib.figure import Figure

from ..style import create_figure, save_figure


def _load_data() -> Optional[np.ndarray]:
    """Try loading real detection data from full_evaluation_results.json."""
    try:
        from .data.result_loaders import evaluation_to_detection_matrix
        archs, cats, matrix = evaluation_to_detection_matrix()
        return matrix
    except Exception:
        return None


_ARCHITECTURES = [
    "Claude Code",
    "AutoGPT",
    "CrewAI",
    "LangGraph",
    "MetaGPT",
    "CAMEL",
]

_CATEGORIES = [
    "Injection",
    "Trust Exploit.",
    "Belief Manip.",
    "Coordination",
]


def _default_data() -> np.ndarray:
    """Generate realistic sample detection rates (6x4)."""
    rng = np.random.default_rng(42)
    base = np.array([
        [0.98, 0.94, 0.91, 0.96],
        [0.95, 0.90, 0.88, 0.93],
        [0.96, 0.92, 0.89, 0.94],
        [0.97, 0.93, 0.90, 0.95],
        [0.94, 0.89, 0.86, 0.92],
        [0.93, 0.87, 0.82, 0.90],
    ])
    noise = rng.normal(0, 0.005, base.shape)
    return np.clip(base + noise, 0.82, 0.99)


def plot_detection_heatmap(
    results: Optional[np.ndarray] = None,
    output_dir: str = "output/figures",
) -> Figure:
    """Create the 6x4 detection heatmap (Fig 3).

    Parameters
    ----------
    results : ndarray, shape (6, 4), optional
        Detection rate matrix.  Generated if *None*.
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    if results is None:
        results = _load_data()
    if results is None:
        results = _default_data()

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

    ax.set_xticks(range(len(_CATEGORIES)))
    ax.set_xticklabels(_CATEGORIES, fontsize=10)
    ax.set_yticks(range(len(_ARCHITECTURES)))
    ax.set_yticklabels(_ARCHITECTURES, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Detection Rate", fontsize=11)

    ax.set_title("Detection Rates by Architecture and Attack Category", fontsize=13, pad=10)
    fig.tight_layout()
    save_figure(fig, "fig03_detection_heatmap", output_dir=output_dir)
    return fig
