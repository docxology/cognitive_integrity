---
name: cogsec-multiagent-2-computational
description: Cognitive Integrity Framework — Part 2 computational validation (3300+ tests, statistics, formal proofs, attack corpus, ablation studies)
triggers:
  - when: "user mentions 'Part 2' or 'computational validation' or 'empirical validation'"
    action: "route to this project"
  - when: "task involves statistics, evaluation metrics, attack corpus, or ablation analysis"
    action: "direct to this project"
version: 1.0.0
author: Daniel Ari Friedman
license: MIT
---

# Cognitive Integrity Framework — Part 2 (Computational Validation)

## Purpose

This skill directs LLM agents to **Part 2** of the Cognitive Security for Multiagent Operators series. Part 2 provides the computational validation engine:

- **3300+ data-driven tests** (90%+ coverage, zero mocks)
- **Statistics module** (hypothesis testing, confidence intervals, effect sizes, ANOVA, Bayesian analysis)
- **Formal methods** (TLA+, NuSMV, Spin specs; category theory; theorem registry)
- **Attack corpus** — 950+ real attack variants (injection, trust exploitation, belief manipulation, coordination)
- **Evaluation framework** (precision/recall, ROC, scalability, benchmarking)
- **Ablation studies** (component removal synergy, minimal configuration)
- **Visualization pipeline** (23 figure generators, 10 table generators)
- **Manuscript injector/verifier** (automated claim-to-code mapping)

## When to Use

Invoke this skill when:
- User asks for empirical results, performance numbers, or statistical significance
- Task involves running experiments, generating figures/tables, or reproducing paper claims
- Need to validate formal theorems or run the theorem registry
- Working with the attack corpus or defense implementations
- Modifying evaluation metrics or ablation methodology

## Key Directories

- `src/statistics/` — Statistical analysis engine
- `src/evaluation/` — Metrics, benchmarking, ROC analysis
- `src/data/` — Data generation, loaders, schema
- `src/attacks/` — Attack corpus generators and validation
- `src/formal/` — TLA+/NuSMV/Spin specs, category theory, theorem proofs
- `src/colony/` — Adversarial multiagent models (sybil, quorum manipulation, emergent misalignment)
- `src/core/` — Defense implementations (firewall, tripwire, sandbox, trust, provenance, consensus, invariants, detection)
- `src/visualization/figures/` — Publication figure generators
- `src/visualization/tables/` — LaTeX table generators
- `src/manuscript/` — Injector and verifier for automated manuscript assembly
- `docs/` — Claims traceability, framework validation, usage guides

## Commands

```bash
# Full test suite (3,380 collected (3,377 pass / 3 skip); ~90-160s with coverage)
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -q

# Run specific module tests
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/test_formal.py -v
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/test_statistics.py -v
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/test_ablation.py -v

# Generate all figures
uv run python projects/cognitive_integrity/cogsec_multiagent_2_computational/scripts/generate_all_figures.py

# Validate manuscript claims
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/test_manuscript_claims.py -v

# Run the theorem registry (validate all formal claims)
uv run python -c "from projects.cognitive_integrity.cogsec_multiagent_2_computational.src.formal.theorem_registry import TheoremRegistry; print(TheoremRegistry().summary())"
```

## Cross-Part Discipline

- Defers to **Part 1** for formal definitions and theorem statements.
- Feeds results to **Part 3+4** for deployment guidance and domain applications.
- All headline metrics (e.g., "96–100% at the parametric ceiling") originate here; consult `docs/claims_traceability.md` for precise sources.

## Performance Notes

- Test suite is large (3,380 collected (3,377 pass / 3 skip) with --cov; ~90s-2.6min).
- Uses `pytest-timeout` (2s default per test) to catch hangs.
- Parallel execution possible: `pytest -n auto` (requires pytest-xdist).

## Agent Tips

- **Stateless tests:** All tests compute from scratch; no shared fixture state leakage.
- **Determinism:** Random seeds fixed (utils/random_seed.py) — do not remove.
- **Matplotlib:** Agg backend enforced in `conftest.py`; figures should call `save_figure()` from `visualization.style`.
- **Type hints:** Complete across codebase; run `mypy src/` to verify.
