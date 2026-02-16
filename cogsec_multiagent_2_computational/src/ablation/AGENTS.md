# Ablation Studies - Agent Reference

Component removal and synergy analysis for defense mechanism evaluation.

## Modules

### component_removal.py

Systematically removes individual defense components to measure their contribution.

**Key Classes:**

- `ComponentRemovalStudy` - Orchestrates single-component ablation
- `RemovalResult` - Captures metrics with/without component

### minimal_config.py

Finds minimal viable defense configurations.

**Key Classes:**

- `MinimalConfigSearch` - Greedy search for smallest effective subset
- `ConfigurationResult` - Tracks configuration performance

### synergy.py

Measures interaction effects between defense components.

**Key Classes:**

- `SynergyAnalysis` - Computes pairwise and higher-order synergies
- `SynergyMatrix` - Stores interaction strengths

## Usage

```python
from src.ablation import ComponentRemovalStudy, SynergyAnalysis

study = ComponentRemovalStudy(baseline_config)
results = study.run_all_removals()

synergy = SynergyAnalysis(components)
matrix = synergy.compute_pairwise()
```
