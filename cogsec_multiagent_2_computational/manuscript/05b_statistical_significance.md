\newpage

# Statistical Significance and Effect Sizes {#sec:statistical-validation}

This section establishes the statistical validity of our empirical findings through analysis of the multi-seed pipeline results ($N=30$ seeds) and ablation data (100-attack corpus).

> **Reproducibility**: Multi-seed data from `scripts/run_multi_seed.py` → `output/data/multi_seed_results.json`. Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Parametric simulation statistics are consolidated in \cref{sec:parametric-analysis}.

## Pipeline Detection Rate Distribution {#sec:pipeline-distribution}

Across 30 random seeds on the Claude Code architecture, the full CIF defense pipeline achieved the following detection rate distribution (\cref{tab:pipeline-distribution}):

Table: Pipeline detection rate distribution (Claude Code, 30 seeds). {#tab:pipeline-distribution}

| Statistic | Value |
| --- | --- |
| Mean DR | 0.448 |
| Median DR | 0.45 |
| Std Dev | 0.0441 |
| Min | 0.37 |
| Max | 0.56 |
| CV | 0.097 |
| 95% Range | [0.37, 0.56] |

The coefficient of variation (CV = 0.097) exceeds the 0.05 stability threshold, indicating that detection rates are moderately sensitive to random seed initialization. The distribution is approximately symmetric, with no evidence of heavy tails or bimodality.

## Effect Sizes (Real Pipeline) {#sec:real-effect-sizes}

### Ablation Effect Sizes

We quantify the marginal contribution of each defense component using the real ablation data ($N=98$ attacks, prototype pipeline) in \\cref{tab:real-component-effects}:

Table: Component removal impact with effect sizes (real pipeline). {#tab:real-component-effects}

| Removed Component | Pipeline TPR | $\\Delta$ TPR | Relative Impact |
| --- | --- | --- | --- |
| None (full pipeline) | 0.122 | --- | Full pipeline (8 components active) |
| Detection module | 0.071 | $\\approx -0.051$ | Largest drop ($\\approx 42\\%$ of baseline TPR) |
| Trust Calculus | 0.102 | $\\approx -0.020$ | Second largest |
| Firewall | 0.112 | $\\approx -0.010$ | Third (tied) |
| Invariants | 0.112 | $\\approx -0.010$ | Third (tied) |
| Tripwires | 0.112 | $\\approx -0.010$ | Third (tied) |
| Consensus | 0.122 | $\\approx 0.000$ | No measurable independent contribution |
| Provenance | 0.122 | $\\approx 0.000$ | No measurable independent contribution |
| Sandbox | 0.122 | $\\approx 0.000$ | No measurable independent contribution |

**Interpretation**: The Detection module accounts for about 42\\% of baseline TPR in marginal-removal terms ($\\Delta\\text{TPR} \\approx -0.051$ vs.\\ full pipeline $\\approx 0.122$). The Trust Calculus is the second most impactful component ($\\Delta\\text{TPR} \\approx -0.020$). Firewall, Invariants, and Tripwires each contribute $\\Delta\\text{TPR} \\approx -0.010$. Consensus, Provenance, and Sandbox show $\\Delta\\text{TPR} = 0.000$, meaning their removal produced no measurable change in detection rate on this 98-attack corpus — this does not imply these components are ineffective, only that the current corpus may not exercise their trigger conditions.

### Synergy Effect Sizes (Real Pipeline)

\cref{tab:real-synergy} reports synergy scores for the top component pairs, where synergy = actual combined effect minus the sum of individual effects.

Table: Component pair synergy scores (real pipeline, ablation data). {#tab:real-synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Firewall + Detection | $\\approx +0.031$ | Strongest: injection pattern-matching + text-feature analysis |
| Tripwire + Detection | $\\approx +0.031$ | Canary monitoring + text-feature analysis |
| Firewall + Trust Calculus | $\\approx +0.020$ | Pattern-based injection + authority claim detection |
| Trust Calculus + Tripwire | $\\approx +0.020$ | Authority detection + canary monitoring |
| Trust Calculus + Detection | $\\approx +0.020$ | Authority detection + text-feature analysis |

Synergy scores measure the detection improvement of the pair beyond the sum of their individual effects. The top synergy pairs (firewall+detection and tripwire+detection, both $\\approx +0.031$) confirm that the Detection module amplifies the contribution of upstream pattern-based and behavioral detectors. Only 5 synergy pairs were measurable on the 98-attack corpus; pairs involving Consensus, Provenance, Sandbox, or Invariants showed no measurable synergy.

## Confidence Intervals (Empirical) {#sec:empirical-ci}

### LLM Validation Confidence Intervals

Given the small sample sizes ($N=5$ per architecture), we report exact binomial confidence intervals (\cref{tab:llm-ci}):

Table: LLM validation detection rates with exact binomial 95\% CI. {#tab:llm-ci}

| Architecture | DR | $N$ | 95\% CI (Clopper-Pearson) |
| --- | --- | --- | --- |
| Claude Code | 0.80 | 5 | [0.28, 0.99] |
| CrewAI | 1.00 | 5 | [0.48, 1.00] |

*The wide confidence intervals reflect the preliminary nature of the LLM validation. The Claude Code interval [0.28, 0.99] spans 71 percentage points, confirming that $N=5$ is insufficient for precise rate estimation. These intervals should narrow substantially with the planned expansion to $N \geq 30$ per architecture.*

### Multi-Seed Pipeline Confidence Intervals

\cref{tab:multi-seed-ci} summarizes the mean pipeline detection rate with a 95\% confidence interval computed from the 30-seed sample.

Table: Multi-seed pipeline summary with 95\% CI (30 seeds, Claude Code). {#tab:multi-seed-ci}

| Metric | Estimate | 95\% CI (t-distribution) |
| --- | --- | --- |
| Mean DR | 0.448 | [0.432, 0.464] |
| Std Dev | 0.0441 | — |

The 95\% confidence interval for the mean pipeline detection rate is [0.432, 0.464], based on 30 seeds with a t-distribution correction. This provides a reliable estimate of expected pipeline performance on the Claude Code architecture with the current adapter implementations.

## Power Analysis {#sec:real-power-analysis}

\cref{tab:real-power} summarizes the statistical power available for each primary empirical comparison.

Table: Power analysis for primary empirical comparisons. {#tab:real-power}

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
\item **Pipeline detection**: Mean 44.8\% [95\% CI: 43.2\%, 46.4\%] across 30 seeds (Claude Code), with CV = 0.097 indicating moderate seed sensitivity.
\item **Component hierarchy**: Detection module ($\Delta\text{TPR} \approx -0.051$) is the dominant contributor, followed by Tripwires and Invariants ($\approx -0.011$ and $\approx -0.010$). The top three harmful removals account for about 82\% of the summed negative $\Delta\text{TPR}$ magnitude.
\item **Synergy**: Tripwire + Detection shows strongest synergy ($\approx +0.025$), confirming complementary detection patterns on the ablation corpus.
\item **LLM validation underpowered**: $N=5$ per architecture yields very wide CIs (e.g., [0.28, 0.99] for Claude Code), necessitating expansion for reliable architecture-level conclusions.
\item **Parametric reference**: Design-level parametric analysis (\cref{sec:parametric-analysis}) achieves 94--100\% detection, establishing the coverage ceiling for fully-realized adapter implementations.
\end{enumerate}
