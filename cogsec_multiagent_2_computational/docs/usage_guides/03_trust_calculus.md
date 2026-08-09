# Trust Calculus Usage Guide

## Concept

The **Trust Calculus** manages dynamic trust relationships between agents. It computes composite trust scores from three weighted components — **base trust**, **reputation**, and **context trust** — and implements **Bounded Delegation** ($\delta^d$), which mathematically guarantees that trust cannot be inflated through long delegation chains.

Formal Definition: *Part 1, Section 4, Theorem 4.2*

## Implementation

The core logic is implemented in `src/core/trust.py`.

### Key Classes

- `TrustCalculus`: Computes composite trust via $T = \alpha \cdot T_{base} + \beta \cdot T_{rep} + \gamma \cdot T_{ctx}$ and bounded delegation via $T_{del} = \min(T_{i \to j}, T_{j \to k}) \cdot \delta^d$.
- `TrustConfig`: Dataclass controlling weights — `alpha` (default 0.3), `beta` (default 0.5), `gamma` (default 0.2), `decay` (default 0.8). Enforces $\alpha + \beta + \gamma = 1$.
- `TrustMatrix`: Pairwise trust management for N agents with efficient updates and delegation queries.
- `ReputationTracker`: History-based reputation with exponential time decay.

## Usage Example

```python
from core.trust import TrustCalculus, TrustConfig, TrustMatrix

# 1. Configure trust weights
config = TrustConfig(
    alpha=0.3,   # Base trust weight
    beta=0.5,    # Reputation weight
    gamma=0.2,   # Context trust weight
    decay=0.8,   # Balanced-profile delegation decay factor (delta)
)

# 2. Initialize Trust Calculus
tc = TrustCalculus(config=config)

# 3. Compute composite trust score
trust = tc.compute_trust(
    base_trust=0.7,      # Direct trust T_base
    reputation=0.9,      # Historical reputation T_rep
    context_trust=0.6,   # Task-specific context T_ctx
)
print(f"Composite trust: {trust:.3f}")
# = 0.3*0.7 + 0.5*0.9 + 0.2*0.6 = 0.21 + 0.45 + 0.12 = 0.78

# 4. Compute bounded delegation
# Agent A trusts B (0.9). B trusts C (0.85). Depth = 1 hop.
t_delegated = tc.delegate_trust(
    source_trust=0.9,
    target_trust=0.85,
    depth=1,
)
print(f"Delegated trust (A→C via B): {t_delegated:.3f}")
# = min(0.9, 0.85) * 0.8^1 = 0.85 * 0.8 = 0.68

# 5. Compute trust along a multi-hop path
path_trust = tc.compute_path_trust([0.9, 0.85, 0.7])
print(f"Path trust (A→B→C→D): {path_trust:.3f}")

# 6. Use TrustMatrix for pairwise trust management
matrix = TrustMatrix(n_agents=4, config=config)
direct = matrix.get_trust(source=0, target=1)
print(f"Direct trust (0→1): {direct:.3f}")

# Update reputation based on observed outcome
matrix.update_reputation(source=0, target=1, outcome=0.95, learning_rate=0.1)

# Get delegated trust along a path
delegation = matrix.get_delegation_trust(path=[0, 1, 2])
print(f"Delegation trust (0→1→2): {delegation:.3f}")
```

## Testing

The trust calculus is tested in `tests/test_trust.py`, covering:

- Composite trust computation (weighted combination).
- Bounded delegation decay ($\delta^d$ monotone decrease).
- Profile convention: $\delta=0.80$ is balanced operation; $\delta=0.60$ is high assurance.
- Path trust computation.
- TrustMatrix pairwise lookups and updates.
- ReputationTracker time-based decay.

Run tests:

```bash
uv run pytest tests/test_trust.py -v
```
