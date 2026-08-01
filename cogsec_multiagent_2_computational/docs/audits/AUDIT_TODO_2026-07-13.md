# Part 2 Computational Paper — Comprehensive Audit
**Date:** 2026-07-13  
**Baseline:** 2,283 tests pass · 93.50% coverage · Ruff clean · mypy 0 errors  
**Auditor:** Hermes subagent (read-only, no edits)

---

## EXECUTIVE SUMMARY

| Category | Count | Severity |
|---|---|---|
| Data integrity / reproducibility gap | 4 | CRITICAL |
| Doc-drift / stale series framing | 2 | HIGH |
| Coverage gaps below 90% | 8 | HIGH/MEDIUM |
| Manuscript citation errors | 1 | HIGH |
| Architecture claim vs code | 0 | RESOLVED (docs already say "four") |
| `from __future__` inside docstring | 1 | MEDIUM |
| `pass` in exception handlers | 3 | MEDIUM |
| Seed/injector schema mismatch | 1 | HIGH |
| Dead test scenario reference | 1 | LOW |

---

## CRITICAL Findings

### C-01 · `DataGenerator.generate_multi_seed_results()` produces synthetic 96.7% data that contradicts the manuscript
**File:** `src/data/generate.py:590`  
**Category:** data-integrity / reproducibility  

```python
# Line 590:
overall = float(np.clip(self._rng.normal(0.967, 0.008), 0.93, 1.0))
```

`make data` → `generate_all_data.py` → `DataGenerator.generate_all()` → writes `output/data/multi_seed_results.json` with `seed_metrics[*].overall ≈ 0.967` (range 0.951–0.982).

**The manuscript claims 44.7% [CI: 43.1%, 46.3%].** Live pipeline execution (`make_pipeline_eval_fn(n_samples=100)`) produces 38–48% per seed. The synthetic data file (96.7%) is never used by the injector (see C-02) so the manuscript is not corrupted — but `multi_seed_results.json` is grossly misleading if read directly.

**Evidence:** Running `make_pipeline_eval_fn()(seed=42)` live returns `overall=0.40`; the stored file says `seed_metrics[0].overall=0.967`.

**Fix:**  
- Option A: Replace `generate_multi_seed_results()` with a real call to `run_multi_seed_stability()`.  
- Option B: Rename the function to `_generate_synthetic_multi_seed_results()` and add a prominent docstring warning that values are synthetic placeholders only.  
- In either case add `REPRODUCE.md` table entry distinguishing `make data` (synthetic scaffolding) vs `python scripts/run_multi_seed.py` (real results).

---

### C-02 · Manuscript injector reads nonexistent key `"overall_metrics"` — manuscript values fall back to hardcoded defaults every run
**File:** `src/manuscript/injector.py:98–109`  
**Category:** data-integrity / doc-drift  

```python
# Lines 98-102 in load_ground_truth():
overall = ms.get("overall_metrics", {})           # always {}
gt["multi_seed_mean_dr"] = overall.get("mean_detection_rate", 0.447)   # → always 0.447
gt["multi_seed_cv"]      = overall.get("cv_detection_rate",  0.097)    # → always 0.097
gt["multi_seed_min_dr"]  = overall.get("min_detection_rate", 0.37)
gt["multi_seed_max_dr"]  = overall.get("max_detection_rate", 0.56)
```

Neither `DataGenerator.generate_multi_seed_results()` nor `scripts/run_multi_seed.py` ever writes an `"overall_metrics"` key. Both write `n_seeds`, `overall_cv`, `seed_metrics`, etc. The injector therefore **always** uses the hardcoded defaults (0.447, 0.097), never the file.

This means the manuscript figures (44.7%, CV=0.097, range 0.37–0.56) are permanently hardcoded fallbacks, not live data. While these values happen to be close to the real pipeline's output (~40-48%), the injection mechanism is broken and will silently fail to update if the pipeline changes.

**Fix:** Update `load_ground_truth()` to read the actual schema:
```python
ms_sm = ms.get("seed_metrics", [])
if ms_sm:
    overall_rates = [m["overall"] for m in ms_sm]
    import statistics as _st
    gt["multi_seed_mean_dr"] = _st.mean(overall_rates)
    gt["multi_seed_cv"]      = ms.get("overall_cv", 0.097)
    gt["multi_seed_min_dr"]  = min(overall_rates)
    gt["multi_seed_max_dr"]  = max(overall_rates)
    gt["multi_seed_n"]       = ms.get("n_seeds", 30)
```
Note: this also requires `make data` to write **real** multi-seed data (C-01) so the injector reads meaningful values.

---

### C-03 · `DataGenerator` stores synthetic ablation/cross-validation/statistical data that is then used as "ground truth" by tests
**File:** `src/data/generate.py:286–560`  
**Category:** data-integrity / genuine vs relabeled integration  

`DataGenerator.generate_ablation_results()` (line 286) hardcodes all component-removal deltas deterministically (`full_tpr = 0.120`, `deltas = [-0.052, -0.019, ...]`), pairwise synergies, and minimal config TPRs — then writes them to `output/data/ablation_results.json`.

`tests/test_manuscript_claims.py` then loads that file and asserts the hardcoded values match the manuscript — effectively asserting that the hardcoded constants equal themselves.

Similarly, `generate_cross_validation_results()` generates `Normal(0.965, 0.008)` cross-validation folds (~96.5% mean TPR) while the real pipeline achieves ~40-48%.

**However:** `output/data/ablation_results.json` was separately confirmed to match what `src/ablation/runner.evaluate_component_subset()` produces live (full pipeline TPR=0.122, detection delta=-0.052). So the ablation numbers happen to be real — DataGenerator was calibrated to match actual run_ablation output.

**Genuine concern:** `cross_validation_results.json` (mean_tpr=0.964) was generated synthetically and never validated against real cross-validation. The real pipeline achieves ~40-48% — the synthetic cross-validation file claiming 96.4% is misleading.

**Fix:**  
- Run `python scripts/run_cross_validation.py` to generate real cross-validation results.  
- Replace `generate_cross_validation_results()` with a real call or clearly label it synthetic.  
- Add `output/data/.real_data_marker` files analogous to those written by `run_full_evaluation.py`.

---

### C-04 · `output/data/full_evaluation_results.json` is synthetic (hardcoded 100%/97.4%) but `test_manuscript_claims.py` asserts these as ground truth
**File:** `src/data/generate.py:229–285`, `tests/test_manuscript_claims.py:123–175`  
**Category:** data-integrity / genuine vs relabeled  

`generate_full_evaluation_results()` hardcodes `base_rates = {"Claude Code": [1.0, 1.0, 1.0, 1.0], "AutoGPT": [0.987, 0.990, 0.960, 0.960], ...}` and writes them as if they were from `run_full_evaluation.py --mode simulation`.

Real simulation mode (`ExperimentRunner.run_full_matrix(adapters, corpus_dict, pipeline=None)`) with seed=42 produces detection_rate=1.0 for Claude Code (all 16 result cells TP=100%), confirmed by live check. So the simulation results happen to be correct.

**However:** The test `test_non_autogpt_architectures_achieve_100_percent` asserts 100% for Claude Code/CrewAI/LangGraph — which is only true because both the real simulator AND the DataGenerator return 1.0 for these architectures under parametric simulation. If the simulator were ever changed, the test would still pass (since it reads the generated file, not re-runs the simulator).

**Fix:** Add a `@pytest.mark.integration` test that actually runs `runner.run_full_matrix()` and checks results agree with `full_evaluation_results.json`, rather than just checking the static file.

---

## HIGH Findings

### H-01 · Stale `"Part 4"` reference in `manuscript/06_discussion.md:86` 
**File:** `manuscript/06_discussion.md:86`  
**Category:** doc-drift (series framing after Part 3+4 merge)

```
Part 4 complements this with domain-calibrated threat profiles ...
```

The series is now three papers (Parts 1, 2, 3+4). `manuscript/07_conclusion.md:65` correctly says "three-part" and references "Part 3+4". The `00_abstract.md` also correctly says "three-part". But `06_discussion.md:86` still references "Part 4" as a separate paper.

`output/pdf/_combined_manuscript.md` at lines 24, 113, 163-165, 2350, 2495–2502 also still references "Part 4" as a separate paper (reflecting an older rendering).

**Fix:** In `manuscript/06_discussion.md:86` replace:
```
Part 4 complements this with domain-calibrated threat profiles --- showing how attack distributions differ ...
and how CIF's temporal parameters must be recalibrated accordingly.
```
→
```
Part 3+4 includes domain-calibrated threat profiles --- showing how attack distributions differ ...
and how CIF's temporal parameters must be recalibrated accordingly.
```
Then re-render PDF to update `output/pdf/_combined_manuscript.md`.

---

### H-02 · Missing citation key `friedman2026cogsec4` — manuscript verification FAILS
**File:** `manuscript/S01_notation_reference.md:5`, `manuscript/references.bib`  
**Category:** broken-citation (manifest-gap)

`scripts/verify_manuscript.py` reports:
```
WARNING - Missing citation key: 'friedman2026cogsec4' in S01_notation_reference.md
Citations: FAIL
```

`S01_notation_reference.md:5` cites `\cite{friedman2026cogsec4}` but there is no corresponding entry in `references.bib` (only cogsec1, cogsec2, cogsec3 are present).

**Fix (option A):** Remove the `\cite{friedman2026cogsec4}` from `S01_notation_reference.md:5` since Part 4 is now merged into Part 3+4.

**Fix (option B):** Add bib entry for the unified Part 3+4 cited as `friedman2026cogsec4`, pointing to the same DOI as `friedman2026cogsec3`.

---

### H-03 · Eight modules below 90% coverage (most are colony/consensus/sandbox)
**Category:** coverage-gap  

| Module | Coverage | Missing lines |
|---|---|---|
| `src/evaluation/benchmark.py` | 77.88% | 80-82, 116-117, 164-165, 193, 199-209 |
| `src/core/consensus.py` | 84.86% | 171, 175, 184-191, 205, 349, 364-372, 443, 458-466, 488-492, 515, 579-602 |
| `src/core/sandbox.py` | 86.07% | 101, 111-116, 126, 140, 247-251, 266-269, 282-328, 357-365 |
| `src/colony/quorum_manipulation.py` | 86.02% | 36-45, 59-60, 116→114 |
| `src/colony/emergent_misalignment.py` | 86.60% | 38-47, 61-62, 102→98 |
| `src/colony/sybil_infiltration.py` | 86.60% | 37-46, 60-61, 125→122 |
| `src/analysis/information_geometry.py` | 86.15% | 57, 77, 106, 119, 163, 209, 213, 247, 309 |
| `src/agents/multiagent_system.py` | 88.28% | 218, 306, 387-392, 413 |

All 8 are above the current 93.50% total floor but dragging it down. Each has uncovered branches corresponding to edge-case paths (zero-weight guards, empty-collection guards, error-handler fallbacks).

**Fix:** Follow the targeted gap-closing technique from the skill:
- Colony modules: uncovered lines 37-47 are typically `__init__` body branches — add tests with non-default constructor args.
- `core/consensus.py`: lines 184-191 are weighted vote submission edge cases (already documented in H-05 of prior audit); add tests with zero-weight votes and empty vote lists.
- `evaluation/benchmark.py:80-82,116-117,164-165`: check what condition these guard (likely empty-results guards or exception paths).

---

### H-04 · `src/__main__.py` at 52.58% coverage (CLI entry point)
**File:** `src/__main__.py:21,26-63,102→105,148-158`  
**Category:** coverage-gap  

Only 47.42% of the CLI entry point is covered. Lines 26-63 (`cmd_evaluate`) and 148-158 (`cmd_verify`) are uncovered. The `cmd_evaluate` function is the primary research reproduce-ability entry point.

**Fix:** Add subprocess-based tests for `python -m src evaluate --seed 42` (with `--seed 1` for speed) and `python -m src verify` in `tests/test_main_cli.py` or `test_main_extended.py`.

---

## MEDIUM Findings

### M-01 · `from __future__ import annotations` is inside the module docstring in `src/statistics/__init__.py`
**File:** `src/statistics/__init__.py:1-2`  
**Category:** dead-code / anti-pattern

```python
# Lines 1-2:
"""Statistical analysis package for the Cognitive Security Framework.
from __future__ import annotations
```

`from __future__ import annotations` is on line 2, **inside** the opening `"""` — it is part of the docstring string literal and never executes. Python 3.10+ tolerates this silently (string annotations work without it) but the annotation is misleading and dead.

**Fix:** Move `from __future__ import annotations` to before the opening `"""`:
```python
from __future__ import annotations

"""Statistical analysis package ..."""
```
Then add `"src/statistics/__init__.py"` to `[tool.ruff.lint.per-file-ignores]` for E402 if ruff flags it.

---

### M-02 · Three bare `except: pass` / silent exception swallowing in `detection.py` and `composable.py`
**Files:**
- `src/core/detection.py:259-260` — `except (TypeError, KeyError, ValueError, AttributeError): pass`
- `src/core/detection.py:287-288` — same pattern in `is_anomalous()`
- `src/visualization/composable.py:289-290` — `except Exception: pass` in `to_svg_string()`

**Category:** code-quality / anti-pattern

Bare `pass` in exception handlers silently discards errors. Any extractor that raises `AttributeError` due to a programming error will be silently swallowed.

**Fix:**
```python
# Replace both detection.py occurrences:
except (TypeError, KeyError, ValueError, AttributeError):
    pass
# → 
except (TypeError, KeyError, ValueError, AttributeError) as _exc:
    import logging as _lg
    _lg.getLogger(__name__).debug("Feature extraction skipped: %s", _exc)

# composable.py line 289-290:
except Exception:
    pass
# →
except Exception as _exc:
    import logging as _lg
    _lg.getLogger(__name__).debug("graphviz pipe failed, using ASCII fallback: %s", _exc)
```

---

### M-03 · `test_statistics.py:1135` `test_six_architectures_scenario` references "6-architecture comparison from manuscript"
**File:** `tests/test_statistics.py:1135`  
**Category:** dead-code / stale test label  

The test docstring says "Simulate the 6-architecture comparison from the manuscript" but the manuscript has 4 architectures (Claude Code, AutoGPT, CrewAI, LangGraph). The test generates 6 synthetic groups unrelated to any real manuscript claim.

**Fix:** Rename the test to `test_kruskal_wallis_multi_group_scenario` and update its docstring to "Test Kruskal-Wallis with 6 groups of different means."

---

### M-04 · `src/data/generate.py` docstrings inaccurately claim outputs "match run_*.py output"
**File:** `src/data/generate.py:286,353,390,442,482,568`  
**Category:** doc-drift / misleading docstring  

Multiple `generate_*()` methods say "matching run_*.py output" when they produce synthetic data diverging significantly from real pipeline runs:
- `generate_cross_validation_results()` (line 442): "matching run_cross_validation.py output" — but produces ~96.5% vs real ~40-48%
- `generate_multi_seed_results()` (line 568): "matching run_multi_seed.py output" — but produces ~96.7% vs real ~40-48%  
- `generate_full_evaluation_results()` (line 229): "matching run_full_evaluation.py output" — happens to be accurate for parametric simulation mode (Claude Code 100%)

**Fix:** Update docstrings to say "synthetic schema-compliant placeholder data for figure generation; see scripts/run_*.py for empirically-measured values."

---

### M-05 · `REPRODUCE.md` table says `make data` → "Generate synthetic evaluation data" but doesn't explain the distinction with real experiment scripts
**File:** `REPRODUCE.md:31`  
**Category:** doc-drift / reproducibility manifest gap  

Current text: `| make data | Generate synthetic evaluation data |`

Readers attempting to reproduce manuscript results may not understand that:
1. `make data` generates schema-compatible synthetic data for figure rendering
2. Real experimental results require separate `python scripts/run_full_evaluation.py`, `run_ablation.py`, `run_multi_seed.py`, `run_colony_benchmarks.py`
3. LLM results require Ollama with `gemma3:4b` installed

**Fix:** Expand `REPRODUCE.md` with a "Synthetic vs. Real Data" section that maps each data file to its source script and notes which require external services.

---

## LOW Findings

### L-01 · CV claim inconsistency: manuscript says CV=0.097 but injector always falls back to hardcoded 0.097 regardless of what `multi_seed_results.json` contains
**File:** `src/manuscript/injector.py:99`, `manuscript/05_results.md:30`  
**Category:** data-integrity / low severity (value happens to be approximately correct)  

The live pipeline with `n_samples=100` over 30 seeds produces CV ≈ 0.065–0.080 (seeds 1-30 in live check showed CV of the real make_pipeline_eval_fn). The stored DataGenerator CV is 0.00651 (synthetic tight). The manuscript claims CV=0.097, which is the hardcoded injector default. This is a plausible value for the real pipeline but is not verified by any stored data.

**Fix:** Run `scripts/run_multi_seed.py`, compute CV from real results, and update injector to read `overall_cv` from the file.

---

### L-02 · `output/pdf/_combined_manuscript.md` still contains stale "four-part series" framing
**File:** `output/pdf/_combined_manuscript.md:24,113,163,164,165,2495,2500`  
**Category:** doc-drift (stale rendered output)  

The PDF combined manuscript (last rendered) references "four-part series" and a separate "Part 4: Applications". This is the rendered output from before the Parts 3+4 merge. Since `manuscript/00_abstract.md` and `07_conclusion.md` are already updated to "three-part", re-rendering will fix this.

**Fix:** Re-render: `uv run python scripts/pipeline/stage_03_render.py --project working/cognitive_integrity/cogsec_multiagent_2_computational --skip-manuscript-hydration`

---

### L-03 · `src/utils/random_seed.py:50` has one uncovered line — `return _GLOBAL_RNG` inside `if _GLOBAL_RNG is None:` branch  
**File:** `src/utils/random_seed.py:50` (89.47% coverage)  
**Category:** coverage-gap (minor)  

The uncovered line is the fallback return in `get_rng()` when `_GLOBAL_RNG is None`. Tests likely call `set_global_seed()` first.

**Fix:** Add one test that calls `get_rng()` on a fresh import (module-level state reset), e.g.:
```python
def test_get_rng_initializes_with_default():
    from utils import random_seed as rs_mod
    rs_mod._GLOBAL_RNG = None  # reset state
    rng = rs_mod.get_rng()
    assert rng is not None
```

---

## VERIFIED PASSING (do not touch)

- ✅ **2,283 tests pass** (0 failures, 0 errors) — stable baseline confirmed
- ✅ **93.50% total coverage** — above 90% gate  
- ✅ **Ruff: clean** — 0 violations
- ✅ **mypy: 0 errors** — `[tool.mypy]` config correct with `mypy_path = "src"`, `explicit_package_bases = true`
- ✅ **`src/__main__.py` CLI** — constructor is correct (`ExperimentRunner(config)` + `run_full_matrix()`), confirmed fixed from prior audit
- ✅ **4 architectures (Claude Code, AutoGPT, CrewAI, LangGraph)** — all implemented and tested; `docs/framework_validation.md:7` correctly says "four distinct multiagent architectural patterns"; no metagpt.py or camel.py stubs exist
- ✅ **Ablation values (12% TPR, ΔTPR=-0.052 detection)** — confirmed by live `evaluate_component_subset()` call: TPR=0.122, delta=-0.052
- ✅ **Colony benchmarks** — `output/data/colony_results.json` is from real `ColonyBenchmark.run_all(seed=42)`, confirmed by exact match to live run (recruitment_poisoning DR=0.814, emergent_misalignment DR=0.561, FPR=0.466)
- ✅ **Manuscript 44.7% claim is plausible** — live `make_pipeline_eval_fn()(seed=42)` returns 0.40; seeds 1-3 return 0.38, 0.45, 0.48 — range consistent with claimed 0.37-0.56
- ✅ **Seed handling** — `set_global_seed(42)` is deterministic; `ExperimentRunner` uses an isolated `np.random.default_rng(seed)` — no global state contamination
- ✅ **No mock frameworks** — confirmed clean (`verify_no_mocks.py` and `grep` over tests/)
- ✅ **No TODO/FIXME/NotImplementedError in src/** — clean
- ✅ **Top synergy pair firewall+detection=0.026** — matches stored `ablation_results.json` and manuscript claim
- ✅ **`from __future__ import annotations` in `src/__main__.py`** — correctly placed (line 12, before docstring)
- ✅ **`ExperimentRunner._simulate_detection()` Modes 1/2/3** — all three paths implemented with proper fallback chain
- ✅ **ExperimentRunner.run_single_llm()** — real implementation, not a stub
- ✅ **LLM evaluator lazy-import pattern** — correctly uses `import requests` + `from agents.llm_agent import OllamaConfig` at call time
- ✅ **statistics package** — comprehensive (10 submodules: hypothesis, effect_size, confidence, nonparametric, regression, anova, sensitivity, stability, cross_validation, assumptions, bayesian, analysis_runner)
- ✅ **Manuscript verification** passes on Files/Labels/Images/Style/Tables/DuplicateLabels/FigAccessibility
- ✅ **`config.yaml`** — correctly says "three-part series" and references Part 3+4

---

## PRIORITIZED SPRINT PLAN

### Sprint 1 — Fix Data Integrity (highest priority, unblocks reproducibility)
1. **C-02**: Fix `injector.py:load_ground_truth()` to read correct `seed_metrics` key
2. **C-01**: Replace `generate_multi_seed_results()` synthetic Normal(0.967) with real pipeline call, OR add explicit synthetic labeling
3. **C-03**: Run `scripts/run_cross_validation.py` to replace synthetic cross-validation data
4. **H-02**: Fix missing `friedman2026cogsec4` citation (remove or add bib entry)
5. **H-01**: Update `manuscript/06_discussion.md:86` "Part 4" → "Part 3+4"

### Sprint 2 — Coverage Gaps
6. **H-03**: Close 8 modules below 90% (colony modules, consensus, sandbox) — target +1.5pp
7. **H-04**: Add subprocess CLI tests for `cmd_evaluate` and `cmd_verify` in `__main__.py`
8. **L-03**: Add `get_rng(None)` test for `random_seed.py` line 50

### Sprint 3 — Code Quality
9. **M-01**: Fix `from __future__` inside docstring in `src/statistics/__init__.py`
10. **M-02**: Replace bare `pass` with `logger.debug(...)` in detection.py:260,288 and composable.py:290
11. **M-03**: Rename `test_six_architectures_scenario` test

### Sprint 4 — Documentation
12. **M-04**: Update `DataGenerator` method docstrings to say "synthetic placeholder"
13. **M-05**: Expand `REPRODUCE.md` with "Synthetic vs. Real Data" section
14. **L-02**: Re-render PDF to fix stale four-part framing in combined manuscript

---

*End of audit. No files were modified.*
