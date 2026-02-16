# Identity Tripwires Usage Guide

## Concept

**Identity Tripwires** are tamper-detection mechanisms that monitor "Canary Beliefs". These are specific, stable beliefs (e.g., "I am an AI assistant deployed by [Company]") that should never change under normal operation. If a tripwire modification is detected, it signals a potential deep prompt injection or model collapse.

Formal Definition: *Part 1, Definition 5.6*

## Implementation

The core logic is implemented in `src/core/tripwire.py`.

### Key Classes

- `CognitiveTripwire`: Monitor that scans for changes in canary beliefs.
- `Canary`: Data class representing a protected belief.

## Usage Example

```python
from src.core.tripwire import CognitiveTripwire, Canary

# 1. Define Canary Beliefs
# These are immutable facts about the agent's identity or core mission
canaries = [
    Canary(key="identity", value="Helpful Assistant", tolerance=0.0), # Exact match required
    Canary(key="model_version", value="v2.5", tolerance=0.0)
]

# 2. Initialize Tripwire Monitor
monitor = CognitiveTripwire(canaries=canaries)

# 3. Check State Integrity
# Current agent state (belief map)
current_beliefs = {
    "identity": "Helpful Assistant",
    "model_version": "v2.5",
    "status": "Active"
}

# Check returns a list of alerts (empty if safe)
alerts = monitor.check(current_beliefs)

if not alerts:
    print("System Integrity: OK")

# 4. Simulate an Attack (State Modification)
compromised_beliefs = {
    "identity": "Chaos GPT", # CHANGED!
    "model_version": "v2.5",
    "status": "Active"
}

alerts = monitor.check(compromised_beliefs)

if alerts:
    for alert in alerts:
        print(f"TRIPWIRE TRIGGERED: {alert.key} changed from '{alert.expected}' to '{alert.actual}'")
        # Trigger emergency shutdown or rollback
```

## Testing

The tripwire module is tested in `tests/core/test_tripwire.py`, covering:

- Exact match failures.
- Fuzzy matching (if tolerance > 0).
- Alert generation format.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_tripwire.py
```
