\newpage

# Detection Algorithms {#sec:detection-algorithms}

This supplementary section presents detection algorithm implementations for the cognitive attack detection methods defined in Part 1. Where \cref{sec:pseudocode} (Section 2a) presents the six core defense mechanisms (Firewall, Sandbox, Trust, Tripwires, Consensus, Drift Detection), this supplement presents the *detection analytics pipeline* that evaluates their output---including ROC analysis, multi-detector fusion, online/batch detection architectures, and false positive mitigation.

## ROC Analysis Algorithms

### Algorithm 1: ROC Curve Construction

\begin{algorithm}
\caption{ROC Curve Construction}
\label{alg:roc-construction}
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

## Detector Performance Results

**Table: Detector performance comparison via ROC metrics.** {#tab:detector-roc}

| Detector  | AUC  | F1-max $\tau$ | TPR@1\%FPR | TPR@5\%FPR |
| --- | --- | --- | --- | --- |
| Drift Score | 0.87 | 0.42 | 0.61 | 0.78 |
| Deviation Score | 0.82 | 0.55 | 0.52 | 0.71 |
| Provenance Check | 0.91 | 0.38 | 0.74 | 0.86 |
| Firewall | 0.85 | 0.60 | 0.58 | 0.75 |
| Tripwire | 0.79 | 0.45 | 0.48 | 0.65 |
| Ensemble | **0.94** | 0.35 | **0.82** | **0.91** |

**Table: Empirical AUC with 95\% confidence intervals.** {#tab:auc-ci}

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

**Table: Fusion strategy performance comparison.** {#tab:fusion-performance}

| Fusion Strategy  | AUC  | FPR@90\%TPR | Latency |
| --- | --- | --- | --- |
| Best Single (Provenance) | 0.91 | 8.2\% | 15ms |
| Weighted Average | 0.93 | 5.4\% | 25ms |
| Majority Voting | 0.92 | 6.1\% | 20ms |
| Learned (MLP) | **0.94** | **4.2\%** | 30ms |
| Learned (Attention) | **0.95** | **3.8\%** | 45ms |

## Online Detection Algorithm

\begin{algorithm}
\caption{Online Detection Loop}
\label{alg:online-detection}
\begin{algorithmic}[1]
\Require Message stream, window size $w$, threshold $\theta$
\State Initialize: $\text{window} \gets \text{CircularBuffer}(w)$
\State Initialize: $\text{stats} \gets \text{OnlineStatistics}()$
\Loop \Comment{For each message $m$ in stream}
    \State $\text{features} \gets \text{extract}(m)$
    \State $\text{stats}.\text{update}(\text{features})$
    \State $z \gets (\text{features} - \text{stats}.\text{mean}) / \text{stats}.\text{std}$
    \State $\text{score} \gets \|z\|$
    \If{$\text{score} > \theta$}
        \State $\text{emit\_alert}(m, \text{score})$
        \State **yield** \textsc{quarantine}
    \Else
        \State **yield** \textsc{accept}
    \EndIf
    \State $\text{window}.\text{push}(\text{features})$
\EndLoop
\end{algorithmic}
\end{algorithm}

## Batch Detection Algorithm

\begin{algorithm}
\caption{Batch Detection Analysis}
\label{alg:batch-detection}
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

**Table: Hybrid configuration trade-off analysis.** {#tab:hybrid-tradeoffs}

| Configuration  | Detection Rate  | Latency | Cost |
| --- | --- | --- | --- |
| Online Only | 87\% | 10ms | Low |
| Batch Only | 94\% | N/A (forensic) | Medium |
| Hybrid (hourly batch) | 92\% | 10ms + lag | Medium |
| Hybrid (continuous) | **94\%** | 10ms | High |

## False Positive Mitigation Results

**Table: False positive root causes and mitigation strategies.** {#tab:fp-root-causes}

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
\label{alg:baseline-update}
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

**Table: False positive mitigation strategy effectiveness.** {#tab:fp-mitigation-results}

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
\label{alg:sliding-window}
\begin{algorithmic}[1]
\Require Monitoring period $\tau$, window size $w$, threshold $\theta$
\Loop \Comment{Every $\tau$ units}
    \State Collect cognitive state snapshot $\sigma_i^t$
    \For{each feature $k$}
        \State $\mu[k] \gets \alpha \cdot \mu[k] + (1-\alpha) \cdot f_k(\sigma_i^t)$
        \State $\sigma^2[k] \gets \alpha \cdot \sigma^2[k] + (1-\alpha) \cdot (f_k(\sigma_i^t) - \mu[k])^2$
    \EndFor
    \State Compute anomaly scores
    \If{any score $> \theta$}
        \State Log alert with context
        \State Trigger response protocol
    \EndIf
    \State Prune data older than $w$
\EndLoop
\end{algorithmic}
\end{algorithm}

## Computational Complexity Summary {#sec:detection-complexity}

**Table: Detection algorithm computational complexity.** {#tab:detection-complexity}

| Algorithm | Time (per message) | Space | Suitable For |
| --- | --- | --- | --- |
| Online Detection (Alg.\ \ref{alg:online-detection}) | $O(d)$ | $O(w \cdot d)$ | Real-time streaming |
| Batch Detection (Alg.\ \ref{alg:batch-detection}) | $O(n \cdot k)$ | $O(n \cdot d)$ | Forensic analysis |
| Multi-Detector Fusion (Alg.\ \ref{alg:fusion}) | $O(k)$ | $O(k)$ | Score aggregation |
| Baseline Update (Alg.\ \ref{alg:baseline-update}) | $O(d)$ | $O(d)$ | Continuous adaptation |
| Sliding Window (Alg.\ \ref{alg:sliding-window}) | $O(d)$ | $O(w \cdot d)$ | Periodic monitoring |

Where $d$ = feature dimension, $w$ = window size, $k$ = number of detectors, $n$ = history length.

## Summary

These algorithms implement the detection methodology defined in Part 1, providing: (1) ROC curve construction with Youden's J threshold optimization, (2) multi-detector fusion via weighted averaging, majority voting, or learned MLP/attention, (3) online and batch detection architectures with configurable latency/accuracy trade-offs, (4) false positive mitigation achieving 75\% FPR reduction with 8\% TPR cost, and (5) adaptive baseline update for non-stationary environments. The hybrid online+batch architecture (\cref{tab:hybrid-tradeoffs}) achieves the best detection-latency profile for production deployments.

For formal definitions and theoretical foundations, see Part 1, Section 5.
