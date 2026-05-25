# Cognitive Integrity Program - Agent Reference

Program directory containing the Cognitive Security for Multiagent Operators research series.

## Location and discovery

- **Path:** `projects/cognitive_integrity/` (active nested program directory).
- **Pipeline / PDF:** use qualified names: `cognitive_integrity/cogsec_multiagent_<part>`.
- **Resolution:** `infrastructure.project.discovery.resolve_project_root` prefers `projects/<name>` then `projects_in_progress/<name>`; nested segments must appear in `--project` (e.g. `cognitive_integrity/cogsec_multiagent_2_computational`).

## Projects

| Project | Description | DOI |
| ------- | ----------- | --- |
| `cogsec_multiagent_1_theory/` | Part 1: Theoretical foundations — trust calculus, defense composition algebra, adversary taxonomy, model-checked invariants | 10.5281/zenodo.18364119 |
| `cogsec_multiagent_2_computational/` | Part 2: Computational validation — 950-attack corpus, ablation studies, parametric ceiling, Bayesian uncertainty | 10.5281/zenodo.18364128 |
| `cogsec_multiagent_3_practical/` | Part 3: A qualitative review for practitioners — deployment guides, incident response, monitoring, cost--benefit, case studies | 10.5281/zenodo.18364130 |
| `cogsec_multiagent_4_applications/` | Part 4: Applications — CIF-AD-OODA integration, ten-domain goal-hijacking analysis, real-world incident retrospective | _DOI pending_ |

## Series overview

The Cognitive Integrity Framework (CIF) provides defense-in-depth security for multiagent AI systems through:

- **Trust Calculus**: Bounded delegation with provable decay
- **Cognitive Firewall**: Multi-stage input classification
- **Belief Sandbox**: Verified/provisional partitioning
- **Byzantine Consensus**: Fault-tolerant agreement
- **Tripwire / Drift Detection**: Canary belief monitoring, KL-divergence surveillance
- **Provenance Tracking**: Information flow with taint labels

Part 4 additionally contributes three novel defense extensions: verification channel separation, active perturbation probing, and physics-informed invariants.

## Cross-paper reading guide

Each paper stands alone; the bridge is:

- **Formal definitions** live in Part 1 (Trust Calculus, Defense Composition Algebra, Adversary Taxonomy)
- **Empirical evidence** lives in Part 2 (Results, Ablations, parametric analysis — see that manuscript for architecture counts and ceiling definitions)
- **Engineering guidance** lives in Part 3 (Deployment, Incident Response, Monitoring, Cost-Benefit)
- **Domain applications** live in Part 4 (Ten domains, Universal attack patterns, incident retrospective)

## Evidence and implementation spine

- [`cogsec_multiagent_2_computational/docs/claims_traceability.md`](cogsec_multiagent_2_computational/docs/claims_traceability.md)
- [`cogsec_multiagent_2_computational/docs/framework_validation.md`](cogsec_multiagent_2_computational/docs/framework_validation.md)

## Repository

- GitHub: <https://github.com/docxology/cognitive_integrity>
- DOIs: 10.5281/zenodo.18364119, .18364128, .18364130 (Part 4 DOI pending)

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

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -q
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -q
uv run pytest projects/cognitive_integrity/cogsec_multiagent_4_applications/tests/ -q
```

Run one part at a time if you need to isolate failures. Part 2 imports `scipy` (see that part’s `pyproject.toml`); if imports fail, `uv sync` from the **repository root** first, or sync that part’s environment as described in the program [README](README.md).
