# Cognitive Security Scripts — Paper 2 (Computational Validation)

Thin orchestrator scripts for the Cognitive Integrity Framework (CIF) Paper 2 series: **Computational Validation**. These scripts drive data generation, figure/table production, statistical analysis, ablation, sensitivity sweeps, colony benchmarks, LLM-backed evaluation, and manuscript verification.

All scripts follow the **thin-orchestrator contract** — computation lives in `src/`; scripts only import, orchestrate, and render.

## Series Position

This is Part 2 of the three-part *Cognitive Security for Multiagent Operators* series. See the [project README](../README.md) for the full series map. The scripts here produce the data and figures cited by:

- **Part 1** \cite{friedman2026cogsec1} — formal-foundations companion (DOI: 10.5281/zenodo.22134544)
- **Part 3** \cite{friedman2026cogsec3} — practitioner's companion (DOI: 10.5281/zenodo.22134548)
- **Part 3+4** \cite{friedman2026cogsec3} — unified applications companion

## Quick Start

```bash
# Generate all experimental data (populates output/data/)
uv run python scripts/generate_all_data.py

# Generate all figures (populates output/figures/)
uv run python scripts/generate_all_figures.py

# Generate all tables (populates output/tables/)
uv run python scripts/generate_all_tables.py

# Run publication suite with bounded default behavior
uv run python scripts/run_publication_suite.py

# Opt into live Ollama-backed LLM evaluation
COGSEC_RUN_LLM_ANALYSIS=1 uv run python scripts/run_publication_suite.py

# Run statistical analysis (H1/H2/H3)
uv run python scripts/run_statistical_analysis.py

# Verify manuscript integrity (citations, labels, figures)
uv run python scripts/verify_manuscript.py

# NEW v2.0: Run adversarial training evaluation
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42

# NEW v2.0: Run red-team attack generation + mutation-operator sweep
uv run python scripts/run_redteam.py --seed 42
```

## Script Inventory (22 scripts)

### Orchestrators (3)

| Script | Purpose | Output |
| ------ | ------- | ------ |
| `generate_all_data.py` | Runs all data-generation pipelines; delegates to `src.data` and `src.evaluation` | `output/data/*.{json,csv,parquet}` |
| `generate_all_figures.py` | Produces all manuscript figures via `src.visualization.figures` | `output/figures/*.pdf` |
| `generate_all_tables.py` | Produces all manuscript tables via `src.visualization.tables` | `output/tables/*.{tex,md}` |

### Analysis Scripts (11)

| Script | Purpose | Manuscript Anchor |
| ------ | ------- | ----------------- |
| `run_full_evaluation.py` | Full evaluation matrix across simulation/pipeline/LLM modes | §5 Results |
| `run_statistical_analysis.py` | Hypothesis tests (H1/H2/H3), effect sizes, assumption checks | §5b Statistical Significance |
| `run_ablation.py` | Component removal + minimal config + pairwise synergy | §5.6, §5d Ablation and Scalability |
| `run_sensitivity_analysis.py` | Parameter sweeps, sensitivity ranking, 2D grid search | §5c Sensitivity Analysis |
| `run_cross_validation.py` | Stratified 5-fold cross-validation on the 950-attack corpus | §5 Results |
| `run_multi_seed.py` | Multi-seed stability analysis (CV across 30 seeds) | §5b, §5e Bayesian Uncertainty |
| `run_colony_benchmarks.py` | Colony-level CogSec benchmark scoring (5 scenarios at 20–100 agents) | §5, §S03 Benchmark Implementation |
| `run_llm_demo.py` | Live LLM-backed multiagent CIF evaluation via Ollama (opt-in with `COGSEC_RUN_LLM_ANALYSIS=1`) | §5 Results |
| `run_publication_suite.py` | Runs publication simulations by default; live LLM branch is opt-in with `COGSEC_RUN_LLM_ANALYSIS=1` or `--run-llm` | — |
| `run_adversarial_training.py` | Iterative adversarial-training rounds via `src.redteam.AdversarialTrainer`; per-round detection-rate deltas and projected Nash-equilibrium DR | §05g Adversarial Training |
| `run_redteam.py` | Ω-level attack generation (`src.redteam.generator.AdversarialGenerator`) plus a mutation-operator sweep scored against the real `CognitiveFirewall` | §05h Red-Team Evaluation |

### Verification & Formal (3)

| Script | Purpose | Manuscript Anchor |
| ------ | ------- | ----------------- |
| `run_formal_validation.py` | Validates Paper 1 theorems via model checkers (NuSMV, SPIN, TLA+) | §S04 Model Checking |
| `verify_formal_specs.py` | Generates and verifies the formal specification files | §S04 |
| `verify_manuscript.py` | Checks citations, labels, `\cref` targets, figure references, style | project-wide |

### Utilities (5)

| Script | Purpose |
| ------ | ------- |
| `convert_latex_tables.py` | Converts LaTeX tables in manuscript `.md` files to Markdown pipe tables (for readability diffs) |
| `z_inject_manuscript_values.py` | Auto-injects computed values from `output/data/` back into manuscript `.md` files (leading `z_` so it runs last) |
| `generate_figure_registry.py` | Scans `manuscript/*.md` for `{#fig:...}`/`{#tab:...}` labels and writes an auto-numbered `output/data/figure_registry.json` |
| `auto_number_figures.py` | Reads `figure_registry.json` and injects `\label{}`/`\listoffigures` commands into manuscript `.md` files |
| `generate_composer_data.py` | Generates the CIF Composer backend data file (`output/data/composer_data.json`) for the web UI, aggregating category-theory verifications and module registry |

## Output Layout

```text
output/
├── data/          # Raw experimental results (JSON/CSV/Parquet)
├── figures/       # Publication PDFs (attack_surface, detection_performance, roc_curves, …)
├── tables/        # LaTeX + Markdown tables
├── formal/        # NuSMV/SPIN/TLA+ spec files + verification logs
├── pdf/           # Final rendered manuscript PDFs
└── reports/       # Validation reports
```

## Manuscript Figures

Figures are produced by `generate_all_figures.py`, which delegates to figure factories in `src/visualization/figures.py`. The set is determined dynamically from `config.yaml` and the data manifest; the **current** set consulted by the manuscript includes: attack-surface breakdown, detection-performance bars, ROC curves per architecture, trust-decay dynamics, defense-composition Venn/stack, cross-architecture comparison, colony scalability, and ablation contribution. To regenerate a single figure, call its factory directly:

```python
from src.visualization.figures import build_figure_manifest, render_figure
manifest = build_figure_manifest(data_dir="output/data")
render_figure(manifest["detection_performance"], output_dir="output/figures")
```

## Thin Orchestrator Contract

```python
#!/usr/bin/env python3
"""Example thin orchestrator (do this, not raw computation)."""
from pathlib import Path
from src.evaluation.runner import ExperimentRunner   # import computation from src/

def main():
    output_dir = Path("output/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = ExperimentRunner(seed=42)   # deterministic
    result = runner.run_all()

    result.save(output_dir / "evaluation.json")
    print(output_dir / "evaluation.json")   # stdout path for manifest collection

if __name__ == "__main__":
    main()
```

**Required** — all computation via `src/` imports; scripts handle only I/O and visualization; print output paths to stdout for pipeline manifest collection; deterministic RNG (seed=42).

**Forbidden** — business logic in scripts; algorithm implementation in scripts; direct numerical computation outside `src/`; use of mocks (see [src/AGENTS.md](../src/AGENTS.md) for the no-mocks policy).

## Reproducibility

All scripts use `seed=42` by default (configurable via `--seed`). To reproduce the headline Paper 2 results end-to-end:

```bash
uv run python scripts/generate_all_data.py --seed 42
uv run python scripts/run_full_evaluation.py --seed 42
uv run python scripts/run_ablation.py --seed 42
uv run python scripts/run_sensitivity_analysis.py --seed 42
uv run python scripts/run_colony_benchmarks.py --seed 42
uv run python scripts/generate_all_figures.py
uv run python scripts/generate_all_tables.py
uv run python scripts/verify_manuscript.py
```

Expected runtime: ~30 min on a modern laptop (without LLM demo), ~2h with `run_llm_demo.py` (Ollama-dependent).

## Cross-Paper Note

Scripts here produce the empirical results that Papers 1/3/4 reference. If you touch a script that changes headline numbers (e.g., ablation deltas, parametric ceiling, colony detection rates), check that sibling papers' cross-references remain accurate:

- Part 1 §8 Discussion — cites Part 2 ablations (§5.6)
- Part 3+4 §3 Evidence — cites Part 2 overall metrics (96–100% parametric ceiling)
- Part 3+4 §9 Methodology — cites Part 2 as validation anchor

A mismatch between a sibling's quoted number and the current `output/data/` value is a **regression**. Run `verify_manuscript.py` after non-trivial changes.
