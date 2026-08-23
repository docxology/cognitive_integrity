# Cognitive Security for Multiagent Operators

A three-part manuscript series establishing the theoretical foundations, computational validation, and unified practical/applications guidance for cognitive security in multiagent AI systems. Parts 3 and 4 were merged into a single comprehensive paper.

## Location in this repository

This program lives in the **`cognitive_integrity`** git repo. In a template checkout it is usually symlinked at **`projects/working/cognitive_integrity/`** (private sidecar) or nested as **`projects/cognitive_integrity/`**. For `./run.sh` and `scripts/pipeline/stage_03_render.py` inside `docxology/template`, pass the **qualified project name**:

`cognitive_integrity/cogsec_multiagent_<N>_<suffix>`

The qualified name keeps each paper's outputs under `output/cognitive_integrity/<paper>/`.

## Who should start where

| Reader | Start here |
| ------ | ---------- |
| Formal definitions, proofs, adversary taxonomy | [Part 1 (Second Edition): Formal Foundations](cogsec_multiagent_1_theory/) |
| Empirical results, adversarial training, reproducibility | [Part 2 (Second Edition): Computational Validation](cogsec_multiagent_2_computational/) — evidence spine: [claims traceability](cogsec_multiagent_2_computational/docs/claims_traceability.md), [framework validation](cogsec_multiagent_2_computational/docs/framework_validation.md) |
| Deployment, checklists, operator guidance, cross-domain applications (minimal math) | [Part 3+4: Practical Guide + Applications](cogsec_multiagent_3_practical/) |

## Paper Series

| Part | Title | Status | DOI |
|------|-------|--------|-----|
| 1 | [Formal Foundations](cogsec_multiagent_1_theory/) (Second Edition) | v1.1 (improved release) | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| 2 | [Computational Validation](cogsec_multiagent_2_computational/) (Second Edition) | Preprint (v1.0) | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| 3+4 merged | [Practical Applications and Deployment Guide](cogsec_multiagent_3_practical/) (Parts 3+4 Unified) | Preprint (v1.0) | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

Release plan: Part 1 ships as the improved **v1.1** (Second Edition); Parts 2 and
3+4 ship as first releases (**v1.0** preprints) of their Second Edition manuscripts.

### Reading order

- **Start with Part 1** if you want definitions, theorems, and the formal trust / defense / adversary apparatus.
- **Start with Part 2** if you want empirical evidence — the 950-attack corpus, ablation studies, Bayesian uncertainty, parametric ceilings (exact architecture set and ceiling definition are in Part 2 methodology).
- **Start with Part 3+4 (merged)** if you are deploying CIF and need engineering guidance without formal prerequisites or are evaluating CIF for a specific operational sector (infrastructure, supply chain, cyber, biowarfare, information ecosystems, etc.).

Each paper stands alone but explicitly points readers to the most relevant sections of its siblings.

## Author

**Daniel Ari Friedman**  
Active Inference Institute

## Key Contributions

- **Trust Calculus** with bounded delegation and δ^d decay (Part 1)
- **Defense Composition Algebra** for layered security reasoning (Part 1)
- **Computational validation** over a 950-attack corpus (Part 2; architecture set and parametric ceiling definitions are in that manuscript's methodology)
- **Operator-facing synthesis** with checklists, risk framing, and deployment guidance (Part 3)
- **CIF-AD-OODA integration** and ten-domain applied analysis of goal hijacking (Part 3+4)
- **Three universal attack patterns** — FR Polarity Inversion, Constraint Relaxation, Context Boundary Violation (Part 3+4)
- **Four defense extensions** in the cross-domain study — verification channel separation, active perturbation probing, physics-informed invariants, semiotic decoupling

## Documentation

Technical documentation for the CIF implementation lives in [`cogsec_multiagent_2_computational/docs/`](cogsec_multiagent_2_computational/docs/):

- [Claims Traceability](cogsec_multiagent_2_computational/docs/claims_traceability.md) — Manuscript-to-code mapping
- [Usage Guides](cogsec_multiagent_2_computational/docs/usage_guides/) — Per-component guides (Firewall, Sandbox, Trust, Consensus, Tripwires, Drift Detection, Provenance, Invariants, Red-Team Evaluation)
- [Framework Validation](cogsec_multiagent_2_computational/docs/framework_validation.md) — Experiment reproduction guide
- [Program Documentation Index](docs/README.md) — Program-wide documentation map

## Figures and accessible outputs

For manuscripts: use explicit figure captions in markdown; where markdown allows `alt` text for images, set meaningful alt text so HTML builds remain readable without the image. Spot-check combined HTML under each part's `output/web/` after changing figures.

## Citation

Part 1 (example; see Zenodo for each part's record):

```bibtex
@article{friedman2026cogsec1,
  author = {Friedman, Daniel Ari},
  title = {Cognitive Integrity Framework: Formal Foundations},
  year = {2026},
  doi = {10.5281/zenodo.18364119},
  publisher = {Zenodo},
  note = {Part 1 of three: Cognitive Security for Multiagent Operators}
}
```

## Repository

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Template**: [docxology/template](https://github.com/docxology/template)

## Building

**If this checkout is nested inside [`docxology/template`](https://github.com/docxology/template)** (i.e. this directory lives at `projects/cognitive_integrity/` under that repo's root), build from the **template repository root** (with `uv sync` already run there):

```bash
# Render any paper as PDF (qualified names required for the nested layout)
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_2_computational
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_3_practical

# Or directly:
uv run python scripts/pipeline/stage_03_render.py --project cognitive_integrity/cogsec_multiagent_1_theory

# Run tests (examples; run from repo root)
uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/ -v
uv run pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -q
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v
```

Part 2's tests import `scipy` (declared in that part's `pyproject.toml`). If collection fails with `ModuleNotFoundError: scipy`, run `uv sync` from `cogsec_multiagent_2_computational/` so its dependencies are installed, then re-run pytest from the repo root as above.

**In a standalone checkout of this repo** (no `run.sh`/`scripts/` at this root — the case if you cloned `docxology/cognitive_integrity` directly rather than as a nested project of `docxology/template`), there is no repo-root build entry point. Each part is independently buildable from its own directory:

```bash
cd cogsec_multiagent_1_theory && uv sync && uv run pytest tests/ -q && uv run ruff check .
cd cogsec_multiagent_2_computational && uv sync && uv run pytest tests/ -q && uv run ruff check . && make all   # data + figures + tables + verify
cd cogsec_multiagent_3_practical && uv sync && uv run pytest tests/ -q && uv run ruff check .
```

Manuscript integrity checks (Parts 1 and 3) and figure regeneration are documented in each part's own `README.md` § Usage and `scripts/README.md`.

## Series-level integrity gate

Every other check in this repository is scoped to one part: each part runs its own
`pytest` and its own `verify_manuscript.py`, and Part 2 runs its claim registry over its own
manuscript. Nothing compared the three papers to each other, which is how a shared quantity
came to be published as two different numbers in two papers that cite each other.

```bash
python3 scripts/check_series_integrity.py            # all checks
python3 scripts/check_series_integrity.py --only bibliography
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

Two variables are derived structurally rather than from an artifact: the applied-domain count
is obtained by counting Part 3's `09c..09l` section files, and the ablation denominator is
recovered from the measurement resolution (with an n-sample corpus every delta is a multiple
of 1/n, so the smallest non-zero delta *is* 1/n). Neither is typed anywhere.


Every check fails on an empty input set: a pattern that matches nothing is a broken guard,
not a clean run. `tests/test_series_integrity.py` drives each check against a planted defect
and requires it to be caught.

## License

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).