"""Fig 8: Measured colony integrity trajectories under attack.

Every curve in this figure is the per-step ``ColonyResult.timeline`` produced by
running the corresponding :mod:`colony` scenario through
:class:`colony.ColonyBenchmark` at a fixed seed.  Nothing here is synthesised
or reconstructed from summary scalars.

History / invariant
-------------------
An earlier revision wrapped the scenario run in ``try: ... except Exception:``
and, on failure, fabricated each curve analytically as
``1 - (1 - detection_rate) * sin(pi * progress)`` from two summary scalars in
``output/data/colony_results.json`` -- while the docstring claimed the series
were measured.  The import inside that ``try`` referenced a module
(``colony.coordinated_attack``) that never existed, so the fabricated branch
was the *only* branch that ever ran, and the legend attributed each synthetic
curve to the wrong scenario.

The fallback is gone deliberately.  ``_load_timelines`` must fail loudly rather
than substitute a plausible-looking curve: a reader cannot tell a fabricated
integrity trace from a measured one by looking at it, so the code must never be
able to silently swap one for the other.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np
from matplotlib.figure import Figure

from colony.benchmark import ColonyBenchmark

from ..style import (
    FONTSIZE,
    PALETTE,
    add_legend,
    create_figure,
    format_axis,
    save_figure,
)

logger = logging.getLogger(__name__)

#: Seed used for the published figure.  Fixed so the figure is reproducible.
TIMELINE_SEED = 42

#: Human-readable labels for the built-in scenario identifiers.
SCENARIO_LABELS = {
    "recruitment_poisoning": "Recruitment Poisoning",
    "sybil_infiltration": "Sybil Infiltration",
    "quorum_manipulation": "Quorum Manipulation",
    "belief_cascade": "Belief Cascade",
    "emergent_misalignment": "Emergent Misalignment",
}


def _load_timelines(
    benchmark: Optional[ColonyBenchmark] = None,
    seed: int = TIMELINE_SEED,
) -> List[Tuple[str, np.ndarray]]:
    """Run the colony scenarios and return their measured integrity timelines.

    Parameters
    ----------
    benchmark : ColonyBenchmark, optional
        Benchmark to run.  Defaults to ``ColonyBenchmark()`` (all five
        built-in scenarios).
    seed : int
        Base seed forwarded to :meth:`ColonyBenchmark.run_all`.

    Returns
    -------
    list of (label, ndarray)
        One entry per scenario, in benchmark order.  Each array is the
        scenario's own per-step integrity trace, unmodified.

    Raises
    ------
    Exception
        Whatever a scenario raises is propagated unchanged.  There is no
        synthetic fallback -- see the module docstring.
    ValueError
        If the benchmark yields no scenarios, or if any scenario returns an
        empty timeline (an empty trace is a broken measurement, not a
        licence to invent one).
    """
    bench = benchmark if benchmark is not None else ColonyBenchmark()
    results = bench.run_all(seed=seed)

    if not results:
        raise ValueError("ColonyBenchmark produced no scenario results")

    series: List[Tuple[str, np.ndarray]] = []
    for result in results:
        name = result.scenario_name or "unnamed_scenario"
        timeline = np.asarray(result.timeline, dtype=float)
        if timeline.size == 0:
            raise ValueError(
                f"Scenario {name!r} returned an empty integrity timeline; "
                "refusing to synthesise a substitute curve"
            )
        series.append((SCENARIO_LABELS.get(name, name), timeline))

    logger.info("Loaded %d measured colony timelines (seed=%d)", len(series), seed)
    return series


def plot_attack_timeline(
    output_dir: str = "output/figures",
    series: Optional[Sequence[Tuple[str, np.ndarray]]] = None,
) -> Figure:
    """Create the measured integrity time-series figure (Fig 8).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.
    series : sequence of (label, ndarray), optional
        Pre-computed timelines.  Defaults to running the colony benchmark via
        :func:`_load_timelines`.

    Returns
    -------
    Figure
    """
    resolved = list(series) if series is not None else _load_timelines()

    fig, ax = create_figure(width=8, height=4.5)

    for i, (label, values) in enumerate(resolved):
        n = len(values)
        # Scenarios have different horizons (100-1000 steps); plot each against
        # its own normalised progress so the traces are comparable.
        x = np.linspace(0.0, 1.0, n) if n > 1 else np.zeros(1)
        ax.plot(
            x,
            values,
            color=PALETTE[i % len(PALETTE)],
            linewidth=1.6,
            label=f"{label} (n={n})",
        )

    format_axis(
        ax,
        xlabel="Simulation progress (fraction of scenario steps)",
        ylabel="Integrity Score",
        title="Measured Colony Integrity Under Attack Scenarios",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    add_legend(ax, loc="lower left")
    ax.text(
        0.99,
        0.02,
        f"ColonyBenchmark, seed={TIMELINE_SEED}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=FONTSIZE["tiny"],
        color="#888888",
    )

    fig.tight_layout()
    save_figure(fig, "fig08_attack_timeline", output_dir=output_dir)
    return fig
