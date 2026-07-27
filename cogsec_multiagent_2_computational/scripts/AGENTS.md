# Cognitive Security Scripts — Agent Reference (Paper 2)

Agent guidance for working with the thin-orchestrator scripts in `cogsec_multiagent_2_computational/scripts/` (standalone repo) or `projects/working/cognitive_integrity/cogsec_multiagent_2_computational/scripts/` (template sidecar).

## Series Position

Paper 2 (*Computational Validation*) is the second paper in the three-paper *Cognitive Security for Multiagent Operators* series. Scripts here produce the empirical evidence cited by the sibling papers. See [../README.md](../README.md) for the series map.

When a script changes any result that siblings cite, update:

- `src.manuscript.verifier` expectations
- `output/data/` headline JSON
- Sibling cross-references (Part 1 §8 and Part 3+4 §3/§9–§10)

## Thin-Orchestrator Contract (MANDATORY)

```python
#!/usr/bin/env python3
"""Thin orchestrator — imports from src/, handles only I/O + viz."""
from pathlib import Path
from src.evaluation.runner import ExperimentRunner

def main():
    out = Path("output/data")
    out.mkdir(parents=True, exist_ok=True)
    result = ExperimentRunner(seed=42).run_all()   # computation in src/
    result.save(out / "experiment.json")
    print(out / "experiment.json")                 # stdout path for manifest

if __name__ == "__main__":
    main()
```

**Required**

- All computation delegated to `src/` imports.
- Scripts handle **only** I/O, visualization, logging, and manifest bookkeeping.
- Print output paths to `stdout` for pipeline manifest collection.
- Deterministic RNG (default `seed=42`, override via `--seed`).
- Respect `MPLBACKEND=Agg` for headless matplotlib.

**Forbidden**

- Business logic, algorithms, or direct numerical computation in scripts.
- Mocks, `unittest.mock`, `MagicMock`, `mocker.patch` — no mocks anywhere in the project (test suite enforces this via `src.validation.no_mock_enforcer` in infrastructure).
- Hard-coded paths outside the repo root.
- `print` statements that are not paths (use `logging`).

## Script Inventory (22 scripts — keep docs in sync)

| Category | Scripts |
| -------- | ------- |
| Orchestrators | `generate_all_data.py`, `generate_all_figures.py`, `generate_all_tables.py` |
| Analysis | `run_full_evaluation.py`, `run_statistical_analysis.py`, `run_ablation.py`, `run_sensitivity_analysis.py`, `run_cross_validation.py`, `run_multi_seed.py`, `run_colony_benchmarks.py`, `run_llm_demo.py`, `run_publication_suite.py`, `run_adversarial_training.py`, `run_redteam.py` |
| Verification | `run_formal_validation.py`, `verify_formal_specs.py`, `verify_manuscript.py` |
| Utilities | `convert_latex_tables.py`, `z_inject_manuscript_values.py`, `generate_figure_registry.py`, `auto_number_figures.py`, `generate_composer_data.py` |

When adding a new script: (1) update this table, (2) update [scripts/README.md](README.md), (3) add a test in `tests/` that smoke-tests the script's CLI surface.

## Manuscript-to-Script Anchor

| Manuscript Claim | Producing Script |
| ---------------- | ---------------- |
| §5 overall detection rates | `run_full_evaluation.py`, `run_multi_seed.py` |
| §5.6 / §5d ablation deltas | `run_ablation.py` |
| §5b statistical significance (H1/H2/H3) | `run_statistical_analysis.py` |
| §5c parameter sensitivity | `run_sensitivity_analysis.py` |
| §5e Bayesian uncertainty | `run_multi_seed.py` |
| Colony benchmarks (§5, §S03) | `run_colony_benchmarks.py` |
| LLM-backed validation (Abstract, §5) | `run_llm_demo.py` |
| Model-checking results (§S04) | `run_formal_validation.py`, `verify_formal_specs.py` |
| Manuscript integrity (citations, refs) | `verify_manuscript.py` |
| Auto-injected numerical values | `z_inject_manuscript_values.py` |
| §05g adversarial training (per-round DR deltas, Nash projection) | `run_adversarial_training.py` |
| §05h red-team evaluation (Ω-level generation, mutation sweep) | `run_redteam.py` |
| Figure/table auto-numbering | `generate_figure_registry.py`, `auto_number_figures.py` |
| Composer web-UI backend data | `generate_composer_data.py` |

## Live LLM Analysis

`run_llm_demo.py` and the LLM branch of `run_publication_suite.py` are opt-in during automated renders. They run real Ollama-backed agents and can take several minutes when Ollama is available. To execute them intentionally:

```bash
COGSEC_RUN_LLM_ANALYSIS=1 uv run python scripts/run_llm_demo.py
COGSEC_RUN_LLM_ANALYSIS=1 uv run python scripts/run_publication_suite.py
```

Without `COGSEC_RUN_LLM_ANALYSIS=1`, these scripts write a skip record and exit successfully so the manuscript render pipeline remains bounded and reproducible.

## Cross-Paper Reference Discipline

When a script changes headline numbers, agents must update **all** sibling papers' cross-references. Use `\cite{friedman2026cogsecN}` throughout:

| Bibkey | Paper | Key Sections that Cite Paper 2 |
| ------ | ----- | ------------------------------ |
| `friedman2026cogsec1` | Part 1: Formal Foundations | §8 Discussion, §9 Conclusion |
| `friedman2026cogsec3` | Part 3+4: Practitioner Guidance + Applications | §2/§3 Evidence and Methodology, §4 Discussion, §5 Deployment, §9–§10 Applications |

**DO NOT** mischaracterize Part 3+4 as "biological" or "eusocial" — that content lives in Part 1's S02 supplementary.

## CI / Verification

Before committing a non-trivial script change, run:

```bash
uv run python scripts/verify_manuscript.py   # citations, refs, figures
uv run pytest tests/ -x -q                   # smoke test suite
```

Expected: `verify_manuscript.py` prints **no warnings**; `pytest` passes with zero failures.
