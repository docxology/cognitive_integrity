"""Colony-level Cognitive Security benchmarks.

Re-exports all public symbols from the colony package:
benchmark runner, scenario implementations, and scorecard utilities.
"""

from .belief_cascade import BeliefCascadeScenario
from .benchmark import ColonyBenchmark, ColonyConfig, ColonyResult, ColonyScenario
from .emergent_misalignment import EmergentMisalignmentScenario
from .quorum_manipulation import QuorumManipulationScenario
from .recruitment_poisoning import RecruitmentPoisoningScenario
from .scorecard import CCSWeights, compute_ccs, compute_recovery_steps, compute_resilience
from .sybil_infiltration import SybilInfiltrationScenario

__all__ = [
    # Benchmark
    "ColonyBenchmark",
    "ColonyConfig",
    "ColonyResult",
    "ColonyScenario",
    # Scorecard
    "CCSWeights",
    "compute_ccs",
    "compute_recovery_steps",
    "compute_resilience",
    # Scenarios
    "RecruitmentPoisoningScenario",
    "SybilInfiltrationScenario",
    "QuorumManipulationScenario",
    "BeliefCascadeScenario",
    "EmergentMisalignmentScenario",
]
