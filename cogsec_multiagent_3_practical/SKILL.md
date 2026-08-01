---
name: cogsec-multiagent-3-practical
description: Cognitive Integrity Framework — Part 3 practical deployment guides (risk assessment, checklists, posture, pitfalls, incident response)
triggers:
  - when: "user mentions 'Part 3' or 'practical' or 'deployment' or 'operations'"
    action: "route to this project"
  - when: "task involves deployment checklists, risk posture, or incident response"
    action: "direct to this project"
version: 1.0.0
author: Daniel Ari Friedman
license: MIT
---

# Cognitive Integrity Framework — Part 3 (Practical Implementation)

## Purpose

This skill directs LLM agents to **Part 3** of the Cognitive Security for Multiagent Operators series. Part 3 translates theoretical foundations and computational validation into actionable operational guidance:

- Operator posture assessment
- Deployment checklists and runbooks
- Risk assessment frameworks
- Common pitfalls and anti-patterns
- Incident response procedures
- Cost–benefit analysis
- Monitoring and observability

## When to Use

Invoke this skill when:
- User asks how to deploy CIF in production
- Task involves creating checklists, runbooks, or deployment guides
- Need to evaluate risk posture or incident scenarios
- Writing operational documentation or playbooks
- Evaluating cost/benefit trade-offs for defense mechanisms

## Key Files

- `src/posture.py` — Cognitive security readiness assessment
- `src/deployment.py` — Deployment configuration and lifecycle
- `src/risk_assessment.py` — Threat modeling and risk scoring
- `src/checklists/` — Pre-flight, post-deployment, and audit checklists (package)
- `src/pitfalls.py` — Anti-patterns and mitigations
- `src/agent_guidelines.py` — Machine-readable security rules for agents
- `src/visualization.py` — Posture and risk visualization

## Manuscript Structure

```
manuscript/
├── 00_abstract.md
├── 01_introduction.md        # Recap Parts 1–2, introduce Part 3
├── 02_operator_posture.md    # Assessment framework
├── 03_deployment_guide.md    # Step-by-step rollout
├── 04_risk_assessment.md     # Threat modeling
├── 05_incident_response.md   # Detection → triage → remediation
├── 06_common_pitfalls.md     # Anti-patterns + fixes
├── 06b_case_studies.md       # Real-world scenarios
├── 07_cost_benefit.md        # Resource allocation analysis
├── 08_operational_monitoring.md # Metrics and alerting
├── 09_conclusion.md
└── 99_references.md
```

## Commands

```bash
# Render PDF
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_3_practical

# Run tests (covers risk, posture, checklists, pitfalls)
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -q

# Generate posture visualization (one figure per `scripts/0X_*_figure.py`; example below)
uv run python projects/cognitive_integrity/cogsec_multiagent_3_practical/scripts/01_posture_radar_figure.py
```

## Cross-Part Discipline

- Content is standalone; minimal cross-references to Part 1 (definitions) and Part 2 (empirical efficacy).
- Maintain consistency with CIF terminology established in Part 1.
- Cite Part 2 results when justifying deployment decisions.

## Agent Guidelines

Agents modifying this project should:

- Keep guidance actionable — avoid theoretical digressions.
- Use clear, checklist-oriented formatting (numbered steps, bullet points).
- Reference specific configuration keys from Part 2 implementations.
- Include cost estimates (compute, latency, token overhead) where applicable.
- Provide incident response playbooks in a structured "trigger → detection → containment → recovery" format.
