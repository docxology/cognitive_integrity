# Cognitive Security Scripts - Quick Reference

Figure generation and data analysis scripts for the CIF manuscript.

## Scripts

| Script | Output | Description |
|--------|--------|-------------|
| `01_attack_surface_figure.py` | Attack surface visualization | Threat taxonomy diagram |
| `02_trust_decay_figure.py` | Trust decay curves | Exponential decay visualization |
| `03_detection_results_figure.py` | Detection performance | ROC/precision-recall curves |
| `04_cif_architecture_figure.py` | System architecture | Component diagram |
| `05_threat_taxonomy_figure.py` | Threat classification | Adversary classes |
| `06_generate_data.py` | Experimental datasets | All analysis data |
| `07_roc_curves_figure.py` | ROC analysis | Detection thresholds |
| `08_scalability_figure.py` | Scalability metrics | Agent count vs performance |
| `09_attack_timeline_figure.py` | Attack progression | Temporal analysis |
| `10_defense_composition_figure.py` | Defense layers | Security stack |
| `11_trust_network_figure.py` | Trust graph | Agent relationships |
| `12_belief_sandbox_figure.py` | Sandbox state | Partition visualization |
| `13_ablation_study_figure.py` | Component analysis | Feature importance |
| `14_detection_performance_figure.py` | Detector comparison | Multi-detector analysis |
| `15_fp_mitigation_figure.py` | False positive handling | Mitigation strategies |
| `16_comprehensive_taxonomy_figure.py` | Full taxonomy | Attack categories |
| `17_cif_comprehensive_figure.py` | Complete framework | Full system diagram |
| `18_trust_calculus_figure.py` | Trust mathematics | Formula visualization |
| `verify_manuscript.py` | Validation report | Cross-reference checks |

## Quick Commands

```bash
# Generate all experimental data
python3 scripts/06_generate_data.py

# Generate key figures
python3 scripts/02_trust_decay_figure.py
python3 scripts/03_detection_results_figure.py
python3 scripts/04_cif_architecture_figure.py

# Verify manuscript
python3 scripts/verify_manuscript.py
```

## Output Locations

- Figures: `output/figures/`
- Data: `output/data/`
- Reports: `output/reports/`

## All scripts follow thin orchestrator pattern - import from src/, handle visualization only.
