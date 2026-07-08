"""Fig 19: 2x2 confusion-matrix heatmap grid.

Displays confusion matrices for 4 architectures in a 2x2 subplot grid,
each showing TP/FP/TN/FN counts as an annotated heatmap.
Reads data from full_evaluation_results.json.
"""

from __future__ import annotations

from typing import Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, apply_style, save_figure

matplotlib.use("Agg")
logger = __import__('logging').getLogger(__name__)


def _load_data() -> Dict[str, np.ndarray]:
    """Load confusion counts from full_evaluation_results.json."""
    from data.result_loaders import evaluation_to_confusion_counts, load_full_evaluation
    rows = load_full_evaluation()
    counts = evaluation_to_confusion_counts(rows)
    result = {}
    for arch, cats in counts.items():
        tp = fp = tn = fn = 0
        for cat, (t, f, tn_, fn_) in cats.items():
            tp += t
            fp += f
            tn += tn_
            fn += fn_
        result[arch] = np.array([[tp, fp], [fn, tn]])
    logger.info("Loaded confusion matrices for %d architectures", len(result))
    return result


def plot_confusion_matrices(output_dir: str = "output/figures") -> Figure:
    """Create the 2x2 confusion matrix grid (Fig 19).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    apply_style()
    data = _load_data()
    archs = list(data.keys())[:4]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.patch.set_facecolor(COLORS["background"])

    labels = [["TP", "FP"], ["FN", "TN"]]

    for idx, arch in enumerate(archs):
        row, col = divmod(idx, 2)
        ax = axes[row, col]
        cm = data[arch]

        ax.imshow(cm, cmap="Blues", aspect="equal")

        for i in range(2):
            for j in range(2):
                val = cm[i, j]
                color = "white" if val > cm.max() * 0.6 else "black"
                ax.text(j, i, f"{labels[i][j]}\n{val:,}",
                        ha="center", va="center", fontsize=FONTSIZE["base"],
                        fontweight="bold", color=color)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Positive", "Negative"], fontsize=FONTSIZE["small"])
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["Positive", "Negative"], fontsize=FONTSIZE["small"])
        ax.set_xlabel("Predicted", fontsize=FONTSIZE["base"])
        ax.set_ylabel("Actual", fontsize=FONTSIZE["base"])
        ax.set_title(arch, fontsize=11, fontweight="bold")

    fig.suptitle("Confusion Matrices by Architecture", fontsize=14, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(fig, "fig19_confusion_matrices", output_dir=output_dir)
    return fig
