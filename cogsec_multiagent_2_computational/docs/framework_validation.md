# Framework Validation & Reproducibility

This document details how the Cognitive Integrity Framework (CIF) was empirically validated, including the target architectures, experimental parameters, and reproducibility instructions. It serves as a guide for reproducing the results presented in Part 2 of the manuscript.

## Target Architectures

The framework was tested against four distinct multiagent architectural patterns to ensure generalizability. Adapters for these architectures are located in `src/architectures/`.

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

The evaluation used a comprehensive corpus of 950 cognitive attacks, generated to cover the theoretical threat model. Categories include:

- **Prompt Injection**: Direct LLM input manipulation.
- **Trust Exploitation**: Social engineering of agent trust scores.
- **Belief Manipulation**: Planting false axioms or data.
- **Coordination Subversion**: Disrupting consensus/voting.

Corpus generation logic: `src/attacks/corpus.py` (`AttackCorpus` class)

## Reproducing the Experiments

All experiments are deterministic (seed=42). Run from the project root directory.

### 1. Full Pipeline (Recommended)

The package provides a `Makefile`; `make all` executes the complete pipeline
(generating all data, figures, and tables under `output/`):

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

Tests the entire attack corpus across all architectures:

```bash
python scripts/run_full_evaluation.py
```

**Output**: `output/data/full_evaluation_results.json`

### 3. Run Ablation Studies

Tests the contribution of individual components (Firewall, Trust, Sandbox, etc.) by removing them one at a time:

```bash
python scripts/run_ablation.py
```

**Output**: `output/data/ablation_results.json`

### 4. Run Multi-Seed Stability Analysis

Measures detection rate stability across 30 random seeds, computing coefficient of variation (CV) for overall, per-architecture, and per-category metrics:

```bash
python scripts/run_multi_seed.py
```

**Output**: `output/data/multi_seed_results.json`

### 5. Run Cross-Validation

K-fold cross-validation of detection rates for statistical rigor:

```bash
python scripts/run_cross_validation.py
```

**Output**: `output/data/cross_validation_results.json`

### 6. Run Colony Benchmarks

Scalability tests measuring framework performance across increasing agent counts:

```bash
python scripts/run_colony_benchmarks.py
```

**Output**: `output/data/colony_results.json`

### 7. Generate Figures

Once data is generated, produce the plots used in the manuscript:

```bash
python scripts/generate_all_figures.py
```

**Output**: `output/figures/*.pdf`

## Validation Results Check

After generating results, compare key metrics (overall detection rate, per-architecture TPR, per-category breakdown) against the values reported in the manuscript Tables 1–3 to confirm reproducibility.

## Requirements

- Python 3.12+
- `numpy`, `scipy`, `matplotlib` (see `pyproject.toml`)
