# Cognitive Security Scripts - Quick Reference

Figure generation and data analysis scripts for the CIF manuscript (Part 1).
Thin orchestrators: scripts bootstrap the project root onto `sys.path`, import
from the `src.*` package, and handle output only — computation lives in `src/`.

## Scripts

| Script | Purpose | Delegates to | Run command |
|--------|---------|--------------|-------------|
| `01_attack_surface_figure.py` | Threat taxonomy / attack surface diagram | `src/visualization/attack_surface.py` | `uv run python scripts/01_attack_surface_figure.py` |
| `02_trust_decay_figure.py` | Trust decay curves across delegation depths | `src/visualization/trust_decay.py` | `uv run python scripts/02_trust_decay_figure.py` |
| `03_detection_results_figure.py` | Detection performance: ROC / precision-recall / F1 | `src/visualization/detection_results.py` | `uv run python scripts/03_detection_results_figure.py` |
| `04_cif_architecture_figure.py` | CIF component architecture diagram | `src/visualization/cif_architecture.py` | `uv run python scripts/04_cif_architecture_figure.py` |
| `05_threat_taxonomy_figure.py` | Adversary classes / threat classification | `src/visualization/threat_taxonomy.py` | `uv run python scripts/05_threat_taxonomy_figure.py` |
| `06_generate_data.py` | All experimental datasets (trust decay, detection, scenarios, consensus) | `src/data_generation.py` | `uv run python scripts/06_generate_data.py` |
| `07_roc_curves_figure.py` | ROC analysis / detection thresholds | `src/visualization/roc_curves.py` | `uv run python scripts/07_roc_curves_figure.py` |
| `08_scalability_figure.py` | Scalability: agent count vs performance | `src/visualization/scalability.py` | `uv run python scripts/08_scalability_figure.py` |
| `09_attack_timeline_figure.py` | Attack progression / temporal analysis | `src/visualization/attack_timeline.py` | `uv run python scripts/09_attack_timeline_figure.py` |
| `10_defense_composition_figure.py` | Defense layers / security stack | `src/visualization/defense_composition.py` | `uv run python scripts/10_defense_composition_figure.py` |
| `11_trust_network_figure.py` | Trust graph / agent relationships | `src/visualization/trust_network.py` | `uv run python scripts/11_trust_network_figure.py` |
| `12_belief_sandbox_figure.py` | Belief sandbox partition state | `src/visualization/belief_sandbox.py` | `uv run python scripts/12_belief_sandbox_figure.py` |
| `13_ablation_study_figure.py` | Component contribution analysis | `src/visualization/ablation_study.py` | `uv run python scripts/13_ablation_study_figure.py` |
| `14_detection_performance_figure.py` | Multi-detector comparison | `src/visualization/detection_performance.py` | `uv run python scripts/14_detection_performance_figure.py` |
| `15_fp_mitigation_figure.py` | False-positive mitigation strategies | `src/visualization/fp_mitigation.py` | `uv run python scripts/15_fp_mitigation_figure.py` |
| `16_comprehensive_taxonomy_figure.py` | Full attack taxonomy | `src/visualization/comprehensive_taxonomy.py` | `uv run python scripts/16_comprehensive_taxonomy_figure.py` |
| `17_cif_comprehensive_figure.py` | Complete framework diagram | `src/visualization/cif_comprehensive.py` | `uv run python scripts/17_cif_comprehensive_figure.py` |
| `18_trust_calculus_figure.py` | Trust calculus formulas / decay bounds | `src/visualization/trust_calculus.py` | `uv run python scripts/18_trust_calculus_figure.py` |
| `19_cif_ad_coupling_figure.py` | CIF-AD coupling heatmap: defense coverage by AD phase | `src/cif_ad_coupling.py` | `uv run python scripts/19_cif_ad_coupling_figure.py` |
| `20_ooda_phase_figure.py` | OODA phase diagram: phase-specific defenses and latency | self-contained (reads `output/figures/data`) | `uv run python scripts/20_ooda_phase_figure.py` |
| `generate_all_figures.py` | Runs every numbered figure script in order; exits non-zero listing failures | subprocess over `NN_*.py` in this directory | `uv run python scripts/generate_all_figures.py` |
| `generate_figure_registry.py` | Scans `docs/manuscript/*.md` for `{#fig:...}`/`{#tab:...}` labels; writes auto-numbered registry | self-contained | `uv run python scripts/generate_figure_registry.py` |
| `verify_manuscript.py` | Manuscript validation: cross-references, figure registration, citations | `src/verification` (`ManuscriptVerifier`) | `uv run python scripts/verify_manuscript.py` |

## Quick Commands

```bash
# Generate all experimental data
uv run python scripts/06_generate_data.py

# Regenerate every figure (single entry point)
uv run python scripts/generate_all_figures.py

# Generate key figures
uv run python scripts/02_trust_decay_figure.py
uv run python scripts/03_detection_results_figure.py
uv run python scripts/04_cif_architecture_figure.py

# Verify manuscript
uv run python scripts/verify_manuscript.py
```

## Output Locations

- Figures: `output/figures/`
- Data: `output/data/`
- Reports: `output/reports/`

## Thin-Orchestrator Pattern

Scripts put the project root on `sys.path` and import the `src.*` package
(e.g. `from src.visualization.trust_decay import generate_trust_decay_figure`);
all computation lives in `src/`, scripts handle I/O and rendering only.
`20_ooda_phase_figure.py` is the one self-contained exception: it draws from
data already under `output/figures/data`.
