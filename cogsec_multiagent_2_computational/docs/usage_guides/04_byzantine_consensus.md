# Byzantine Consensus Usage Guide

## Concept

**Byzantine Consensus** enables a group of agents to reach reliable agreement even if some agents are compromised (Byzantine) or faulty. The protocol guarantees safety and liveness provided that $n \geq 3f + 1$, where $n$ is the total number of agents and $f$ is the number of faulty agents.

Formal Definition: *Part 1, Section 5.4, Theorem 5.2*

## Implementation

The core logic is implemented in `src/core/consensus.py`.

### Key Classes

- `ByzantineConsensus`: Standard BFT consensus protocol.
- `WeightedByzantineConsensus`: Trust-weighted consensus where high-trust agents have more voting power.

## Usage Example

```python
from src.core.consensus import ByzantineConsensus

# 1. Initialize Consensus
# System with 4 agents, tolerating f=1 fault (4 >= 3*1 + 1)
agents = ["Agent_1", "Agent_2", "Agent_3", "Agent_4"]
consensus = ByzantineConsensus(participants=agents)

# 2. Propose a Value
# Agent_1 proposes "ACTION_X"
proposition_id = "prop_123"
consensus.propose(proposer="Agent_1", value="ACTION_X", proposal_id=proposition_id)

# 3. Collect Votes
# Honest agents vote based on their local validation
consensus.cast_vote(voter="Agent_2", proposal_id=proposition_id, vote=True)
consensus.cast_vote(voter="Agent_3", proposal_id=proposition_id, vote=True)
consensus.cast_vote(voter="Agent_4", proposal_id=proposition_id, vote=False) # Disagrees

# 4. Check Result
# Needs 2/3 majority (approx 3 votes for n=4, or strict supermajority logic)
result = consensus.compute_result(proposal_id=proposition_id)

if result.status == "COMMITTED":
    print(f"Consensus Reached: {result.value}")
elif result.status == "ABORTED":
    print("Consensus Failed.")
else:
    print("Pending more votes.")
```

## Testing

The consensus module is tested in `tests/core/test_consensus.py`, covering:

- Agreement in the presence of faults.
- Liveness (reaching a decision).
- Sybil attack resilience (in weighted version).

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_consensus.py
```
