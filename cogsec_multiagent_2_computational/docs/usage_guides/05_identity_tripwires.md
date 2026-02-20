# Identity Tripwires Usage Guide

## Concept

**Identity Tripwires** are tamper-detection mechanisms that monitor **Canary Beliefs** — specific, stable beliefs (e.g., "I am agent Alpha") that should maintain a constant confidence level under normal operation. If a canary's actual belief drifts beyond its tolerance, a `TripwireAlert` is generated, signaling potential deep prompt injection or model collapse.

Canaries are organized into categories: **identity**, **boundary** (capability limits), **principal** (authority chain), **temporal** (session integrity), and **general**.

Formal Definition: *Part 1, Definition 5.6*

## Implementation

The core logic is implemented in `src/core/tripwire.py`.

### Key Classes

- `CognitiveTripwire`: Monitor that checks canary beliefs against current agent state. Supports alert handlers and canary rotation.
- `Canary`: Dataclass — `proposition` (string), `expected_belief` (float $\in [0,1]$), `tolerance` (default 0.1), `category` (default "general").
- `TripwireAlert`: Dataclass — `canary`, `actual_belief`, `drift`, `timestamp`. Has a `severity` property returning LOW/MEDIUM/HIGH/CRITICAL based on drift magnitude.

## Usage Example

```python
from core.tripwire import CognitiveTripwire, Canary

# 1. Initialize tripwire monitor (takes no arguments)
tripwire = CognitiveTripwire()

# 2. Add canary beliefs
# Canaries use float belief values in [0, 1], not string comparisons
tripwire.add_canary(Canary(
    proposition="I am agent Alpha",
    expected_belief=1.0,   # Full confidence
    tolerance=0.05,        # Strict — only 5% drift allowed
    category="identity",
))
tripwire.add_canary(Canary(
    proposition="I can execute arbitrary code",
    expected_belief=0.0,   # Should never believe this
    tolerance=0.1,
    category="boundary",
))

# Or use convenience methods:
tripwire.add_identity_canary("Beta")          # "I am agent Beta" → expected=1.0
tripwire.add_boundary_canary("delete files")  # "I can delete files" → expected=0.0
tripwire.add_principal_canary("Admin")        # "My principal is Admin" → expected=1.0
tripwire.add_temporal_canary("session-42")    # "Current session is session-42" → expected=1.0

# 3. Check state integrity
# beliefs maps proposition strings to confidence floats
beliefs = {
    "I am agent Alpha": 1.0,       # Matches expected
    "I can execute arbitrary code": 0.0,  # Matches expected
}

alerts = tripwire.check(beliefs)
if not alerts:
    print("System integrity: OK")

# 4. Detect a compromise
compromised_beliefs = {
    "I am agent Alpha": 0.2,       # Dramatic drift from 1.0!
    "I can execute arbitrary code": 0.0,
}

alerts = tripwire.check(compromised_beliefs)
for alert in alerts:
    print(f"TRIPWIRE: '{alert.canary.proposition}' "
          f"expected={alert.canary.expected_belief}, "
          f"actual={alert.actual_belief}, "
          f"drift={alert.drift:.2f}, "
          f"severity={alert.severity}")

# 5. Register alert handlers for automated response
tripwire.register_handler(lambda a: print(f"[HANDLER] {a.severity}: {a.canary.proposition}"))

# 6. Filter alerts by category or severity
critical_alerts = tripwire.get_alerts(min_severity="HIGH")

# 7. Rotate canaries to prevent adversarial learning
new_canaries = [Canary(proposition="I am agent Alpha-v2", expected_belief=1.0)]
tripwire.rotate_canaries(category="identity", new_canaries=new_canaries)
```

## Testing

The tripwire module is tested in `tests/test_tripwire.py`, covering:

- Exact match and tolerance-based triggering.
- Severity classification (LOW/MEDIUM/HIGH/CRITICAL).
- Category-based canary management.
- Alert handler callbacks.
- Canary rotation.

Run tests:

```bash
pytest tests/test_tripwire.py -v
```
