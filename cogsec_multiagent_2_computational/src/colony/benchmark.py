"""Colony-level CogSec benchmark runner.

Orchestrates execution of all colony scenarios and collects results.
Each scenario simulates a multi-agent colony under different threat
models (or no threat) and reports detection, resilience, and recovery
metrics via the Colony Cognitive Security (CCS) score.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
        """Run every registered scenario.

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
