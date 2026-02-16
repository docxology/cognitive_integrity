# Defense Composition - Agent Reference

Defense composition algebra for combining security mechanisms.

## Modules

### algebra.py

Formal algebra for defense composition.

**Key Classes:**

- `DefenseAlgebra` - Composition operators (⊕, ⊗, ||)
- `ComposedDefense` - Result of composition

### pipeline.py

Sequential defense pipelines.

**Key Classes:**

- `DefensePipeline` - Ordered defense chain
- `PipelineStage` - Single stage with config

### fusion.py

Parallel defense fusion with voting.

**Key Classes:**

- `DefenseFusion` - Parallel execution with aggregation
- `FusionStrategy` - Voting/averaging strategies

### adapters.py

Adapters to wrap core defenses for composition.

**Key Classes:**

- `DefenseAdapter` - Base adapter interface
- `FirewallAdapter`, `TrustAdapter`, etc.

### factory.py

Factory for building composed defenses.

## Usage

```python
from src.composition import DefensePipeline, DefenseFusion

pipeline = DefensePipeline([
    FirewallAdapter(),
    TrustAdapter(),
    ConsensusAdapter()
])

fusion = DefenseFusion([
    FirewallAdapter(),
    SemanticDetector()
], strategy="majority_vote")
```
