# Trust Calculus Usage Guide

## Concept

The **Trust Calculus** manages dynamic trust relationships between agents. It updates trust scores based on interaction outcomes and implements **Bounded Delegation** ($\delta^d$), which mathematically guarantees that trust cannot be inflated through long delegation chains.

Formal Definition: *Part 1, Section 4, Theorem 4.2*

## Implementation

The core logic is implemented in `src/core/trust.py`.

### Key Classes

- `TrustCalculus`: Computes composite trust scores from base, reputation, and context components.
- `TrustMatrix`: Efficient lookup table for pairwise agent trust.
- `ReputationTracker`: Tracks history-based reputation with time decay.

## Usage Example

```python
from src.core.trust import TrustCalculus, TrustMatrix

# 1. Initialize Trust Calculus
# - decay_factor (delta): How much trust degrades per delegation hop (0.0-1.0)
trust_engine = TrustCalculus(delegation_decay=0.8) 

# 2. Delegate Trust
# Agent A trusts B (0.9). B trusts C (0.9).
# What is A's transitive trust in C?
t_a_b = 0.9
t_b_c = 0.9
depth = 2

# T_transitive = min(t_ab, t_bc) * delta^(depth-1)
#              = 0.9 * 0.8^1 = 0.9 * 0.8 = 0.72
t_transitive = trust_engine.delegate_trust(
    source_trust=t_a_b,
    target_trust=t_b_c,
    depth=depth
)
print(f"Transitive Trust (A->C): {t_transitive:.2f}")

# 3. Update Trust based on Interaction
# Agent A delegates a task to B. B succeeds.
current_trust = 0.5
outcome = "SUCCESS"  # or "FAILURE"

new_trust = trust_engine.update_trust(
    current_trust=current_trust,
    outcome=outcome,
    weight=0.1
)
print(f"Updated Trust: {new_trust:.2f}")
```

## Testing

The trust calculus is tested in `tests/core/test_trust.py`, covering:

- Delegation decay math.
- Reputation updates.
- Matrix limits and lookups.
- Trust erosion on failure.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_trust.py
```
