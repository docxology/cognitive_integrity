# Byzantine Consensus Usage Guide

## Concept

**Byzantine Consensus** enables a group of agents to reach reliable agreement even if some agents are compromised (Byzantine) or faulty. The protocol guarantees safety and liveness provided that $n \geq 3f + 1$, where $n$ is the total number of agents and $f$ is the number of faulty agents. Voting is belief-based: each agent submits a continuous belief value $\in [0, 1]$, and consensus is reached when a supermajority agrees.

Formal Definition: *Part 1, Section 5.4, Theorem 5.2*

## Implementation

The core logic is implemented in `src/core/consensus.py`.

### Key Classes

- `ByzantineConsensus`: Standard BFT consensus with belief-based voting. Requires $n \geq 3f + 1$.
- `ConsensusConfig`: Thresholds — `acceptance_threshold` (default 0.7), `rejection_threshold` (default 0.3), `quorum_fraction` (default 2/3).
- `Vote`: Dataclass — `agent_id`, `proposition` (string), `belief` (float $\in [0,1]$), `timestamp`.
- `ConsensusResult`: Enum — `ACCEPT`, `REJECT`, `UNDECIDED`.
- `WeightedByzantineConsensus`: Trust-weighted variant where high-trust agents have proportionally more voting power.
- `QuorumVerification`: Quorum-based action approval requiring $q = \lceil (n + f + 1) / 2 \rceil$ approvals.

## Usage Example

```python
from core.consensus import (
    ByzantineConsensus, ConsensusConfig, Vote, ConsensusResult
)

# 1. Initialize consensus
# 4 agents, tolerating f=1 fault (4 >= 3*1 + 1 ✓)
consensus = ByzantineConsensus(
    n_agents=4,
    max_byzantine=1,
    config=ConsensusConfig(acceptance_threshold=0.7),
)

# 2. Submit votes as belief values
# Agents vote on a proposition with a belief confidence in [0, 1]
consensus.submit_vote(Vote(agent_id="Agent_1", proposition="deploy_v2", belief=0.95))
consensus.submit_vote(Vote(agent_id="Agent_2", proposition="deploy_v2", belief=0.88))
consensus.submit_vote(Vote(agent_id="Agent_3", proposition="deploy_v2", belief=0.92))
consensus.submit_vote(Vote(agent_id="Agent_4", proposition="deploy_v2", belief=0.20))  # Dissenter

# 3. Compute consensus
result, confidence = consensus.compute_consensus("deploy_v2")

if result == ConsensusResult.ACCEPT:
    print(f"Consensus ACCEPTED with confidence {confidence:.2f}")
elif result == ConsensusResult.REJECT:
    print("Consensus REJECTED.")
else:
    print("UNDECIDED — need more votes or stronger agreement.")

# 4. Inspect vote distribution
dist = consensus.get_vote_distribution("deploy_v2")
print(f"Votes: accept={dist['accept']}, reject={dist['reject']}, uncertain={dist['uncertain']}")

# 5. Get consensus belief value (weighted average if accepted)
belief = consensus.get_belief("deploy_v2")
print(f"Consensus belief: {belief:.2f}")

# 6. Reset for a new proposition
consensus.reset(proposition="deploy_v2")
```

## Testing

The consensus module is tested in `tests/test_consensus.py`, covering:

- Agreement in the presence of Byzantine faults.
- Liveness (reaching a decision with honest supermajority).
- Quorum verification thresholds.
- Weighted consensus with trust scores.
- Edge cases (unanimous, split, single-agent).

Run tests:

```bash
uv run pytest tests/test_consensus.py -v
```
