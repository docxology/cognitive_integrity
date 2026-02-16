# Provenance Tracking Usage Guide

## Concept

**Provenance Tracking** maintains a causal history for every belief in the system. It answers the question "Where did this information come from?" and enables the system to:

1. Trace errors back to their source.
2. Invalidate trees of beliefs if a root source is found to be compromised.
3. Compute "Taint" propagation for untrusted inputs.

Formal Definition: *Part 2, Section 3.2 (Auxiliary)*

## Implementation

The core logic is implemented in `src/core/provenance.py`.

### Key Classes

- `ProvenanceGraph`: Directed Acyclic Graph (DAG) storing belief dependencies.
- `ProvenanceChain`: Linear history for simple beliefs.
- `CausalAttribution`: Logic for assigning credit/blame to sources.

## Usage Example

```python
from src.core.provenance import ProvenanceGraph

# 1. Initialize Graph
graph = ProvenanceGraph()

# 2. Record Event/Belief
# node_id: unique ID for the information
# sources: list of IDs that contributed to this info
graph.add_node(
    node_id="belief_101",
    content="Sky is blue",
    source_agent="Sensor_A"
)

# 3. Record Derived Information
graph.add_node(
    node_id="belief_102",
    content="Sky is blue AND clear",
    source_agent="Logic_Module",
    dependencies=["belief_101"] # Derived from belief_101
)

# 4. Trace Provenance
# Get all ancestors of belief_102
history = graph.get_ancestry("belief_102")
print("Ancestry:", history) 
# Output: ['belief_101']

# 5. Handle Source Compromise
# If Sensor_A is hacked, what is affected?
affected_nodes = graph.get_descendants_of_source("Sensor_A")
print("Compromised Nodes:", affected_nodes)
# Output: ['belief_101', 'belief_102']
```

## Testing

The provenance module is tested in `tests/core/test_provenance.py`, covering:

- Graph construction.
- Ancestry/Descendant queries.
- Cycle detection (preventing loops).

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_provenance.py
```
