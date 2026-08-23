# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-22
**Owner:** Daniel Ari Friedman
**Status:** Round 10 (cross-paper) complete at HEAD. Round 10 found that every gate in this
repository was scoped to a single part, so cross-paper drift was structurally invisible; a
program-level gate now exists (`scripts/check_series_integrity.py`, wired into CI).
**Auditor:** seven-lens review with adversarial verification of every finding; 113 of 114
findings survived verification, 44 at HIGH
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work | `[H+A]` both

---

## Executive Summary - measured 2026-08-16 (Round 9)

| Paper | Tests | Manuscript verifier | Notes |
|-------|-------|---------------------|-------|
| 1 | 437 passed / 0 skipped | PASS (7/7) | |
| 2 | 3369 passed / 3 skipped | claim registry 163/163 MATCH | |
| 3 | 935 passed / 0 skipped | PASS (8/8) | |
| series | 25 passed (`tests/test_series_integrity.py`) | gate PASS | new in Round 10 |

Measured 2026-08-22. The series row is the new program-level gate; it had no predecessor,
which is the finding that organises this round.

---

## Completed / Closed

### Round 10 (2026-08-22) — cross-paper pass

The organising finding: **every gate was per-part.** Each paper ran its own tests and its
own `verify_manuscript.py`, and Part 2 ran its claim registry over its own manuscript only.
No gate compared the three papers to each other, so a quantity could be published as two
different numbers in two papers that cite each other and stay green for nine rounds.

| ID | Sev | Issue | Status |
|----|-----|-------|--------|
| R10-BIB-FAB | HIGH | Seven bibliography entries carried arXiv IDs belonging to unrelated papers (astronomy, nuclear theory, general relativity, federated learning). Verified individually against arxiv.org. | DONE — repaired to the real source where one exists (EchoLeak → CVE-2025-32711 advisory; TopicAttack → arXiv:2507.13686; PromptPwnd → Trail of Bits argument-injection disclosure; Prompt Infection → arXiv:2410.07283; Zero-Trust → NIST SP 800-207), deleted where none does |
| R10-BIB-AUTH | HIGH | Fourteen entries for real papers carried invented author lists; three propagated into Part 2's related-work prose as wrong attributions. | DONE — all corrected against the primary record |
| R10-BIB-DUP | MED | Four duplicate works under two bibkeys (P1 carlini, P2 goodfellow, P3 owasp, P3 cpwbft/zheng); `friston2022free` resolved to two different papers in P2 vs P3. | DONE — duplicates removed, key collision split |
| R10-CEIL | HIGH | The parametric ceiling was published as 94--100% in 26 places and 96--100% in the rest. The artifact's minimum cell is 0.96 and `tests/test_manuscript_claims.py` already asserted ≥0.96. | DONE — 96--100% everywhere; derived gap 49--88 → 51--88 |
| R10-ARCH | HIGH | Part 1's Discussion claimed six architectures and named peer-to-peer; Part 2 evaluates four. | DONE |
| R10-MEAN | HIGH | Part 1 carried 44.7% [43.4, 46.2] for Part 2's multi-seed mean of 44.8% [43.2, 46.4]. | DONE |
| R10-OMEGA | HIGH | Ω₁–Ω₅ names two different ladders: Part 1's access-based classes and Part 2's technique ladder (`redteam/generator.py::OmegaLevel`), with Part 2 attributing its own ladder to "Part 1 Definition 4". They do not correspond by index. | PARTIAL — false attribution removed and the two ladders disambiguated in Part 2 §3; figure caption restored to Part 1's classes (the figure code was already correct). **Author decision below.** |
| R10-05G | HIGH | Part 2 §5g ended mid-sentence on a dangling heading; the per-Ω table it once held was deleted as a design model, and Part 1 still cited its numbers (97%…49%). | DONE — section closed honestly, Part 1's citation of the retracted numbers removed |
| R10-EMERG | HIGH | Part 3 headlined 56.1% / 46.6% FPR for emergent misalignment, which Part 2 retracts in three places (real: 74.3% / 25.5%). Part 3 also narrowed Part 2's 95% HDI from [35.5, 54.7] to [41.3, 48.3]. | DONE |
| R10-SEMI | HIGH | Part 1's supplement proved a "closed semiring" its own body says is not constructed; the type-closure proof used an outcome outside its stated codomain and the distributivity gloss was wrong. | DONE — restated as the bounded distributive lattice the proof establishes |
| R10-CT | HIGH | S04 labelled CT.1/CT.2/CT.3 as left identity / right identity / associativity, contradicting the same file's intro and the CT.1–CT.3 defined in §01c/§02c. | DONE |
| R10-PTR | MED | 73 hardcoded cross-paper pointers ("Part 1, Theorem 3.2a", "Paper 1, Def. 5.5"). Part 3's 22 numbered definition pointers each named a different definition than their sentence, and 5.5 was used for two defenses. Part 2's audited as mostly correct. | PARTIAL — Part 3's converted to named references; "Theorem 3.2a" (names nothing in Part 1) repointed; Part 2's 44 remain, gated advisory |
| R10-TESTS | MED | Test counts hardcoded in Part 3's abstract and introduction (3,308) and in Part 2's `SKILL.md` (3338). | DONE — 3,369. Still hand-maintained; see backlog |


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

### Author decisions surfaced by Round 10

- **R10-OMEGA — one symbol, two ladders.** Part 1's Ω₁–Ω₅ are *access* classes
  (external / peripheral / agent-level / coordination / systemic). Part 2's are *technique*
  classes (passive / injection / impersonation / belief / coordinated), encoded in
  `src/redteam/generator.py::OmegaLevel`. They cannot be renumbered into each other: this
  corpus's "Ω₂ (injection)" spans Part 1's Ω₁ and Ω₂, because direct injection arrives
  through user input and indirect injection through fetched tool content. Round 10 removed
  the false attribution and stated the divergence in Part 2 §3. **Decide:** (a) rename
  Part 2's enum and regenerate the affected artifacts so one Ω ladder serves the series, or
  (b) keep two ladders and give the second its own symbol.
- **R10-S08 — S08's tables are not the artifact.** `S08_parametric_analysis.md` reports
  per-architecture TPR 0.94/0.94/0.96/0.98 and per-cell Full-CIF values from 0.85 to 0.98,
  while `output/data/full_evaluation_results.json` gives 1.00/0.98/1.00/1.00 with a 0.96
  floor. The prose ceiling is now consistent at 96--100% and gated, but the tables beneath
  it are hand-calibrated illustrations. **Decide:** regenerate them from the artifact, or
  label them design-model illustrations in the S08 methodology note.
- **R10-PTR — Part 2's 44 numbered cross-paper pointers.** Audited as mostly resolving
  correctly, so they were left in place rather than churned. Converting them to named
  references is what promotes `cross-paper-pointers` from advisory to gating.
- **R10-TESTS — the test count is still hand-typed** in Part 3's abstract and introduction.
  It has now drifted three times. Emitting it into a Part 2 artifact and hydrating a
  `{{TOKEN}}` at render time is the fix that holds.

### Round 10 findings not yet implemented

113 findings survived adversarial verification; the table above records those closed. The
remainder are recorded in the review output and are dominated by three classes: Part 2
presenting `DataGenerator` output as end-to-end measurement in §05d, three mutually
inconsistent component-hierarchy orderings across §05f/§06/§07, and a false Honest-Majority
lemma in Part 1 whose proof inverts its own hypothesis. Each changes what a paper claims and
is an author call, not a mechanical correction.

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
