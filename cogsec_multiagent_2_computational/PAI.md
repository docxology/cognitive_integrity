# PAI.md - Cognitive Security Computational Validation Context

## Purpose
Part 2 of the **Cognitive Security for Multiagent Operators** series. This project provides computational validation of the Cognitive Integrity Framework (CIF).

## PAI Integration Points

### Skill Compatibility
- **Security Benchmarking**: Attack corpus for testing PAI agent resilience
- **Implementation Reference**: Defense mechanism implementations
- **Statistical Validation**: Significance testing methodology

### Key Modules for PAI Use
| Module | PAI Application |
|--------|-----------------|
| `trust.py` | Agent trust scoring implementation |
| `firewall.py` | Input classification defense |
| `consensus.py` | Multi-agent decision validation |
| `tripwire.py` | Belief monitoring implementation |
| `provenance.py` | Information flow tracking |
| `detection.py` | Behavioral anomaly detection |
| `invariants.py` | Runtime constraint enforcement |
| `sandbox.py` | Belief state partitioning |

### Example PAI Usage
```python
from projects.cogsec_multiagent_2_computational.src import (
    TrustCalculus, CognitiveFirewall, ByzantineConsensus
)

# Full defense stack
firewall = CognitiveFirewall()
trust_calc = TrustCalculus()
consensus = ByzantineConsensus(n_agents=7)
```

## Agent Guidelines
- **Test Coverage**: 90%+ coverage required
- **No Mocks**: Tests use real computations only
- **Reproducible**: Fixed seeds for deterministic results
- **Notation**: Follow Paper 1 canonical notation
