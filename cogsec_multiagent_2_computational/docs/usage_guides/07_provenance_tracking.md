# Provenance Tracking Usage Guide

## Concept

**Provenance Tracking** maintains a causal history for every belief in the system. It implements **taint propagation**: every belief inherits the trust level of its least-trusted ancestor. This enables the system to:

1. Trace errors and misinformation back to their originating source.
2. Invalidate entire trees of derived beliefs if a root source is compromised.
3. Compute effective taint levels to enforce security policies (e.g., "no untrusted data in critical decisions").

Formal Definition: *Part 2, Section 3.2*

## Implementation

The core logic is implemented in `src/core/provenance.py`.

### Key Classes

- `ProvenanceChain`: Primary data structure — a directed acyclic graph (DAG) of belief derivations with taint propagation. Supports ancestry queries and effective taint computation.
- `ProvenanceGraph`: Graph analysis wrapper around `ProvenanceChain`. Provides dependency checking, descendant queries, and contamination analysis.
- `CausalAttribution`: Identifies which untrusted sources contributed to a potentially compromised belief. Generates attribution reports.
- `TaintLabel`: Enum-like class with trust ordering — `SYSTEM_VERIFIED` (level 7, trusted), `PRINCIPAL_INPUT` (level 6), `VERIFIED_EXTERNAL` (level 5), `UNVERIFIED_EXTERNAL` (level 3), `ANONYMOUS` (level 1, untrusted), etc.
- `ProvenanceRecord`: Dataclass — `belief_id`, `content`, `source` (TaintLabel), `agent_id`, `parent_ids`, `metadata`, `timestamp`.

## Usage Example

```python
from core.provenance import (
    ProvenanceChain, ProvenanceGraph, CausalAttribution, TaintLabel
)

# 1. Initialize the provenance chain
chain = ProvenanceChain()

# 2. Record a root belief from a trusted source
chain.add_belief(
    belief_id="sensor-001",
    content="Temperature is 72°F",
    source=TaintLabel.SYSTEM_VERIFIED,
    agent_id="Sensor_A",
)

# 3. Record a derived belief (depends on the root)
chain.add_belief(
    belief_id="conclusion-001",
    content="Temperature is safe for operation",
    source=TaintLabel.PRINCIPAL_INPUT,
    agent_id="Logic_Module",
    parent_ids=["sensor-001"],  # Derived from sensor-001
)

# 4. Record a belief from an untrusted source
chain.add_belief(
    belief_id="external-001",
    content="Weather forecast says 90°F tomorrow",
    source=TaintLabel.UNVERIFIED_EXTERNAL,
    agent_id="External_API",
)

# 5. A derived belief mixing trusted and untrusted sources
chain.add_belief(
    belief_id="plan-001",
    content="Schedule cooling for tomorrow",
    source=TaintLabel.PRINCIPAL_INPUT,
    agent_id="Planner",
    parent_ids=["conclusion-001", "external-001"],  # Mixed provenance
)

# 6. Trace ancestry
ancestors = chain.get_ancestry("plan-001")
print(f"Ancestors of plan-001: {ancestors}")
# {'sensor-001', 'conclusion-001', 'external-001'}

# 7. Get effective taint (minimum trust across all ancestors)
taint = chain.get_effective_taint("plan-001")
print(f"Effective taint: {taint} (trust level: {taint.trust_level})")
# UNVERIFIED_EXTERNAL (level 3) — tainted by external-001

# 8. Graph-based dependency analysis
graph = ProvenanceGraph(chain)

# Check if one belief depends on another
depends = graph.depends_on("plan-001", "sensor-001")
print(f"plan-001 depends on sensor-001: {depends}")  # True

# Find all beliefs affected if a source is compromised
contaminated = graph.get_contaminated_by("external-001")
print(f"Contaminated by external-001: {contaminated}")
# {'plan-001'}

# 9. Causal attribution for compromise analysis
attrib = CausalAttribution(chain)
report = attrib.generate_report("plan-001")
print(f"Untrusted sources: {report['untrusted_sources']}")
```

## Testing

The provenance module is tested in `tests/test_provenance.py`, covering:

- DAG construction and ancestry queries.
- Taint propagation (conservative minimum trust).
- Dependency and contamination analysis.
- Cycle prevention.
- Causal attribution reports.

Run tests:

```bash
uv run pytest tests/test_provenance.py -v
```
