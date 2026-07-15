# Cognitive Integrity Framework: Computational Validation and Empirical Analysis (Second Edition)

Part 2 of the **Cognitive Security for Multiagent Operators** series — **Version 2.0 (2026-07-05)**.

**Status: Preprint** | **DOI:** [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128)

## What's New in v2.0

- **Adversarial training evaluation** (§05g): 5 rounds of iterative AT with threshold refinement; +3.4 pp over pre-AT baseline; convergence projection to Nash equilibrium DR ≈ 50.5%
- **Red-team evaluation framework** (§05h): 12 mutation operators; 5 multi-stage campaign scenarios; coverage analysis across Ω_1–Ω_5
- **Ω_1–Ω_5 attack taxonomy** (§03): Full mapping of 950-attack corpus to adversary capability levels; Ω_5 gossip-poisoning gap identified
- **Category-theoretic foundations** (v2.0+): Full typed categorical framework — defense lattice (7 axioms ✓), symmetric monoidal category (unitors, associator, symmetry ✓), operad structure (unit + associativity ✓), enriched category over [0,1] (✓), pipeline monad (3 monad laws ✓), Kan extensions between architectures (✓), lens/optic profunctor (3 lens laws ✓), F-algebra catamorphism — serialized as JSON via `scripts/generate_composer_data.py`
- **Composable visualization engine**: DefenseGraph (DAG), CategoryDiagram (commutative diagrams), LatticeViz (Hasse), OperadPlot (trees), MonadFlow (Kleisli), LensDiagram — all Python/Graphviz-based
- **Algebra extension**: Hybrid detection rate (Corollary 3.3), weighted parallel (Gaussian approx), optimal module ordering (descending rate sort), latency models (series sum, parallel max, hybrid fast_max+deep_sum)
- **Composer data API** (`src/visualization/composer_data.py`): Full 8-module registry, algebra formulas, 4 preset pipelines, category theory verification results — exported as `output/data/composer_data.json` (0.03s generation)
- **Drag-and-drop web UI v2** (`output/web/cif_composer_v2.html`): 2,455-line ground-up rewrite — black/gray/white theme with two user-selectable accent colors (localStorage-persisted), search-filtered palette with animated drag preview, D3 zoom/pan canvas with bezier edge routing, right-click edge context menu, 20-step undo (Ctrl+Z), parameter sliders, Ω-coverage pills, 6 category law indicators, 9 D3 Category Explorer diagrams, Python/JSON/SVG export, dark/light toggle
- **Extended S10** (information geometry): Complete Fisher information matrix derivations; natural gradient in CIF threshold space; geometric interpretation of drift threshold
- **New supplement S11** (adversarial training theory): AT game formulation; convergence guarantees; connection to information geometry
- **Colony stress tests** (100–500 agents): 23 new stress tests; 500-agent simulations complete in <60s
- **Property-based tests** (Hypothesis): 19 property-based tests verifying mathematical invariants across CIF modules
- **Extended formal verification**: TLA+ v2 (9 safety invariants, 3 liveness properties); Promela v2 (8 LTL properties); NuSMV v2 (composition algebra properties)
- **New src/redteam/ module**: AdversarialGenerator, AttackMutator, NashEquilibriumEstimator, convergence analysis
- **11 new references**: Adversarial training (Madry 2018, Goodfellow 2015), game theory (von Neumann 1928), network topology (Watts-Strogatz 1998), Hypothesis library

## Overview

This paper provides **computational validation** of the Cognitive Integrity Framework (CIF) through implementation, benchmarking, and statistical analysis across production multiagent architectures.

**Prerequisites:** Part 1 for notation ([`S03_notation.md`](../cogsec_multiagent_1_theory/manuscript/S03_notation.md)); Python and `uv` for tests and scripts.

## Primary Focus

- **Implementation**: Defense mechanisms (firewall, sandbox, trust, consensus) + adversarial training + red-teaming
- **Attack Corpus**: 950 attacks across 4 categories, fully mapped to Ω_1–Ω_5 adversary taxonomy
- **Validation**: Four target architectures (Claude Code, AutoGPT, CrewAI, LangGraph); colony simulations at 20–500 agents
- **Analysis**: Statistical significance, ablation studies, scalability benchmarks, adversarial training convergence

## Paper Series

| Part | Title | Focus | Status | DOI |
| ---- | ----- | ----- | ------ | --- |
| 1 | Formal Foundations | Theory, proofs, formalisms | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| **2 (This, v2.0)** | Computational Validation | Empirical results, adversarial training | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| 3+4 (merged) | Practical Guidance + Applications | Deployment + domains | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

## Project Structure

```text
cogsec_multiagent_2_computational/
├── manuscript/           # Paper content (34 files, v2.0)
│   ├── 00_abstract.md–07_conclusion.md
│   ├── 05g_adversarial_training.md      # NEW v2.0
│   ├── 05h_redteam_evaluation.md        # NEW v2.0
│   ├── S01–S10 supplementary sections
│   ├── S11_adversarial_training_theory.md  # NEW v2.0
│   └── references.bib  (835 entries, 11 new in v2.0)
├── src/
│   ├── core/             # Defense mechanism implementations
│   ├── colony/           # Multi-agent colony simulations (6 modules)
│   ├── formal/           # Formal verification (15 modules: category_theory, category_theory_advanced, extended_specs, TLA+/Promela/SMV specs)
│   ├── redteam/          # Adversarial training framework (NEW v2.0)
│   │   ├── __init__.py   # AdversarialTrainer, ATConfig, NashEquilibriumEstimator
│   │   ├── generator.py  # AdversarialGenerator, AttackMutator
│   │   └── convergence.py # natural_gradient_at_step, geometric_convergence_projection
│   ├── statistics/       # Statistical analysis (12 modules)
│   ├── visualization/    # Figure generation + composable visualization engine
├── manuscript/           # Paper content (34 files, v2.0)
├── tests/                # 44 test files (3+ new in v2.0+)
│   ├── test_colony_stress.py    # NEW: 23 stress tests at 100-500 agents
│   ├── test_property_based.py   # NEW: 19 Hypothesis property-based tests
│   └── test_redteam.py          # NEW: 35 adversarial training tests
├── output/formal/        # Formal specs (6 files: original + v2)
│   ├── CognitiveIntegrityFramework_v2.tla  # NEW: 9 safety, 3 liveness props
│   ├── cif_model_v2.pml                    # NEW: 8 LTL properties
│   └── cif_model_v2.smv                    # NEW: composition algebra props
├── scripts/              # Evaluation and figure scripts
└── docs/                 # Technical documentation
```

## Citation

```bibtex
@article{friedman2026cogsec2,
  author    = {Friedman, Daniel Ari},
  title     = {Cognitive Integrity Framework: Computational Validation and Empirical Analysis (Second Edition)},
  year      = {2026},
  doi       = {10.5281/zenodo.18364128},
  publisher = {Zenodo},
  note      = {Part 2, v2.0. Cognitive Security for Multiagent Operators series.
               New in v2.0: adversarial training (5 rounds), red-team framework,
               Ω_1-Ω_5 attack taxonomy, Fisher information metric derivations,
               colony stress tests (100-500 agents), property-based tests.}
}
```

## Usage

```bash
# Run full test suite (90%+ coverage required)
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# NEW v2.0: Run adversarial training evaluation
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42

# NEW v2.0: Run red-team evaluation
uv run python scripts/run_redteam.py --seed 42

# NEW v2.0: Verify all category-theoretic foundations (25/25 checks)
uv run python -c "from src.formal.category_theory_advanced import run_all_verifications; import json; print(json.dumps(run_all_verifications(), indent=2))"

# NEW: Generate composer data JSON for web UI
uv run python scripts/generate_composer_data.py --verbose

# NEW: Generate composable visualization diagrams (PDF)
uv run python -c "from src.visualization.composable import DefenseGraph, CategoryDiagram, LatticeViz, OperadPlot, MonadFlow, LensDiagram; [g.render(f'output/figures/{n}', format='pdf', cleanup=False) for n, g in [('defense_graph', DefenseGraph()), ('commutative_diagram', CategoryDiagram()), ('lattice_diagram', LatticeViz()), ('operad_trees', OperadPlot()), ('monad_flow', MonadFlow()), ('lens_diagram', LensDiagram())]]"

# NEW: Open the drag-and-drop defense pipeline builder v2
open output/web/cif_composer_v2.html

# Run colony stress tests (100-500 agents)
uv run pytest tests/test_colony_stress.py -v

# Run property-based tests (Hypothesis)
uv run pytest tests/test_property_based.py -v

# Run formal validation (7 theorems)
uv run python scripts/run_formal_validation.py --seed 42

# Run full evaluation matrix (950 attacks)
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

- [Claims Traceability](docs/claims_traceability.md) — Maps every manuscript claim to its code implementation and test
- [Framework Validation](docs/framework_validation.md) — How to reproduce all experiments (seed=42)
- [Usage Guides](docs/usage_guides/) — Per-component guides with code examples

## Key Results (v2.0 Summary)

| Evaluation Mode | Detection Rate | Notes |
| :--- | :---: | :--- |
| Multi-seed pipeline (N=30, Claude Code) | 44.7% mean | CV=0.097 |
| After 5 rounds of adversarial training | 48.1% | +3.4 pp over baseline |
| Projected Nash equilibrium DR | 50.5% | Geometric series projection |
| LLM validation (Gemma 3 4B, N=10) | 80–100% | Per architecture |
| Colony benchmarks (20–100 agents) | 81–100% | Structured scenarios |
| Colony stress tests (500 agents) | Valid | No errors; DR stable |
| Parametric simulation ceiling | 94–100% | Design-level maximum |
| Property-based test coverage | 19/19 pass | Hypothesis library |

## Repository

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128)

These manuscripts are built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Notation

All notation follows the canonical definitions in Part 1: [`cogsec_multiagent_1_theory/manuscript/S03_notation.md`](../cogsec_multiagent_1_theory/manuscript/S03_notation.md).
