# Part 1 (cogsec_multiagent_1_theory) — Audit Report
**Date:** 2026-07-13  
**Auditor:** Hermes Agent (subagent)  
**Commands run:** pytest + coverage, mypy, ruff, AST analysis, no-mocks check, manuscript verify

---

## EXECUTIVE SUMMARY

| Category | Count | Severity |
|----------|-------|----------|
| Broken `from __future__` (inside docstring) | 6 files | HIGH |
| mypy errors | 59 errors across 11 files | HIGH |
| Coverage gaps below 90% | 2 modules | HIGH |
| Missing `[tool.mypy]` config | 1 | MEDIUM |
| Misplaced shebang (not line 1) | 15 files | MEDIUM |
| Duplicate/redundant docstrings | 15 files | MEDIUM |
| `calibrate_baseline()` success path untested | 1 | MEDIUM |
| `pass` in exception handler | 1 | MEDIUM |
| Doc/README stale test counts | 3 claims | LOW |
| `UserWarning: Glyph missing from font` | 39 warnings (1 test) | LOW |
| Missing return type hints | 38 functions | LOW |

**Overall health:** CI gate passes (96.07% coverage ≥ 90%, ruff clean, 350/350 tests pass). No mock violations. Manuscript verify: PASS. Data generation: reproducible (seed=42). No `TODO/FIXME/NotImplementedError`.

---

## HIGH

### H-01 — `from __future__ import annotations` trapped inside docstring
- **Files:** `src/trust.py:2`, `src/tripwire.py:2`, `src/provenance.py:2`, `src/visualization/attack_surface.py:2`, `src/visualization/trust_decay.py:2`, `src/visualization/trust_network.py:2`
- **Category:** broken-impl
- **Detail:** Each of these files begins with a bare `"""` on line 1 (opening a docstring), then has `from __future__ import annotations` on line 2 — *inside the docstring*. AST confirms the import is not present as an executable node (`ast.ImportFrom`), meaning it never executes. Python 3.10+ with PEP 563 deferred evaluation is NOT active in these modules.
- **Evidence:**
  ```
  src/trust.py:1:  '"""'
  src/trust.py:2:  'from __future__ import annotations'
  src/trust.py:3:  ''
  src/trust.py:4:  'Trust Calculus for Multiagent Systems.'
  ```
  AST verification: `from __future__ import annotations` absent from AST in 6 files, present in 24 others.
- **Fix:** Move `from __future__ import annotations` BEFORE the opening `"""`. Add each file to `[tool.ruff.lint.per-file-ignores]` with `["E402"]` to suppress the resulting import-position lint error.

### H-02 — 59 mypy errors across 11 source files
- **Files (error count):**
  - `src/visualization/cif_comprehensive.py`: 16 errors
  - `src/visualization/comprehensive_taxonomy.py`: 11 errors
  - `src/visualization/attack_timeline.py`: 11 errors
  - `src/visualization/detection_results.py`: 7 errors
  - `src/data_generation.py`: 4 errors
  - `src/visualization/trust_calculus.py`: 3 errors
  - `src/consensus.py`: 3 errors
  - `src/visualization/trust_network.py`: 1 error
  - `src/visualization/trust_decay.py`: 1 error
  - `src/verification.py`: 1 error
  - `src/provenance.py`: 1 error
- **Category:** mypy-error
- **Detail:** `Found 59 errors in 11 files (checked 32 source files)`. Key error classes:
  1. **`[arg-type]`** in `cif_comprehensive.py` (16) and `comprehensive_taxonomy.py` (11): `object` typed dict values from untyped list of dicts passed to matplotlib `ax.text()` and `FancyBboxPatch`. Fix: type data as `list[Any]` or `list[dict[str, Any]]`.
  2. **`[call-overload]`** in `attack_timeline.py` (11): `np.random.Generator.normal()` called with `numpy.bool[builtins.bool]` third arg — result of `np.random.choice([True, False])`. Cast to `int | None` or use `size=None`.
  3. **`[assignment]`** in `detection_results.py` (7): `ndarray` assigned to `list[float]` variables and vice versa. Fix: annotate as `np.ndarray` or `list[float]` consistently.
  4. **`[index]`** in `data_generation.py` (3): `Collection[str]` is not indexable. Fix: annotate as `list[str]` or `Sequence[str]`.
  5. **`[override]`** in `consensus.py` (3): `WeightedByzantineConsensus.submit_vote(vote: WeightedVote)`, `ConfidenceByzantineConsensus.submit_vote(vote: ConfidenceVote)`, and `CombinedByzantineConsensus.submit_vote(vote: CombinedVote)` narrow the base class argument type. Fix: use `Union` on base or add `# type: ignore[override]`.
  6. **`[arg-type]`** in `trust_network.py` (1): `list[float]` passed to `tight_layout(rect=...)` — expects `tuple[float, float, float, float] | None`.
  7. **`[attr-defined]`** in `trust_decay.py` (1): `np.viridis` — should be `plt.get_cmap("viridis")` or `matplotlib.colormaps["viridis"]`.
  8. **`[var-annotated]`** in `provenance.py:294`, `verification.py:79`: untyped `set()` assignments.
- **Fix:** Add `[tool.mypy]` block to `pyproject.toml` (see M-01), then fix per-file errors.

### H-03 — `src/visualization/detection_results.py` at 83.33% coverage
- **File:** `src/visualization/detection_results.py`, Miss lines: 42-43, 64, 99-117, 162-170
- **Category:** coverage-gap
- **Detail:** Three distinct uncovered code paths:
  1. Lines 42-43: `data_path` not found → `print(...)` + `return output_dir / "error.pdf"` — early exit when detection data file missing
  2. Line 64: `return [0.0] * 5` — fallback when ablation list is empty
  3. Lines 99-117: Data-file load path for `ablation_results.json` (when the file exists and is read with `json.load`)
  4. Lines 162-170: CSV `DictReader` path reading `integrity_timeseries.csv` columns
- **Fix:** Add tests that (1) call with no data file present, (2) create the data files at `output_dir.parent/data/` before calling, as in the `roc_curves` data-file branch test pattern already in `test_visualization.py`.

### H-04 — `src/visualization/scalability.py` at 94.29%
- **File:** `src/visualization/scalability.py`, Miss lines: 54-55, 138-139
- **Category:** coverage-gap
- **Detail:**
  - Lines 54-55: `print(f"Data file not found...")` + early return — data file missing path
  - Lines 138-139: `except (np.linalg.LinAlgError, ValueError): pass` — exception handler for degenerate `polyfit`
- **Fix:** Add test calling with no data file; add test injecting 2 or fewer data points to trigger the polyfit exception path.

---

## MEDIUM

### M-01 — No `[tool.mypy]` configuration in `pyproject.toml`
- **File:** `pyproject.toml`
- **Category:** code-quality
- **Detail:** `pyproject.toml` has no `[tool.mypy]` section. mypy runs with no config, so path discovery (for `src/` layout), `ignore_missing_imports`, and `explicit_package_bases` must be passed on the CLI. This makes CI mypy non-idiomatic and misses the opportunity to centralize type config.
- **Fix:** Add:
  ```toml
  [tool.mypy]
  mypy_path = "src"
  explicit_package_bases = true
  ignore_missing_imports = true
  exclude = ["src/__main__.py"]
  ```

### M-02 — Misplaced shebang (`#!/usr/bin/env python3`) in 15 source files
- **Files:** `src/data_generation.py:6`, `src/visualization/ablation_study.py:6`, `src/visualization/attack_timeline.py:6`, `src/visualization/belief_sandbox.py:6`, `src/visualization/cif_architecture.py:6`, `src/visualization/cif_comprehensive.py:6`, `src/visualization/comprehensive_taxonomy.py:6`, `src/visualization/defense_composition.py:6`, `src/visualization/detection_performance.py:6`, `src/visualization/detection_results.py:6`, `src/visualization/fp_mitigation.py:6`, `src/visualization/roc_curves.py:6`, `src/visualization/scalability.py:6`, `src/visualization/threat_taxonomy.py:6`, `src/visualization/trust_calculus.py:6`
- **Category:** code-quality
- **Detail:** Each file has a module docstring on lines 1-4, then `#!/usr/bin/env python3` on line 6. A shebang is only meaningful when it is the **very first line** of a file. On line 6 it is dead string literal (treated as a bare expression statement). These files are not executable scripts — they are imported modules in `src/`. The shebang is never useful here.
- **Fix:** Remove the `#!/usr/bin/env python3` lines from all 15 files.

### M-03 — Duplicate/redundant docstrings in 15 source files
- **Files:** same 15 as M-02
- **Category:** code-quality
- **Detail:** Each of these files has a machine-generated "stub" docstring on lines 1-4 (e.g. `"""Ablation Study module.\n\nPart of the Cognitive Integrity Framework.\n"""`), then a second, more descriptive docstring on line 9 (e.g. `"""Ablation study visualization module."""`). The first is the active Python module docstring (it is what `__doc__` contains), making the second unreachable as a docstring (it becomes a bare string expression).
- **Fix:** Remove the redundant first-line stub docstrings (lines 1-4) from the 15 affected files, keeping the specific second docstring as the module's `__doc__`.

### M-04 — `calibrate_baseline()` success path never tested
- **File:** `src/detection.py:58-61`, `tests/test_detection.py`
- **Category:** test-gap
- **Detail:** Lines 58-61 (the success path of `calibrate_baseline()` — stacking observations into arrays and setting `_calibrated = True`) are never executed by the test suite. `tests/test_detection.py` has exactly one test for this method (`test_calibrate_baseline_insufficient_samples_raises`), which only exercises the `ValueError` path.
- **Fix:** Add a test that adds ≥50 observations then calls `calibrate_baseline()` successfully, asserting `detector._calibrated is True` and that `compute_drift` subsequently works.

### M-05 — `except (np.linalg.LinAlgError, ValueError): pass` silences real errors
- **File:** `src/visualization/scalability.py:138-139`
- **Category:** code-quality  
- **Detail:** A bare `pass` in an exception handler silences `LinAlgError` and `ValueError` during the `np.polyfit` call without logging. Runtime errors from bad data would be invisible.
- **Fix:** Replace `pass` with `logger.debug("polyfit failed: %s", exc, exc_info=True)` (add `exc` to the `except` clause).

### M-06 — Font glyph warnings in `comprehensive_taxonomy.py`
- **File:** `src/visualization/comprehensive_taxonomy.py`
- **Category:** code-quality
- **Detail:** 39 `UserWarning: Glyph NNNN (\N{...}) missing from font(s) Times New Roman` warnings during test execution. Affected characters: subscript numerals (₁₂₃₄₅), warning sign (⚠), high voltage (⚡), fisheye (◉), white hexagon (⬡). These render as blank/tofu in the PDF figure.
- **Fix:** Replace Unicode special characters with LaTeX mathtext alternatives (`$_1$`, etc.) or switch to a font that supports these glyphs (DejaVu Sans, Noto Sans).

---

## LOW

### L-01 — README.md stale test counts
- **File:** `README.md:35,78,79`
- **Category:** doc-drift
- **Detail:**
  - Line 35: `12 test files` — actual is **13** (`test_cif_ad_coupling.py`, `test_consensus.py`, `test_data_generation.py`, `test_detection.py`, `test_firewall.py`, `test_invariants.py`, `test_ooda_monitor.py`, `test_provenance.py`, `test_sandbox.py`, `test_tripwire.py`, `test_trust.py`, `test_verification.py`, `test_visualization.py`)
  - Line 78: `test_ooda_monitor.py: 51 tests` — actual is **42**
  - Line 79: `test_cif_ad_coupling.py: 32 tests` — actual is **41**
- **Fix:** Update all three counts.

### L-02 — 38 functions missing return type hints
- **Files:** `src/detection.py`, `src/verification.py`, `src/firewall.py`, `src/tripwire.py`, `src/sandbox.py`, `src/consensus.py`, `src/trust.py`, `src/provenance.py`, `src/invariants.py`
- **Category:** missing-type-hint
- **Detail:** 38 `__init__` and `run_all` functions lack `-> None` return annotations. Example: `src/detection.py:36 __init__()`, `src/verification.py:207 run_all()`.
- **Fix:** Add `-> None` to all `__init__` and `run_all` method signatures.

### L-03 — `detection.py:233` zero-`baseline_std` branch untested
- **File:** `src/detection.py:233`
- **Category:** coverage-gap
- **Detail:** Line 233 (`z = 0.0` when `extractor.baseline_std == 0`) is never reached. Tests always use calibrated extractors with non-zero std.
- **Fix:** Add test with `extractor.baseline_std = 0.0` directly to exercise the zero-std branch.

### L-04 — Visualization modules with single uncovered `output_dir.mkdir` line
- **Files (11 modules):** `attack_surface.py:28`, `attack_timeline.py:28`, `cif_architecture.py:33`, `cif_comprehensive.py:26`, `comprehensive_taxonomy.py:26`, `defense_composition.py:27`, `detection_performance.py:26`, `fp_mitigation.py:26`, `threat_taxonomy.py:26`, `trust_calculus.py:27`, `trust_network.py:29`
- **Category:** coverage-gap
- **Detail:** All test calls pass an already-existing tmpdir, so the `mkdir` guard (`output_dir.mkdir(parents=True, exist_ok=True)`) always finds the directory. Only 1 line per module uncovered.
- **Fix:** In one test per module, pass a `Path(tmpdir) / "subdir"` that doesn't exist yet, forcing the `mkdir` branch to execute.

---

## VERIFICATION CHECKS PASSED

| Check | Result |
|-------|--------|
| `pytest` 350/350 pass | ✅ PASS |
| Coverage ≥ 90% gate (`fail_under = 90`) | ✅ PASS (96.07%) |
| `ruff check src/ tests/ scripts/` | ✅ PASS (0 violations) |
| No mock violations (`MagicMock`, `unittest.mock`, `mocker.patch`) | ✅ PASS |
| Manuscript `verify_manuscript.py` | ✅ PASS (Files, Citations, Labels/Refs, Images/Links, Style) |
| `scripts/06_generate_data.py` | ✅ PASS (5 data files generated) |
| `src/__init__.py` all 60 `__all__` exports present | ✅ PASS |
| `src/visualization/__init__.py` all 17 `__all__` exports present | ✅ PASS |
| No `TODO/FIXME/NotImplementedError` in `src/` | ✅ PASS |
| No skipped or xfail tests | ✅ PASS |
| Reproducibility: `np.random.seed(42)` in all data-generating modules | ✅ PASS |
| Figure scripts: no unseeded random calls | ✅ PASS |
| Series framing (Part 1–3, not 4) in AGENTS.md/README.md | ✅ PASS |
| `from __future__ import annotations` active (in AST) — 24/30 non-init modules | ✅ PASS for 24; HIGH finding for 6 |

---

## PRIORITIZED TODO LIST (Sprint Plan)

### Sprint 1 — Fix trapped `__future__` and add mypy config (unblocks type safety)
1. **H-01**: Move `from __future__ import annotations` before opening `"""` in 6 files
2. **M-01**: Add `[tool.mypy]` block to `pyproject.toml`

### Sprint 2 — mypy fixes (type safety, 59 errors)
3. **H-02a**: Type data dicts as `list[Any]` in `cif_comprehensive.py` and `comprehensive_taxonomy.py` (27 errors)
4. **H-02b**: Fix `attack_timeline.py` `np.random.normal()` `call-overload` — add `int()` cast (11 errors)
5. **H-02c**: Fix `detection_results.py` ndarray/list assignments (7 errors)
6. **H-02d**: Fix `data_generation.py` `Collection[str]` → `list[str]` (3 errors)
7. **H-02e**: Fix `consensus.py` `[override]` errors (3 errors)
8. **H-02f**: Fix single-error files: `trust_network.py`, `trust_decay.py`, `verification.py`, `provenance.py`

### Sprint 3 — Coverage gaps
9. **H-03**: Add data-file branch tests for `detection_results.py` (3 test cases)
10. **H-04**: Add missing-data-file + polyfit-error tests for `scalability.py`
11. **M-04**: Add `calibrate_baseline()` success-path test
12. **L-03**: Add zero-`baseline_std` branch test for `detection.py:233`
13. **L-04**: Add `output_dir` non-existent path tests for 11 visualization modules

### Sprint 4 — Code quality cleanup
14. **M-02**: Remove misplaced shebangs from 15 files
15. **M-03**: Remove duplicate stub docstrings from 15 files
16. **M-05**: Replace `pass` with `logger.debug(...)` in scalability exception handler
17. **M-06**: Fix Unicode glyph warnings in `comprehensive_taxonomy.py`
18. **L-01**: Update README.md test count claims (12→13 files, 51→42 OODA, 32→41 CIF-AD)
19. **L-02**: Add `-> None` to 38 `__init__` / `run_all` methods
