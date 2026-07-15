"""Defense composition algebra: pipelines, fusion strategies, and operators.

Provides tools for composing multiple defense modules into series,
parallel, and hybrid pipelines with configurable score-fusion strategies.
"""

from __future__ import annotations

from .adapters import (
    ConsensusAdapter,
    DetectionAdapter,
    FirewallAdapter,
    InvariantsAdapter,
    ProvenanceAdapter,
    SandboxAdapter,
    TripwireAdapter,
    TrustAdapter,
)
from .algebra import (
    compute_parallel_detection_rate,
    compute_series_detection_rate,
    parallel_compose,
    series_compose,
    validate_composition_theorem,
)
from .factory import (
    CANONICAL_ORDER,
    MODULE_REGISTRY,
    create_full_pipeline,
    create_module_dict,
    create_pipeline_without,
)
from .fusion import (
    AttentionFusion,
    FusionStrategy,
    LearnedFusion,
    MajorityVotingFusion,
    MaxScoreFusion,
    WeightedAverageFusion,
)
from .pipeline import (
    DefenseModule,
    HybridPipeline,
    ParallelPipeline,
    PipelineResult,
    SeriesPipeline,
)

__all__ = [
    # Pipeline
    "DefenseModule",
    "PipelineResult",
    "SeriesPipeline",
    "ParallelPipeline",
    "HybridPipeline",
    # Fusion
    "FusionStrategy",
    "WeightedAverageFusion",
    "MajorityVotingFusion",
    "MaxScoreFusion",
    "AttentionFusion",
    "LearnedFusion",
    # Algebra
    "series_compose",
    "parallel_compose",
    "compute_series_detection_rate",
    "compute_parallel_detection_rate",
    "validate_composition_theorem",
    # Adapters
    "FirewallAdapter",
    "DetectionAdapter",
    "TripwireAdapter",
    "TrustAdapter",
    "ConsensusAdapter",
    "ProvenanceAdapter",
    "SandboxAdapter",
    "InvariantsAdapter",
    # Factory
    "CANONICAL_ORDER",
    "MODULE_REGISTRY",
    "create_full_pipeline",
    "create_pipeline_without",
    "create_module_dict",
]
