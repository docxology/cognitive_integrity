# .github/ — Agent Notes

Contains `workflows/` (single workflow `ci.yml`). CI runs each of the three
standalone parts independently on Python 3.11 and 3.15.2: pinned ruff lint, tests
with a coverage floor, a tracked-tree import sweep, and manuscript verification
for all parts. Mypy gates Part 2 on Python 3.15.2; series CI recollects every test inventory. Only
`ruff format --check` and the cross-paper pointer lint are advisory.
