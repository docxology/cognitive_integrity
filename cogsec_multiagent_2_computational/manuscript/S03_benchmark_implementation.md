\newpage

# Benchmark Implementation Guidelines {#sec:benchmark-implementation}

This supplementary section provides implementation guidance for colony cognitive security benchmarks introduced in Part 1, Section S05.

## Test Environment Specification {#sec:test-environment}

Colony CogSec benchmarks require test environments that support:

1. **Scalable agent populations** — $n \in \{10, 50, 100, 500, 1000\}$
2. **Configurable stigmergic substrates** — Shared memory, message queues, artifact stores
3. **Instrumented communication channels** — Full message logging with timestamps
4. **Controllable adversary injection** — Precise Sybil insertion and signal poisoning
5. **Collective function measurement** — Aggregate outcome metrics beyond individual agent states

\begin{table}[htbp]
\centering
\caption{Recommended colony CogSec benchmark configurations.}
\label{tab:benchmark-configs}
\begin{tabular}{@{}lccccc@{}}
\toprule
\textbf{Benchmark} & \textbf{Min $n$} & \textbf{Stigmergy} & \textbf{Adversary} & \textbf{Duration} & \textbf{Metrics} \\
\midrule
Recruitment Poisoning & 20 & Required & $\Omega_2$ & 100 steps & Diversion rate \\
Sybil Infiltration & 50 & Optional & $\Omega_4$ & 500 steps & Trust ceiling \\
Quorum Manipulation & 30 & Optional & $\Omega_3$ & 200 steps & Quorum corruption \\
Belief Cascade & 100 & Optional & $\Omega_2$ & 300 steps & Penetration rate \\
Emergent Misalignment & 50 & Required & None & 1000 steps & Goal deviation \\
\bottomrule
\end{tabular}
\end{table}

## Metrics Framework {#sec:metrics-framework}

The *Colony CogSec Scorecard* integrates individual and collective metrics:

\begin{definition}[Colony CogSec Score]
\label{def:cogsec-score-impl}
The *Colony CogSec Score* (CCS) is:
\begin{equation}
\label{eq:ccs-impl}
\text{CCS} = w_1 \cdot \text{DR}_c + w_2 \cdot (1 - \text{FPR}_c) + w_3 \cdot \text{Resilience} + w_4 \cdot \text{Recovery}
\end{equation}
where:
\begin{align}
\text{DR}_c &= \text{Colony-level detection rate} \\
\text{FPR}_c &= \text{Colony-level false positive rate} \\
\text{Resilience} &= \frac{\mathcal{F}_c(\text{under attack})}{\mathcal{F}_c(\text{baseline})} \\
\text{Recovery} &= \frac{1}{t_{\text{recovery}}} \text{ (normalized)}
\end{align}
with weights $w_i$ summing to 1.
\end{definition}

## Implementation Reference

### Python Environment Setup

```bash
# Create benchmark environment
python -m venv cogsec-bench
source cogsec-bench/bin/activate

# Install dependencies
pip install numpy scipy networkx redis kafka-python

# Run benchmark suite
python -m cogsec.benchmarks.colony --config colony_configs.yaml
```

### Benchmark Runner

```python
from cogsec.benchmarks import ColonyBenchmark

# Configure benchmark
config = {
    "n_agents": 100,
    "stigmergy": "redis",
    "adversary_class": "omega_2",
    "duration_steps": 300,
}

# Run recruitment poisoning benchmark
benchmark = ColonyBenchmark("recruitment_poisoning", config)
results = benchmark.run()

# Compute Colony CogSec Score
ccs = benchmark.compute_ccs(
    weights=[0.3, 0.2, 0.3, 0.2]
)
print(f"Colony CogSec Score: {ccs:.3f}")
```

### Stigmergic Substrate Configuration

```yaml
# stigmergy_config.yaml
substrate:
  type: redis  # or: kafka, filesystem, memory
  connection:
    host: localhost
    port: 6379
  
  markers:
    - name: recruitment
      decay_rate: 0.1  # per step
      max_intensity: 1.0
    - name: alarm
      decay_rate: 0.5
      propagation: broadcast

  logging:
    enabled: true
    path: ./logs/stigmergy/
    include_timestamps: true
```

## Integration with CIF Test Suite

The colony benchmarks integrate with the main CIF test suite:

```python
from cogsec.testing import CIFTestSuite

suite = CIFTestSuite(
    project="cogsec_multiagent_2_computational"
)

# Run individual agent tests
suite.run_agent_tests()

# Run colony benchmarks
suite.run_colony_benchmarks(
    benchmarks=["recruitment_poisoning", "sybil_infiltration"]
)

# Generate combined report
suite.generate_report(output="./reports/cif_full.pdf")
```

## Summary

This implementation guide enables reproduction of colony CogSec benchmark results. For formal definitions and theoretical foundations, see Part 1, Supplementary Section S05.
