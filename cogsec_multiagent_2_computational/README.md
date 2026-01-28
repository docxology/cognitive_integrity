# Cognitive Integrity Framework: Computational Validation (Paper 2)

Part 2 of the **Cognitive Security for Multiagent Operators** series.

## Overview

This paper provides **computational validation** of the Cognitive Integrity Framework (CIF) through implementation, benchmarking, and statistical analysis across production multiagent architectures.

## Primary Focus

- **Implementation**: Defense mechanisms (firewall, sandbox, trust, consensus)
- **Attack Corpus**: 950 attacks across 4 categories
- **Validation**: 6 production architectures (Claude Code, AutoGPT, CrewAI, LangGraph, MetaGPT, Camel)
- **Analysis**: Statistical significance, ablation studies, scalability benchmarks

## Paper Series

| Part | Title | Focus |
| ---- | ----- | ----- |
| 1 | Formal Foundations | Theory, proofs, formalisms |
| **2 (This)** | Computational Validation | Empirical results, algorithms |
| 3 | Practical Guidance | Deployment checklists, guidelines |

## Project Structure

```text
cogsec_multiagent_2_computational/
├── manuscript/           # Paper content
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_methodology.md
│   ├── 03_attack_corpus.md
│   ├── 04_experimental_setup.md
│   ├── 05_results.md
│   ├── 06_discussion.md
│   ├── 07_conclusion.md
│   ├── 99_references.md
│   ├── S01_notation_reference.md
│   ├── S02_detection_algorithms.md
│   ├── S03_benchmark_implementation.md
│   └── S04_model_checking.md
├── scripts/              # 18 figure generation scripts
│   ├── 01_attack_surface_figure.py
│   ├── 02_trust_decay_figure.py
│   └── ...
├── src/                  # Defense mechanism implementations
│   ├── consensus.py
│   ├── detection.py
│   ├── firewall.py
│   ├── invariants.py
│   ├── provenance.py
│   ├── sandbox.py
│   ├── tripwire.py
│   └── trust.py
├── tests/                # 90%+ coverage test suite
│   ├── test_consensus.py
│   ├── test_detection.py
│   └── ...
└── output/               # Generated figures and PDF
```

## Usage

```bash
# Run full test suite (90%+ coverage required)
python3 -m pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ \
    --cov=projects/cognitive_integrity/cogsec_multiagent_2_computational/src \
    --cov-fail-under=90 -v

# Generate figures
./run.sh --project cogsec_multiagent_2_computational --run-analysis

# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_2_computational
```

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.16903352](https://doi.org/10.5281/zenodo.16903352)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Notation

All notation follows the canonical definitions in Paper 1 (`cogsec_multiagent_1_theory/manuscript/S06_notation.md`).
