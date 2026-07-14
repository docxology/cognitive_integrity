# Cognitive Integrity Framework: Formal Foundations (Second Edition)

Part 1 of the **Cognitive Security for Multiagent Operators** series — **v2.0 Revised and Expanded**.

**Status: Published (v1) / v2.0 in preparation** | **DOI:** [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) | **v1 Published:** January 28, 2026 | **v2.0 Date:** July 5, 2026

## Overview

This paper presents the **theoretical foundations** of the Cognitive Integrity Framework (CIF) for securing multiagent AI operators against cognitive manipulation attacks.

**Prerequisites:** Comfort with formal notation and security definitions; for empirical and implementation detail, read [Part 2](../cogsec_multiagent_2_computational/) ([claims traceability](../cogsec_multiagent_2_computational/docs/claims_traceability.md)).

## Primary Contributions (v2.0)

1. **Trust Calculus**: Bounded delegation with δ^d decay preventing trust amplification; blast radius theorem for compromised agents
2. **Defense Composition Algebra**: Formal semiring structure; complete proof of closure, associativity, identity, distributivity
3. **Information-Theoretic Bounds**: Neyman-Pearson optimal detection; Chernoff information error exponents; fundamental undetectability regime
4. **Formal Verification**: Safety properties (belief integrity, trust boundedness, goal alignment)
5. **Formal Ω Adversary Taxonomy** *(v2.0)*: Mathematical characterization of all five adversary classes with KL-divergence distinguishability
6. **CIF-AD-OODA Integration** *(v2.0)*: Action-Delegation coupling matrix (5×5); OODA phase-specific defenses and latency constraints
7. **Information-Geometric Bounds** *(v2.0)*: Fisher-Rao tight bound I·S ≤ π/2; geometric justification of drift threshold θ = 0.3
8. **Limitations and Boundary Conditions** *(v2.0)*: Honest characterization of 5 formal assumptions and where they break

## v2.0 Major Changes

| Component | v1 | v2 |
|---|---|---|
| Adversary taxonomy | Descriptive table | Formal math characterization + distinguishability theorem |
| Formal framework | Trust calculus, belief updates | + CIF-AD coupling theory + OODA state machine integration |
| Defense mechanisms | 5 defenses defined | + Formal semiring closure proofs + CUSUM ARL bounds |
| Detection methods | ROC + ensemble | + Neyman-Pearson, Chernoff bounds, multi-stage pipeline |
| New section | — | §10 Limitations and Boundary Conditions |
| Proofs supplement | 7 theorems | +6 new v2.0 proofs (Fisher-Rao, semiring, blast radius) |
| Source modules | 10 modules | +2: `ooda_monitor.py`, `cif_ad_coupling.py` |
| Test coverage | 12 test files | +2 files: 83 new tests (OODA, CIF-AD, Byzantine stress) |
| Figures | 18 scripts | +2: CIF-AD coupling heatmap, OODA phase diagram |
| Citations | ~100 | +10 new: Fisher-Rao, Neyman-Pearson, CUSUM, FLP, etc. |

## Paper Series

|| Part | Title | Focus | Status | DOI |
||------|-------|-------|--------|-----|
|| **1 (This)** | Formal Foundations (Second Edition) | Theory, proofs, formalisms, CIF-AD-OODA | **v2.0** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
|| 2 | Computational Validation | Empirical results, algorithms | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
|| 3+4 (merged) | Practical Guidance + Applications | Deployment checklists, guidelines, cross-domain CIF-AD-OODA | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

## Project Structure

```
cogsec_multiagent_1_theory/
├── manuscript/           # Paper content (theory-focused)
│   ├── 00_quote.md           # Blake epigraph
│   ├── 01_abstract.md
│   ├── 02_introduction.md
│   ├── 03_threat_model.md    # v2: Formal Ω taxonomy (§adversary-formal)
│   ├── 04_formal_framework.md # v2: CIF-AD + OODA integration (§cif-ad-coupling, §cif-ooda)
│   ├── 05_defense_mechanisms.md # v2: Semiring proofs + CUSUM ARL (§defense-formal-guarantees)
│   ├── 06_detection_methods.md  # v2: NP bounds + multi-stage pipeline (§it-detection-limits)
│   ├── 07_formal_verification.md
│   ├── 08_discussion.md
│   ├── 09_conclusion.md
│   ├── 10_limitations.md     # NEW v2: Boundary conditions §10
│   ├── S01_proofs.md         # v2: +6 new proofs (Fisher-Rao, semiring, blast radius)
│   ├── S02_eusocial_cogsec.md
│   ├── S03_notation.md       # CANONICAL notation reference
│   └── references.bib        # v2: +10 new citations
├── src/                  # CIF reference implementations
│   ├── ooda_monitor.py       # NEW v2: OODA phase monitor
│   ├── cif_ad_coupling.py    # NEW v2: CIF-AD coupling detector
│   ├── trust.py, firewall.py, consensus.py, tripwire.py
│   ├── provenance.py, detection.py, invariants.py, sandbox.py
│   └── visualization/
├── scripts/              # Figure and data scripts
│   ├── 19_cif_ad_coupling_figure.py  # NEW v2
│   ├── 20_ooda_phase_figure.py       # NEW v2
│   └── (01-18 existing scripts)
├── tests/                # Module and visualization tests
│   ├── test_ooda_monitor.py    # NEW v2: 51 tests (incl. Hypothesis property-based)
│   ├── test_cif_ad_coupling.py # NEW v2: 32 tests (incl. Byzantine stress)
│   └── (existing test files)
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

**If this checkout is nested inside `docxology/template`** (i.e. this directory lives at `projects/cognitive_integrity/cogsec_multiagent_1_theory/` under that repo's root), use the qualified project name from the **template repository root** (see [`../README.md`](../README.md) — Location):

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
# or
uv run python scripts/pipeline/stage_03_render.py --project cognitive_integrity/cogsec_multiagent_1_theory

uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/ -v
# or: ./run.sh --project cognitive_integrity/cogsec_multiagent_1_theory --project-tests
```

**In a standalone checkout of this repo** (no `run.sh`/`scripts/pipeline/` at the root — this is the case if you cloned `docxology/cognitive_integrity` directly), the `./run.sh` wrapper above does not exist. Work from this directory instead:

```bash
uv sync
uv run pytest tests/ -q                    # test suite
uv run ruff check .                        # lint
uv run python scripts/verify_manuscript.py --root manuscript   # manuscript integrity checks
uv run python scripts/<NN>_*.py            # generate an individual figure (see scripts/README.md)
```
