\newpage

# Supplementary: Framework API Reference {#sec:framework-api}

## Overview

This supplementary material documents the core framework modules that implement the theoretical constructs from Part 1 \cite{friedman2026cogsec1}. The complete source code is available at \url{https://github.com/docxology/cognitive_integrity} (DOI: 10.5281/zenodo.22134546).

> **Cross-paper reading guide.**
> • For **formal definitions and theorems** of every construct referenced below, see Part 1 (DOI: 10.5281/zenodo.22134544) §3–§5.
> • For **deployment guidance** on configuring these APIs in production (operator posture, monitoring, incident response), see Part 3 (DOI: 10.5281/zenodo.22134548) §5–§6.
> • For **domain-specific application** of these mechanisms across ten critical sectors (infrastructure, supply chain, cyber, biowarfare, information ecosystems, etc.), see Part 3's applied domains and cross-domain analysis.
> • A parallel **functional-style API** (free-function form rather than class form) is documented in §S09 Functional API of this paper; choose whichever style fits your integration context.
> • Concrete **pseudocode** for every algorithm in this API appears in §S07 Algorithm Pseudocode.

## Trust Module {#sec:trust-module-api}

The trust module implements bounded trust delegation with configurable decay.

Table: Trust module API: Core classes for trust computation and management. {#tab:trust-api}

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

Table: Firewall module API: Classes for message classification and threat detection. {#tab:firewall-api}

| Class | Description |
| --- | --- |
| \texttt{CognitiveFirewall} | Three-tier classifier (ACCEPT/QUARANTINE/REJECT) using dual thresholds, at their operational default $\tau_1 = 0.8$ (REJECT, hard-reject; inputs scoring above this are blocked outright) and operational default $\tau_2 = 0.5$ (QUARANTINE; inputs scoring in $(\tau_2, \tau_1]$ are sandboxed). Combines pattern matching, semantic analysis, and anomaly detection. |
| \texttt{PatternDetector} | Heuristic pattern matching with 13 injection patterns and 7 suspicious indicators. Weighted scoring based on pattern severity. |
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

Table: Consensus module API: Classes for Byzantine-tolerant multiagent decisions. {#tab:consensus-api}

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

Table: Detection module API: Classes for belief drift and anomaly detection. {#tab:detection-api}

| Class | Description |
| --- | --- |
| \texttt{DriftDetector} | KL-divergence based belief distribution drift detection. Sliding window comparison with configurable thresholds. |
| \texttt{AnomalyScorer} | Weighted Z-score anomaly scoring for belief state vectors. Calibrated on baseline distribution with configurable feature extractors. |

## Provenance Module {#sec:provenance-api}

The provenance module implements information flow tracking with causal attribution.

Table: Provenance module API: Classes for belief origin tracking and taint propagation. {#tab:provenance-api}

| Class | Description |
| --- | --- |
| \texttt{ProvenanceChain} | Linked list of provenance records tracking belief transformations. |
| \texttt{ProvenanceGraph} | DAG structure for complex multi-source belief provenance. Supports transitive queries. |
| \texttt{TaintLabel} | Labels for marking untrusted information sources. Propagates through belief operations. |
| \texttt{CausalAttribution} | Attributes beliefs to original evidence with contribution weights. |

## Sandbox Module {#sec:sandbox-api}

The sandbox module implements belief partitioning for provisional information management.

Table: Sandbox module API: Classes for belief sandboxing and promotion. {#tab:sandbox-api}

| Class | Description |
| --- | --- |
| \texttt{SandboxManager} | Coordinates the belief state, promotion criteria and expiry: enforces per-belief TTL (\texttt{cleanup\_expired}, \texttt{extend\_ttl}) and the provisional-store cap from \texttt{SandboxConfig}. |
| \texttt{BeliefState} | Holds the two partitions as belief dictionaries; supports add, promote, demote and partition lookup. |
| \texttt{BeliefPartition} | Two-member enum (\texttt{VERIFIED}, \texttt{PROVISIONAL}) tagging which partition a belief occupies; returned by \texttt{BeliefState.get\_partition}. |
| \texttt{PromotionCriteria} | Configurable criteria for promoting beliefs from provisional to verified. |

## Tripwire Module {#sec:tripwire-api}

The tripwire module implements canary belief monitoring for intrusion detection.

Table: Tripwire module API: Classes for canary belief monitoring. {#tab:tripwire-api}

| Class | Description |
| --- | --- |
| \texttt{CognitiveTripwire} | Monitors canary beliefs for unauthorized modifications. Configurable alert severity levels. |
| \texttt{Canary} | Individual canary belief with expected value and tolerance. |
| \texttt{TripwireAlert} | Alert record with severity, timestamp, and drift magnitude. |

## Invariants Module {#sec:invariants-api}

The invariants module implements runtime behavioral constraint checking.

Table: Invariants module API: Classes for behavioral invariant enforcement. {#tab:invariants-api}

| Class | Description |
| --- | --- |
| \texttt{InvariantChecker} | Evaluates agent actions against registered invariants. Returns violations with severity. |
| \texttt{RuntimeMonitor} | Continuous monitoring of agent behavior for invariant violations. Supports real-time alerting. |
| \texttt{Invariant} | Declarative invariant specification with predicate and severity. |
