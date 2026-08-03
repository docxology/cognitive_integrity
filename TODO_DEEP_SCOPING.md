# Cognitive Integrity Program — Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-03
**Auditor:** Hermes Agent (hostile red-team review — 3 parallel subagent audits of Parts 1/2 + lead pass on Part 3, CLI/claims/provenance/statistics layers; every MAJOR re-verified by lead with live probes)
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified complete at HEAD `993d7c0` · `OPEN` tracked forward (author/agent) · `NEW` filed this pass
**Owner conventions:** `[A]` author/subject-matter decision · `[H]` Hermes-agent scoped engineering item · `[H+A]` both

---

## Executive Summary — measured 2026-08-03 (fresh runs, not hand-pinned)

| Paper | Tests (pytest) | Coverage (`--cov-fail-under=90`) | Ruff | Mypy | Manuscript verify | Claims gate |
|-------|----------------|----------------------------------|------|------|-------------------|-------------|
| 1 (Theory) | 381 passed / 0 skipped | 96.18% | 0 violations | N/A (no `[tool.mypy]`) | PASS (6 checks) | N/A |
| 2 (Computational) | 3338 passed / 3 skipped | 97.18% (branch) | 0 violations | **clean** (P2-13 fixed) | PASS (10 checks) | 163 claims: 159 MATCH / 0 MISMATCH / 0 NOT_FOUND / 4 UNBACKED (env-gated LLM) — now **wired into CI** (P2-4) |
| 3 (Practical) | 882 passed / 0 skipped | 99.69% | 0 violations | N/A | PASS (7 checks) | N/A |

All suites green on current deps; all three `verify_manuscript.py` runs PASS; `make check-real-data` guard satisfied (5 tracked evidence files present, 4 declare `data_origin: real_pipeline`). Prior documented counts (TODO 07-06: 350/2281/848; handoff 08-01: 355/3334/882; SKILL.md "2100+"; CI comment "2026-07-27: 96.42/95.40/94.72") are all stale — the numbers above are authoritative for this review.

This pass filed **11 MAJOR · 24 MEDIUM · 24 MINOR · 2 LATENT** findings (Phase 4) and carries the author-level OPEN ledger forward from `cogsec_multiagent_2_computational/docs/RED_TEAM_ASSESSMENT.md` (Phase 5).

### Implementation pass (2026-08-03, part 2) — fixed since the review

The hostile-red-team findings were implemented and gate-verified at commit
`<HEAD>` (this follow-up session). Resolved (with tests):

- **P1-1…P1-22 (Part 1)** — all implemented: canonical-injection regex + firewall
  quarantine-on-pattern, invariants fail-closed, artifact determinism, ROC
  degenerate-AUC, data-driven detection figure, weighted consensus, empty-portfolio
  semantics, trust total-depth decay, verification logging, sandbox promotion/cap,
  provenance JSON-serialization + scale doc, monotonic analytic scalability.
- **P2-1** (sensitivity `parametric_simulation` origin + provenance block),
  **P2-2** (LLM-fallback honest `measurement_mode` + counter), **P2-3** (ablation
  ordering corrected + pinning test), **P2-4** (claims gate wired into CI),
  **P2-13** (mypy clean), **P2-16** (RED_TEAM_ASSESSMENT wording), **P2-21**
  (Makefile comment), **P2-25/P2-30** (version drift in AGENTS/README), **P2-29**
  (CI mypy comment).
- **P3-1** (figure-script `sys.exit`), **P3-2** (style check now honest; the one real
  hyperbole reworded), **P3-3** (belief `id` KeyError).

Still **OPEN** (documented in Phase 5 backlog): the remaining Part-2 MEDIUMs
(P2-5…P2-12, P2-14–P2-15, P2-17–P2-19) and the MINOR batch (P2-20, P2-22–P2-24,
P2-26–P2-28, P2-31–P2-34), plus the author-level theory items. P2-19/M3
("z=1.96 t-distribution") does **not** reproduce at HEAD — no `1.96`/`_Z95` exists
in the statistics core (intervals come from bootstrap), so it is treated as
already-resolved/superseded.

---

## Phase 3 — Completed / Closed (verified at HEAD 993d7c0, 2026-08-03)

Items below were previously open in this file or sibling audits; each was **verified in source/tests/artifacts** this pass (subagent read-through + lead spot checks + real suite runs). No rework needed.

### Paper 1 (`cogsec_multiagent_1_theory`) — completed ledger

| ID (old) | Issue | Verification |
|----------|-------|--------------|
| C-1 | `from __future__ import annotations` trapped in docstring (6 modules) | DONE — placement correct in all 14 src modules + `visualization/` |
| C-2 | `\newtheorem{remark}` dropped by pandoc | DONE — trailing-comment workaround in `preamble.md` holds; PDF compiles |
| C-3 | Missing bib entries (`friston2010action`, `parr2019generalised`) | DONE — present; `verify_manuscript.py` Citations PASS |
| H-1 | `callable` lowercase annotation | DONE — `Callable` used; ruff clean |
| H-2 | Per-module coverage gaps | DONE — total 96.35% ≥ 90 gate; no module below gate in measured run |
| H-4/H-6 | Font/LaTeX warnings (TU/lmr/m/scit) | PARTIAL — still 39 warnings in suite, incl. missing glyphs (Times New Roman: SUBSCRIPT FIVE U+2085, WARNING SIGN U+26A0) in `comprehensive_taxonomy.py:369` figure render — cosmetic; carry as MINOR P1-21 |
| H-7 | Stale validation report | DONE — `verify_manuscript.py` regenerates on each run; PASS |
| M-1…M-10 | Ruff F403/E501/imports, bare excepts, config self-DOI, PAI path, ROC labels, hypothesis dep | DONE — ruff 0 violations; `detection.py` excepts now typed; verified |
| L-1 | `_calibrated` flag set but never read | DONE — now read in `detection.py:174-178 is_anomalous` with regression tests |
| L-3 | `run_all()` calls `sys.exit()` | DONE — `verification.py:207-242` returns bool; `scripts/verify_manuscript.py:35` owns exit; tested |
| L-4 | Missing `__all__` in `visualization/__init__.py` | DONE — present |
| L-5 | Mixed import style in tests | DONE — consistent |
| L-7 | `10_limitations.md` has no slides | SUPERSEDED — slide decks now render (with beamer warnings) — see Phase 5 render item |
| H-5 | `verification.py run_all()` untested | DONE — tested |
| M-11 | `roc_curves.py` measured-data path untested | DONE — `test_visualization.py:370-400` |
| L-2 (07-13 sprint) | `-> None` on 38 methods | DONE |

### Paper 2 (`cogsec_multiagent_2_computational`) — completed ledger

| ID (old) | Issue | Verification |
|----------|-------|--------------|
| C-01/C-02 | `src/__main__.py` broken constructor/method | DONE — `ExperimentRunner(config=ExperimentConfig(seed=...))` + `run_full_matrix`; CLI smoke-tested |
| H-01…H-03 | Coverage gaps (composable.py, llm_evaluator.py) | DONE — 97.16% total; `composable.py` removed (superseded by `composition/`), llm_evaluator covered |
| H-04 | metagpt/camel missing vs "6 architectures" | DONE — README now declares 4; `architectures/` holds exactly 4 adapters |
| H-05 | `submit_vote()` Liskov overrides | DONE — resolved |
| H-06 | 150 mypy errors | PARTIAL — 1 error remains (`redteam/__init__.py:341`) — see MEDIUM P2-13 |
| M-01/M-20 | 247 ruff violations; 20 modules <90% | DONE — ruff 0 violations; coverage floor met |
| M-02…M-04, L-01…L-06 | save_figure Path, lazy import, REPRODUCE.md, SKILL counts, hyperbole, PAI paths | DONE — verified (SKILL count itself now stale again — see MINOR P2-17) |
| S1/S2 (THERMO 07-22) | Forked CIF core; rate-semantics schism (`composable.py` max vs algebra OR) | PARTIAL — S2 DONE (`composable.py` deleted; `algebra.py` series/parallel/majority formulas consistent, probe-checked). S1 **still open**: Part 1 firewall `injection_threshold=0.7` vs Part 2 `core/firewall.py:33` `0.8` — see MEDIUM P2-14 |
| S3 (THERMO) | >1k-line modules | DONE — `composable.py` gone; remaining modules ≤ ~1k |
| S4 (THERMO) | Paper 3 dual API stubs | DONE — `src/__init__.py` hosts real lightweight classes; module classes distinct and exported |
| 07-06 sprint items | `__main__.py`, coverage, ruff I/F, mypy, roc trapz, REPRODUCE.md, PAI, "perfect detection" | DONE — verified |
| RED_TEAM M2 / MED-3 | Non-deterministic timestamps in colony/scalability artifacts | DONE — `generated_utc: null`; artifacts deterministic |
| RED_TEAM MED-4 | Stale/unsupported provenance fields | DONE — regenerated with honest `provenance` block (see MAJOR P2-1 for the residual labeling tension) |
| RED_TEAM L4 | §05g "Key Finding 3/4" empirical-sounding | DONE — now "by construction of the design model" |
| 07-26 audit REPRO-01 | `make all` overwriting real evidence | DONE — `make data` removed; `check-real-data` guard wired; `synthetic-data` isolated to `output/data_synthetic/` |

### Paper 3 (`cogsec_multiagent_3_practical`) — completed ledger

| ID (old) | Issue | Verification |
|----------|-------|--------------|
| C-1/C-2 | "Papers 1–4" framing; orphan `friedman2026cogsec4` | DONE — three-part framing throughout; bib entry handled |
| H-1…H-6 | Quorum Verification clarification; Def 5.3→5.2; Part-4 residual in `__init__.py`; posture/deployment coverage; tight_layout | DONE — verified; 99.69% coverage; `07_domain_coverage_figure.py` fine |
| M-1…M-11 | numpy import scope; dead `plt.Circle`; Trade Wars 1×1 note; §10 renumber; self-cites; domain content tests; E501 ignores; bib comments; S01 notation | DONE — verified; `test_applications.py` now asserts pattern totals (5/2/3), mechanism row totals, and §10.1/§10.4 table parity |
| L-1…L-10 | identity `merged_from` docstring; return annotations; domain content check; attack-pattern sum test; AGENTS test-file count; README status; pyproject ignores; self-citation; `\cref` to supplement | DONE — verified |
| M-6 (old) | test_applications existence-only | DONE — content checks now present |

### Cross-paper — completed ledger
- Series framing "Parts 1–4" → "Parts 1, 2, 3+4" in all `references.bib` files and READMEs — DONE.
- Version reconciliation Part 1=1.1 / Parts 2,3=1.0 in `config.yaml` + `pyproject.toml` — DONE (but see MINOR P2-18, P2-19, P1-22 for residual README/AGENTS/SKILL version drift).
- Part 2 claims gate: KNOWN_UNRECONCILED now exactly the 4 env-gated LLM claims — verified in `tests/test_claim_registry.py:63-70`.

---

## Phase 4 — New findings from the 2026-08-03 hostile red-team review

### Major (11)

**P2-1 | MAJOR | `output/data/sensitivity_results.json` (+ `scripts/run_sensitivity_analysis.py`, `src/statistics/sensitivity.py:294-330`) — `data_origin: "real_pipeline"` stamped on closed-form quadratic response-surface data with no disclosure.**
Evidence: `sensitivity_results.json` carries `data_origin: real_pipeline` + `source_script` + `generated_by`, but its producer is `make_default_evaluate_fn` — `rate = 0.85 + Σ -2.0·(v-opt)² + rng.normal(0, 0.005)` (a hand-tuned quadratic model, no measured pipeline). Unlike `statistical_results.json`, it has **no nested `provenance` block** disclosing this. Any machine reader (e.g. `src/evaluation/baselines.py:1368-1384`, which refuses to plot anything not stamped `real_pipeline`) treats synthetic numbers as measured. Why: data-integrity break against the project's own "never stamp `data_origin: real_pipeline` on closed-form" guardrail. Fix: introduce a distinct `parametric_simulation` (or `closed_form`) origin value; keep the anti-clobber preservation marker keyed on a separate field; add a provenance-disclosure block like `statistical_results.json`'s.

**P2-2 | MAJOR | `src/evaluation/runner.py:414-418, 518` — `measurement_mode="llm"` stamped even when the LLM path silently fell back to parametric/pipeline.**
Evidence: `_simulate_detection` catches `(ConnectionError, RuntimeError)` from the LLM system and "falls through to Mode 1 or Mode 2", but `run_single_llm` unconditionally sets `measurement_mode="llm"` at line 518. With Ollama down, every cell is scored by the fallback yet published as an LLM measurement. Why: provenance lie in the artifact (the very class the 19332f3 provenance commit was built to prevent). Fix: track actual mode per sample (e.g. `llm_fallback=True` counter) and set `measurement_mode="parametric"`/`"real"` when zero samples ran through the LLM; add a regression test with a raising stub.

**P2-3 | MAJOR | `manuscript/05_results.md:184` vs `output/data/ablation_results.json` — component-hierarchy claim omits the second-largest ablation delta.**
Evidence (probe-verified against tracked artifact): data deltas are detection −0.051, **trust_calculus −0.020**, firewall/invariants/tripwire all −0.010. Prose: "Detection … largest marginal loss (≈ −0.051), **followed by Tripwires (≈ −0.011), Invariants (≈ −0.010), and Firewall (≈ −0.009)**" — trust calculus (−0.020, second) is dropped entirely and the tied triple is mis-stated as distinct values. The claim is unregistered, so the claims gate cannot catch it (gate passes 159 MATCH). Why: published prose contradicts the paper's own tracked evidence on a named "Component hierarchy" claim. Fix: correct the ordering (Detection → Trust Calculus → Firewall/Invariants/Tripwires tie at −0.010) or register the claim; add a content test pinning the ordering.

**P1-1 | MAJOR | `src/firewall.py:48,74` — flagship injection regex cannot match the canonical injection phrase; firewall detects 0% of its own test corpus.**
Evidence (live probe): `INJECTION_PATTERNS[0] = r"ignore\s+(previous|all|above)\s+instructions?"` — the alternation allows exactly one word between "ignore" and "instructions", so "Ignore **all previous** instructions" (the single most famous injection string in the literature, and the first message of the project's own corpus at `src/data_generation.py:44`) scores **0.00** and is classified **ACCEPT**. Committed `detection_results.json` shows Firewall prompt_injection rate 0.0; the ROC sweep can only reach TPR 0.25. Why: the paper's central defense mechanism demonstrably fails on the canonical attack, baked into committed evidence and figures. Fix: multi-token optional alternation (e.g. `ignore\s+(?:all\s+|the\s+)?(?:previous|above)\s+instructions?`), add the canonical phrase to corpus + tests.

**P1-2 | MAJOR | `src/invariants.py:202,210,220,232` — security invariants fail OPEN on missing context fields.**
Evidence (live probe): INV-1 `ctx.get("code_trusted", True)`, INV-2 `ctx.get("contains_secrets", False)`, INV-3 `ctx.get("has_permission", True)`, INV-4 `ctx.get("tool_output_verified", True)` — `check_all({"action": "execute_code"})` → **no violations**; same for `write_file` to a system path and `use_tool_result`. Contradicts the repo's own "Fail-Safe Defaults — unknown inputs treated as untrusted" principle (src/AGENTS.md). Why: a monitoring integration that omits the security fields silently permits untrusted code execution / credential exfiltration / system writes. Fix: reverse the defaults (unknown → untrusted/unverified/no-permission); add missing-field tests.

**P1-3 | MAJOR | `src/data_generation.py:89,196-201` — committed experimental data is not reproducible: 2 of 6 tracked artifacts cannot be regenerated byte-identically.**
Evidence: `detection_results.json` metadata writes `"timestamp": datetime.now().isoformat()` while the **tracked** file has `"timestamp": null` (committed artifact produced by different/stale code — current code cannot produce it); `scalability_results.json` uses wall-clock `time.time()` for `consensus_latency_ms`. Regeneration hashes differ for both (the other 4 artifacts match). Why: pipeline determinism contract violated; committed evidence predates the generating code (code↔artifact provenance break). Fix: pin timestamps to a fixed value/None in artifact writers; use an analytic latency model; add a two-run byte-equality test.

**P1-4 | MAJOR | `src/visualization/roc_curves.py:65-84` + `output/figures/data/roc_results.json` — measured ROC curve is degenerate; displayed AUC = 0.000 contradicts the paper's AUC claims and the figure's own caption.**
Evidence: measured data has FPR ≡ 0 across all 20 thresholds (benign corpus never triggers); trapezoidal AUC on zero-FPR-width returns **0.0**; the figure labels the firewall curve "Cognitive Firewall (Measured, AUC=0.000)" while manuscript 06:419 claims "AUC > 0.84" and 06:67 says curves are "Theoretical, not empirical" (the firewall curve is not labeled so). Why: figure-integrity defect in a published figure; a perfect-FPR classifier is displayed as AUC 0.000. Fix: detect degenerate FPR and compute AUC by the conventional (0,0)→(0,TPR) segment or a rank-based method; reconcile legend/caption.

**P1-5 | MAJOR | `src/visualization/detection_results.py:66-72 vs 222` — detection figure contradicts itself: Panel A shows firewall 0%, Panel D shows 78%, and "Full CIF" is identical to "Firewall Only".**
Evidence: Panel A reads `detection_results.json` where the generator writes identical rates for Firewall Only and Full CIF (`data_generation.py:93-97,131-132`) and all are 0.0 (see P1-1); Panel D uses hard-coded `[0.0, 0.78, 0.65, 0.82, 0.94]` plus a fabricated "Pareto frontier"; the test renders with fabricated data (firewall 0.85) that never matches committed artifacts. Why: same mechanism shown at 0% and 78% in one figure; figure not a faithful rendering of its data. Fix: compute Panel D from the JSON; make Full CIF differ from Firewall Only; add a data-consistency test against committed artifacts.

**P1-6 | MAJOR | `src/consensus.py:270-338, 492-560` — Weighted/Combined "consensus" decisions ignore the weights entirely.**
Evidence (live probe): `WeightedByzantineConsensus` does not override `compute_consensus`; 5 votes with `trust_weight=0.01` each and belief 0.9 → **ACCEPT** (plain majority counting). Weights appear only in the separate `get_weighted_average` accessor. Class docstrings and src/AGENTS.md promise "trust-weighted voting"; `test_consensus.py:218-235` calls `compute_consensus` and makes **no assertion**. (Same defect class confirmed in Part 2 `src/core/consensus.py` — see MEDIUM P2-6.) Why: the advertised capability (trusted agents dominate decisions) does not exist in the decision path. Fix: override `compute_consensus` to use weighted counts, or document that weights only affect the aggregate; add an assertion-bearing test where weights flip a verdict.

**P1-7 | MAJOR | `src/cif_ad_coupling.py:182,205-216,340-364` — empty-portfolio `or` idiom silently means "all defenses"; `minimum_viable_portfolio()` returns [].**
Evidence (live probe): `get_phase_coverage(ADPhase.PLAN, [])` → **0.9** (falls back to full stack via `portfolio or list(CIFDefense)`); `minimum_viable_portfolio()` → **[]** (empty is deemed sufficient); `analyze_portfolio([])` reports `full_coverage_achieved=True` with `total_coverage_score=0.0` (internally contradictory — gap detection uses the full-stack max while the score uses combined=0). Tests codify the wrong semantics (`test_cif_ad_coupling.py:214-233` treats an empty MVP as acceptable). Why: portfolio-optimization API returns semantically wrong answers; any downstream coverage gate is wrong. Fix: `if portfolio is None:` fallback only; add explicit `[]` tests for all three methods.

**P2-4 | MAJOR | `.github/workflows/ci.yml:32-212` + `Makefile:112-116` — the fail-closed claims gate is red at HEAD and not wired into CI.**
Evidence: `verify_claims.py --only-failures` exits **1** at HEAD (`FAILED: 4 claim(s)` — the 4 env-gated LLM claims, correctly pinned in `tests/test_claim_registry.py:63-70`). CI jobs are `test`, `tracked-tree-import`, `manuscript`, `compat` — **none runs `verify_claims`** (the `manuscript` job runs `make check-real-data` + `verify_manuscript.py` only). The gate that RED_TEAM_ASSESSMENT.md:99 cites as the verification record is exercised by no CI job. Why: a new unreconciled number would not fail CI; the "fail-closed" claim is decorative. Fix: add a CI job running `make verify-claims` (accepting the 4 pinned UNBACKED explicitly, e.g. by env-gating or `--allow-unbacked` list), or fold it into the existing `manuscript` job.

### Medium (24)

**P2-5 | MEDIUM | `output/data/full_evaluation_results.json` — published FPR = 0.0 is structurally undefined (0/0), and the artifact is provenance-bare.**
All 16 rows have `tn=0, fp=0` → `fpr = fp/0 → 0.0` published as a rate; the file is a bare list (no `data_origin`, no `.provenance.json` sidecar; writer `scripts/run_full_evaluation.py:119-121` writes `mode` not `measurement_mode`). Manuscript §5 labels it honestly as the "parametric ceiling", but row-level data is easy to misread as measured. Fix: emit `fpr: null` when no benign samples; write `measurement_mode` + provenance sidecar; consider excluding this parametric file from the Makefile `REAL_DATA_FILES` guard list (whose stated premise is "empirically measured pipeline evidence") or relabel the guard.

**P2-6 | MEDIUM | `src/core/consensus.py:305-375, 389-515` — "Weighted"/"Confidence"/"Combined" consensus variants are decision-decorative (same class as P1-6).**
Each subclass only adds a weighted-average getter; `compute_consensus` is inherited and counts unweighted votes at `acceptance_threshold`. Weights never change a decision. Fix: implement weighted decision semantics or document the limitation; add a test where weights flip a verdict.

**P2-7 | MEDIUM | `src/composition/adapters.py:421-438` — ConsensusAdapter profile-count trap.**
Votes are submitted only for `len(sensitivity_profiles)` (default 7) agents, but quorum `min_votes = ceil(n_agents·2/3)` uses `n_agents`; any caller setting `n_agents != 7` silently yields permanent UNDECIDED. Fix: derive the vote count from the same `n_agents` the quorum uses (or vice versa); add a non-7 test.

**P2-8 | MEDIUM | `src/ablation/runner.py:94-109` — `make_default_components()` returns plausible per-component rates (0.58–0.82) that are dead data.**
`evaluate_component_subset` ignores the values (real pipeline measures TPR≈0.12); the function name/values mislead readers into thinking 0.58–0.82 are per-component rates. Fix: rename to `default_component_prior_rates` with an explicit "unused for scoring" note, or remove.

**P2-9 | MEDIUM | `scripts/run_full_evaluation.py:102-129` — non-atomic artifact writes + unbound `.real_data_marker`.**
Results JSON written in place (no temp+rename; partial file unlinked only on success); `.real_data_marker` records mode/seed/timestamp but no content hash, so a stale or hand-edited results file cannot be detected by any verifier. Fix: atomic write (temp+fsync+rename); include `sha256(data_file)` in the marker; make the marker tracked or hash-checked.

**P2-10 | MEDIUM | `src/evaluation/runner.py:328-445` (probe-verified) — real-pipeline ("Mode 1") results carry zero architecture signal.**
Over the 950-corpus, all 4 architectures yield identical row values (0.1920/0.0300/0.1733/0.2400) because the corpus is split by top-category and `_DIFFICULTY_MAP` is never consulted in pipeline mode; adapter/profile/trust topology has no effect on the real path. Any architecture-gap inference from these 16 cells is unsupported. Fix: document that real mode is architecture-agnostic, or thread architecture adapters into the real path; label cross-arch tables as parametric.

**P2-11 | MEDIUM | `src/redteam/__init__.py:122-128,203-214` — threshold clip `[0.01, 0.99]` destroys non-probability scales.**
Probe: after model-mode refinement, `sandbox_kappa 3.0 → 0.99`, `firewall_depth_max 3.0 → 0.99`, `delegation_chain_max 2.0 → 0.99` — `np.clip` is applied to every threshold regardless of domain (kappa is a count, depth is an int). The "hardened config" is semantically corrupted yet deterministic. Fix: per-threshold clip ranges or clip only probabilistic thresholds; add a test with non-probability thresholds.

**P2-12 | MEDIUM | `src/redteam/convergence.py:62-67` + `__init__.py:390-395` — "Nash 100%" is structural: divergent geometric ratio clamped ⇒ projection always 1.0.**
Probe: gains `[0.077,0.129,0.177,0.205,0.232]` → median successive ratio 1.265 (>1, diverging) → clamped to 0.99 → projected 1.0; the trainer's alternative rule (`gains[-1]/gains[0]`) also yields 1.0. Two estimators, one guaranteed-maximum answer; the number is data-insensitive (manuscript §05g now honestly says "projection, not a measured result"). Fix: reject ratios ≥ 1 (no finite projection) and report divergence instead of clamping.

**P2-13 | MEDIUM | `src/redteam/__init__.py:341` — mypy is red at HEAD (contradicts the "mypy clean" claim in AGENTS.md/README/handoff).**
`threshold_updates` annotated redefinition after earlier assignment in `run_round` → `error: Name "threshold_updates" already defined [no-redef]`; `mypy src` fails (161 files, 1 error). CI's advisory mypy comment names a *different*, already-fixed error (`src/formal/trust_bounds.py:84`) — stale. Fix: drop the annotation on line 341 (or annotate at first assignment); update the CI comment; consider promoting mypy to gating once clean.

**P2-14 | MEDIUM | Part 1 vs Part 2 firewall divergence — forked CIF core with divergent defaults (THERMO S1 still open).**
Part 1 `src/firewall.py:34` `injection_threshold=0.7`; Part 2 `src/core/firewall.py:33` `injection_threshold=0.8` (with a Paper-§2 table anchor). Two parallel implementations of the same mechanism with different default rejection thresholds and no shared package or explicit fork contract. Fix: either extract a shared config/contract, or document the fork as intentional (Part 1 = illustrative reference) at both module heads, and pin both defaults in tests.

**P2-15 | MEDIUM | `src/statistics/analysis_runner.py:193` + `output/data/statistical_results.json` — Cohen's d = 62.17 vs an invented control persists (RED_TEAM Part-2 H3, OPEN).**
Probe reproduced `d=62.1700`: CIF scores (n=16, mean 0.9935) vs `baseline = rng.normal(0.03, 0.02)` (no control arm ran); H1 t=230, p≈2.5e-28. The nested `provenance` block is honest and the manuscript does not cite d (grep-clean), so this is a foot-gun, not published fraud — but the artifact invites misreading. Fix: drop the simulated-control tests or gate them behind `simulated=True`; do not report d≈62 as real evidence anywhere.

**P2-16 | MEDIUM | `RED_TEAM_ASSESSMENT.md:49` — resolution statement is stale: the `data_origin/source_script/generated_by` keys were relabeled, not removed.**
The assessment claims the keys "are gone"; the committed `statistical_results.json` still carries them (writer documents them as a "preservation marker" with honest nested `provenance`). Fix: correct the wording in the assessment (keys kept as preservation markers; the *false* provenance was replaced by honest disclosure).

**P2-17 | MEDIUM | `src/redteam/__init__.py:290-299` + `output/data/redteam_evaluation_results.json` — RED_TEAM M4 confirmed: real-mode AT round batch is 100 attacks → 3 distinct payloads.**
Probe: OMEGA_3 batch of 100 → `{identity_impersonation: 34, delegation_abuse: 34, trust_inflation: 32}` (3 distinct strings); real-mode base DR is measured over a duplicate-inflated denominator. The committed evasion artifact discloses distinct counts, but the AT round denominator does not de-dup. Fix: de-dup the AT batch before measuring (helper exists at `evasion.py:98`); add a regression test.

**P2-18 | MEDIUM | `src/statistics/hypothesis.py:213-251` + `output/data/statistical_results.json` — H3 p-values are degenerate: 12/16 eval rows have rate = 1.0.**
`full_evaluation_results.json` contains all-1.0 rows for Claude Code, CrewAI, LangGraph; the paired tests on constant-vs-simulated data yield identical/meaningless p-values (e.g. H3 p=8.7e-07 byte-identical across archs). Fix: report the degenerate operating point explicitly (all-1.0 rows), use an exact count-based test (Fisher/exact) on the underlying contingency, and add a degeneracy guard.

**P2-19 | MEDIUM | `manuscript/05b_statistical_significance.md:86,91` vs `claim_registry.py:269` / `injector.py:501` — "t-distribution correction" prose vs z=1.96 implementation (RED_TEAM M3, OPEN, confirmed).**
Probe with the real 30-seed artifact: z-interval [0.4322, 0.4638] vs t₂₉ [0.4316, 0.4644] — both round to the published [0.432, 0.464], which is exactly why the gate passes while the prose is false. (`src/evaluation/scalability.py:222` correctly uses `stats.t.ppf`.) Fix: use `stats.t.ppf(0.975, k-1)` in both registry and injector, or correct the prose.

**P1-8 | MEDIUM | `src/consensus.py:213` — `QuorumVerification(max_byzantine=0)` falls back to `(n-1)//3` via the `or` idiom (quorum inflated for f=0; `ByzantineConsensus` handles None correctly — inconsistent).**
Fix: `self.max_byzantine = (n_agents - 1) // 3 if max_byzantine is None else max_byzantine`.

**P1-9 | MEDIUM | `src/trust.py:94-97` vs manuscript 04:212,327,340 — path delegation over-decays: code compounds δ^(k(k+1)/2) over k hops; manuscript states and illustrates δ^d.**
Probe: 4-hop chain of 1.0s → 0.5314 (vs manuscript "0.9⁴×1.0 = 0.66"); depth-5 → 0.3487 (vs "0.9⁵ ≈ 0.59"). The bound still holds (code is more conservative) but the flagship worked examples are not reproducible from shipped code, and no test pins the value. Fix: apply δ^d once for total depth (match Def 4.4), or update the manuscript examples and pin in a test.

**P1-10 | MEDIUM | `src/verification.py:31` — import-time side effect: `logging.basicConfig` with a CWD-relative `FileHandler` runs on `import src.verification`, appending to the tracked `manuscript_verification.log` on every test run (dirtied git status during this audit; breaks clean-tree gates and fails from read-only CWDs).**
Fix: configure logging only under `__main__`/explicit `configure_logging()` call, or write under `output/logs/` and gitignore.

**P1-11 | MEDIUM | `src/sandbox.py:153-156,215-228` vs manuscript 04:528-540,05:228-235 — default promotion requires NO corroboration (and no provenance/consistency check); `max_provisional_beliefs` never enforced.**
Default `PromotionCriteria(min_confidence=0.8, min_corroborations=0, min_age_seconds=0)` promotes a fresh single-source belief immediately, contradicting the manuscript's Rule S-PROMOTE (corroboration κ); `SandboxConfig.max_provisional_beliefs=1000` is never read (unbounded store). Fix: default `min_corroborations ≥ 1`, add provenance/consistency hooks, enforce the cap.

**P1-12 | MEDIUM | `src/provenance.py:22-28` vs manuscript 06:330-336 — taint "trust level" scale mismatch: code uses integers 1–7, manuscript table uses 0.1–1.0, with no mapping code.**
Fix: document the integer scale as ordinal (or map to [0,1]) in both code and manuscript so implementers don't mix schemes.

**P1-13 | MEDIUM | `src/data_generation.py:73-87,248-271` — hard-coded "results": FPR 0.12/0.06 contradict the generator's own measured FPR=0; ablation (0.94…0.91) and architecture-comparison rows (Claude Code 0.45→0.97, Camel 0.33→0.92…) are literal constants with no model/source.**
The ablation figure is honestly captioned "Schematic (illustrative, not measured)", but the JSON fields and architecture_comparison.json are presented as data. Fix: mark these files `illustrative: true` in metadata, or compute them from an explicit model; reconcile FPR constants with measured 0.0.

**P1-14 | MEDIUM | `src/data_generation.py:192-216` + `src/visualization/scalability.py:132-139` — scalability data is physically implausible (latency *decreases* 2→16 agents: [0.15,0.05,0.03,0.02,0.04,0.05]; memory flat 1.0 MB) and the figure fits "O(N²)" to a decreasing series, labeled "Measured".**
Fix: real workload per size + repetitions/median, honest memory accounting, and drop the O(N²) fit on non-fitting data.

**P1-15 | MEDIUM | `src/provenance.py:395-401` — `CausalAttribution.generate_report` returns a dict containing a raw `TaintLabel` enum → `json.dumps` raises TypeError despite the "machine-readable report" docstring.**
Fix: serialize as `.value`/`.name`.

**P1-16 | MEDIUM | `src/detection.py:127-131,81 vs 171` — drift history filtered by value-array length only (same-length/different-key observations silently misaligned), and calibration window (`min(i,10)`) differs from scoring window (10).**
Fix: track keys per observation and align on key equality; unify windows.

### Minor (24)

**P2-20 | MINOR | 13 of 26 Part-2 scripts use bare `if __name__ == "__main__": main()` (no `sys.exit`):** `convert_latex_tables`, `generate_all_data`, `run_ablation`, `run_adversarial_training`, `run_colony_benchmarks`, `run_cross_validation`, `run_full_evaluation`, `run_llm_demo`, `run_multi_seed`, `run_publication_suite`, `run_scalability`, `run_sensitivity_analysis`, `run_statistical_analysis`, `z_inject_manuscript_values`. Most `main()` return `None` (failures propagate as exceptions → non-zero exit, so not currently a silent-success bug), but the convention is inconsistent with the 8 scripts that correctly use `sys.exit(main())`. Fix: standardize on `sys.exit(main())` with `main() -> int`.

**P2-21 | MINOR | `Makefile:113` comment "expected to fail on the ~58 KNOWN_UNRECONCILED drift entries" is stale** — current state: 4 UNBACKED / 0 MISMATCH / 0 NOT_FOUND. Fix: update the comment.

**P2-22 | MINOR | `SKILL.md:3,20,81` "2100+ tests … ~18s" stale** (measured: 3336 passed, ~89s with `-q`); `scripts/AGENTS.md` "Script Inventory (22 scripts)" vs 26 present. Fix: refresh counts.

**P2-23 | MINOR | `src/statistics/AGENTS.md:34` documents `t_ci()` — phantom API, never implemented** (confidence.py exposes wilson/bootstrap only). Fix: implement or remove from docs.

**P2-24 | MINOR | `RED_TEAM_ASSESSMENT.md:85` MED-5 cites `visualization.py:472-473` which does not exist in HEAD** (nearest real site checked clean). Fix: mark MED-5 stale/superseded in the assessment.

**P2-25 | MINOR | `cogsec_multiagent_2_computational/AGENTS.md:5` says "Version: 2.0.0"** while README/config.yaml/manuscript/pyproject all say 1.0 (Second Edition). Fix: align to 1.0 or label as edition.

**P2-26 | MINOR | `src/AGENTS.md` references `infrastructure/validation/no_mock_enforcer.py` CI gate that does not exist in this repo** (policy holds in practice — zero mock usage found — but the enforcer is phantom). Fix: point to the actual enforcement (or add the gate).

**P2-27 | MINOR | `output/data/full_evaluation_results.json` sits in the Makefile `REAL_DATA_FILES` guard whose stated premise is "empirically measured pipeline evidence", but it is the parametric-simulation artifact (mode=simulation, no data_origin).** Fix: split the guard list (real vs parametric) or rename the variable.

**P2-28 | MINOR | `src/attacks/corpus.py:278` — `expected_detection=True` on all 950 samples; field is a constant, unused anywhere.** Fix: remove or make it reflect per-sample difficulty.

**P2-29 | MINOR | CI comment (.github/workflows/ci.yml:116-118) mypy note names `trust_bounds.py:84` (fixed); current error is `redteam/__init__.py:341`.** Fix: update comment (see P2-13).

**P2-30 | MINOR | Root `README.md:25` status cell "**v2.0**" for Part 1 vs authoritative 1.1** (config.yaml/pyproject/part README); also Part-1 README "v1.1 in preparation" wording is stale (v1.1 is current). Fix: reconcile labels.

**P2-31 | MINOR | `src/colony/sybil_infiltration.py:118-126`, `quorum_manipulation.py:112-117` — 100% detection rows are near-tautological by construction** (adversaries vote exactly-identical/opposite values; the detector flags exactly that pattern). Manuscript reports honestly, but these should not be cited as evidence CIF "detects" anything. Fix: add a "scenario-construction" caveat where cited.

**P2-32 | MINOR | `src/statistics/nonparametric.py:134-136` — `rank_biserial_correlation` sign depends on which U scipy returns** (probe: separated groups give +1.0 vs conventional −1.0 for x<y). Fix: compute U₁ explicitly to pin the sign.

**P2-33 | MINOR | `src/formal/tla_spec.py:86` — literal word "placeholder" in a generated-spec comment** (would trip any forbidden-word docs gate; harmless to TLA+ consumers). Fix: reword the comment. [LATENT-class]

**P2-34 | MINOR | `src/formal/extended_specs.py:479-492` (SMV) — liveness specs are generated but never model-checked** (no NuSMV/SPIN binary invoked anywhere; `verify_formal_specs.py` verifies generation only). Fix: disclose "generated, not checked" in docs, or wire a checker. [LATENT-class]

**P1-17 | MINOR | `src/consensus.py:116-127` — quorum-fraction off-by-one: `min_votes = ceil(2n/3)` passes while acceptance requires `> 2n/3` (n≡2 mod 3 deadlocks at nominal quorum; probe: 4 votes of 6 → UNDECIDED).** Fix: consistent `floor(2n/3)+1` or `>=`.

**P1-18 | MINOR | Vacuous/conditional test asserts (false confidence):** `test_firewall.py:88-95` asserts only `if classification == REJECT` (classify is ACCEPT → assert never fires); `test_quarantine_tracking` asserts only `isinstance(list)`; `test_benign_message_low_similarity` asserts only `isinstance(float)`; `test_weighted_consensus_basic` (`test_consensus.py:218-235`) has **no assertion**. These let P1-1/P1-6 sail through a 96%-coverage suite. Fix: assert concrete values/verdicts.

**P1-19 | MINOR | `src/ooda_monitor.py:582-599` — `stealth_impact_product` is a tautology returning π/2 for any r.** Fix: return `(impact, stealth, product)` and let consumers check the bound, or drop.

**P1-20 | MINOR | `src/trust.py:160-161` — `get_delegation_trust` returns 1.0 (maximal trust) for paths with < 2 nodes.** Fix: return 0.0 or raise.

**P1-21 | MINOR | `src/firewall.py:260-277` — `EmbeddingStub` is word-order-invariant (bag-of-words) and bypassable via zero-width space (probe: `Ignore\u200b all previous…` → 0.0) / homoglyphs.** Fix: normalize unicode; document bypass limits. (Also: figure glyph warnings — `comprehensive_taxonomy.py:369` Times New Roman missing U+2085/U+26A0 — font fallback.)

**P1-22 | MINOR | `tests/test_trust.py:132-137` — unseeded `np.random.uniform` in a test; `data_generation.py:6` shebang not on line 1; `MPLBACKEND=Agg` set at import time in visualization modules.** Fix: seed the RNG; move shebang; defer backend selection.

**P3-1 | MINOR | Part 3: all 7 figure scripts use bare `main()` (no `sys.exit`)** — inconsistent with `scripts/verify_manuscript.py`. Fix: `sys.exit(main())` uniformly.

**P3-2 | MINOR | Part 3 `src/verification.py:206-223` — `check_style` always returns True (hyperbole warnings never fail), so the summary row "Style: PASS" is vacuous.** Fix: return status reflecting warnings (or label the check "advisory").

**P3-3 | MINOR | Part 3 `src/agent_guidelines.py:287-295` — `check_belief_consistency` indexes `b["id"]` (KeyError on a belief dict without "id") while defensively `.get()`-ing the other fields.** Fix: `b.get("id", ...)`.

### Test-coverage gaps worth closing (this pass)

1. Canonical injection phrase ("Ignore all previous instructions") → `PatternDetector`/`CognitiveFirewall` (P1-1).
2. Invariant missing-field fail-open (P1-2); weighted-consensus decision behavior (P1-6, P2-6).
3. Two-run byte-equality determinism for `detection_results.json`/`scalability_results.json` (P1-3).
4. `compute_path_trust` exact value (P1-9); `QuorumVerification(max_byzantine=0)` (P1-8); empty-portfolio semantics (P1-7).
5. `measurement_mode` correctness when LLM falls back (P2-2); `verify_claims` exit-code end-to-end (P2-4).
6. Threshold scale-clipping (P2-11); Nash projection with divergent ratio (P2-12); AT batch de-dup (P2-17).
7. `statistical_results.json` provenance block vs writer (P2-15); ablation delta ordering (P2-3).
8. `rank_biserial` sign vs hand reference (P2-32); sandbox `max_provisional_beliefs` enforcement (P1-11).

### Checked and deliberately cleared (this pass)

- Attack corpus: 950 = 500/200/150/100, all 12 subcategory counts exact, difficulty 80/335/535, unique SHA-256 ids, same-seed byte-identical, stratified_split deterministic, no unfilled `{var}` placeholders — **probe-verified clean**.
- Stats primitives: Wilson CI, Cohen's d, bootstrap, ANOVA, Kruskal–Wallis, Mann–Whitney, Dunn, beta-binomial/BF10/calibration, regression, stability — numerically verified against scipy/hand references.
- Claims registry verdict semantics (NOT_FOUND always fails; UNBACKED fails for non-illustrative); KNOWN_UNRECONCILED pin exact; injector fail-closed (zero-match raises; unbacked raises).
- No `hash()`-seeded RNG / unseeded `random` / `default_rng(None)` in production paths; `dominant_category` tie-break hash-independent.
- `requests` calls carry `timeout=`; subprocess calls use `check=`/timeout in the formal tier.
- No mocks anywhere (`MagicMock`/`mock.patch`/`unittest.mock` — zero usages); no `sys.exit` in `src/`; no rmtree/security hazards; no eval/exec/pickle/yaml.load.
- Part 3 CIF-AD-OODA matrices consistent with §10 prose (FR dominance 5/10; mechanism-correlation claims hold); 6 incidents in S03 match the retrospective.
- Colony scenario dynamics reproduce the manuscript's colony table (recruitment 80.7%, sybil 100%, quorum 100%, cascade 100% @ 37.4% FPR, emergent 74.3%) from the 30-repeat tracked file.
- Manuscript 05_results/05b are substantially honest about the parametric-vs-real gap (12% ablation TPR, ~44% multi-seed mean, "structural gap") — the provenance-labeling and ordering defects above, not fabrication, are the harms.

---

## Phase 5 — Forward-looking backlog (author/subject-matter OPEN items + next steps)

Carried from `cogsec_multiagent_2_computational/docs/RED_TEAM_ASSESSMENT.md` (status as of 2026-08-01, re-confirmed this pass) plus this pass's extensions. Owner: `[A]` author decision, `[H]` Hermes-agent scoped work.

### Part 1 — theory soundness (mostly `[A]`)

| ID | Item | Status this pass | Owner |
|----|------|------------------|-------|
| H1 | Defense-independence: full re-derivation replacing multiplicative products with union/Fréchet bounds (or explicit correlation ρ) — `S01_proofs.md` | OPEN (scoped assumption added; re-derivation open) | [A] |
| H2 | "Closed semiring" → prove the four axioms directly on a single focal predicate (bounded distributive lattice scoped) | OPEN | [A] |
| H3 | Fisher–Rao `I·S ≤ π/2`: author decision — delete or restate for consistent definitions (Chernoff/Stein governs detectability) | OPEN (artifact removed) | [A] |
| H5 | KL–AUC coupling: correct bound (Bretagnolle–Huber / Pinsker direction) + recomputed table — `06_detection_methods.md:489-518` | OPEN | [A] |
| H7 | Blast-radius: align reachable-agent-factor definition with δ-bound — `03:98-114` vs `S01:977-1005` | OPEN | [A] |
| M1/M2/M4–M7/M9–M11 | Goal-alignment corollary overclaim; Byzantine round sketch; theorems-as-assertions split (min-entropy, detection limit, stealth-impact, progressive detection, budget allocation, diversity, undetectability); trust-matrix EMA convergence (Robbins–Monro); provenance decidability scope (O(|Φ|²)); firewall-liveness tautology; CUSUM ARL; adversary-class separation; ch.3 asserted bounds → "proposed properties" | OPEN — flag for Claim vs Proof split | [A] |
| HIGH-2 | Part-1 illustrative figure scripts: delete and defer fully to Part 2, or keep (captions already honest) | OPEN (option) | [A] |

### Part 2 — empirical/model validity (`[H+A]`)

| ID | Item | Status this pass | Owner |
|----|------|------------------|-------|
| H2 | Real-mode AT: thread refined thresholds into `CognitiveFirewall`/detector so real mode can actually improve DR (currently a disclosed no-op, Δ=+0.00000) | OPEN (disclosed) | [H] (with [A] design input) |
| M3 | t-CI vs z-CI: implement `stats.t.ppf(0.975, k−1)` in claim_registry/injector or correct prose (P2-19) | OPEN — confirmed | [H] |
| M4 | AT batch de-dup before measuring base DR (P2-17) | OPEN — confirmed | [H] |
| — | statisticalResults effect sizes (d≈62) must never be reported as real; drop/gate the simulated-control tests (P2-15) | OPEN — disclosed | [A] |
| L2 | Power-analysis null (mean>0) is a strawman — reframe | OPEN | [A] |
| LOW-3 | `evasion_score` field rename → `heuristic_evasion_score` (+ `unit:"heuristic"`) | OPEN (low risk) | [H] |
| MED-5 | Mark stale (cited file does not exist at HEAD — P2-24) | OPEN → close as stale | [H] |
| H3-new | Degenerate statistical operating point (12/16 rows at rate 1.0): report + use exact tests (P2-18) | NEW | [H+A] |

### Part 2 — engineering backlog (new this pass, all `[H]`, sized)

1. MAJOR P2-4: wire `verify_claims` into CI (accepting the 4 pinned UNBACKED explicitly) — small.
2. MAJOR P2-1: `parametric_simulation` origin value + provenance block for sensitivity_results — small.
3. MAJOR P2-2: honest `measurement_mode` on LLM fallback + regression test — small.
4. MAJOR P2-3: correct 05_results.md:184 ablation ordering + pinning test — small.
5. MEDIUM P2-5…P2-12, P2-13, P2-14: artifact sidecar/atomicity, consensus weight semantics, adapter quorum trap, dead component rates, arch-agnostic real mode disclosure, threshold clip ranges, Nash divergence handling, mypy red, fork-contract doc — each small-to-medium, independent.
6. MINOR batch P2-20…P2-34: exit-code standardization, stale comments/counts/docs, phantom API, marker fields — trivial.

### Part 1 — engineering backlog (new this pass, `[H]`)

1. MAJOR P1-1 (firewall regex) — small, highest user-facing value: fix pattern + add canonical-phrase tests.
2. MAJOR P1-2 (invariants fail-open) — small: reverse defaults + tests.
3. MAJOR P1-3 (artifact determinism) — small: pin timestamps, analytic latency, two-run test.
4. MAJOR P1-4/P1-5 (degenerate ROC AUC=0.000; contradictory detection figure) — small-medium.
5. MAJOR P1-6/P1-7 (weighted consensus decorative; empty-portfolio `or`) — small + tests.
6. MEDIUM P1-8…P1-16, MINOR P1-17…P1-22 — as listed in Phase 4.
7. H-6 family: font glyph fallback for figure rendering (U+2085/U+26A0) — trivial.

### Part 3 — engineering backlog (`[H]`)

1. MINOR P3-1 (figure-script exit codes), P3-2 (style-check vacuousness), P3-3 (belief `id` KeyError) — trivial.
2. No MAJOR/MEDIUM findings this pass — Part 3 is the healthiest of the three.

### Render/publication next steps (from HANDOFF_2026-08-01, still open)

1. Fix beamer slide "Undefined control sequence" errors (the only remaining render blemish) — reconcile slide-renderer preamble with manuscript macros (`\cogstate{}`, `\cref` in slides, stmaryrd/tikz-cd); re-render + re-deliver. — [H]
2. Publication hardening: Zenodo metadata vs config (title/authors/version/DOI status); consider `CITATION.cff`; decide slide-deck inclusion. — [A]
3. Determinism/evidence hygiene for any new committed artifact: provenance keys, no wall-clock timestamps, never `data_origin: real_pipeline` on closed-form; run claims gate + affected suites before committing. — [H]

---

## Cross-Paper Consistency (this pass)

- Series framing and version reconciliation hold at the config/pyproject/manuscript level (1.1 / 1.0 / 1.0); residual drift is confined to README/AGENTS/SKILL prose (P2-23, P2-25, P2-30, P1-22) and the Part-1-vs-Part-2 firewall default divergence (P2-14).
- Claims gate: 163 claims, 159 MATCH / 0 MISMATCH / 0 NOT_FOUND / 4 UNBACKED (env-gated LLM, pinned) — but not CI-wired and red at HEAD (P2-4).
- Part 2 evidence spine (`claims_traceability.md`, `framework_validation.md`, RED_TEAM_ASSESSMENT) is current except the stale items noted (P2-16, P2-24).
