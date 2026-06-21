# Manuscript - cognitive_integrity

This directory is a template-format manuscript scaffold for:

**Cognitive Security for Multiagent Operators**

A four-part manuscript series covering theoretical foundations, computational validation, practical deployment guidance, and applied domain analyses for cognitive security in multiagent AI systems.

## File Inventory

- `config.yaml`
- `preamble.md`
- `references.bib`
- `00_abstract.md`
- `01_introduction.md`
- `02_system_context.md`
- `03_methods.md`
- `04_artifacts_and_evidence.md`
- `05_reproducibility.md`
- `06_limitations_and_next_steps.md`
- `S01_source_surface.md`
- `98_symbols_glossary.md`
- `99_references.md`
- `AGENTS.md`
- `README.md`
- `SYNTAX.md`

## Source Surfaces

| Surface | Role |
|---|---|
| `cogsec_multiagent_1_theory/` | Source directory to inspect before turning prose into claims. |
| `cogsec_multiagent_2_computational/` | Source directory to inspect before turning prose into claims. |
| `cogsec_multiagent_3_practical/` | Source directory to inspect before turning prose into claims. |
| `cogsec_multiagent_4_applications/` | Source directory to inspect before turning prose into claims. |

## Verification

From the sibling template checkout, after `link-projects` has synced the sidecar:

```bash
uv run python -m infrastructure.orchestration link-projects
uv run python -m infrastructure.validation.cli markdown projects/archive/cognitive_integrity/manuscript/
```

Render only after replacing scaffold prose with project-bound evidence and checking any project-local gates documented in the repository root.
