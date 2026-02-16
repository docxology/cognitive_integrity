"""Data schemas for experimental results.

Provides typed dataclasses for detection, scalability, ablation, and
colony benchmark data with serialisation helpers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class DetectionData:
    """Detection rates across architectures and attack categories.

    Attributes:
        architectures: List of architecture names.
        categories: List of attack category names.
        means: 2D list of mean detection rates (arch x category).
        cis: 2D list of 95% CI half-widths.
        seed: Random seed used for generation.
    """

    architectures: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    means: List[List[float]] = field(default_factory=list)
    cis: List[List[float]] = field(default_factory=list)
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScalabilityData:
    """Scalability measurements across agent counts.

    Attributes:
        agent_counts: List of agent counts tested.
        latency_ms: Latency measurement per agent count.
        memory_mb: Memory measurement per agent count.
        regression_coeffs: Quadratic regression coefficients [a, b, c].
        r_squared: Regression R-squared value.
        seed: Random seed used for generation.
    """

    agent_counts: List[int] = field(default_factory=list)
    latency_ms: List[float] = field(default_factory=list)
    memory_mb: List[float] = field(default_factory=list)
    regression_coeffs: List[float] = field(default_factory=list)
    r_squared: float = 0.0
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScalabilityData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AblationData:
    """Ablation study results for component removal.

    Attributes:
        configurations: List of configuration names.
        detection_rates: Detection rate per configuration.
        cis: 95% CI half-width per configuration.
        seed: Random seed used for generation.
    """

    configurations: List[str] = field(default_factory=list)
    detection_rates: List[float] = field(default_factory=list)
    cis: List[float] = field(default_factory=list)
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AblationData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ColonyData:
    """Colony-level benchmark results.

    Attributes:
        colony_sizes: List of colony sizes tested.
        convergence_steps: Steps to consensus per colony size.
        integrity_scores: Final integrity scores per colony size.
        attack_success_rate: Rate of successful attacks per colony size.
        seed: Random seed used for generation.
    """

    colony_sizes: List[int] = field(default_factory=list)
    convergence_steps: List[int] = field(default_factory=list)
    integrity_scores: List[float] = field(default_factory=list)
    attack_success_rate: List[float] = field(default_factory=list)
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColonyData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
