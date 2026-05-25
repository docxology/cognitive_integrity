# Cognitive Integrity Framework: Formal Foundations (Part 1)

Part 1 of the **Cognitive Security for Multiagent Operators** series.

**Status: Published** | **DOI:** [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) | **Published:** January 28, 2026

## Overview

This paper presents the **theoretical foundations** of the Cognitive Integrity Framework (CIF) for securing multiagent AI operators against cognitive manipulation attacks.

**Prerequisites:** Comfort with formal notation and security definitions; for empirical and implementation detail, read [Part 2](../cogsec_multiagent_2_computational/) ([claims traceability](../cogsec_multiagent_2_computational/docs/claims_traceability.md)).

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
| 4 | [Applications](../cogsec_multiagent_4_applications/) | Ten-domain CIF-AD-OODA, goal hijacking | Preprint | _DOI pending_ |

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
├── src/                  # CIF reference implementations + visualization helpers
├── scripts/              # Figure and data scripts
├── tests/                # Module and visualization tests
└── output/               # Generated PDF, figures, reports
```

## Notation Reference

The **canonical notation** for the entire paper series is defined in:

- `manuscript/S03_notation.md`

Parts 2 and 3 point here for full symbol definitions (Part 3 also ships a short `S01_notation_reference.md` for readers who stay in the operator paper).

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

From the **template repository root**, use the qualified project name (see [`../README.md`](../README.md) — Location):

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
# or
uv run python scripts/03_render_pdf.py --project cognitive_integrity/cogsec_multiagent_1_theory

uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/ -v
# or: ./run.sh --project cognitive_integrity/cogsec_multiagent_1_theory --project-tests
```
