# Formal Verification - Agent Reference

Theorem validation and model checker specifications.

## Modules

### theorem_registry.py

Central registry of security theorems.

**Key Classes:**

- `TheoremRegistry` - Stores and retrieves theorems
- `Theorem` - Theorem with proof status

### trust_bounds.py

Trust bound proofs.

**Key Functions:**

- `prove_trust_bounded()` - Trust always in [0,1]
- `prove_delegation_decay()` - Delegation reduces trust

### byzantine_guarantees.py

Byzantine fault tolerance proofs.

**Key Functions:**

- `prove_consensus_safety()` - n >= 3f+1 guarantees
- `prove_quorum_liveness()` - Quorum completion

### composition_proofs.py

Defense composition proofs.

### latency_bound.py

Latency bound analysis.

### stealth_impact.py

Stealth attack impact analysis.

### tla_spec.py

TLA+ specifications.

### spin_spec.py

SPIN model specifications.

### nusmv_spec.py

NuSMV model specifications.

## Usage

```python
from src.formal import TheoremRegistry

registry = TheoremRegistry.load_default()
theorem = registry.get("trust_bounded")
result = theorem.verify()
```
