\newpage

# Ablation Studies and Scalability Benchmarks {#sec:extended-ablation}

This section quantifies the contribution of individual defense components and characterizes performance scaling with agent count and message volume.

> **Reproducibility**: Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Scalability data from `scripts/run_colony_benchmarks.py` → `output/data/colony_results.json`.

## Defense Component Contributions {#sec:component-removal}

![Ablation Study: Defense Component Contribution. Horizontal bar chart showing detection rate impact of removing each CIF component from the full ensemble. The Cognitive Firewall contributes the largest marginal improvement ($\Delta\text{TPR} = +0.13$ when added), followed by Tripwires ($+0.09$), Provenance Tracking ($+0.07$), Sandbox ($+0.06$), Invariants ($+0.05$), Drift Detection ($+0.04$), and Trust Decay ($+0.03$). Components are classified by impact severity: *critical* ($\Delta > 0.10$, Firewall), *major* ($0.05 < \Delta \leq 0.10$, Tripwires and Provenance), and *moderate* ($\Delta \leq 0.05$, remaining). The Firewall + Tripwires pair exhibits the strongest positive synergy ($+0.09$ beyond additive prediction), detecting complementary attack patterns (pattern-based input filtering vs.\ behavioral anomaly monitoring). Data from \texttt{output/data/ablation\_results.json}.](figures/ablation_study.pdf){#fig:ablation-study width=95%}

The ablation analysis (\cref{fig:ablation-study}) quantifies each defense component's contribution.

**Table: Component removal impact analysis.** {#tab:component-removal}

| Removed Component | TPR | $\Delta$ TPR | FPR | $\Delta$ FPR | F1 | $\Delta$ F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Firewall | 0.81 | $-0.13$ | 0.04 | $-0.02$ | 0.88 | $-0.06$ |
| Sandbox | 0.88 | $-0.06$ | 0.05 | $-0.01$ | 0.91 | $-0.03$ |
| Tripwires | 0.85 | $-0.09$ | 0.05 | $-0.01$ | 0.89 | $-0.05$ |
| Invariants | 0.89 | $-0.05$ | 0.06 | 0.00 | 0.91 | $-0.03$ |
| Trust decay | 0.91 | $-0.03$ | 0.06 | 0.00 | 0.92 | $-0.02$ |
| Drift detection | 0.90 | $-0.04$ | 0.06 | 0.00 | 0.92 | $-0.02$ |
| Provenance tracking | 0.87 | $-0.07$ | 0.05 | $-0.01$ | 0.90 | $-0.04$ |

## Minimal Viable Configurations {#sec:minimal-config}

For resource-constrained deployments, we identify minimal component sets achieving TPR $\geq 0.90$:

**Table: Minimal viable configurations.** {#tab:minimal-configs}

| Config | Components | TPR | FPR | Latency Overhead |
| --- | --- | --- | --- | --- |
| Minimal-A | Firewall + Tripwires + Invariants | 0.91 | 0.07 | +14\% |
| Minimal-B | Firewall + Sandbox + Tripwires | 0.92 | 0.06 | +18\% |
| Minimal-C | Firewall + Tripwires + Drift | 0.90 | 0.07 | +12\% |

**Observation**: Minimal-C achieves the highest detection rate (90%) at the lowest latency overhead (12%) among tested configurations.

## Component Synergy Analysis {#sec:synergy}

Synergy score = Actual combined effect $-$ Sum of individual effects:

**Table: Component synergy analysis.** {#tab:synergy}

| Pair | Sum of Individual | Combined | Synergy |
| --- | --- | --- | --- |
| Firewall + Tripwires | 0.38 | 0.47 | +0.09 |
| Sandbox + Tripwires | 0.35 | 0.39 | +0.04 |
| Tripwires + Invariants | 0.32 | 0.38 | +0.06 |

**Finding**: Firewall + Tripwires show strongest synergy (+0.09), detecting complementary attack patterns (pattern-based vs. behavioral).

## Agent Count Scaling {#sec:agent-scaling}

**Table: Performance scaling with agent count.** {#tab:agent-scaling}

| Agents | Detection Time | 95\% CI | Memory | Consensus Time |
| --- | --- | --- | --- | --- |
| 3 | 14ms | [12, 17] | 112MB | 78ms |
| 5 | 18ms | [15, 22] | 134MB | 112ms |
| 7 | 24ms | [20, 29] | 167MB | 189ms |
| 10 | 31ms | [26, 38] | 201MB | 287ms |
| 15 | 45ms | [38, 54] | 278MB | 456ms |
| 20 | 58ms | [49, 70] | 356MB | 634ms |
| 30 | 89ms | [75, 106] | 523MB | 1.1s |
| 50 | 142ms | [120, 169] | 823MB | 1.8s |
| 100 | 312ms | [265, 372] | 1.6GB | 4.2s |

## Scaling Regression Models {#sec:regression}

**Detection time model**: $T_{detect} = \beta_0 + \beta_1 \cdot n + \beta_2 \cdot n^2$

**Table: Detection time regression coefficients.** {#tab:detection-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\beta_0$ (intercept) | 8.2 | 1.1 | [6.0, 10.4] | $<$0.0001 |
| $\beta_1$ (linear) | 1.8 | 0.3 | [1.2, 2.4] | $<$0.0001 |
| $\beta_2$ (quadratic) | 0.012 | 0.003 | [0.006, 0.018] | $<$0.0001 |

$R^2 = 0.994$, indicating excellent fit. The dominant linear term ($\beta_1 = 1.8$) confirms approximately linear scaling up to 50 agents, with the quadratic contribution ($\beta_2 = 0.012$) becoming material only beyond this range.

**Memory model**: $M = \gamma_0 + \gamma_1 \cdot n + \gamma_2 \cdot n^2$

**Table: Memory usage regression coefficients.** {#tab:memory-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\gamma_0$ (intercept) | 78.3 | 5.6 | [67.1, 89.5] | $<$0.0001 |
| $\gamma_1$ (linear) | 12.4 | 1.2 | [10.0, 14.8] | $<$0.0001 |
| $\gamma_2$ (quadratic) | 0.089 | 0.012 | [0.065, 0.113] | $<$0.0001 |

Memory growth is quadratic, primarily due to trust matrix storage ($O(n^2)$). The intercept ($\gamma_0 \approx 78$ MB) reflects baseline framework overhead independent of agent count.

## Message Volume Scaling {#sec:volume-scaling}

**Table: Performance scaling with message volume.** {#tab:volume-scaling}

| Messages/sec | Detection Rate | Latency | CPU Usage |
| --- | --- | --- | --- |
| 500 | 0.94 | 52ms | 34\% |
| 1000 | 0.94 | 68ms | 56\% |
| 2000 | 0.93 | 112ms | 78\% |
| 5000 | 0.92 | 234ms | 94\% |
| 10000 | 0.89 | 567ms | 99\% |

**Saturation point**: $\sim$5000 messages/sec with current configuration.

## Summary {#sec:ablation-summary}

\begin{enumerate}
\item **Component hierarchy**: Firewall $>$ Tripwires $>$ Provenance $>$ Sandbox $>$ Invariants
\item **Minimal config**: Firewall + Tripwires + Drift achieves 90\% detection with 12\% overhead
\item **Scalability**: Linear time scaling up to 50 agents; quadratic memory manageable to 100 agents
\item **Throughput limit**: 5000 msg/sec before detection degradation
\end{enumerate}
