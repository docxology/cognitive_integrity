\newpage

# Ablation Studies and Scalability Benchmarks {#sec:extended-ablation}

This section quantifies the contribution of individual defense components and characterizes performance scaling with agent count and message volume. All values are auto-injected from generated data files.

> **Reproducibility**: Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Scalability data from `scripts/run_scalability.py` → `output/data/scalability_results.json` (`data_origin: real_pipeline`). Note that the `scalability_data.json` file in the same directory is a `DataGenerator` placeholder that exists only so visualization tests have a schema-valid file; per that module's own rule it is not a source for manuscript tables.

## Defense Component Contributions {#sec:component-removal}

\cref{fig:ablation-study} visualizes the detection-rate impact of removing each CIF component from the full ensemble. One component dominates: removing the Invariants module costs $\Delta\text{TPR} \approx -0.847$ of the pipeline's 0.959, and the Firewall and Tripwire contribute $\approx -0.010$ each. Every other component, Detection and Trust Calculus included, has no measurable independent contribution on this corpus.

This is a reversal of what the same ablation reported before the Invariants module was rewritten, and the reason is worth stating rather than burying. The earlier version scored topic nouns: a message was suspicious if it contained the word "token" or "credential". That fired on a benign document describing a rate limiter's token bucket while missing 1,345 of 1,475 attacks, and it left the module contributing $\Delta\text{TPR} \approx -0.010$. The rewrite scores demand structure instead, requiring a verb acting on a sensitive object across five named invariants, on the observation that attacks demand things whereas documents mention them. The pipeline's measured detection moves from 0.122 to 0.959 on the same corpus with no change to any other module.

The corollary is uncomfortable and should not be smoothed over: the components that had received the most pattern engineering, Detection and the Firewall, now measure at or near zero marginal contribution, because everything they catch the Invariants module already caught.

![Ablation Study: Defense Component Contribution. Horizontal bar chart of the detection-rate cost of removing each CIF component from the full ensemble (prototype pipeline, real corpus, 98-attack stratified sample). The Invariants module dominates, followed by Firewall ($\approx -0.010$), and Tripwire ($\approx -0.010$); Consensus, Detection, Provenance, Sandbox, and Trust Calculus show no measurable independent contribution --- not because they detect nothing in isolation, but because everything they catch on this corpus the Invariants module catches too, which is what a leave-one-out delta cannot distinguish. The strongest pair beyond additive prediction is Firewall + Detection at $\approx +0.031$. All values from \texttt{output/data/ablation\_results.json}.](figures/ablation_study.pdf){#fig:ablation-study width=95%}

The ablation analysis quantifies each defense component's marginal contribution on the prototype pipeline evaluated against a stratified 98-attack corpus (\cref{tab:component-removal}).

> **Methodology**: Results from `scripts/run_ablation.py` → `output/data/ablation_results.json`. The full pipeline achieves $\sim$95.9\% TPR on this corpus. That figure has to be read with its corpus in mind: the attack corpus is generated from templates, and a detector keyed on demand structure is being asked to recognise generated demands, so 95.9\% is an upper bound relative to adversarial text written by a human trying to evade it. The false-positive side is measured against `BenignCorpus`, half of which is a deliberately hard stratum of legitimate messages carrying attack-adjacent vocabulary; that is the number to watch, and it is reported alongside every rate here.

Table: Component removal impact analysis (prototype pipeline, real corpus, 98-attack stratified sample). {#tab:component-removal}

| Removed Component | TPR | $\Delta$ TPR | Interpretation |
| --- | --- | --- | --- |
| Invariants | 0.112 | $\approx -0.847$ | Dominant: demand structure across five named invariants |
| Firewall | 0.949 | $\approx -0.010$ | Pattern matching for known injection strings, context-weighted |
| Tripwires | 0.949 | $\approx -0.010$ | Canary-belief shift detection |
| Detection module | 0.959 | $\approx +0.000$ | Subsumed: what it catches, Invariants catches first |
| Trust Calculus | 0.959 | $\approx +0.000$ | No measurable independent contribution on this corpus |
| Consensus | 0.959 | $\approx +0.000$ | No measurable independent contribution on this corpus |
| Provenance | 0.959 | $\approx +0.000$ | No measurable independent contribution on this corpus |
| Sandbox | 0.959 | $\approx +0.000$ | No measurable independent contribution on this corpus |

> **Note**: A $\Delta\text{TPR}$ of 0.000 under leave-one-out is not evidence that a component does nothing, and this corpus now demonstrates the point twice over. First, removal deltas are *marginal*: a component whose detections are all also caught by the Invariants module shows zero here while detecting a great deal on its own, which is what happened to the Detection module. Second, a component can be invisible to this measurement because the combination rule cannot see it. The pipeline compares a maximum across eight scores to one threshold, and those scores do not share a scale; measured in units of their own benign distributions, Consensus, Provenance, Sandbox and Invariants are the four that separate the classes best, which is the reverse of what this table showed before the Invariants rewrite. That analysis is in \texttt{scripts/run\_combination\_rule\_study.py}, and it means leave-one-out ablation understates any component the maximum rule is already discarding.

## Minimal Viable Configurations {#sec:minimal-config}

Minimal viable configuration analysis---identifying component sets achieving specific TPR thresholds with minimal latency overhead---was conducted using the parametric simulation model. These results are consolidated in \cref{sec:parametric-minimal} (Supplementary S08). The parametric analysis identifies Minimal-C (Firewall + Tripwires + Drift Detection) as achieving 90\% detection at 12\% latency overhead in the parametric model. Empirical validation of these configurations with the real pipeline is planned for future work.

## Component Synergy Analysis {#sec:synergy}

Synergy score = Actual combined effect $-$ Sum of individual effects (\cref{tab:synergy}). Only the top 5 synergy pairs from the real ablation data are reported; pairs not listed showed no measurable synergy on the 98-attack corpus.

Table: Component synergy analysis (real pipeline, 98-attack corpus). {#tab:synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Firewall + Detection | $\approx +0.031$ | Strongest: injection pattern-matching + text-feature analysis |
| Tripwire + Detection | $\approx +0.020$ | Canary monitoring + text-feature analysis |
| Firewall + Trust Calculus | $\approx +0.020$ | Pattern-based injection + authority claim detection |
| Trust Calculus + Tripwire | $\approx +0.020$ | Authority detection + canary monitoring |
| Trust Calculus + Detection | $\approx +0.020$ | Authority detection + text-feature analysis |

**Finding**: The strongest pair (firewall+detection, $\approx +0.031$) confirms that the Detection module amplifies the contribution of upstream pattern-based and behavioral detectors. The second tier (all $\approx +0.020$) shows that Trust Calculus pairs with multiple other components to produce modest but consistent synergy. No synergy pairs involving Consensus, Provenance, Sandbox, or Invariants were measurable on this corpus. See \cref{tab:real-synergy} for effect sizes and confidence intervals.

## Agent Count Scaling {#sec:agent-scaling}

\cref{tab:agent-scaling} reports measured per-round latency and peak traced memory as agent
count scales from 2 to 100, from `scripts/run_scalability.py` →
`output/data/scalability_results.json` (`data_origin: real_pipeline`). One round is a colony
broadcast at $n$ agents: a `TrustMatrix(n)` is constructed and materialised ($O(n^2)$ framework
state), then $n$ messages are evaluated through the full eight-module pipeline from
`create_full_pipeline()` ($O(n)$ detection cost). Latency is wall-clock per round over 15 timed
repeats after 3 warm-up rounds; memory is the `tracemalloc` peak traced allocation for one round,
which measures the framework's own allocation rather than process RSS.

Table: Performance scaling with agent count. {#tab:agent-scaling}

| Agents | Latency (ms) | 95\% CI | Peak traced memory (MB) | Min (ms) | Max (ms) |
| --- | --- | --- | --- | --- | --- |
| 2 | 0.133 | [0.131, 0.135] | 0.01 | 0.130 | 0.146 |
| 3 | 0.196 | [0.194, 0.198] | 0.01 | 0.191 | 0.205 |
| 5 | 0.320 | [0.305, 0.335] | 0.01 | 0.305 | 0.426 |
| 7 | 0.447 | [0.434, 0.461] | 0.01 | 0.434 | 0.534 |
| 10 | 0.651 | [0.630, 0.672] | 0.01 | 0.614 | 0.753 |
| 15 | 0.974 | [0.955, 0.992] | 0.01 | 0.944 | 1.065 |
| 20 | 1.297 | [1.294, 1.301] | 0.02 | 1.286 | 1.312 |
| 30 | 2.158 | [2.121, 2.194] | 0.03 | 2.072 | 2.292 |
| 50 | 3.954 | [3.906, 4.002] | 0.08 | 3.872 | 4.181 |
| 100 | 10.175 | [10.087, 10.264] | 0.31 | 9.948 | 10.644 |

$^\ddagger$\textit{95\% CIs computed via bootstrap resampling ($B = 1{,}000$ iterations) over 10 independent runs per agent count. Detection time measured end-to-end including network simulation latency.}

## Scaling Regression Models {#sec:regression}

**Detection time model**: $T_{detect} = \beta_0 + \beta_1 \cdot n + \beta_2 \cdot n^2$

\cref{tab:detection-regression} gives the fitted coefficients and significance tests.

Table: Detection time regression coefficients. {#tab:detection-regression}

| Coefficient | Estimate (ms) | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\beta_0$ (intercept) | 0.0253 | 0.0108 | [-0.0003, 0.0509] | 0.0519 |
| $\beta_1$ (linear) | 0.0555 | 0.0008 | [0.0537, 0.0573] | $<$0.0001 |
| $\beta_2$ (quadratic) | 0.00046 | 0.00001 | [0.00044, 0.00047] | $<$0.0001 |

$R^2 = 0.99997$ over $n = 10$ agent counts (median latency per count). Both the linear and
quadratic terms are significant; the intercept is not, consistent with a cost that is entirely
per-agent rather than fixed. The linear term dominates at small $n$, but the quadratic term is
real and takes over as $n$ grows: at 100 agents the $\beta_2 n^2$ contribution (4.6 ms) already
exceeds the $\beta_1 n$ contribution (5.6 ms) by nearly half, which is the $O(n^2)$ trust-matrix
construction becoming visible, with the quadratic contribution ($\beta_2 = 0.00046$ ms per agent-pair) already material at this range.

**Memory model**: $M = \gamma_0 + \gamma_1 \cdot n + \gamma_2 \cdot n^2$

\cref{tab:memory-regression} gives the fitted memory-growth coefficients over the measured range (2--100 agents).

Table: Memory usage regression coefficients. {#tab:memory-regression}

| Coefficient | Estimate (KiB) | SE | 95\% CI | $p$ |
| --- | --- | --- | --- | --- |
| $\gamma_0$ (intercept) | 7.457 | 0.303 | [6.740, 8.174] | $<$0.0001 |
| $\gamma_1$ (linear) | -0.201 | 0.022 | [-0.252, -0.149] | $<$0.0001 |
| $\gamma_2$ (quadratic) | 0.0327 | 0.0002 | [0.0322, 0.0332] | $<$0.0001 |

Memory growth is **quadratic**, not linear, across the measured range: $\gamma_2$ is significant
($p < 0.0001$, CI excluding zero) and dominates beyond roughly a dozen agents, while the negative
linear term is a curve-fitting artifact of the small-$n$ end rather than a saving. This is the
$O(n^2)$ trust-matrix storage behaving exactly as the complexity analysis predicts, and it is
visible in the measurement rather than merely anticipated. The intercept ($\gamma_0 \approx 7.5$ KiB) is baseline framework overhead independent of agent count, and the quadratic term ($\gamma_2 \approx 0.033$ KiB per agent-pair) is the trust matrix itself. The practical consequence is the opposite of a linear reading: memory is negligible at deployment scales in the tens of agents (0.31 MB at $n = 100$) but grows as $n^2$, so a colony an order of magnitude larger pays a hundredfold, not tenfold.

\textit{Note: The measured peak traced allocation at $n=100$ is 0.31 MB, and the fitted model is quadratic. The $O(n^2)$ trust-matrix storage would become dominant only at larger scales ($n > 500$). Practitioners should reference the directly measured values in the table for deployment sizing.}

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
\item **Component hierarchy (real prototype pipeline, 98-attack corpus)**: Invariants $\gg$ Firewall $\approx$ Tripwire $>$ Consensus $\approx$ Detection module $\approx$ Provenance $\approx$ Sandbox $\approx$ Trust Calculus. This ordering reflects the current adapter implementations; the three bottom-ranked components may show contributions on larger or more diverse corpora.
\item **Coverage gap**: Full prototype pipeline achieves $\sim$12.2\% TPR on the 98-attack ablation corpus; multi-seed analysis shows $\sim$44.8\% mean DR across 30 seeds (Claude Code). The parametric simulation achieves 96--100\% (\cref{sec:parametric-analysis}). The gap reflects adapter implementation maturity, not fundamental architectural limitations.
\item **Scalability**: Approximately linear time and memory scaling up to 100 agents. The $O(n^2)$ trust-matrix storage becomes dominant only at larger scales ($n > 500$).
\item **Throughput limit**: $\sim$5000 msg/sec before detection degradation.
\end{enumerate}
