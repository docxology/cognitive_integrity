# CIF Practical Applications and Deployment Guide — Agent Reference

**Location:** `projects/cognitive_integrity/cogsec_multiagent_3_practical/`. Active nested project under program `cognitive_integrity/`; use qualified name `cognitive_integrity/cogsec_multiagent_3_practical` for `./run.sh` and `scripts/03_render_pdf.py`.

## Overview

**Unified Part 3+4** of the *Cognitive Security for Multiagent Operators* series (v2.0.0). This project combines:

- **Practitioner guidance** for deploying CIF in multiagent AI systems (§1–§8): checklists, posture assessment, risk assessment, deployment configuration, incident response, pitfalls, and case studies.
- **Cross-domain CIF-AD-OODA applications** (§9–§10): systematic analysis of Goal Hijacking across ten critical operational domains using the integrated Axiomatic Design + OODA Loop model, three universal attack patterns, three novel defense extensions, and retrospective validation against six documented 2024–2025 AI security incidents.

This project supersedes the now-deleted `cogsec_multiagent_4_applications/` directory. All Part 4 content has been fully integrated here.

## Content focus

### Human-actionable guidance (§1–§8)

- **Operator Posture**: Assessment of cognitive security readiness (five pillars)
- **Deployment and operations**: Guides in `05_*.md`, `05b`–`05d`
- **Risk Assessment**: Threat modeling for cognitive attack surfaces
- **Common Pitfalls**: Anti-patterns and mitigations (`06_common_pitfalls.md`, `06b_case_studies.md`)

### Agent-readable guidance (§1–§8)

- **Security Invariants and monitoring**: `src/agent_guidelines.py`; coverage across `05_*.md` sections
- **Trust Boundaries**: Guidelines for inter-agent communication

### Cross-domain applications (§9–§10)

- **CIF-AD-OODA Methodology**: `09b_cif_ad_ooda_methodology.md`
- **10 Domain analyses**: `09c_*.md` through `09l_*.md`
- **Cross-domain synthesis**: `10_cross_domain_discussion.md`
- **Real-world incidents**: `S03_real_world_incidents.md` (6 documented AI security incidents, 2024–2025)

## Directory structure

```text
cogsec_multiagent_3_practical/
├── manuscript/
│   ├── 00_abstract.md … 08_conclusion.md    (Part 3 practitioner content)
│   ├── 09_applications_intro.md             (Part 4 teleological attack surface)
│   ├── 09b_cif_ad_ooda_methodology.md       (CIF-AD-OODA framework)
│   ├── 09c_rare_earth_mining.md … 09l_fake_news.md   (10 domain case studies)
│   ├── 10_cross_domain_discussion.md        (attack patterns, BFT validation)
│   ├── 10b_applications_conclusion.md
│   ├── 99_references.md, S01_notation_reference.md
│   ├── S03_real_world_incidents.md          (6 documented incidents)
│   └── config.yaml (v2.0), preamble.md, references.bib (merged, 148+ entries)
├── src/                   posture, checklists, agent_guidelines, deployment,
│                          risk_assessment, pitfalls, visualization, identity
├── scripts/               Figure generators + verify_manuscript.py
├── tests/                 test_practical.py + test_applications.py + test_identity.py + 7 more test files (10 total)
└── output/
```

## Merge provenance

| Source | Content | Original version |
|--------|---------|-----------------|
| `cogsec_multiagent_3_practical` | §1–§8 practitioner guidance | v1.0.0 |
| `cogsec_multiagent_4_applications` | §9–§10 CIF-AD-OODA applications | v1.0.0 |

## Target audience

- Security practitioners assessing multiagent deployments
- Developers building agentic AI applications
- AI system operators managing cognitive security
- Compliance teams evaluating AI risk frameworks
- Domain security analysts applying CIF to specific operational sectors

## Notation reference

Minimal notation in §1–§8; formal notation in S01; full definitions:
- `../cogsec_multiagent_1_theory/manuscript/S03_notation.md`

## Usage

From the template repository root:

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_3_practical
uv run pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v
```

## Guidelines for editing

- **Prose-first (§1–§8)**: Keep manuscript sections actionable; follow project conventions for code in `src/` vs manuscript.
- **Actionable**: Each major section should yield concrete steps where appropriate.
- **Cross-referenced**: Link to Parts 1–2 for formal and empirical depth.
- **Domain template (§9)**: Each domain analysis uses the standardized five-step CIF-AD-OODA template from `09b_cif_ad_ooda_methodology.md`.
- **No Part 4 sibling**: This project absorbs Part 4 entirely. Do not reference `cogsec_multiagent_4_applications` as a sibling — it no longer exists.
