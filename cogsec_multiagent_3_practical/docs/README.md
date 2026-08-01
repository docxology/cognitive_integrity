# Part 3+4 — Practical Applications and Deployment Guide: Documentation

Documentation index for **Part 3+4 (merged)** of *Cognitive Security for
Multiagent Operators*. This part is the practitioner-facing guide and
cross-domain application study that consumes the formal foundations (Part 1) and
computational evidence (Part 2).

## Documentation map

| Entry | Role |
| ----- | ---- |
| [`../README.md`](../README.md) | Onboarding, build/test commands, cross-paper reading guide |
| [`../AGENTS.md`](../AGENTS.md) | Agent reference: structure, verification, invariants |
| **`README.md` (this file)** | Documentation index and claims-to-code map |
| [`../PAI.md`](../PAI.md) | Paper authoring instructions |
| [`../SKILL.md`](../SKILL.md) | Agent skills for this exemplar |
| [`../manuscript/`](../manuscript/) | The paper content (34 files: 32 markdown + `config.yaml` + `references.bib`) |
| [`../src/`](../src/) | Source: checklists, applications, verification |

## What this part provides

- **Deployment guide** — hardening, posture, incident response, monitoring,
  cost–benefit (§05*, §06*).
- **Cross-domain CIF-AD-OODA analyses** — ten applied domains (§09b–§09l),
  e.g. cyber security, supply chain, biowarfare, food security, infrastructure.
- **Universal attack patterns + incident retrospective** (§06b, §10).
- **Human-actionable checklists** — `src/checklists/` (pre-deployment,
  operational, incident response).
- **Domain coverage rendering** — `src/applications/domain_coverage.py` →
  `scripts/07_domain_coverage_figure.py`.

## Claims → code map

| Manuscript area | Concept | Implementation |
| --------------- | ------- | -------------- |
| §10 domain coverage | Ten-domain CIF-AD-OODA coverage matrix | `src/applications/domain_coverage.py` (`DOMAINS`, coverage renderer) |
| §4/§5 deployment checklists | Pre-deployment / operational / incident-response checklists | `src/checklists/` (`PreDeploymentChecklist`, `OperationalChecklist`, `IncidentResponseChecklist`) |
| §2 configuration reference | Firewall thresholds, tripwires, trust parameters | `src/checklists/config_reference.py` (`ConfigurationReference`, `FirewallThreshold`, ...) |
| Manuscript integrity | Citation / link / structure / weasel-word checks | `src/verification.py` (+ `scripts/verify_manuscript.py`) |

## Figures

`scripts/` produces 8 deterministic figures into `output/figures/` (posture
radar, checklist flowchart, risk matrix, trust decay, pitfall severity, timeline,
domain coverage, CIF mechanism coverage):

```bash
uv run python scripts/07_domain_coverage_figure.py
uv run python scripts/01_posture_radar_figure.py
# ... 02..06 analogue figure scripts
```

> **Note:** As of this writing the produced figures are not embedded in the
> rendered PDF — the `manuscript/config.yaml` `figures:` block declares paths
> that the scripts do not produce, and none of the 8 real outputs are referenced
> in the markdown. Wiring the figures into the paper is tracked as follow-up
> work; the scripts themselves are real and deterministic.

## Verification and tests

```bash
# Manuscript integrity (citations, links, labels, structure)
uv run python scripts/verify_manuscript.py --root manuscript

# Tests
uv run pytest tests/ -q

# Lint
uv run ruff check .
```

See [`../AGENTS.md`](../AGENTS.md) and [`../README.md`](../README.md) for the
cross-paper reading guide and how to render this paper as PDF from the template
repo (`cognitive_integrity/cogsec_multiagent_3_practical`).