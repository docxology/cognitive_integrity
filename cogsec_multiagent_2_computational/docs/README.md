# Part 2 — Computational Validation: Documentation

Documentation index for **Part 2** of *Cognitive Security for Multiagent
Operators*. This part implements and empirically validates the CIF defense suite
(cognitive firewall, belief sandbox, tripwires, drift/anomaly scoring, trust
calculus, provenance tracking, Byzantine-tolerant consensus) built on the formal
foundations of [Part 1](../cogsec_multiagent_1_theory/).

## Documentation map

| Entry | Role |
| ----- | ---- |
| [`../README.md`](../README.md) | Onboarding, build/test commands, component overview |
| [`../REPRODUCE.md`](../REPRODUCE.md) | End-to-end experiment reproduction |
| [`../AGENTS.md`](../AGENTS.md) | Agent reference: structure, verification, invariants |
| [`../PAI.md`](../PAI.md) | Paper authoring instructions |
| [`../SKILL.md`](../SKILL.md) | Agent skills for this exemplar |
| **`README.md` (this file)** | Documentation index |
| [`../manuscript/`](../manuscript/) | The paper content (markdown + `config.yaml` + `references.bib`) |
| [`../src/`](../src/) | The authoritative CIF implementation (each subpackage ships its own `README.md`/`AGENTS.md`) |

## Core documents

| Entry | Role |
| ----- | ---- |
| [`claims_traceability.md`](claims_traceability.md) | Manuscript-to-code mapping for every claim; authority for what the paper asserts |
| [`framework_validation.md`](framework_validation.md) | Framework validation and reproducibility: how each experiment maps to data artifacts |
| [`usage_guides/`](usage_guides/) | Per-component usage guides (9): how to instantiate and use each defense module |

## Usage guides

| Guide | Component |
| ----- | --------- |
| [`usage_guides/01_cognitive_firewall.md`](usage_guides/01_cognitive_firewall.md) | Cognitive Firewall |
| [`usage_guides/02_belief_sandbox.md`](usage_guides/02_belief_sandbox.md) | Belief Sandbox |
| [`usage_guides/03_trust_calculus.md`](usage_guides/03_trust_calculus.md) | Trust Calculus with bounded delegation |
| [`usage_guides/04_byzantine_consensus.md`](usage_guides/04_byzantine_consensus.md) | Byzantine-tolerant Consensus |
| [`usage_guides/05_identity_tripwires.md`](usage_guides/05_identity_tripwires.md) | Identity Tripwires |
| [`usage_guides/06_drift_detection.md`](usage_guides/06_drift_detection.md) | Drift / anomaly detection |
| [`usage_guides/07_provenance_tracking.md`](usage_guides/07_provenance_tracking.md) | Provenance tracking |
| [`usage_guides/08_invariant_monitoring.md`](usage_guides/08_invariant_monitoring.md) | Invariant monitoring |
| [`usage_guides/09_redteam_evaluation.md`](usage_guides/09_redteam_evaluation.md) | Red-team evaluation & adversarial training (§05g/§05h) |

## Claims traceability

Every manuscript claim is bound, via a claims registry
(`src/manuscript/claim_registry.py`), to a reproducible data artifact under
`output/data/`. `scripts/verify_claims.py` checks the installed manuscript
against the current data; a green run means every registry-backed number matches
its source. See [`claims_traceability.md`](claims_traceability.md) for the
claim-by-claim map and
[`framework_validation.md`](framework_validation.md) for how each experiment is
reproduced.

## Evidence-integrity notes

- **Provenance honesty**: `scripts/run_redteam.py` /
  `scripts/run_adversarial_training.py` write `seed` and `source_script` on every
  artifact. Adversarial-training runs in `model` measurement mode are a
  closed-form design model and deliberately omit a `data_origin: real_pipeline`
  stamp (see `src/redteam/`); only `real` mode records real-measured provenance.
- **Determinism**: same-seed re-runs reproduce artifacts byte-for-byte (no
  timestamps in committed JSON).
- **No mocks**: tests validate against real/independent data.

## Verification and tests

```bash
# Claims registry against installed manuscript (expect: MATCH on all real claims)
uv run python scripts/verify_claims.py

# Injector (data-backed manuscript variable substitution) dry-run
uv run python -c "from pathlib import Path; from src.manuscript.injector import inject_all; inject_all(Path('output/data'), Path('manuscript'), dry_run=True, strict=False)"

# Tests (full Part 2 suite)
.venv/bin/python -m pytest tests/ -q

# Lint
.venv/bin/ruff check src scripts tests
```

## Red-Team assessment & historical audits

| Entry | Role |
| ----- | ---- |
| [`RED_TEAM_ASSESSMENT.md`](RED_TEAM_ASSESSMENT.md) | Deep adversarial (red-team) assessment of the program: theory soundness, empirical/model validity, code/security/reproducibility, and their resolutions (authoritative, kept current) |
| [`audits/README.md`](audits/README.md) | Index of historical, point-in-time audit snapshots |

See [`../README.md`](../README.md) and the program
[`docs/README.md`](../../docs/README.md) for the cross-paper reading guide and
how to render this paper as PDF from the template repo.
