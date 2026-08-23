# Cognitive Integrity Program - Agent Reference

Program directory containing the Cognitive Security for Multiagent Operators research series.

## Location and discovery

- **Path:** `cognitive_integrity/` repo root; in template checkouts typically `projects/working/cognitive_integrity/` (sidecar symlink) or `projects/cognitive_integrity/`.
- **Pipeline / PDF:** use qualified names: `cognitive_integrity/cogsec_multiagent_<part>`.
- **Resolution:** `infrastructure.project.discovery.resolve_project_root` prefers `projects/<name>` then `projects_in_progress/<name>`; nested segments must appear in `--project` (e.g. `cognitive_integrity/cogsec_multiagent_2_computational`).

## Projects

| Project | Description | DOI |
| ------- | ----------- | --- |
| `cogsec_multiagent_1_theory/` | Part 1 v2: Theoretical foundations — trust calculus, defense composition algebra, adversary taxonomy, CIF-AD-OODA | 10.5281/zenodo.18364119 |
| `cogsec_multiagent_2_computational/` | Part 2 v2: Computational validation — 950-attack corpus, adversarial training, red-teaming, colony detection benchmarks at 20--100 agents plus no-error stress runs at 100--500 | 10.5281/zenodo.18364128 |
| `cogsec_multiagent_3_practical/` | Part 3+4 merged: Practical guidance + cross-domain CIF-AD-OODA applications | 10.5281/zenodo.18364130 |

## Series overview

The Cognitive Integrity Framework (CIF) provides defense-in-depth security for multiagent AI systems through:

- **Trust Calculus**: Bounded delegation with provable decay
- **Cognitive Firewall**: Multi-stage input classification
- **Belief Sandbox**: Verified/provisional partitioning
- **Byzantine Consensus**: Fault-tolerant agreement
- **Tripwire / Drift Detection**: Canary belief monitoring, KL-divergence surveillance
- **Provenance Tracking**: Information flow with taint labels

Part 3+4 additionally contributes four novel defense extensions: verification channel separation, active perturbation probing, physics-informed invariants, and semiotic decoupling (the fourth is the type-theoretic PassiveData/ExecutableDirective separation introduced in the drone-wars domain).

## Cross-paper reading guide

Each paper stands alone; the bridge is:

- **Formal definitions** live in Part 1 (Trust Calculus, Defense Composition Algebra, Adversary Taxonomy)
- **Empirical evidence** lives in Part 2 (Results, Ablations, parametric analysis — see that manuscript for architecture counts and ceiling definitions)
- **Engineering guidance + domain applications** live in Part 3+4 (merged): Deployment, Incident Response, Monitoring, Cost-Benefit, ten-domain CIF-AD-OODA analyses, universal attack patterns, incident retrospective

## Evidence and implementation spine

- [`cogsec_multiagent_2_computational/docs/claims_traceability.md`](cogsec_multiagent_2_computational/docs/claims_traceability.md)
- [`cogsec_multiagent_2_computational/docs/framework_validation.md`](cogsec_multiagent_2_computational/docs/framework_validation.md)

## Series-level integrity gate

Every other check in this repository is scoped to one part: each part runs its own
`pytest` and its own `verify_manuscript.py`, and Part 2 runs its claim registry over its own
manuscript. Nothing compared the three papers to each other, which is how a shared quantity
came to be published as two different numbers in two papers that cite each other.

```bash
# the gating set — this is what CI runs and what must exit 0
python3 scripts/check_series_integrity.py \
  --only shared-quantities --only bibliography --only truncation \
  --only math-hygiene --only artifact-provenance

python3 scripts/check_series_integrity.py            # adds the advisory pointer lint,
                                                     # so a bare run exits 1 by design
python3 scripts/check_series_integrity.py --json     # machine-readable
```

Stdlib-only, no build step. Four checks:

| Check | What it refuses to let through |
| ----- | ------------------------------ |
| `shared-quantities` | A number that appears in more than one paper disagreeing with itself, or with the Part 2 artifact it is derived from |
| `bibliography` | The same work entered twice under two bibkeys, or the same work disagreeing about its own metadata across the three bibliographies |
| `truncation` | A manuscript file ending mid-sentence, or a heading whose section body never arrives |
| `math-hygiene` | LaTeX that builds but renders wrong: a doubled backslash before a command name, or a `*` where a subscript `_` was meant. Parts 1 and 3 each check this in their own verifier; Part 2 had no such gate |
| `artifact-provenance` | A manuscript citing a data artifact that does not positively declare where it came from. `src/data/generate.py` forbids its placeholders from backing manuscript tables; the rule was unenforced until a scaling table was found built on one |
| `cross-paper-pointers` | Hardcoded `Part 1, Theorem 3.2a`-style pointers, which the renderer numbers per part and which therefore cannot be verified from a sibling paper (advisory) |
### The series ledger

`scripts/series_ledger.py` is the single source of truth for every number the papers share.
Each variable binds a name to a *deriver* that recomputes the value from a shipped artifact
under Part 2's `output/data/`; nothing in it stores a number.

```bash
python3 scripts/series_ledger.py             # every derived value
python3 scripts/series_ledger.py --coverage  # how much of the prose is managed
```

Part 2 already ran derive-then-verify on its own manuscript (`injector.py` writes measured
values in, `claim_registry.py` reads them back and re-derives). Parts 1 and 3 had neither, so
every number they quoted from Part 2 was typed by hand. The ledger closes that: the
`shared-quantities` check gates every ledger variable across all three manuscripts, and a
stated number that disagrees with its artifact fails the build.

The series test count is derived too. It was typed by hand three times and stale three times
(2,283, then 3,308, then 3,369), because it changes whenever anyone adds a test.
`scripts/collect_test_inventory.py` records the real counts into
`test_inventory.json`; `--check` recollects and fails if the recorded numbers have moved, so
a commit that adds tests without refreshing the inventory is caught rather than left to rot
in an abstract. It counts *collected* tests rather than passes, because collection is
deterministic and side-effect free while a pass count depends on the environment a given run
happened to have.

The matching write path is `scripts/inject_series_values.py`: it rewrites any governed site
whose number has drifted from its artifact, reusing the ledger's own patterns so the two
mechanisms cannot disagree about where a number lives. Reporting is the default; `--write`
applies. It refuses to run at all if any variable fails to derive, because injecting a subset
would leave some numbers sourced from the artifacts and some not.

```bash
python3 scripts/inject_series_values.py           # report drift, change nothing
python3 scripts/inject_series_values.py --write   # rewrite from the artifacts
```

Two variables are derived structurally rather than from an artifact: the applied-domain count
is obtained by counting Part 3's `09c..09l` section files, and the ablation denominator is
recovered from the measurement resolution (with an n-sample corpus every delta is a multiple
of 1/n, so the smallest non-zero delta *is* 1/n). Neither is typed anywhere.


Every check fails on an empty input set: a pattern that matches nothing is a broken guard,
not a clean run. `tests/test_series_integrity.py` drives each check against a planted defect
and requires it to be caught.

## Repository

- GitHub: <https://github.com/docxology/cognitive_integrity>
- DOIs: 10.5281/zenodo.18364119, .18364128, .18364130 (Parts 3+4 merged under .18364130)

## Navigation

Each project follows the standalone paradigm with:

- `manuscript/` — Paper content
- `src/` — Source implementations
- `scripts/` — Entry point scripts
- `tests/` — Test suites
- `docs/` — Technical documentation (Paper 2 has usage guides and claims traceability)
- `output/` — Generated artifacts (figures, PDFs, slides)

## Artifacts and ignores

- Each part’s generated PDFs, figures, and reports live under that part’s `output/` and (after `05_copy_outputs.py`) under `output/cognitive_integrity/<part>/`. Program-level [`.gitignore`](.gitignore) ignores `**/output/`, cache dirs, and `**/manuscript_verification.log`.

## Build / test (from repo root)

**When nested inside `docxology/template`** (`./run.sh` and `scripts/` present at that repo's root):

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -q
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -q
```

Run one part at a time if you need to isolate failures. Part 2 imports `scipy` (see that part’s `pyproject.toml`); if imports fail, `uv sync` from the **repository root** first, or sync that part’s environment as described in the program [README](README.md).

**In a standalone checkout** (no `run.sh` at this root), there is no repo-root entry point — build/test each part from its own directory instead: `uv sync && uv run pytest tests/ -q && uv run ruff check .`, plus `make all` in `cogsec_multiagent_2_computational/` for the full data/figures/tables/verify pipeline, or `uv run python scripts/verify_manuscript.py --root manuscript` in Parts 1/3. See the program [README](README.md) § Building.
