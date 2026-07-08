\newpage

# Statistical Significance and Effect Sizes {#sec:statistical-validation}

This section establishes the statistical validity of our empirical findings through analysis of the multi-seed pipeline results ($N=30$ seeds) and ablation data (100-attack corpus).

> **Reproducibility**: Multi-seed data from `scripts/run_multi_seed.py` → `output/data/multi_seed_results.json`. Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Parametric simulation statistics are consolidated in \cref{sec:parametric-analysis}.

## Pipeline Detection Rate Distribution {#sec:pipeline-distribution}

Across 30 random seeds on the Claude Code architecture, the full CIF defense pipeline achieved the following detection rate distribution (\cref{tab:pipeline-distribution}):

**Table: Pipeline detection rate distribution (Claude Code, 30 seeds).** {#tab:pipeline-distribution}

| Statistic | Value |
| --- | --- |
| Mean DR | 0.447 |
| Median DR | 0.45 |
| Std Dev | 0.0441 |
| Min | 0.37 |
| Max | 0.56 |
| CV | 0.097 |
| 95% Range | [0.37, 0.56] |

The coefficient of variation (CV = 0.097) exceeds the 0.05 stability threshold, indicating that detection rates are moderately sensitive to random seed initialization. The distribution is approximately symmetric, with no evidence of heavy tails or bimodality.

## Effect Sizes (Real Pipeline) {#sec:real-effect-sizes}

### Ablation Effect Sizes

We quantify the marginal contribution of each defense component using the real ablation data ($N=100$ attacks, prototype pipeline) in \cref{tab:real-component-effects}:

**Table: Component removal impact with effect sizes (real pipeline).** {#tab:real-component-effects}

| Removed Component | Pipeline TPR | $\Delta$ TPR | Relative Impact |
| --- | --- | --- | --- |
| None (full pipeline) | $\approx 0.124$ | — | Full pipeline (8 components active) |
| Detection module | 0.071 | $\approx -0.052$ | Largest drop ($\approx 42\%$ of baseline TPR) |
| Tripwire | 0.113 | $\approx -0.011$ | Second largest |
| Invariants | 0.113 | $\approx -0.010$ | Third largest |
| Firewall | 0.105 | $\approx -0.019$ | Fourth |
| Trust Calculus | 0.117 | $\approx -0.007$ | Fifth |
| Provenance | 0.123 | $\approx -0.001$ | Small marginal harm when removed |
| Sandbox | 0.124 | $\approx +0.000$ | On this corpus, small increase when removed |
| Consensus | 0.125 | $\approx +0.002$ | On this corpus, small increase when removed |

**Interpretation**: The Detection module accounts for about 42\% of baseline TPR in marginal-removal terms ($\Delta\text{TPR} \approx -0.052$ vs.\ full pipeline $\approx 0.124$). The top three harmful removals (Detection, Tripwires, Invariants) together contribute about 82\% of the summed negative $\Delta\text{TPR}$ magnitude. Positive $\Delta\text{TPR}$ when Sandbox or Consensus is removed indicates overlap with other modules or limited exercise on this corpus---not that those components are globally dispensable.

### Synergy Effect Sizes (Real Pipeline)

\cref{tab:real-synergy} reports synergy scores for the top component pairs, where synergy = actual combined effect minus the sum of individual effects.

**Table: Component pair synergy scores (real pipeline, ablation data).** {#tab:real-synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Firewall + Detection | $\approx +0.026$ | Strongest: injection patterns + statistical |
| Firewall + Trust Calculus | $\approx +0.018$ | Injection patterns + authority claim detection |
| Provenance + Invariants | $\approx +0.009$ | Attribution + policy checks |
| Firewall + Invariants | $\approx +0.009$ | Injection patterns + policy checks |
| Tripwire + Invariants | $\approx +0.008$ | Canary monitoring + policy checks |

Synergy scores measure the detection improvement of the pair beyond the sum of their individual effects. The Firewall + Detection pair exhibits the strongest synergy ($\approx +0.026$), confirming that injection pattern filtering and text-feature analysis detect complementary attack patterns on this corpus.

## Confidence Intervals (Empirical) {#sec:empirical-ci}

### LLM Validation Confidence Intervals

Given the small sample sizes ($N=5$ per architecture), we report exact binomial confidence intervals (\cref{tab:llm-ci}):

**Table: LLM validation detection rates with exact binomial 95\% CI.** {#tab:llm-ci}

| Architecture | DR | $N$ | 95\% CI (Clopper-Pearson) |
| --- | --- | --- | --- |
| Claude Code | 0.80 | 5 | [0.28, 0.99] |
| CrewAI | 1.00 | 5 | [0.48, 1.00] |

*The wide confidence intervals reflect the preliminary nature of the LLM validation. The Claude Code interval [0.28, 0.99] spans 71 percentage points, confirming that $N=5$ is insufficient for precise rate estimation. These intervals should narrow substantially with the planned expansion to $N \geq 30$ per architecture.*

### Multi-Seed Pipeline Confidence Intervals

\cref{tab:multi-seed-ci} summarizes the mean pipeline detection rate with a 95\% confidence interval computed from the 30-seed sample.

**Table: Multi-seed pipeline summary with 95\% CI (30 seeds, Claude Code).** {#tab:multi-seed-ci}

| Metric | Estimate | 95\% CI (t-distribution) |
| --- | --- | --- |
| Mean DR | 0.447 | [0.434, 0.462] |
| Std Dev | 0.0441 | — |

The 95\% confidence interval for the mean pipeline detection rate is [0.434, 0.462], based on 30 seeds with a t-distribution correction. This provides a reliable estimate of expected pipeline performance on the Claude Code architecture with the current adapter implementations.

## Power Analysis {#sec:real-power-analysis}

\cref{tab:real-power} summarizes the statistical power available for each primary empirical comparison.

**Table: Power analysis for primary empirical comparisons.** {#tab:real-power}

| Comparison | Effect Size | Required $n$ | Available $n$ | Power |
| --- | --- | --- | --- | --- |
| Multi-seed mean vs 0 | Very large | 5 | 30 | $>$0.99 |
| LLM DR per architecture | Large | 30 | 5 | 0.24 |
| Ablation component removal | Medium | 64 | 100 | 0.68 |

**Key finding**: The LLM validation ($N=5$ per architecture) is substantially underpowered for detecting architecture-specific differences. The multi-seed analysis is well-powered for estimating the pipeline's mean detection rate. The ablation analysis has moderate power for detecting component contributions.

## Multiple Comparison Correction {#sec:real-bonferroni}

For the ablation analysis comparing 8 component removals against the full pipeline, we apply Bonferroni correction: $\alpha_{\text{corrected}} = 0.05 / 8 = 0.00625$. Components with the largest harmful $\Delta$TPR values (Detection, then Tripwires and Invariants, then Firewall) dominate the marginal-loss profile; Sandbox and Consensus show near-zero or positive $\Delta$TPR on this corpus (\cref{tab:real-component-effects}). Formal $p$-values require bootstrap resampling of the detection pipeline, deferred to future work with larger sample sizes.

## Summary {#sec:real-stats-summary}

\begin{enumerate}
\item **Pipeline detection**: Mean 44.8\% [95\% CI: 43.4\%, 46.2\%] across 30 seeds (Claude Code), with CV = 0.097 indicating moderate seed sensitivity.
\item **Component hierarchy**: Detection module ($\Delta\text{TPR} \approx -0.052$) is the dominant contributor, followed by Tripwires and Invariants ($\approx -0.011$ and $\approx -0.010$). The top three harmful removals account for about 82\% of the summed negative $\Delta\text{TPR}$ magnitude.
\item **Synergy**: Firewall + Detection shows strongest synergy ($\approx +0.026$), confirming complementary detection patterns on the ablation corpus.
\item **LLM validation underpowered**: $N=5$ per architecture yields very wide CIs (e.g., [0.28, 0.99] for Claude Code), necessitating expansion for reliable architecture-level conclusions.
\item **Parametric reference**: Design-level parametric analysis (\cref{sec:parametric-analysis}) achieves 94--100\% detection, establishing the coverage ceiling for fully-realized adapter implementations.
\end{enumerate}
