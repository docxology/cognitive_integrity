---
name: cogsec-multiagent-1-theory
description: Cognitive Integrity Framework — Part 1 theoretical foundations (trust calculus, cognitive firewall, tripwire, provenance, consensus, invariants)
triggers:
  - when: "user mentions 'Part 1' or 'theoretical foundations' or 'CIF theory'"
    action: "route to this project"
  - when: "task involves trust calculus, defense composition algebra, or adversary taxonomy"
    action: "direct to this project"
version: 1.0.0
author: Daniel Ari Friedman
license: MIT
---

# Cognitive Integrity Framework — Part 1 (Theory)

## Purpose

This skill directs LLM agents to the **Part 1** project of the Cognitive Security for Multiagent Operators series. Part 1 defines the formal foundations:

- Trust Calculus with bounded delegation and exponential decay
- Cognitive Firewall (three-tier classification: ACCEPT/QUARANTINE/REJECT)
- Tripwire system (canary beliefs for drift detection)
- Provenance tracking (taint propagation)
- Byzantine-tolerant consensus
- Behavioral invariants

## When to Use

Invoke this skill when:
- User asks about theoretical underpinnings or formal definitions
- Task requires understanding of defense mechanisms composition
- Work involves adversary taxonomy (Ω₁–Ω₅) or threat modeling
- Need reference implementations of core CIF modules
- Generating figures from the theory part (trust calculus, firewall pipeline, tripwire, etc.)

## Key Files

- `src/trust.py` — Bounded trust delegation with decay
- `src/firewall.py` — Multi-stage input classification
- `src/tripwire.py` — Canary belief monitoring
- `src/provenance.py` — Information flow tracking
- `src/consensus.py` — Byzantine-tolerant agreement
- `src/invariants.py` — Runtime invariant checking
- `src/detection.py` — Anomaly and drift detection
- `src/visualization/` — 20 figure modules for manuscript
- `manuscript/` — Part 1 paper (9 sections, 4 appendices)

## Commands

```bash
# Render PDF
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_1_theory

# Run tests
uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/ -q

# Generate figures only
uv run python projects/cognitive_integrity/cogsec_multiagent_1_theory/scripts/generate_figures.py
```

## Cross-Part Discipline

- Part 2 (computational) validates these claims empirically; defer to Part 2 for data-backed performance numbers.
- Part 3 (practical) translates these mechanisms into deployment guidance.
- Part 3+4 (unified practical and applications paper) applies these across domains.

All definitions live here; downstream parts import and reuse.
