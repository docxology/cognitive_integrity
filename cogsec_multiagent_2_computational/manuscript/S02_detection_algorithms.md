\newpage

# Detection Algorithms {#sec:detection-algorithms}

This supplementary section presents detection algorithm implementations for the cognitive attack detection methods defined in Part 1 \cite{friedman2026cogsec1}. Where \cref{sec:pseudocode} (Section 2a) presents the six core defense mechanisms (Firewall, Sandbox, Trust, Tripwires, Consensus, Drift Detection), this supplement presents the *detection analytics pipeline* that evaluates their output---including ROC analysis, multi-detector fusion, online/batch detection architectures, and false positive mitigation.

> **Cross-paper reading guide.**
> • **Formal detection bounds** (information-theoretic stealth–impact tradeoff, series/parallel composition) are in Part 1 \cite{friedman2026cogsec1} §4.3 and §5.
> • **Deployment-facing detector configuration** (thresholds, false-positive budgets, retraining cadence) appears in Part 3 \cite{friedman2026cogsec3} §5–§5d.
> • **Domain-calibrated detection** thresholds vary dramatically across operational sectors (millisecond drone swarms vs. year-scale diplomatic agents); see unified Part 3+4 \cite{friedman2026cogsec3}, Sections 9--10, for per-domain recalibration examples.
> • **Code pointers**: online/batch detectors in [`src/core/online_detection.py`](../src/core/online_detection.py) and [`src/core/batch_detection.py`](../src/core/batch_detection.py); ROC analysis in [`src/evaluation/roc.py`](../src/evaluation/); multi-detector fusion in [`src/composition/fusion.py`](../src/composition/).

## ROC Analysis Algorithms

### Algorithm 1: ROC Curve Construction

\begin{algorithm}
\caption{ROC Curve Construction}
\begin{algorithmic}[1]
\Require Detector $D$, attack samples $X_{\text{attack}}$, benign samples $X_{\text{benign}}$, threshold count $n$
\Ensure ROC curve, AUC, optimal threshold $\tau^*$
\State Compute scores: $S_{\text{attack}} \gets [D(x) : x \in X_{\text{attack}}]$
\State Compute scores: $S_{\text{benign}} \gets [D(x) : x \in X_{\text{benign}}]$
\State Generate thresholds: $T \gets \text{linspace}(\min(S), \max(S), n)$
\For{each $\tau \in T$}
    \State $\text{TPR}[\tau] \gets |S_{\text{attack}} > \tau| / |X_{\text{attack}}|$
    \State $\text{FPR}[\tau] \gets |S_{\text{benign}} > \tau| / |X_{\text{benign}}|$
\EndFor
\State $\text{AUC} \gets \int \text{TPR} \, d(\text{FPR})$ \Comment{Trapezoidal integration}
\State $\tau^* \gets \argmax_\tau (\text{TPR}[\tau] - \text{FPR}[\tau])$ \Comment{Youden's J}
\State \Return $(\text{ROC}, \text{AUC}, \tau^*)$
\end{algorithmic}
\end{algorithm}
\label{alg:roc-construction}

## Detector Performance Results

Table: Detector performance comparison via ROC metrics. {#tab:detector-roc}

| Detector  | AUC  | F1-max $\tau$ | TPR@1\%FPR | TPR@5\%FPR |
| --- | --- | --- | --- | --- |
| Drift Score | 0.87 | 0.42 | 0.61 | 0.78 |
| Deviation Score | 0.82 | 0.55 | 0.52 | 0.71 |
| Provenance Check | 0.91 | 0.38 | 0.74 | 0.86 |
| Firewall | 0.85 | 0.60 | 0.58 | 0.75 |
| Tripwire | 0.79 | 0.45 | 0.48 | 0.65 |
| Ensemble | **0.94** | 0.35 | **0.82** | **0.91** |

*Note: These are design-level detector AUC values from parametric evaluation on the calibrated attack corpus. Empirical ensemble performance with current adapter implementations shows lower realized detection rates (see \cref{sec:extended-results}).*

Table: Empirical AUC with 95\% confidence intervals. {#tab:auc-ci}

| Detector  | AUC  | 95\% CI |
| --- | --- | --- |
| Drift Score | 0.87 | [0.84, 0.90] |
| Ensemble | 0.94 | [0.92, 0.96] |

## Multi-Detector Fusion Algorithm

\begin{algorithm}
\caption{Multi-Detector Fusion}
\label{alg:fusion}
\begin{algorithmic}[1]
\Require Detectors $[D_1, \ldots, D_k]$, training data $(X, y)$, fusion type
\Ensure Fusion function $f_{\text{fused}}$, threshold $\tau_{\text{fused}}$
\State Generate scores: $S \gets [[D_i(x) : x \in X] : D_i \in \text{detectors}]^T$
\If{fusion\_type = ``weighted''}
    \State $w \gets \text{LinearRegression}(S, y).\text{coef}$
    \State $w \gets \text{softmax}(w)$
    \State $f_{\text{fused}} \gets \lambda s: w \cdot s$
\ElsIf{fusion\_type =``voting''}
    \State $(\tau^*, q^*) \gets \argmax_{\tau,q} \text{accuracy}(S, y, \tau, q)$
    \State $f_{\text{fused}} \gets \lambda s: \sum_i \mathbb{1}[s_i > \tau_i^*] \geq q^*$
\ElsIf{fusion\_type = ``learned''}
    \State Train MLP: $\theta^* \gets \argmin_\theta \mathcal{L}(S, y; \theta)$
    \State $f_{\text{fused}} \gets \lambda s: \text{MLP}(s; \theta^*)$
\EndIf
\State Calibrate $\tau_{\text{fused}}$ on validation set
\State \Return $(f_{\text{fused}}, \tau_{\text{fused}})$
\end{algorithmic}
\end{algorithm}
\label{alg:multi-detector-fusion}

Table: Fusion strategy performance comparison. {#tab:fusion-performance}

| Fusion Strategy  | AUC  | FPR@90\%TPR | Latency |
| --- | --- | --- | --- |
| Best Single (Provenance) | 0.91 | 8.2\% | 15ms |
| Weighted Average | 0.93 | 5.4\% | 25ms |
| Majority Voting | 0.92 | 6.1\% | 20ms |
| Learned (MLP) | **0.94** | **4.2\%** | 30ms |
| Learned (Attention) | **0.95** | **3.8\%** | 45ms |

*Note: Fusion strategy AUC values are from parametric evaluation. See \cref{sec:parametric-analysis} for the complete parametric analysis.*

## Online Detection Algorithm

\begin{algorithm}
\caption{Online Detection Loop}
\begin{algorithmic}[1]
\Require Message stream, window size $w$, detection threshold $\theta_{\text{det}}$
\Comment{Note: $\theta_{\text{det}}$ is a statistical anomaly threshold, distinct from the firewall thresholds $\tau_1$ (REJECT) and $\tau_2$ (QUARANTINE).}
\State Initialize: $\text{window} \gets \text{CircularBuffer}(w)$
\State Initialize: $\text{stats} \gets \text{OnlineStatistics}()$
\Loop \Comment{For each message $m$ in stream}
    \State $\text{features} \gets \text{extract}(m)$
    \State $\text{stats}.\text{update}(\text{features})$
    \State $z \gets (\text{features} - \text{stats}.\text{mean}) / \text{stats}.\text{std}$
    \State $\text{score} \gets \|z\|$
    \If{$\text{score} > \theta_{\text{det}}$}
        \State $\text{emit\_alert}(m, \text{score})$
        \State **yield** \textsc{quarantine}
    \Else
        \State **yield** \textsc{accept}
    \EndIf
    \State $\text{window}.\text{push}(\text{features})$
\EndLoop
\end{algorithmic}
\end{algorithm}
\label{alg:online-detection}

## Batch Detection Algorithm

\begin{algorithm}
\caption{Batch Detection Analysis}
\begin{algorithmic}[1]
\Require Full interaction history $H$, detectors $[D_1, \ldots, D_k]$
\Ensure Anomalies, attack patterns, optimal thresholds
\State $\text{features} \gets \text{extract\_all}(H)$
\State $\text{patterns} \gets \text{analyze\_sessions}(H)$
\State $\text{anomalies} \gets \text{detect\_anomalies}(\text{patterns})$
\For{each detector $D_i$}
    \State $\text{scores}[D_i] \gets D_i.\text{batch\_score}(\text{features})$
\EndFor
\State $\text{attack\_patterns} \gets \text{mine\_patterns}(H, \text{scores})$
\State $\tau^* \gets \text{optimize\_thresholds}(\text{scores}, \text{labels})$
\State \Return $(\text{anomalies}, \text{attack\_patterns}, \tau^*)$
\end{algorithmic}
\end{algorithm}
\label{alg:batch-detection}

Table: Hybrid configuration trade-off analysis. {#tab:hybrid-tradeoffs}

| Configuration  | Detection Rate  | Latency | Cost |
| --- | --- | --- | --- |
| Online Only | 87\% | 10ms | Low |
| Batch Only | 94\% | N/A (forensic) | Medium |
| Hybrid (hourly batch) | 92\% | 10ms + lag | Medium |
| Hybrid (continuous) | **94\%** | 10ms | High |

*Note: These detection rates reflect parametric evaluation of the detector architecture. Realized pipeline detection rates are lower with current adapter implementations (see \cref{sec:extended-results}).*

## False Positive Mitigation Results

Table: False positive root causes and mitigation strategies. {#tab:fp-root-causes}

| Cause  | Frequency  | Impact | Mitigation |
| --- | --- | --- | --- |
| Benign novelty | 35\% | High | Incremental learning |
| Threshold drift | 25\% | Medium | Adaptive thresholds |
| Feature noise | 20\% | Low | Smoothing |
| Label errors | 10\% | High | Label audit |
| Distribution shift | 10\% | High | Domain adaptation |

## Baseline Update Algorithm

\begin{algorithm}
\caption{Online Baseline Update}
\begin{algorithmic}[1]
\Require Alert, feedback $\in \{\text{FP}, \text{TP}\}$, learning rate $\eta$
\If{feedback = FP}
    \State $\mu \gets (1-\eta) \cdot \mu + \eta \cdot \text{alert.features}$
    \State $\sigma^2 \gets (1-\eta) \cdot \sigma^2 + \eta \cdot (\text{alert.features} - \mu)^2$
    \If{$\text{fp\_count} > \text{fp\_threshold}$}
        \State $\theta \gets \theta \cdot (1 + \Delta)$ \Comment{Raise threshold}
    \EndIf
\Else \Comment{feedback = TP}
    \State $\text{attack\_patterns}.\text{add}(\text{alert.pattern})$
    \If{$\text{tp\_count} > \text{tp\_threshold}$}
        \State $\theta \gets \theta \cdot (1 - \Delta)$ \Comment{Lower threshold}
    \EndIf
\EndIf
\end{algorithmic}
\end{algorithm}
\label{alg:baseline-update}

Table: False positive mitigation strategy effectiveness. {#tab:fp-mitigation-results}

| Strategy  | FPR Reduction  | TPR Impact | Complexity |
| --- | --- | --- | --- |
| Baseline | -- | -- | -- |
| Confirmation Cascade | $-60\%$ | $-5\%$ | Medium |
| Temporal Smoothing | $-40\%$ | $-3\%$ | Low |
| Contextual Whitelist | $-50\%$ | $-2\%$ | Medium |
| Incremental Learning | $-45\%$ | $+2\%$ | High |
| Cost-Sensitive | $-30\%$ | Variable | Low |
| **Combined** | $\mathbf{-75\%}$ | $\mathbf{-8\%}$ | High |

## Sliding Window Monitoring Algorithm

\begin{algorithm}
\caption{Sliding Window Monitoring}
\begin{algorithmic}[1]
\Require Monitoring period $T_m$, window size $w$, anomaly threshold $\theta_{\text{det}}$
\Comment{Note: $T_m$ denotes the monitoring interval (time units); $\theta_{\text{det}}$ is distinct from firewall thresholds $\tau_1$/$\tau_2$.}
\Loop \Comment{Every $T_m$ units}
    \State Collect cognitive state snapshot $\sigma_i^t$
    \For{each feature $k$}
        \State $\mu[k] \gets \alpha \cdot \mu[k] + (1-\alpha) \cdot f_k(\sigma_i^t)$
        \State $\sigma^2[k] \gets \alpha \cdot \sigma^2[k] + (1-\alpha) \cdot (f_k(\sigma_i^t) - \mu[k])^2$
    \EndFor
    \State Compute anomaly scores
    \If{any score $> \theta_{\text{det}}$}
        \State Log alert with context
        \State Trigger response protocol
    \EndIf
    \State Prune data older than $w$
\EndLoop
\end{algorithmic}
\end{algorithm}
\label{alg:sliding-window}

## Computational Complexity Summary {#sec:detection-complexity}

Table: Detection algorithm computational complexity. {#tab:detection-complexity}

| Algorithm | Time (per message) | Space | Suitable For |
| --- | --- | --- | --- |
| Online Detection (Alg.\ \ref{alg:online-detection}) | $O(d)$ | $O(w \cdot d)$ | Real-time streaming |
| Batch Detection (Alg.\ \ref{alg:batch-detection}) | $O(n \cdot k)$ | $O(n \cdot d)$ | Forensic analysis |
| Multi-Detector Fusion (Alg.\ \ref{alg:fusion}) | $O(k)$ | $O(k)$ | Score aggregation |
| Baseline Update (Alg.\ \ref{alg:baseline-update}) | $O(d)$ | $O(d)$ | Continuous adaptation |
| Sliding Window (Alg.\ \ref{alg:sliding-window}) | $O(d)$ | $O(w \cdot d)$ | Periodic monitoring |

Where $d$ = feature dimension, $w$ = window size, $k$ = number of detectors, $n$ = history length.

\newpage

## Information-Geometric Detection {#sec:ig-detection}

The Fisher-Rao metric on the belief simplex $\Delta^{n-1}$ provides a principled distance measure for detecting belief manipulation that is more sensitive to distributional shifts than KL divergence alone, particularly for attacks that operate near distribution boundaries. These algorithms implement the information-geometric detection layer described in \cref{sec:information-geometry}.

### Algorithm IG.1: Fisher-Rao Geodesic Drift Detector

\begin{algorithm}
\caption{Fisher-Rao Geodesic Drift Detector}
\begin{algorithmic}[1]
\Require Belief stream $\{p_t\}$, window $w$, geodesic threshold $\rho$, smoothing $\alpha$
\Ensure Drift alerts with geodesic distance scores
\State Initialize: $\bar{p} \gets p_0$, $\text{window} \gets \text{CircularBuffer}(w)$
\Loop \Comment{For each new belief state $p_t$}
    \State Compute Fisher information matrix: $G_{ii}(p) \gets 1/p_i$, $G_{ij}(p) \gets 0$ for $i \neq j$
    \State Compute geodesic distance: $d_\text{FR}(p_t, \bar{p}) \gets 2 \arccos\!\left(\textstyle\sum_i \sqrt{p_t[i] \cdot \bar{p}[i]}\right)$
    \If{$d_\text{FR}(p_t, \bar{p}) > \rho$}
        \State $\text{emit\_alert}(t, d_\text{FR}, p_t, \bar{p})$
        \State **yield** \textsc{quarantine}
    \Else
        \State $\bar{p} \gets \alpha \cdot \bar{p} + (1-\alpha) \cdot p_t$ \Comment{EMA baseline update}
        \State **yield** \textsc{accept}
    \EndIf
    \State $\text{window}.\text{push}(p_t)$
\EndLoop
\end{algorithmic}
\end{algorithm}
\label{alg:fisher-rao-drift}

**Relationship to Theorem CG.1.** The geodesic threshold $\rho$ in Algorithm IG.1 corresponds to the sandbox radius derived in \cref{sec:information-geometry}: setting $\rho = 2\arccos(\sqrt{1 - \kappa \cdot \varepsilon_\text{precision}})$ makes the drift detector and the belief sandbox mutually consistent---any update rejected by the sandbox would also trigger an alert, and vice versa.

### Algorithm IG.2: Natural Gradient Anomaly Score

\begin{algorithm}
\caption{Natural Gradient Anomaly Score}
\label{alg:natural-gradient-anomaly}
\begin{algorithmic}[1]
\Require Belief $p$, detection scores $s \in \mathbb{R}^n$, threshold $\theta_\text{nat}$
\Ensure Natural gradient score $\nabla_\text{nat}$, anomaly flag
\State Compute Fisher information: $G_{ii}(p) \gets 1/p_i$
\State Compute natural gradient: $(\nabla_\text{nat})_i \gets p_i \cdot s_i$ \Comment{$G^{-1}\nabla = \text{diag}(p)\cdot s$}
\State Compute anomaly score: $\text{score} \gets \|\nabla_\text{nat}\|_1 = \sum_i |p_i \cdot s_i|$
\If{$\text{score} > \theta_\text{nat}$}
    \State **return** $(\nabla_\text{nat}, \textsc{anomalous})$
\Else
    \State **return** $(\nabla_\text{nat}, \textsc{normal})$
\EndIf
\end{algorithmic}
\end{algorithm}
\label{alg:natural-gradient}

The natural gradient anomaly score weights each dimension's detection signal by the current belief probability, making the score sensitive to manipulations of high-probability beliefs (which carry more semantic content) while remaining robust to noise in low-probability dimensions.

Table: Information-geometric vs.\ KL-based detection comparison. {#tab:ig-vs-kl}

| Detector | AUC | TPR@1\%FPR | Geodesic Sensitivity | Boundary Attacks |
| :--- | :--- | :--- | :--- | :--- |
| KL Divergence | 0.87 | 0.61 | Low | Missed |
| Fisher-Rao Geodesic (IG.1) | 0.90 | 0.71 | High | Detected |
| Natural Gradient (IG.2) | 0.88 | 0.67 | Medium | Partial |
| Ensemble (KL + Fisher-Rao) | **0.93** | **0.79** | High | Detected |

*Note: Geodesic sensitivity measures detector response to attacks that travel along shortest-path trajectories on the belief manifold—these minimize detection risk while maximizing impact, and are precisely the attacks that KL-based detectors miss most often.*

## Summary (Updated)

These algorithms implement the detection methodology defined in Part 1, providing: (1) ROC curve construction with Youden's J threshold optimization, (2) multi-detector fusion via weighted averaging, majority voting, or learned MLP/attention, (3) online and batch detection architectures with configurable latency/accuracy trade-offs, (4) false positive mitigation achieving 75\% FPR reduction with 8\% TPR cost, (5) adaptive baseline update for non-stationary environments, and (6) information-geometric detection (Algorithms IG.1--IG.2) using the Fisher-Rao geodesic distance and natural gradient anomaly score for enhanced detection of boundary-trajectory attacks. The hybrid online+batch architecture (\cref{tab:hybrid-tradeoffs}) achieves the best detection-latency profile for production deployments; pairing it with the Fisher-Rao geodesic detector (\cref{tab:ig-vs-kl}) improves AUC from 0.94 to an estimated 0.95--0.96 on geodesic attack variants.

For formal definitions and theoretical foundations, see Part 1's Detection Methods section and Part 2, \cref{sec:information-geometry}.
