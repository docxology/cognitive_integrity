"""Shared enums, dataclasses, and type definitions for the CogSec framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Attack taxonomy
# ---------------------------------------------------------------------------

class AttackCategory(Enum):
    """Top-level attack categories (4 categories, 12 subcategories)."""

    # Prompt injection attacks (500 of 950)
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    NESTED_INJECTION = "nested_injection"

    # Trust exploitation attacks (200 of 950)
    IMPERSONATION = "impersonation"
    TRUST_INFLATION = "trust_inflation"
    DELEGATION_ABUSE = "delegation_abuse"

    # Belief manipulation attacks (150 of 950)
    BELIEF_DRIFT = "belief_drift"
    BELIEF_FABRICATION = "belief_fabrication"
    BELIEF_INJECTION = "belief_injection"

    # Coordination attacks (100 of 950)
    SYBIL_ATTACK = "sybil_attack"
    CONSENSUS_POISONING = "consensus_poisoning"
    TIMING_ATTACK = "timing_attack"

    @property
    def top_category(self) -> str:
        """Return the top-level category name."""
        _map = {
            "direct_injection": "injection",
            "indirect_injection": "injection",
            "nested_injection": "injection",
            "impersonation": "trust_exploitation",
            "trust_inflation": "trust_exploitation",
            "delegation_abuse": "trust_exploitation",
            "belief_drift": "belief_manipulation",
            "belief_fabrication": "belief_manipulation",
            "belief_injection": "belief_manipulation",
            "sybil_attack": "coordination",
            "consensus_poisoning": "coordination",
            "timing_attack": "coordination",
        }
        return _map[self.value]


class AttackOutcome(Enum):
    """Result of an attack against a defense pipeline."""

    DETECTED = "detected"
    MISSED = "missed"
    PARTIAL = "partial"


class ArchitectureType(Enum):
    """Production multi-agent architecture types."""

    CLAUDE_CODE = "claude_code"
    AUTOGPT = "autogpt"
    CREWAI = "crewai"
    LANGGRAPH = "langgraph"


# ---------------------------------------------------------------------------
# Defense result
# ---------------------------------------------------------------------------

@dataclass
class DefenseResult:
    """Result from a defense module evaluation.

    Attributes:
        detected: Whether the defense flagged the input.
        score: Confidence/severity score in [0, 1].
        module_name: Name of the defense module that produced this result.
        details: Optional diagnostic information.
        latency_ms: Processing time in milliseconds.
    """

    detected: bool
    score: float
    module_name: str
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Metric result
# ---------------------------------------------------------------------------

@dataclass
class MetricResult:
    """Container for a single metric computation.

    Attributes:
        name: Metric name (e.g. ``'TPR'``, ``'F1'``).
        value: Computed metric value.
        ci_lower: Lower bound of 95 % confidence interval (if computed).
        ci_upper: Upper bound of 95 % confidence interval (if computed).
        n: Sample size used.
    """

    name: str
    value: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    n: int = 0


# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------

@dataclass
class ExperimentConfig:
    """Configuration for a full evaluation experiment.

    Attributes:
        seed: Random seed for reproducibility.
        n_runs: Number of independent repetitions.
        agent_counts: Agent counts for scalability sweeps.
        attack_corpus_size: Total attacks in the corpus.
        architectures: Which architectures to evaluate.
        output_dir: Directory for experiment outputs.
    """

    seed: int = 42
    n_runs: int = 10
    agent_counts: List[int] = field(
        default_factory=lambda: [2, 3, 5, 7, 10, 15, 20, 30, 50, 100]
    )
    attack_corpus_size: int = 950
    architectures: List[ArchitectureType] = field(
        default_factory=lambda: list(ArchitectureType)
    )
    output_dir: str = "output"


# ---------------------------------------------------------------------------
# Severity enum (shared across modules)
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """Severity levels shared across defense modules."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
