# Colony Benchmarks - Agent Reference

Colony-level cognitive security benchmarks for multi-agent systems.

## Modules

### benchmark.py

Main benchmark orchestration.

**Key Classes:**

- `ColonyBenchmark` - Runs full colony evaluation
- `BenchmarkConfig` - Colony size, attack mix, duration

### scorecard.py

Colony health scoring.

**Key Classes:**

- `ColonyScorecard` - Aggregate health metrics
- `HealthIndicator` - Individual metric tracker

### belief_cascade.py

Belief propagation attack simulation.

### sybil_infiltration.py

Sybil agent insertion attacks.

### quorum_manipulation.py

Consensus quorum attacks.

### recruitment_poisoning.py

New agent recruitment poisoning.

### emergent_misalignment.py

Emergent goal drift detection.

## Usage

```python
from src.colony import ColonyBenchmark, BenchmarkConfig

config = BenchmarkConfig(colony_size=20, attack_rate=0.1)
benchmark = ColonyBenchmark(config)
scorecard = benchmark.run(duration=1000)
```
