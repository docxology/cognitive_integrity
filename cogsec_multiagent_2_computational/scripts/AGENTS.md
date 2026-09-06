# CogSec Multiagent — Paper 2 `scripts/` — Agent Reference

Agent guidance for working with the thin-orchestrator scripts in
`cogsec_multiagent_2_computational/scripts/` (standalone repo) or
`projects/working/cognitive_integrity/cogsec_multiagent_2_computational/scripts/`
(template sidecar).

Paper 2 (*Computational Validation*) is the empirical part of the three-part
*Cognitive Security for Multiagent Operators* series. Scripts here produce the
evidence cited by the sibling papers; see [../README.md](../README.md) for the
series map. When a script changes any result that siblings cite, update:

- `src/manuscript/` verifier expectations and the claims registry
- `output/data/` headline JSON
- Sibling cross-references (Part 1 §8 and Part 3+4 §2–§5, §9–§10)

## Thin-Orchestrator Contract (MANDATORY)

Scripts are orchestration only: argparse, path bootstrap, logging, and a single
delegated call into `src/`. Business, data, plot, and analysis logic lives in
`src/` and must be importable and tested there.

```python
#!/usr/bin/env python3
"""Thin orchestrator — imports from src/, handles only I/O + reporting."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from evaluation.runner import ExperimentRunner  # noqa: E402 — computation in src/

def main() -> None:
    out = ROOT / "output" / "data"
    out.mkdir(parents=True, exist_ok=True)
    result = ExperimentRunner(seed=42).run_all()
    result.save(out / "experiment.json")
    print(out / "experiment.json")   # stdout path for manifest collection

if __name__ == "__main__":
    main()
```

**Required**

- All computation delegated to `src/` imports.
- Scripts handle only I/O, reporting, logging, and manifest bookkeeping.
- Bootstrap idiom (used by every script here): `sys.path.insert(0, str(ROOT / "src"))`,
  then import the top-level modules that live under `src/` — e.g.
  `from evaluation.runner import ExperimentRunner`, **not** `from src.evaluation.runner import ...`.
  `src/` itself is not an importable package from these scripts.
- Deterministic RNG: default `seed=42`, overridable via `--seed`.
- Respect `MPLBACKEND=Agg` for headless matplotlib; figure entry points pin
  `SOURCE_DATE_EPOCH` before matplotlib is imported (see `generate_all_figures.py`).

**stdout policy**

- Print output artifact paths to `stdout` for pipeline manifest collection.
- The `run_*` scripts additionally print short, human-readable result summaries
  (tables of measured values, per-round deltas). That reporting is part of the
  orchestrator contract, not business logic — pipelines and Make targets parse
  it. Diagnostics go through `logging`; errors go to `stderr` with a non-zero exit.

**Forbidden**

- Business logic, algorithms, or direct numerical computation in scripts.
- Mocks, `unittest.mock`, `MagicMock`, `mocker.patch` — no mocks anywhere in the
  project (test suite enforces this; see `src/AGENTS.md` for the no-mocks policy).
- Hard-coded paths outside the repo root.

## Script Inventory (37 scripts — keep docs in sync)

### Orchestrators (3)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `generate_all_data.py` | Runs all data-generation pipelines | `src/data/generate.py`, `src/utils/` | `output/data/*.{json,csv,parquet}` |
| `generate_all_figures.py` | Produces all manuscript figures | `src/visualization/figures.py` | `output/figures/*.pdf` |
| `generate_all_tables.py` | Produces all manuscript tables | `src/visualization/tables/*` | `output/tables/*.tex` |

### Corpus measurement (11) — write one artifact, support `--check`

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `run_taxonomy_evaluation.py` | Full attack taxonomy × all 256 defense-subset configurations (18-config `--axes` mode) | `src/attacks/corpus.py`, `src/composition/factory.py`, `src/evaluation/benign_corpus.py`, `src/ablation/runner.py` | `output/data/taxonomy_evaluation_results.json` |
| `run_detector_auc.py` | AUC with bootstrap intervals for the drift detector and the fused ensemble | `src/evaluation/roc.py`, `src/composition/fusion.py`, `src/attacks/corpus.py` | `output/data/detector_auc.json` |
| `run_baseline_comparison.py` | Full CIF pipeline vs baseline detectors vs a chance null (out-of-fold) | `src/evaluation/baselines.py` | `output/data/baseline_comparison.json` |
| `run_defense_overlap.py` | Per-module total/unique/shared detection rates plus the union row | `src/composition/algebra.py`, `src/composition/factory.py` | `output/data/defense_overlap.json` |
| `run_module_capability_matrix.py` | Per-module capability vs marginal contribution (masking vs incapacity) | `src/composition/factory.py`, `src/attacks/corpus.py` | `output/data/module_capability_matrix.json` |
| `run_stratified_detection.py` | Detection stratified by adversary class and attack target | `src/attacks/corpus.py`, `src/composition/factory.py` | `output/data/stratified_detection.json` |
| `run_threshold_sweep.py` | Firewall τ quarantine/reject threshold sweeps (operating curve) | `src/evaluation/threshold_sweep.py`, `src/core/firewall.py` | `output/data/threshold_sweep.json` |
| `run_load_sweep.py` | Controlled arrival-rate sweep; finds pipeline saturation point | `src/evaluation/load_driver.py`, `src/composition/factory.py` | `output/data/load_sweep.json` |
| `run_overhead_control.py` | Defended-vs-undefended control arm: latency and memory cost of the pipeline | `src/composition/factory.py` | `output/data/overhead_control.json` |
| `run_fp_mitigation.py` | False-positive root-cause attribution and per-mitigation cost/benefit | `src/composition/mitigations.py`, `src/evaluation/benign_corpus.py` | `output/data/fp_mitigation.json` |
| `run_combination_rule_study.py` | Combination-rule study: standardized-score fusion vs the shipped max rule (b1/b2/b3 split protocol) | `src/attacks/corpus.py`, `src/composition/factory.py`, `src/evaluation/benign_corpus.py` | `output/data/combination_rule_study.json` |

### Evaluation & statistics (7)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `run_full_evaluation.py` | Full evaluation matrix across simulation/pipeline/LLM modes | `src/evaluation/runner.py`, `src/attacks/corpus.py`, `src/architectures/` | `output/data/full_evaluation_results.json` |
| `run_statistical_analysis.py` | Hypothesis tests (H1/H2/H3), effect sizes, assumption checks | `src/statistics/analysis_runner.py` | `output/data/statistical_results.json` |
| `run_ablation.py` | Component removal, minimal configs, pairwise synergy | `src/ablation/runner.py` | `output/data/ablation_results.json` |
| `run_cross_validation.py` | Stratified 5-fold cross-validation on the attack corpus | `src/statistics/cross_validation.py`, `src/ablation/runner.py` | `output/data/cross_validation_results.json` |
| `run_multi_seed.py` | Multi-seed stability analysis (CV across 30 seeds) | `src/statistics/stability.py` | `output/data/multi_seed_results.json` |
| `run_sensitivity_analysis.py` | Parameter sweeps, sensitivity ranking, 2D grid search | `src/statistics/sensitivity.py` | `output/data/sensitivity_results.json` |
| `run_scalability.py` | Colony broadcast rounds at *n* agents; latency/memory scaling with regression inference | `src/evaluation/scalability.py`, `src/evaluation/benchmark.py`, `src/core/trust.py` | `output/data/scalability_results.json` |

### Colony & adversarial / LLM (5)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `run_colony_benchmarks.py` | Colony-level CogSec benchmark scoring (scenarios at 20–100 agents) | `src/colony/benchmark.py` | `output/data/colony_results.json` |
| `run_adversarial_training.py` | Iterative adversarial-training rounds; per-round DR deltas and Nash projection | `src/redteam/` (`AdversarialTrainer`, `NashEquilibriumEstimator`) | `output/data/adversarial_training_results.json` |
| `run_redteam.py` | Ω-level attack generation plus mutation-operator sweep scored against the real `CognitiveFirewall` | `src/redteam/generator.py`, `src/redteam/evasion.py`, `src/core/firewall.py` | `output/data/redteam_evaluation_results.json` |
| `run_llm_demo.py` | Live Ollama-backed multiagent CIF evaluation (opt-in) | `src/agents/`, `src/evaluation/llm_evaluator.py` | `output/data/llm_demo_results.json` |
| `run_publication_suite.py` | Drives `run_full_evaluation.py` per `experiment_config.toml`; LLM branch opt-in | subprocess over `run_full_evaluation.py` | `output/data/*` |

### Verification & formal (3)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `run_formal_validation.py` | Validates Paper 1 theorems via model checkers (NuSMV, SPIN, TLA+) | `src/formal/theorem_registry.py` | `output/data/formal_validation_results.json` |
| `verify_formal_specs.py` | Generates and verifies the formal specification files | `src/formal/spec_verifier.py` | `output/formal/*` + `verification_summary.json` |
| `verify_manuscript.py` | Checks citations, labels, `\cref` targets, figure references, style | `src/manuscript/verifier.py` | `output/logs/manuscript_verification.log` |

### Claims registry (2)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `verify_claims.py` | Re-derives every registered numeric claim from `output/data/` and compares to the prose (CI gate; exit 1 on MISMATCH/NOT_FOUND/UNBACKED) | `src/manuscript/claim_registry.py` | stdout report, optional `--json` |
| `sync_claims.py` | Rewrites MISMATCH literals in place, formatting preserved; never writes NOT_FOUND/UNBACKED | `src/manuscript/claim_registry.py` | `docs/manuscript/*.md` |

### Utilities (6)

| Script | Purpose | Delegates to | Output |
| ------ | ------- | ------------ | ------ |
| `convert_latex_tables.py` | Converts LaTeX tables in manuscript `.md` files to Markdown pipe tables | `src/manuscript/latex_converter.py` | in-place `.md` edits |
| `z_inject_manuscript_values.py` | Auto-injects computed values from `output/data/` into the manuscript (leading `z_` so it runs last) | `src/manuscript/injector.py` | in-place `.md` edits |
| `generate_figure_registry.py` | Scans `docs/manuscript/*.md` for `{#fig:...}`/`{#tab:...}` labels; writes auto-numbered registry | self-contained | `output/data/figure_registry.json` |
| `auto_number_figures.py` | Reads `figure_registry.json`; injects `\label{}`/`\listoffigures` commands | self-contained | in-place `.md` edits |
| `fix_table_labels.py` | Converts bold-paragraph table captions to pandoc-crossref table captions (`--dry-run` to preview) | self-contained | in-place `.md` edits |
| `generate_composer_data.py` | Generates the CIF Composer web-UI data file | `src/visualization/composer_data.py` | `output/data/composer_data.json` |

When adding a new script: (1) add it to this inventory, (2) update
[scripts/README.md](README.md), (3) add a smoke test in `tests/` for the CLI
surface. Docs that list scripts must match the directory.

## Gotchas

- **`--check` family.** The corpus-measurement scripts are pure functions of
  `--seed` and support `--check`, which re-derives and diffs instead of
  re-measuring. Artifacts carry a corpus digest, so a corpus change surfaces as
  a digest mismatch rather than silently invalidating every cell.
- **LLM opt-in.** `run_llm_demo.py` and the LLM branch of
  `run_publication_suite.py` run real Ollama agents and are gated by
  `COGSEC_RUN_LLM_ANALYSIS=1` (or `--run-llm`). Without it they write a skip
  record and exit 0, keeping the render pipeline bounded and reproducible.
- **`z_` prefix.** `z_inject_manuscript_values.py` is named to sort last in the
  manuscript render pipeline; do not rename it.
- **Claim rewrites.** `sync_claims.py` writes only for `MISMATCH`. A
  `NOT_FOUND` is a dead pattern (how a fabricated number hides) and an
  `UNBACKED` is a missing/failed artifact — both are reported, never written.
- **Figure reproducibility.** `generate_all_figures.py` pins
  `SOURCE_DATE_EPOCH` and the matplotlib SVG hash salt before importing
  matplotlib; keep that ordering if you touch it.
- **Import idiom.** After the `sys.path.insert(0, str(ROOT / "src"))`
  bootstrap, import top-level modules (`from evaluation.runner import ...`).
  `ruff` noqa `E402` on those lines is expected.

## Manuscript-to-Script Anchor

| Manuscript claim | Producing script |
| ---------------- | ---------------- |
| §5 overall detection rates | `run_full_evaluation.py`, `run_multi_seed.py` |
| §5.6 / §5d ablation deltas | `run_ablation.py` |
| §5b statistical significance (H1/H2/H3) | `run_statistical_analysis.py` |
| §5c parameter sensitivity | `run_sensitivity_analysis.py` |
| §5e Bayesian uncertainty | `run_multi_seed.py` |
| Colony benchmarks (§5, §S03) | `run_colony_benchmarks.py`, `run_scalability.py` |
| LLM-backed validation (Abstract, §5) | `run_llm_demo.py` |
| Model-checking results (§S04) | `run_formal_validation.py`, `verify_formal_specs.py` |
| S02 `tab:auc-ci` (drift detector, fused ensemble AUC + CI) | `run_detector_auc.py` |
| S08 per-architecture taxonomy tables | `run_taxonomy_evaluation.py` |
| ROC/PR curves with measured bootstrap bands | `run_baseline_comparison.py` |
| Defense-composition figure (unique/shared/union row) | `run_defense_overlap.py` |
| Capability vs marginal contribution (Shapley masking) | `run_module_capability_matrix.py` |
| Stratified (adversary class / target) claims | `run_stratified_detection.py` |
| Firewall threshold operating curve | `run_threshold_sweep.py` |
| `tab:volume-scaling` (arrival-rate sweep, saturation) | `run_load_sweep.py` |
| Overhead/latency comparisons (defended vs control arm) | `run_overhead_control.py` |
| FP root-cause and mitigation tables | `run_fp_mitigation.py` |
| Combination-rule (standardized fusion) results | `run_combination_rule_study.py` |
| §05g adversarial training (per-round DR deltas, Nash projection) | `run_adversarial_training.py` |
| §05h red-team evaluation (Ω-level generation, mutation sweep) | `run_redteam.py` |
| Auto-injected numerical values | `z_inject_manuscript_values.py`, `sync_claims.py` |
| Claim read-back gate (CI) | `verify_claims.py` |
| Figure/table auto-numbering | `generate_figure_registry.py`, `auto_number_figures.py`, `fix_table_labels.py` |
| Composer web-UI backend data | `generate_composer_data.py` |
| Manuscript integrity (citations, refs) | `verify_manuscript.py` |

## CI / Verification

Before committing a non-trivial script change, run:

```bash
uv run python scripts/verify_manuscript.py   # citations, refs, figures
uv run pytest tests/ -x -q                   # smoke test suite
```

Expected: `verify_manuscript.py` prints no warnings; `pytest` passes with zero
failures.
