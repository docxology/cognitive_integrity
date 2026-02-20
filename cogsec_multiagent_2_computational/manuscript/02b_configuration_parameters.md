\newpage

# Framework Configuration Reference {#sec:config-params}

This section documents configuration parameters for all CIF defense components. For algorithm pseudocode, see \cref{sec:methodology}. Sensitivity analysis quantifying parameter impact is provided in \cref{sec:sensitivity}.

> **Reproducibility**: Default values were determined via `scripts/run_sensitivity_analysis.py` → `output/data/sensitivity_results.json`. Empirically validated ranges are reported across all four architecture types.

## Core Framework Parameters {#sec:core-params}

**Table: Core framework configuration parameters.** {#tab:core-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Acceptance threshold | $\tau_{accept}$ | 0.7 | $(0, 1)$ | Minimum belief confidence |
| Trusted source threshold | $\tau_{trusted}$ | 0.9 | $(0, 1)$ | Direct promotion threshold |
| Corroboration count | $\kappa$\footnote{Throughout this paper, $\kappa$ denotes the corroboration threshold count in the CIF framework, distinct from Cohen's $\kappa$ (kappa) coefficient used as an inter-rater reliability measure in \cref{sec:exp-setup}.} | 2 | $[1, n-1]$ | Required confirmations |
| Consistency threshold | $\tau$ | 0.8 | $(0, 1)$ | Contradiction detection |
| Random seed | $s$ | 42 | $\mathbb{Z}^+$ | Reproducibility seed |

## Trust Calculus Parameters {#sec:trust-params}

**Table: Trust calculus configuration parameters.** {#tab:trust-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Base trust weight | $\alpha$ | 0.3 | $[0, 1]$ | Direct observation weight |
| Reputation weight | $\beta$ | 0.5 | $[0, 1]$ | Historical accuracy weight |
| Context weight | $\gamma$ | 0.2 | $[0, 1]$ | Task-specific weight |
| Trust decay factor | $\delta$ | 0.8 | $(0, 1)$ | Delegation chain decay |
| Learning rate | $\eta$ | 0.1 | $(0, 1)$ | Reputation update rate |
| Penalty factor | $\rho$ | 2.0 | $[1, 5]$ | Failure penalty multiplier |

**Constraint**: $\alpha + \beta + \gamma = 1$ (see Part 1, Equation 5). The default $\alpha = 0.3$, $\beta = 0.5$, $\gamma = 0.2$ weights direct observation, historical reputation, and contextual trust respectively.

## Firewall Parameters {#sec:firewall-params}

**Table: Cognitive firewall configuration parameters.** {#tab:firewall-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Quarantine threshold | $\tau_2$ | 0.5 | $(0, 1)$ | Sandbox routing |
| Injection weight | $w_1$ | 0.4 | $[0, 1]$ | Pattern match weight |
| Semantic weight | $w_2$ | 0.3 | $[0, 1]$ | Embedding similarity weight |
| Anomaly weight | $w_3$ | 0.3 | $[0, 1]$ | Structural analysis weight |

## Sandbox Parameters {#sec:sandbox-params}

**Table: Belief sandbox configuration parameters.** {#tab:sandbox-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Check interval | $\tau_{check}$ | 60s | $[10, 600]$ | Verification frequency |
| Max provisional | $N_{max}$ | 1000 | $[100, 10000]$ | Memory limit |

## Tripwire Parameters {#sec:tripwire-params}

**Table: Cognitive tripwire configuration parameters.** {#tab:tripwire-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Critical epsilon | $\epsilon_{critical}$ | 0.05 | $(0, 0.2)$ | Critical alert threshold |
| Medium epsilon | $\epsilon_{medium}$ | 0.08 | $(0, 0.3)$ | Medium threshold |
| Check interval | $\tau_{tripwire}$ | 30s | $[5, 300]$ | Monitoring frequency |
| Canary tolerance | $\epsilon_{canary}$ | 0.1 | $(0, 0.5)$ | Canary deviation tolerance |

## Drift Detection Parameters {#sec:drift-params}

**Table: Drift detection configuration parameters.** {#tab:drift-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| KL threshold | $\theta_{drift}$ | 0.3 | $(0, 2)$ | Alert threshold |
| Max delta weight | $\lambda$ | 0.3 | $[0, 1]$ | Sudden change weight |
| Smoothing factor | $\alpha_{ema}$ | 0.1 | $(0, 1)$ | EMA decay |

## Consensus Parameters {#sec:consensus-params}

**Table: Byzantine consensus configuration parameters.** {#tab:consensus-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Max rounds | $R_{max}$ | 10 | $[3, 50]$ | Termination limit |
| Quorum fraction | $q$ | 2/3 | $(0.5, 1)$ | Agreement threshold |

## Invariant Parameters {#sec:invariant-params}

**Table: Invariant enforcement configuration parameters.** {#tab:invariant-params}

| Parameter | Symbol | Default | Range | Description |
| --- | --- | --- | --- | --- |
| Check interval | $\tau_{inv}$ | 60s | $[10, 600]$ | Invariant check frequency |

## Deployment Profiles {#sec:tuning-profiles}

**Table: Recommended configuration profiles by deployment scenario.** {#tab:tuning-profiles}

| Profile | Configuration |
| --- | --- |
| Low latency | $\tau_1 = 0.9$, $w = 50$, $T_{round} = 2000$ |
| High throughput | $N_{max} = 5000$, $\tau_{check} = 120$, disable sandbox |
| Byzantine-heavy | $\delta = 0.6$, $R_{max} = 20$, $q = 0.75$ |
