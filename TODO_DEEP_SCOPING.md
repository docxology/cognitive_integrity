# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-16
**Owner:** Daniel Ari Friedman
**Status:** Round 8 review+implement complete at HEAD; remaining rows are author-math or architecture decisions
**Auditor:** autonomous hostile red-team review - 3 parallel audits of Parts 1/2 + lead pass on Part 3; rounds 2026-08-04 through 2026-08-08 implemented prior engineering items; Round 8 (2026-08-16) re-ran all gates and implemented remaining validated engineering findings
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD (see commit SHAs) | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work | `[H+A]` both

---

## Executive Summary - measured 2026-08-16 (fresh runs)

| Paper | Tests | Coverage (>=90) | Ruff (touched) | Mypy | Manuscript verify |
|-------|-------|-----------------|----------------|------|-------------------|
| 1 | 429 passed / 0 skipped | 97.73% | 0 | N/A | PASS (7) |
| 2 | 3361 passed / 3 skipped | 96.96% (branch) | 0 | clean (2 scoped files; full src previously clean) | PASS (prior) |
| 3 | 934 passed / 0 skipped | 99.94% | 0 | N/A | PASS (8) |

Claims gate (Part 2) was last CI-wired as 159 MATCH / 0 MISMATCH / 0 NOT_FOUND / 4 UNBACKED (pinned). Not re-run this round (no claim-prose edits).

---

## Completed / Closed

### Round 8 (2026-08-16) — this pass
| ID | Sev | Issue | Status |
|----|-----|-------|--------|
| R8-P1-M3 | MED | Part 1 `check_images_and_links` never rejected absolute/`..` image paths and never exercised `link_pattern` | DONE — `_escapes_root` + link checks + 7 tests |
| R8-P3-R7 | MED | Part 3 verifier lacked pandoc-attribute, math-hygiene, and duplicate-label detection | DONE — ported from Part 1 + 9 tests |
| R8-P3-DUP | MED | Duplicate `{#sec:reading-companion}` in `01_introduction.md` and `09_applications_intro.md` | DONE — applications heading relabeled `sec:applications-reading-companion` |
| R8-P3-NP | MIN | `01_introduction.md` / `preamble.md` used doubled `\\newpage` (other sections used `\newpage`) | DONE — normalized; math-hygiene now PASS |
| R8-P3-FLT | MED | `test_custom_scores` asserted `== 0.7` (3.10 float: 0.7000000000000001); CI documented this as why py3.10 stayed advisory | DONE — `pytest.approx(0.7)` |
| R8-P2-CV | MIN | `coefficient_of_variation` returned 0.0 on any zero mean, labeling oscillating signed series as stable | DONE — all-zero → 0.0; zero-mean + spread → +inf + test |
| R8-TRUST | MED | `compute_trust` accepted non-finite / out-of-range inputs while documenting a [0,1] range | DONE — both Part 1 and Part 2 cores raise `ValueError`; 4 tests |
| R8-CI | MED | CI manuscript job covered only Part 2; checkout/setup-uv floated on major tags | DONE — parts 1+3 verify jobs; pin checkout@v4.2.2 / setup-uv@v3.2.2 SHAs |

### Prior rounds (verified historically; not re-litigated)
Paper 1 P1-1..P1-22, H7, Round 6/7 math hygiene / pandoc / dup labels, schematic figure disclosures.
Paper 2 P2-1..P2-4/6..20/22..38, P2-F1..F4/F5a/F6/F8..F16, LOW-3, L2, Round 7 headline-number integrity, P2-39 f=0, Round 7b provenance/stability/notation.
Paper 3 P3-1..P3-3, P3-M1..M5, P3-m6..m11, profile/pitfall/link-status fixes.
Program: CITATION.cff schema-valid.

---

## Open backlog (by severity)

### Major — Scoped (deferred)
- **H2 (Part 2) — Real-mode AT is a structural no-op.** Refined thresholds are never threaded into the real detector, so `measurement_mode="real"` measures no improvement (delta ~0). Disclosed in 05g. **Acceptance:** design a defensible mapping from the AT threshold vector onto `CognitiveFirewall`/detector parameters, then verify real-mode delta > 0 on a held-out corpus with a regression test. **Why deferred:** author architecture decision; a hand-invented mapping would present an arbitrary improvement as meaningful.

### Part 1 — theory soundness (author decision, carried)
- **H1** — defense-independence: re-derive with union/Frechet bounds (or explicit rho). S01_proofs.md.
- **H2** — "closed semiring": prove the four axioms on one focal predicate.
- **H3** — Fisher-Rao I*S <= pi/2 — delete or restate.
- **H5** — KL-AUC bound direction + recomputed table (06_detection_methods.md).
- **M1/M2/M4-M7/M9-M11, HIGH-2** — Claim vs Proof split; illustrative-figure scripts.
- **Claim-vs-Proof catalog** — 7 MAJOR theorems asserted without proof (thm:aggregation, thm:trust-monotonic, thm:cross-modality-bound, thm:threshold-selection, thm:fpr-composition, thm:cascade-fpr, thm:pipeline-tpr) + 6 corollaries.

### Medium
- **P2-5 (PARTIAL)** — committed `full_evaluation_results.json` is legacy provenance-bare (0.0 FPR on 0/0). Writer is honest; deciding the dominant-label tie-break and regenerating artifact + tracked tables + re-render is an author publication decision.
- **P2-F5b (MED)** — full import refactor (`from statistics.*` → `from src.statistics.*` + drop `mypy_path=src` + remove sys.path shim). Previously tried, half-done, and reverted (mypy double-module-name). Scope: convert ALL legacy absolute imports, then verify. Do not half-fix.
- **P2-F11 (MED)** — stability `per_architecture={"Claude Code": overall}` labels an architecture-agnostic pipeline as architecture-specific. Needs real arch names or dropping the field; touches committed multi-seed aggregation.

### Minor
- **CI py3.10 compat job** remains `continue-on-error`. The documented Part-3 float pin is fixed; promote to gating only after a full 3.10 matrix is re-verified green on a runner.
- **Part 2/3 DOIs reserved-not-public** (404 expected until first release).
- **Canonical Part 1 title divergence** (author decision: 3 variants exist).

---

## Checked and deliberately cleared (Round 8)
- No `unittest.mock` / MagicMock / mocker.patch in tests (comment-only mentions).
- No `eval`/`exec`/`pickle.loads`/`yaml.load` in src.
- `requests` calls carry timeouts.
- Part 1/3 manuscript verifiers PASS after the new checks.
- Full suites: 429 / 3361+3skip / 934; coverage 97.73 / 96.96 / 99.94.
- Author-math items and H2 AT threading left untouched (not half-fixed).
