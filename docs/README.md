# Cognitive Integrity Program — Documentation

Documentation index for the **Cognitive Security for Multiagent Operators**
three-part manuscript series. This index is the entry point for documentation
across the program and each part's `docs/` folder.

## Program overview

The **Cognitive Integrity Framework (CIF)** provides defense-in-depth security
for multiagent AI systems. See the [program `README.md`](../README.md) for the
series map, reading order, and build commands, and
[`AGENTS.md`](../AGENTS.md) for the agent reference.

## Documentation map

| Location | Contents |
| -------- | -------- |
| **`README.md` (this file)** | Program-wide documentation index |
| `THERMO_NUCLEAR_AUDIT_2026-07-22.md` | Historical program audit (thermo-nuclear framing) |
| [`deep_audit_improvements.md`](deep_audit_improvements.md) | Ledger of hostile red-team / deep-audit rounds by Part (2026-08-03 to 2026-08-05) |
| [Part 2 `docs/RED_TEAM_ASSESSMENT.md`](../cogsec_multiagent_2_computational/docs/RED_TEAM_ASSESSMENT.md) | Authoritative deep red-team (adversarial) assessment — theory soundness, empirical/model validity, code/security/reproducibility, and their resolutions |
| [Part 1 `docs/`](../cogsec_multiagent_1_theory/docs/) | [Part 1 index](../cogsec_multiagent_1_theory/docs/README.md) — formal-foundations documentation (manuscript map, figures, tests) |
| [Part 2 `docs/`](../cogsec_multiagent_2_computational/docs/) | [Part 2 index](../cogsec_multiagent_2_computational/docs/README.md) — claims traceability, framework validation, per-module usage guides, audit reports |
| [Part 3 `docs/`](../cogsec_multiagent_3_practical/docs/) | [Part 3 index](../cogsec_multiagent_3_practical/docs/README.md) — Part 3+4 practical/applications documentation (claims → code map) |

## Per-part documentation

### Part 1 — Formal Foundations (`cogsec_multiagent_1_theory/`)

- [`docs/`](../cogsec_multiagent_1_theory/docs/) — theory-part documentation and
  audit TODO.
- Manuscript: trust calculus, defense composition algebra, adversary taxonomy,
  CIF-AD-OODA.

### Part 2 — Computational Validation (`cogsec_multiagent_2_computational/`)

This part carries the richest documentation spine:

- [`docs/claims_traceability.md`](../cogsec_multiagent_2_computational/docs/claims_traceability.md)
  — manuscript-to-code mapping for every claim.
- [`docs/RED_TEAM_ASSESSMENT.md`](../cogsec_multiagent_2_computational/docs/RED_TEAM_ASSESSMENT.md)
  — deep red-team (adversarial) assessment and the status of every finding.
- [`docs/framework_validation.md`](../cogsec_multiagent_2_computational/docs/framework_validation.md)
  — experiment reproduction guide.
- [`docs/usage_guides/`](../cogsec_multiagent_2_computational/docs/usage_guides/)
  — per-component guides (firewall, sandbox, trust, consensus, tripwires, drift
  detection, provenance, invariants, red-team evaluation).
- Audit reports (`AUDIT_*.md`) — historical review records.

### Part 3+4 — Practical Guide + Applications (`cogsec_multiagent_3_practical/`)

- [`docs/`](../cogsec_multiagent_3_practical/docs/) — deployment/application
  documentation index and claims → code map.
- Manuscript: deployment guide, incident response, monitoring, cost–benefit,
  ten-domain CIF-AD-OODA analyses, universal attack patterns.

## Source-package documentation

Part 2's `src/` is the authoritative CIF implementation; every subpackage ships
its own `README.md` + `AGENTS.md`. The adversarial-training/red-team module is
documented at
[`src/redteam/`](../cogsec_multiagent_2_computational/src/redteam/README.md).

## Cross-paper evidence spine

- Claims traceability: [`Part 2 docs/claims_traceability.md`](../cogsec_multiagent_2_computational/docs/claims_traceability.md)
- Framework validation (experiment reproduction): [`Part 2 docs/framework_validation.md`](../cogsec_multiagent_2_computational/docs/framework_validation.md)

Keep this index in sync with each part's `docs/` contents; re-derive measured
counts from the live tree rather than hard-coding them.