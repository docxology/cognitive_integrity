"""Fig 21: Violin plots of detection score distributions per architecture.

Shows the full distribution of detection scores across architectures,
revealing modality and spread differences not visible in summary stats.
Reads data from full_evaluation_results.json.
"""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, format_axis, save_figure

logger = logging.getLogger(__name__)


def _load_distributions() -> Dict[str, np.ndarray]:
    """Load per-architecture detection scores from full_evaluation_results.json."""
    from data.result_loaders import load_full_evaluation
    rows = load_full_evaluation()
    arch_scores: Dict[str, list] = {}
    for r in rows:
        arch_scores.setdefault(r.architecture, []).append(r.detection_rate)
    logger.info("Loaded detection distributions for %d architectures", len(arch_scores))
    return {k: np.array(v) for k, v in arch_scores.items()}


def plot_detection_distributions(output_dir: str = "output/figures") -> Figure:
    """Create violin plots of detection scores per architecture (Fig 21).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=9, height=5)
    data = _load_distributions()

    names = list(data.keys())
    values = [data[n] for n in names]
    positions = list(range(len(names)))

    parts = ax.violinplot(values, positions=positions, showmeans=True,
                          showmedians=True, showextrema=False)

    # Color the violins
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(PALETTE[i % len(PALETTE)])
        pc.set_edgecolor("black")
        pc.set_alpha(0.7)

    if "cmeans" in parts:
        parts["cmeans"].set_color("black")
        parts["cmeans"].set_linewidth(1.5)
    if "cmedians" in parts:
        parts["cmedians"].set_color(COLORS["accent"])
        parts["cmedians"].set_linewidth(1.5)

    # Add individual points (jittered)
    rng = np.random.default_rng(99)
    for i, vals in enumerate(values):
        jitter = rng.uniform(-0.15, 0.15, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals,
                   alpha=0.1, s=5, color=PALETTE[i % len(PALETTE)], zorder=1)

    ax.set_xticks(positions)
    ax.set_xticklabels(names, fontsize=FONTSIZE["base"], rotation=15, ha="right")
    format_axis(ax, xlabel="Architecture", ylabel="Detection Score",
                title="Detection Score Distributions by Architecture")
    ax.set_ylim(0.5, 1.05)

    fig.tight_layout()
    save_figure(fig, "fig21_detection_distributions", output_dir=output_dir)
    return fig
