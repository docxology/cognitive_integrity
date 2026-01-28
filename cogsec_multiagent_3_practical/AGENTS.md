# Cognitive Security in Practice - Agent Reference

**This is an active project** in the `projects/` directory, discovered and executed by infrastructure discovery functions.

## Overview

Part 3 of the **Cognitive Security for Multiagent Operators** series. This project provides actionable practical guidance for deploying cognitive security in multiagent AI systems.

## Content Focus

### Human-Actionable Guidance
- **Operator Posture**: Assessment of cognitive security readiness
- **Deployment Checklists**: Step-by-step security configuration
- **Risk Assessment**: Threat modeling for cognitive attack surfaces
- **Common Pitfalls**: Anti-patterns and mitigations

### Agent-Readable Guidelines
- **Machine-Readable Checklists**: Structured guidance for AI agents
- **Security Invariants**: Rules for agent self-monitoring
- **Trust Boundaries**: Guidelines for inter-agent communication

## Directory Structure

```
cogsec_multiagent_3_practical/
├── manuscript/                 # Paper content (prose-only)
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_operator_posture.md
│   ├── 03_human_checklist.md
│   ├── 04_agent_guidelines.md
│   ├── 05_deployment.md
│   ├── 06_risk_assessment.md
│   ├── 07_common_pitfalls.md
│   ├── 08_conclusion.md
│   └── S01_notation_reference.md
└── output/                     # Generated PDF
```

## Target Audience

- Security practitioners assessing multiagent deployments
- Developers building agentic AI applications
- AI system operators managing cognitive security
- Compliance teams evaluating AI risk

## Notation Reference

Minimal notation used; full definitions in:
- `../cogsec_multiagent_1_theory/manuscript/S06_notation.md`

## Usage

```bash
# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_3_practical
```

## Guidelines for Editing

- **Prose-Only**: No code blocks in manuscript
- **Actionable**: Every section should have concrete steps
- **Accessible**: Minimal technical prerequisites
- **Cross-Referenced**: Link to Papers 1 and 2 for depth
