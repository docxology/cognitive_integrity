# Cognitive Integrity Program - Agent Reference

Program directory containing the Cognitive Security for Multiagent Operators research series.

## Location and discovery

- **Path:** `projects/cognitive_integrity/` (active nested program directory).
- **Pipeline / PDF:** use qualified names: `cognitive_integrity/cogsec_multiagent_<part>`.
- **Resolution:** `infrastructure.project.discovery.resolve_project_root` prefers `projects/<name>` then `projects_in_progress/<name>`; nested segments must appear in `--project` (e.g. `cognitive_integrity/cogsec_multiagent_2_computational`).

## Projects

| Project | Description | DOI |
| ------- | ----------- | --- |
| `cogsec_multiagent_1_theory/` | Part 1 v2: Theoretical foundations — trust calculus, defense composition algebra, adversary taxonomy, CIF-AD-OODA | 10.5281/zenodo.18364119 |
| `cogsec_multiagent_2_computational/` | Part 2 v2: Computational validation — 950-attack corpus, adversarial training, red-teaming, colony 500-agent stress | 10.5281/zenodo.18364128 |
| `cogsec_multiagent_3_practical/` | Part 3+4 merged: Practical guidance + cross-domain CIF-AD-OODA applications | 10.5281/zenodo.18364130 |

## Series overview

The Cognitive Integrity Framework (CIF) provides defense-in-depth security for multiagent AI systems through:

- **Trust Calculus**: Bounded delegation with provable decay
- **Cognitive Firewall**: Multi-stage input classification
- **Belief Sandbox**: Verified/provisional partitioning
- **Byzantine Consensus**: Fault-tolerant agreement
- **Tripwire / Drift Detection**: Canary belief monitoring, KL-divergence surveillance
- **Provenance Tracking**: Information flow with taint labels

Part 4 additionally contributed three novel defense extensions (now merged into Part 3+4): verification channel separation, active perturbation probing, and physics-informed invariants.

## Cross-paper reading guide

Each paper stands alone; the bridge is:

- **Formal definitions** live in Part 1 (Trust Calculus, Defense Composition Algebra, Adversary Taxonomy)
- **Empirical evidence** lives in Part 2 (Results, Ablations, parametric analysis — see that manuscript for architecture counts and ceiling definitions)
- **Engineering guidance + domain applications** live in Part 3+4 (merged): Deployment, Incident Response, Monitoring, Cost-Benefit, ten-domain CIF-AD-OODA analyses, universal attack patterns, incident retrospective

## Evidence and implementation spine

- [`cogsec_multiagent_2_computational/docs/claims_traceability.md`](cogsec_multiagent_2_computational/docs/claims_traceability.md)
- [`cogsec_multiagent_2_computational/docs/framework_validation.md`](cogsec_multiagent_2_computational/docs/framework_validation.md)

## Repository

- GitHub: <https://github.com/docxology/cognitive_integrity>
- DOIs: 10.5281/zenodo.18364119, .18364128, .18364130 (Parts 3+4 merged under .18364130)

## Navigation

Each project follows the standalone paradigm with:

- `manuscript/` — Paper content
- `src/` — Source implementations
- `scripts/` — Entry point scripts
- `tests/` — Test suites
- `docs/` — Technical documentation (Paper 2 has usage guides and claims traceability)
- `output/` — Generated artifacts (figures, PDFs, slides)

## Artifacts and ignores

- Each part’s generated PDFs, figures, and reports live under that part’s `output/` and (after `05_copy_outputs.py`) under `output/cognitive_integrity/<part>/`. Program-level [`.gitignore`](.gitignore) ignores `**/output/`, cache dirs, and `**/manuscript_verification.log`.

## Build / test (from repo root)

**When nested inside `docxology/template`** (`./run.sh` and `scripts/` present at that repo's root):

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -q
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -q
```

Run one part at a time if you need to isolate failures. Part 2 imports `scipy` (see that part’s `pyproject.toml`); if imports fail, `uv sync` from the **repository root** first, or sync that part’s environment as described in the program [README](README.md).

**In a standalone checkout** (no `run.sh` at this root), there is no repo-root entry point — build/test each part from its own directory instead: `uv sync && uv run pytest tests/ -q && uv run ruff check .`, plus `make all` in `cogsec_multiagent_2_computational/` for the full data/figures/tables/verify pipeline, or `uv run python scripts/verify_manuscript.py --root manuscript` in Parts 1/3. See the program [README](README.md) § Building.
