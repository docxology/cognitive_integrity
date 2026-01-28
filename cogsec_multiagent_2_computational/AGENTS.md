# Cognitive Integrity Framework: Computational Validation - Agent Reference

**This is an active project** in the `projects/` directory, discovered and executed by infrastructure discovery functions.

## Overview

Part 2 of the **Cognitive Security for Multiagent Operators** series. This project provides computational validation of the Cognitive Integrity Framework (CIF) through implementation, benchmarking, and statistical analysis.

## Key Features & Capabilities

### Defense Mechanism Implementations
- **Cognitive Firewall**: Pattern-based and semantic injection detection
- **Belief Sandbox**: Provisional belief management with TTL
- **Trust Calculus**: Bounded delegation with decay
- **Byzantine Consensus**: Fault-tolerant multi-agent agreement
- **Tripwire Detection**: Canary belief monitoring
- **Provenance Tracking**: Information flow with taint labels
- **Behavioral Invariants**: Runtime security constraint checking

### Attack Corpus (950 attacks)
- **Prompt Injection** (500): Direct, indirect, nested variants
- **Trust Exploitation** (200): Identity impersonation, delegation abuse
- **Belief Manipulation** (150): Evidence fabrication, progressive drift
- **Coordination Attacks** (100): Sybil, consensus poisoning, quorum manipulation

### Target Architectures (6 systems)
- Claude Code (hierarchical)
- AutoGPT (autonomous + plugins)
- CrewAI (role-based)
- LangGraph (graph-based)
- MetaGPT (SOP-driven)
- Camel (debate)

## Directory Structure

```
cogsec_multiagent_2_computational/
├── src/                        # Defense mechanism implementations
│   ├── __init__.py
│   ├── trust.py                # Trust calculus
│   ├── firewall.py             # Cognitive firewall
│   ├── consensus.py            # Byzantine consensus
│   ├── tripwire.py             # Canary detection
│   ├── provenance.py           # Provenance tracking
│   ├── detection.py            # Anomaly detection
│   ├── invariants.py           # Behavioral invariants
│   └── sandbox.py              # Belief sandboxing
├── scripts/                    # Figure generation (18 scripts)
│   ├── 01_attack_surface_figure.py
│   ├── 02_trust_decay_figure.py
│   ├── ...
│   ├── 06_generate_data.py     # Synthetic data generation
│   └── verify_manuscript.py    # Manuscript validation
├── tests/                      # Test suite (90%+ coverage)
│   ├── conftest.py
│   ├── test_consensus.py
│   ├── test_detection.py
│   ├── test_firewall.py
│   ├── test_invariants.py
│   ├── test_provenance.py
│   ├── test_sandbox.py
│   ├── test_tripwire.py
│   └── test_trust.py
├── manuscript/                 # Paper content
└── output/                     # Generated figures and results
```

## Testing

```bash
# Run all tests with 90%+ coverage requirement
pytest tests/ -v --cov=src --cov-fail-under=90

# Run specific module tests
pytest tests/test_trust.py -v
pytest tests/test_firewall.py -v

# Generate all figures
./run.sh --project cogsec_multiagent_2_computational --run-analysis
```

## Notation Reference

All notation follows the canonical definitions in:
- `../cogsec_multiagent_1_theory/manuscript/S06_notation.md`

Key symbols used in this paper:
- $\mathcal{T}_{i \to j}$: Trust from agent $i$ to agent $j$
- $\delta$: Trust decay factor
- $q$: Quorum threshold
- $f$: Maximum Byzantine agents

## Module Dependencies

```
firewall.py ──> detection.py (anomaly scoring)
consensus.py ──> (standalone)
trust.py ──> (standalone, uses numpy)
tripwire.py ──> (standalone, uses numpy)
provenance.py ──> (standalone)
invariants.py ──> (standalone)
sandbox.py ──> (standalone)
detection.py ──> (standalone, uses numpy)
```

## Security Considerations

- All modules implement defense-in-depth principles
- Trust scores are always bounded [0, 1]
- Delegation cannot amplify trust
- Byzantine consensus requires n >= 3f + 1
- No mock methods - all tests use real computations
