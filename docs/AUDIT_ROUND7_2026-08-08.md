# COGDOCS Lane Audit — Round 7 (2026-08-08)

Lane: **cogdocs** — program docs (`docs/README.md`, `docs/deep_audit_improvements.md`,
`docs/THERMO_NUCLEAR_AUDIT_2026-07-22.md`), program `README.md`, `CITATION.cff`.
Scope per lane brief: documentation map completeness, README series-table accuracy,
CITATION.cff schema validity, round ledger, thermo-nuclear audit staleness.
Sibling paper subtrees read only; no edits to AGENTS.md or TODO_DEEP_SCOPING.md.

## Findings

| ID | Severity | File:line (pre-fix) | What / Why | Status |
|----|----------|---------------------|------------|--------|
| CD-1 | MEDIUM | docs/README.md:18-24 | Documentation map incomplete: the `docs/audits/` directories of all three parts (Part 1 `AUDIT_TODO_2026-07-13.md`, Part 2 `AUDIT_2026-07-26.md` + index + TODO files, Part 3 empty dir) were unmapped. | implemented |
| CD-2 | MINOR | docs/README.md:20 | deep_audit_improvements.md description said "2026-08-03 to 2026-08-05"; Round 7 (2026-08-08) extends the ledger's coverage. | implemented |
| CD-3 | MINOR | docs/README.md:18-24 | `TODO_DEEP_SCOPING.md` (program scoping backlog) not present in the program documentation map, though the ledger links it. | implemented |
| CD-4 | MAJOR | CITATION.cff:16-20 | `preferred-citation` missing required `authors` — `cffconvert --validate` fails with " 'authors' is a required property" (exit 1). Round 3's claim of schema-validity did not hold. | implemented |
| CD-5 | MEDIUM | README.md:17-18,25-27 | Series-table/reading-order labels inconsistent with the release plan: row labels "1 v2"/"2 v2" contradicted actual versions (Part 1 = v1.1, Part 2 = v1.0); Part 1 status cell was a bare version ("**v1.1**") while Parts 2/3 said "Preprint" with no version; the release plan (Part 1 improved release; Parts 2/3 first releases) was implicit. | implemented |
| CD-6 | MINOR | README.md:72, CITATION.cff:18,24 | Three title variants for Part 1 across docs: bibtex/CFF "…for Securing Multiagent AI Operators", manuscript config/part README "Formal Foundations", live Zenodo v1 record "…for Multiagent Security". Aligned CFF + README bibtex to the manuscript title; the live-record divergence is an author decision (see Deferred). | implemented (partial) / scoped |
| CD-7 | MEDIUM | CITATION.cff:17,26,33,40 | `type: software` on all citation entries contradicted the live Zenodo record (resource_type=publication for 10.5281/zenodo.18364119) and the README `@article` bibtex. Changed to `article` (Part 1) and `preprint` (Parts 2/3, status Preprint); "publication" is not a valid CFF 1.2.0 type. | implemented |
| CD-8 | MINOR | CITATION.cff:40 | Part 3 reference title "…(Parts 3+4 Unified)" diverged from the part's own title "…(Parts 3 + 4, Unified)". | implemented |
| CD-9 | INFO | CITATION.cff:31-35,38-43 | Part 2/3 DOIs (10.5281/zenodo.18364128, .18364130) return 404 from Zenodo API — reserved, not yet public; consistent with first-release preprints. No change; re-verify at release. | scoped |
| CD-10 | MEDIUM | docs/deep_audit_improvements.md:81 | Ledger skipped Round 6 ("4-tab fleet additions", 2026-08-05) though TODO_DEEP_SCOPING.md documents it. Added entry sourced from the orchestrator's own text (no invented numbers). | implemented |
| CD-11 | MINOR | docs/THERMO_NUCLEAR_AUDIT_2026-07-22.md:73-75 | Two "Doc / signpost drift" findings (SKILL.md → nonexistent scripts) are resolved in current state but the audit records no resolution; file-size table needed a currency check. | implemented |
| CD-12 | INFO | docs/THERMO_NUCLEAR_AUDIT_2026-07-22.md:58-68 | Verified file-size table still approximately current (7 files, +0.2–1.4% growth); S1 forked-core still present; shared `cif_core` still deferred. | cleared |

## Gate outcomes (real runs, 2026-08-08)

- Link check over owned markdown (relative links; external URLs exempt): before fix 0
  broken relative links (the lane script's 7 "BROKEN" hits were false positives on
  `https://`/`http://` links — it resolves scheme URLs against the filesystem).
  After fix: 0 broken relative links across all 4 owned markdown files.
- `uvx cffconvert --validate --infile CITATION.cff`: **FAIL before** (exit 1,
  "preferred-citation: 'authors' is a required property") → **PASS after** (see
  below, re-run).
- Zenodo API checks (real HTTP): 10.5281/zenodo.18364119 → v1, publication,
  2026-01-28; 18364128/18364130 → 404 (not yet public).
- File/link existence verified with `ls` against the live mirror (byte-identical to
  the real repo before edits).

## Implemented (this lane)

1. **CITATION.cff**: added `authors` to `preferred-citation`; changed citation types
   to `article` (Part 1) / `preprint` (Parts 2/3); aligned Part 1 titles to the
   manuscript title; aligned Part 3 title spacing. Schema-valid per cffconvert.
2. **docs/README.md**: mapped all three `docs/audits/` dirs (incl. Part 2's audits
   index), added `TODO_DEEP_SCOPING.md` row, extended the ledger date range,
   refined the per-part audit-report lines.
3. **README.md (root)**: replaced ambiguous "1 v2"/"2 v2" row labels with
   "(Second Edition)" markers; status column now carries version + release stage
   (v1.1 improved release / Preprint v1.0); added an explicit release-plan sentence;
   aligned the example bibtex title with the manuscript title.
4. **docs/deep_audit_improvements.md**: added Round 6 entry (orchestrator-sourced)
   and the Round 7 (2026-08-08) placeholder pointing to per-part AUDIT files;
   clarified round numbering note.
5. **docs/THERMO_NUCLEAR_AUDIT_2026-07-22.md**: appended dated status check with
   verified current-state facts (resolved SKILL.md findings, file-size table
   currency, S1/deferred state, test-count growth, path note).

## Additions

- `docs/AUDIT_ROUND7_2026-08-08.md` (this file).
- Round 7 section in the round ledger; Round 6 section restored from orchestrator
  source.

## Deferred (acceptance criteria)

- **Canonical Part 1 title (author decision):** three variants exist (manuscript
  "Cognitive Integrity Framework: Formal Foundations", README/CFF legacy
  "…for Securing Multiagent AI Operators", live Zenodo v1 record "…for Multiagent
  Security"). CFF/bibtex now match the manuscript. ACCEPT when the v1.1 Zenodo
  deposition title matches the manuscript title (or the author picks another
  canonical title and docs/CFF/bibtex are re-aligned).
- **Part 2/3 DOIs not yet public:** reserved (404 today). ACCEPT when
  `zenodo.org/api/records/<doi>` returns 200 with the expected title/version;
  re-run `cffconvert --validate` after any CFF change.
- **README bibtex note ("see Zenodo for each part's record")** remains the
  guardrail for citation details until the improved-release records are live.
