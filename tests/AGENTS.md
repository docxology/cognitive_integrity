# tests/ — Agent Notes

Tests for the program-level scripts (`check_series_integrity.py`,
`check_conclusion_numbers.py`, `check_unhappened_claims.py`,
`inject_series_values.py`). Two obligations per gate: it reports the defects it
should on the live tree, AND it can fail (every check is also driven against a
synthetic tree with a planted defect and must catch it — anti-vacuity
assertions).

## Verify

```bash
uv run pytest tests/ -q
```

Note: per-part suites live in each `cogsec_multiagent_<part>/tests/` — one
pytest process per project directory (conftest collision if combined).
