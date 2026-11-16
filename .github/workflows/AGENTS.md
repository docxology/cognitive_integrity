# .github/workflows/ — Agent Notes

Single workflow `ci.yml` running each of the three standalone parts
independently on Python 3.11 and 3.15.2. Gating: pinned ruff lint, tests with a
coverage floor, a tracked-tree import sweep, manuscript verification for all
parts, fresh series test collection, and mypy on Part 2 with Python 3.15.2. Advisory
(`continue-on-error`): `ruff format --check` and the cross-paper pointer lint.
