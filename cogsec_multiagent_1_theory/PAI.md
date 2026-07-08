# PAI.md - Cognitive Security Multiagent Context

## Purpose
This project implements the **Cognitive Integrity Framework (CIF)** - a formal security architecture for multiagent AI systems.

## PAI Integration Points

### Skill Compatibility
- **Security Analysis**: CIF modules can augment PAI security validation
- **Trust Calculus**: Applicable to PAI agent delegation patterns
- **Anomaly Detection**: Behavioral monitoring for PAI agent systems

### Key Modules for PAI Use
| Module | PAI Application |
|--------|-----------------|
| `trust.py` | Agent trust scoring and delegation bounds |
| `firewall.py` | Input classification for prompt injection defense |
| `consensus.py` | Multi-agent decision agreement |
| `tripwire.py` | Canary belief monitoring |
| `provenance.py` | Information flow tracking |
| `detection.py` | Behavioral anomaly detection |
| `invariants.py` | Runtime invariant checking |
| `sandbox.py` | Belief state partitioning |

### Example PAI Usage
```python
# After installing the package (pip install -e ".[dev]" from this project root)
from src.trust import TrustCalculus
from src.firewall import CognitiveFirewall

# Validate external input
firewall = CognitiveFirewall()
classification = firewall.classify(external_input)

# Calculate agent trust
calc = TrustCalculus()
trust = calc.compute_trust(base=0.8, reputation=0.9, context=0.7)
```

## Agent Guidelines
- **Security-Critical**: All modifications require test coverage
- **No Mocks**: Tests use real computations only
- **Bounded Values**: All scores in [0, 1] range
- **Fail-Safe**: Unknown inputs treated as untrusted
