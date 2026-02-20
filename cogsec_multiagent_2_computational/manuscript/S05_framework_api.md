\newpage

# Supplementary: Framework API Reference {#sec:framework-api}

## Overview

This supplementary material documents the core framework modules that implement the theoretical constructs from Part 1. The complete source code is available at: **<https://github.com/docxology/cognitive_integrity>**

## Trust Module {#sec:trust-module-api}

The trust module implements bounded trust delegation with configurable decay.

**Table: Trust module API: Core classes for trust computation and management.** {#tab:trust-api}

| Class | Description |
| --- | --- |
| \texttt{TrustCalculus} | Computes composite trust: $T = \alpha \cdot T_{base} + \beta \cdot T_{rep} + \gamma \cdot T_{ctx}$. Implements delegation decay: $T_{delegated} = \min(T_{i \to j}, T_{j \to k}) \cdot \delta^d$ |
| \texttt{TrustMatrix} | Manages pairwise trust between $n$ agents with O(1) lookups and O(1) updates. Supports efficient path trust queries. |
| \texttt{ReputationTracker} | Tracks time-decayed reputation based on interaction history. Implements exponential decay for staleness. |
| \texttt{ContextAwareTrust} | Provides task-specific trust modulation based on capability matching. |
| \texttt{TrustMatrixWithDecay} | Extension of TrustMatrix with automatic time-based trust decay. |

**Key Methods**:

- `TrustCalculus.compute_trust(base, reputation, context)` → $[0, 1]$
- `TrustCalculus.delegate_trust(source_trust, target_trust, depth)` → bounded trust
- `TrustMatrix.get_delegation_trust(path)` → end-to-end path trust
- `ReputationTracker.record_interaction(source, target, outcome, timestamp)`

## Firewall Module {#sec:firewall-api}

The firewall module implements multi-stage classification for cognitive attack detection.

**Table: Firewall module API: Classes for message classification and threat detection.** {#tab:firewall-api}

| Class | Description |
| --- | --- |
| \texttt{CognitiveFirewall} | Three-tier classifier (ACCEPT/QUARANTINE/REJECT) with configurable thresholds. Combines pattern matching, semantic analysis, and anomaly detection. |
| \texttt{PatternDetector} | Heuristic pattern matching with 15 injection patterns and 20 suspicious indicators. Weighted scoring based on pattern severity. |
| \texttt{SemanticSimilarityDetector} | Embedding-based similarity to known malicious patterns. Supports custom embedding models or hash-based fallback. |
| \texttt{MultiStageClassifier} | Orchestrates multi-stage detection pipeline with configurable stage weights. |
| \texttt{EnhancedCognitiveFirewall} | Extended firewall with provenance tracking and audit logging. |

**Key Methods**:

- `CognitiveFirewall.classify(message)` → Classification enum
- `CognitiveFirewall.process(message)` → (classification, processed\_message)
- `PatternDetector.score_injection(message)` → $[0, 1]$
- `SemanticSimilarityDetector.score_semantic_similarity(message)` → $[0, 1]$

## Consensus Module {#sec:consensus-api}

The consensus module implements Byzantine-tolerant agreement protocols.

**Table: Consensus module API: Classes for Byzantine-tolerant multiagent decisions.** {#tab:consensus-api}

| Class | Description |
| --- | --- |
| \texttt{ByzantineConsensus} | Core consensus with $n \geq 3f + 1$ guarantee. Implements three-phase protocol: collect, echo, decide. |
| \texttt{WeightedByzantineConsensus} | Trust-weighted voting where high-trust agents have greater influence. Prevents low-trust Sybil attacks. |
| \texttt{ConfidenceByzantineConsensus} | Votes weighted by agent confidence in their own belief. |
| \texttt{CombinedByzantineConsensus} | Multiplies trust and confidence weights for robust aggregation. |
| \texttt{QuorumVerification} | Action-level quorum gates for critical operations. Configurable approval thresholds. |

**Key Methods**:

- `ByzantineConsensus.submit_vote(vote)` → None
- `ByzantineConsensus.compute_consensus(proposition)` → (result, confidence)
- `QuorumVerification.approve(action_id, agent_id)` → bool (True if quorum reached)

## Detection Module {#sec:detection-api}

The detection module implements statistical anomaly and drift detection.

**Table: Detection module API: Classes for belief drift and anomaly detection.** {#tab:detection-api}

| Class | Description |
| --- | --- |
| \texttt{DriftDetector} | KL-divergence based belief distribution drift detection. Sliding window comparison with configurable thresholds. |
| \texttt{AnomalyScorer} | Weighted Z-score anomaly scoring for belief state vectors. Calibrated on baseline distribution with configurable feature extractors. |

## Provenance Module {#sec:provenance-api}

The provenance module implements information flow tracking with causal attribution.

**Table: Provenance module API: Classes for belief origin tracking and taint propagation.** {#tab:provenance-api}

| Class | Description |
| --- | --- |
| \texttt{ProvenanceChain} | Linked list of provenance records tracking belief transformations. |
| \texttt{ProvenanceGraph} | DAG structure for complex multi-source belief provenance. Supports transitive queries. |
| \texttt{TaintLabel} | Labels for marking untrusted information sources. Propagates through belief operations. |
| \texttt{CausalAttribution} | Attributes beliefs to original evidence with contribution weights. |

## Sandbox Module {#sec:sandbox-api}

The sandbox module implements belief partitioning for provisional information management.

**Table: Sandbox module API: Classes for belief sandboxing and promotion.** {#tab:sandbox-api}

| Class | Description |
| --- | --- |
| \texttt{SandboxManager} | Manages verified and provisional belief partitions. Enforces TTL expiry and consistency checks. |
| \texttt{BeliefPartition} | Container for beliefs with shared trust properties. Supports batch operations. |
| \texttt{PromotionCriteria} | Configurable criteria for promoting beliefs from provisional to verified. |

## Tripwire Module {#sec:tripwire-api}

The tripwire module implements canary belief monitoring for intrusion detection.

**Table: Tripwire module API: Classes for canary belief monitoring.** {#tab:tripwire-api}

| Class | Description |
| --- | --- |
| \texttt{CognitiveTripwire} | Monitors canary beliefs for unauthorized modifications. Configurable alert severity levels. |
| \texttt{Canary} | Individual canary belief with expected value and tolerance. |
| \texttt{TripwireAlert} | Alert record with severity, timestamp, and drift magnitude. |

## Invariants Module {#sec:invariants-api}

The invariants module implements runtime behavioral constraint checking.

**Table: Invariants module API: Classes for behavioral invariant enforcement.** {#tab:invariants-api}

| Class | Description |
| --- | --- |
| \texttt{InvariantChecker} | Evaluates agent actions against registered invariants. Returns violations with severity. |
| \texttt{RuntimeMonitor} | Continuous monitoring of agent behavior for invariant violations. Supports real-time alerting. |
| \texttt{Invariant} | Declarative invariant specification with predicate and severity. |
