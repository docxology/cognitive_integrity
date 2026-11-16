# .github/workflows/

CI: `ci.yml` builds/tests all three parts independently on Python 3.11 and 3.15.2.
Mypy gates Part 2 on Python 3.15.2; the series job recollects the test inventory. Format checking and cross-paper pointer lint
are advisory; see AGENTS.md.
