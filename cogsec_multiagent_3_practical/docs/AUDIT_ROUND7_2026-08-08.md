# Round 7 Audit — Part 3 Practical

Date: 2026-08-08
Scope: `cogsec_multiagent_3_practical/`
Mission: hostile review and release hardening of the CIF Practical Applications and Deployment Guide.

## Baseline and release gates

The mirror started from the reported healthy baseline:

- `uv run pytest tests/ -q`: 907 passed.
- `uv run ruff check .`: clean.
- `uv run python scripts/verify_manuscript.py --root manuscript`: 7/7 checks passed.
- `uv run pytest tests/ --cov=src --cov-report=term-missing`: 98.79% total coverage.

After the changes below:

- `uv run pytest tests/ -q`: **925 passed**.
- `uv run ruff check .`: **clean**.
- `uv run python scripts/verify_manuscript.py --root manuscript`: **all checks passed** (files, citations, labels/refs, images/links, style, domain content).
- `uv run pytest tests/ --cov=src --cov-report=term-missing`: **99.94% total coverage** (1651/1652 statements; `src/verification.py` 99.47%).
- `uv run python scripts/01_posture_radar_figure.py` through `07_domain_coverage_figure.py`: all scripts completed and wrote their PNG/PDF artifacts.
- Independent repeated-render probe: all six core visualization renderers and the domain-coverage PNG renderer produced byte-identical output on repeated renders.

No git commands were run. No mocks, `MagicMock`, `unittest.mock`, `mocker.patch`, or `monkeypatch.setattr` were added or used.

## Findings

| ID | Severity | Evidence | Finding and impact | Status |
|---|---|---|---|---|
| R7-P3-01 | MAJOR | `src/deployment.py:161-199`; `manuscript/05_deployment_guide.md:25-49`; Part 2 `manuscript/S08_parametric_analysis.md:270-304` | The executable medium/high deployment profiles used trust-decay deltas `0.90`/`0.85`, while the Part 3 deployment guide declared the balanced/high-assurance profiles as `0.80`/`0.60`. This changes effective delegation depth and is safety-relevant configuration drift: an operator following the paper would not get the implementation represented by the paper. | implemented |
| R7-P3-02 | MAJOR | `src/pitfalls.py:216-221,273-278`; `manuscript/06_common_pitfalls.md` severity table; `tests/test_pitfalls.py` | PIT-5 (Static Tripwires) was coded severity 4 while the manuscript labels it Medium; PIT-8 (Single-Orchestrator Reliance) was coded severity 2 while the manuscript labels it High. Because the checklist maps severity to operational risk and remediation ordering, the mismatch could under-prioritize orchestrator compromise and over-prioritize static tripwires. | implemented |
| R7-P3-03 | MEDIUM | `src/verification.py:247-254` (pre-fix behavior); `tests/test_verification.py` | The manuscript verifier logged broken local links but returned success. This was a hollow-green integrity gate: a missing cross-reference could pass the release check. The branch now sets `link_status = False`, and tests exercise both broken and resolvable local links. | implemented |
| R7-P3-04 | MEDIUM | `manuscript/03_simulation_review.md:90-94` (pre-fix); Part 2 `output/data/ablation_results.json` | The practical guide called the ablation floor `12.4%` over 100 attacks. The authoritative Part 2 result is full-pipeline TPR `0.12244897959183673` on the 98-attack corpus (approximately 12.2%). The prose now says `~12.2%` and `98 attacks`, avoiding a false precision/count claim. | implemented |
| R7-P3-05 | MINOR | `manuscript/S01_notation_reference.md:17,25` (pre-fix); Part 1 notation cross-reference | The Part 3 notation summary described the five adversary classes as passive/injection/spoofing/belief-manipulation/coordinated tiers, which did not match the Part 1 class structure used by the rest of the program. The summary now uses external, peripheral, agent-level, coordination, and systemic/orchestrator descriptions. | implemented |
| R7-P3-06 | MINOR | `manuscript/05_deployment_guide.md:47`; `manuscript/09_applications_intro.md:68`; `manuscript/10b_applications_conclusion.md:15`; `manuscript/10_cross_domain_discussion.md:137` | Additional prose drift was found: the `delta=0.60` half-trust depth was rounded too aggressively; the temporal-scale summary said eight orders while the stated milliseconds-to-years range exceeds ten; and the incident-pattern sentence named only two of the three patterns despite claiming all three were represented. These were corrected to match the stated values and scope. | implemented |
| R7-P3-07 | MINOR | `tests/test_visualization.py` (new Round 7 class); figure scripts `scripts/01..07` | Existing rendering tests checked artists, but did not protect reproducibility against future time/RNG drift. A no-mock repeated-render byte-equality suite was added for six core renderers; the seventh domain renderer was independently probed during this audit. | implemented |

## What was implemented

1. Aligned `DeploymentConfigurator` and `TrustDecayAnalyzer.compare_profiles()` with the deployment guide's declared profile deltas: low `0.95`, medium `0.80`, high `0.60`.
2. Corrected PIT-5/PIT-8 executable severities to match the manuscript's Medium/High operational labels.
3. Made broken local manuscript links fail `check_images_and_links()` rather than only emitting a warning.
4. Added real filesystem tests for absolute paths, parent escapes, `file:` links, broken links, resolvable links, logging setup, and citation-file handling.
5. Added figure determinism tests using real Matplotlib rendering and byte comparisons; no mocks.
6. Added a code-to-manuscript binding test for the three Section 05 profile deltas.
7. Corrected the verified manuscript drift items listed in the findings table.

## Additions and measured improvement

- Tests: 907 -> **925 passed** (+18).
- Coverage: 98.79% -> **99.94%** total.
- Ruff: clean before and after.
- Manuscript verification: 7/7 baseline checks remained green after hardening the link gate.
- Figure generation: all seven scripts executed successfully and wrote the expected artifacts.
- Figure reproducibility: repeated real renders were byte-identical in the independent probe and in the new core-renderer tests.

## Deferred items and acceptance criteria

### D1 — Make the deployment profile table a single generated source of truth (MEDIUM)

The implemented fix aligns current code and prose, but the values still exist in multiple files. Future drift remains possible. Acceptance criteria:

- Define the profile parameters once in an importable data structure or generated artifact.
- Generate or validate the Section 05 profile table from that source.
- Add a test that parses every profile row and compares every safety-relevant field, not only `delta`.
- Preserve the current no-mock and manuscript gates.

### D2 — Resolve author-level semantic ownership of the five adversary classes (MINOR/MEDIUM)

This audit corrected the Part 3 summary to the Part 1 cross-paper vocabulary, but did not alter Part 1's formal taxonomy. Acceptance criteria:

- Author confirms the canonical class names and capability boundaries across Parts 1–3.
- The Part 3 notation table and all `Omega` prose are regenerated from or checked against that canonical definition.
- Any remaining domain-specific use is explicitly labeled as an application mapping rather than a taxonomy definition.

### D3 — Expand manuscript verification to validate section anchors and cross-paper paths (MINOR)

The current verifier now fails broken local links, but Markdown heading-anchor semantics and cross-paper relative references are not fully modeled by the script. Acceptance criteria:

- Add a resolver for local heading anchors and cross-paper paths.
- Add fixtures for valid anchors, missing anchors, and nested relative paths.
- Keep the existing real-manuscript 7-check gate green.

### D4 — Audit remaining quantitative prose against a machine-readable evidence ledger (MEDIUM)

This pass corrected the verified ablation-count/rate drift and several consistency statements. It did not claim that every historical number in the manuscript has been independently regenerated. Acceptance criteria:

- Enumerate every measured number in the Part 3 manuscript that cites Part 2.
- Bind each to a concrete Part 2 JSON artifact or explicitly label it illustrative/design-level.
- Run the ledger check in the release gate and report unresolved values rather than silently accepting them.

## Epistemic status

The implemented findings are verified against the mirror's source, tests, manuscript files, and the real Part 2 `ablation_results.json` artifact read during the review. The complete Part 3 test, lint, manuscript, coverage, and figure-script gates were rerun after modification. I did not run a full three-paper build or regenerate committed Part 2 data, and the deferred items above remain unverified by design.
