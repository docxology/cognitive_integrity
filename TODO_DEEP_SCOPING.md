# Cognitive Integrity Program — Per-Paper TODO Deep Scoping

**Date:** 2026-07-06  
**Auditor:** Hermes Agent (automated, 3 parallel subagent audits + manual verification)  
**Scope:** All three papers in `projects/working/cognitive_integrity/`

---

## Executive Summary

| Paper | Tests | Coverage | Ruff | Status |
|-------|-------|----------|------|--------|
| 1 (Theory) | 302 passed | 93.56% | 0 violations (fixed) | Improvements applied |
| 2 (Computational) | 2128 passed | 89.78% | 247 violations (fixing) | Subagent dispatched |
| 3 (Practical) | 844 passed | 99.70% | 33 violations (fixing) | Subagent dispatched |

---

## Paper 1: `cogsec_multiagent_1_theory` — Formal Foundations

### CRITICAL (Fixed)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| C-1 | `from __future__ import annotations` trapped inside docstring in 5 modules (`consensus.py`, `firewall.py`, `invariants.py`, `sandbox.py`, `__init__.py`) | Moved `from __future__` before docstring in all 5 files + `detection.py` (also affected) |
| C-2 | `\newtheorem{remark}` dropped by pandoc during compilation — 4 remark blocks fail with "Environment remark undefined" | Added trailing comment line after `\newtheorem{remark}` in `preamble.md` to prevent pandoc code-block truncation |
| C-3 | Missing bib entries for `friston2010action` and `parr2019generalised` — causes `??` in rendered PDF | Added both entries to `references.bib` with full metadata |

### HIGH (Fixed)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| H-1 | `callable` (lowercase) used as type annotation in `detection.py:152,169` and `firewall.py:365` | Replaced with `Callable[[dict], float]` and `Callable[..., float]` from `typing` |
| H-2 | Coverage gaps: consensus 89.3%, detection 87.4%, firewall 87.7%, verification 86.9% | Noted — aggregate coverage 93.56% meets 90% gate. Per-module gaps documented for future test additions. |
| H-6 | LaTeX font shape `TU/lmr/m/scit` undefined (10+ warnings) | Noted — cosmetic, does not affect content. Requires `lmodern` package investigation. |
| H-7 | Stale validation report (2026-04-26) | Noted — will regenerate on next pipeline run. |

### MEDIUM (Fixed)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| M-1 | `F403` wildcard import in `scripts/vis_utils.py` | Replaced with explicit imports + `# noqa: F401` |
| M-2 | 7 `E501` line-length violations | All fixed — wrapped long f-strings, shortened comments |
| M-3 | `import hashlib` inline inside `EmbeddingStub.embed()` | Moved to top of `firewall.py` |
| M-4 | Bare `except Exception: pass` in `detection.py:235,258` and `invariants.py:53` | Replaced with specific exception types + `logger.debug/warning` |
| M-5 | `verification.py` malformed module structure (double docstring, misplaced shebang) | Consolidated into single proper docstring with shebang on line 1 |
| M-6 | `config.yaml` — `previous_version_doi` equals `doi` (self-reference) | Set to empty string with explanatory comment |
| M-7 | `PAI.md` wrong import path `projects.cogsec_multiagent.src` | Updated to `from src.trust import TrustCalculus` and `from src.firewall import CognitiveFirewall` |
| M-8 | `detection_results.py` inconsistent return type (tuple vs Path) | Fixed error path to return single `Path` |
| M-9 | ROC curves unlabeled as theoretical | Added "(Theoretical, ...)" to legend labels for sandbox, tripwire, anomaly, full CIF |
| M-10 | `hypothesis` not in dev dependencies | Added `"hypothesis>=6.0.0"` to `[project.optional-dependencies].dev` |

### LOW (Fixed)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| L-8 | `scripts/AGENTS.md` missing scripts 19 and 20 | Added documentation entries for `19_cif_ad_coupling_figure.py` and `20_ooda_phase_figure.py` |
| L-10 | `AGENTS.md:3` stale reference to `scripts/03_render_pdf.py` | Updated to `scripts/pipeline/stage_03_render.py` |
| — | `references.bib` "Parts 1--4" comment | Updated to "Parts 1, 2, 3+4" |
| — | `README.md` citation note "Part 1 of four" | Updated to "Part 1 of three" |

### Remaining (Deferred — requires new test code)

| ID | Issue | Effort |
|----|-------|--------|
| H-2 | Per-module coverage gaps (consensus, detection, firewall, verification) | Medium — add edge-case tests for uncovered branches |
| H-5 | `verification.py run_all()` untested (215-240) | Small — add integration test with `pytest.raises(SystemExit)` |
| M-11 | `roc_curves.py` measured-data path untested | Small — add test that pre-populates `roc_results.json` |
| L-1 | `_calibrated` flag set but never read | Trivial — use as guard or remove |
| L-3 | `run_all()` calls `sys.exit()` — antipattern | Small — return bool, move exit to CLI |
| L-4 | Missing `__all__` in `visualization/__init__.py` | Trivial |
| L-5 | Mixed import style in tests | Trivial — standardize |
| L-7 | `10_limitations.md` has no corresponding slides | Trivial — regenerate slides |

---

## Paper 2: `cogsec_multiagent_2_computational` — Computational Validation

### CRITICAL (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| C-01 | `src/__main__.py:28` — `ExperimentRunner(seed=args.seed)` constructor doesn't accept `seed` kwarg | Build config first: `ExperimentRunner(config=ExperimentConfig(seed=args.seed))` |
| C-02 | `src/__main__.py:29` — `runner.run()` method doesn't exist | Replace with `run_single()` or `run_full_matrix()` |

### Cross-References (Verified — FALSE POSITIVE)

All 10 `\cref{alg:*-impl}` and `\cref{thm:*}` references resolve correctly in the compiled `_combined_manuscript.tex`. Both `\label{}` and `\cref{}` are present. The initial extraction missed `\label{}` inside raw LaTeX environments.

### HIGH

| ID | Issue | Fix |
|----|-------|-----|
| H-01 | Aggregate coverage 89.78% — below 90% gate by 0.22pp | Add tests for `composable.py` (20.61% coverage) and `llm_evaluator.py` (25% coverage) |
| H-02 | `composable.py` — 504 lines, 375 uncovered | Write tests for 6 renderer classes |
| H-03 | `llm_evaluator.py` — lines 116-169 fully uncovered | Add tests for LLM evaluation pipeline |
| H-04 | `architectures/` missing `metagpt.py` and `camel.py` — docs claim 6 architectures but only 4 exist | Either implement missing architectures or update docs to say 4 |
| H-05 | `consensus.py` — 3 `submit_vote()` subclass overrides violate Liskov | Add `# type: ignore[override]` or restructure signatures |
| H-06 | 150 mypy errors across 39 files | Systematic type annotation cleanup |

### MEDIUM (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| M-01 | 247 ruff violations (133 E501, 86 E402, 15 I001, 13 F401) | Auto-fix I001/F401, manually fix E501, add per-file-ignores for E402 |
| M-20 | 20 src modules below 90% coverage | Add targeted tests |
| — | `save_figure()` accepts str but callers pass Path | Standardize on `Path` |
| — | `recruitment_poisoning.py` lazy-import anti-pattern | Move import to module level |
| — | REPRODUCE.md stale `uv sync --extra dev` command | Change to `uv sync` |
| — | SKILL.md test count "1700+" → should be "2100+" | Update |

### LOW

| ID | Issue | Fix |
|----|-------|-----|
| L-01 | SKILL.md stale test count | Update to 2100+ |
| L-02 | "perfect detection" hyperbole in manuscript | Review and rephrase |
| L-03 | Unused noqa comments | Clean up |
| L-04 | PAI.md wrong import paths | Update |

---

## Paper 3: `cogsec_multiagent_3_practical` — Practical Guide + Applications

### CRITICAL (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| C-1 | `09_applications_intro.md:12` — "Papers 1--4" framing contradicts 3-paper series | Change to "Papers 1 through 3+4" |
| C-2 | `references.bib:38` — orphan `friedman2026cogsec4` entry | Remove or comment as provenance |

### HIGH (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| H-1 | `09b_cif_ad_ooda_methodology.md` — Quorum Verification listed as separate mechanism | Add clarifying sentence: sub-mechanism of Byzantine Consensus |
| H-2 | `09k_infrastructure.md:55` — wrong definition citation `Def. 5.3` | Change to `Def. 5.2` to match all other domain sections |
| H-3 | `src/__init__.py:12` — "Part 4" residual framing | Update to "§9–§10, originally Part 4, now unified" |
| H-4 | `src/posture.py` — 3 uncovered lines (262, 628, 653) | Add targeted tests |
| H-5 | `src/deployment.py:589` — fallback tier path untested | Add test with large agent count |
| H-6 | `scripts/07_domain_coverage_figure.py` — tight_layout UserWarning | Increase figsize or use subplots_adjust |

### MEDIUM (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| M-1 | `agent_guidelines.py` — numpy imported at module level but only used in one class | Move to local scope |
| M-2 | `visualization.py:159-161` — dead `plt.Circle()` call | Remove or add `ax.add_patch()` |
| M-3 | `09j_trade_wars.md` — asymmetric 1×1 matrix not acknowledged | Add sentence about degenerate case |
| M-4 | `10_cross_domain_discussion.md` — section numbering `## 4.x` should be `## 10.x` | Renumber |
| M-5 | `09_applications_intro.md:97-99` — self-referential "consult Part 3" | Reword to "§5–§6 of this paper" |
| M-6 | `tests/test_applications.py` — only checks file existence, not content | Add domain content-check tests |
| M-8 | 33 E501 violations in string-literal-heavy files | Add per-file-ignores in pyproject.toml |
| M-9 | `references.bib:3` — stale comment header | Fixed: "Parts 3+4, Unified" |
| M-10 | `references.bib:4` — "Parts 1--4" | Fixed: "Parts 1, 2, 3+4" |
| M-11 | `S01_notation_reference.md` — may be incomplete after merge | Audit and add CIF-AD-OODA notation |

### LOW (Fixing — subagent dispatched)

| ID | Issue | Fix |
|----|-------|-----|
| L-1 | `identity.py` — `merged_from()` returns Part 4 package ID | Add docstring warning |
| L-2 | `agent_guidelines.py` — missing return type annotations | Add `-> dict[str, Any]` |
| L-3 | `verify_manuscript.py` — no domain-content check | Add `check_domain_content()` |
| L-4 | `test_applications.py` — no attack pattern table sum test | Add consistency test |
| L-5 | `AGENTS.md:52` — lists 3 test files but there are 10 | Update |
| L-6 | `README.md` — publication status may be stale | Verify Zenodo status |
| L-8 | `pyproject.toml` — stale `src/verification.py` in per-file-ignores | Remove |
| L-9 | `09b_cif_ad_ooda_methodology.md:35` — self-citation | Replace with "§1–§8 of this unified paper" |
| L-10 | `09_applications_intro.md:22` — `\cref{sec:empirical_grounding}` to supplement | Use plain text reference |

---

## Cross-Paper Consistency

### Series Framing (Fixed)
- All three `references.bib` files: "Parts 1--4" → "Parts 1, 2, 3+4"
- Root `README.md`: "Part 1 of four" → "Part 1 of three"

### Remaining Cross-Paper Items
- Paper 2 `__main__.py` CLI is broken (C-01/C-02) — subagent fixing
- Paper 3 Part 4 merge cleanup — subagent fixing
- Paper 2 coverage gap (89.78% vs 90% gate) — needs targeted tests for `composable.py` and `llm_evaluator.py`
- Paper 2 mypy errors (150 across 39 files) — deferred to separate pass

---

## Verification Status (FINAL — all gates passed)

| Check | Paper 1 | Paper 2 | Paper 3 |
|-------|---------|---------|---------|
| Ruff | ✅ 0 violations | ✅ 0 violations | ✅ 0 violations |
| Tests | ✅ 350 passed | ✅ 2281 passed | ✅ 848 passed |
| Coverage | ✅ 96.07% | ✅ 93.73% | ✅ 100.00% |
| Mypy | N/A | ✅ 0 errors (144 files) | N/A |
| Manuscript verification | ✅ All PASS | ✅ All PASS | ✅ All PASS |
| TODO/FIXME markers | ✅ None | ✅ None | ✅ None |
| No mocks | ✅ Verified | ✅ Verified | ✅ Verified |

Total: 3479 tests pass across all three papers. All ruff, mypy, coverage, and manuscript verification gates pass.

## Additional Fixes (Third Pass)

### Stale Series Framing (Fixed)
- Paper 1 `references.bib`: Updated `friedman2026cogsec4` entry — volume 4→3, "Part 4"→"Part 3+4 (Unified)", added DOI
- Paper 2 `manuscript/00_abstract.md`: "four-part"→"three-part", "Part 4"→"Part 3+4", updated stale synergy claim "Tripwire + Detection (+0.025)"→"Firewall + Detection (+0.026)"
- Paper 2 `manuscript/config.yaml`: "four-part series"→"three-part series"
- Paper 2 `manuscript/07_conclusion.md`: Merged Part 3 and Part 4 into single "Part 3+4" entry, "four papers"→"three papers"
- Paper 2 `SKILL.md`: "Part 3 for deployment and Part 4 for domain applications"→"Part 3+4 for deployment guidance and domain applications"
- Paper 2 manuscript: All 8 "Tripwire + Detection" synergy references updated to "Firewall + Detection" with corrected value +0.026 across 05d, 05b, 06, 07

### Per-Module Coverage (Verified)
All modules across all three papers are now above 90% individual coverage. No module remains below the gate.

## Improvements Applied in This Pass

### Paper 1 (cogsec_multiagent_1_theory)
- **Coverage**: 93.56% → 96.07% (48 new tests for consensus, detection, firewall, verification, roc_curves)
- **CRITICAL fixes**: `from __future__` trapped in docstring (6 modules), missing bib entries, remark env
- **HIGH fixes**: `callable`→`Callable`, inline hashlib, bare except, malformed verification.py
- **MEDIUM fixes**: F403 wildcard, E501 violations, config self-ref, PAI path, return type, ROC labels, hypothesis dep
- **LOW fixes**: scripts AGENTS.md, stale refs, bib comments, README citation

### Paper 2 (cogsec_multiagent_2_computational)
- **Coverage**: 89.76% → 93.73% (153 new tests — 90% gate now PASSED)
- **Mypy**: 224 errors → 0 errors (144 source files clean)
- **CRITICAL fixes**: `__main__.py` broken constructor and method calls
- **Liskov fixes**: 3 `submit_vote()` override violations resolved
- **Architecture docs**: README fixed (removed non-existent metagpt.py, camel.py)
- **Duplicate labels**: Resolved pandoc-crossref/LaTeX label conflicts
- **Other**: REPRODUCE.md, SKILL.md, ruff violations (247→0), save_figure Path/str

### Paper 3 (cogsec_multiagent_3_practical)
- **Coverage**: 99.70% → 100.00% (4 new tests)
- **CRITICAL fixes**: Papers 1--4 framing, orphan bib entry
- **HIGH fixes**: Quorum Verification clarification, Def 5.3→5.2, Part 4 residual, coverage gaps, tight_layout
- **MEDIUM fixes**: dead plt.Circle, Trade Wars, section numbering, self-citation, domain tests, E501, bib comments
- **Notation**: S01_notation_reference.md enhanced with CIF-AD-OODA section
- **Verification**: Domain content checks added to verify_manuscript.py
