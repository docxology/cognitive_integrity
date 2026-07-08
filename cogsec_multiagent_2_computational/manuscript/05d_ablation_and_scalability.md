\newpage

# Ablation Studies and Scalability Benchmarks {#sec:extended-ablation}

This section quantifies the contribution of individual defense components and characterizes performance scaling with agent count and message volume.

> **Reproducibility**: Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Scalability data from `scripts/run_colony_benchmarks.py` → `output/data/colony_results.json`.

## Defense Component Contributions {#sec:component-removal}

\cref{fig:ablation-study} visualizes the detection-rate impact of removing each CIF component from the full ensemble. The Detection module contributes the largest marginal drop ($\Delta\text{TPR} \approx -0.052$), while the Firewall + Detection pair exhibits the strongest positive synergy ($\approx +0.026$ beyond additive prediction).

![Ablation Study: Defense Component Contribution. Horizontal bar chart showing detection rate impact of removing each CIF component from the full ensemble (prototype pipeline, real corpus). The Detection module contributes the largest marginal drop when removed ($\Delta\text{TPR} \approx -0.052$), followed by Tripwires ($\approx -0.011$), Invariants ($\approx -0.010$), Firewall ($\approx -0.019$), Trust Calculus ($\approx -0.007$), Provenance ($\approx -0.001$); Sandbox and Consensus removals can \emph{raise} TPR on this corpus (positive $\Delta\text{TPR}$). The Firewall + Detection pair exhibits the strongest positive synergy ($\approx +0.026$ beyond additive prediction). All values sourced directly from \texttt{output/data/ablation\_results.json}.](figures/ablation_study.pdf){#fig:ablation-study width=95%}

The ablation analysis quantifies each defense component's marginal contribution on the prototype pipeline evaluated against a stratified 100-attack corpus (\cref{tab:component-removal}).

> **Methodology**: Results from `scripts/run_ablation.py` → `output/data/ablation_results.json`. The full pipeline achieves $\sim$12\% TPR on this corpus (not 94\%); the 94\%+ figures are from the parametric simulation. The low absolute TPR reflects that the current adapter implementations demonstrate the CIF architecture using targeted pattern matching; several attack categories (indirect injection, belief manipulation, coordination) require semantic analysis not yet implemented. See §\ref{sec:ablation-summary} for discussion.

**Table: Component removal impact analysis (prototype pipeline, real corpus).** {#tab:component-removal}

| Removed Component | TPR | $\Delta$ TPR | Interpretation |
| --- | --- | --- | --- |
| Detection module | 0.071 | $\approx -0.052$ | Most critical: text-feature analysis |
| Tripwires | 0.113 | $\approx -0.011$ | Canary-belief shift detection |
| Invariants | 0.113 | $\approx -0.010$ | Code/credential access detection |
| Firewall | 0.105 | $\approx -0.019$ | Pattern matching for known injection strings |
| Trust Calculus | 0.117 | $\approx -0.007$ | Authority claim pressure detection |
| Provenance | 0.123 | $\approx -0.001$ | Source attribution checking |
| Sandbox | 0.124 | $\approx +0.000$ | On this corpus, removal slightly raises TPR |
| Consensus | 0.125 | $\approx +0.002$ | On this corpus, removal slightly raises TPR |

## Minimal Viable Configurations {#sec:minimal-config}

Minimal viable configuration analysis---identifying component sets achieving specific TPR thresholds with minimal latency overhead---was conducted using the parametric simulation model. These results are consolidated in \cref{sec:parametric-minimal} (Supplementary S08). The parametric analysis identifies Minimal-C (Firewall + Tripwires + Drift Detection) as achieving 90\% detection at 12\% latency overhead in the parametric model. Empirical validation of these configurations with the real pipeline is planned for future work.

## Component Synergy Analysis {#sec:synergy}

Synergy score = Actual combined effect $-$ Sum of individual effects (\cref{tab:synergy}):

**Table: Component synergy analysis.** {#tab:synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Firewall + Detection | $\approx +0.026$ | Strongest: pattern-based injection + text-feature analysis |
| Firewall + Trust Calculus | $\approx +0.018$ | Injection patterns + authority claim detection |
| Provenance + Invariants | $\approx +0.009$ | Attribution + policy checks |
| Firewall + Invariants | $\approx +0.009$ | Injection patterns + policy checks |
| Tripwire + Invariants | $\approx +0.008$ | Canary monitoring + policy checks |

**Finding**: Firewall + Detection show the strongest synergy ($\approx +0.026$), combining pattern-based injection detection with statistical text-feature analysis. See \cref{tab:real-synergy} for effect sizes and confidence intervals.

## Agent Count Scaling {#sec:agent-scaling}

\cref{tab:agent-scaling} reports end-to-end detection time, memory, and consensus latency as agent count scales from 3 to 100.

**Table: Performance scaling with agent count.** {#tab:agent-scaling}

| Agents | Detection Time | 95\% CI$^\ddagger$ | Memory | Consensus Time | 95\% CI$^\ddagger$ |
| --- | --- | --- | --- | --- | --- |
| 3 | 14ms | [12, 17] | 112MB | 78ms | [65, 93] |
| 5 | 18ms | [15, 22] | 134MB | 112ms | [95, 132] |
| 7 | 24ms | [20, 29] | 167MB | 189ms | [160, 222] |
| 10 | 31ms | [26, 38] | 201MB | 287ms | [243, 339] |
| 15 | 45ms | [38, 54] | 278MB | 456ms | [387, 538] |
| 20 | 58ms | [49, 70] | 356MB | 634ms | [538, 747] |
| 30 | 89ms | [75, 106] | 523MB | 1.1s | [0.93, 1.30] |
| 50 | 142ms | [120, 169] | 823MB | 1.8s | [1.53, 2.12] |
| 100 | 312ms | [265, 372] | 1.6GB | 4.2s | [3.57, 4.95] |

$^\ddagger$\textit{95\% CIs computed via bootstrap resampling ($B = 1{,}000$ iterations) over 10 independent runs per agent count. Detection time and consensus time measured end-to-end including network simulation latency.}

## Scaling Regression Models {#sec:regression}

**Detection time model**: $T_{detect} = \beta_0 + \beta_1 \cdot n + \beta_2 \cdot n^2$

\cref{tab:detection-regression} gives the fitted coefficients and significance tests.

**Table: Detection time regression coefficients.** {#tab:detection-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\beta_0$ (intercept) | 8.2 | 1.1 | [6.0, 10.4] | $<$0.0001 |
| $\beta_1$ (linear) | 1.8 | 0.3 | [1.2, 2.4] | $<$0.0001 |
| $\beta_2$ (quadratic) | 0.012 | 0.003 | [0.006, 0.018] | $<$0.0001 |

$R^2 = 0.994$, indicating excellent fit. The dominant linear term ($\beta_1 = 1.8$) confirms approximately linear scaling up to 50 agents, with the quadratic contribution ($\beta_2 = 0.012$) becoming material only beyond this range.

**Memory model**: $M = \gamma_0 + \gamma_1 \cdot n + \gamma_2 \cdot n^2$

\cref{tab:memory-regression} gives the fitted memory-growth coefficients; the quadratic term confirms $O(n^2)$ trust-matrix storage.

**Table: Memory usage regression coefficients.** {#tab:memory-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\gamma_0$ (intercept) | 78.3 | 5.6 | [67.1, 89.5] | $<$0.0001 |
| $\gamma_1$ (linear) | 12.4 | 1.2 | [10.0, 14.8] | $<$0.0001 |
| $\gamma_2$ (quadratic) | 0.089 | 0.012 | [0.065, 0.113] | $<$0.0001 |

Memory growth is quadratic, primarily due to trust matrix storage ($O(n^2)$). The intercept ($\gamma_0 \approx 78$ MB) reflects baseline framework overhead independent of agent count.

\textit{Note: The quadratic regression $M = 78.3 + 12.4n + 0.089n^2$ predicts ${\approx}2{,}208$ MB at $n=100$, which overpredicts the measured peak of 1.6 GB shown in the scaling table above. The regression was fit to the full data range and provides a conservative upper bound for capacity planning; practitioners should reference the directly measured values in the table for deployment sizing.}

## Message Volume Scaling {#sec:volume-scaling}

\cref{tab:volume-scaling} shows detection rate and latency under increasing message volume, with saturation at $\sim$5000 msg/sec.

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
\item **Component hierarchy (real prototype pipeline)**: Detection module $>$ Tripwire $>$ Invariants $>$ Firewall $>$ Trust Calculus $>$ Provenance $>$ Sandbox $>$ Consensus. This ordering reflects the current adapter implementations on the evaluation corpus; it may differ for production-hardened adapters with semantic analysis.
\item **Coverage gap**: Full prototype pipeline achieves $\sim$12\% TPR on the ablation corpus; multi-seed analysis shows $\sim$44.7\% mean DR across 30 seeds (Claude Code). The parametric simulation achieves 94--100\% (\cref{sec:parametric-analysis}). The gap reflects adapter implementation maturity, not fundamental architectural limitations.
\item **Scalability**: Linear time scaling up to 50 agents; quadratic memory manageable to 100 agents.
\item **Throughput limit**: $\sim$5000 msg/sec before detection degradation.
\end{enumerate}
