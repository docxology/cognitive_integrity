# .github/

GitHub Actions CI for this repo: `workflows/ci.yml` runs each of the three
standalone parts independently (pinned ruff lint, tests with a coverage floor,
an import sweep over the tracked tree, and manuscript verification for part 2).
Advisory steps (continue-on-error): `ruff format --check`, mypy, the Python 3.10
compatibility matrix, and the cross-paper pointer lint.
