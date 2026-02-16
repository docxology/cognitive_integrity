# Data Package - Agent Reference

Data generation, loading, and schema definitions.

## Modules

### generate.py

Synthetic data generation for experiments.

**Key Functions:**

- `generate_attack_corpus()` - Generate attack samples
- `generate_agent_traces()` - Generate behavioral traces
- `generate_trust_matrices()` - Generate trust networks

### loaders.py

Data loading utilities.

**Key Functions:**

- `load_corpus()` - Load attack corpus
- `load_results()` - Load experiment results

### result_loaders.py

Result file parsing and aggregation.

**Key Classes:**

- `ResultLoader` - Load and parse result files
- `ResultAggregator` - Combine multiple runs

### schema.py

Data schemas and validation.

**Key Classes:**

- `AttackSchema` - Attack data structure
- `ResultSchema` - Result data structure
- `TraceSchema` - Agent trace structure

## Usage

```python
from src.data import generate_attack_corpus, load_results

corpus = generate_attack_corpus(n=500, seed=42)
results = load_results("output/experiment_001/")
```
