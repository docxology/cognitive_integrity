# Belief Sandbox Usage Guide

## Concept

The **Belief Sandbox** partitions agent memory into "Verified" and "Provisional" states. It ensures that unverified information from low-trust sources cannot corrupt the agent's core knowledge base. Information is held in a provisional sandbox until it meets specific **Promotion Criteria** (e.g., multi-source corroboration, trust threshold, or verification challenge).

Formal Definition: *Part 1, Definition 5.4, Property 5.2*

## Implementation

The core logic is implemented in `src/core/sandbox.py`.

### Key Classes

- `SandboxManager`: Manages the two partitions and handles add/promote operations.
- `BeliefPartition`: Data structure for holding beliefs (Verified vs. Provisional).
- `PromotionCriteria`: Logic defining when a belief can be promoted.

## Usage Example

```python
from src.core.sandbox import SandboxManager, PromotionCriteria

# 1. Initialize the Sandbox Manager
# Define promotion criteria: requires 2 independent sources OR high trust score (>0.9)
criteria = PromotionCriteria(
    min_corroboration=2,
    min_trust_score=0.9
)
sandbox = SandboxManager(promotion_criteria=criteria)

# 2. Add a belief from a source
belief_content = "Stock price of ACME is $150."
source_agent = "Agent_B"
source_trust = 0.6 # Medium trust

# This will go to PROVISIONAL partition because trust < 0.9
status = sandbox.add_belief(
    content=belief_content,
    source=source_agent,
    trust_score=source_trust
)
print(f"Belief Status: {status}") # "PROVISIONAL"

# 3. Corroborate from a second source
# This triggers promotion because min_corroboration=2 is met
status_update = sandbox.add_belief(
    content=belief_content,
    source="Agent_C",
    trust_score=0.7
)
print(f"Belief Status Update: {status_update}") # "VERIFIED"

# 4. Access Verified Beliefs
verified_beliefs = sandbox.get_verified_beliefs()
print("Verified Knowledge Base:", verified_beliefs)
```

## Testing

The sandbox is tested in `tests/core/test_sandbox.py`, covering:

- Partition separation.
- Trusted source promotion.
- Corroboration counting.
- TTL (Time-To-Live) expiry for provisional beliefs.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_sandbox.py
```
