# Thermo-Nuclear Code Quality Review — cognitive_integrity

Date: 2026-07-22  
Scope: all three papers (`cogsec_multiagent_1_theory`, `_2_computational`, `_3_practical`)  
Baseline: post-merge with `origin/main` (21 ultracode commits) + local WIP reconciliation

## Executive verdict

**FAIL** on pre-remediation bar (presumptive blockers present).  
**Conditional PASS** after remediations applied in this session for the highest-conviction structural fixes listed under “Remediations applied”.

Tests after sync + remediations: Paper 1 **355** passed, Paper 2 **2422** passed, Paper 3 **872** passed.

---

## Ranked findings (all papers)

### 1. Structural regressions (presumptive blockers)

| ID | Severity | Finding |
|----|----------|---------|
| S1 | **Blocker** | **Forked CIF core** — Paper 1 flat `src/*.py` duplicates Paper 2 `src/core/*` (~2.5k LOC) with divergent defaults (e.g. firewall injection threshold 0.7 vs 0.8). No shared package or explicit fork contract. |
| S2 | **Blocker** | **Rate semantics schism** — parallel composition used `max(rates)` in `composable.py` while `composition/algebra.py` and lattice join use OR/series formulas. Diagrams could pass while algebra disagrees. |
| S3 | **Blocker** | **>1k-line src modules** — `category_theory_advanced.py` (1437), `checklists.py` (1116), `composable.py` (1081). |
| S4 | **High** | **Dual API in Paper 3** — stub classes in `src/__init__.py` vs real modules (`posture.py`, `deployment.py`, `risk_assessment.py`). |
| S5 | **High** | **Part 4 code asymmetry** — ten-domain analysis lived only in manuscript + fat script `07_domain_coverage_figure.py`. |
| S6 | **High** | **Claim–code drift (Paper 2)** — composer/module rates hardcoded (~0.91) vs ablation TPR ~12%; injector still hardcodes multi-seed fallbacks when JSON missing. |

### 2. Missed code-judo (addressed vs deferred)

| Move | Status |
|------|--------|
| Split `category_theory_advanced.py` → `formal/advanced/*` + facade | **Applied** |
| Split `checklists.py` → `checklists/` package | **Applied** |
| Unify `parallel_rate` with `composition.algebra` | **Applied** |
| Promote Part 4 domain data to `src/applications/domain_coverage.py` | **Applied** |
| Remove import-time logging in `verification.py` | **Applied** |
| Extract shared `cif_core` package (P1/P2 dedup) | **Deferred** — large cross-repo contract; document as follow-on |
| Collapse Paper 1 firewall class hierarchy | **Deferred** |
| Split `composable.py` renderers + single module registry | **Deferred** |
| Retire `test_coverage_boost.py` pattern | **Deferred** — merge into domain tests in dedicated pass |
| Extract Paper 3 stub layer from `__init__.py` | **Deferred** — needs test migration |

### 3. Spaghetti / branching

- Paper 1: three parallel firewall classification paths in one file.
- Paper 2: `DriftDetector` silent history-row drops; duplicate z-score loops in `AnomalyScorer`.
- Paper 2: `sys.path` mutation in `src/__init__.py` masking import inconsistencies.

### 4. Boundary / type problems

- Loose `dict` agent state in detection; untyped `deque` history.
- Injector crashes on missing required JSON instead of explicit draft mode.
- Three import styles in Paper 1 tests (`consensus`, `src.visualization`, `src.trust`).

### 5. File size / decomposition

**Still >900 lines (post-split targets for next pass):**

| Paper | File | Lines (approx) |
|-------|------|----------------|
| 2 | `src/visualization/composable.py` | ~1080 |
| 3 | `src/agent_guidelines.py` | ~959 |
| 3 | `src/visualization.py` | ~943 |
| 3 | `src/risk_assessment.py` | ~910 |
| 2 | `tests/test_statistics.py` | ~1923 |
| 2 | `tests/test_composition.py` | ~1661 |
| 2 | `tests/test_coverage_boost.py` | ~1155 |

### 6. Doc / signpost drift

- Paths say `projects/cognitive_integrity/`; sidecar checkout is `projects/working/cognitive_integrity/` (symlinked in template).
- Paper 3 `SKILL.md` references nonexistent `scripts/generate_visuals.py`.
- Paper 1 `SKILL.md` references nonexistent `scripts/generate_figures.py`.
- Paper 1 `src/AGENTS.md` cloned from Paper 2 core docs; omits v2-only modules.

---

## Per-paper notes

### Paper 1 — theory

- Manuscript claims defense composition algebra; Paper 2 has `src/composition/`, Paper 1 has diagram-only `visualization/defense_composition.py`.
- `data_generation.py` mixes simulated runs with hardcoded headline metrics.
- Coverage padding embedded in domain test files (not isolated like Paper 2’s `test_coverage_boost.py`).

### Paper 2 — computational (evidence spine)

- Implementation spine is sound; main risk is **evidence presentation** (composer rates, injector fallbacks) not core detection tests.
- Remote ultracode pass improved: drift calibration wired, fail-closed invariants, ManuscriptVerifier returns bool, SVG scaffold deduped, dedicated `test_category_theory_advanced.py`.
- Script inventory now includes `run_adversarial_training.py`, `run_redteam.py` (22 scripts).

### Paper 3 — practical + applications (merged)

- Manuscript merge validated by `tests/test_applications.py` (33 sections, 10 domains).
- `identity.py` correctly records Part 4 provenance; keep for audit trail.
- Pitfall data duplicated between `pitfalls.py` and `visualization.py` (chart-specific hardcoded list).

---

## Remediations applied (this session)

1. Synced `origin/main` (stash/pull/pop); resolved conflicts in `composable.py`, `ablation_study.py`, `scripts/AGENTS.md`, verification logs.
2. Split `cogsec_multiagent_3_practical/src/checklists.py` → `src/checklists/` package (API unchanged via `src.checklists`).
3. Split `cogsec_multiagent_2_computational/src/formal/category_theory_advanced.py` → `formal/advanced/*` + thin facade.
4. Fixed `parallel_rate` / `series_rate` in `composable.py` to delegate to `composition.algebra`.
5. Created `src/applications/domain_coverage.py`; thinned `scripts/07_domain_coverage_figure.py`.
6. Moved verification logging setup out of module import path (`_configure_verification_logging()`).

---

## Approval bar (thermo-nuclear skill)

| Criterion | Pre-fix | Post-fix |
|-----------|---------|----------|
| No unjustified >1k src growth | Fail | **Partial** — two blockers removed; composable still >1k |
| No obvious rate-semantics fork | Fail | **Pass** (composable aligned) |
| No import side effects in library modules | Fail | **Pass** (verification) |
| No feature logic in 200+ line scripts (Part 4) | Fail | **Pass** (domain script thinned) |
| Documented path to dedup P1/P2 core | Missing | **Documented** (follow-on) |

---

## Recommended follow-on (ordered)

1. Shared `cif_core` wheel consumed by Paper 1 (re-export) and Paper 2 (`from cif_core import …`).
2. Split `composable.py` + single `module_registry.py` fed from ablation JSON (with `illustrative: true` flag for composer).
3. Paper 3: `src/types.py` + remove stub classes from `__init__.py`; migrate `test_practical.py`.
4. Split Paper 2 `tests/test_statistics.py` mirroring `src/statistics/`.
5. Fix injector hardcoded fallbacks; wire composer rates to measured ablation outputs or label as illustrative in UI.
