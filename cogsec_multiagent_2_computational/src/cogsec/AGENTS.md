# src/cogsec/ — Agent Notes

Cogsec-specific testing and benchmark helpers on top of the core defense stack:

- `testing.py` — cogsec test support
- `benchmarks/colony.py` — colony-level benchmarks (delegates to `src/colony/`)

Gotcha: this package name shadows nothing but sits beside `src/core/`, `src/colony/`;
when importing, prefer absolute package imports. Regenerate benchmark numbers via
the evaluation runner, not ad hoc.
