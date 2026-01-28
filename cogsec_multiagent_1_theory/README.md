# Cognitive Integrity Framework: Formal Foundations (Paper 1)

Part 1 of the **Cognitive Security for Multiagent Operators** series.

## Overview

This paper presents the **theoretical foundations** of the Cognitive Integrity Framework (CIF) for securing multiagent AI operators against cognitive manipulation attacks.

## Primary Contributions

1. **Trust Calculus**: Bounded delegation with $\delta^d$ decay preventing trust amplification
2. **Defense Composition Algebra**: Formal reasoning about layered security
3. **Information-Theoretic Bounds**: Detection limits under stealth constraints
4. **Formal Verification**: Safety properties (belief integrity, trust boundedness, goal alignment)

## Paper Series

| Part | Title | Focus |
|------|-------|-------|
| **1 (This)** | Formal Foundations | Theory, proofs, formalisms |
| 2 | Computational Validation | Empirical results, algorithms |
| 3 | Practical Guidance | Deployment checklists, guidelines |

## Project Structure

```
cogsec_multiagent_1_theory/
├── manuscript/           # Paper content (theory-focused)
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_threat_model.md
│   ├── 03_formal_framework.md
│   ├── 04_defense_mechanisms.md
│   ├── 05_detection_methods.md
│   ├── 06_formal_verification.md
│   ├── 08_discussion.md
│   ├── 09_conclusion.md
│   ├── S03_proofs.md         # Mathematical proofs
│   ├── S05_eusocial_cogsec.md # Colony cognitive security
│   ├── S06_notation.md       # CANONICAL notation reference
│   └── references.bib
├── src/                  # Minimal type definitions
├── tests/                # Basic validation
└── output/               # Generated PDF
```

## Notation Reference

The **canonical notation** for the entire paper series is defined in:

- `manuscript/S06_notation.md`

Papers 2 and 3 reference this document for all symbol definitions.

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.16903352](https://doi.org/10.5281/zenodo.16903352)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Usage

```bash
# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_1_theory

# Run tests
./run.sh --project cogsec_multiagent_1_theory --run-tests
```
