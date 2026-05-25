---
name: cogsec-multiagent-4-applications
description: Cognitive Integrity Framework — Part 4 cross-domain applications (CIF-AD-OODA, ten-domain analysis, real-world incident retrospectives)
triggers:
  - when: "user mentions 'Part 4' or 'applications' or 'domain' or 'CIF-AD-OODA'"
    action: "route to this project"
  - when: "task involves applying CIF to specific operational domains or incident analysis"
    action: "direct to this project"
version: 1.0.0
author: Daniel Ari Friedman
license: MIT
---

# Cognitive Integrity Framework — Part 4 (Applications)

## Purpose

This skill directs LLM agents to **Part 4** of the Cognitive Security for Multiagent Operators series. Part 4 applies the CIF framework across ten operational domains and provides:

- Domain-specific attack surface analysis
- Universal attack pattern catalog (the Ω attack taxonomies)
- CIF-AD-OODA integration model (defense cycles embedded in OODA loops)
- Real-world 2024–2025 incident retrospectives
- Cross-domain validation of CIF generality

## When to Use

Invoke this skill when:
- User asks how CIF applies to a specific domain (finance, healthcare, cybersecurity, etc.)
- Task involves analyzing an AI-agent incident through the CIF lens
- Writing domain-specific deployment guidance or threat models
- Mapping CDF mechanisms onto OODA (Observe-Orient-Decide-Act) loops
- Extending the ten-domain analysis or adding new domains

## Key Files

- `src/identity.py` — Package identity marker (Part 4 codebase is lightweight; manuscript is primary artifact)
- `manuscript/` — Full paper with domain applications and incident retrospectives

## Manuscript Structure

```
manuscript/
├── 00_abstract.md
├── 01_introduction.md          # Part 4 role in series; CIF-AD-OODA overview
├── 02_methodology.md           # Five-step domain analysis template
├── 03_domain_analysis.md       # Ten-domain categorization
├── 04_incident_retrospectives.md  # 2024-2025 real-world incidents
├── 05_universal_attack_patterns.md # Cross-domain attack motifs
├── 06_future_work.md
├── 97_appendices.md
├── 98_glossary.md
├── 99_references.md
└── S01_notation_reference.md   # Symbol table (consolidated across all parts)
```

## Domains Covered

1. Cybersecurity Operations
2. Financial Trading & Compliance
3. Healthcare & Clinical Decision Support
4. Scientific Research Automation
5. Software Engineering & DevOps
6. Content Moderation & Trust & Safety
7. Autonomous Vehicles & Robotics
8. Legal & Contract Analysis
9. Education & Tutoring
10. Government & Intelligence

## Commands

```bash
# Render PDF
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_4_applications

# Run tests (currently minimal, Part 4 is manuscript-centric)
uv run pytest projects/cognitive_integrity/cogsec_multiagent_4_applications/tests/ -q
```

## Cross-Part Discipline

- **Definitions** from Part 1 (CIF mechanisms, adversary taxonomy Ω₁–Ω₅)
- **Empirical backing** from Part 2 (performance ceiling, attack corpus)
- **Operational templates** from Part 3 (deployment playbooks)
- Part 4 ties it all together by showing how the same formalism maps onto diverse problem spaces.

## Agent Guidelines

Agents contributing to Part 4 must:

1. **Follow the five-step template** from `manuscript/02_methodology.md` for each domain:
   - Operational characterization
   - Attack surface analysis
   - Transient coupling assessment
   - Defense mapping (which CIF mechanisms apply)
   - Validation anchoring (tie to Part 2 empirical results where possible)

2. **Use consistent symbol set** — reference `manuscript/S01_notation_reference.md` for canonical notation.

3. **Cite Parts 1–2 appropriately**:
   - Part 1: formal definitions (trust calculus, firewall, etc.)
   - Part 2: empirical efficacy (mention "94–100% at parametric ceiling" only when referring to mature adapters; be precise about architecture counts: 4 headline architectures in main manuscript, 6 implementations total)

4. **Keep real-world incident analysis evidence-based** — link to known public incidents (2024–2025); avoid speculation.

5. **Expand code only if needed** — Part 4's artifact is primarily the manuscript; `src/identity.py` is the placeholder. New implementations should live in Part 2 unless domain-specific logic is truly novel.

## Development Status

- Manuscript is the primary deliverable (≈21 markdown sections).
- Codebase is intentionally minimal; implementations reuse Parts 1–2.
- Test suite is placeholder (one identity check).
- Future work: domain-specific benchmarks or case study datasets may populate `src/` as they mature.
