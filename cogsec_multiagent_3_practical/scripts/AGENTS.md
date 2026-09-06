# Practical CogSec Scripts - Agent Reference

Thin-orchestrator figure scripts for the practical guide manuscript
(Part 3+4). Computation lives in `src/`; scripts only bootstrap the import
path, call a `src/` renderer, and write `output/figures/`.

## Script Inventory (9 scripts — keep docs in sync)

| Script | Purpose | Delegates to | Output |
|--------|--------|--------------|--------|
| `01_posture_radar_figure.py` | Security posture radar (five pillars) | `src/visualization` (`get_five_pillars_data`, `render_posture_radar`) | `output/figures/` PNG + PDF |
| `02_checklist_flowchart_figure.py` | Deployment checklist flow | `src/visualization` (`get_deployment_phases_data`, `render_checklist_flowchart`) | `output/figures/` PNG + PDF |
| `03_risk_matrix_figure.py` | Risk assessment matrix | `src/visualization` (`get_risk_matrix_data`, `render_risk_matrix`) | `output/figures/` PNG + PDF |
| `04_trust_decay_figure.py` | Trust decay visualization | `src/visualization` (`get_trust_decay_data`, `render_trust_decay`) | `output/figures/` PNG + PDF |
| `05_pitfall_severity_figure.py` | Pitfall severity chart | `src/visualization` (`get_pitfalls_data`, `render_pitfall_severity`) | `output/figures/` PNG + PDF |
| `06_timeline_figure.py` | Implementation timeline | `src/visualization` (`get_timeline_data`, `render_timeline`) | `output/figures/` PNG + PDF |
| `07_domain_coverage_figure.py` | CIF-AD-OODA domain coverage figures (Part 3+4 §10) | `src/applications/domain_coverage.py` (`render_domain_coverage_figures`) | `output/figures/` |
| `generate_all_figures.py` | Runs every `NN_*.py` in numeric order; exits non-zero listing failures | subprocess over the numbered scripts | all figures |
| `verify_manuscript.py` | Manuscript validation: cross-references, figure registration, citations | `src/verification` (`ManuscriptVerifier`) | `output/reports/` |

When adding a new script: update this table and [scripts/README.md](README.md)
so docs match the directory.

## Thin-Orchestrator Contract

- Scripts do argparse/path bootstrap only, then delegate to `src/` renderers.
- Import idiom (mirrors scripts 01–06): put the project root on `sys.path` and
  import the `src.*` package, e.g.
  `from src.applications.domain_coverage import render_domain_coverage_figures`.
- All plotting/data logic lives in `src/visualization/` and
  `src/applications/`; nothing numerical happens in `scripts/`.

## Usage

```bash
uv run python scripts/generate_all_figures.py   # every numbered figure, in order
uv run python scripts/07_domain_coverage_figure.py
uv run python scripts/verify_manuscript.py
```
