"""
from __future__ import annotations

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
"""

# Consensus module
from .consensus import (ByzantineConsensus, CombinedByzantineConsensus,
                        CombinedVote, ConfidenceByzantineConsensus,
                        ConfidenceVote, ConsensusConfig, ConsensusResult,
                        QuorumVerification, Vote, WeightedByzantineConsensus,
                        WeightedVote)
# Detection module
from .detection import AnomalyScorer, DetectionConfig, DriftDetector
# Firewall module
from .firewall import (Classification, CognitiveFirewall, EmbeddingStub,
                       EnhancedCognitiveFirewall, FirewallConfig,
                       MultiStageClassifier, PatternDetector,
                       SemanticSimilarityDetector)
# Invariants module
from .invariants import (AgentAction, Invariant, InvariantChecker,
                         InvariantSeverity, InvariantViolation, RuntimeMonitor)
# Provenance module
from .provenance import (CausalAttribution, ProvenanceChain, ProvenanceGraph,
                         ProvenanceRecord, TaintLabel)
# Sandbox module
from .sandbox import (Belief, BeliefPartition, BeliefState, PromotionCriteria,
                      SandboxConfig, SandboxManager)
# Tripwire module
from .tripwire import Canary, CognitiveTripwire, TripwireAlert
# Trust module
from .trust import (ContextAwareTrust, ReputationTracker, TrustCalculus,
                    TrustConfig, TrustMatrix, TrustMatrixWithDecay)

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
]
