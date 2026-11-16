# Cognitive Integrity Framework: Computational Validation and Empirical Analysis

Part 2 of the **Cognitive Security for Multiagent Operators** series — **Version 2.0.0 (2026-08-26)**.

**Status: Published (first publication)** | **DOI:** [10.5281/zenodo.22134546](https://doi.org/10.5281/zenodo.22134546)

## Highlights

- **Adversarial-training parametric simulation** (§05g): 5 modeled rounds; final modeled DR 67.9%, +23.2 percentage points over the modeled baseline; projected Nash-equilibrium DR 100%. These are nonmeasured design-model outputs, not observed training improvements.
- **Red-team evaluation framework** (§05h): 12 mutation operators; implemented evasion sweep and coverage analysis across category-derived Ω_1–Ω_5 annotations
- **Ω_1–Ω_5 attack annotations** (§03): Category-derived technique-level mapping, distinct from Part 1's access-based adversary taxonomy; Ω_5 gossip-poisoning gap identified
- **Category-theoretic foundations**: Full typed categorical framework — defense lattice (7 axioms ✓), symmetric monoidal category (unitors, associator, symmetry ✓), operad structure (unit + associativity ✓), enriched category over [0,1] (✓), pipeline monad (3 monad laws ✓), Kan extensions between architectures (✓), lens/optic profunctor (3 lens laws ✓), F-algebra catamorphism — serialized as JSON via `scripts/generate_composer_data.py`
- **Composable visualization engine**: DefenseGraph (DAG), CategoryDiagram (commutative diagrams), LatticeViz (Hasse), OperadPlot (trees), MonadFlow (Kleisli), LensDiagram — all Python/Graphviz-based
- **Algebra extension**: Hybrid detection rate (Corollary 3.3), weighted parallel (Gaussian approx), optimal module ordering (descending rate sort), latency models (series sum, parallel max, hybrid fast_max+deep_sum)
- **Composer data API** (`src/visualization/composer_data.py`): Full 8-module registry, algebra formulas, 4 preset pipelines, category theory verification results — exported as `output/data/composer_data.json` (0.03s generation)
- **Composer data bundle** (`output/data/composer_data.json`): the eight defense modules with their attack families, and each module's measured detection rate and latency hydrated from `output/data/module_capability_matrix.json`. There is no interactive application in this repository.
- **Extended S10** (information geometry): Complete Fisher information matrix derivations; natural gradient in CIF threshold space; geometric interpretation of drift threshold
- **New supplement S11** (adversarial training theory): AT game formulation; convergence guarantees; connection to information geometry
- **Colony stress tests** (100–500 agents): no-error and bounded-runtime checks; these report no validated detection rate
- **Property-based tests** (Hypothesis): mathematical-invariant checks across CIF modules; see the current test inventory for collected counts
- **Extended formal verification**: TLA+ v2 (9 safety invariants, 3 liveness properties); Promela v2 (8 LTL properties); NuSMV v2 (composition algebra properties)
- **New src/redteam/ module**: AdversarialGenerator, AttackMutator, NashEquilibriumEstimator, convergence analysis
- **11 new references**: Adversarial training (Madry 2018, Goodfellow 2015), game theory (von Neumann 1928), network topology (Watts-Strogatz 1998), Hypothesis library

## Overview

This paper provides **computational validation** of the Cognitive Integrity Framework (CIF) through implementation, benchmarking, and statistical analysis. Architecture-specific ceilings come from parametric simulations; the multi-seed pipeline measurements are architecture-agnostic.

**Prerequisites:** Part 1 for notation ([`S03_notation.md`](../cogsec_multiagent_1_theory/docs/manuscript/S03_notation.md)); Python and `uv` for tests and scripts.

## Primary Focus

- **Implementation**: Defense mechanisms (firewall, sandbox, trust, consensus) + adversarial training + red-teaming
- **Attack Corpus**: 1,475 attacks across 5 categories and fifteen subcategories, carrying a category-derived technique-level Ω mapping (distinct from Part 1's access-based taxonomy)
- **Validation**: Architecture-agnostic pipeline measurements; four modeled target architectures (Claude Code, AutoGPT, CrewAI, LangGraph) in the historical parametric simulation; colony benchmarks reporting detection results at 20–100 agents, plus non-functional stress tests (no-error/runtime only) at 100–500 agents
- **Analysis**: Statistical significance, ablation studies, scalability benchmarks, adversarial training convergence

## Paper Series

| Part | Title | Focus | Status | DOI |
| ---- | ----- | ----- | ------ | --- |
| 1 | Formal Foundations | Theory, proofs, formalisms | **v2.0, Second Edition** | [10.5281/zenodo.22134544](https://doi.org/10.5281/zenodo.22134544) |
| **2 (This, v2.0)** | Computational Validation | Empirical results, adversarial training | **First publication** | [10.5281/zenodo.22134546](https://doi.org/10.5281/zenodo.22134546) |
| 3+4 (merged) | Practical Guidance + Applications | Deployment + domains | v2.0, first publication | [10.5281/zenodo.22134548](https://doi.org/10.5281/zenodo.22134548) |

## Project Structure

```text
cogsec_multiagent_2_computational/
├── docs/manuscript/           # Paper content
│   ├── 00_abstract.md–07_conclusion.md
│   ├── 05g_adversarial_training.md
│   ├── 05h_redteam_evaluation.md
│   ├── S01–S10 supplementary sections
│   ├── S11_adversarial_training_theory.md
│   └── references.bib
├── src/
│   ├── core/             # Defense mechanism implementations
│   ├── colony/           # Multi-agent colony simulations
│   ├── formal/           # Formal verification and TLA+/Promela/SMV specs
│   ├── redteam/          # Adversarial training framework
│   │   ├── __init__.py   # AdversarialTrainer, ATConfig, NashEquilibriumEstimator
│   │   ├── generator.py  # AdversarialGenerator, AttackMutator
│   │   └── convergence.py # natural_gradient_at_step, geometric_convergence_projection
│   ├── statistics/       # Statistical analysis
│   ├── visualization/    # Figure generation + composable visualization engine
├── tests/                # Test suite; see the tracked inventory for current counts
│   ├── test_colony_stress.py    # Stress tests at 100-500 agents
│   ├── test_property_based.py   # Hypothesis property-based tests
│   └── test_redteam.py          # Adversarial-training tests
├── output/formal/        # Formal specifications
│   ├── CognitiveIntegrityFramework_v2.tla
│   ├── cif_model_v2.pml
│   └── cif_model_v2.smv
├── scripts/              # Evaluation and figure scripts
└── docs/                 # Technical documentation
```

Current collected-test totals are recorded in the [test inventory](output/data/test_inventory.json), not hard-coded here.

## Citation

```bibtex
@article{friedman2026cogsec2,
  author    = {Friedman, Daniel Ari},
  title     = {Cognitive Integrity Framework: Computational Validation and Empirical Analysis},
  year      = {2026},
  doi       = {10.5281/zenodo.22134546},
  publisher = {Zenodo},
  note      = {Part 2, v2.0 (first publication), released 2026-08-26.
               Cognitive Security for Multiagent Operators series.}
}
```

## Usage

```bash
# Run full test suite (90%+ coverage required)
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Run adversarial training evaluation
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42

# Run red-team evaluation
uv run python scripts/run_redteam.py --seed 42

# Verify the category-theoretic foundations
uv run python -c "from src.formal.category_theory_advanced import run_all_verifications; import json; print(json.dumps(run_all_verifications(), indent=2))"

# Generate the composer data JSON bundle
uv run python scripts/generate_composer_data.py --verbose

# Generate composable visualization diagrams (PDF)
uv run python -c "from src.visualization.composable import DefenseGraph, CategoryDiagram, LatticeViz, OperadPlot, MonadFlow, LensDiagram; [g.render(f'output/figures/{n}', format='pdf', cleanup=False) for n, g in [('defense_graph', DefenseGraph()), ('commutative_diagram', CategoryDiagram()), ('lattice_diagram', LatticeViz()), ('operad_trees', OperadPlot()), ('monad_flow', MonadFlow()), ('lens_diagram', LensDiagram())]]"

# Inspect the composer data bundle (there is no interactive application)
cat output/data/composer_data.json

# Run colony stress tests (100-500 agents)
uv run pytest tests/test_colony_stress.py -v

# Run property-based tests (Hypothesis)
uv run pytest tests/test_property_based.py -v

# Run formal validation (7 theorems)
uv run python scripts/run_formal_validation.py --seed 42

# Run historical parametric evaluation (950 attacks × 4 modeled architectures; no benign arm)
uv run python scripts/run_full_evaluation.py --seed 42

# Run statistical analysis (H1/H2/H3 hypothesis tests)
uv run python scripts/run_statistical_analysis.py --seed 42

# Run ablation studies
uv run python scripts/run_ablation.py --seed 42

# Run colony benchmarks
uv run python scripts/run_colony_benchmarks.py --seed 42

# Run sensitivity analysis
uv run python scripts/run_sensitivity_analysis.py --seed 42

# Generate all data, figures, and tables
uv run python scripts/generate_all_data.py --seed 42
uv run python scripts/generate_all_figures.py
uv run python scripts/generate_all_tables.py
```

## Building the manuscript PDF

From the template repository root:

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_2_computational
```

## Documentation

Comprehensive technical documentation is available in [`docs/`](docs/):

- [Documentation Index](docs/README.md) — index of all Part 2 documentation
- [Claims Traceability](docs/claims_traceability.md) — Lists concept-to-code mappings and the registered numeric-claim verification boundary
- [Framework Validation](docs/framework_validation.md) — How to reproduce all experiments (seed=42)
- [Usage Guides](docs/usage_guides/) — Per-component guides with code examples

## Current Artifact Summary

| Evaluation Mode | Detection Rate | Notes |
| :--- | :---: | :--- |
| Multi-seed pipeline (architecture-agnostic; 30 seeds × 100 stratified attacks + 120 benign messages per seed) | 86.3% mean TPR | Overall population SD 0.021; CV 0.0243; range 82–90%; mean FPR 18.53% over the 120 benign messages per seed. `stable=false` because of per-category CVs. |
| Adversarial-training parametric simulation (5 modeled rounds) | 67.9% final modeled DR | +23.2 percentage points over the 44.7% modeled baseline; nonmeasured |
| Projected Nash-equilibrium DR (parametric model) | 100% modeled projection | Geometric-series projection; nonmeasured |
| LLM validation (Gemma 3 4B, N=10) | 80–100% | Per architecture |
| Colony benchmarks (20–100 agents) | 80.7–100% | Structured scenarios |
| Colony stress tests (500 agents) | Not measured | No-error/runtime checks only; no validated detection rate |
| Parametric simulation ceiling (950 attacks × 4 modeled architectures = 3,800 attack instances; no benign arm) | 96–100% simulated DR | Design-level maximum; no measured FPR or field-performance bound |

## Repository

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.22134546](https://doi.org/10.5281/zenodo.22134546)

These manuscripts are built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Notation

All notation follows the canonical definitions in Part 1: [`cogsec_multiagent_1_theory/docs/manuscript/S03_notation.md`](../cogsec_multiagent_1_theory/docs/manuscript/S03_notation.md).
