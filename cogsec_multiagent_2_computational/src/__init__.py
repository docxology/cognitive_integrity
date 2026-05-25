"""
from __future__ import annotations

Cognitive Security Framework for Multiagent Operators.

Core modules (in ``src.core``):
- trust: Trust calculus with bounded delegation, reputation decay, context boosting
- firewall: Cognitive firewall with multi-stage classification and semantic detection
- tripwire: Canary belief monitoring
- detection: Anomaly and drift detection
- consensus: Byzantine-tolerant belief consensus with weighted voting
- provenance: Information flow tracking with taint propagation
- invariants: Behavioral invariant checking and runtime monitoring
- sandbox: Belief sandboxing with verified/provisional partitions

New packages:
- composition: Defense composition algebra (pipelines, fusion)
- attacks: 950-attack corpus with generators
- architectures: Production multi-agent architecture adapters
- evaluation: Experiment runner, metrics, ROC, benchmarks
- statistics: Hypothesis testing, effect sizes, confidence intervals
- ablation: Component removal and synergy studies
- colony: Colony-level CogSec benchmarks
- formal: Theorem validation and model checker specs
- visualization: Publication-quality figures and LaTeX tables
- data: Data generation and management
- utils: Shared configuration, logging, timing, types
"""

# Many sibling modules use absolute imports (``from utils.timing import ...``)
# that only resolve when ``src/`` is on ``sys.path``.  When the package is
# executed as ``python -m src``, sibling packages are not available by default,
# so we insert the package directory onto ``sys.path`` before triggering any
# transitive imports below.
import sys as _sys
from pathlib import Path as _Path

_SRC_DIR = str(_Path(__file__).resolve().parent)
if _SRC_DIR not in _sys.path:
    _sys.path.insert(0, _SRC_DIR)

# Re-export all core symbols for backward compatibility.
# Existing code using ``from trust import TrustCalculus`` or
# ``from src import TrustCalculus`` continues to work unchanged.

# Consensus module
# Batch detection module
from .core.batch_detection import BatchDetector
from .core.consensus import (
    ByzantineConsensus,
    CombinedByzantineConsensus,
    CombinedVote,
    ConfidenceByzantineConsensus,
    ConfidenceVote,
    ConsensusConfig,
    ConsensusResult,
    QuorumVerification,
    Vote,
    WeightedByzantineConsensus,
    WeightedVote,
)

# Detection module
from .core.detection import (
    AdaptiveBaseline,
    AnomalyScorer,
    DetectionConfig,
    DriftDetector,
    SlidingWindowMonitor,
)

# Firewall module
from .core.firewall import (
    Classification,
    ClassificationStage,
    CognitiveFirewall,
    EmbeddingStub,
    EnhancedCognitiveFirewall,
    FirewallConfig,
    MultiStageClassifier,
    PatternDetector,
    SemanticSimilarityDetector,
    TFIDFEmbedder,
)

# Invariants module
from .core.invariants import (
    AgentAction,
    Invariant,
    InvariantChecker,
    InvariantSeverity,
    InvariantViolation,
    RuntimeMonitor,
)

# Online detection module
from .core.online_detection import CircularBuffer, OnlineDetector, OnlineStatistics

# Provenance module
from .core.provenance import (
    CausalAttribution,
    ProvenanceChain,
    ProvenanceGraph,
    ProvenanceRecord,
    TaintLabel,
)

# Sandbox module
from .core.sandbox import (
    Belief,
    BeliefPartition,
    BeliefState,
    PromotionCriteria,
    SandboxConfig,
    SandboxManager,
)

# Tripwire module
from .core.tripwire import Canary, CognitiveTripwire, TripwireAlert

# Trust module
from .core.trust import (
    ContextAwareTrust,
    InteractionRecord,
    ReputationTracker,
    TrustCalculus,
    TrustConfig,
    TrustMatrix,
    TrustMatrixWithDecay,
)

# Evaluation module
from .evaluation.metrics import DetectionMetrics
from .evaluation.runner import ExperimentResult, ExperimentRunner

__all__ = [
    # Trust
    "TrustCalculus",
    "TrustMatrix",
    "TrustConfig",
    "ReputationTracker",
    "ContextAwareTrust",
    "TrustMatrixWithDecay",
    "InteractionRecord",
    # Firewall
    "CognitiveFirewall",
    "Classification",
    "ClassificationStage",
    "FirewallConfig",
    "PatternDetector",
    "EmbeddingStub",
    "SemanticSimilarityDetector",
    "MultiStageClassifier",
    "EnhancedCognitiveFirewall",
    "TFIDFEmbedder",
    # Tripwire
    "CognitiveTripwire",
    "Canary",
    "TripwireAlert",
    # Detection
    "DriftDetector",
    "AnomalyScorer",
    "DetectionConfig",
    "AdaptiveBaseline",
    "SlidingWindowMonitor",
    # Online Detection
    "CircularBuffer",
    "OnlineStatistics",
    "OnlineDetector",
    # Batch Detection
    "BatchDetector",
    # Consensus
    "ByzantineConsensus",
    "QuorumVerification",
    "ConsensusResult",
    "ConsensusConfig",
    "Vote",
    "WeightedVote",
    "WeightedByzantineConsensus",
    "ConfidenceVote",
    "ConfidenceByzantineConsensus",
    "CombinedVote",
    "CombinedByzantineConsensus",
    # Provenance
    "TaintLabel",
    "ProvenanceRecord",
    "ProvenanceChain",
    "ProvenanceGraph",
    "CausalAttribution",
    # Invariants
    "Invariant",
    "InvariantSeverity",
    "InvariantViolation",
    "InvariantChecker",
    "RuntimeMonitor",
    "AgentAction",
    # Sandbox
    "Belief",
    "BeliefState",
    "BeliefPartition",
    "PromotionCriteria",
    "SandboxManager",
    "SandboxConfig",
    # Evaluation
    "DetectionMetrics",
    "ExperimentRunner",
    "ExperimentResult",
]
