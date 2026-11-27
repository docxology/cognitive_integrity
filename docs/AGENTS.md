# AGENTS.md — Cognitive Integrity Program docs/

Agent-facing notes for this documentation tree.

## Layout

- `README.md` — human entry point; indexes this program docs/ and each part's own `docs/` folder.
- `verification/` contains the local trust fixture and its reproduction guide.
- `manuscript/` contains the finite trust assurance note and the publication inventory.

## Repository structure

The program root contains three self-contained sub-projects, each with its own
`docs/manuscript/`, `tests/`, `scripts/`, and pinned environment:

- `cogsec_multiagent_1_theory/`
- `cogsec_multiagent_2_computational/`
- `cogsec_multiagent_3_practical/`

Top-level `README.md` documents per-paper commands (`uv sync --locked`, `uv run pytest tests/ -q`,
`uv run python scripts/generate_all_figures.py`). Verify against it before running anything.

## Conventions

- Each sub-project is its own environment and test suite; do not run all suites in one process.
- Program-level provenance: `CHANGELOG.md`, `CITATION.cff`, and `AGENTS.md` at the repository root.

## Maintenance

Docs here are hand-maintained. When adding a part or renaming a sub-project, update
`docs/README.md` links and this file together.
