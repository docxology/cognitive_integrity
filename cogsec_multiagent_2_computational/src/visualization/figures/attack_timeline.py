"""Fig 8: Integrity degradation time-series during attacks.

Shows how system integrity degrades under attack and how different
defense configurations respond and recover.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from ..style import (
    COLORS,
    FONTSIZE,
    add_legend,
    create_figure,
    format_axis,
    save_figure,
)


def _generate_timeseries(n_steps: int = 500, attack_step: int = 100, seed: int = 42):
    """Generate three integrity time-series."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps)
    noise = rng.normal(0, 0.01, n_steps)

    # No defense: rapid drop, no recovery
    no_def = np.ones(n_steps) + noise
    decay = np.exp(-0.015 * np.maximum(t - attack_step, 0))
    no_def[attack_step:] = 0.95 * decay[attack_step:] + 0.05 + noise[attack_step:]
    no_def = np.clip(no_def, 0, 1)

    # Partial defense: moderate drop, slow partial recovery
    partial = np.ones(n_steps) + noise
    drop = np.exp(-0.008 * np.maximum(t - attack_step, 0))
    recover = 1 - 0.5 * np.exp(-0.005 * np.maximum(t - attack_step - 80, 0))
    partial[attack_step:] = np.minimum(drop[attack_step:], recover[attack_step:]) * 0.95 + 0.05
    partial = np.clip(partial, 0, 1)

    # Full CIF: brief dip, rapid recovery
    full_cif = np.ones(n_steps) + noise
    dip = 1 - 0.25 * np.exp(-0.05 * np.maximum(t - attack_step, 0))
    full_cif[attack_step:] = dip[attack_step:] + noise[attack_step:]
    full_cif = np.clip(full_cif, 0, 1)

    return t, no_def, partial, full_cif


def plot_attack_timeline(output_dir: str = "output/figures") -> Figure:
    """Create the integrity degradation time-series (Fig 8).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=8, height=4.5)
    attack_step = 100
    t, no_def, partial, full_cif = _generate_timeseries(attack_step=attack_step)

    ax.plot(t, no_def, color=COLORS["accent"], linewidth=1.8, label="No Defense")
    ax.plot(t, partial, color=COLORS["warning"], linewidth=1.8, label="Partial Defense")
    ax.plot(t, full_cif, color=COLORS["secondary"], linewidth=1.8, label="Full CIF")

    # Attack injection marker
    ax.axvline(x=attack_step, color=COLORS["neutral"], linestyle=":", linewidth=1.5, alpha=0.7)
    ax.annotate(
        "Attack injected",
        xy=(attack_step, 0.98),
        xytext=(attack_step + 40, 0.75),
        fontsize=FONTSIZE["base"],
        arrowprops=dict(arrowstyle="->", color=COLORS["neutral"]),
        color=COLORS["neutral"],
    )

    # Recovery annotation
    ax.annotate(
        "CIF recovery",
        xy=(180, 0.96),
        xytext=(240, 0.85),
        fontsize=FONTSIZE["base"],
        arrowprops=dict(arrowstyle="->", color=COLORS["secondary"]),
        color=COLORS["secondary"],
    )

    format_axis(ax, xlabel="Time Step", ylabel="Integrity Score", title="Integrity Degradation Under Attack")
    ax.set_xlim(0, 500)
    ax.set_ylim(0, 1.05)
    add_legend(ax, loc="lower left")

    fig.tight_layout()
    save_figure(fig, "fig08_attack_timeline", output_dir=output_dir)
    return fig
