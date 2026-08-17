# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-16
**Owner:** Daniel Ari Friedman
**Status:** Round 9 review+implement complete at HEAD; remaining rows are author-math or architecture decisions
**Auditor:** autonomous hostile red-team review; Round 9 (2026-08-16) improved all three parts after Round 8
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work | `[H+A]` both

---

## Executive Summary - measured 2026-08-16 (Round 9)

| Paper | Tests | Coverage (>=90) | Ruff (touched) | Mypy | Notes |
|-------|-------|-----------------|----------------|------|-------|
| 1 | 437 passed / 0 skipped | 97.72% | 0 | N/A | +8 tests vs Round 8 |
| 2 | 3367 passed / 3 skipped | 96.95% (branch) | 0 | clean (trust+consensus) | +6 tests vs Round 8 |
| 3 | 934 passed / 0 skipped | 99.94% | 0 | N/A | README table repaired |

---

## Completed / Closed

### Round 9 (2026-08-16) — this pass
| ID | Sev | Issue | Status |
|----|-----|-------|--------|
| R9-BFT-N | MED | `ByzantineConsensus` accepted n<=0 because default f=(n-1)//3 is negative and n>=3f+1 still held | DONE — both cores reject n<1 and f<0 |
| R9-P1-Q | MED | Part 1 `QuorumVerification` lacked the Part 2 n_agents/f guards (P2-39 sibling) | DONE — same guards + tests |
| R9-TM | MED | `TrustMatrix(n_agents=0)` built an empty array | DONE — both cores reject n<1 |
| R9-DEL | MED | `delegate_trust` / `compute_path_trust` accepted NaN, out-of-range edges, and negative depth | DONE — unit-interval + depth>=0 (d=0 is identity, used by decay figures) |
| R9-P3-TBL | MIN | Part 3 README series table dropped its own row after the Documentation heading | DONE — row restored in the table |
| P2-F11 | MED | stability writer labeled one pipeline as Claude Code | DONE earlier (Round 7b): `per_architecture={}` with explicit comment |

### Round 8 (2026-08-16)
R8-P1-M3, R8-P3-R7, R8-P3-DUP, R8-P3-NP, R8-P3-FLT, R8-P2-CV, R8-TRUST, R8-CI. See prior commit b218a19.

### Prior rounds
Paper 1 P1-1..P1-22, H7, Round 6/7 math/pandoc/labels.
Paper 2 P2-1..P2-4/6..20/22..38, P2-F1..F4/F5a/F6/F8..F16, LOW-3, L2, P2-39, Round 7b.
Paper 3 P3-1..P3-3, P3-M1..M5, P3-m6..m11.
Program: CITATION.cff schema-valid.

---

## Open backlog (by severity)

### Major — Scoped (deferred)
- **H2 (Part 2) — Real-mode AT is a structural no-op.** Refined thresholds are never threaded into the real detector. **Acceptance:** defensible mapping onto detector parameters + held-out delta>0 + regression test. Author architecture decision.

### Part 1 — theory soundness (author decision)
- **H1** defense-independence re-derivation. **H2** closed-semiring axioms. **H3** Fisher-Rao I*S <= pi/2. **H5** KL-AUC bound direction.
- **M1/M2/M4-M7/M9-M11, HIGH-2** Claim vs Proof.
- **Claim-vs-Proof catalog** — 7 theorems without proof (aggregation, trust-monotonic, cross-modality-bound, threshold-selection, fpr-composition, cascade-fpr, pipeline-tpr) + 6 corollaries.

### Medium
- **P2-5 (PARTIAL)** — committed full_evaluation_results.json still provenance-bare; writer is honest. Author tie-break / regen decision.
- **P2-F5b** — full `from statistics.*` import refactor. Previously half-done and reverted. Do not half-fix.

### Minor
- **CI py3.10** still `continue-on-error`. Promote after a runner-verified 3.10 matrix.
- **Part 2/3 DOIs** reserved-not-public until first release.
- **Part 1 title variants** — author decision.

---

## Checked this round
- Full suites: 437 / 3367+3skip / 934; coverage 97.72 / 96.95 / 99.94.
- d=0 kept as identity so trust-decay figures stay valid.
- Author-math and H2 AT threading untouched.
