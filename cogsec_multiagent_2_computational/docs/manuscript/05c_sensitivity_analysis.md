\newpage

# Parameter Sensitivity Analysis {#sec:sensitivity}

The parameter sensitivity analysis---characterizing how CIF performance varies with firewall threshold ($\tau$), trust decay factor ($\delta$), corroboration count ($\kappa$), and drift detection window size ($w$)---was conducted using the parametric simulation model. These results are consolidated in \cref{sec:parametric-analysis} (Supplementary S08) to maintain clear separation between parametric design exploration and empirical results.

> **Cross-reference**: See \cref{sec:parametric-sensitivity} for the complete sensitivity analysis, including firewall threshold sensitivity (\cref{sec:parametric-firewall-sensitivity}), trust decay sensitivity (\cref{tab:parametric-decay-sensitivity}), corroboration count sensitivity (\cref{tab:parametric-corroboration}), window size sensitivity (\cref{tab:parametric-window}), parameter interaction effects (\cref{tab:parametric-interactions}), robustness to distribution shift (\cref{tab:parametric-generalization}), and the empirically optimal configuration (\cref{tab:parametric-recommended-config}).

## Summary of Optimal Configuration

The parametric analysis identifies the following parameter configuration as F1-maximizing within that design model (\cref{tab:default-config}). These are parametric optima, not a statement of the operational defaults used by the real pipeline:

Table: Parametric F1-maximizing configuration (design-model optima, not operational defaults). {#tab:default-config}

| Parameter | Value | Rationale |
| --- | --- | --- |
| $\tau_1$ (reject) | 0.7 | Hard-reject threshold; maximizes security–utility tradeoff in parametric model |
| $\tau_2$ (quarantine) | 0.5 | Quarantine threshold; $\tau_2 < \tau_1$; F1-maximizing in parametric model |
| $\delta$ | 0.8 | Permits 3-hop delegation ($\delta^3 = 0.51$) |
| $\kappa$ | 2 | Best bypass-reduction-to-latency ratio |
| $w$ (window) | 100 | Drift detection within $\sim$8.5s |

The empirical evaluations reported in Sections \ref{sec:extended-results} and \ref{sec:extended-ablation} used the operational `FirewallConfig` reject default $\tau_1=0.8$, not the parametric design optimum $\tau_1=0.7$; the operational quarantine default is $\tau_2=0.5$. Future work should conduct sensitivity analysis using the real pipeline to test whether the parametric optima transfer under a separately defined empirical evaluation.
