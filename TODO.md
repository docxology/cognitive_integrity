# cognitive_integrity — canonical backlog

Open, owner-local work only. Completed work belongs in `CHANGELOG.md` and Git history.

## Runtime qualification

- [ ] **CI-006 — P2: Qualify the configured Python 3.11 / 3.15.2 matrix.** The workflow now sets exact `3.15.2` as primary, retains the 3.11 floor cell, gates Part 2 mypy on primary, and all Ruff targets are `py311`. Native source and evidence gates have run on Python 3.12.16; this is not evidence that the new target runtimes pass. **Acceptance probe:** all three frozen environments install, tests and lint pass on 3.15.2, and the 3.11 matrix remains covered. Record any exact package/platform installation constraint rather than changing the declared floor or silently substituting an interpreter. Remove this open brief only after actual target-runtime qualification.
