# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-04
**Auditor:** autonomous hostile red-team review - 3 parallel audits of Parts 1/2 + lead pass on Part 3; every MAJOR re-verified by lead with live probes; 2026-08-04 pass re-ran all gates and implemented the remaining open engineering items
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD (see commit SHAs) | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work
**Owner conventions:** `[A]` author/subject-matter decision | `[H]` agent-scoped engineering item | `[H+A]` both

---

## Executive Summary - measured 2026-08-04 (fresh runs, not hand-pinned)

| Paper | Tests | Coverage (>=90) | Ruff | Mypy | Manuscript verify | Claims gate |
|-------|-------|-----------------|------|------|-------------------|-------------|
| 1 | 382 passed / 0 skipped | 96.18% | 0 | N/A | PASS | N/A |
| 2 | 3347 passed / 3 skipped | 96.98% (branch) | 0 | clean (161) | PASS (10) | 163: 159 MATCH / 0 MISMATCH / 0 NOT_FOUND / 4 UNBACKED, CI-wired |
| 3 | 882 passed / 0 skipped | 99.69% | 0 | N/A | PASS (7) | N/A |

All suites green. Claims gate exits 1 only on the 4 env-gated LLM claims (pinned); CI asserts mismatch=0 / not_found=0 / unbacked=4 (P2-4).

### 2026-08-04 implementation pass - fixed this session

Re-verified MAJORs from `ca941f3`+`3dd7e2b` live: P1-1 regex, P1-2 invariants, P1-3 determinism, P1-4/5 ROC+figure, P1-6/7 weighted consensus+portfolio, P2-1 origin+provenance, P2-2 fallback mode, P2-3 ablation ordering, P2-4 CI claims gate.

Implemented remaining open medium/minor items:
- P2-6: Weighted/Confidence/Combined consensus now override compute_consensus (weighted supermajority); 3 flip-verdict tests.
- P2-7: ConsensusAdapter submits exactly n_agents votes (profiles cycled); non-7 test.
- P2-8: ablation priors documented as unused (only keys authoritative).
- P2-9: run_full_evaluation atomic write + sha256 marker.
- P2-10: runner docstring discloses real mode is architecture-agnostic.
- P2-11: per-domain threshold clip (PROBABILISTIC_THRESHOLDS only); test.
- P2-12: geometric projection returns +inf on divergent ratio; round-estimate returns 0 on divergence; design-model 1.0 kept as disclosed.
- P2-14: firewall fork documented at both heads; defaults pinned (0.7 / 0.8).
- P2-18: H3 degeneracy guard (constant series flagged, not significant); test.
- P2-19: 05b prose corrected to the recorded normal approximation (mean +/- 1.96*s/sqrt(k)).
- P2-22/23/24/26/27/28/31/32/33/34: SKILL+AGENTS counts, phantom t_ci, stale MED-5, phantom no_mock_enforcer, Makefile note, expected_detection, surrogate/quorum caveats, rank-biserial sign, TLA placeholder, generated-not-checked.
- P1-14 collateral: Part-1 firewall fork note + pin test (382nd).

### Partial / carried
- P2-5 (PARTIAL): writer fixed (null FPR, measurement_mode, sidecar); committed artifact left as-is (regeneration changes category labels + latencies).
- P2-20 (PARTIAL): run_full_evaluation standardized to sys.exit(main()); ~12 scripts remain bare (advisory).

---

## Completed / Closed (verified at HEAD 2026-08-04)

### Paper 1
| ID | Issue | Status |
|----|-------|--------|
| P1-1 | Firewall regex fails canonical phrase | DONE |
| P1-2 | Invariants fail OPEN on missing fields | DONE |
| P1-3 | Artifact non-reproducibility | DONE |
| P1-4/5 | Degenerate ROC AUC; contradictory detection figure | DONE |
| P1-6 | Weighted consensus decorative | DONE (decision overrides) |
| P1-7 | Empty-portfolio or-idiom | DONE |
| P1-8..P1-16 | Medium engineering items | DONE |
| P1-17..P1-22 | Minor items | DONE |

### Paper 2
| ID | Issue | Status |
|----|-------|--------|
| P2-1 | sensitivity false-real-pipeline origin | DONE |
| P2-2 | measurement_mode on fallback | DONE |
| P2-3 | ablation ordering | DONE |
| P2-4 | claims gate CI-wired | DONE |
| P2-13 | mypy red | DONE |
| P2-14 | firewall fork | DONE (this pass) |
| P2-19 | t vs z prose | DONE (this pass) |
| P2-32 | rank-biserial sign | DONE (this pass) |
| P2-22/23/24/26/27/28/31/33/34 | doc/count/phantom minors | DONE (this pass) |

### Paper 3
All findings (P3-1..P3-3 + ledger) DONE at 3dd7e2b. No new findings this pass.

---

## Open backlog (by severity)

### Major
No MAJOR defect remains open. Deferred with Major-like scope:
- H2 (Part 2) - Real-mode AT is a structural no-op (thresholds never threaded into the detector; real-mode delta ~0). Disclosed in 05g. **Deferred:** thread thresholds into the real detector so real mode can improve; acceptance = real-mode delta > 0 + test. Author input needed.

### Medium
- P2-17: AT real-mode round batch duplicate-inflated (~100 -> 3 distinct payloads). De-dup before measuring (helper at redteam/evasion.py). Tied to H2; deferred.
- P2-15: statistics effect size (Cohens-d ~62) vs invented control. Provenance honest, but must never be reported as real. Drop/gate simulated-control tests. Author decision.
- P2-5: committed full_evaluation_results.json remains legacy provenance-bare. Dedicated regeneration pass (stable category determination first).
- P2-10: consider labeling cross-arch table (05f) parametric-only in prose (runner disclosure added).
- P2-20: standardize remaining ~12 script exit codes (advisory).

### Part 1 - theory soundness (author, carried)
- H1 independence re-derivation (union/Frechet or rho); H2 closed-semiring proof; H3 Fisher-Rao I*S<=pi/2; H5 KL-AUC bound + table; H7 blast-radius alignment; Claim vs Proof split items (M1/M2/M4-M7/M9-M11, HIGH-2).

---

## Test-coverage gaps worth closing (future passes)
1. Regenerate full_evaluation_results.json honestly (P2-5) + claims-gate confirmation.
2. Real-mode AT: de-dup (P2-17) + thread thresholds (H2).
3. Standardize script exit codes (P2-20).

## Checked and deliberately cleared (this pass)
- Attack corpus 950 = 500/200/150/100; byte-identical at fixed seed; no unfilled placeholders.
- Stats primitives verified vs scipy/hand refs; rank-biserial sign pinned.
- Consensus variants now exercise weights in compute_consensus (P2-6).
- No mocks; no sys.exit in src; no eval/exec/pickle; requests carry timeout.
- Part 3 matrices consistent with prose; 6 incidents match retrospective.

---

## Cross-Paper Consistency (this pass)
- Versions hold (1.1 / 1.0 / 1.0). Prose drift refreshed (P2-22).
- Claims gate 159/0/0/4, CI-wired (P2-4).
- Firewall fork (0.7 reference / 0.8 operational) documented + pinned (P2-14).
