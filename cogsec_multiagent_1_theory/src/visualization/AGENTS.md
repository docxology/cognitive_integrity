# src/visualization/ — Agent Notes

Figure-generation modules for Part 1 (trust calculus/decay/network, firewall,
sandbox, consensus, tripwire, provenance, detection/ROC, attack surface and
timeline, ablation, scalability, threat taxonomy, CIF architecture, and
comprehensive/taxonomy composites). `utils.py` holds shared plotting helpers.

- These are the Part 1 figure library; they write into `../../output/figures/`.
- Imported from `src/` modules and `scripts/generate_all_figures.py`.
- Regenerate: `uv run python scripts/generate_all_figures.py` (from part root).
- `cogsec_multiagent_theory.egg-info/` sibling at `src/` level is build
  metadata (uv-generated, never edit).
