"""Core defense modules for the Cognitive Security Framework.
from __future__ import annotations


Re-exports all public symbols from the 8 foundational defense modules:
trust, firewall, tripwire, detection, consensus, provenance, invariants, sandbox.
"""

# Trust module
# Consensus module
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
    ClassificationStage,
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
from .trust import (
    ContextAwareTrust,
    InteractionRecord,
    ReputationTracker,
    TrustCalculus,
    TrustConfig,
    TrustMatrix,
    TrustMatrixWithDecay,
)

__all__ = [
    # Trust
    "TrustCalculus", "TrustMatrix", "TrustConfig", "ReputationTracker",
    "ContextAwareTrust", "TrustMatrixWithDecay", "InteractionRecord",
    # Firewall
    "CognitiveFirewall", "Classification", "FirewallConfig", "PatternDetector",
    "EmbeddingStub", "SemanticSimilarityDetector", "MultiStageClassifier",
    "EnhancedCognitiveFirewall", "ClassificationStage",
    # Tripwire
    "CognitiveTripwire", "Canary", "TripwireAlert",
    # Detection
    "DriftDetector", "AnomalyScorer", "DetectionConfig",
    # Consensus
    "ByzantineConsensus", "QuorumVerification", "ConsensusResult",
    "ConsensusConfig", "Vote", "WeightedVote", "WeightedByzantineConsensus",
    "ConfidenceVote", "ConfidenceByzantineConsensus", "CombinedVote",
    "CombinedByzantineConsensus",
    # Provenance
    "TaintLabel", "ProvenanceRecord", "ProvenanceChain", "ProvenanceGraph",
    "CausalAttribution",
    # Invariants
    "Invariant", "InvariantSeverity", "InvariantViolation", "InvariantChecker",
    "RuntimeMonitor", "AgentAction",
    # Sandbox
    "Belief", "BeliefState", "BeliefPartition", "PromotionCriteria",
    "SandboxManager", "SandboxConfig",
]
