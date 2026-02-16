# Cognitive Security Scripts

Figure generation, analysis, and verification scripts for CIF Paper 2.

## Quick Start

```bash
# Generate all 8 manuscript figures
python3 scripts/generate_all_figures.py

# Run all analysis
python3 scripts/run_statistical_analysis.py

# Verify manuscript
python3 scripts/verify_manuscript.py
```

## Manuscript Figures (8)

| Script | Figure |
|--------|--------|
| `01_attack_surface_figure.py` | attack_surface.pdf |
| `02_trust_decay_figure.py` | trust_decay.pdf |
| `07_roc_curves_figure.py` | roc_curves.pdf |
| `10_defense_composition_figure.py` | defense_composition.pdf |
| `13_ablation_study_figure.py` | ablation_study.pdf |
| `14_detection_performance_figure.py` | detection_performance.pdf |
| `16_comprehensive_taxonomy_figure.py` | comprehensive_taxonomy.pdf |
| `17_cif_comprehensive_figure.py` | cif_comprehensive.pdf |

## Analysis Scripts

| Script | Purpose |
|--------|---------|
| `run_ablation.py` | Component ablation study |
| `run_cross_validation.py` | 5-fold cross-validation |
| `run_full_evaluation.py` | Full 950-attack evaluation |
| `run_statistical_analysis.py` | Hypothesis testing |

## Output Locations

- Figures: `output/figures/`
- Data: `output/data/`
- Reports: `output/reports/`

All scripts follow thin orchestrator pattern - import from `src/`, handle visualization only.
