# Reproducibility Guide

## System Requirements

- Python 3.11+; CI targets the 3.11 floor and the exact primary runtime 3.15.2.
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
# Clone repository
git clone https://github.com/docxology/cognitive_integrity.git
cd cognitive_integrity/cogsec_multiagent_2_computational

# Install dependencies
uv sync
```

`uv sync` creates `.venv` but does **not** put it on `PATH`. Every `make`
target therefore routes through `uv run`; bare `python` / `pytest` / `ruff`
are not resolvable from a clean shell. Override the interpreter if you already
have one activated, e.g. `make tests PYTEST=.venv/bin/pytest`.

## Full Pipeline

```bash
make all
```

This runs, in order:

1. `check-real-data` — assert the git-tracked publication evidence in
   `output/data/` is present and is not synthetic placeholder data
2. `verify` — manuscript integrity
3. `tests` — the full test suite
4. `figures` — the manuscript figures, from the data already in `output/data/`
5. `tables` — the LaTeX tables, from the same data

`make all` **does not generate data.** It reads the tracked results committed
to the repository. If they are missing it stops with an error naming the
missing files rather than silently substituting placeholders. The protected set
includes both measured pipeline artifacts and the explicitly labelled
`full_evaluation_results.json` parametric simulation; overwrite protection does
not make that simulation a measurement.

> **`make data` has been removed.** It used to run
> `scripts/generate_all_data.py` with its default output directory, which
> overwrote the tracked real-pipeline evidence in `output/data/` with synthetic
> placeholders — and `all` depended on it, so the headline reproduction command
> rebuilt every figure and table on top of fabricated numbers. Invoking
> `make data` now exits non-zero with a pointer to the honest alternatives:
> `make synthetic-data` for placeholders (written elsewhere), and the real
> experiment scripts for measured results.

## Individual Targets

| Command | Description |
|---------|-------------|
| `make all` | check-real-data → verify → tests → figures → tables |
| `make check-real-data` | Assert `output/data/` holds tracked publication evidence, not placeholders |
| `make synthetic-data` | Write **synthetic** placeholder data to `output/data_synthetic/` |
| `make figures` | Generate the manuscript figures into `output/figures/` |
| `make tables` | Generate LaTeX tables into `output/tables/` |
| `make verify` | Verify manuscript integrity |
| `make tests` | Run the full test suite |
| `make evaluate` | Run the evaluation matrix and print TPR/FPR (writes nothing) |
| `make lint` | `ruff check src/ scripts/ tests/` |
| `make format-check` | `ruff format --check` — advisory; the tree is not format-clean yet |
| `make clean` | Remove **untracked** regenerable artifacts (see below) |

Useful overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PYTHON` | `uv run python` | Interpreter for every script target |
| `PYTEST` | `uv run pytest` | Test runner |
| `RUFF` | `uv run ruff` | Linter |
| `REAL_DATA_DIR` | `output/data` | Directory `check-real-data` inspects |
| `SYNTHETIC_DATA_DIR` | `output/data_synthetic` | Where `synthetic-data` writes |
| `DRY_RUN` | *(unset)* | With `make clean`: list what would be removed, delete nothing |

### `make clean` is tracked-file safe

`output/` holds git-tracked publication artifacts alongside regenerable ones.
`clean` asks git which is which and removes only the
untracked files; it never deletes a tracked artifact, and it leaves
`manuscript_verification.log` in place while that file is tracked. Preview
with:

```bash
make clean DRY_RUN=1
```

## Synthetic vs. Real Data

`make synthetic-data` produces schema-compliant **placeholder** data. It is
fast and useful for exercising the rendering code, but its distributions differ
from the measured ones and must not be interpreted as empirical results. It
writes to `output/data_synthetic/` precisely so it cannot overwrite the tracked
evidence.

Measured values currently committed under `output/data/`, versus what
`make synthetic-data` produces for the same schema:

| Quantity | Source file | Real (`data_origin: real_pipeline`) | Synthetic (`data_origin: synthetic_schema`) |
|----------|-------------|-------------------------------------|---------------------------------------------|
| Mean overall detection, 30 seeds | `multi_seed_results.json` | **0.863** (min 0.82, max 0.90; CV 0.0243, `stable: false`) | 0.9676 (CV 0.0065) |
| 5-fold cross-validated TPR | `cross_validation_results.json` | **0.160** (std 0.0237; mean F1 0.275) | 0.9641 (std 0.0055; mean F1 0.9612) |

For the multi-seed row, each of the 30 seeds evaluates 100 stratified attacks
and 120 benign messages using one architecture-agnostic CIF pipeline. The mean
benign-arm FPR is **0.1853** (18.53%); the overall TPR population SD is 0.021.
The `stable: false` verdict comes from per-category CVs, not the overall CV.

To regenerate tracked results, run their source scripts directly. The
full-evaluation command regenerates a parametric simulation, not measured
pipeline evidence. Each command writes into `output/data/`, replacing tracked
evidence — do this deliberately, never as part of a routine build:

| Data file | Real source | Notes |
|-----------|-------------|-------|
| `output/data/ablation_results.json` | `uv run python scripts/run_ablation.py` | Ablation deltas validated against live `evaluate_component_subset()` |
| `output/data/full_evaluation_results.json` | `uv run python scripts/run_full_evaluation.py` | Parametric simulation (no external service needed) |
| `output/data/multi_seed_results.json` | `uv run python scripts/run_multi_seed.py` | 30-seed stability sweep |
| `output/data/cross_validation_results.json` | `uv run python scripts/run_cross_validation.py` | 5-fold stratified CV over the attack corpus |
| `output/data/colony_results.json` | `uv run python scripts/run_colony_benchmarks.py --n-repeats 30` | `ColonyBenchmark.run_all_repeated(seed=42, n_repeats=30)` |
| `output/data/llm_demo_results.json` | `uv run python scripts/run_llm_demo.py` | Requires Ollama + `gemma3:4b` |

The injector (`src/manuscript/injector.py`) reads these files when present.
`make check-real-data` fails if any of the five core files is missing, if any
of them declares a `data_origin` other than `real_pipeline`, or if none of
them declares provenance at all (which would make the check vacuous).

## Expected Outputs

- `output/figures/` — PDF + PNG figure pairs
- `output/tables/` — LaTeX table files
- `output/data/` — tracked evaluation data (JSON), with per-artifact provenance

## Runtime Notes

- Figure generation uses a headless matplotlib backend (`Agg`) and pins
  `SOURCE_DATE_EPOCH`, so PDFs are byte-reproducible across runs
- Tests use deterministic seeds and carry a 120 s per-test timeout
  (`pytest-timeout`, configured in `pyproject.toml`)
- Nothing in the pipeline requires a GPU
- LLM validation targets (`llm_demo_results.json`) require Ollama with
  `gemma3:4b` (`ollama pull gemma3:4b`)

## Packaging Note

The distribution publishes a single top-level package, `src`. It previously
published multiple generic top-level names (`core`, `data`, `utils`, `evaluation`,
`statistics`, …); `statistics` in particular shadowed the standard-library
module for anything that put `src/` on `sys.path`. In-repo consumers are
unaffected: the test suite resolves modules through pytest's
`pythonpath = ["src"]` and the scripts insert `src/` on `sys.path` themselves,
never through the installed distribution. `import src` still runs the
`sys.path` shim in `src/__init__.py`, so `from core.trust import ...` keeps
working after it.

## Verification Log

The commands in this document were executed on 2026-07-27 against this
checkout (Python 3.12, macOS, `uv` 0.11.32):

| Command | Exit | Note |
|---------|------|------|
| `uv sync` | 0 | |
| `make all` | 2 | Stops at `tests`; see below |
| `make check-real-data` | 0 | `5 files present, 2 declare data_origin=real_pipeline` |
| `make verify` | 0 | All manuscript checks pass |
| `make tests` | 1 | 2641 passed, 2 skipped, **2 pre-existing failures** |
| `make figures` | 0 | 8/8 generated |
| `make tables` | 0 | 10/10 generated |
| `make synthetic-data` | 0 | Wrote `output/data_synthetic/`; `output/data/` byte-identical afterwards |
| `make evaluate` | 0 | `TPR=0.995, FPR=0.000` |
| `make lint` | 1 | 1 pre-existing `I001` in `src/formal/category_theory_advanced.py` |
| `make format-check` | 1 | Advisory; 189 files would be reformatted |
| `make clean DRY_RUN=1` | 0 | 347 untracked removable, 43 tracked kept |

The two failing tests
(`tests/test_corner_cases.py::TestAnomalyScorerCornerCases::test_missing_keys_in_state`
and `tests/test_manuscript_claims.py::test_top_synergy_pair_is_tripwire_detection`)
are pre-existing and unrelated to the build system; `make all` stopping there is
the intended behaviour of a gate that no longer proceeds past a red suite.
`make clean` itself was exercised only in `DRY_RUN` mode, with the removal list
verified to have an empty intersection with `git ls-files -- output`.
