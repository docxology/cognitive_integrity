# .github/workflows/ — Agent Notes

Single workflow `ci.yml` running each of the three standalone parts
independently. Gating: pinned ruff lint, tests with a coverage floor, an
import sweep over the tracked tree, and manuscript verification for part 2.
Advisory (continue-on-error — four steps): `ruff format --check`, mypy, the
Python 3.10 compatibility matrix, and the cross-paper pointer lint.
