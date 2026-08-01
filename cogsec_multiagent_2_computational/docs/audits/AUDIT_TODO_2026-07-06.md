# Deep Audit TODO — cogsec_multiagent_2_computational
**Audit Date:** 2026-07-06  
**Auditor:** Hermes Agent (automated)  
**Baseline:** 2128 tests, 2128 passed, total coverage 89.78% (FAIL: <90% threshold), 247 ruff errors

---

## EXECUTIVE SUMMARY

| Category | Count | Worst Severity |
|---|---|---|
| Coverage failures | 1 (aggregate) + 20 modules below 90% | HIGH |
| Ruff lint violations | 247 (133 E501, 86 E402, 15 I001, 13 F401, 3 other) | MEDIUM |
| mypy type errors | 150 errors in 39 files | HIGH |
| Missing type hints on functions | 49 functions | MEDIUM |
| Critical API mismatch in `__main__.py` | 2 errors | HIGH |
| SKILL.md test count stale | claims "1700+" but suite has 2128 | LOW |
| Missing architecture modules | metagpt.py, camel.py absent from src/ | HIGH |
| Unused import (legacy `numpy.trapz`) | 1 mypy false positive (handled at runtime) | LOW |
| Spec verifiers skip when tools not installed | NuSMV/SPIN/TLA+ all SKIP | MEDIUM |
| coverage/visualization/composable.py | 20.61% coverage — major gap | HIGH |
| evaluation/llm_evaluator.py | 25.00% coverage — major gap | HIGH |
| evaluation/benchmark.py | 77.88% coverage | MEDIUM |
| formal/category_theory_advanced.py | 81.46% coverage | MEDIUM |
| colony/* several modules | 86-89% coverage | MEDIUM |
| Recruiment_poisoning lazy-import anti-pattern | `_ColonyResult` local fallback | MEDIUM |
| consensus.py submit_vote override mismatches | 3 subclasses override with incompatible types | HIGH |
| analysis/information_geometry.py | 86.15% coverage | MEDIUM |
| `save_figure()` accepts str but callers pass Path | mypy arg-type errors in 4 figure modules | MEDIUM |
| `__main__.py` uses `ExperimentRunner(seed=...)` | constructor takes no `seed` kwarg | CRITICAL |
| `colony/recruitment_poisoning.py` import dance | fragile late-import pattern | MEDIUM |
| Manuscript hyperbole warnings | "perfect" used in 2 sections | LOW |
| REPRODUCE.md `uv sync --extra dev` stale | project uses `[dependency-groups]`, not `[extras]` | MEDIUM |

---

## CRITICAL

### C-01: `__main__.py` passes `seed=` to `ExperimentRunner` which doesn't accept it
- **File:** `src/__main__.py:28`
- **Category:** broken-impl, mypy-error
- **Error:** `ExperimentRunner(seed=args.seed)` — mypy reports "Unexpected keyword argument 'seed'". `ExperimentRunner.__init__` takes only `config: Optional[ExperimentConfig]`.
- **Fix:** Either update `ExperimentRunner.__init__` to accept `seed: int` and wire it to `ExperimentConfig`, or build the config first: `ExperimentRunner(config=ExperimentConfig(seed=args.seed))`.
- **Impact:** CLI `python -m src evaluate` is broken at runtime.

### C-02: `__main__.py` calls `runner.run()` but method doesn't exist
- **File:** `src/__main__.py:29`
- **Category:** broken-impl, mypy-error
- **Error:** `result = runner.run()` — mypy reports `"ExperimentRunner" has no attribute "run"`. Public API is `run_single()` and `run_full_matrix()`.
- **Fix:** Replace with a meaningful demonstration call, e.g. `run_full_matrix` or add a `run()` convenience method to `ExperimentRunner`.
- **Impact:** CLI `python -m src evaluate` raises `AttributeError` at runtime.

---

## HIGH

### H-01: Total test coverage 89.78% — fails `fail_under=90` gate
- **File:** `pyproject.toml` (`fail_under = 90`)
- **Category:** coverage-gap
- **Modules dragging average below threshold:** `src/visualization/composable.py` (20.61%), `src/evaluation/llm_evaluator.py` (25.00%), `src/visualization/figures/ablation_study.py` (78.18%), `src/evaluation/benchmark.py` (77.88%), `src/formal/category_theory_advanced.py` (81.46%), `src/formal/free_energy.py` (81.37%), `src/formal/nusmv_spec.py` (81.58%), `src/formal/spin_spec.py` (81.08%), `src/manuscript/verifier.py` (82.29%).
- **Fix:** See individual HIGH/MEDIUM items below. Critical path: `composable.py` tests would add the most coverage points.

### H-02: `src/visualization/composable.py` — 20.61% coverage (504 lines, 375 uncovered)
- **File:** `src/visualization/composable.py`
- **Category:** coverage-gap, test-gap
- **Detail:** `DefenseGraph`, `CategoryDiagram`, `LatticeViz`, `OperadPlot`, `MonadFlow`, `LensDiagram` classes have essentially no test coverage. Only ASCII fallback paths are exercised.
- **Fix:** Add `tests/test_composable_engine.py` with tests for each renderer class — ASCII fallback (no graphviz required), config roundtrips, node/edge counts, and `render()` output type assertions. Should bring this to >90%.

### H-03: `src/evaluation/llm_evaluator.py` — 25.00% coverage (lines 116-169 uncovered)
- **File:** `src/evaluation/llm_evaluator.py:116-169`
- **Category:** coverage-gap, test-gap
- **Detail:** The entire main loop of `run_llm_evaluation` (adapter loop, category sampling, `runner.run_single_llm` calls) is uncovered. The test suite only covers the error path (Ollama unreachable) and `DEMO_ATTACKS` constant.
- **Fix:** Add a `pytest-httpserver`-based integration test that stubs Ollama's `/api/tags` and `/api/generate` endpoints, runs `run_llm_evaluation` with a single adapter/category, and asserts the result list is non-empty. Mark with `@pytest.mark.requires_ollama` for real integration; use httpserver for the stubbed path.

### H-04: Missing architecture modules (`metagpt.py`, `camel.py`)
- **File:** `src/architectures/` — only has `autogpt.py`, `base.py`, `claude_code.py`, `crewai.py`, `langgraph.py`
- **Category:** doc-drift, stub-impl
- **Detail:** `README.md`, `AGENTS.md`, `src/AGENTS.md`, and the top-level `README.md` all list **six** architectures: Claude Code, AutoGPT, CrewAI, LangGraph, MetaGPT (SOP-driven), CAMEL (Debate). The actual `src/architectures/` directory is missing `metagpt.py` and `camel.py`. `docs/framework_validation.md` says "six target architectures" but only 4 are present.
- **Fix:** Either (a) implement `metagpt.py` and `camel.py` adapters inheriting from `base.py`, or (b) remove all references to them from docs and revise the count from "six" to "four" throughout.

### H-05: `consensus.py` — `submit_vote()` override type incompatibilities (3 subclasses)
- **File:** `src/core/consensus.py:322`, `:416`, `:552`
- **Category:** mypy-error, code-quality
- **Detail:** `WeightedByzantineConsensus.submit_vote(vote: WeightedVote)`, `ConfidenceByzantineConsensus.submit_vote(vote: ConfidenceVote)`, and `CombinedByzantineConsensus.submit_vote(vote: CombinedVote)` all override `ByzantineConsensus.submit_vote(vote: Vote)` with incompatible subtypes — Liskov Substitution Principle violation.
- **Fix:** Use `Union[Vote, WeightedVote, ConfidenceVote, CombinedVote]` on the base class, or make `Vote` a generic base class with `TypeVar`, or annotate overrides with `@override` and `# type: ignore[override]` with a comment explaining the intentional contravariance.

### H-06: mypy reports 150 errors across 39 files
- **Category:** mypy-error, code-quality
- **Detail:** Major clusters:
  - `visualization/figures/*` (17+12+11+9+9+9+8+7+7 errors) — all `Axes | ndarray` union-attr errors (matplotlib returns `Axes | np.ndarray` from `plt.subplots()`; callers need to cast to `Axes`).
  - `src/__main__.py` (2 critical errors — see C-01, C-02)
  - `src/evaluation/roc.py:116` — `Module has no attribute 'trapz'` (numpy 2.x removed `trapz`; code handles it at runtime with `getattr` fallback, but mypy still flags the fallback expression)
  - `src/data/generate.py:95` — incompatible type passed to `save()`
  - `src/core/consensus.py` (3 override errors — see H-05)
  - `src/analysis/game_theory.py:103` — incompatible list type assignment
  - `src/colony/recruitment_poisoning.py:91` — type assignment `_ColonyResult` / `ColonyResult` mismatch
  - `src/visualization/figures/attack_surface.py:295,303` — float/int mismatch, Path/str mismatch
  - `src/formal/category_theory_advanced.py:1240` — int/DetectionBound assignment
- **Fix:** Run `mypy src/ --ignore-missing-imports` and fix systematically by module cluster. Priority: `src/__main__.py` (critical runtime), then `visualization/figures/` (mass-fix with `ax: Axes = cast(Axes, fig.subplots(...))` pattern), then `src/core/consensus.py`.

---

## MEDIUM

### M-01: `save_figure()` signature takes `str` but callers pass `Path`
- **Files:** `src/visualization/figures/ablation_study.py:129`, `attack_surface.py:303`, `trust_decay.py:131`
- **Category:** mypy-error, type-hint
- **Detail:** `save_figure(fig, name, output_dir: str)` but callers pass `Path` objects. Works at runtime (Path stringifies) but mypy flags as `[arg-type]`.
- **Fix:** Update `save_figure` signature to accept `output_dir: str | Path` and convert internally: `output_dir = str(output_dir)`.

### M-02: 247 ruff violations — 133 E501 + 86 E402 + 15 I001 + 13 F401
- **Category:** code-quality, lint
- **Breakdown:**
  - **133 × E501 (line too long >100)**: Primarily in `scripts/` (docstrings, print statements). Run `ruff check --select E501 --fix` won't auto-fix, but can be addressed in a single pass.
  - **86 × E402 (module-level import not at top)**: All in `scripts/*.py` — pattern is `sys.path.insert(0, ROOT/"src")` before the package import. Suppress with `# noqa: E402` on each affected import line, or restructure with `if __name__ == "__main__": sys.path.insert(...)`.
  - **15 × I001 (unsorted imports)**: Auto-fixable with `ruff check --select I --fix`. Run it.
  - **13 × F401 (unused imports)**: In test files and scripts. Most are auto-fixable with `ruff check --select F401 --fix`. Notable: `pytest` imported but unused in 7 test files.
- **Fix (priority order):** (1) `ruff check --select I --fix src/ tests/ scripts/` — auto-fixes all I001. (2) `ruff check --select F401 --fix src/ tests/ scripts/` — removes unused imports. (3) Add `# noqa: E402` to scripts with sys.path manipulation. (4) Manually fix E501 lines in scripts.

### M-03: `src/evaluation/benchmark.py` — 77.88% coverage
- **File:** `src/evaluation/benchmark.py:80-82,116-117,164-165,193,199-202,205-209`
- **Category:** coverage-gap
- **Detail:** Error paths (exception handling blocks) and certain edge cases in `ScalabilityBenchmark` are not exercised.
- **Fix:** Add tests for: empty `agent_counts` list, single-element counts list, negative agent counts, and exception paths in the benchmark harness.

### M-04: `src/formal/category_theory_advanced.py` — 81.46% coverage (490 lines, 81 uncovered)
- **File:** `src/formal/category_theory_advanced.py`
- **Category:** coverage-gap
- **Detail:** Large module (490 lines) with many advanced categorical constructions (Kan extensions, lenses, F-algebras) that are under-tested. Uncovered lines include monad law validators, Kan extension computations, and catamorphism implementations.
- **Fix:** Extend `tests/test_category_theory.py` or create `tests/test_category_theory_advanced.py` with tests specifically for: `KanExtension`, `LensOptic`, `FAlgebra`, `CatamorphismRunner`.

### M-05: `src/formal/free_energy.py` — 81.37% coverage
- **File:** `src/formal/free_energy.py:59,74-77,116,118,126,185,225,229,239,244,281,353,362`
- **Category:** coverage-gap
- **Fix:** Add tests for edge-case free energy computations, including near-zero distributions and boundary conditions for KL divergence.

### M-06: `src/formal/spin_spec.py` and `nusmv_spec.py` — ~81% coverage each
- **Files:** `src/formal/spin_spec.py`, `src/formal/nusmv_spec.py`
- **Category:** coverage-gap
- **Detail:** `generate_categorical_promela_spec()` (lines 23-125) and `generate_categorical_nusmv_spec()` (lines 24-142) are uncovered — these are the extended categorical specs.
- **Fix:** The test for `test_spec_verifier.py` probably only exercises `generate_promela_spec()`/`generate_nusmv_spec()` (the parametric ones). Add direct calls to the categorical generators in `test_formal.py`.

### M-07: `src/manuscript/verifier.py` — 82.29% coverage
- **File:** `src/manuscript/verifier.py:91,161,170-175,178,223-226,232,245-249,264,267-275,292-304,329,334`
- **Category:** coverage-gap
- **Detail:** Several warning/error paths and edge case branches are not exercised in `test_manuscript.py`.
- **Fix:** Add edge-case tests: missing `.bib` file, broken `\ref{}` to non-existent label, duplicate figure IDs, accessibility check failure (missing alt text).

### M-08: `src/colony/*` modules — 86-89% coverage, below 90% threshold
- **Files:** `src/colony/belief_cascade.py` (89.04%), `src/colony/emergent_misalignment.py` (86.60%), `src/colony/quorum_manipulation.py` (86.02%), `src/colony/sybil_infiltration.py` (86.60%)
- **Category:** coverage-gap
- **Detail:** All four main colony scenario modules fall below the 90% threshold. Missing: early-exit paths (lines 75→64 style branch misses), error handling, and edge cases with `n_adversaries=0`.
- **Fix:** In `tests/test_colony.py`/`test_colony_stress.py`, add tests for: zero adversaries, maximum adversary fraction (>0.5), and a 1-agent colony edge case.

### M-09: `src/agents/multiagent_system.py` — 88.28% coverage
- **File:** `src/agents/multiagent_system.py:218,306,387-392,413`
- **Category:** coverage-gap
- **Fix:** Test error paths when `llm_config` is malformed, and ensure the `generate_response` fallback path is covered.

### M-10: `src/analysis/information_geometry.py` — 86.15% coverage
- **File:** `src/analysis/information_geometry.py:57,77,106,119,163,209,213,247,309`
- **Category:** coverage-gap
- **Detail:** Fisher information matrix, geodesic computations, and curvature paths are uncovered.
- **Fix:** Extend `tests/test_information_geometry.py` (24 tests exist) to cover Fisher matrix diagonal verification, geodesic length monotonicity, and curvature sign tests.

### M-11: `src/core/consensus.py` — 84.86% coverage
- **File:** `src/core/consensus.py:171,175,184-191,205,...`
- **Category:** coverage-gap
- **Fix:** Add tests for: `WeightedByzantineConsensus` with weight=0 votes, `ConfidenceByzantineConsensus` edge cases, and `CombinedByzantineConsensus` failure paths.

### M-12: `src/core/sandbox.py` — 86.07% coverage
- **File:** `src/core/sandbox.py:101,111-112,116,126,140,...`
- **Category:** coverage-gap
- **Fix:** Extend `tests/test_sandbox.py` to cover TTL expiry paths, promotion criteria boundary conditions, and the sandbox overflow error paths.

### M-13: `colony/recruitment_poisoning.py` uses fragile lazy-import anti-pattern
- **File:** `src/colony/recruitment_poisoning.py:85-91`
- **Category:** code-quality
- **Detail:** Module defines its own `_ColonyResult` and `_ColonyConfig` dataclasses as fallbacks, then does a late `try: from .benchmark import ColonyResult` inside a method. This creates two separate class objects and causes the mypy type assignment error at line 91.
- **Fix:** Refactor to import from `benchmark.py` at module level (same as other colony modules). If circular import is the concern, restructure `benchmark.py` to extract the result dataclass to a `_types.py` module.

### M-14: REPRODUCE.md uses `uv sync --extra dev` — wrong syntax for dependency-groups
- **File:** `REPRODUCE.md`
- **Category:** doc-drift
- **Detail:** `pyproject.toml` uses `[dependency-groups]` (PEP 735 groups, not `[extras]`). The correct invocation is `uv sync` (groups install by default) or `uv sync --group dev`.
- **Fix:** Update REPRODUCE.md: change `uv sync --extra dev` to `uv sync` (dev group is included by default with uv).

### M-15: `src/architectures/base.py` — 89.83% coverage
- **File:** `src/architectures/base.py:84,102,107,115,124,133`
- **Category:** coverage-gap
- **Fix:** Test abstract method contracts and optional override stubs in the base adapter class.

### M-16: `src/utils/random_seed.py` — 89.47% coverage
- **File:** `src/utils/random_seed.py:50`
- **Category:** coverage-gap
- **Fix:** Add test for the `if __name__ == "__main__"` block or the error path in seed validation.

### M-17: 49 functions missing return type hints
- **Category:** missing-type-hint
- **Key files:** `src/visualization/tables/` (5 private functions), `src/visualization/figures/` (10 private helpers), `src/manuscript/verifier.py:30`, `src/core/detection.py:33,175,326` (`__init__` methods), and others.
- **Fix:** Add `-> None` to all `__init__` methods (standard practice). For private helpers like `_load_results()`, add appropriate return types (`-> dict[str, Any]` etc.). Can be done in bulk with a focused pass.

### M-18: `analysis/game_theory.py:103` — type mismatch in Nash equilibrium computation
- **File:** `src/analysis/game_theory.py:103`
- **Category:** mypy-error
- **Detail:** `list[tuple[float, None]]` assigned where `list[tuple[float | None, float | None]]` expected.
- **Fix:** Change the tuple construction to use `Optional[float]` consistently, or cast explicitly.

### M-19: `src/evaluation/roc.py` — `numpy.trapz` deprecated; mypy flags even the fallback
- **File:** `src/evaluation/roc.py:116`
- **Category:** mypy-error
- **Detail:** `_trapz = getattr(np, "trapezoid", None) or np.trapz` — mypy flags `np.trapz` as missing attribute since numpy 2.x. The runtime fallback is correct logic but mypy can't see through `getattr`.
- **Fix:** Change to: `_trapz = np.trapezoid if hasattr(np, "trapezoid") else getattr(np, "trapz")` or add `# type: ignore[attr-defined]` with a comment.

### M-20: Formal verification skips all tools (NuSMV/SPIN/TLA+) — no executable verification
- **File:** `scripts/verify_formal_specs.py`
- **Category:** doc-drift, infra-gap
- **Detail:** `python scripts/verify_formal_specs.py` outputs `[SKIP: NuSMV not found in PATH]` for all three model checkers. The manuscript claims formal verification was performed, but there's no automated CI gate to ensure specs remain valid.
- **Fix options:** (a) Add `tlc` (TLA+ tools), `nusmv`, `spin` installation instructions to REPRODUCE.md with verification steps. (b) Add CI step that at least parses/syntax-checks the generated specs. (c) Add `@pytest.mark.skipif(not shutil.which("nusmv"), reason="NuSMV not installed")` to spec tests to make the skip explicit and visible in test counts.

---

## LOW

### L-01: SKILL.md test count stale — claims "1700+" but suite has 2128 tests
- **File:** `SKILL.md` (frontmatter description), also root `README.md` shows "1700+"
- **Category:** doc-drift
- **Fix:** Update SKILL.md description from "1700+ data-driven tests" to "2100+ data-driven tests". Update README.md's "Colony stress tests: 23 new stress tests" to match current count.

### L-02: Manuscript hyperbole warnings — "perfect" used in 2 sections
- **Files:** `manuscript/04_experimental_setup.md:49`, `manuscript/05_results.md:126`
- **Category:** manuscript-issue (style warning)
- **Detail:** `scripts/verify_manuscript.py` warns on "perfect" in both files. `04_experimental_setup.md` uses `"almost perfect"` in the Cohen's κ context (acceptable citation of Landis 1977 scale); `05_results.md` uses `"perfect detection"` referring to sybil scenario (100% detection rate).
- **Fix:** `04_experimental_setup.md:49` is fine — "almost perfect" is a direct citation. `05_results.md:126` should be rephrased to `"100\% detection rate"` rather than "perfect detection" to avoid the style flag.

### L-03: F401 unused imports in 7 test files
- **Files:** `tests/test_utils_types.py:20` (`dataclass`), `tests/test_utils_types.py:22` (`pytest`), and 5 others (see ruff F401 output)
- **Category:** code-quality, lint
- **Fix:** Auto-fix: `ruff check --select F401 --fix tests/`.

### L-04: `src/visualization/composer_data.py:417` — `# type: ignore[import]` on category_theory_advanced import
- **File:** `src/visualization/composer_data.py:417`
- **Category:** code-quality
- **Detail:** Late import with type ignore. This works but is not ideal for static analysis.
- **Fix:** Move import to module top with proper try/except guard.

### L-05: `src/analysis/information_geometry.py:124` — `# noqa: ARG002` comment
- **File:** `src/analysis/information_geometry.py:124`
- **Category:** code-quality
- **Detail:** `ARG002` is not in the active ruff ruleset (only E/F/I/W selected). The noqa comment is unnecessary.
- **Fix:** Remove the `# noqa: ARG002` annotation or add `ARG` to ruff's `select` list if the rule is intended.

### L-06: PAI.md import example uses wrong path prefix
- **File:** `PAI.md:16-18`
- **Category:** doc-drift
- **Detail:** Example shows `from projects.cogsec_multiagent_2_computational.src import ...` — this is not how the package is installed. The actual import paths are `from core.trust import TrustCalculus` etc. (per `src/AGENTS.md`).
- **Fix:** Update PAI.md example to match actual import convention.

### L-07: `src/visualization/figures/attack_surface.py:295` — float assigned to int variable
- **File:** `src/visualization/figures/attack_surface.py:295`
- **Category:** mypy-error
- **Fix:** Explicitly cast: `my_var = int(my_float_expression)`.

### L-08: `src/utils/logging_setup.py:41` — StreamHandler arg incompatibility
- **File:** `src/utils/logging_setup.py:41`
- **Category:** mypy-error (minor)
- **Fix:** Cast the handler argument: `logging.StreamHandler(cast(Optional[IO[str]], stream))`.

### L-09: `src/formal/category_theory_advanced.py:1240` — int assigned to DetectionBound
- **File:** `src/formal/category_theory_advanced.py:1240`
- **Category:** mypy-error
- **Fix:** Wrap in `DetectionBound(...)` constructor call.

---

## VERIFICATION CHECKS PASSED (no action needed)

- ✅ All 2128 tests pass (0 failures)
- ✅ `test_latency_increases_with_agents` is **NOT flaky** — already uses `counts=[2, 50, 200]` and `n_timing_runs=20` (fix was already applied)
- ✅ `scripts/verify_manuscript.py` — all checks PASS (Files, Citations, Labels/Refs, Images/Links, Style, Table Format, Duplicate Labels, Fig Accessibility)
- ✅ No `??` unresolved reference markers in any manuscript section
- ✅ `scripts/generate_all_figures.py` — all 8 figures generate OK
- ✅ `scripts/generate_all_data.py` — runs successfully
- ✅ `scripts/run_colony_benchmarks.py` — all 5 scenarios complete
- ✅ `scripts/run_statistical_analysis.py` — runs successfully
- ✅ `scripts/run_sensitivity_analysis.py` — runs successfully
- ✅ TLA+/Promela/NuSMV spec generators are syntactically well-formed Python; generated specs are structurally valid
- ✅ 500-agent colony infrastructure is present (`test_colony_stress.py` has `xlarge_colony_config` fixture)
- ✅ No TODO/FIXME/NotImplementedError/pass-only stub functions in `src/`
- ✅ `src/evaluation/llm_evaluator.py` — correctly requires Ollama at runtime; HTTP error path tested with pytest-httpserver
- ✅ `docs/claims_traceability.md` — entries are consistent with actual source files and class names
- ✅ `docs/framework_validation.md` — reproduction commands are accurate
- ✅ `tests/test_manuscript_claims.py` exists and exercises claim-to-code mappings
- ✅ No mock framework usage (`MagicMock`, `mocker.patch`, `unittest.mock`) anywhere
- ✅ All `scripts/*.py` run without import errors (E402 violations are cosmetic only)

---

## PRIORITIZED TODO LIST

### Sprint 1 (Unblocks CI/coverage gate — do first)
1. **[C-01+C-02]** Fix `src/__main__.py`: change `ExperimentRunner(seed=args.seed)` to `ExperimentRunner(config=ExperimentConfig(seed=args.seed))` and replace `.run()` with `.run_full_matrix(adapters, corpus, pipeline)` or add a `.run()` convenience wrapper.
2. **[H-02]** Add `tests/test_composable_engine.py` — cover `DefenseGraph`, `CategoryDiagram`, `LatticeViz`, `OperadPlot`, `MonadFlow`, `LensDiagram` with ASCII-only tests (no graphviz needed). Target: bring composable.py from 20.61% to >90%.
3. **[H-03]** Add httpserver-based test for `run_llm_evaluation` happy path. Use `pytest_httpserver` to serve fake Ollama `/api/tags` + `/api/generate` responses. Target: bring llm_evaluator.py from 25% to >90%.
4. **[M-02]** Run `ruff check --select I --fix src/ tests/ scripts/` (auto-fix 15 I001). Then `ruff check --select F401 --fix tests/` (auto-fix 13 F401). Add `# noqa: E402` to scripts' path-manipulation lines.

### Sprint 2 (Type safety)
5. **[H-05]** Fix `consensus.py` submit_vote type overrides — add Union typing or `@override` annotations.
6. **[H-06 + M-01]** Fix `save_figure()` signature to accept `str | Path`. Fix `ax: Axes = cast(Axes, ...)` pattern across visualization/figures/ to resolve mypy union-attr errors.
7. **[M-19]** Fix `roc.py:116` numpy.trapz fallback to avoid mypy attr error.
8. **[M-17]** Add `-> None` to all `__init__` methods missing return type; add return types to private helpers in `visualization/tables/` and `visualization/figures/`.

### Sprint 3 (Coverage gaps)
9. **[M-05, M-06]** Add tests for `formal/free_energy.py` edge cases and categorical spec generators.
10. **[M-07]** Add edge-case tests to `test_manuscript.py` for verifier error paths.
11. **[M-08]** Extend `test_colony.py` for zero-adversary and maximum-adversary edge cases.
12. **[M-03]** Add `ScalabilityBenchmark` exception-path tests.
13. **[M-04]** Add tests for `KanExtension`, `LensOptic`, `FAlgebra` in category_theory_advanced.

### Sprint 4 (Architecture completeness and doc sync)
14. **[H-04]** Implement `src/architectures/metagpt.py` and `src/architectures/camel.py`, or remove all references. Add tests to `test_architectures.py`.
15. **[M-13]** Refactor `colony/recruitment_poisoning.py` to use top-level imports from `benchmark.py` (extract shared types to `_types.py` if needed).
16. **[M-14]** Fix REPRODUCE.md: `uv sync --extra dev` → `uv sync`.
17. **[L-01]** Update SKILL.md description test count to "2100+".
18. **[L-02]** Fix "perfect detection" in `manuscript/05_results.md:126`.
19. **[L-06]** Fix PAI.md import example paths.
20. **[M-20]** Document NuSMV/SPIN/TLA+ installation in REPRODUCE.md; add skip-with-reason markers to spec tests.
