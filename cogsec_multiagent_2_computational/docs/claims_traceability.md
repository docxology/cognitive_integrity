# Claims Traceability Matrix

This document maps the theoretical claims and definitions from the Cognitive Integrity Framework (CIF) manuscript (Part 1 & 2) to their specific concrete implementations in the `cogsec_multiagent_2_computational` codebase. This ensures that every theoretical construct is backed by verified, production-ready code.

## Core Defense Mechanisms

| Manuscript Reference | Concept | Implementation Class | Source File | Test File |
| :--- | :--- | :--- | :--- | :--- |
| **Part 1, Def 5.3** | **Cognitive Firewall** | `CognitiveFirewall` | `src/core/firewall.py` | `tests/core/test_firewall.py` |
| Part 1, Sec 5.2.1 | Injection Detection | `PatternDetector` | `src/core/firewall.py` | `tests/core/test_firewall.py` |
| Part 1, Sec 5.2.1 | Semantic Filtering | `SemanticSimilarityDetector` | `src/core/firewall.py` | `tests/core/test_firewall.py` |
| **Part 1, Def 5.4** | **Belief Sandbox** | `SandboxManager` | `src/core/sandbox.py` | `tests/core/test_sandbox.py` |
| Part 1, Prop 5.2 | Promotion Criteria | `PromotionCriteria` | `src/core/sandbox.py` | `tests/core/test_sandbox.py` |
| **Part 1, Sec 4** | **Trust Calculus** | `TrustCalculus` | `src/core/trust.py` | `tests/core/test_trust.py` |
| Part 1, Thm 4.2 | Bounded Delegation ($\delta^d$) | `TrustCalculus.delegate_trust` | `src/core/trust.py` | `tests/core/test_trust.py` |
| Part 1, Sec 4.2 | Trust Matrix | `TrustMatrix` | `src/core/trust.py` | `tests/core/test_trust.py` |
| **Part 1, Def 5.6** | **Identity Tripwire** | `CognitiveTripwire` | `src/core/tripwire.py` | `tests/core/test_tripwire.py` |
| Part 1, Def 5.6 | Canary Belief | `Canary` | `src/core/tripwire.py` | `tests/core/test_tripwire.py` |
| **Part 1, Thm 5.2** | **Byzantine Consensus** | `ByzantineConsensus` | `src/core/consensus.py` | `tests/core/test_consensus.py` |
| Part 1, Sec 5.4.1 | Weighted Voting | `WeightedByzantineConsensus` | `src/core/consensus.py` | `tests/core/test_consensus.py` |
| **Part 1, Def 6.1** | **Drift Detection** | `DriftDetector` | `src/core/detection.py` | `tests/core/test_detection.py` |
| Part 1, Sec 6.1 | Anomaly Scoring | `AnomalyScorer` | `src/core/detection.py` | `tests/core/test_detection.py` |

## Auxiliary Mechanisms

| Manuscript Reference | Concept | Implementation Class | Source File | Test File |
| :--- | :--- | :--- | :--- | :--- |
| Part 2, Sec 3.2 | Provenance Graph | `ProvenanceGraph` | `src/core/provenance.py` | `tests/core/test_provenance.py` |
| Part 2, Sec 3.2 | Causal Attribution | `CausalAttribution` | `src/core/provenance.py` | `tests/core/test_provenance.py` |
| Part 2, Sec 3.3 | Invariant Checking | `InvariantChecker` | `src/core/invariants.py` | `tests/core/test_invariants.py` |
| Part 2, Sec 3.3 | Runtime Monitor | `RuntimeMonitor` | `src/core/invariants.py` | `tests/core/test_invariants.py` |

## Validation & Experiments

| Manuscript Reference | Experiment | Script | Source Directory | Data Output |
| :--- | :--- | :--- | :--- | :--- |
| Part 2, Sec 5.1 | Attack Surface Analysis | `scripts/run_full_evaluation.py` | `src/evaluation/` | `output/data/attack_surface.json` |
| Part 2, Sec 5.2 | Scalability Benchmarking | `scripts/run_scalability_analysis.py` | `src/evaluation/` | `output/data/scalability_results.json` |
| Part 2, Sec 5.3 | Ablation Studies | `scripts/run_ablation.py` | `src/ablation/` | `output/data/ablation_results.json` |
| Part 2, S03 | Colony Benchmarks | `scripts/run_colony_benchmarks.py` | `src/colony/` | `output/data/colony_scores.json` |

## Notes

- All implementation classes are located in `projects/cognitive_integrity/cogsec_multiagent_2_computational/src/core/`.
- All tests are located in `projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/`.
- Full API documentation for these classes is available in `manuscript/S05_framework_api.md`.
