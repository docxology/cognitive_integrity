# Cognitive Security in Practice: Actionable Guidance (Paper 3)

Part 3 of the **Cognitive Security for Multiagent Operators** series.

**Status: Preprint** | **DOI:** [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130)

## Overview

This paper translates the Cognitive Integrity Framework (CIF) into **actionable guidance** for practitioners deploying multiagent AI systems. Prose-only format with minimal technical prerequisites.

## Primary Focus

- **Operator Posture Assessment**: Five-pillar security posture evaluation with maturity scoring
- **Human Checklists**: Pre-deployment, operational, and incident response procedures
- **Agent Guidelines**: Machine-readable security invariants and self-monitoring protocols
- **Deployment Configuration**: Risk-profile-based parameter selection with architecture guidance
- **Risk Assessment**: Attack surface mapping, threat modeling, and worked examples
- **Common Pitfalls**: Eight documented anti-patterns with detection and remediation

## Paper Series

| Part | Title | Focus | Status | DOI |
|------|-------|-------|--------|-----|
| 1 | Formal Foundations | Theory, proofs, formalisms | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| 2 | Computational Validation | Empirical results, algorithms | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| **3 (This)** | Practical Guidance | Deployment checklists, guidelines | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

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
│   └── S01_notation_reference.md
├── src/                  # Implementation modules
│   ├── __init__.py           # Core types (RiskLevel, PostureLevel, ChecklistItem, etc.)
│   ├── posture.py            # Five Pillars assessment + maturity scoring
│   ├── checklists.py         # Pre-deployment, operational, incident response
│   ├── agent_guidelines.py   # Security invariants + monitoring + response protocols
│   ├── deployment.py         # Risk profiles, architecture guidance, scaling
│   ├── risk_assessment.py    # Attack surface mapping + threat modeling
│   ├── pitfalls.py           # Anti-pattern catalog + detection + remediation
│   ├── integration.py        # Cross-module orchestrator + worked examples
│   └── visualization.py      # Figure generation (radar, heatmap, bar, etc.)
├── scripts/              # Figure generation orchestrators
│   ├── 01_posture_radar_figure.py
│   ├── 02_checklist_flowchart_figure.py
│   ├── 03_risk_matrix_figure.py
│   ├── 04_trust_decay_figure.py
│   ├── 05_pitfall_severity_figure.py
│   ├── 06_timeline_figure.py
│   └── verify_manuscript.py
├── tests/                # 90%+ coverage test suite
│   ├── conftest.py
│   ├── test_practical.py
│   ├── test_visualization.py
│   ├── test_posture.py
│   ├── test_checklists.py
│   ├── test_agent_guidelines.py
│   ├── test_deployment.py
│   ├── test_risk_assessment.py
│   ├── test_pitfalls.py
│   └── test_integration.py
└── output/               # Generated figures and PDF
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

```bash
# Run full test suite
python3 -m pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v

# Run with coverage
python3 -m pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ \
    --cov=projects/cognitive_integrity/cogsec_multiagent_3_practical/src \
    --cov-fail-under=90 -v

# Render PDF
./run.sh --render-pdf --project cogsec_multiagent_3_practical
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
