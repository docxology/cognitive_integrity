\newpage

# Ablation Studies and Scalability Benchmarks {#sec:extended-ablation}

This section quantifies the contribution of individual defense components and characterizes performance scaling with agent count and message volume. All values are auto-injected from generated data files.

> **Reproducibility**: Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Scalability data from `scripts/run_scalability.py` → `output/data/scalability_data.json`.

## Defense Component Contributions {#sec:component-removal}

\cref{fig:ablation-study} visualizes the detection-rate impact of removing each CIF component from the full ensemble. The Detection module contributes the largest marginal drop ($\Delta\text{TPR} \approx -0.051$), accounting for nearly half of all pipeline detection. The Trust Calculus is the second most impactful component ($\Delta\text{TPR} \approx -0.020$). The remaining active components (Firewall, Invariants, Tripwire) each contribute $\Delta\text{TPR} \approx -0.010$, while Provenance, Sandbox, and Consensus show no measurable independent contribution on the current 98-attack stratified corpus.

![Ablation Study: Defense Component Contribution. Horizontal bar chart showing detection rate impact of removing each CIF component from the full ensemble (prototype pipeline, real corpus, 98-attack stratified sample). The Detection module contributes the largest marginal drop when removed ($\Delta\text{TPR} \approx -0.051$), followed by Trust Calculus ($\approx -0.020$), Firewall ($\approx -0.010$), Invariants ($\approx -0.010$), Tripwire ($\approx -0.010$), Consensus ($\approx +0.000$), Provenance ($\approx +0.000$), and Sandbox ($\approx +0.000$); Provenance, Sandbox, and Consensus show no measurable independent delta on this corpus. Top synergy pair (firewall+detection and tripwire+detection, tied): $\approx +0.031$ beyond additive prediction. All values sourced directly from \texttt{output/data/ablation\_results.json}.](figures/ablation_study.pdf){#fig:ablation-study width=95%}

The ablation analysis quantifies each defense component's marginal contribution on the prototype pipeline evaluated against a stratified 98-attack corpus (\cref{tab:component-removal}).

> **Methodology**: Results from `scripts/run_ablation.py` → `output/data/ablation_results.json`. The full pipeline achieves $\sim$12.2\% TPR on this corpus (not 94\%); the 94\%+ figures are from the parametric simulation. The low absolute TPR reflects that the current adapter implementations demonstrate the CIF architecture using targeted pattern matching; several attack categories (indirect injection, belief manipulation, coordination) require semantic analysis not yet implemented. See §\ref{sec:ablation-summary} for discussion.

Table: Component removal impact analysis (prototype pipeline, real corpus, 98-attack stratified sample). {#tab:component-removal}

| Removed Component | TPR | $\Delta$ TPR | Interpretation |
| --- | --- | --- | --- |
| Detection module | 0.071 | $\approx -0.051$ | Most critical: text-feature analysis accounts for 42\% of pipeline detection |
| Trust Calculus | 0.102 | $\approx -0.020$ | Second most impactful: authority-claim pressure detection |
| Firewall | 0.112 | $\approx -0.010$ | Pattern matching for known injection strings |
| Invariants | 0.112 | $\approx -0.010$ | Code/credential access detection |
| Tripwires | 0.112 | $\approx -0.010$ | Canary-belief shift detection |
| Consensus | 0.122 | $\approx +0.000$ | No measurable independent contribution on this corpus |
| Provenance | 0.122 | $\approx +0.000$ | No measurable independent contribution on this corpus |
| Sandbox | 0.122 | $\approx +0.000$ | No measurable independent contribution on this corpus |

> **Note**: The three bottom-ranked components (Consensus, Provenance, Sandbox) show $\Delta\text{TPR} = 0.000$ on this corpus, meaning their removal produced no measurable change in detection rate. This does not imply these components are ineffective — the 98-attack stratified sample may not exercise their trigger conditions, or their contribution may be in false-positive reduction (which is 0.0 for all configurations on this corpus) rather than true-positive detection. Evaluation on larger, more diverse corpora is needed to characterize these components' contributions.

## Minimal Viable Configurations {#sec:minimal-config}

Minimal viable configuration analysis---identifying component sets achieving specific TPR thresholds with minimal latency overhead---was conducted using the parametric simulation model. These results are consolidated in \cref{sec:parametric-minimal} (Supplementary S08). The parametric analysis identifies Minimal-C (Firewall + Tripwires + Drift Detection) as achieving 90\% detection at 12\% latency overhead in the parametric model. Empirical validation of these configurations with the real pipeline is planned for future work.

## Component Synergy Analysis {#sec:synergy}

Synergy score = Actual combined effect $-$ Sum of individual effects (\cref{tab:synergy}). Only the top 5 synergy pairs from the real ablation data are reported; pairs not listed showed no measurable synergy on the 98-attack corpus.

Table: Component synergy analysis (real pipeline, 98-attack corpus). {#tab:synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Firewall + Detection | $\approx +0.031$ | Strongest: injection pattern-matching + text-feature analysis |
| Tripwire + Detection | $\approx +0.031$ | Canary monitoring + text-feature analysis |
| Firewall + Trust Calculus | $\approx +0.020$ | Pattern-based injection + authority claim detection |
| Trust Calculus + Tripwire | $\approx +0.020$ | Authority detection + canary monitoring |
| Trust Calculus + Detection | $\approx +0.020$ | Authority detection + text-feature analysis |

**Finding**: The top synergy tier (firewall+detection and tripwire+detection, both $\approx +0.031$) confirms that the Detection module amplifies the contribution of upstream pattern-based and behavioral detectors. The second tier (all $\approx +0.020$) shows that Trust Calculus pairs with multiple other components to produce modest but consistent synergy. No synergy pairs involving Consensus, Provenance, Sandbox, or Invariants were measurable on this corpus. See \cref{tab:real-synergy} for effect sizes and confidence intervals.

## Agent Count Scaling {#sec:agent-scaling}

\cref{tab:agent-scaling} reports end-to-end detection time and memory as agent count scales from 2 to 100. Data from `scripts/run_scalability.py` → `output/data/scalability_data.json`.

Table: Performance scaling with agent count. {#tab:agent-scaling}

| Agents | Detection Time | 95\% CI$^\ddagger$ | Memory | Consensus Time | 95\% CI$^\ddagger$ |
| --- | --- | --- | --- | --- | --- |
| 2 | 7ms | [6.0, 8.1] | 63MB | --- | --- |
| 3 | 8ms | [6.8, 9.3] | 75MB | --- | --- |
| 5 | 14ms | [12.1, 16.4] | 91MB | --- | --- |
| 7 | 19ms | [15.9, 21.5] | 108MB | --- | --- |
| 10 | 22ms | [18.5, 25.0] | 135MB | --- | --- |
| 15 | 30ms | [25.8, 34.9] | 173MB | --- | --- |
| 20 | 41ms | [35.1, 47.6] | 216MB | --- | --- |
| 30 | 69ms | [58.9, 79.7] | 294MB | --- | --- |
| 50 | 131ms | [111.8, 151.2] | 460MB | --- | --- |
| 100 | 356ms | [302.7, 409.5] | 873MB | --- | --- |

$^\ddagger$\textit{95\% CIs computed via bootstrap resampling ($B = 1{,}000$ iterations) over 10 independent runs per agent count. Detection time measured end-to-end including network simulation latency.}

## Scaling Regression Models {#sec:regression}

**Detection time model**: $T_{detect} = \beta_0 + \beta_1 \cdot n + \beta_2 \cdot n^2$

\cref{tab:detection-regression} gives the fitted coefficients and significance tests.

Table: Detection time regression coefficients. {#tab:detection-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\beta_0$ (intercept) | 4.5 | 1.1 | [2.3, 6.7] | $<$0.0001 |
| $\beta_1$ (linear) | 1.5 | 0.3 | [0.9, 2.1] | $<$0.0001 |
| $\beta_2$ (quadratic) | 0.020 | 0.003 | [0.014, 0.026] | $<$0.0001 |

$R^2 = 0.9998$, indicating excellent fit. The dominant linear term ($\beta_1 = 1.5$) confirms approximately linear scaling up to 50 agents, with the quadratic contribution ($\beta_2 = 0.020$) becoming material only beyond this range.

**Memory model**: $M = \gamma_0 + \gamma_1 \cdot n + \gamma_2 \cdot n^2$

\cref{tab:memory-regression} gives the fitted memory-growth coefficients; at measured scales (2--100 agents) memory growth is approximately linear.

Table: Memory usage regression coefficients. {#tab:memory-regression}

| Coefficient | Estimate | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\gamma_0$ (intercept) | 50.2 | 5.6 | [39.0, 61.4] | $<$0.0001 |
| $\gamma_1$ (linear) | 8.2 | 1.2 | [5.8, 10.6] | $<$0.0001 |
| $\gamma_2$ (quadratic) | 0.001 | 0.012 | [-0.023, 0.025] | 0.93 |

Memory growth is approximately linear for the measured range (2--100 agents), with the quadratic term insignificant ($p = 0.93$). The intercept ($\gamma_0 \approx 50$ MB) reflects baseline framework overhead independent of agent count. The dominant linear term ($\gamma_1 \approx 8.2$ MB/agent) corresponds to per-agent state storage; the trust matrix contribution ($O(n^2)$) is negligible at these scales because the matrix entries are small floating-point values.

\textit{Note: The measured peak memory of 873 MB at $n=100$ confirms approximately linear memory growth at practical agent counts. The $O(n^2)$ trust-matrix storage would become dominant only at larger scales ($n > 500$). Practitioners should reference the directly measured values in the table for deployment sizing.}

## Message Volume Scaling {#sec:volume-scaling}

\cref{tab:volume-scaling} shows detection rate and latency under increasing message volume, with saturation at $\sim$5000 msg/sec.

Table: Performance scaling with message volume. {#tab:volume-scaling}

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
\item **Component hierarchy (real prototype pipeline, 98-attack corpus)**: Detection module $\gg$ Trust Calculus $>$ Firewall $\approx$ Invariants $\approx$ Tripwire $>$ Consensus $\approx$ Provenance $\approx$ Sandbox. This ordering reflects the current adapter implementations; the three bottom-ranked components may show contributions on larger or more diverse corpora.
\item **Coverage gap**: Full prototype pipeline achieves $\sim$12.2\% TPR on the 98-attack ablation corpus; multi-seed analysis shows $\sim$44.8\% mean DR across 30 seeds (Claude Code). The parametric simulation achieves 96--100\% (\cref{sec:parametric-analysis}). The gap reflects adapter implementation maturity, not fundamental architectural limitations.
\item **Scalability**: Approximately linear time and memory scaling up to 100 agents. The $O(n^2)$ trust-matrix storage becomes dominant only at larger scales ($n > 500$).
\item **Throughput limit**: $\sim$5000 msg/sec before detection degradation.
\end{enumerate}
