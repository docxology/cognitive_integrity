# Cognitive Security Scripts — Agent Reference

Scripts for figure generation, data analysis, and manuscript verification for CIF Paper 2.

## Manuscript Figures (8 scripts)

| Script | Figure | Section |
|--------|--------|---------|
| `01_attack_surface_figure.py` | attack_surface.pdf | §3 Attack Corpus |
| `02_detection_performance_figure.py` | detection_performance.pdf | §4.1 Finding 1 |
| `03_roc_analysis_figure.py` | roc_curves.pdf | §4.2 Finding 2 |
| `04_trust_dynamics_figure.py` | trust_dynamics.pdf | §4.2 Trust Calculus |
| `05_defense_composition_figure.py` | defense_composition.pdf | §2 Composition Algebra |
| `06_architecture_comparison_figure.py` | architecture_comparison.pdf | §4.3 Finding 3 |
| `07_scalability_figure.py` | scalability.pdf | §S4 Scalability |
| `08_ablation_figure.py` | ablation.pdf | §S4 Ablation |

## Analysis Scripts (8 scripts)

| Script | Purpose |
|--------|---------|
| `run_full_evaluation.py` | Full evaluation matrix (simulation/pipeline/LLM modes) |
| `run_statistical_analysis.py` | Hypothesis tests (H1/H2/H3), effect sizes, assumptions |
| `run_ablation.py` | Component removal, minimal config, pairwise synergy |
| `run_sensitivity_analysis.py` | Parameter sweeps, sensitivity ranking, 2D grid search |
| `run_cross_validation.py` | Stratified 5-fold cross-validation on attack corpus |
| `run_multi_seed.py` | Multi-seed stability analysis (CV across 30 seeds) |
| `run_colony_benchmarks.py` | Colony-level CogSec benchmark scoring (5 scenarios) |
| `run_llm_demo.py` | Live LLM multiagent CIF evaluation via Ollama |

## Verification & Formal (3 scripts)

| Script | Purpose |
|--------|---------|
| `run_formal_validation.py` | Validates Paper 1 theorems via NuSMV/SPIN/TLA+ |
| `verify_formal_specs.py` | Generates and verifies formal specification files |
| `verify_manuscript.py` | Checks citations, labels, refs, images, style, tables |

## Utilities (1 script)

| Script | Purpose |
|--------|---------|
| `convert_latex_tables.py` | Converts LaTeX tables in manuscript `.md` files to Markdown pipe tables |

## Orchestrators (3 scripts)

| Script | Purpose |
|--------|---------|
| `generate_all_data.py` | Run all data generation scripts |
| `generate_all_figures.py` | Run all 8 figure scripts |
| `generate_all_tables.py` | Run all table generation |

## Thin Orchestrator Pattern

All scripts follow the thin orchestrator pattern:

```python
#!/usr/bin/env python3
"""Script follows thin orchestrator pattern."""
from pathlib import Path
from src.module import compute  # Import from src

def main():
    output_dir = Path("output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use src methods for computation
    results = compute()
    
    # Script handles only visualization/output
    fig = visualize(results)
    fig.savefig(output_dir / "figure.pdf")
    print(output_dir / "figure.pdf")

if __name__ == "__main__":
    main()
```

**Required:**

- All computation via `src/` imports
- Scripts handle only I/O and visualization
- Print output paths for manifest collection

**Forbidden:**

- Business logic in scripts
- Algorithm implementation
- Direct numerical computation
