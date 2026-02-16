# Cognitive Integrity Framework: Computational Validation (Paper 2)

Part 2 of the **Cognitive Security for Multiagent Operators** series.

**Status: Preprint** | **DOI:** [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128)

## Overview

This paper provides **computational validation** of the Cognitive Integrity Framework (CIF) through implementation, benchmarking, and statistical analysis across production multiagent architectures.

## Primary Focus

- **Implementation**: Defense mechanisms (firewall, sandbox, trust, consensus)
- **Attack Corpus**: 950 attacks across 4 categories
- **Validation**: 6 production architectures (Claude Code, AutoGPT, CrewAI, LangGraph, MetaGPT, Camel)
- **Analysis**: Statistical significance, ablation studies, scalability benchmarks

## Paper Series

| Part | Title | Focus | Status | DOI |
| ---- | ----- | ----- | ------ | --- |
| 1 | Formal Foundations | Theory, proofs, formalisms | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| **2 (This)** | Computational Validation | Empirical results, algorithms | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| 3 | Practical Guidance | Deployment checklists, guidelines | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

## Project Structure

```text
cogsec_multiagent_2_computational/
├── manuscript/           # Paper content (23 files)
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 01b_related_work.md
│   ├── 02_methodology.md
│   ├── 02a_defense_algorithms.md
│   ├── 02b_configuration_parameters.md
│   ├── 03_attack_corpus.md
│   ├── 03b_attack_examples.md
│   ├── 03c_attack_ethics.md
│   ├── 04_experimental_setup.md
│   ├── 05_results.md
│   ├── 05b_statistical_significance.md
│   ├── 05c_sensitivity_analysis.md
│   ├── 05d_ablation_and_scalability.md
│   ├── 06_discussion.md
│   ├── 07_conclusion.md
│   ├── S01–S06 supplementary sections
│   └── references.bib
├── docs/                 # Technical documentation
│   ├── claims_traceability.md
│   ├── framework_validation.md
│   └── usage_guides/     # Per-component guides
│       ├── 01_cognitive_firewall.md
│       ├── 02_belief_sandbox.md
│       ├── 03_trust_calculus.md
│       ├── 04_byzantine_consensus.md
│       ├── 05_identity_tripwires.md
│       ├── 06_drift_detection.md
│       ├── 07_provenance_tracking.md
│       └── 08_invariant_monitoring.md
├── src/core/             # Defense mechanism implementations
│   ├── firewall.py, sandbox.py, trust.py
│   ├── consensus.py, tripwire.py, detection.py
│   ├── provenance.py, invariants.py
│   └── batch_detection.py, online_detection.py
├── scripts/              # Evaluation and figure scripts
├── tests/                # 90%+ coverage test suite
└── output/               # Generated figures, PDFs, slides
```

## Citation

```bibtex
@article{friedman2026cogsec_computational,
  author = {Friedman, Daniel Ari},
  title = {Cognitive Integrity Framework: Computational Validation Across Production Architectures},
  year = {2026},
  doi = {10.5281/zenodo.18364128},
  publisher = {Zenodo},
  note = {Part 2 of Cognitive Security for Multiagent Operators series}
}
```

## Usage

```bash
# Run full test suite (90%+ coverage required)
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Run formal validation (7 theorems)
uv run python scripts/run_formal_validation.py --seed 42

# Run full evaluation matrix (950 attacks x 6 architectures)
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

## Documentation

Comprehensive technical documentation is available in [`docs/`](docs/):

- [Claims Traceability](docs/claims_traceability.md) — Maps every manuscript claim to its code implementation and test
- [Framework Validation](docs/framework_validation.md) — How to reproduce all experiments (seed=42)
- [Usage Guides](docs/usage_guides/) — Per-component guides with code examples for Firewall, Sandbox, Trust, Consensus, Tripwires, Drift Detection, Provenance, and Invariant Monitoring

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Notation

All notation follows the canonical definitions in Paper 1 (`cogsec_multiagent_1_theory/manuscript/S03_notation.md`).
