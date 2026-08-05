# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-05
**Auditor:** autonomous hostile red-team review - 3 parallel audits of Parts 1/2 + lead pass on Part 3; rounds 2026-08-04 and 2026-08-05 re-ran all gates and implemented the open engineering items
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD (see commit SHAs) | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work | `[H+A]` both

---

## Executive Summary - measured 2026-08-05 (fresh runs)

| Paper | Tests | Coverage (>=90) | Ruff | Mypy | Manuscript verify | Claims gate |
|-------|-------|-----------------|------|------|-------------------|-------------|
| 1 | 382 passed / 0 skipped | 96.18% | 0 | N/A | PASS | N/A |
| 2 | 3354 passed / 3 skipped | 96.98% (branch) | 0 | clean (161) | PASS (10) | 163: 159 MATCH / 0 MISMATCH / 0 NOT_FOUND / 4 UNBACKED, CI-wired |
| 3 | 882 passed / 0 skipped | 99.69% | 0 | N/A | PASS (7) | N/A |

All suites green. Claims gate exits 1 only on the 4 env-gated LLM claims (pinned); CI asserts mismatch=0 / not_found=0 / unbacked=4 (P2-4).

### Rounds 1-2 (2026-08-04) - completed
Round 1 filed and implemented P1-1..P1-22, P2-1..P2-4/13/16/19, P3-1..P3-3 and the medium/minor batch
(P2-6..P2-12/14/18/22/23/24/26/27/28/31/32/33/34, P1-14 fork pin). Round 2 mirrored the
Part-1 defect fixes into the Part-2 authoritative core (P2-35 trust decay/short-path,
P2-36 sandbox corroboration + cap, P2-37 invariants fail-closed, P2-38 provenance report
JSON-safe). See Completed/Closed below.

### Round 3 (2026-08-05) - comprehensive completion pass, implemented:
- **P2-17** - real-mode AT round now de-duplicates the generated batch before measuring
  base detection rate (phantom 100-attack -> ~3-distinct-payload denominator); regression test.
- **P2-15** - `load_real_data` gains a `simulated_control` gate: requesting a real (non-simulated)
  control arm fails closed because no undefended control was ever run; effect sizes against the
  disclosed simulated N(0.03,0.02) control remain labeled; test.
- **P2-20** - all remaining bare-`main()` scripts standardized to `sys.exit(main())`
  (13 scripts; `run_llm_demo.py` is inline-only and already exit-honest).
- **LOW-3** - `GeneratedAttack.evasion_score` renamed `heuristic_evasion_score` (unit:
  "heuristic"), script output key renamed `mean_heuristic_evasion_score`, committed
  redteam artifact regenerated (identical values, renamed key only).
- **L2** - power-analysis "mean vs 0" row reframed: explicitly a degenerate reference row,
  not the research question; the substantive null (mean vs parametric ceiling) is settled by
  the Bayes-factor gap analysis.
- **H7** - blast-radius reachability-factor alignment documented at thm:blast-radius,
  pointing to the consistent S01 restatement (thm:blast-radius-restated).
- **CITATION.cff** added at repo root (schema-valid, three-part DOIs).
- **P2-10** - verified already addressed: S08/05_results label every cross-arch table
  "parametric/design-level" and name the producing script/artifact; round-1 runner docstring
  discloses that real mode is architecture-agnostic. Closed without code change.

### P2-5 - PARTIAL (writer DONE, artifact preserved)
The `run_full_evaluation.py` writer emits honest output (null FPR on 0/0, `measurement_mode`,
atomic write, sha256 marker, provenance sidecar). The **committed** `full_evaluation_results.json`
was deliberately NOT regenerated: a regeneration flips the injection-cell dominant label
(deterministic tie-break `direct_injection` vs the committed `indirect_injection`), which would
churn the tracked `detection_rates.tex` and the manuscript render for no scientific gain (detection
rates are identical, and the manuscript already labels the artifact "parametric ceiling").
Scope to close fully: decide the tie-break label for the injection cell (or emit the top-level
category), regenerate artifact + tracked tables + re-render, confirm the claims gate.

---

## Completed / Closed (verified at HEAD 2026-08-05)

### Paper 1
| ID | Issue | Status |
|----|-------|--------|
| P1-1..P1-22 | Full Part-1 hostile-red-team batch | DONE (ca941f3) |
| H7 | Blast-radius reachability factor vs delta-bound alignment | DONE (2026-08-05) - documented at thm:blast-radius referencing S01 restatement |

### Paper 2
| ID | Issue | Status |
|----|-------|--------|
| P2-1..P2-4/13/16/19 | provenance/CI/gate/mypy batch | DONE (3dd7e2b) |
| P2-6..P2-12/14/18/22/23/24/26/27/28/31/32/33/34 | medium/minor batch | DONE (dcd2f9e) |
| P2-35..P2-38 | Part-2 core divergence mirrors (trust/sandbox/invariants/provenance) | DONE (da7bca7) |
| P2-17 | AT real-mode batch de-dup | DONE (2026-08-05) |
| P2-15 | simulated-control gate (fail-closed) | DONE (2026-08-05) |
| P2-20 | script exit-code standardization | DONE (2026-08-05) |
| P2-10 | cross-arch table parametric labeling | DONE (2026-08-05) - verified already labeled |
| LOW-3 | heuristic_evasion_score rename + artifact | DONE (2026-08-05) |
| L2 | power-analysis strawman reframe | DONE (2026-08-05) |

### Paper 3
All findings (P3-1..P3-3 + ledger) DONE at 3dd7e2b. No new findings in rounds 2-3.

### Publication / program
| Item | Status |
|------|--------|
| CITATION.cff (schema-valid, 3 DOIs) | DONE (2026-08-05) |

---

## Open backlog (by severity)

### Major - Scoped (deferred)
- **H2 (Part 2) - Real-mode AT is a structural no-op** - refined thresholds are never threaded
  into the real detector, so `measurement_mode="real"` measures no improvement (delta ~0).
  Disclosed in 05g. **Scope/acceptance:** design a defensible mapping from the AT threshold
  vector (drift/anomaly/trust_decay/...) onto `CognitiveFirewall`/detector parameters, then
  verify real-mode delta > 0 on a held-out corpus with a regression test.
  **Reason deferred:** the threshold-to-detector coupling is an architecture decision the author
  flagged for design input; a hand-invented mapping risks presenting an arbitrary improvement as
  meaningful. All independent pieces (P2-17 de-dup, measurement mode labeling) are done.

### Part 1 - theory soundness (author decision, carried)
- **H1** - defense-independence: full re-derivation with union/Frechet bounds (or explicit rho). S01_proofs.md. Reason: mathematical re-derivation authored by the paper's author.
- **H2** - "closed semiring" - prove the four axioms on one focal predicate. Reason: proof authorship.
- **H3** - Fisher-Rao I*S <= pi/2 - delete or restate. Reason: author decision on claim scope.
- **H5** - KL-AUC bound direction + recomputed table (06_detection_methods.md:489-518). Reason: re-derivation + table recomputation is author math.
- **M1/M2/M4-M7/M9-M11, HIGH-2** - Claim vs Proof split items; illustrative-figure scripts. Reason: author decision on which claims to reclassify.

### Medium
- **P2-5 (PARTIAL)** - committed full_evaluation_results.json is legacy provenance-bare (0.0 FPR on 0/0). Writer fixed; deciding the dominant-label tie-break and regenerating artifact + tracked tables + re-render is scoped above (see Partial note).

---

## Checked and deliberately cleared (rounds 1-3)
- Attack corpus 950 = 500/200/150/100; byte-identical at fixed seed; no unfilled placeholders.
- Stats primitives (cohens_d, Wilson, bootstrap, rank-biserial) verified vs scipy/hand refs.
- No mocks; no sys.exit in src; no eval/exec/pickle; requests carry timeout; no bare excepts in either src tree.
- Part 3 matrices consistent with prose; 6 incidents match the retrospective.
- Part 1/2/3 manuscripts pass verify_manuscript after the H7/L2 prose edits.
