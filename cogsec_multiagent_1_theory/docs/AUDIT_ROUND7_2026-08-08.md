# Round 7 Deep Review — Part 1 Theory

Date: 2026-08-08
Subtree: `cogsec_multiagent_1_theory`
Review mode: hostile correctness, reproducibility, manuscript-integrity, figure-honesty, and test-quality pass.

## Findings

| ID | Severity | Evidence | Finding | Status |
|---|---|---|---|---|
| F1 | MAJOR | `manuscript/S02_eusocial_cogsec.md` (13 bare `{#eq:...}` lines); `output/pdf/_combined_manuscript.log` (`13` fatal `!` diagnostics) | Equation identifiers were written as standalone Pandoc attribute lines. The source-to-LaTeX path leaves these as literal `#` text and breaks the generated PDF. | implemented in source; PDF regeneration deferred to the owning render pipeline |
| F2 | MAJOR | `manuscript/04_formal_framework.md`, `08_discussion.md`, `S02_eusocial_cogsec.md` (97 malformed `*` subscript patterns before remediation) | A literal `*` had replaced `_` in math expressions (`\\mathcal{T}*{...}`, `\\sum*{...}`, etc.). Pandoc accepts this syntactically but renders the mathematics incorrectly. | implemented; added verifier guard |
| F3 | MAJOR | duplicate `cor:layered-defense` and `sec:limitations` labels | Duplicate labels silently make LaTeX resolve cross-references to the last definition. | implemented: `cor:n-layer-bound` and `sec:formal-limitations`; boundary-condition references retained as `sec:limitations` |
| F4 | MEDIUM | `manuscript/S01_proofs.md:5,26-45` | The supplement introduction overstated completeness (“complete formal proofs for all theorems”), while its own status section deferred several theorem/corollary proofs. | implemented: proof-status boundary and expanded deferred catalog; no new proofs authored |
| F5 | MEDIUM | `src/visualization/ablation_study.py:14-16,135`, `fp_mitigation.py:15,179`, `trust_decay.py:23-27,171` | Schematic/hardcoded values were not uniformly marked in the code and rendered figures. This is a scientific-honesty risk even where the manuscript captions qualify the figures. | implemented: docstring disclosures, visible figure footers, and guard tests |
| F6 | MAJOR | `src/verification.py:87-161,231-241,336-337` | The manuscript verifier checked citations and references but did not catch bare Pandoc equation attributes, math subscript corruption, double-escaped LaTeX controls, or duplicate labels. | implemented; both positive and negative no-mock tests added |
| F7 | MINOR | `README.md` test inventory; `scripts/README.md` figure table | Documentation omitted current test totals and the two newest figure scripts. | implemented |
| F8 | MINOR | `src/visualization/comprehensive_taxonomy.py:77-136`; `src/visualization/cif_comprehensive.py:124-139` | Several Unicode glyphs generated font-missing warnings in Matplotlib. | implemented: mathtext/ASCII-safe figure labels; targeted visualization tests are warning-free |
| F9 | MINOR | `pyproject.toml:23-28` and documented `uv sync` gate | Test dependencies are optional (`dev` extra), so plain `uv sync` leaves `python -m pytest` unavailable in a clean environment. | scoped: gate invocation should use `uv sync --extra dev`; no dependency-model change made |
| F10 | MEDIUM | `output/pdf/_combined_manuscript.log` | The checked-in/generated PDF surface predates the source fixes and still records 13 LaTeX errors and 2 overfull-box warnings. | scoped: regenerate through the owning manuscript/render pipeline before release; no hand-edit to generated output |

## Implemented changes

- Converted all 13 standalone S02 equation attributes to in-equation `\\label{...}` declarations.
- Corrected 97 malformed mathematical subscript/control-sequence instances across the affected manuscript files, including the missed `Q_\\alpha` case and two double-escaped controls.
- Removed duplicate labels and repaired the discussion cross-reference split between formal limitations and boundary conditions.
- Reframed S01 as a partial proof supplement and expanded its deferred theorem/corollary catalog without attempting author-math proofs.
- Added `check_pandoc_attributes()`, `check_math_hygiene()`, and duplicate-label detection to `src/verification.py`; added both sides of each guard in `tests/test_verification.py`.
- Added figure-honesty disclosures and visible footers to the ablation, false-positive mitigation, and trust-decay generators; added source/docstring guard tests.
- Replaced warning-producing Unicode figure labels with Matplotlib mathtext or ASCII-safe symbols.
- Updated README test counts and script inventory.

## Verification evidence

Fresh mirror run after `uv sync --extra dev`:

- Tests: **420 passed**, 0 failed.
- Ruff: **pass** (`uv run ruff check .`).
- Manuscript verifier: **all checks pass**, including the new Pandoc Attributes and Math Hygiene checks; 102 bibliography entries found.
- Coverage: **97.71%** (`3143` statements, `72` missed), above the configured 90% floor.
- Targeted visualization/verifier run before the final two figure-honesty additions: **67 passed**; the final full suite collected and passed **420** tests.
- The final full run was performed with the project environment after installing the declared `dev` extra. Plain `uv sync` alone does not install pytest in this project.

The pre-fix baseline recorded by the mission was 409 tests / 97.68%; an intermediate run after the first source changes collected 418 tests. The exact final numbers above are the authoritative post-fix results.

## Deferred items and acceptance criteria

1. **Regenerate the PDF through the canonical render pipeline (F10).** Acceptance: generated `_combined_manuscript.log` contains zero lines beginning with `!`, zero emergency stops/undefined-control-sequence diagnostics, and the corrected S02 equations appear in extracted PDF text. Do not hand-edit `output/`.
2. **Author-math items remain deferred.** This review did not prove the defense-independence re-derivation, closed-semiring axiom result, Fisher–Rao inequality, KL-AUC direction/table, or the other author-owned theorem decisions listed in `lane_part1.md`. Acceptance: author supplies or explicitly scopes proofs and updates the claim/proof catalog before asserting those results as proved.
3. **Cross-paper notation review remains observational.** Part 1 source and canonical S03 notation were reviewed; sibling-lane files were not modified. Acceptance: the orchestrator reconciles any Part 2/3 notation drift during the program-level pass.
4. **Clean-release artifact gate.** After render regeneration, rerun the four Part 1 commands in the lane brief with `uv sync --extra dev`, then verify PDF metadata/text and the final output hashes before publication.

## Files changed in this lane

- `manuscript/S02_eusocial_cogsec.md`
- `manuscript/04_formal_framework.md`
- `manuscript/05_defense_mechanisms.md`
- `manuscript/07_formal_verification.md`
- `manuscript/08_discussion.md`
- `manuscript/S01_proofs.md`
- `src/verification.py`
- `src/visualization/ablation_study.py`
- `src/visualization/fp_mitigation.py`
- `src/visualization/trust_decay.py`
- `src/visualization/comprehensive_taxonomy.py`
- `src/visualization/cif_comprehensive.py`
- `tests/test_verification.py`
- `tests/test_visualization.py`
- `README.md`
- `scripts/README.md`
- `docs/AUDIT_ROUND7_2026-08-08.md`
