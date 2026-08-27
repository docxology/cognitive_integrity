# Part 1 — Formal Foundations (Theory): Documentation

Documentation index for **Part 1** of *Cognitive Security for Multiagent
Operators* — the formal/theoretical part (trust calculus, defense composition
algebra, information-theoretic detection bounds, formal Ω adversary taxonomy,
CIF-AD-OODA integration).

## Documentation map

| Entry | Role |
| ----- | ---- |
| [`../README.md`](../README.md) | Onboarding, contributions (v1 → v2.0), series map |
| [`../AGENTS.md`](../AGENTS.md) | Agent reference: structure, verification, invariants |
| [`../PAI.md`](../PAI.md) | Paper authoring instructions |
| [`../SKILL.md`](../SKILL.md) | Agent skills for this exemplar |
| **`README.md` (this file)** | Documentation index |
| [`../manuscript/`](../manuscript/) | The paper content (markdown sections + preamble) |
| [`../src/`](../src/) | Source modules (trust calculus, OODA monitor, CIF-AD coupling, etc.) |
| [`../scripts/`](../scripts/) | Figure-generation scripts |

## Manuscript structure

| File | Section |
| ---- | ------- |
| [`../manuscript/00_quote.md`](../manuscript/00_quote.md) | Epigraph |
| [`../manuscript/01_abstract.md`](../manuscript/01_abstract.md) | Abstract |
| [`../manuscript/02_introduction.md`](../manuscript/02_introduction.md) | Introduction |
| [`../manuscript/03_threat_model.md`](../manuscript/03_threat_model.md) | Adversary taxonomy & attack surface (§Ω1–Ω5) + threat-model figures |
| [`../manuscript/04_formal_framework.md`](../manuscript/04_formal_framework.md) | Formal framework: trust calculus, belief updates |
| [`../manuscript/05_defense_mechanisms.md`](../manuscript/05_defense_mechanisms.md) | Defense mechanisms (5 defenses, composition algebra) |
| [`../manuscript/06_detection_methods.md`](../manuscript/06_detection_methods.md) | Detection methods (Neyman–Pearson, CUSUM, ensemble) |
| [`../manuscript/07_formal_verification.md`](../manuscript/07_formal_verification.md) | Formal verification (safety properties) |
| [`../manuscript/08_discussion.md`](../manuscript/08_discussion.md) | Discussion |
| [`../manuscript/09_conclusion.md`](../manuscript/09_conclusion.md) | Conclusion |
| [`../manuscript/10_limitations.md`](../manuscript/10_limitations.md) | Limitations and boundary conditions (v2.0) |
| [`../manuscript/S01_proofs.md`](../manuscript/S01_proofs.md) | Proofs supplement |
| [`../manuscript/S02_eusocial_cogsec.md`](../manuscript/S02_eusocial_cogsec.md) | Eusocial/cogsec supplement |
| [`../manuscript/S03_notation.md`](../manuscript/S03_notation.md) | Notation index |
| [`../manuscript/99_references.md`](../manuscript/99_references.md) | References |

## Figures

`scripts/*_figure.py` generates the manuscript figures (threat taxonomy, attack
surface, trust decay, defense composition, ROC curves, belief sandbox, detection
performance, false-positive mitigation, ablation study, CIF-AD coupling heatmap,
OODA phase diagram, and more) into `output/figures/`. Every figure is embedded
in the manuscript with an accurate caption and a `{#fig:...}` label; the figure
registry is maintained by
[`scripts/generate_figure_registry.py`](../scripts/generate_figure_registry.py).

```bash
# Example
uv run python scripts/05_threat_taxonomy_figure.py
```

## Source modules

See [`../src/`](../src/) and [`../README.md`](../README.md) §Source modules for
the module list (10 base modules + `ooda_monitor.py`, `cif_ad_coupling.py`).

## Verification and tests

```bash
# Tests (Part 1 suite)
uv run pytest tests/ -q

# Lint
uv run ruff check src scripts tests
```

## Historical audit reports

| Entry | Role |
| ----- | ---- |

See [`../README.md`](../README.md) and the program
[`docs/README.md`](../../docs/README.md) for the cross-paper reading guide and
how to render this paper as PDF from the template repo.
