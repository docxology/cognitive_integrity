# Framework Validation & Reproducibility

This document details how the Cognitive Integrity Framework (CIF) was empirically validated, including the target architectures, experimental parameters, and reproducibility instructions. It serves as a guide for reproducing the results presented in Part 2 of the manuscript.

## Target Architectures

Adapters for four multiagent architectural patterns are located in
`src/architectures/`. The retained full-evaluation artifact uses these adapters
in a historical parametric simulation; that simulation is not a measured
architecture comparison. The multi-seed pipeline measurement is
architecture-agnostic and has no per-architecture results.

1. **Claude Code (Hierarchical)**: Orchestrator-Worker pattern modeled on Enterprise RAG systems.
    - *Implementation*: `src/architectures/claude_code.py`
2. **AutoGPT (Autonomous)**: Autonomous agent with plugin-based tool access.
    - *Implementation*: `src/architectures/autogpt.py`
3. **CrewAI (Role-Based)**: Role-based team with sequential task handoff.
    - *Implementation*: `src/architectures/crewai.py`
4. **LangGraph (State Machine)**: Graph-based state machine protocol.
    - *Implementation*: `src/architectures/langgraph.py`

All adapters inherit from the base adapter at `src/architectures/base.py`.

## Attack Corpus

The default integrated corpus contains 1,475 attacks across five primary
families and fifteen subcategories. The legacy `extended=False` corpus contains
950 attacks across four families and twelve subcategories; the retained
parametric architecture simulation uses that legacy corpus. The integrated
families are:

- **Prompt Injection**: Direct LLM input manipulation.
- **Trust Exploitation**: Social engineering of agent trust scores.
- **Belief Manipulation**: Planting false axioms or data.
- **Coordination Subversion**: Disrupting consensus/voting.
- **Provenance and Isolation**: Attacks on provenance boundaries and isolation guarantees.

Corpus generation logic: `src/attacks/corpus.py` (`AttackCorpus` class). Each
reported rate must identify which corpus or stratified subsample it used.

## Reproducing the Experiments

The experiment scripts are deterministic under their recorded seeds. Most commands here default to seed 42; the tracked multi-seed sweep instead records seeds 1–30. Run from the project root directory.

### 1. Full Pipeline (Recommended)

The package provides a `Makefile`; `make all` runs `check-real-data`, `verify`,
`tests`, `figures` and `tables` in that order. It does **not** generate data:
that is deliberate, so the build cannot silently replace measured artifacts
with fresh synthetic ones (see [`REPRODUCE.md`](../REPRODUCE.md)):

```bash
make all
```

> **Note:** There is no `bash run.sh` entry point in this part. For the full
> end-to-end reproduction recipe — including the synthetic-vs-real data caveat
> and per-experiment commands — see [`REPRODUCE.md`](../REPRODUCE.md), which is
> the single reproduction authority for Part 2. All commands below assume
> `uv run python ...` (the project is `uv`-managed; bare `python`/`pytest` are
> not on `PATH` after `uv sync`).

### 2. Run Full Evaluation

Runs the historical parametric simulation over the legacy 950-attack corpus for
four modeled architectures: 950 × 4 = 3,800 simulated attack instances. This
artifact has no benign arm, so it provides no measured FPR, precision, F1 or
field-performance bound.

```bash
uv run python scripts/run_full_evaluation.py
```

**Output**: `output/data/full_evaluation_results.json`

### 3. Run Ablation Studies

Tests the contribution of individual components (Firewall, Trust, Sandbox, etc.) by removing them one at a time:

```bash
uv run python scripts/run_ablation.py
```

**Output**: `output/data/ablation_results.json`

### 4. Run Multi-Seed Stability Analysis

Measures the architecture-agnostic pipeline across 30 seeds, with 100 stratified
attacks and 120 benign messages per seed. It computes overall and per-category
coefficients of variation (CV), not per-architecture measurements:

```bash
uv run python scripts/run_multi_seed.py
```

**Output**: `output/data/multi_seed_results.json`

### 5. Run Cross-Validation

K-fold cross-validation of detection rates for statistical rigor:

```bash
uv run python scripts/run_cross_validation.py
```

**Output**: `output/data/cross_validation_results.json`

### 6. Run Colony Benchmarks

Scalability tests measuring framework performance across increasing agent counts.
The tracked artifact used 30 seeds per scenario (default); `--n-repeats 1`
reproduces the legacy single-seed draw:

```bash
uv run python scripts/run_colony_benchmarks.py --n-repeats 30
```

**Output**: `output/data/colony_results.json`

### 7. Generate Figures

Once data is generated, produce the plots used in the manuscript:

```bash
uv run python scripts/generate_all_figures.py
```

**Output**: `output/figures/*.pdf`

## Validation Results Check

After generating results, compare registered metrics against the corresponding manuscript values and artifacts. For the multi-seed experiment these include overall TPR, benign-arm FPR and per-category breakdowns; its architecture-agnostic design has no per-architecture TPR. Keep the full-evaluation simulation's modeled architecture ceilings distinct from measured pipeline results.

## Requirements

- Python 3.11+; CI targets the 3.11 floor and the exact primary runtime 3.15.2.
- `numpy`, `scipy`, `matplotlib` (see `pyproject.toml`)
