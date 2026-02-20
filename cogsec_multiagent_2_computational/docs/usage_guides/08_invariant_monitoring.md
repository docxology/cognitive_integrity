# Invariant Monitoring Usage Guide

## Concept

**Invariant Monitoring** enforces strict logical rules (invariants) that must always hold for the system to be considered safe. Unlike statistical drift detection, invariants are binary: a violation is an immediate security failure. The checker comes pre-loaded with five built-in security invariants and supports custom invariants.

Formal Definition: *Part 2, Section 3.3*

## Implementation

The core logic is implemented in `src/core/invariants.py`.

### Key Classes

- `InvariantChecker`: Engine that evaluates a context dictionary against registered invariants. Pre-loaded with 5 built-in security invariants (INV-1 through INV-5).
- `RuntimeMonitor`: Continuous monitoring service that wraps `InvariantChecker` for ongoing action monitoring with violation logging.
- `Invariant`: Dataclass — `id` (e.g., "INV-1"), `predicate` (callable returning bool), `description`, `severity` (`InvariantSeverity` enum).
- `InvariantSeverity`: IntEnum — `LOW` (1), `MEDIUM` (2), `HIGH` (3), `CRITICAL` (4).
- `InvariantViolation`: Dataclass — `invariant_id`, `description`, `severity`, `context`, `timestamp`.
- `AgentAction`: Dataclass — `agent_id`, `action_type`, `parameters`, `timestamp`. Has a `to_context()` method for invariant checking.

### Built-in Invariants

| ID | Description | Severity |
|----|-------------|----------|
| INV-1 | Never execute untrusted code | CRITICAL |
| INV-2 | Never leak credentials | CRITICAL |
| INV-3 | Never modify system files without permission | HIGH |
| INV-4 | Always verify tool outputs | MEDIUM |
| INV-5 | Delegated trust must not exceed direct trust | HIGH |

## Usage Example

```python
from core.invariants import (
    InvariantChecker, Invariant, InvariantSeverity,
    RuntimeMonitor, AgentAction,
)

# 1. Initialize checker (built-in invariants loaded by default)
checker = InvariantChecker(load_builtins=True)

# 2. Add a custom invariant
budget_limit = Invariant(
    id="INV-BUDGET",
    predicate=lambda ctx: ctx.get("spend", 0) <= 1000,
    description="Spending must not exceed $1000",
    severity=InvariantSeverity.CRITICAL,
)
checker.add_invariant(budget_limit)

# 3. Check all invariants against a context
safe_context = {
    "action_type": "read_data",
    "spend": 500,
    "is_trusted": True,
}
violations = checker.check_all(safe_context)
if not violations:
    print("All invariants satisfied.")

# 4. Detect a violation
unsafe_context = {
    "action_type": "execute_code",
    "code_source": "untrusted",
    "spend": 5000,  # Over budget!
    "is_trusted": False,
}
violations = checker.check_all(unsafe_context)
for v in violations:
    print(f"VIOLATION: {v.invariant_id} — {v.description} "
          f"(severity: {v.severity.name})")

# 5. Check a single invariant
result = checker.check_single("INV-BUDGET", {"spend": 1500})
if result:
    print(f"Single check failed: {result.invariant_id}")

# 6. Use RuntimeMonitor for continuous monitoring
monitor = RuntimeMonitor(checker=checker)

action = AgentAction(
    agent_id="Agent_1",
    action_type="write_file",
    parameters={"path": "/etc/config", "is_system_file": True},
)
new_violations = monitor.monitor_action(action)

# Query monitoring stats
stats = monitor.get_stats()
print(f"Total actions: {stats['total_actions']}, Violations: {stats['total_violations']}")

# Filter violations by severity
critical = monitor.get_violations_by_severity(InvariantSeverity.CRITICAL)
```

## Testing

The invariants module is tested in `tests/test_invariants.py`, covering:

- Built-in invariant evaluation (INV-1 through INV-5).
- Custom invariant registration and removal.
- Severity-based violation filtering.
- RuntimeMonitor action monitoring and logging.
- AgentAction context conversion.

Run tests:

```bash
pytest tests/test_invariants.py -v
```
