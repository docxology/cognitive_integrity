# Cognitive Security in Practice — Part 3 — Agent Reference

**Location:** `projects/cognitive_integrity/cogsec_multiagent_3_practical/`. Active nested project under program `cognitive_integrity/`; use qualified name `cognitive_integrity/cogsec_multiagent_3_practical` for `./run.sh` and `scripts/03_render_pdf.py`.

## Overview

Part 3: actionable guidance for deploying cognitive security in multiagent AI systems (checklists, posture, risk, pitfalls, case studies).

## Content focus

### Human-actionable guidance

- **Operator Posture**: Assessment of cognitive security readiness
- **Deployment and operations**: Guides split across `05_*.md` and `05b`–`05d`
- **Risk Assessment**: Threat modeling for cognitive attack surfaces
- **Common Pitfalls**: Anti-patterns and mitigations (`06_common_pitfalls.md`, `06b_case_studies.md`)

### Agent-readable guidance

- **Security Invariants and monitoring**: Implemented in `src/agent_guidelines.py`; manuscript coverage is distributed across the deployment and operations sections (see `05_*.md` and related body sections).
- **Trust Boundaries**: Guidelines for inter-agent communication

## Directory structure

```text
cogsec_multiagent_3_practical/
├── manuscript/
│   ├── 00_abstract.md, 01_introduction.md
│   ├── 02_theory_review.md, 03_simulation_review.md
│   ├── 04_attack_scenarios.md, 04b_subagent_hardening.md
│   ├── 05_deployment_guide.md, 05b_incident_response.md, 05c_cost_benefit.md, 05d_monitoring_guide.md
│   ├── 06_common_pitfalls.md, 06b_case_studies.md
│   ├── 07_future_directions.md, 08_conclusion.md
│   ├── 99_references.md, S01_notation_reference.md
│   └── config.yaml, preamble.md, references.bib
├── src/                        # posture, checklists, agent_guidelines, deployment, risk_assessment, pitfalls, integration, visualization
├── scripts/
├── tests/
└── output/
```

## Target audience

- Security practitioners assessing multiagent deployments
- Developers building agentic AI applications
- AI system operators managing cognitive security
- Compliance teams evaluating AI risk frameworks

## Notation reference

Minimal notation in Part 3; full definitions:

- `../cogsec_multiagent_1_theory/manuscript/S03_notation.md`

## Usage

From the template repository root:

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_3_practical
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v
```

## Guidelines for editing

- **Prose-first**: Keep manuscript sections actionable; follow project conventions for code in `src/` vs manuscript.
- **Actionable**: Each major section should yield concrete steps where appropriate.
- **Cross-referenced**: Link to Parts 1–2 for formal and empirical depth; Part 4 for domain applications.
