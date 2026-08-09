# Round 7 Audit — Part 2 Computational

Date: 2026-08-08
Scope: `cogsec_multiagent_2_computational/`, including `src/`, `tests/`, `scripts/`, `manuscript/`, `docs/`, and committed data artifacts. No credentials or secrets were read or retained.

## Findings

| ID | Severity | Evidence | Finding / why it matters | Status |
|---|---|---|---|---|
| P2-R7-01 | MAJOR | `manuscript/04_experimental_setup.md:137`, `manuscript/05e_bayesian_uncertainty.md:39`, `manuscript/06_discussion.md:134`, `manuscript/07_conclusion.md:35`; `output/data/colony_results_single_seed.json` | The published 56.1% emergent-misalignment value was a single seed (seed 46). The authoritative 30-seed artifact reports a 74.2933% mean and 25.4839% FPR. The single-seed result was not an appropriate headline estimate. | implemented: prose now uses the 30-seed mean and explicitly identifies the single-seed number as non-headline. |
| P2-R7-02 | MAJOR | `manuscript/07_conclusion.md:21`; `manuscript/05e_bayesian_uncertainty.md:33` | The conclusion reported a 44.8% multi-seed estimate with HDI [41.3%, 48.3%], but the representative Beta(46,56) row in the Bayesian section gives [35.5%, 54.7%]. The two statements were internally inconsistent. | implemented: conclusion now reports the interval used by the Bayesian table and labels the estimate as representative. |
| P2-R7-03 | MEDIUM | `src/core/consensus.py:248` | `QuorumVerification` used `max_byzantine or default`, so an explicit valid `max_byzantine=0` silently became the default budget. This changed quorum semantics for deployments with no Byzantine tolerance budget. | implemented: explicit `None` check, non-negative validation, positive-agent validation; two no-mock regression tests added. |
| P2-R7-04 | MEDIUM | `manuscript/07_conclusion.md:29` vs `output/data/ablation_results.json` | Conclusion said the top three harmful removals accounted for about 82%; the artifact-backed calculation and `05b` claim registry give 80%. | implemented: corrected to 80%. |
| P2-R7-05 | MEDIUM | `manuscript/05e_bayesian_uncertainty.md:39` | Colony seed-sweep mean was presented as a Beta-Binomial posterior with `k=56,n=100`, conflating a single-seed Bernoulli-like count with a 30-seed bootstrap summary. | implemented: row now identifies the 30-seed mean and points to the bootstrap CI rather than inventing a Beta posterior. |
| P2-R7-06 | MEDIUM | `src/redteam/__init__.py:346-376`; prior `docs/RED_TEAM_ASSESSMENT.md:47-49` | Real-mode adversarial-training thresholds are refined but are not threaded into the firewall decision function; real-mode hardening is therefore a structural no-op. | scoped, per lane instructions: author architecture decision required. Acceptance: threshold updates must alter the injected detector configuration, followed by measured nonzero/zero delta reporting and regenerated 05g artifacts. |
| P2-R7-07 | MEDIUM | `src/statistics/analysis_runner.py` and `output/data/statistical_results.json` | Cohen's d / H1-style comparisons use a simulated control distribution. This is now provenance-labeled, but the resulting very large effect size must not be presented as a real-world control comparison. | scoped/cleared by existing provenance disclosure; acceptance: retain explicit simulated-control labels in artifact and prose, or replace with a genuine pre-registered control. |
| P2-R7-08 | MINOR | `scripts/run_ablation.py:54-57` | Ablation writer does not add the provenance metadata used by sibling artifact writers, making the artifact less self-describing and more vulnerable to stale-data confusion. | deferred: acceptance is a targeted writer update plus artifact regeneration and claims/manuscript gates; not changed because the lane rule forbids unnecessary committed-artifact regeneration. |
| P2-R7-09 | MINOR | `tests/test_claim_registry.py:63-67`, `output/data/llm_demo_results.json` | Four LLM claims remain environment-gated and unbacked when Ollama is not run. This is known and CI-pinned, not a newly introduced mismatch. | cleared/pinned: exactly four UNBACKED, zero MISMATCH, zero NOT_FOUND; acceptance is the existing CI assertion and an explicit LLM rerun before those claims are treated as measured. |

## Review and implementation summary

Reviewed the shared frame and Part 2 lane brief, then inspected the authoritative core modules (`firewall`, `trust`, `consensus`, `sandbox`, `tripwire`, `provenance`, `detection`, `invariants`), evaluation runner, adversarial-training/red-team modules, scripts, claim registry/tests, provenance/reproduction docs, manuscript sections, and data artifacts. The corpus generator was executed directly: 950 samples, with category totals matching the manuscript's grouped totals (500 prompt injection, 200 trust exploitation, 150 belief manipulation, 100 coordination).

Implemented:

- Corrected quorum handling for explicit `f=0` and invalid agent counts.
- Added two real regression tests in `tests/test_consensus.py`.
- Reconciled emergent-misalignment prose to the 30-seed artifact and removed the single-seed headline usage.
- Removed the invalid colony Beta-Binomial representation.
- Reconciled the conclusion's Bayesian interval and ablation-share wording.

No output artifact was regenerated. No mathematical theorem or proof was rewritten. No AGENTS.md or TODO_DEEP_SCOPING.md was modified.

## Gate results

Baseline and post-change measurements:

- Full pytest baseline: `3354 passed, 3 skipped`.
- Full pytest with coverage: `3354 passed, 3 skipped`; total coverage `96.96%`; required 90% reached.
- Focused regression: `tests/test_consensus.py`: `42 passed` (40 before the two additions, 42 after).
- Ruff: `All checks passed!`.
- Manuscript verifier: all checks passed; it reports 51 unused bibliography entries as a warning.
- Claims verifier after changes: `163 claims: 159 MATCH, 0 MISMATCH, 0 NOT_FOUND, 4 UNBACKED`. The nonzero exit is expected for the four pinned, skipped Ollama claims and is the lane's known CI contract.

The full suite and coverage run completed after the code change. The second full-suite ordering-stability run completed before synchronization: `3356 passed, 3 skipped` in 106.38s. The count increased by two because of the new regression tests; no ordering-dependent failures occurred.

## Deferred acceptance criteria

1. Real-mode AT coupling: wire refined thresholds into the actual detector, measure adaptive and original-corpus rates, regenerate only the affected 05g artifact/table, and verify claims, manuscript, tests, and provenance.
2. Ablation provenance: add deterministic `data_origin`, `source_script`, seed, and generator metadata to `run_ablation.py`; regenerate `ablation_results.json`; rerun all Part 2 gates.
3. Simulated-control statistical claims: either retain and visibly label all simulated-control comparisons, or replace them with an actual registered control design; do not call the current Cohen's d a real-world effect.
4. LLM arm: run the documented Ollama-backed evaluation with the required model and update the four pinned claims only after the result artifact is independently verified.
5. Existing known items from the lane brief (P2-5 legacy full-evaluation regeneration, P2-F5b import refactor, P2-F11 architecture stability field, P2-F6 memory formula) remain out of scope.
