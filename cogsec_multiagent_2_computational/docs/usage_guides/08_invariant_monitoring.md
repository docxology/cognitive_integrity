# Invariant Monitoring Usage Guide

## Concept

**Invariant Monitoring** enforces strict logical rules (invariants) that must effectively always be true for the system to be considered safe. Unlike statistical drift detection, invariants are binary: a violation is an immediate security failure.

Formal Definition: *Part 2, Section 3.3 (Auxiliary)*

## Implementation

The core logic is implemented in `src/core/invariants.py`.

### Key Classes

- `InvariantChecker`: Engine that evaluates state against defined rules.
- `RuntimeMonitor`: Service that runs the checker continuously.
- `Invariant`: Data class defining a rule (predicate).

## Usage Example

```python
from src.core.invariants import InvariantChecker, Invariant

# 1. Define Invariants
# Lambda function returns True if safe, False if violated
inv_budget = Invariant(
    name="Budget_Limit",
    predicate=lambda state: state['metrics']['spend'] <= 1000,
    severity="CRITICAL"
)

inv_uptime = Invariant(
    name="System_Active",
    predicate=lambda state: state['status'] != "CRASHED",
    severity="CRITICAL"
)

# 2. Initialize Checker
checker = InvariantChecker(invariants=[inv_budget, inv_uptime])

# 3. Check System State
safe_state = {
    "metrics": {"spend": 500},
    "status": "Running"
}

violations = checker.check(safe_state)
if not violations:
    print("All invariants satisfied.")

# 4. Detect Violation
unsafe_state = {
    "metrics": {"spend": 5000}, # Violation!
    "status": "Running"
}

violations = checker.check(unsafe_state)
for v in violations:
    print(f"VIOLATION: {v.invariant_name} - Severity: {v.severity}")
    # Trigger failsafe
```

## Testing

The invariants module is tested in `tests/core/test_invariants.py`, covering:

- Predicate evaluation.
- Severity levels.
- Batch processing of multiple invariants.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_invariants.py
```
