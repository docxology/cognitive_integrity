# Cognitive Security Scripts — Paper 2 (Computational Validation)

Thin orchestrator scripts for the Cognitive Integrity Framework (CIF) Paper 2 series: **Computational Validation**. These scripts drive data generation, figure/table production, statistical analysis, ablation, sensitivity sweeps, colony benchmarks, LLM-backed evaluation, and manuscript verification.

All scripts follow the **thin-orchestrator contract** — computation lives in `src/`; scripts only import, orchestrate, and report. See [AGENTS.md](AGENTS.md) for the contract and per-script detail.

## Series Position

This is Part 2 of the three-part *Cognitive Security for Multiagent Operators* series. See the [project README](../README.md) for the full series map. The scripts here produce the data and figures cited by:

- **Part 1** \cite{friedman2026cogsec1} — formal-foundations companion (DOI: 10.5281/zenodo.22134544)
- **Part 3+4** \cite{friedman2026cogsec3} — practitioner's companion + unified applications (DOI: 10.5281/zenodo.22134548)

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

# Re-derive every registered numeric claim from output/data/ (CI gate)
uv run python scripts/verify_claims.py

# Run adversarial training evaluation
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42

# Run red-team attack generation + mutation-operator sweep
uv run python scripts/run_redteam.py --seed 42
```

## Script Inventory (37 scripts)

### Orchestrators (3)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `generate_all_data.py` | Runs all data-generation pipelines | `src/data/generate.py`, `src/utils/` | `uv run python scripts/generate_all_data.py` |
| `generate_all_figures.py` | Produces all manuscript figures | `src/visualization/figures.py` | `uv run python scripts/generate_all_figures.py` |
| `generate_all_tables.py` | Produces all manuscript tables | `src/visualization/tables/*` | `uv run python scripts/generate_all_tables.py` |

### Corpus measurement (11) — write one artifact to `output/data/`, support `--check`

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `run_taxonomy_evaluation.py` | Full attack taxonomy × all 256 defense-subset configurations (18-config `--axes` mode) | `src/attacks/corpus.py`, `src/composition/factory.py`, `src/evaluation/benign_corpus.py`, `src/ablation/runner.py` | `uv run python scripts/run_taxonomy_evaluation.py` |
| `run_detector_auc.py` | AUC with bootstrap intervals for the drift detector and the fused ensemble | `src/evaluation/roc.py`, `src/composition/fusion.py`, `src/attacks/corpus.py` | `uv run python scripts/run_detector_auc.py` |
| `run_baseline_comparison.py` | Full CIF pipeline vs baseline detectors vs a chance null (out-of-fold) | `src/evaluation/baselines.py` | `uv run python scripts/run_baseline_comparison.py` |
| `run_defense_overlap.py` | Per-module total/unique/shared detection rates plus the union row | `src/composition/algebra.py`, `src/composition/factory.py` | `uv run python scripts/run_defense_overlap.py` |
| `run_module_capability_matrix.py` | Per-module capability vs marginal contribution (masking vs incapacity) | `src/composition/factory.py`, `src/attacks/corpus.py` | `uv run python scripts/run_module_capability_matrix.py` |
| `run_stratified_detection.py` | Detection stratified by adversary class and attack target | `src/attacks/corpus.py`, `src/composition/factory.py` | `uv run python scripts/run_stratified_detection.py` |
| `run_threshold_sweep.py` | Firewall τ quarantine/reject threshold sweeps (operating curve) | `src/evaluation/threshold_sweep.py`, `src/core/firewall.py` | `uv run python scripts/run_threshold_sweep.py` |
| `run_load_sweep.py` | Controlled arrival-rate sweep; finds pipeline saturation point | `src/evaluation/load_driver.py`, `src/composition/factory.py` | `uv run python scripts/run_load_sweep.py` |
| `run_overhead_control.py` | Defended-vs-undefended control arm: latency and memory cost of the pipeline | `src/composition/factory.py` | `uv run python scripts/run_overhead_control.py` |
| `run_fp_mitigation.py` | False-positive root-cause attribution and per-mitigation cost/benefit | `src/composition/mitigations.py`, `src/evaluation/benign_corpus.py` | `uv run python scripts/run_fp_mitigation.py` |
| `run_combination_rule_study.py` | Combination-rule study: standardized-score fusion vs the shipped max rule (b1/b2/b3 split protocol) | `src/attacks/corpus.py`, `src/composition/factory.py`, `src/evaluation/benign_corpus.py` | `uv run python scripts/run_combination_rule_study.py` |

### Evaluation & statistics (7)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `run_full_evaluation.py` | Full evaluation matrix across simulation/pipeline/LLM modes | `src/evaluation/runner.py`, `src/attacks/corpus.py`, `src/architectures/` | `uv run python scripts/run_full_evaluation.py` |
| `run_statistical_analysis.py` | Hypothesis tests (H1/H2/H3), effect sizes, assumption checks | `src/statistics/analysis_runner.py` | `uv run python scripts/run_statistical_analysis.py` |
| `run_ablation.py` | Component removal, minimal configs, pairwise synergy | `src/ablation/runner.py` | `uv run python scripts/run_ablation.py --seed 42` |
| `run_cross_validation.py` | Stratified 5-fold cross-validation on the attack corpus | `src/statistics/cross_validation.py`, `src/ablation/runner.py` | `uv run python scripts/run_cross_validation.py` |
| `run_multi_seed.py` | Multi-seed stability analysis (CV across 30 seeds) | `src/statistics/stability.py` | `uv run python scripts/run_multi_seed.py` |
| `run_sensitivity_analysis.py` | Parameter sweeps, sensitivity ranking, 2D grid search | `src/statistics/sensitivity.py` | `uv run python scripts/run_sensitivity_analysis.py` |
| `run_scalability.py` | Colony broadcast rounds at *n* agents; latency/memory scaling with regression inference | `src/evaluation/scalability.py`, `src/evaluation/benchmark.py`, `src/core/trust.py` | `uv run python scripts/run_scalability.py --repeats 15 --seed 42` |

### Colony & adversarial / LLM (5)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `run_colony_benchmarks.py` | Colony-level CogSec benchmark scoring (scenarios at 20–100 agents) | `src/colony/benchmark.py` | `uv run python scripts/run_colony_benchmarks.py --seed 42` |
| `run_adversarial_training.py` | Iterative adversarial-training rounds; per-round DR deltas and Nash projection | `src/redteam/` (`AdversarialTrainer`, `NashEquilibriumEstimator`) | `uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42` |
| `run_redteam.py` | Ω-level attack generation plus mutation-operator sweep scored against the real `CognitiveFirewall` | `src/redteam/generator.py`, `src/redteam/evasion.py`, `src/core/firewall.py` | `uv run python scripts/run_redteam.py --seed 42` |
| `run_llm_demo.py` | Live Ollama-backed multiagent CIF evaluation (opt-in) | `src/agents/`, `src/evaluation/llm_evaluator.py` | `COGSEC_RUN_LLM_ANALYSIS=1 uv run python scripts/run_llm_demo.py` |
| `run_publication_suite.py` | Drives `run_full_evaluation.py` per `experiment_config.toml`; LLM branch opt-in | subprocess over `run_full_evaluation.py` | `uv run python scripts/run_publication_suite.py` |

### Verification & formal (3)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `run_formal_validation.py` | Validates Paper 1 theorems via model checkers (NuSMV, SPIN, TLA+) | `src/formal/theorem_registry.py` | `uv run python scripts/run_formal_validation.py` |
| `verify_formal_specs.py` | Generates and verifies the formal specification files | `src/formal/spec_verifier.py` | `uv run python scripts/verify_formal_specs.py` |
| `verify_manuscript.py` | Checks citations, labels, `\cref` targets, figure references, style | `src/manuscript/verifier.py` | `uv run python scripts/verify_manuscript.py` |

### Claims registry (2)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `verify_claims.py` | Re-derives every registered numeric claim from `output/data/` and compares to the prose (CI gate; exit 1 on MISMATCH/NOT_FOUND/UNBACKED) | `src/manuscript/claim_registry.py` | `uv run python scripts/verify_claims.py` |
| `sync_claims.py` | Rewrites MISMATCH literals in place, formatting preserved; never writes NOT_FOUND/UNBACKED | `src/manuscript/claim_registry.py` | `uv run python scripts/sync_claims.py --dry-run` |

### Utilities (6)

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `convert_latex_tables.py` | Converts LaTeX tables in manuscript `.md` files to Markdown pipe tables (for readability diffs) | `src/manuscript/latex_converter.py` | `uv run python scripts/convert_latex_tables.py` |
| `z_inject_manuscript_values.py` | Auto-injects computed values from `output/data/` into the manuscript (leading `z_` so it runs last) | `src/manuscript/injector.py` | `uv run python scripts/z_inject_manuscript_values.py` |
| `generate_figure_registry.py` | Scans `docs/manuscript/*.md` for `{#fig:...}`/`{#tab:...}` labels; writes auto-numbered registry | self-contained | `uv run python scripts/generate_figure_registry.py` |
| `auto_number_figures.py` | Reads `figure_registry.json`; injects `\label{}`/`\listoffigures` commands | self-contained | `uv run python scripts/auto_number_figures.py` |
| `fix_table_labels.py` | Converts bold-paragraph table captions to pandoc-crossref table captions | self-contained | `uv run python scripts/fix_table_labels.py --dry-run` |
| `generate_composer_data.py` | Generates the CIF Composer web-UI data file | `src/visualization/composer_data.py` | `uv run python scripts/generate_composer_data.py` |

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

## Thin Orchestrator Contract

```python
#!/usr/bin/env python3
"""Example thin orchestrator (do this, not raw computation)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from evaluation.runner import ExperimentRunner   # computation from src/

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

**Required** — all computation via `src/` imports; scripts handle only I/O, reporting, logging, and manifest bookkeeping; print output paths to stdout for pipeline manifest collection; deterministic RNG (seed=42). The bootstrap is `sys.path.insert(0, str(ROOT / "src"))` followed by top-level imports (`from evaluation.runner import ...`), matching every script in this directory.

**Forbidden** — business logic in scripts; algorithm implementation in scripts; direct numerical computation outside `src/`; use of mocks (see `src/AGENTS.md` for the no-mocks policy).

**stdout** — artifact paths for manifest collection, plus short human-readable result summaries from the `run_*` scripts; diagnostics go through `logging`.

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

Scripts here produce the empirical results that Papers 1/3+4 reference. If you touch a script that changes headline numbers (e.g., ablation deltas, parametric ceiling, colony detection rates), check that sibling papers' cross-references remain accurate:

- Part 1 §8 Discussion — cites Part 2 ablations (§5.6)
- Part 3+4 §3 Evidence — cites Part 2 overall metrics (96–100% parametric ceiling)
- Part 3+4 §9 Methodology — cites Part 2 as validation anchor

A mismatch between a sibling's quoted number and the current `output/data/` value is a **regression**. Run `verify_manuscript.py` and `verify_claims.py` after non-trivial changes.
