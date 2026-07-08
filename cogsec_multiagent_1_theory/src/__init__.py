from __future__ import annotations

"""
Cognitive Security Framework for Multiagent Operators.

Core modules:
- trust: Trust calculus with bounded delegation, reputation decay, context boosting
- firewall: Cognitive firewall with multi-stage classification and semantic detection
- tripwire: Canary belief monitoring
- detection: Anomaly and drift detection
- consensus: Byzantine-tolerant belief consensus with weighted voting
- provenance: Information flow tracking with taint propagation
- invariants: Behavioral invariant checking and runtime monitoring
- sandbox: Belief sandboxing with verified/provisional partitions

v2.0 additions:
- ooda_monitor: OODA phase monitor with Fisher-Rao geometry and CIF-OODA integration
- cif_ad_coupling: CIF-AD coupling matrix analysis and defense portfolio optimization
"""

# Consensus module
# v2.0: CIF-AD Coupling Detector
from .cif_ad_coupling import (
    CIF_AD_COUPLING_MATRIX,
    ADPhase,
    AttackSurfaceMapping,
    CIFADCouplingDetector,
    CIFDefense,
    CouplingAnalysis,
)
from .consensus import (
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
from .detection import AnomalyScorer, DetectionConfig, DriftDetector

# Firewall module
from .firewall import (
    Classification,
    CognitiveFirewall,
    EmbeddingStub,
    EnhancedCognitiveFirewall,
    FirewallConfig,
    MultiStageClassifier,
    PatternDetector,
    SemanticSimilarityDetector,
)

# Invariants module
from .invariants import (
    AgentAction,
    Invariant,
    InvariantChecker,
    InvariantSeverity,
    InvariantViolation,
    RuntimeMonitor,
)

# v2.0: OODA Phase Monitor
from .ooda_monitor import (
    OODAAlert,
    OODACycleStats,
    OODAEvent,
    OODAPhase,
    OODAPhaseAttack,
    OODAPhaseMonitor,
)

# Provenance module
from .provenance import (
    CausalAttribution,
    ProvenanceChain,
    ProvenanceGraph,
    ProvenanceRecord,
    TaintLabel,
)

# Sandbox module
from .sandbox import (
    Belief,
    BeliefPartition,
    BeliefState,
    PromotionCriteria,
    SandboxConfig,
    SandboxManager,
)

# Tripwire module
from .tripwire import Canary, CognitiveTripwire, TripwireAlert

# Trust module
from .trust import (
    ContextAwareTrust,
    ReputationTracker,
    TrustCalculus,
    TrustConfig,
    TrustMatrix,
    TrustMatrixWithDecay,
)

__all__ = [
    # Trust
    "TrustCalculus",
    "TrustMatrix",
    "TrustConfig",
    "ReputationTracker",
    "ContextAwareTrust",
    "TrustMatrixWithDecay",
    # Firewall
    "CognitiveFirewall",
    "Classification",
    "FirewallConfig",
    "PatternDetector",
    "EmbeddingStub",
    "SemanticSimilarityDetector",
    "MultiStageClassifier",
    "EnhancedCognitiveFirewall",
    # Tripwire
    "CognitiveTripwire",
    "Canary",
    "TripwireAlert",
    # Detection
    "DriftDetector",
    "AnomalyScorer",
    "DetectionConfig",
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
    # v2.0: OODA Monitor
    "OODAPhase",
    "OODAPhaseAttack",
    "OODAPhaseMonitor",
    "OODAEvent",
    "OODAAlert",
    "OODACycleStats",
    # v2.0: CIF-AD Coupling
    "ADPhase",
    "CIFDefense",
    "CIFADCouplingDetector",
    "CouplingAnalysis",
    "AttackSurfaceMapping",
    "CIF_AD_COUPLING_MATRIX",
]
