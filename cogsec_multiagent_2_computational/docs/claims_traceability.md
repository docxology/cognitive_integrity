# Claims Traceability Matrix

This document maps the theoretical claims and definitions from the Cognitive Integrity Framework (CIF) manuscript (Part 1 & 2) to their concrete implementations in the `cogsec_multiagent_2_computational` codebase. Every theoretical construct is backed by tested, production-ready code.


> **Scope.** This matrix maps *concepts* --- Part 1's definitions and theorems ---
> to the classes that implement them. It is not the map from reported *numbers*
> to the artifacts that produce them: that is the reader-side claim registry in
> `src/manuscript/claim_registry.py`, checked by `scripts/verify_claims.py`,
> which binds 171 numeric claims across the results, statistics, ablation,
> sensitivity, Bayesian, gap-analysis, red-team and parametric sections to
> `output/data/`. A number that appears in the manuscript and in neither place
> is unaudited; run `uv run python scripts/verify_claims.py` to check.

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
| **Part 1, Tripwire Alert Condition** | **Identity Tripwire** | `CognitiveTripwire` | `src/core/tripwire.py` | `tests/test_tripwire.py` |
| Part 1, Canary Belief | Canary Belief | `Canary` | `src/core/tripwire.py` | `tests/test_tripwire.py` |
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

## v2.0 Additions

| Manuscript Reference | Concept | Implementation Class/Function | Source File | Test File |
| :--- | :--- | :--- | :--- | :--- |
| Sec 05g | Adversarial Training | `AdversarialTrainer` | `src/redteam/__init__.py` | `tests/test_redteam.py` |
| Sec 05g | Nash-Equilibrium Projection | `NashEquilibriumEstimator` | `src/redteam/__init__.py` | `tests/test_redteam.py` |
| Sec 05h | Attack Generation (Ω1-Ω5) | `AdversarialGenerator` | `src/redteam/generator.py` | `tests/test_redteam.py` |
| Sec 05h | Mutation Testing (12 operators) | `AttackMutator` | `src/redteam/generator.py` | `tests/test_redteam.py` |
| Sec 05g/05h | AT convergence estimators | `natural_gradient_at_step`, `geometric_convergence_projection`, `convergence_round_estimate` | `src/redteam/convergence.py` | `tests/test_redteam_convergence.py` |
| Sec 05h | Mutation-operator evasion sweep | `flagged_payloads`, `run_evasion_sweep`, `OperatorEvasion` | `src/redteam/evasion.py` | `tests/test_redteam.py` |
| "Defense composition algebra" (25 verification checks) | Lattice / Monoidal / F-Algebra / Operad / Enriched / Kan / Monad / Lens | `run_all_verifications`, `serialize_verification_results` | `src/formal/category_theory_advanced.py` | `tests/test_category_theory_advanced.py` |
| Composer web-UI backend | Aggregated category-theory + module data | `get_composer_data` | `src/visualization/composer_data.py` | `tests/test_composer_data.py` |

Note: the mutation-operator evasion-rate figures in Sec 05h
(`manuscript/05h_redteam_evaluation.md`) are produced by
`scripts/run_redteam.py --seed 42` over the real 950-sample `AttackCorpus`,
de-duplicated and scored against the real `CognitiveFirewall`, and are pinned
by `tests/test_redteam.py` (evasion-sweep and manuscript-consistency tests) so
the manuscript cannot drift from the data. The section's original
`campaign.py`/`evasion_probe.py`/`scorer.py`/`report.py` campaign-orchestration
modules remain unimplemented; the published table reports the implemented
`AttackMutator` sweep only (via the `src/redteam/evasion.py` harness).

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
