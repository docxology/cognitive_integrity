# Cognitive Integrity Framework: Formal Foundations (Paper 1)

Part 1 of the **Cognitive Security for Multiagent Operators** series.

**Status: Published** | **DOI:** [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) | **Published:** January 28, 2026

## Overview

This paper presents the **theoretical foundations** of the Cognitive Integrity Framework (CIF) for securing multiagent AI operators against cognitive manipulation attacks.

## Primary Contributions

1. **Trust Calculus**: Bounded delegation with δ^d decay preventing trust amplification
2. **Defense Composition Algebra**: Formal reasoning about layered security
3. **Information-Theoretic Bounds**: Detection limits under stealth constraints
4. **Formal Verification**: Safety properties (belief integrity, trust boundedness, goal alignment)

## Paper Series

| Part | Title | Focus | Status | DOI |
|------|-------|-------|--------|-----|
| **1 (This)** | Formal Foundations | Theory, proofs, formalisms | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| 2 | Computational Validation | Empirical results, algorithms | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| 3 | Practical Guidance | Deployment checklists, guidelines | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

## Project Structure

```
cogsec_multiagent_1_theory/
├── manuscript/           # Paper content (theory-focused)
│   ├── 00_quote.md           # Blake epigraph
│   ├── 01_abstract.md
│   ├── 02_introduction.md
│   ├── 03_threat_model.md
│   ├── 04_formal_framework.md
│   ├── 05_defense_mechanisms.md
│   ├── 06_detection_methods.md
│   ├── 07_formal_verification.md
│   ├── 08_discussion.md
│   ├── 09_conclusion.md
│   ├── S01_proofs.md         # Mathematical proofs
│   ├── S02_eusocial_cogsec.md # Colony cognitive security
│   ├── S03_notation.md       # CANONICAL notation reference
│   └── references.bib
├── src/                  # Minimal type definitions
├── tests/                # Basic validation
└── output/               # Generated PDF
```

## Notation Reference

The **canonical notation** for the entire paper series is defined in:

- `manuscript/S03_notation.md`

Papers 2 and 3 reference this document for all symbol definitions.

## Citation

```bibtex
@article{friedman2026cogsec_theory,
  author = {Friedman, Daniel Ari},
  title = {Cognitive Integrity Framework: Formal Foundations for Securing Multiagent AI Operators},
  year = {2026},
  doi = {10.5281/zenodo.18364119},
  publisher = {Zenodo},
  note = {Part 1 of Cognitive Security for Multiagent Operators series}
}
```

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Usage

```bash
# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_1_theory

# Run tests
./run.sh --project cogsec_multiagent_1_theory --run-tests
```
