# Belief Sandbox Usage Guide

## Concept

The **Belief Sandbox** partitions agent memory into **Verified** and **Provisional** states. Unverified information from low-trust sources is held in the provisional partition until it meets specific **Promotion Criteria** (confidence threshold, corroboration count, or minimum age). Provisional beliefs expire via configurable TTL (Time-To-Live) to prevent stale unverified data from accumulating.

Formal Definition: *Part 1, Definition 5.4, Property 5.2*

## Implementation

The core logic is implemented in `src/core/sandbox.py`.

### Key Classes

- `SandboxManager`: Top-level manager coordinating belief state, promotion criteria, and TTL expiration.
- `BeliefState`: Manages two internal partitions (verified/provisional) with promote/demote operations.
- `BeliefPartition`: Enum with values `VERIFIED` and `PROVISIONAL`.
- `Belief`: Dataclass representing a belief — `belief_id`, `content`, `confidence`, `source_agent`, `corroboration_count`, `created_at`, `metadata`.
- `PromotionCriteria`: Defines when a belief can be promoted — `min_confidence` (default 0.8), `min_corroborations` (default 0), `min_age_seconds` (default 0.0), plus optional `custom_check` callable.
- `SandboxConfig`: TTL and capacity settings — `default_ttl_seconds` (default 3600), `max_provisional_beliefs`, `auto_cleanup_interval`.

## Usage Example

```python
from core.sandbox import (
    SandboxManager, SandboxConfig, PromotionCriteria, Belief, BeliefPartition
)

# 1. Configure promotion criteria
criteria = PromotionCriteria(
    min_confidence=0.8,       # Belief confidence must be >= 0.8
    min_corroborations=2,     # Must be corroborated by 2+ sources
    min_age_seconds=0.0,      # No minimum age requirement
)

# 2. Configure sandbox TTL
config = SandboxConfig(
    default_ttl_seconds=3600,      # Provisional beliefs expire after 1 hour
    max_provisional_beliefs=1000,
)

# 3. Initialize
sandbox = SandboxManager(config=config, promotion_criteria=criteria)

# 4. Add a provisional belief
belief = Belief(
    belief_id="b-001",
    content="Stock price of ACME is $150.",
    confidence=0.6,
    source_agent="Agent_B",
)
sandbox.add_provisional(belief, ttl_seconds=1800)  # Custom 30-min TTL

# Check partition
partition = sandbox.state.get_partition("b-001")
print(f"Belief partition: {partition}")  # BeliefPartition.PROVISIONAL

# 5. Manually promote a belief (e.g., after corroboration)
sandbox.promote("b-001")

# 6. Access verified beliefs
verified = sandbox.state.verified
print(f"Verified beliefs: {[b.content for b in verified]}")

# 7. Cleanup expired provisional beliefs
expired_ids = sandbox.cleanup_expired()
print(f"Expired beliefs removed: {expired_ids}")
```

## Testing

The sandbox is tested in `tests/test_sandbox.py`, covering:

- Partition separation (verified vs. provisional).
- Promotion criteria evaluation (confidence, corroboration, age, custom predicates).
- TTL expiry and automatic cleanup.
- Demote operations (verified → provisional).
- Max provisional capacity enforcement.

Run tests:

```bash
pytest tests/test_sandbox.py -v
```
