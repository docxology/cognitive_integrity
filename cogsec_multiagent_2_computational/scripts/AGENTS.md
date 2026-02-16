# Cognitive Security Scripts - Agent Reference

Scripts for figure generation, data analysis, and manuscript verification for CIF Paper 2.

## Manuscript Figures (8 scripts)

| Script | Figure | Section |
|--------|--------|---------|
| `01_attack_surface_figure.py` | attack_surface.pdf | §3 Attack Corpus |
| `02_trust_decay_figure.py` | trust_decay.pdf | §5 Results |
| `07_roc_curves_figure.py` | roc_curves.pdf | §5 Results |
| `10_defense_composition_figure.py` | defense_composition.pdf | §6 Discussion |
| `13_ablation_study_figure.py` | ablation_study.pdf | §5 Results |
| `14_detection_performance_figure.py` | detection_performance.pdf | §5 Results |
| `16_comprehensive_taxonomy_figure.py` | comprehensive_taxonomy.pdf | §3 Attack Corpus |
| `17_cif_comprehensive_figure.py` | cif_comprehensive.pdf | §5 Results |

## Analysis Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `06_generate_data.py` | Generate experimental data | data/*.json |
| `run_ablation.py` | Ablation study | data/ablation_results.json |
| `run_cross_validation.py` | 5-fold CV | data/cross_validation_results.json |
| `run_full_evaluation.py` | 950×6 evaluation | data/full_evaluation_results.json |
| `run_multi_seed.py` | Multi-seed analysis | data/multi_seed_results.json |
| `run_sensitivity_analysis.py` | Parameter sensitivity | data/sensitivity_results.json |
| `run_statistical_analysis.py` | Hypothesis testing | data/statistical_results.json |
| `run_formal_validation.py` | Formal validation | data/formal_validation_results.json |
| `run_colony_benchmarks.py` | Benchmark data | data/colony_results.json |
| `verify_manuscript.py` | Manuscript validation | Verification report |

## Orchestrators

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
