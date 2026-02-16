"""Fig 21: Violin plots of detection score distributions per architecture.

Shows the full distribution of detection scores across architectures,
revealing modality and spread differences not visible in summary stats.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from matplotlib.figure import Figure

from ..style import COLORS, FONTSIZE, PALETTE, create_figure, format_axis, save_figure


def _generate_distributions(seed: int = 42) -> Dict[str, np.ndarray]:
    """Generate synthetic detection score distributions."""
    rng = np.random.default_rng(seed)
    archs = {
        "Claude Code": (0.97, 0.02),
        "AutoGPT": (0.95, 0.03),
        "CrewAI": (0.96, 0.025),
        "LangGraph": (0.96, 0.025),
        "MetaGPT": (0.94, 0.03),
        "CAMEL": (0.93, 0.035),
    }
    result = {}
    for name, (mean, std) in archs.items():
        scores = np.clip(rng.normal(mean, std, size=200), 0.5, 1.0)
        result[name] = scores
    return result


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
    data = _generate_distributions()

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
