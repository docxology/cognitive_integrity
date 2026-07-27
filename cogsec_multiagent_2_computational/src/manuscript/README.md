# `src/manuscript/` — Manuscript Utilities

Tooling for maintaining manuscript integrity in Paper 2 (*Computational Validation*). Provides a verifier for citation / label / figure consistency, a LaTeX-table-to-Markdown converter, and an automated numerical-value injector that keeps manuscript numbers synced with `output/data/`.

## Series Position

Part 2 of three in the *Cognitive Security for Multiagent Operators* series. These utilities produce the manuscript-integrity guarantees that allow sibling papers to cite Paper 2's numbers with confidence.

## Modules

| Module | Purpose | Key Exports |
| ------ | ------- | ----------- |
| `verifier.py` | Checks citations, `\cref` targets, figure references, label uniqueness, style rules | `ManuscriptVerifier` |
| `latex_converter.py` | Converts LaTeX tables in manuscript `.md` files to Markdown pipe tables for readability diffs | `convert_file`, `convert_latex_table_to_markdown` |
| `injector.py` | Auto-injects computed values from `output/data/*.json` into manuscript `.md` files, keeping numbers in sync with regenerated data | `ManuscriptInjector` |

## Quick Usage

```python
from src.manuscript import ManuscriptVerifier, convert_file

# 1. Verify manuscript integrity
verifier = ManuscriptVerifier(manuscript_dir="manuscript")
report = verifier.verify_all()
if report.errors:
    for err in report.errors:
        print(f"[{err.severity}] {err.file}:{err.line} {err.message}")

# 2. Convert a LaTeX-table-heavy file to Markdown tables for easier review
convert_file("manuscript/05_results.md", output="manuscript/05_results.md")
```

## Script Entry Points

Paper 2's [`../../scripts/`](../../scripts/) directory uses these utilities via thin orchestrators:

| Script | Uses |
| ------ | ---- |
| `scripts/verify_manuscript.py` | `ManuscriptVerifier` |
| `scripts/convert_latex_tables.py` | `convert_file` |
| `scripts/z_inject_manuscript_values.py` | `ManuscriptInjector` |

## Manuscript-Integrity Checks

`ManuscriptVerifier.verify_all()` returns a report with the following check categories:

1. **Citations** — every `\cite{key}` resolves against `references.bib`
2. **References** — every `\cref{label}` resolves against defined labels
3. **Figures** — every figure referenced exists in `output/figures/` or `figures/`
4. **Labels** — no duplicate `{#label}` or `\label{}` identifiers
5. **Style** — sanctioned markdown conventions (heading levels, emphasis consistency)
6. **Series Consistency** — citations to `friedman2026cogsecN` resolve for N ∈ {1,2,3,4}

## Design Principles

- No manuscript mutation without explicit `--write` flag (verify is read-only by default).
- Deterministic — same input → same report.
- Graceful degradation — missing optional files warn, don't fail.
- Cross-paper aware — detects Paper 2's citations to siblings and flags broken references.

## Dependencies

- Python standard library only (no LaTeX / pandoc required for verification)
- `bibtexparser` (optional, falls back to regex parsing)
