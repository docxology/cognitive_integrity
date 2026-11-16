\newpage

# Parametric Simulation Analysis {#sec:parametric-analysis}

This supplementary section consolidates all results derived from CIF's parametric, architecture-aware simulation model. These results characterize the framework's **design-level detection properties under calibrated conditions** and are presented separately from the empirical results (Section \ref{sec:results}) to maintain clear provenance for each category of evidence.

> **Methodology**: The parametric simulation computes detection scores from calibrated base rates indexed by attack difficulty (easy, medium, hard), modulated by architecture-specific attack-surface multipliers, with Gaussian noise ($\sigma = 0.05$). See §\ref{sec:eval-methodology} for full description. **Two distinct sources appear in this section and must not be read as one.** The aggregate rows --- the overall and per-architecture detection rates in \cref{sec:parametric-summary} --- are computed from `scripts/run_full_evaluation.py --mode simulation` → `output/data/full_evaluation_results.json`, whose 16 cells cover four corpus categories (direct injection, impersonation, belief drift, sybil) across four architectures. The per-architecture attack-type tables below use a finer six-way attack taxonomy that the corpus does not carry, and are illustrations of the calibrated response-surface model rather than rows of that artifact: no value in them is read back from `full_evaluation_results.json`, and they should be cited as design-model figures, not measurements.

## Per-Architecture Parametric Detection Rates {#sec:parametric-per-arch}

*Note: The following detection rates are computed from the parametric simulation ($N=3{,}800$), not from live pipeline execution or LLM inference. They characterize CIF's design-level properties under calibrated conditions.*

### Claude Code (Hierarchical Architecture) {#sec:parametric-claude-code}

**Architecture Characteristics**:
\begin{itemize}
\item Primary agent: Orchestrator with full context
\item Sub-agents: Task-specific workers with limited scope
\item Communication: Unidirectional delegation
\item State: Centralized in orchestrator
\end{itemize}

Table: Claude Code parametric detection results by attack type. {#tab:parametric-claude-code-detection}

| Attack Type  | Baseline  | Firewall | Sandbox | Tripwires | Full CIF |
| --- | --- | --- | --- | --- | --- |
| Direct injection | 0.00 | 0.89 | 0.72 | 0.81 | 0.97 |
| Indirect injection | 0.00 | 0.82 | 0.68 | 0.78 | 0.95 |
| Nested injection | 0.00 | 0.76 | 0.65 | 0.84 | 0.94 |
| Trust exploitation | 0.00 | 0.58 | 0.71 | 0.89 | 0.92 |
| Belief manipulation | 0.00 | 0.67 | 0.79 | 0.85 | 0.94 |
| Coordination | 0.00 | 0.52 | 0.61 | 0.76 | 0.88 |

Table: Measured pipeline overhead against a control that does not run it. {#tab:parametric-claude-code-perf}

| Metric  | Baseline  | Full CIF | Delta |
| --- | --- | --- | --- |
| Latency (p50) | 0.0002 ms | 0.6102 ms | $+0.6100$ ms |
| Latency (p95) | 0.0002 ms | 0.9041 ms | $+0.9039$ ms |
| Latency (p99) | 0.0004 ms | 1.2429 ms | $+1.2425$ ms |
| Throughput | 3,201,474 msg/s | 1,784 msg/s | single-threaded, one process |
| Peak traced memory | 51 KiB | 84 KiB | $+32$ KiB |

*Measured by `scripts/run_overhead_control.py` over 1,595 messages (1,475 attacks and 120 benign), two passes in one process after a 50-message warmup. The control does the loop and no evaluation, so the Delta column is the cost of the defense and nothing else.*

*No percentage overhead is reported here, and the reason is the point. The control is the loop rather than a unit of agent work, so a ratio against it would have no referent. There is a denominator that does exist: measured against the mean agent turn each architecture took in \cref{sec:llm-validation-results}, the pipeline's added median latency is Claude Code 0.0076%, CrewAI 0.0061%.*

**Integrity preservation is not reported.** The framework offers no definition of belief or system integrity that anything in `src/` computes, no sustained or multi-vector attack scenario in the evaluation suite, and no undefended arm against which an integrity ratio could be formed. The nearest available signal is the colony benchmark's per-step integrity timeline in `colony_results.json`, which runs only under attack and so supplies no baseline. Reporting an integrity improvement would require all three. The undefended control arm added for the overhead measurement (`scripts/run_overhead_control.py`) supplies a baseline for cost but not for integrity, because no integrity metric exists to compare across it.

### AutoGPT (Autonomous Architecture) {#sec:parametric-autogpt}

Table: AutoGPT parametric detection results by attack type. {#tab:parametric-autogpt-detection}

| Attack Type  | Baseline  | Firewall | Sandbox | Tripwires | Full CIF |
| --- | --- | --- | --- | --- | --- |
| Direct injection | 0.00 | 0.91 | 0.69 | 0.77 | 0.96 |
| Indirect injection | 0.00 | 0.78 | 0.71 | 0.73 | 0.93 |
| Nested injection | 0.00 | 0.73 | 0.62 | 0.79 | 0.91 |
| Trust exploitation | 0.00 | 0.61 | 0.68 | 0.82 | 0.90 |
| Belief manipulation | 0.00 | 0.69 | 0.76 | 0.88 | 0.95 |
| Coordination | 0.00 | 0.48 | 0.55 | 0.71 | 0.85 |

**Overhead is not reported per architecture.** `create_full_pipeline()` takes no architecture argument and the adapters do not vary by one, so the pipeline's cost is a property of the pipeline rather than of the system it defends. The single overhead measurement in \cref{tab:parametric-claude-code-perf} applies to all four architectures.

### CrewAI (Role-Based Architecture) {#sec:parametric-crewai}

Table: CrewAI parametric detection results by attack type. {#tab:parametric-crewai-detection}

| Attack Type  | Baseline  | Firewall | Sandbox | Tripwires | Full CIF |
| --- | --- | --- | --- | --- | --- |
| Direct injection | 0.00 | 0.87 | 0.74 | 0.83 | 0.97 |
| Indirect injection | 0.00 | 0.80 | 0.70 | 0.79 | 0.94 |
| Nested injection | 0.00 | 0.74 | 0.67 | 0.82 | 0.93 |
| Trust exploitation | 0.00 | 0.65 | 0.73 | 0.91 | 0.94 |
| Belief manipulation | 0.00 | 0.72 | 0.81 | 0.86 | 0.95 |
| Coordination | 0.00 | 0.59 | 0.64 | 0.79 | 0.91 |

### LangGraph (Graph-Based Architecture) {#sec:parametric-langgraph}

Table: LangGraph parametric detection results by attack type. {#tab:parametric-langgraph-detection}

| Attack Type  | Baseline  | Firewall | Sandbox | Tripwires | Full CIF |
| --- | --- | --- | --- | --- | --- |
| Direct injection | 0.00 | 0.92 | 0.76 | 0.85 | 0.98 |
| Indirect injection | 0.00 | 0.85 | 0.73 | 0.81 | 0.96 |
| Nested injection | 0.00 | 0.79 | 0.69 | 0.86 | 0.95 |
| Trust exploitation | 0.00 | 0.67 | 0.75 | 0.88 | 0.93 |
| Belief manipulation | 0.00 | 0.74 | 0.82 | 0.89 | 0.96 |
| Coordination | 0.00 | 0.61 | 0.67 | 0.82 | 0.92 |

## Cross-Architecture Parametric Summary {#sec:parametric-cross-arch}

Table: Cross-architecture parametric detection summary (Full CIF). {#tab:parametric-cross-arch-summary}

*Design-model table.* The overall TPRs below (0.94--0.98) come from the calibrated
response surface over its six-way attack taxonomy, not from
`full_evaluation_results.json`, whose four-category cells give 1.00 / 0.98 / 1.00 /
1.00 for the same four architectures. The artifact-derived aggregates are the
detection-rate rows in the overall summary table further down, which the claim
registry pins.

| Architecture | Overall TPR | Strongest Category | Weakest Category |
| --- | --- | --- | --- |
| Claude Code | 0.94 | Direct injection (0.97) | Coordination (0.88) |
| AutoGPT | 0.94 | Direct injection (0.96) | Coordination (0.85) |
| CrewAI | 0.96 | Direct injection (0.97) | Coordination (0.91) |
| LangGraph | 0.98 | Direct injection (0.98) | Coordination (0.92) |

No per-architecture latency overhead is reported: the pipeline has no architecture argument, and the single measured overhead control is not an architecture comparison.

## Parametric Statistical Analysis {#sec:parametric-stats}

### Effect Sizes (Cohen's d) {#sec:parametric-cohens-d}

Table: Effect sizes (Cohen's $d$) for primary comparisons (parametric simulation). {#tab:parametric-effect-sizes}

| Comparison | Cohen's $d$ | Interpretation |
| --- | --- | --- |
| CIF vs Firewall-only | 1.10 | Large |
| CIF vs Sandbox-only | 1.80 | Large |
| CIF vs Tripwires-only | 0.90 | Large |
| CIF vs Invariants-only | 1.40 | Large |

### Odds Ratios {#sec:parametric-odds-ratios}

Table: Odds ratios for detection comparisons (parametric simulation). {#tab:parametric-odds-ratios}

| Comparison | OR | 95\% CI |
| --- | --- | --- |
| CIF detect vs Firewall | 4.8 | [3.1, 7.4] |
| CIF detect vs Sandbox | 8.2 | [5.4, 12.5] |

### Number Needed to Treat {#sec:parametric-nnt}

Table: Number needed to treat by attack type (parametric simulation). {#tab:parametric-nnt}

| Attack Type | Baseline DR | CIF DR (sim) | NNT |
| --- | --- | --- | --- |
| Injection (indirect) | 0.03 | 0.99 | 1.04 |
| Trust (impersonation) | 0.03 | 0.96 | 1.08 |
| Belief manipulation | 0.03 | 0.99 | 1.04 |
| Coordination (sybil) | 0.03 | 0.96 | 1.08 |

### Confidence Intervals {#sec:parametric-ci}

Table: Per-architecture design-model TPR with 95\% intervals (parametric simulation). {#tab:parametric-arch-ci}

| Architecture | TPR | 95\% interval (TPR) |
| --- | --- | --- |
| Claude Code | 0.94 | [0.90, 0.97] |
| AutoGPT | 0.94 | [0.90, 0.97] |
| CrewAI | 0.96 | [0.93, 0.98] |
| LangGraph | 0.98 | [0.95, 0.99] |

No FPR or FPR interval is reported: the historical simulation contains attacks only, with zero true negatives and a null FPR in every cell.

Table: Detection rate confidence intervals by attack subcategory (parametric simulation). {#tab:parametric-attack-ci}

| Subcategory | DR | Lower | Upper |
| --- | --- | --- | --- |
| Direct injection | 0.96 | 0.93 | 0.98 |
| Indirect injection | 0.94 | 0.90 | 0.97 |
| Nested injection | 0.93 | 0.89 | 0.96 |
| Identity impersonation | 0.92 | 0.86 | 0.96 |
| Trust inflation | 0.90 | 0.83 | 0.95 |
| Delegation abuse | 0.91 | 0.84 | 0.96 |
| Belief injection | 0.94 | 0.88 | 0.98 |
| Evidence fabrication | 0.92 | 0.85 | 0.97 |
| Progressive drift | 0.91 | 0.83 | 0.96 |
| Sybil attacks | 0.89 | 0.80 | 0.95 |
| Consensus poisoning | 0.88 | 0.78 | 0.94 |
| Timing attacks | 0.87 | 0.76 | 0.94 |

## Parameter Sensitivity Analysis (Parametric) {#sec:parametric-sensitivity}

> **Provenance**: The tables below are historical design-model illustrations, not pipeline measurements or rows copied from the current `output/data/sensitivity_results.json`. That artifact contains separate closed-form response-surface sweeps from `scripts/run_sensitivity_analysis.py`; it supplies no benign arm and does not reproduce the removed FPR, precision, or F1 values.

### Firewall Threshold Sensitivity {#sec:parametric-firewall-sensitivity}

The firewall uses **dual thresholds**: $\tau_1$ (hard-reject; inputs above this score are blocked outright) and $\tau_2$ (quarantine; inputs scoring in $(\tau_2, \tau_1]$ are sandboxed). Sensitivity analysis holds one threshold fixed while varying the other.

Table: Reject threshold ($\tau_1$) sensitivity — quarantine threshold held fixed at $\tau_2 = 0.5$ (parametric simulation). {#tab:parametric-firewall-tau1-sensitivity}

| $\tau_1$ | Design-model TPR | 95\% interval (TPR) |
| --- | --- | --- |
| 0.6 | 0.91 | [0.88, 0.93] |
| 0.7 | 0.87 | [0.84, 0.90] |
| 0.8 | 0.82 | [0.78, 0.85] |
| 0.9 | 0.72 | [0.67, 0.76] |

In this historical design-model table, lower $\tau_1$ corresponds to higher TPR. No precision, false-reject rate, FPR, or utility optimum is identifiable without a benign arm.

Table: Quarantine threshold ($\tau_2$) sensitivity — reject threshold held fixed at $\tau_1 = 0.7$ (parametric simulation). {#tab:parametric-firewall-tau2-sensitivity}

| $\tau_2$ | Design-model TPR | 95\% interval (TPR) |
| --- | --- | --- |
| 0.3 | 0.88 | [0.85, 0.91] |
| 0.4 | 0.91 | [0.88, 0.93] |
| 0.5 | 0.94 | [0.92, 0.96] |
| 0.55 | 0.94 | [0.91, 0.96] |
| 0.6 | 0.93 | [0.90, 0.95] |

The highest design-model TPR in this table occurs at $\tau_2=0.5$ and $0.55$. This attack-only sweep cannot identify an F1 or FPR optimum; the sweep held $\tau_1$ at $0.7$; this is a design-model setting, not the operational default of $0.8$.

### Trust Decay Factor Sensitivity {#sec:parametric-decay-sensitivity}

![Trust decay sensitivity, two panels. Panel A: effective trust across delegation-chain depth for representative $\delta$ values, computed from \texttt{TrustCalculus.delegate\_trust}, showing where bounded delegation prevents trust amplification. Panel B is schematic, not a measurement: its four trust-retention bars illustrate the shape of the argument and are produced by no artifact under \texttt{output/data}.](figures/trust_decay.pdf){#fig:trust-decay-sensitivity width=80%}

Table: Trust decay factor sensitivity analysis (parametric simulation). {#tab:parametric-decay-sensitivity}

| $\delta$ | $\delta^3$ | Design-model Detection Rate |
| --- | --- | --- |
| 0.6 | 0.216 | 0.95 |
| 0.7 | 0.343 | 0.94 |
| 0.8 | 0.512 | 0.94 |
| 0.9 | 0.729 | 0.91 |
| 0.95 | 0.857 | 0.87 |

### Corroboration Count Sensitivity {#sec:parametric-corroboration}

Table: Corroboration count sensitivity analysis (parametric simulation). {#tab:parametric-corroboration}

| $\kappa$ | Design-model Attack Bypass Rate | Design-model Latency Overhead |
| --- | --- | --- |
| 2 | 0.72 | +15\% |
| 3 | 0.58 | +24\% |
| 4 | 0.41 | +35\% |
| 5 | 0.28 | +48\% |

### Window Size Sensitivity {#sec:parametric-window}

Table: Sliding window size sensitivity analysis (parametric simulation). {#tab:parametric-window}

| Window Size | Design-model Detection Rate | Design-model Latency |
| --- | --- | --- |
| 50 | 0.85 | 4.2s |
| 100 | 0.91 | 8.5s |
| 200 | 0.94 | 17.2s |
| 500 | 0.96 | 43.1s |

### Parameter Interaction Effects {#sec:parametric-interactions}

Table: Two-way ANOVA interaction effects (parametric simulation). {#tab:parametric-interactions}

| Parameter A | Parameter B | $F$ | $p$ | $\eta^2$ |
| --- | --- | --- | --- | --- |
| $\tau_1$ | $\kappa$ | 4.12 | 0.017 | 0.04 |
| $\delta$ | $\kappa$ | 1.89 | 0.154 | 0.02 |
| $\tau_1$ | $w$ | 3.56 | 0.029 | 0.03 |

### Robustness to Attack Distribution Shift {#sec:parametric-robustness}

Table: Cross-validation with held-out attack types (parametric simulation). {#tab:parametric-generalization}

| Held-Out Type | Train DR | Test DR | Gap |
| --- | --- | --- | --- |
| Trust exploitation | 0.95 | 0.88 | $-7\%$ |
| Belief manipulation | 0.94 | 0.90 | $-4\%$ |
| Coordination | 0.95 | 0.85 | $-10\%$ |

### Illustrative Configuration (Parametric) {#sec:parametric-optimal-config}

Table: Historical design-model parameter configuration; not an empirically measured optimum. {#tab:parametric-recommended-config}

| Parameter | Value | Design-model rationale |
| --- | --- | --- |
| $\tau_1$ (reject) | 0.7 | Historical simulation setting; the operational default is 0.8, and no FPR or utility optimum is identifiable without benign inputs |
| $\tau_2$ (quarantine) | 0.5 | High design-model TPR in the attack-only sweep; $\tau_2 < \tau_1$ required |
| $\delta$ | 0.8 | Permits 3-hop delegation ($\delta^3 = 0.512$) while bounding amplification |
| $\kappa$ | 2 | Illustrates the modeled corroboration--latency trade-off |
| $w$ (window) | 100 | Historical design-model setting with 8.5s simulated latency, not a measured deployment bound |

## Minimal Viable Configurations (Parametric) {#sec:parametric-minimal}

Table: Minimal viable configurations (parametric simulation). {#tab:parametric-minimal-configs}

| Config | Components | Design-model TPR | Design-model Latency Overhead |
| --- | --- | --- | --- |
| Minimal-A | Firewall + Tripwires + Invariants | 0.91 | +14\% |
| Minimal-B | Firewall + Sandbox + Tripwires | 0.92 | +18\% |
| Minimal-C | Firewall + Tripwires + Drift | 0.90 | +12\% |

## Parametric Overall Summary {#sec:parametric-summary}

Table: Parametric simulation overall performance summary. {#tab:parametric-overall-summary}

| Metric | Value | Interval / provenance |
| --- | --- | --- |
| Detection Rate (simulation) | 0.994 | [0.96, 1.00] |
| Detection Rate — AutoGPT only | 0.974 | [0.96, 0.99] |
| False Positive Rate | Not measured | No benign arm in `full_evaluation_results.json` |
| Precision | Not measured | Requires false positives; no benign arm |
| F1 Score | Not measured | Requires precision; no benign arm |
| Latency overhead | $+0.61$ ms per message | measured; see \cref{tab:parametric-claude-code-perf} |
| Throughput | 1{,}784 msg/s | measured, single-threaded |
| Memory overhead | $+32$ KiB peak | measured |

### Summary {#sec:parametric-findings-summary}

\begin{enumerate}
\item **Design-level detection**: The parametric simulation achieves 96--100\% detection across all four architectures, establishing the CIF defense architecture's theoretical coverage ceiling under calibrated conditions. These rates characterize the design's intrinsic properties, not current adapter implementation performance.
\item **Architecture sensitivity**: Architectural differences are small but significant ($\eta^2 \approx 0.03$), with LangGraph (graph-based) achieving the highest design-level rates (0.98) and AutoGPT (autonomous) the lowest (0.94), consistent with attack-surface analysis.
\item **Illustrative parameters**: $\tau_1=0.7$, $\tau_2=0.5$, $\delta=0.8$, $\kappa=2$, and $w=100$ are historical design-model settings, not an F1 optimum or an operational recommendation; the operational reject default is 0.8. The parametric interaction analysis reports $\tau_1$--$\kappa$ interaction at $p=0.017$.
\item **Distinct evaluation modes**: The ablation experiment measures 89.0\% TPR on 100 attacks, while the architecture-agnostic multi-seed experiment measures 86.3\% mean attack detection over 30 seeds of 100 stratified attacks plus 120 benign messages each. Their numerical differences from the historical attack-only parametric band do not form matched-arm contrasts and do not identify a causal adapter-maturity effect.
\end{enumerate}
