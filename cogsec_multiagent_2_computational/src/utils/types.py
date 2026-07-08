"""Shared enums, dataclasses, and type definitions for the CogSec framework.

Also provides serialization helpers used by the composer web UI data pipeline.
"""

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

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict representation.

        Recursively converts nested dataclasses and enums so the output
        can be passed directly to ``json.dumps`` without a custom encoder.

        Returns:
            Dict with keys ``detected``, ``score``, ``module_name``,
            ``details``, and ``latency_ms``.
        """
        return {
            "detected": self.detected,
            "score": round(self.score, 6),
            "module_name": self.module_name,
            "details": _serialize_value(self.details),
            "latency_ms": round(self.latency_ms, 3),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DefenseResult":
        """Reconstruct a :class:`DefenseResult` from a serialized dict.

        Args:
            d: Dict produced by :meth:`to_dict` (or compatible).

        Returns:
            Populated :class:`DefenseResult` instance.
        """
        return cls(
            detected=bool(d["detected"]),
            score=float(d["score"]),
            module_name=str(d["module_name"]),
            details=d.get("details", {}),
            latency_ms=float(d.get("latency_ms", 0.0)),
        )


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

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        return {
            "name": self.name,
            "value": round(self.value, 6),
            "ci_lower": round(self.ci_lower, 6) if self.ci_lower is not None else None,
            "ci_upper": round(self.ci_upper, 6) if self.ci_upper is not None else None,
            "n": self.n,
        }


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

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        return {
            "seed": self.seed,
            "n_runs": self.n_runs,
            "agent_counts": list(self.agent_counts),
            "attack_corpus_size": self.attack_corpus_size,
            "architectures": [a.value for a in self.architectures],
            "output_dir": self.output_dir,
        }


# ---------------------------------------------------------------------------
# Severity enum (shared across modules)
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """Severity levels shared across defense modules."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ---------------------------------------------------------------------------
# Web UI data format — serialization helpers
# ---------------------------------------------------------------------------

def _serialize_value(v: Any) -> Any:
    """Recursively convert a value to a JSON-serialisable type.

    Handles:
    - ``None``, ``bool``, ``int``, ``float``, ``str`` — passed through.
    - ``Enum`` subtypes — converted to their ``.value``.
    - ``dataclasses.dataclass`` instances — converted via :func:`asdict`.
    - ``dict`` — values recursively processed.
    - ``list`` / ``tuple`` — elements recursively processed.
    - Other objects — converted to ``str``.

    Args:
        v: Any Python value.

    Returns:
        A JSON-serialisable counterpart.
    """
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, dict):
        return {str(k): _serialize_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_serialize_value(item) for item in v]
    # Check if it is a dataclass instance (not a class itself)
    try:
        from dataclasses import fields as _fields
        from dataclasses import is_dataclass
        if is_dataclass(v) and not isinstance(v, type):
            return {f.name: _serialize_value(getattr(v, f.name)) for f in _fields(v)}
    except Exception:
        pass
    return str(v)


def serialize_defense_result(result: DefenseResult) -> Dict[str, Any]:
    """Serialize a :class:`DefenseResult` for the web UI.

    Convenience wrapper around :meth:`DefenseResult.to_dict`.

    Args:
        result: Defense result to serialize.

    Returns:
        JSON-serialisable dict.
    """
    return result.to_dict()


def serialize_metric_result(result: MetricResult) -> Dict[str, Any]:
    """Serialize a :class:`MetricResult` for the web UI.

    Args:
        result: Metric result to serialize.

    Returns:
        JSON-serialisable dict.
    """
    return result.to_dict()


def serialize_attack_category(category: AttackCategory) -> Dict[str, str]:
    """Serialize an :class:`AttackCategory` enum value with metadata.

    Args:
        category: Attack category enum member.

    Returns:
        Dict with ``value`` and ``top_category`` keys.
    """
    return {
        "value": category.value,
        "top_category": category.top_category,
    }


def serialize_experiment_config(config: ExperimentConfig) -> Dict[str, Any]:
    """Serialize an :class:`ExperimentConfig` for the web UI.

    Args:
        config: Experiment configuration instance.

    Returns:
        JSON-serialisable dict.
    """
    return config.to_dict()


def make_web_ui_payload(
    module_results: Optional[List[DefenseResult]] = None,
    metrics: Optional[List[MetricResult]] = None,
    config: Optional[ExperimentConfig] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble a complete web UI payload from individual components.

    All arguments are optional; only non-``None`` values are included.

    Args:
        module_results: List of :class:`DefenseResult` instances.
        metrics:        List of :class:`MetricResult` instances.
        config:         Experiment configuration.
        extra:          Additional key-value pairs to merge into the payload.

    Returns:
        JSON-serialisable dict ready for ``json.dumps``.
    """
    payload: Dict[str, Any] = {}

    if module_results is not None:
        payload["module_results"] = [r.to_dict() for r in module_results]

    if metrics is not None:
        payload["metrics"] = [m.to_dict() for m in metrics]

    if config is not None:
        payload["config"] = config.to_dict()

    if extra:
        payload.update(_serialize_value(extra))  # type: ignore[arg-type]

    return payload


__all__ = [
    # Core types
    "AttackCategory",
    "AttackOutcome",
    "ArchitectureType",
    "DefenseResult",
    "MetricResult",
    "ExperimentConfig",
    "Severity",
    # Serialization helpers
    "_serialize_value",
    "serialize_defense_result",
    "serialize_metric_result",
    "serialize_attack_category",
    "serialize_experiment_config",
    "make_web_ui_payload",
]
