# Cognitive Security Source Modules - Quick Reference

Core implementations for the Cognitive Integrity Framework (CIF).

## Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `trust.py` | Trust calculus with decay | `TrustCalculus`, `TrustMatrix`, `ReputationTracker` |
| `firewall.py` | Input classification | `CognitiveFirewall`, `PatternDetector`, `Classification` |
| `consensus.py` | Byzantine agreement | `ByzantineConsensus`, `QuorumVerification`, `Vote` |
| `tripwire.py` | Canary monitoring | `CognitiveTripwire`, `Canary`, `TripwireAlert` |
| `provenance.py` | Information flow | `ProvenanceChain`, `TaintLabel`, `CausalAttribution` |
| `detection.py` | Anomaly detection | `DriftDetector`, `AnomalyScorer`, `DetectionConfig` |
| `invariants.py` | Behavioral checking | `InvariantChecker`, `RuntimeMonitor`, `AgentAction` |
| `sandbox.py` | Belief partitioning | `SandboxManager`, `BeliefState`, `PromotionCriteria` |

## Quick Usage

### Trust Evaluation
```python
from src.trust import TrustCalculus
calc = TrustCalculus()
trust = calc.compute_trust(base_trust=0.8, reputation=0.9, context_trust=0.7)
```

### Firewall Classification
```python
from src.firewall import CognitiveFirewall, Classification
fw = CognitiveFirewall()
result = fw.classify("Hello world")  # Classification.ACCEPT
```

### Byzantine Consensus
```python
from src.consensus import ByzantineConsensus, Vote
consensus = ByzantineConsensus(n_agents=7)
consensus.submit_vote(Vote("agent-0", "prop", 0.9))
```

### Tripwire Detection
```python
from src.tripwire import CognitiveTripwire
tw = CognitiveTripwire()
tw.add_identity_canary("agent-1")
alerts = tw.check({"I am agent agent-1": 0.3})  # Returns alerts
```

## Dependencies

- `numpy>=1.22` - Numerical computations for trust matrices and statistics
- Standard library: `dataclasses`, `datetime`, `enum`, `re`, `logging`

## All modules follow the thin orchestrator pattern - they implement algorithms, scripts coordinate.
