# Cognitive Security in Practice: Actionable Guidance (Paper 3)

Part 3 of the **Cognitive Security for Multiagent Operators** series.

## Overview

This paper translates the Cognitive Integrity Framework (CIF) into **actionable guidance** for practitioners deploying multiagent AI systems. Prose-only format with minimal technical prerequisites.

## Primary Focus

- **Human Checklists**: Security posture assessment for operators
- **Agent Guidelines**: Machine-readable guidance for AI systems
- **Deployment Considerations**: Risk profiles and configuration
- **Common Pitfalls**: Anti-patterns and mitigations

## Paper Series

| Part | Title | Focus |
| ---- | ----- | ----- |
| 1 | Formal Foundations | Theory, proofs, formalisms |
| 2 | Computational Validation | Empirical results, algorithms |
| **3 (This)** | Practical Guidance | Deployment checklists, guidelines |

## Project Structure

```text
cogsec_multiagent_3_practical/
├── manuscript/           # Paper content (prose-only)
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_operator_posture.md
│   ├── 03_human_checklist.md
│   ├── 04_agent_guidelines.md
│   ├── 05_deployment.md
│   ├── 06_risk_assessment.md
│   ├── 07_common_pitfalls.md
│   ├── 08_conclusion.md
│   └── S01_notation_reference.md  # References Paper 1
└── output/               # Generated PDF
```

## Usage

```bash
# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_3_practical
```

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.16903352](https://doi.org/10.5281/zenodo.16903352)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Audience

- Security practitioners assessing multiagent deployments
- Developers building agentic AI applications
- AI system operators managing cognitive security posture
- Compliance teams evaluating AI risk frameworks
