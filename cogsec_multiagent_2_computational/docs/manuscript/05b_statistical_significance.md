\newpage

# Statistical Significance and Effect Sizes {#sec:statistical-validation}

This section establishes the statistical validity of our empirical findings through analysis of the multi-seed pipeline results ($N=30$ seeds) and ablation data (100-attack ablation corpus).

> **Reproducibility**: Multi-seed data from `scripts/run_multi_seed.py` → `output/data/multi_seed_results.json`. Ablation data from `scripts/run_ablation.py` → `output/data/ablation_results.json`. Parametric simulation statistics are consolidated in \cref{sec:parametric-analysis}.

## Pipeline Detection Rate Distribution {#sec:pipeline-distribution}

Across 30 random seeds, the architecture-agnostic CIF defense pipeline achieved the following detection rate distribution (\cref{tab:pipeline-distribution}):

Table: Pipeline detection rate distribution (architecture-agnostic pipeline, 30 seeds). {#tab:pipeline-distribution}

| Statistic | Value |
| --- | --- |
| Mean DR | 0.863 |
| Median DR | 0.86 |
| Population Std Dev | 0.021 |
| Min | 0.82 |
| Max | 0.90 |
| CV | 0.024 |
| Observed Range | [0.82, 0.90] |

The overall coefficient of variation (CV = 0.024) is below the 0.05 threshold. The artifact's `stable` flag is nevertheless false because stability requires every per-category CV to fall below that threshold; belief manipulation (0.094) and provenance-and-isolation (0.085) exceed it.

## Effect Sizes (Real Pipeline) {#sec:real-effect-sizes}

### Ablation Effect Sizes

We quantify the marginal contribution of each defense component using the real ablation data ($N=100$ attacks, prototype pipeline) in \cref{tab:real-component-effects}:

Table: Component removal impact with effect sizes (real pipeline). {#tab:real-component-effects}

| Removed Component | Pipeline TPR | $\Delta$ TPR | Relative Impact |
| --- | --- | --- | --- |
| None (full pipeline) | 0.890 | --- | Full pipeline (8 components active) |
| Invariants | 0.220 | $\approx -0.670$ | Dominant ($\approx 75.3\%$ of baseline TPR) |
| Tripwires | 0.880 | $\approx -0.010$ | Second, and the only other measurable loss |
| Firewall | 0.890 | $\approx 0.000$ | No measurable marginal contribution |
| Detection module | 0.890 | $\approx 0.000$ | No measurable marginal contribution |
| Trust Calculus | 0.890 | $\approx 0.000$ | No measurable marginal contribution |
| Consensus | 0.890 | $\approx 0.000$ | No measurable marginal contribution |
| Provenance | 0.890 | $\approx 0.000$ | No measurable marginal contribution |
| Sandbox | 0.890 | $\approx 0.000$ | No measurable marginal contribution |

**Interpretation**: Removing the Invariants module costs $\Delta\text{TPR} \approx -0.670$ against a full pipeline $\approx 0.890$, about 75.3\% of the pipeline's detection on this corpus. Tripwires are the only other removal with a measurable cost ($\approx -0.010$); the remaining six components measure exactly zero. Zero marginal contribution is not zero capability, and the two are routinely confused. Measured alone against the family each was built for (`scripts/run_module_capability_matrix.py`), Provenance detects 20.0\% of provenance-laundering payloads, Sandbox 28.6\% of sandbox-escape payloads and Consensus 81.1\% of byzantine-manipulation payloads -- all at a false-positive rate of 0.000 against the hard benign corpus. They contribute nothing here because Invariants already catches the same payloads, so a maximum rule that contains it gains nothing from a second detector firing on a subset of the same inputs. The pairwise synergies below, which are measured over coalitions that mostly exclude Invariants, are where those modules become visible.

### Synergy Effect Sizes (Real Pipeline)

\cref{tab:real-synergy} reports synergy scores for the top component pairs, where synergy = combined TPR minus the better singleton TPR. It is not excess beyond the sum of singleton effects and does not demonstrate detector independence.

Table: Component pair synergy scores (real pipeline, ablation data). {#tab:real-synergy}

| Pair | Synergy Score | Interpretation |
| --- | --- | --- |
| Consensus + Sandbox | $\approx +0.050$ | Quorum-subversion detection + provisional-belief isolation |
| Tripwire + Consensus | $\approx +0.050$ | Canary monitoring + quorum-subversion detection |
| Tripwire + Sandbox | $\approx +0.050$ | Canary monitoring + provisional-belief isolation |
| Tripwire + Invariants | $\approx +0.040$ | Canary monitoring + invariant-violation detection |
| Detection + Consensus | $\approx +0.040$ | Text-feature analysis + quorum-subversion detection |

Synergy scores measure the pair's improvement over its better singleton. Three pairs tie for the strongest synergy (consensus+sandbox, tripwire+consensus and tripwire+sandbox, all $\approx +0.050$). The modules' zero leave-one-out deltas in the full pipeline do not mean that they detect nothing alone: their detections overlap with other modules' detections. Pairs involving Invariants show less synergy because that module already detects most of this corpus, leaving less for a partner to add.

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

Table: Multi-seed pipeline summary with 95\% CI (30 seeds, architecture-agnostic pipeline). {#tab:multi-seed-ci}

| Metric | Estimate | 95\% CI (normal approximation) |
| --- | --- | --- |
| Mean DR | 0.863 | [0.855, 0.871] |
| Population Std Dev | 0.021 | — |

The 95\% confidence interval for the mean pipeline detection rate is [0.855, 0.871], based on 30 seeds using the normal approximation on the seed-level mean (mean ± 1.96·s/√k), matching the recorded interval method (P2-19). It estimates the mean of the architecture-agnostic pipeline's seed-level rates and does not pool 3,000 attacks as independent trials.

## Power Analysis {#sec:real-power-analysis}

\cref{tab:real-power} summarizes the statistical power available for each primary empirical comparison.

Table: Power analysis for primary empirical comparisons. {#tab:real-power}

| Comparison | Effect Size | Required $n$ | Available $n$ | Power |
| --- | --- | --- | --- | --- |
| Multi-seed mean vs 0 | Very large | 5 | 30 | $>$0.99 |
| LLM DR per architecture | Large | 30 | 5 | 0.24 |
| Ablation component removal | Medium | 64 | 100 | 0.68 |

**Key finding**: The LLM validation ($N=5$ per architecture) is substantially underpowered for 
detecting architecture-specific differences. The multi-seed analysis is well-powered for 
estimating the pipeline's mean detection rate (95\% CI [85.5, 87.1]); the ablation analysis has 
moderate power for detecting component contributions.

*Note on the first row (L2): 'mean vs 0' is a degenerate/reference power row, not the research question---a detection rate of 86.3\% is trivially distinguishable from 0. A substantive parametric--empirical test would require matched corpora and evaluation modes; those arms are not matched, so this section reports no Bayes factor for their descriptive separation. The informative read of the table is the underpowered LLM row and the moderate ablation row.*

## Multiple Comparison Correction {#sec:real-bonferroni}

For the ablation analysis comparing 8 component removals against the full pipeline, we apply Bonferroni correction: $\alpha_{\text{corrected}} = 0.05 / 8 = 0.00625$. Invariants and Tripwires are the only removals with a measurable harmful $\Delta$TPR on this corpus; the remaining six components show no measurable marginal loss (\cref{tab:real-component-effects}). Formal $p$-values require bootstrap resampling of the detection pipeline, deferred to future work with larger sample sizes.

## Summary {#sec:real-stats-summary}

\begin{enumerate}
\item **Pipeline detection**: Mean 86.3\% [95\% CI: 85.5\%, 87.1\%] across 30 seeds for the architecture-agnostic pipeline, with CV = 0.024 below the overall 0.05 threshold but per-category stability not achieved.
\item **Component hierarchy**: Invariants ($\Delta\text{TPR} \approx -0.670$) $\gg$ Tripwire ($\approx -0.010$) $>$ every remaining component (each $\approx 0.000$).
\item **Synergy**: Three pairs tie for the strongest synergy at $\approx +0.050$ over the better singleton (consensus+sandbox, tripwire+consensus, tripwire+sandbox); this is not super-additivity or evidence of independence.
\item **LLM validation underpowered**: $N=5$ per architecture yields very wide CIs (e.g., [0.28, 0.99] for Claude Code), necessitating expansion for reliable architecture-level conclusions.
\item **Parametric reference**: Design-level parametric analysis (\cref{sec:parametric-analysis}) reports 96--100\% detection under its simulation model, not a measured target for the architecture-agnostic pipeline.
\end{enumerate}
