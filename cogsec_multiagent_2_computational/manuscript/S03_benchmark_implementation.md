\newpage

# Colony Benchmark Design (Proposed) {#sec:benchmark-implementation}

This supplementary section presents the *design specification* for colony cognitive security benchmarks extending the individual-focused CIF in Part 1 \cite{friedman2026cogsec1} (see Part 1 S02 for the eusocial-colony analogy that motivates this benchmark direction). These benchmarks are proposed for scaling CIF evaluation beyond the main text's 3–10 agent deployments toward colony-scale populations ($n > 10$); implementations of the design below live in [`src/colony/`](../src/colony/), and the current codebase already exercises 20–100 agent scenarios via `scripts/run_colony_benchmarks.py`.

> **Status.** The $n \geq 500$ benchmarks below are proposed extensions. The codebase currently validates at 20–100 agent scale (see §5 Results, colony tier); scaling to $n \in \{500, 1000\}$ is active future work (\cref{sec:discussion}).

> **Cross-paper reading guide.**
> • **Biological grounding** for colony-level defenses (stigmergic substrates, collective invariants) appears in Part 1 S02 *Eusocial CogSec* \cite{friedman2026cogsec1}.
> • **Deployment patterns** for operating colony-scale systems (including $\Omega_5$ playbooks for emergent drift) are in Part 3 \cite{friedman2026cogsec3}, in its *Incident Response Playbooks* section (Playbook 5, $\Omega_5$ Emergent Misalignment).
> • **Domain applications** of colony-scale CIF to nation-state and infrastructure contexts appear in unified Part 3+4 \cite{friedman2026cogsec3}, Sections 9.04 and 9.10.

1. **Scalable agent populations** — $n \in \{10, 50, 100, 500, 1000\}$
2. **Configurable stigmergic substrates** — Shared memory, message queues, artifact stores
3. **Instrumented communication channels** — Full message logging with timestamps
4. **Controllable adversary injection** — Precise Sybil insertion and signal poisoning
5. **Collective function measurement** — Aggregate outcome metrics beyond individual agent states

Table: Recommended colony CogSec benchmark configurations. {#tab:benchmark-configs}

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
\text{Resilience} &= \frac{\mathcal{F}_c(\text{under attack})}{\mathcal{F}_c(\text{baseline})} \\
\text{Recovery} &= \max(0,\, 1 - t_{\text{recovery}} / t_{\max}) \text{ (normalized; } t_{\max} = 60\text{s default, configurable)}
\end{align}
with weights $w_i$ summing to 1.
\end{definition}

## Implementation Reference

### Python Environment Setup

```bash
# Create benchmark environment
uv venv cogsec-bench
source cogsec-bench/bin/activate

# Install dependencies
uv pip install numpy scipy networkx redis kafka-python

# Run benchmark suite
uv run python -m cogsec.benchmarks.colony --config colony_configs.yaml
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

> **Note**: The import path `cogsec.benchmarks` shown above reflects the proposed public API. The current internal import path is `from src.colony.benchmark import ColonyBenchmark` (see `scripts/run_colony_benchmarks.py`).

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
