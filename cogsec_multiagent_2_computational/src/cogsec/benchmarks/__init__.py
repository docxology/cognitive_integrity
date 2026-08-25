"""Colony-scale benchmarks, in the form S03 documents them.

The supplement's runner reads::

    from cogsec.benchmarks import ColonyBenchmark

    benchmark = ColonyBenchmark("recruitment_poisoning", config)
    results = benchmark.run()
    ccs = benchmark.compute_ccs(weights=[0.3, 0.2, 0.3, 0.2])

The internal :class:`colony.benchmark.ColonyBenchmark` takes a list of scenario
objects and runs all of them; it has no single-scenario constructor, no
``run()`` and no ``compute_ccs()``. Rather than rewrite the supplement to the
internal shape, this wraps the internals in the documented shape, because a
reader reproducing one published scenario wants exactly one scenario, and the
config dict in the supplement is the natural way to say which.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from colony.benchmark import ColonyConfig, ColonyResult
from colony.scorecard import CCSWeights, compute_ccs

__all__ = ["ColonyBenchmark", "SCENARIOS"]


def _scenario_registry() -> Dict[str, Any]:
    """The five built-in scenarios, by the names the manuscript uses."""
    from colony.belief_cascade import BeliefCascadeScenario
    from colony.emergent_misalignment import EmergentMisalignmentScenario
    from colony.quorum_manipulation import QuorumManipulationScenario
    from colony.recruitment_poisoning import RecruitmentPoisoningScenario
    from colony.sybil_infiltration import SybilInfiltrationScenario

    return {
        "recruitment_poisoning": RecruitmentPoisoningScenario,
        "sybil_infiltration": SybilInfiltrationScenario,
        "quorum_manipulation": QuorumManipulationScenario,
        "belief_cascade": BeliefCascadeScenario,
        "emergent_misalignment": EmergentMisalignmentScenario,
    }


#: Scenario names accepted by :class:`ColonyBenchmark`, in manuscript order.
SCENARIOS = tuple(_scenario_registry())


class ColonyBenchmark:
    """One named colony scenario, configured and run.

    Parameters
    ----------
    name:
        One of :data:`SCENARIOS`. An unknown name raises rather than falling
        back to a default scenario, because silently running something other
        than what was asked for is how a benchmark result gets attributed to
        the wrong experiment.
    config:
        The supplement's config dict. ``n_agents``, ``duration_steps`` and
        ``seed`` map onto :class:`~colony.benchmark.ColonyConfig`;
        ``adversary_class`` selects the Omega level, which sets the adversary
        count when one is not given explicitly. ``stigmergy`` is accepted and
        recorded but does not change the simulation: the substrate is not
        modelled, and pretending otherwise by accepting the key silently would
        be worse than saying so here.
    """

    #: Adversary fraction implied by each Omega level when the caller gives no
    #: explicit count. Higher classes field more compromised agents.
    _OMEGA_FRACTION = {
        "omega_1": 0.05,
        "omega_2": 0.10,
        "omega_3": 0.20,
        "omega_4": 0.30,
        "omega_5": 0.40,
    }

    #: Config keys this facade understands. Anything else raises, so a typo in
    #: a published config is an error rather than a silently ignored setting.
    _KNOWN_KEYS = frozenset(
        {"n_agents", "duration_steps", "n_steps", "seed", "adversary_class",
         "n_adversaries", "adversary_fraction", "stigmergy"}
    )

    def __init__(self, name: str, config: Optional[Mapping[str, Any]] = None) -> None:
        registry = _scenario_registry()
        if name not in registry:
            raise KeyError(
                f"unknown scenario {name!r}; known scenarios are {', '.join(SCENARIOS)}"
            )
        config = dict(config or {})
        unknown = set(config) - self._KNOWN_KEYS
        if unknown:
            raise KeyError(
                f"unknown config key(s) {sorted(unknown)}; understood keys are "
                f"{sorted(self._KNOWN_KEYS)}"
            )

        self.name = name
        self.scenario = registry[name]()
        self.stigmergy = config.get("stigmergy")
        self.config = self._build_config(config)
        self.result: Optional[ColonyResult] = None

    def _build_config(self, config: Mapping[str, Any]) -> ColonyConfig:
        n_agents = int(config.get("n_agents", ColonyConfig.n_agents))
        n_steps = int(config.get("duration_steps", config.get("n_steps", ColonyConfig.n_steps)))
        seed = int(config.get("seed", ColonyConfig.seed))

        if "n_adversaries" in config:
            n_adversaries = int(config["n_adversaries"])
            fraction = n_adversaries / max(n_agents, 1)
        else:
            omega = config.get("adversary_class")
            if omega is not None and omega not in self._OMEGA_FRACTION:
                raise KeyError(
                    f"unknown adversary_class {omega!r}; known classes are "
                    f"{', '.join(self._OMEGA_FRACTION)}"
                )
            fraction = (
                self._OMEGA_FRACTION[omega]
                if omega is not None
                else float(config.get("adversary_fraction", ColonyConfig.adversary_fraction))
            )
            n_adversaries = max(1, round(n_agents * fraction))

        return ColonyConfig(
            n_agents=n_agents,
            n_steps=n_steps,
            n_adversaries=n_adversaries,
            adversary_fraction=fraction,
            seed=seed,
        )

    def run(self) -> ColonyResult:
        """Run the scenario once and return its result.

        A single run of a stochastic simulation is one draw. Use
        :meth:`run_repeated` for anything that will be published; this exists
        because the supplement's example is a demonstration, not an experiment.
        """
        import numpy as np

        rng = np.random.default_rng(self.config.seed)
        self.result = self.scenario.run(self.config, rng)
        return self.result

    def run_repeated(self, n_repeats: int = 20) -> list[ColonyResult]:
        """Run the scenario across consecutive seeds, returning every run."""
        import numpy as np

        if n_repeats < 1:
            raise ValueError(f"n_repeats must be positive, got {n_repeats}")
        runs = []
        for offset in range(n_repeats):
            config = ColonyConfig(
                n_agents=self.config.n_agents,
                n_steps=self.config.n_steps,
                n_adversaries=self.config.n_adversaries,
                adversary_fraction=self.config.adversary_fraction,
                seed=self.config.seed + offset,
            )
            runs.append(self.scenario.run(config, np.random.default_rng(config.seed)))
        self.result = runs[-1]
        return runs

    def compute_ccs(
        self,
        weights: Optional[Sequence[float] | CCSWeights] = None,
        result: Optional[ColonyResult] = None,
    ) -> float:
        """The Colony Cognitive Security score for a completed run.

        ``weights`` accepts the supplement's four-element sequence
        ``[detection, false_positive, resilience, recovery]`` as well as a
        :class:`~colony.scorecard.CCSWeights`. Calling this before :meth:`run`
        raises rather than returning zero, because a zero CCS is a meaningful
        score and must not also mean "no run happened".
        """
        target = result if result is not None else self.result
        if target is None:
            raise RuntimeError("call run() before compute_ccs(); there is no result to score")
        if weights is None:
            resolved = None
        elif isinstance(weights, CCSWeights):
            resolved = weights
        else:
            values = list(weights)
            if len(values) != 4:
                raise ValueError(
                    f"weights must have four elements "
                    f"[detection, false_positive, resilience, recovery], got {len(values)}"
                )
            resolved = CCSWeights(*values)
        return compute_ccs(
            detection_rate=target.detection_rate,
            false_positive_rate=target.false_positive_rate,
            resilience=target.resilience_score,
            recovery_steps=target.recovery_steps,
            max_steps=self.config.n_steps,
            weights=resolved,
        )
