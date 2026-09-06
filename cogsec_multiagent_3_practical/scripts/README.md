# Practical CogSec Scripts

Thin-orchestrator scripts for the practical guide (Part 3+4). Figure generation
for the manuscript; computation lives in `src/` and each script only bootstraps
the import path, invokes a `src/` renderer, and writes `output/figures/`.

## Scripts

| Script | Purpose | Delegates to | Run command |
| ------ | ------- | ------------ | ----------- |
| `01_posture_radar_figure.py` | Security posture radar (five pillars) | `src/visualization` (`get_five_pillars_data`, `render_posture_radar`) | `uv run python scripts/01_posture_radar_figure.py` |
| `02_checklist_flowchart_figure.py` | Deployment checklist flowchart | `src/visualization` (`get_deployment_phases_data`, `render_checklist_flowchart`) | `uv run python scripts/02_checklist_flowchart_figure.py` |
| `03_risk_matrix_figure.py` | Risk assessment matrix | `src/visualization` (`get_risk_matrix_data`, `render_risk_matrix`) | `uv run python scripts/03_risk_matrix_figure.py` |
| `04_trust_decay_figure.py` | Trust decay visualization | `src/visualization` (`get_trust_decay_data`, `render_trust_decay`) | `uv run python scripts/04_trust_decay_figure.py` |
| `05_pitfall_severity_figure.py` | Pitfall severity chart | `src/visualization` (`get_pitfalls_data`, `render_pitfall_severity`) | `uv run python scripts/05_pitfall_severity_figure.py` |
| `06_timeline_figure.py` | Implementation timeline | `src/visualization` (`get_timeline_data`, `render_timeline`) | `uv run python scripts/06_timeline_figure.py` |
| `07_domain_coverage_figure.py` | CIF-AD-OODA domain coverage figures (Part 3+4 §10) | `src/applications/domain_coverage.py` (`render_domain_coverage_figures`) | `uv run python scripts/07_domain_coverage_figure.py` |
| `generate_all_figures.py` | Runs every numbered figure script in order; fails non-zero listing any failures | subprocess over `NN_*.py` in this directory | `uv run python scripts/generate_all_figures.py` |
| `verify_manuscript.py` | Manuscript validation (cross-references, figures, citations) | `src/verification` (`ManuscriptVerifier`) | `uv run python scripts/verify_manuscript.py` |

## Usage

```bash
# Regenerate every figure
uv run python scripts/generate_all_figures.py

# Generate a single figure
uv run python scripts/07_domain_coverage_figure.py

# Verify manuscript integrity
uv run python scripts/verify_manuscript.py
```

## Output Locations

- Figures: `output/figures/`
- Reports: `output/reports/`

## Thin-Orchestrator Contract

Scripts here bootstrap the project root onto `sys.path` and import from the
`src.*` package (e.g. `from src.applications.domain_coverage import ...`),
matching scripts 01–06. All figure construction lives in `src/`; scripts handle
only paths, rendering calls, and stdout reporting.
