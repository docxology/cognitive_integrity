"""Colony-level CogSec benchmark runner.

Orchestrates execution of all colony scenarios and collects results.
Each scenario simulates a multi-agent colony under different threat
models (or no threat) and reports detection, resilience, and recovery
metrics via the Colony Cognitive Security (CCS) score.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics.confidence import bootstrap_mean_ci
from typing import Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ColonyConfig:
    """Configuration for a colony simulation run.

    Attributes:
        n_agents: Total number of agents in the colony.
        n_steps: Number of simulation steps.
        n_adversaries: Number of adversarial agents (Omega level).
        adversary_fraction: Fraction of agents that are adversaries.
        seed: Random seed for reproducibility.
    """

    n_agents: int = 20
    n_steps: int = 100
    n_adversaries: int = 2
    adversary_fraction: float = 0.1
    seed: int = 42


@dataclass
class ColonyResult:
    """Result of a colony scenario simulation.

    Attributes:
        scenario_name: Identifier for the scenario.
        config: Colony configuration used.
        detection_rate: Fraction of adversarial actions detected [0,1].
        false_positive_rate: Fraction of honest actions falsely flagged [0,1].
        resilience_score: Post-attack integrity / pre-attack integrity [0,1].
        recovery_steps: Steps until integrity recovers above threshold.
        ccs_score: Composite Colony Cognitive Security score [0,1].
        timeline: Integrity scores at each simulation step.
    """

    scenario_name: str = ""
    config: Optional[ColonyConfig] = None
    detection_rate: float = 0.0
    false_positive_rate: float = 0.0
    resilience_score: float = 0.0
    recovery_steps: int = 0
    ccs_score: float = 0.0
    timeline: List[float] = field(default_factory=list)


@dataclass
class ColonyScenarioSummary:
    """Seed-sweep summary for one colony scenario.

    A single simulation run is a single draw from a stochastic process
    (agent initialisation, message ordering and adversary placement are all
    RNG-driven), so a headline such as "100% detection at 0% false
    positives" from one seed is a point estimate with unknown variance.
    This container holds every per-seed run plus mean, 95% bootstrap CI and
    observed min/max for each headline metric.

    Attributes:
        scenario_name: Identifier for the scenario.
        runs: The per-repeat :class:`ColonyResult` objects, in seed order.
        seeds: The seed used for each repeat, in the same order as ``runs``.
        detection_rate_mean: Mean detection rate across repeats.
        detection_rate_ci95: Bootstrap 95% CI for the mean detection rate.
        detection_rate_range: ``(min, max)`` observed detection rate.
        fpr_mean: Mean false-positive rate across repeats.
        fpr_ci95: Bootstrap 95% CI for the mean false-positive rate.
        fpr_range: ``(min, max)`` observed false-positive rate.
        ccs_mean: Mean CCS score across repeats.
        ccs_ci95: Bootstrap 95% CI for the mean CCS score.
        ccs_range: ``(min, max)`` observed CCS score.
        n_repeats: Number of repeats (== ``len(runs)``).
    """

    scenario_name: str
    runs: List[ColonyResult]
    seeds: List[int]
    detection_rate_mean: float
    detection_rate_ci95: Tuple[float, float]
    detection_rate_range: Tuple[float, float]
    fpr_mean: float
    fpr_ci95: Tuple[float, float]
    fpr_range: Tuple[float, float]
    ccs_mean: float
    ccs_ci95: Tuple[float, float]
    ccs_range: Tuple[float, float]
    n_repeats: int

    @property
    def detection_rate_values(self) -> List[float]:
        """Per-repeat detection rates."""
        return [r.detection_rate for r in self.runs]

    @property
    def fpr_values(self) -> List[float]:
        """Per-repeat false-positive rates."""
        return [r.false_positive_rate for r in self.runs]

    @property
    def ccs_values(self) -> List[float]:
        """Per-repeat CCS scores."""
        return [r.ccs_score for r in self.runs]

    def all_runs_at(self, metric: str, value: float, tol: float = 0.0) -> bool:
        """True only if *every* repeat hit *value* on *metric*.

        This is the test a "guarantee"-shaped claim has to pass: a mean of
        1.0 with one repeat at 0.98 is not a guarantee.

        Args:
            metric: ``"detection_rate"``, ``"false_positive_rate"`` or
                ``"ccs_score"``.
            value: The value every repeat must equal.
            tol: Absolute tolerance.

        Returns:
            True if all repeats are within *tol* of *value*.

        Raises:
            ValueError: If *metric* is not a recognised ColonyResult field.
        """
        valid = {"detection_rate", "false_positive_rate", "ccs_score"}
        if metric not in valid:
            raise ValueError(f"metric must be one of {sorted(valid)}, got '{metric}'")
        return all(abs(getattr(r, metric) - value) <= tol for r in self.runs)


def _summarise(
    values: List[float], seed: int
) -> Tuple[float, Tuple[float, float], Tuple[float, float]]:
    """Return ``(mean, bootstrap_ci95, (min, max))`` for *values*."""
    arr = np.asarray(values, dtype=np.float64)
    mean = float(arr.mean())
    if arr.size < 2:
        # A single observation carries no information about the spread; a
        # degenerate CI is the honest representation, not a narrow one.
        return mean, (mean, mean), (mean, mean)
    _, lower, upper = bootstrap_mean_ci(arr, n_bootstrap=2000, seed=seed)
    return mean, (float(lower), float(upper)), (float(arr.min()), float(arr.max()))


# ---------------------------------------------------------------------------
# Scenario ABC
# ---------------------------------------------------------------------------

class ColonyScenario(ABC):
    """Abstract base class for colony scenarios."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique scenario identifier."""
        ...

    @abstractmethod
    def default_config(self) -> ColonyConfig:
        """Return the default configuration for this scenario."""
        ...

    @abstractmethod
    def run(self, config: ColonyConfig, rng: np.random.Generator) -> ColonyResult:
        """Execute the scenario and return results."""
        ...


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

class ColonyBenchmark:
    """Run all colony CogSec scenarios and collect results.

    Usage::

        bench = ColonyBenchmark()
        results = bench.run_all(seed=42)
        print(bench.summary())
    """

    def __init__(
        self,
        scenarios: Optional[List[ColonyScenario]] = None,
    ) -> None:
        """Initialise with scenarios.

        Args:
            scenarios: List of scenarios to run.  If ``None``, loads all
                five built-in scenarios.
        """
        if scenarios is not None:
            self._scenarios = scenarios
        else:
            self._scenarios = self._load_default_scenarios()

        self._results: List[ColonyResult] = []
        self._summaries: List[ColonyScenarioSummary] = []

    @staticmethod
    def _load_default_scenarios() -> list:
        """Load all five built-in colony scenarios."""
        from .belief_cascade import BeliefCascadeScenario
        from .emergent_misalignment import EmergentMisalignmentScenario
        from .quorum_manipulation import QuorumManipulationScenario
        from .recruitment_poisoning import RecruitmentPoisoningScenario
        from .sybil_infiltration import SybilInfiltrationScenario

        return [
            RecruitmentPoisoningScenario(),
            SybilInfiltrationScenario(),
            QuorumManipulationScenario(),
            BeliefCascadeScenario(),
            EmergentMisalignmentScenario(),
        ]

    def run_all(self, seed: int = 42) -> List[ColonyResult]:
        """Run every registered scenario once.

        Single-run point estimates from a stochastic simulation carry no
        uncertainty information; prefer :meth:`run_all_repeated` for any
        number that will be published.

        Args:
            seed: Base random seed; each scenario gets a derived seed.

        Returns:
            List of ColonyResult, one per scenario.
        """
        self._results = []
        for i, scenario in enumerate(self._scenarios):
            result = self.run_scenario(scenario, seed=seed + i)
            self._results.append(result)
        return list(self._results)

    def seed_for(self, scenario_index: int, repeat_index: int, base_seed: int) -> int:
        """Return the seed used for one (scenario, repeat) pair.

        The stride is the scenario count, so every (scenario, repeat) pair
        gets a distinct seed and ``repeat_index=0`` reproduces the legacy
        single-run seeds ``base_seed + scenario_index`` exactly.

        Args:
            scenario_index: Index into the registered scenarios.
            repeat_index: Zero-based repeat number.
            base_seed: Base seed for the sweep.

        Returns:
            The derived seed.
        """
        return base_seed + scenario_index + repeat_index * len(self._scenarios)

    def run_all_repeated(
        self,
        seed: int = 42,
        n_repeats: int = 30,
    ) -> List[ColonyScenarioSummary]:
        """Run every scenario over a seed sweep and interval-estimate.

        Each scenario is executed ``n_repeats`` times on distinct seeds (see
        :meth:`seed_for`) and the headline metrics are reported as a mean
        with a 95% bootstrap CI plus the observed min/max.  With
        ``n_repeats=1`` the per-scenario runs are byte-identical to
        :meth:`run_all` with the same base seed, so the legacy artifact can
        be reproduced for comparison.

        Args:
            seed: Base random seed for the sweep.
            n_repeats: Number of repeats per scenario; must be >= 1.

        Returns:
            One :class:`ColonyScenarioSummary` per registered scenario.

        Raises:
            ValueError: If *n_repeats* < 1.
        """
        if n_repeats < 1:
            raise ValueError(f"n_repeats must be >= 1, got {n_repeats}")

        summaries: List[ColonyScenarioSummary] = []
        for i, scenario in enumerate(self._scenarios):
            seeds = [self.seed_for(i, r, seed) for r in range(n_repeats)]
            runs = [self.run_scenario(scenario, seed=s) for s in seeds]

            # Bootstrap seeds are derived from the sweep seed so the CI is
            # reproducible without being shared across metrics.
            dr_mean, dr_ci, dr_range = _summarise(
                [r.detection_rate for r in runs], seed=seed + 1_000 + i
            )
            fpr_mean, fpr_ci, fpr_range = _summarise(
                [r.false_positive_rate for r in runs], seed=seed + 2_000 + i
            )
            ccs_mean, ccs_ci, ccs_range = _summarise(
                [r.ccs_score for r in runs], seed=seed + 3_000 + i
            )

            summaries.append(
                ColonyScenarioSummary(
                    scenario_name=runs[0].scenario_name,
                    runs=runs,
                    seeds=seeds,
                    detection_rate_mean=dr_mean,
                    detection_rate_ci95=dr_ci,
                    detection_rate_range=dr_range,
                    fpr_mean=fpr_mean,
                    fpr_ci95=fpr_ci,
                    fpr_range=fpr_range,
                    ccs_mean=ccs_mean,
                    ccs_ci95=ccs_ci,
                    ccs_range=ccs_range,
                    n_repeats=n_repeats,
                )
            )

        self._summaries = summaries
        # Keep ``summary()`` meaningful after a sweep: expose the first repeat.
        self._results = [s.runs[0] for s in summaries]
        return list(summaries)

    def run_scenario(
        self,
        scenario,
        seed: int = 42,
    ) -> ColonyResult:
        """Run a single scenario.

        Args:
            scenario: ColonyScenario instance.
            seed: Random seed.

        Returns:
            ColonyResult from the scenario.
        """
        rng = np.random.default_rng(seed)
        config = scenario.default_config()
        config.seed = seed
        return scenario.run(config, rng)

    def summary(self) -> Dict[str, float]:
        """Return CCS score per scenario.

        Returns:
            Dict mapping scenario name to CCS score.
        """
        return {r.scenario_name: r.ccs_score for r in self._results}
