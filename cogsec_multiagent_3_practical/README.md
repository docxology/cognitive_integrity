# Cognitive Security in Practice: Actionable Guidance (Part 3)

Part 3 of the **Cognitive Security for Multiagent Operators** series.

**Status: Preprint** | **DOI:** [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130)

## Overview

This paper translates the Cognitive Integrity Framework (CIF) into **actionable guidance** for practitioners deploying multiagent AI systems. Prose-first format with minimal formal prerequisites.

**Prerequisites:** None required. Optional: [Part 1](../cogsec_multiagent_1_theory/) [`S03_notation.md`](../cogsec_multiagent_1_theory/manuscript/S03_notation.md) for full notation; this part’s [`S01_notation_reference.md`](manuscript/S01_notation_reference.md) is a short in-paper table. For benchmarks and code-level defenses, see [Part 2](../cogsec_multiagent_2_computational/).

## Primary Focus

- **Operator Posture Assessment**: Five-pillar security posture evaluation with maturity scoring
- **Human Checklists**: Pre-deployment, operational, and incident response procedures
- **Agent Guidelines**: Machine-readable security invariants and self-monitoring protocols
- **Deployment Configuration**: Risk-profile-based parameter selection with architecture guidance
- **Risk Assessment**: Attack surface mapping, threat modeling, and worked examples
- **Common Pitfalls**: Documented anti-patterns with detection and remediation

## Paper Series

| Part | Title | Focus | Status | DOI |
|------|-------|-------|--------|-----|
| 1 | Formal Foundations | Theory, proofs, formalisms | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| 2 | Computational Validation | Empirical results, algorithms | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| **3 (This)** | Practical Guidance | Deployment checklists, guidelines | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |
| 4 | [Applications](../cogsec_multiagent_4_applications/) | Ten-domain CIF-AD-OODA | Preprint | _DOI pending_ |

## Project Structure

```text
cogsec_multiagent_3_practical/
├── manuscript/
│   ├── 00_abstract.md
│   ├── 01_introduction.md
│   ├── 02_theory_review.md
│   ├── 03_simulation_review.md
│   ├── 04_attack_scenarios.md, 04b_subagent_hardening.md
│   ├── 05_deployment_guide.md, 05b_incident_response.md, 05c_cost_benefit.md, 05d_monitoring_guide.md
│   ├── 06_common_pitfalls.md, 06b_case_studies.md
│   ├── 07_future_directions.md, 08_conclusion.md
│   ├── 99_references.md, S01_notation_reference.md
│   ├── config.yaml, preamble.md, references.bib
├── src/
│   ├── posture.py, checklists.py, agent_guidelines.py, deployment.py
│   ├── risk_assessment.py, pitfalls.py, integration.py, visualization.py
│   └── __init__.py
├── scripts/              # Figure orchestrators + verify_manuscript.py
├── tests/
└── output/
```

## Citation

```bibtex
@article{friedman2026cogsec_practical,
  author = {Friedman, Daniel Ari},
  title = {Cognitive Security in Practice: Actionable Guidance for Multiagent Operators},
  year = {2026},
  doi = {10.5281/zenodo.18364130},
  publisher = {Zenodo},
  note = {Part 3 of Cognitive Security for Multiagent Operators series}
}
```

## Usage

From the **template repository root**:

```bash
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v

uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ \
    --cov=projects/cognitive_integrity/cogsec_multiagent_3_practical/src \
    --cov-fail-under=90 -v

./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_3_practical
```

From this project directory:

```bash
uv run pytest tests/ -v --cov=src --cov-fail-under=90
```

## Repository

The complete Cognitive Integrity Framework manuscript series is available at:

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Zenodo**: [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130)

These manuscripts are designed to be built using the [docxology/template](https://github.com/docxology/template) research project infrastructure.

## Audience

- Security practitioners assessing multiagent deployments
- Developers building agentic AI applications
- AI system operators managing cognitive security posture
- Compliance teams evaluating AI risk frameworks
