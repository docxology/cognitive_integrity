# Claims Traceability Matrix

This document maps the theoretical claims and definitions from the Cognitive Integrity Framework (CIF) manuscript (Part 1 & 2) to their concrete implementations in the `cogsec_multiagent_2_computational` codebase. Every theoretical construct is backed by tested, production-ready code.

## Core Defense Mechanisms

| Manuscript Reference | Concept | Implementation Class | Source File | Test File |
| :--- | :--- | :--- | :--- | :--- |
| **Part 1, Def 5.3** | **Cognitive Firewall** | `CognitiveFirewall` | `src/core/firewall.py` | `tests/test_firewall.py` |
| Part 1, Sec 5.2.1 | Firewall Configuration | `FirewallConfig` | `src/core/firewall.py` | `tests/test_firewall.py` |
| Part 1, Sec 5.2.1 | Injection Detection | `PatternDetector` | `src/core/firewall.py` | `tests/test_firewall.py` |
| Part 1, Sec 5.2.1 | Semantic Filtering | `SemanticSimilarityDetector` | `src/core/firewall.py` | `tests/test_firewall.py` |
| Part 1, Sec 5.2.1 | Text Embedding | `TFIDFEmbedder` | `src/core/firewall.py` | `tests/test_firewall_extended.py` |
| **Part 1, Def 5.4** | **Belief Sandbox** | `SandboxManager` | `src/core/sandbox.py` | `tests/test_sandbox.py` |
| Part 1, Prop 5.2 | Promotion Criteria | `PromotionCriteria` | `src/core/sandbox.py` | `tests/test_sandbox.py` |
| Part 1, Prop 5.2 | Belief State Management | `BeliefState` | `src/core/sandbox.py` | `tests/test_sandbox.py` |
| **Part 1, Sec 4** | **Trust Calculus** | `TrustCalculus` | `src/core/trust.py` | `tests/test_trust.py` |
| Part 1, Thm 4.2 | Bounded Delegation ($\delta^d$) | `TrustCalculus.delegate_trust` | `src/core/trust.py` | `tests/test_trust.py` |
| Part 1, Sec 4.2 | Trust Matrix | `TrustMatrix` | `src/core/trust.py` | `tests/test_trust.py` |
| Part 1, Sec 4.2 | Reputation Tracking | `ReputationTracker` | `src/core/trust.py` | `tests/test_trust.py` |
| **Part 1, Def 5.6** | **Identity Tripwire** | `CognitiveTripwire` | `src/core/tripwire.py` | `tests/test_tripwire.py` |
| Part 1, Def 5.6 | Canary Belief | `Canary` | `src/core/tripwire.py` | `tests/test_tripwire.py` |
| Part 1, Def 5.6 | Tripwire Alert | `TripwireAlert` | `src/core/tripwire.py` | `tests/test_tripwire.py` |
| **Part 1, Thm 5.2** | **Byzantine Consensus** | `ByzantineConsensus` | `src/core/consensus.py` | `tests/test_consensus.py` |
| Part 1, Sec 5.4.1 | Weighted Voting | `WeightedByzantineConsensus` | `src/core/consensus.py` | `tests/test_consensus.py` |
| Part 1, Sec 5.4.1 | Quorum Verification | `QuorumVerification` | `src/core/consensus.py` | `tests/test_consensus.py` |
| **Part 1, Def 6.1** | **Drift Detection** | `DriftDetector` | `src/core/detection.py` | `tests/test_detection.py` |
| Part 1, Sec 6.1 | Anomaly Scoring | `AnomalyScorer` | `src/core/detection.py` | `tests/test_detection.py` |

## Auxiliary Mechanisms

| Manuscript Reference | Concept | Implementation Class | Source File | Test File |
| :--- | :--- | :--- | :--- | :--- |
| Part 2, Sec 3.2 | Provenance Chain (DAG) | `ProvenanceChain` | `src/core/provenance.py` | `tests/test_provenance.py` |
| Part 2, Sec 3.2 | Provenance Graph Analysis | `ProvenanceGraph` | `src/core/provenance.py` | `tests/test_provenance.py` |
| Part 2, Sec 3.2 | Taint Labels | `TaintLabel` | `src/core/provenance.py` | `tests/test_provenance.py` |
| Part 2, Sec 3.2 | Causal Attribution | `CausalAttribution` | `src/core/provenance.py` | `tests/test_provenance.py` |
| Part 2, Sec 3.3 | Invariant Checking | `InvariantChecker` | `src/core/invariants.py` | `tests/test_invariants.py` |
| Part 2, Sec 3.3 | Runtime Monitor | `RuntimeMonitor` | `src/core/invariants.py` | `tests/test_invariants.py` |

## Validation & Experiments

| Manuscript Reference | Experiment | Script | Source Directory | Data Output |
| :--- | :--- | :--- | :--- | :--- |
| Part 2, Sec 5.1 | Attack Surface Analysis | `scripts/run_full_evaluation.py` | `src/evaluation/` | `output/data/full_evaluation_results.json` |
| Part 2, Sec 5.2 | Multi-Seed Stability | `scripts/run_multi_seed.py` | `src/statistics/` | `output/data/multi_seed_results.json` |
| Part 2, Sec 5.3 | Ablation Studies | `scripts/run_ablation.py` | `src/ablation/` | `output/data/ablation_results.json` |
| Part 2, S03 | Colony Benchmarks | `scripts/run_colony_benchmarks.py` | `src/colony/` | `output/data/colony_results.json` |
| Part 2, Sec 5.2 | Cross-Validation | `scripts/run_cross_validation.py` | `src/statistics/` | `output/data/cross_validation_results.json` |

## Notes

- All implementation classes are in `src/core/`.
- All tests are in `tests/` (flat directory, no `core/` subdirectory).
- Architectures (Claude Code, AutoGPT, CrewAI, LangGraph) are in `src/architectures/`.
- Full API documentation is available in `manuscript/S05_framework_api.md`.
