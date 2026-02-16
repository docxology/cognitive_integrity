\newpage

# Colony Benchmark Design (Proposed) {#sec:benchmark-implementation}

This supplementary section presents the *design specification* for colony cognitive security benchmarks introduced in Part 1, Section S05. These benchmarks are proposed for future implementation; the current CIF codebase validates individual-agent and small-group defense mechanisms (3--10 agents) as described in the main text. The configurations below define the target infrastructure for scaling CIF evaluation to colony-scale populations ($n > 10$).

> **Status**: The benchmark specifications in this section are *proposed designs*. The code snippets illustrate the intended API and are not yet implemented in the CIF repository. Colony-scale evaluation is an active area of future work (see \cref{sec:discussion}).

1. **Scalable agent populations** — $n \in \{10, 50, 100, 500, 1000\}$
2. **Configurable stigmergic substrates** — Shared memory, message queues, artifact stores
3. **Instrumented communication channels** — Full message logging with timestamps
4. **Controllable adversary injection** — Precise Sybil insertion and signal poisoning
5. **Collective function measurement** — Aggregate outcome metrics beyond individual agent states

**Table: Recommended colony CogSec benchmark configurations.** {#tab:benchmark-configs}

**Benchmark** | **Min $n$** | **Stigmergy** | **Adversary** | **Duration** | **Metrics** |
| --- | --- | --- | --- | --- | --- |
| Recruitment Poisoning | 20 | Required | $\Omega_2$ | 100 steps | Diversion rate |
| Sybil Infiltration | 50 | Optional | $\Omega_4$ | 500 steps | Trust ceiling |
| Quorum Manipulation | 30 | Optional | $\Omega_3$ | 200 steps | Quorum corruption |
| Belief Cascade | 100 | Optional | $\Omega_2$ | 300 steps | Penetration rate |
| Emergent Misalignment | 50 | Required | None | 1000 steps | Goal deviation |

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
\text{Resilience} &= \frac{\mathcal{F}_c(\text{under attack})}{\mathcal{F}*c(\text{baseline})} \\
\text{Recovery} &= \frac{1}{t*{\text{recovery}}} \text{ (normalized)}
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

## Benchmark Validity Considerations {#sec:benchmark-validity}

Colony-scale benchmarks introduce considerations not present in individual-agent evaluation:

1. **Emergent behavior confounds**: At $n > 50$, agent collectives may develop coordination patterns that affect both attack success and detection rates independently of CIF mechanisms. Benchmarks should include control runs without adversaries to establish behavioral baselines.

2. **Stigmergic channel security**: Shared memory substrates (Redis, message queues) introduce attack surfaces not present in direct communication models. The benchmark suite includes substrate-specific attack generators for each supported backend.

3. **Temporal coupling**: Colony dynamics evolve over hundreds of steps; snapshot metrics (single-point detection rate) may miss temporal patterns. The CCS metric addresses this through the Recovery component, but practitioners should also examine detection rate trajectories over the benchmark duration.

4. **Scalability of ground truth**: Manual annotation becomes infeasible at colony scale. The benchmark uses programmatic ground truth (attacks are generated with known labels) supplemented by automated consistency checks.

## Summary

This implementation guide enables reproduction of colony CogSec benchmark results. For formal definitions and theoretical foundations, see Part 1, Supplementary Section S05.
