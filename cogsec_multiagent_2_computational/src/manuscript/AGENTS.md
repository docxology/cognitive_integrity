# `src/manuscript/` — Agent Reference

Guidance for agents modifying the manuscript-utility package.

## Purpose

Tooling for manuscript integrity (verifier, LaTeX-table converter, value injector). See [`README.md`](README.md) for the full module map.

## Rules

- **Read-only by default** — verification never mutates manuscript files without an explicit `--write` or `auto_fix=True` flag.
- **Deterministic** — given the same manuscript state, reports are identical.
- **Cross-paper aware** — verifier must resolve `friedman2026cogsecN` (N=1..4) bibtex keys as valid series cross-references and **not** flag them as broken citations.
- **Paper 3 discipline** — do not accept a `friedman2026cogsec3` note that characterizes Paper 3 as "biological" or "eusocial". That text lives in Paper 1's S02 supplementary. Paper 3 is the practitioner's qualitative review.

## When Editing

- Update [`README.md`](README.md) for public API changes.
- Add tests in `tests/test_manuscript_utils.py` (or create it) using real `.md` fixtures — no mocks.
- Keep the verifier's rule set encoded as first-class `Rule` objects, not hard-coded branches.

## Typical Invocation

```python
from src.manuscript import ManuscriptVerifier
report = ManuscriptVerifier(manuscript_dir="manuscript").verify_all()
assert not report.errors, report.format()
```
