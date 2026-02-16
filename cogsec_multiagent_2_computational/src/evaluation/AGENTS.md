# Evaluation Package - Agent Reference

Experiment runner, metrics, and benchmarks.

## Modules

### runner.py

Main experiment orchestration.

**Key Classes:**

- `ExperimentRunner` - Run full experiments
- `ExperimentConfig` - Experiment parameters
- `ExperimentResult` - Captured results

### metrics.py

Evaluation metrics computation.

**Key Functions:**

- `compute_accuracy()` - Classification accuracy
- `compute_f1()` - F1 score
- `compute_latency_stats()` - Timing statistics

### precision_recall.py

Precision-recall curve analysis.

**Key Classes:**

- `PRCurve` - Precision-recall curve
- `PRAnalyzer` - Threshold optimization

### roc.py

ROC curve and AUC analysis.

**Key Classes:**

- `ROCCurve` - ROC curve computation
- `AUCCalculator` - Area under curve

### benchmark.py

Standard benchmarks.

**Key Classes:**

- `Benchmark` - Standard benchmark suite
- `BenchmarkResult` - Benchmark outcomes

### scalability.py

Scalability analysis.

**Key Classes:**

- `ScalabilityTest` - Scale vs performance
- `ScalingCurve` - Fitted scaling model

## Usage

```python
from src.evaluation import ExperimentRunner, ExperimentConfig

config = ExperimentConfig(
    architectures=["claude_code", "autogpt"],
    attack_sample=100,
    seed=42
)
runner = ExperimentRunner(config)
results = runner.run()
```
