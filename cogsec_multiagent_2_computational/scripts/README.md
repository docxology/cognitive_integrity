# Cognitive Security Scripts

Figure generation, data analysis, and verification scripts for CIF Paper 2.

## Quick Start

```bash
# Generate all experimental data
python3 scripts/generate_all_data.py

# Generate all 8 manuscript figures
python3 scripts/generate_all_figures.py

# Generate all manuscript tables
python3 scripts/generate_all_tables.py

# Run statistical analysis
python3 scripts/run_statistical_analysis.py

# Verify manuscript integrity
python3 scripts/verify_manuscript.py
```

## Manuscript Figures (8)

| Script | Figure |
| ------ | ------ |
| `01_attack_surface_figure.py` | attack_surface.pdf |
| `02_detection_performance_figure.py` | detection_performance.pdf |
| `03_roc_analysis_figure.py` | roc_curves.pdf |
| `04_trust_dynamics_figure.py` | trust_dynamics.pdf |
| `05_defense_composition_figure.py` | defense_composition.pdf |
| `06_architecture_comparison_figure.py` | architecture_comparison.pdf |
| `07_scalability_figure.py` | scalability.pdf |
| `08_ablation_figure.py` | ablation.pdf |

## Analysis Scripts (8)

| Script | Purpose |
| ------ | ------- |
| `run_full_evaluation.py` | Full evaluation matrix (simulation/pipeline/LLM) |
| `run_statistical_analysis.py` | Hypothesis tests (H1/H2/H3) and effect sizes |
| `run_ablation.py` | Component removal and synergy analysis |
| `run_sensitivity_analysis.py` | Parameter sweeps and sensitivity ranking |
| `run_cross_validation.py` | Stratified k-fold cross-validation |
| `run_multi_seed.py` | Multi-seed stability analysis (CV) |
| `run_colony_benchmarks.py` | Colony-level CogSec scoring |
| `run_llm_demo.py` | Live LLM multiagent CIF demonstration |

## Verification & Formal (3)

| Script | Purpose |
| ------ | ------- |
| `run_formal_validation.py` | Validates Paper 1 theorems via model checkers |
| `verify_formal_specs.py` | Generates and verifies NuSMV/SPIN/TLA+ specs |
| `verify_manuscript.py` | Checks citations, refs, images, style |

## Utilities (1)

| Script | Purpose |
| ------ | ------- |
| `convert_latex_tables.py` | Converts LaTeX tables in manuscript to Markdown |

## Orchestrators (3)

| Script | Purpose |
| ------ | ------- |
| `generate_all_data.py` | Run all data generation |
| `generate_all_figures.py` | Run all 8 figure scripts |
| `generate_all_tables.py` | Run all table generation |

## Output Locations

- Figures: `output/figures/`
- Data: `output/data/`
- Formal specs: `output/formal/`

All scripts follow thin orchestrator pattern — import from `src/`, handle visualization only.
