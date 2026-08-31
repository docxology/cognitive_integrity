# manuscript/ — Agent Notes

Part 1 manuscript source: 12 numbered section files (quote → references),
preamble.md, config.yaml, references.bib, plus three appendices
(`S01_proofs.md`, `S02_eusocial_cogsec.md`, `S03_notation.md`).

- Verify: `uv run python scripts/verify_manuscript.py --root manuscript`
  (standalone checkout) — see `AGENTS.md` at part root for pipeline vs standalone.
- config.yaml owns paper metadata; numbers must trace to
  `output/data/` artifacts (program rule — see `../../README.md`).
- Every quantity shared with Parts 2/3 is checked by
  `../../scripts/check_series_integrity.py`.
