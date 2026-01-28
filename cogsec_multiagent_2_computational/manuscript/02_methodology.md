\newpage

# Methodology: Implementation Details {#sec:methodology}

This section provides pseudocode for major algorithms (\cref{sec:pseudocode}), configuration parameters (\cref{sec:config-params}), framework API reference (\cref{sec:framework-api}), deployment considerations (\cref{sec:deployment-checklist}), and integration examples (\cref{sec:integration-examples}).

> **Cross-Reference Note**: All algorithms in this section implement the formal definitions and theorems from Part 1 of this series. We cite specific theorems and definitions using the notation "(Part 1, Theorem X.Y)" to enable readers to trace implementations to their theoretical foundations.

## Pseudocode for Major Algorithms {#sec:pseudocode}

### Algorithm 1: Cognitive Firewall {#sec:alg-firewall}

The cognitive firewall classifies incoming messages using a multi-stage detection pipeline. This algorithm implements the formal Cognitive Firewall definition from Part 1, Section 5.1, which specifies the three-stage filtering ($F_{sig} \to F_{sem} \to F_{anom}$) with combined threat scoring (Part 1, Definition 5.1).

\begin{algorithm}
\caption{Cognitive Firewall Classification}
\label{alg:firewall-impl}
\begin{algorithmic}[1]
\Require message $m$, context $ctx$
\Ensure decision $\in \{\text{ACCEPT}, \text{QUARANTINE}, \text{REJECT}\}$
\Function{Classify}{$m$, $ctx$}
  \State \Comment{Stage 1: Pattern-based injection detection}
  \State $S_{inj} \gets 0$
  \For{each pattern $p \in \mathcal{P}_{injection}$}
    \If{$\text{Match}(m, p)$}
      \State $S_{inj} \gets S_{inj} + p.weight$
    \EndIf
  \EndFor
  \State \Comment{Stage 2: Semantic analysis}
  \State $\mathbf{e} \gets \text{Embed}(m)$
  \State $S_{sem} \gets \text{CosineSim}(\mathbf{e}, \mathbf{c}_{attack})$
  \State \Comment{Stage 3: Anomaly detection}
  \State $S_{anom} \gets \text{IsolationForest.Score}(\text{Features}(m, ctx))$
  \State \Comment{Combine scores}
  \State $S_{combined} \gets w_1 \cdot S_{inj} + w_2 \cdot S_{sem} + w_3 \cdot S_{anom}$
  \State \Comment{Decision logic}
  \If{$S_{combined} > \tau_1$}
    \State \Return REJECT
  \ElsIf{$S_{combined} > \tau_2$}
    \State \Return QUARANTINE
  \Else
    \State \Return ACCEPT
  \EndIf
\EndFunction
\end{algorithmic}
\end{algorithm}

### Algorithm 2: Belief Sandboxing {#sec:alg-sandbox}

Manages provisional beliefs with verification and promotion logic. This algorithm implements the Belief Sandboxing rules from Part 1, Section 5.2, including the sandboxing rule $\mathcal{B}_{provisional} \gets \mathcal{B}_{provisional} \cup \{(\phi, \pi, TTL)\}$ for unverified beliefs, and the promotion rule requiring $\kappa$-corroboration (Part 1, Definition 5.2 and Property 5.2).

\begin{algorithm}
\caption{Belief Sandbox Operations}
\label{alg:sandbox-impl}
\begin{algorithmic}[1]
\Require belief $\phi$, source $s$, trust score $\mathcal{T}_s$
\Ensure updated belief state
\Function{AddBelief}{$\phi$, $s$, $\mathcal{T}_s$}
  \State $\pi \gets \{source: s, timestamp: \text{Now}(), trust: \mathcal{T}_s, hash: \text{SHA256}(\phi)\}$
  \If{$\mathcal{T}_s \geq \tau_{trusted}$}
    \If{$\text{Consistent}(\mathcal{B}_{verified}, \phi)$}
      \State $\mathcal{B}_{verified} \gets \mathcal{B}_{verified} \cup \{\phi\}$
      \Return SUCCESS
    \Else
      \Return CONFLICT
    \EndIf
  \Else
    \State $\mathcal{B}_{provisional} \gets \mathcal{B}_{provisional} \cup \{(\phi, \pi, TTL_{default})\}$
    \Return PENDING
  \EndIf
\EndFunction
\Function{PromotionCheck}{}
  \For{each $(\phi, \pi, ttl) \in \mathcal{B}_{provisional}$}
    \If{$ttl \leq 0$}
      \State $\mathcal{B}_{provisional} \gets \mathcal{B}_{provisional} \setminus \{(\phi, \pi, ttl)\}$
      \State \textbf{continue}
    \EndIf
    \If{$\neg V(\pi)$}
      \State \textbf{continue}
    \EndIf
    \If{$\neg \text{Consistent}(\mathcal{B}_{verified}, \phi)$}
      \State \textbf{continue}
    \EndIf
    \If{$|\text{Corroborate}(\phi)| \geq \kappa$}
      \State $\mathcal{B}_{verified} \gets \mathcal{B}_{verified} \cup \{\phi\}$
      \State $\mathcal{B}_{provisional} \gets \mathcal{B}_{provisional} \setminus \{(\phi, \pi, ttl)\}$
    \EndIf
  \EndFor
\EndFunction
\end{algorithmic}
\end{algorithm}

### Algorithm 3: Trust Update {#sec:alg-trust}

Implements the trust calculus with decay and reputation updates. This is a direct implementation of Part 1's Trust Algebra (Section 3), including the bounded delegation with $\delta^d$ decay (Theorem 3.1: Trust Boundedness) and EMA-based reputation updates (Definition 3.3). The trust score is bounded by $\delta^d$ as proven in Part 1, ensuring that trust cannot be arbitrarily inflated through delegation chains.

\begin{algorithm}
\caption{Trust Update Operations}
\label{alg:trust-impl}
\begin{algorithmic}[1]
\Require agents $i$, $j$, interaction result
\Ensure updated trust score
\Function{UpdateTrust}{$i$, $j$, result}
  \State $T_{base} \gets \text{GetBaseTrust}(j)$
  \State $T_{rep} \gets \text{GetReputation}(j)$
  \State $T_{ctx} \gets \text{GetContextualTrust}(i, j)$
  \If{$result.success$}
    \State $\Delta \gets \eta \cdot (1 - T_{rep})$
  \Else
    \State $\Delta \gets -\eta \cdot T_{rep} \cdot \rho$
  \EndIf
  \State $T_{rep}^{new} \gets \text{Clip}(T_{rep} + \Delta, 0, 1)$
  \State $\text{SetReputation}(j, T_{rep}^{new})$
  \State $T_{combined} \gets \alpha \cdot T_{base} + \beta \cdot T_{rep}^{new} + \gamma \cdot T_{ctx}$
  \If{$i \neq \text{DirectObserver}(j)$}
    \State $d \gets \text{DelegationDepth}(i, j)$
    \State $T_{combined} \gets T_{combined} \cdot \delta^d$
  \EndIf
  \Return $T_{combined}$
\EndFunction
\Function{GetTransitiveTrust}{$i$, $k$, path}
  \State $T_{min} \gets 1.0$
  \For{each $(a, b) \in \text{ConsecutivePairs}(path)$}
    \State $T_{min} \gets \min(T_{min}, \mathcal{T}_{a \to b})$
  \EndFor
  \State $d \gets |path| - 1$
  \Return $T_{min} \cdot \delta^d$
\EndFunction
\end{algorithmic}
\end{algorithm}

### Algorithm 4: Cognitive Tripwire Monitoring {#sec:alg-tripwire}

Continuously monitors canary beliefs for unauthorized modifications. Tripwires implement the runtime defense mechanism defined in Part 1, Section 5.3 (Definition 5.3: Cognitive Tripwire), which specifies canary beliefs $\omega \in \mathcal{W}$ that should remain stable under normal operation. Any deviation triggers alerts for investigation.

\begin{algorithm}
\caption{Tripwire Monitoring}
\label{alg:tripwire-impl}
\begin{algorithmic}[1]
\Require agent state $\sigma$, tripwire set $\mathcal{W}$
\Ensure alert status
\Function{MonitorTripwires}{$\sigma$, $\mathcal{W}$}
  \State $alerts \gets []$
  \For{each $(\omega, p_{expected}) \in \mathcal{W}$}
    \State $p_{actual} \gets \sigma.\mathcal{B}[\omega]$
    \State $drift \gets |p_{actual} - p_{expected}|$
    \If{$drift > \epsilon_{drift}$}
      \State $alert \gets \{tripwire: \omega, expected: p_{expected}, actual: p_{actual},$
      \State \quad\quad\quad\quad $drift: drift, timestamp: \text{Now}(), severity: \text{Classify}(\omega, drift)\}$
      \State $alerts.\text{append}(alert)$
    \EndIf
  \EndFor
  \If{$|alerts| > 0$}
    \State $\text{AggregateAlerts}(alerts)$
    \State $\text{TriggerResponse}(alerts)$
  \EndIf
  \Return $alerts$
\EndFunction
\Function{ClassifySeverity}{$\omega$, $drift$}
  \If{$\omega.category \in \{\text{IDENTITY}, \text{PRINCIPAL}\}$}
    \If{$drift > \epsilon_{critical}$}
      \Return CRITICAL
    \ElsIf{$drift > \epsilon_{warning}$}
      \Return WARNING
    \EndIf
  \Else
    \If{$drift > 2 \cdot \epsilon_{critical}$}
      \Return CRITICAL
    \ElsIf{$drift > 2 \cdot \epsilon_{warning}$}
      \Return WARNING
    \EndIf
  \EndIf
  \Return INFO
\EndFunction
\end{algorithmic}
\end{algorithm}

### Algorithm 5: Byzantine Consensus {#sec:alg-byzantine}

Implements Byzantine fault-tolerant consensus for multi-agent decisions. This algorithm satisfies the Byzantine Agreement Requirement from Part 1, Section 5.5 (Theorem 5.3), ensuring that all honest agents agree on the same value when at most $f$ agents are Byzantine and $n \geq 3f + 1$. The implementation follows the "send, echo, ready" pattern described in Part 1.

\begin{algorithm}
\caption{Byzantine Consensus Protocol}
\label{alg:byzantine-impl}
\begin{algorithmic}[1]
\Require agents $\mathcal{A}$, proposition $\phi$, max Byzantine $f$
\Ensure consensus value or UNDECIDED
\Function{Consensus}{$\mathcal{A}$, $\phi$}
  \State $n \gets |\mathcal{A}|$
  \Require $n \geq 3f + 1$
  \State $votes \gets \{\}$
  \State \Comment{Phase 1: Collect votes}
  \For{each agent $a \in \mathcal{A}$}
    \State $vote \gets a.\text{GetBelief}(\phi)$
    \State $sig \gets a.\text{Sign}(vote)$
    \State $\text{Broadcast}(\{agent: a, vote: vote, sig: sig\})$
  \EndFor
  \State \Comment{Phase 2: Echo round}
  \For{each agent $a \in \mathcal{A}$}
    \State $received \gets \text{CollectMessages}(timeout = T_{round})$
    \State $verified \gets [m : m \in received \land \text{VerifySignature}(m)]$
    \If{$|verified| \geq n - f$}
      \State $majority \gets \text{MajorityValue}(verified)$
      \State $\text{Broadcast}(\{agent: a, echo: majority\})$
    \EndIf
  \EndFor
  \State \Comment{Phase 3: Decide}
  \State $echoes \gets \text{CollectEchoes}(timeout = T_{round})$
  \State $positive \gets |\{e : e.echo = \text{TRUE}\}|$
  \State $negative \gets |\{e : e.echo = \text{FALSE}\}|$
  \If{$positive > \frac{2n}{3}$}
    \Return ACCEPT
  \ElsIf{$negative > \frac{2n}{3}$}
    \Return REJECT
  \Else
    \Return UNDECIDED
  \EndIf
\EndFunction
\end{algorithmic}
\end{algorithm}

### Algorithm 6: Drift Detection {#sec:alg-drift}

Monitors belief distributions for anomalous changes over time. This implements Part 1's progressive drift detection (Section 6.1, Definition 6.1), using KL divergence to detect cumulative shifts.

\begin{algorithm}
\caption{Belief Drift Detection}
\label{alg:drift-impl}
\begin{algorithmic}[1]
\Require belief state $\mathcal{B}_{current}$, history $\mathcal{H}$, window $w$
\Ensure drift score and alerts
\Function{DetectDrift}{$\mathcal{B}_{current}$, $\mathcal{H}$, $w$}
  \State $\mathcal{B}_{baseline} \gets \text{GetBaselineDistribution}(\mathcal{H}, w)$
  \State \Comment{Compute KL divergence}
  \State $D_{KL} \gets 0$
  \For{each $\phi \in \text{Domain}(\mathcal{B}_{current})$}
    \State $p \gets \mathcal{B}_{current}[\phi]$
    \State $q \gets \mathcal{B}_{baseline}[\phi]$
    \If{$p > 0 \land q > 0$}
      \State $D_{KL} \gets D_{KL} + p \cdot \log(p / q)$
    \EndIf
  \EndFor
  \State \Comment{Compute max delta}
  \State $\Delta_{max} \gets 0$
  \For{each $\phi \in \text{Domain}(\mathcal{B}_{current})$}
    \State $\Delta \gets |\mathcal{B}_{current}[\phi] - \mathcal{B}_{baseline}[\phi]|$
    \State $\Delta_{max} \gets \max(\Delta_{max}, \Delta)$
  \EndFor
  \State \Comment{Combined score}
  \State $S_{drift} \gets D_{KL} + \lambda \cdot \Delta_{max}$
  \If{$S_{drift} > \theta_{drift}$}
    \State $alert \gets \{type: \text{DRIFT\_DETECTED}, score: S_{drift},$
    \State \quad\quad\quad\quad $kl: D_{KL}, max\_delta: \Delta_{max}, timestamp: \text{Now}()\}$
    \Return $(S_{drift}, [alert])$
  \EndIf
  \Return $(S_{drift}, [])$
\EndFunction
\end{algorithmic}
\end{algorithm}

## Configuration Parameters {#sec:config-params}

### Core Framework Parameters {#sec:core-params}

\begin{table}[htbp]
\centering
\caption{Core framework configuration parameters.}
\label{tab:core-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Trust decay factor & $\delta$ & 0.8 & $(0, 1)$ & Per-hop trust attenuation \\
Acceptance threshold & $\tau_{accept}$ & 0.7 & $(0, 1)$ & Minimum belief confidence \\
Trusted source threshold & $\tau_{trusted}$ & 0.9 & $(0, 1)$ & Direct promotion threshold \\
Corroboration count & $\kappa$ & 2 & $[1, n-1]$ & Required confirmations \\
Consistency threshold & $\tau$ & 0.8 & $(0, 1)$ & Contradiction detection \\
\bottomrule
\end{tabular}
\end{table}

### Trust Calculus Parameters {#sec:trust-params}

\begin{table}[htbp]
\centering
\caption{Trust calculus configuration parameters.}
\label{tab:trust-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Base trust weight & $\alpha$ & 0.3 & $[0, 1]$ & Architectural trust weight \\
Reputation weight & $\beta$ & 0.5 & $[0, 1]$ & Historical accuracy weight \\
Context weight & $\gamma$ & 0.2 & $[0, 1]$ & Task-specific weight \\
Learning rate & $\eta$ & 0.1 & $(0, 1)$ & Reputation update rate \\
Penalty factor & $\rho$ & 2.0 & $[1, 5]$ & Failure penalty multiplier \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Constraint}: $\alpha + \beta + \gamma = 1$ (see the trust function equation (Part 1, Equation 5)).

### Firewall Parameters {#sec:firewall-params}

\begin{table}[htbp]
\centering
\caption{Cognitive firewall configuration parameters.}
\label{tab:firewall-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Reject threshold & $\tau_1$ & 0.8 & $(0, 1)$ & Immediate rejection \\
Quarantine threshold & $\tau_2$ & 0.5 & $(0, 1)$ & Sandbox routing \\
Injection weight & $w_1$ & 0.4 & $[0, 1]$ & Pattern match weight \\
Semantic weight & $w_2$ & 0.35 & $[0, 1]$ & Embedding similarity weight \\
Anomaly weight & $w_3$ & 0.25 & $[0, 1]$ & Isolation forest weight \\
\bottomrule
\end{tabular}
\end{table}

### Sandbox Parameters {#sec:sandbox-params}

\begin{table}[htbp]
\centering
\caption{Belief sandbox configuration parameters.}
\label{tab:sandbox-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Default TTL & $TTL_{default}$ & 3600s & $[60, 86400]$ & Seconds before expiry \\
Check interval & $\tau_{check}$ & 60s & $[10, 600]$ & Verification frequency \\
Max provisional & $N_{max}$ & 1000 & $[100, 10000]$ & Memory limit \\
\bottomrule
\end{tabular}
\end{table}

### Tripwire Parameters {#sec:tripwire-params}

\begin{table}[htbp]
\centering
\caption{Cognitive tripwire configuration parameters.}
\label{tab:tripwire-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Drift epsilon & $\epsilon_{drift}$ & 0.1 & $(0, 0.5)$ & Alert threshold \\
Critical epsilon & $\epsilon_{critical}$ & 0.05 & $(0, 0.2)$ & Critical alert threshold \\
Warning epsilon & $\epsilon_{warning}$ & 0.08 & $(0, 0.3)$ & Warning threshold \\
Check interval & $\tau_{tripwire}$ & 30s & $[5, 300]$ & Monitoring frequency \\
\bottomrule
\end{tabular}
\end{table}

### Drift Detection Parameters {#sec:drift-params}

\begin{table}[htbp]
\centering
\caption{Drift detection configuration parameters.}
\label{tab:drift-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Window size & $w$ & 100 & $[10, 1000]$ & Historical samples \\
KL threshold & $\theta_{drift}$ & 0.5 & $(0, 2)$ & Alert threshold \\
Max delta weight & $\lambda$ & 0.3 & $[0, 1]$ & Sudden change weight \\
Smoothing factor & $\alpha_{ema}$ & 0.1 & $(0, 1)$ & EMA decay \\
\bottomrule
\end{tabular}
\end{table}

### Consensus Parameters {#sec:consensus-params}

\begin{table}[htbp]
\centering
\caption{Byzantine consensus configuration parameters.}
\label{tab:consensus-params}
\begin{tabular}{@{}lllll@{}}
\toprule
Parameter & Symbol & Default & Range & Description \\
\midrule
Round timeout & $T_{round}$ & 5000ms & $[1000, 30000]$ & Message collection window \\
Max rounds & $R_{max}$ & 10 & $[3, 50]$ & Termination limit \\
Quorum fraction & $q$ & 2/3 & $(0.5, 1)$ & Agreement threshold \\
\bottomrule
\end{tabular}
\end{table}

### Performance Tuning Profiles {#sec:tuning-profiles}

\begin{table}[htbp]
\centering
\caption{Recommended configuration profiles by deployment scenario.}
\label{tab:tuning-profiles}
\begin{tabular}{@{}lp{10cm}@{}}
\toprule
Scenario & Recommended Configuration \\
\midrule
High security & $\tau_1 = 0.6$, $\epsilon_{drift} = 0.05$, $\kappa = 3$ \\
Low latency & $\tau_1 = 0.9$, $w = 50$, $T_{round} = 2000$ \\
High throughput & $N_{max} = 5000$, $\tau_{check} = 120$, disable sandbox \\
Byzantine-heavy & $\delta = 0.6$, $R_{max} = 20$, $q = 0.75$ \\
\bottomrule
\end{tabular}
\end{table}

## Framework API Reference {#sec:framework-api}

This section documents the core framework modules that implement the theoretical constructs from Part 1. The complete source code is available in the companion repository.

### Trust Module {#sec:trust-api}

The trust module implements bounded trust delegation with configurable decay.

\begin{table}[htbp]
\centering
\caption{Trust module API: Core classes for trust computation and management.}
\label{tab:trust-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{TrustCalculus} & Computes composite trust: $T = \alpha \cdot T_{base} + \beta \cdot T_{rep} + \gamma \cdot T_{ctx}$. Implements delegation decay: $T_{delegated} = \min(T_{i \to j}, T_{j \to k}) \cdot \delta^d$ \\
\texttt{TrustMatrix} & Manages pairwise trust between $n$ agents with O(1) lookups and O(1) updates. Supports efficient path trust queries. \\
\texttt{ReputationTracker} & Tracks time-decayed reputation based on interaction history. Implements exponential decay for staleness. \\
\texttt{ContextAwareTrust} & Provides task-specific trust modulation based on capability matching. \\
\texttt{TrustMatrixWithDecay} & Extension of TrustMatrix with automatic time-based trust decay. \\
\bottomrule
\end{tabular}
\end{table}

**Key Methods**:

- `TrustCalculus.compute_trust(base, reputation, context)` → $[0, 1]$
- `TrustCalculus.delegate_trust(source_trust, target_trust, depth)` → bounded trust
- `TrustMatrix.get_delegation_trust(path)` → end-to-end path trust
- `ReputationTracker.record_interaction(source, target, outcome, timestamp)`

### Firewall Module {#sec:firewall-api}

The firewall module implements multi-stage classification for cognitive attack detection.

\begin{table}[htbp]
\centering
\caption{Firewall module API: Classes for message classification and threat detection.}
\label{tab:firewall-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{CognitiveFirewall} & Three-tier classifier (ACCEPT/QUARANTINE/REJECT) with configurable thresholds. Combines pattern matching, semantic analysis, and anomaly detection. \\
\texttt{PatternDetector} & Heuristic pattern matching with 15 injection patterns and 20 suspicious indicators. Weighted scoring based on pattern severity. \\
\texttt{SemanticSimilarityDetector} & Embedding-based similarity to known malicious patterns. Supports custom embedding models or hash-based fallback. \\
\texttt{MultiStageClassifier} & Orchestrates multi-stage detection pipeline with configurable stage weights. \\
\texttt{EnhancedCognitiveFirewall} & Extended firewall with provenance tracking and audit logging. \\
\bottomrule
\end{tabular}
\end{table}

**Key Methods**:

- `CognitiveFirewall.classify(message)` → Classification enum
- `CognitiveFirewall.process(message)` → (classification, processed\_message)
- `PatternDetector.score_injection(message)` → $[0, 1]$
- `SemanticSimilarityDetector.score_semantic_similarity(message)` → $[0, 1]$

### Consensus Module {#sec:consensus-api}

The consensus module implements Byzantine-tolerant agreement protocols.

\begin{table}[htbp]
\centering
\caption{Consensus module API: Classes for Byzantine-tolerant multi-agent decisions.}
\label{tab:consensus-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{ByzantineConsensus} & Core consensus with $n \geq 3f + 1$ guarantee. Implements three-phase protocol: collect, echo, decide. \\
\texttt{WeightedByzantineConsensus} & Trust-weighted voting where high-trust agents have greater influence. Prevents low-trust Sybil attacks. \\
\texttt{ConfidenceByzantineConsensus} & Votes weighted by agent confidence in their own belief. \\
\texttt{CombinedByzantineConsensus} & Multiplies trust and confidence weights for robust aggregation. \\
\texttt{QuorumVerification} & Action-level quorum gates for critical operations. Configurable approval thresholds. \\
\bottomrule
\end{tabular}
\end{table}

**Key Methods**:

- `ByzantineConsensus.submit_vote(vote)` → None
- `ByzantineConsensus.compute_consensus(proposition)` → (result, confidence)
- `QuorumVerification.approve(action_id, agent_id)` → bool (True if quorum reached)

### Detection Module {#sec:detection-api}

The detection module implements statistical anomaly and drift detection.

\begin{table}[htbp]
\centering
\caption{Detection module API: Classes for belief drift and anomaly detection.}
\label{tab:detection-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{DriftDetector} & KL-divergence based belief distribution drift detection. Sliding window comparison with configurable thresholds. \\
\texttt{AnomalyScorer} & Isolation forest anomaly scoring for belief state vectors. Trained on baseline distribution. \\
\bottomrule
\end{tabular}
\end{table}

### Provenance Module {#sec:provenance-api}

The provenance module implements information flow tracking with causal attribution.

\begin{table}[htbp]
\centering
\caption{Provenance module API: Classes for belief origin tracking and taint propagation.}
\label{tab:provenance-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{ProvenanceChain} & Linked list of provenance records tracking belief transformations. \\
\texttt{ProvenanceGraph} & DAG structure for complex multi-source belief provenance. Supports transitive queries. \\
\texttt{TaintLabel} & Labels for marking untrusted information sources. Propagates through belief operations. \\
\texttt{CausalAttribution} & Attributes beliefs to original evidence with contribution weights. \\
\bottomrule
\end{tabular}
\end{table}

### Sandbox Module {#sec:sandbox-api}

The sandbox module implements belief partitioning for provisional information management.

\begin{table}[htbp]
\centering
\caption{Sandbox module API: Classes for belief sandboxing and promotion.}
\label{tab:sandbox-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{SandboxManager} & Manages verified and provisional belief partitions. Enforces TTL expiry and consistency checks. \\
\texttt{BeliefPartition} & Container for beliefs with shared trust properties. Supports batch operations. \\
\texttt{PromotionCriteria} & Configurable criteria for promoting beliefs from provisional to verified. \\
\bottomrule
\end{tabular}
\end{table}

### Tripwire Module {#sec:tripwire-api}

The tripwire module implements canary belief monitoring for intrusion detection.

\begin{table}[htbp]
\centering
\caption{Tripwire module API: Classes for canary belief monitoring.}
\label{tab:tripwire-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{CognitiveTripwire} & Monitors canary beliefs for unauthorized modifications. Configurable alert severity levels. \\
\texttt{Canary} & Individual canary belief with expected value and tolerance. \\
\texttt{TripwireAlert} & Alert record with severity, timestamp, and drift magnitude. \\
\bottomrule
\end{tabular}
\end{table}

### Invariants Module {#sec:invariants-api}

The invariants module implements runtime behavioral constraint checking.

\begin{table}[htbp]
\centering
\caption{Invariants module API: Classes for behavioral invariant enforcement.}
\label{tab:invariants-api}
\begin{tabular}{@{}lp{8cm}@{}}
\toprule
Class & Description \\
\midrule
\texttt{InvariantChecker} & Evaluates agent actions against registered invariants. Returns violations with severity. \\
\texttt{RuntimeMonitor} & Continuous monitoring of agent behavior for invariant violations. Supports real-time alerting. \\
\texttt{Invariant} & Declarative invariant specification with predicate and severity. \\
\bottomrule
\end{tabular}
\end{table}

## Deployment Considerations {#sec:deployment-checklist}

### Pre-Deployment {#sec:pre-deploy}

\textbf{Framework installation}:
\begin{itemize}
\item Install Python 3.10+ with pip
\item Install core dependencies: numpy $\geq$ 1.24, scipy $\geq$ 1.10, scikit-learn $\geq$ 1.2
\item Optional: torch $\geq$ 2.0 for semantic embeddings
\item Test GPU availability if using embeddings
\end{itemize}

\textbf{Security preparation}:
\begin{itemize}
\item Generate signing key pairs for each agent
\item Configure TLS certificates for inter-agent communication
\item Set up secrets management (e.g., HashiCorp Vault)
\item Configure firewall rules for inter-agent communication
\end{itemize}

### Configuration {#sec:config-checklist}

\textbf{Core framework}:
\begin{itemize}
\item Set trust decay factor $\delta$ based on security requirements (\cref{tab:core-params})
\item Configure belief thresholds $\tau_{accept}$, $\tau_{trusted}$
\item Define corroboration count $\kappa$ based on agent pool size
\item Set trust weights $\alpha, \beta, \gamma$ (must sum to 1)
\end{itemize}

\textbf{Firewall configuration}:
\begin{itemize}
\item Load injection pattern database
\item Initialize semantic embedding model
\item Configure threshold values $\tau_1$, $\tau_2$ (\cref{tab:firewall-params})
\item Set score weights $w_1, w_2, w_3$
\end{itemize}

\textbf{Tripwire setup}:
\begin{itemize}
\item Define canary beliefs for each agent (canary belief definition (Part 1, Definition 7))
\item Set expected probability values
\item Configure drift thresholds (\cref{tab:tripwire-params})
\item Set monitoring intervals
\end{itemize}

\textbf{Consensus configuration}:
\begin{itemize}
\item Verify $n \geq 3f + 1$ for expected Byzantine count (Byzantine termination theorem (Part 1, Theorem 5))
\item Set round timeout based on network latency
\item Configure quorum thresholds (\cref{tab:consensus-params})
\end{itemize}

### Post-Deployment Verification {#sec:post-deploy}

\textbf{Functional testing}:
\begin{itemize}
\item Send test messages through firewall (expect ACCEPT)
\item Send known attack patterns (expect REJECT/QUARANTINE)
\item Verify tripwire alerts on artificial drift
\item Test consensus with simulated Byzantine agent
\end{itemize}

\textbf{Performance validation}:
\begin{itemize}
\item Measure baseline latency
\item Verify overhead within 23\% target (latency overhead theorem (Part 1, Theorem 6))
\item Confirm throughput meets requirements
\item Monitor memory usage over 24h
\end{itemize}

\textbf{Security verification}:
\begin{itemize}
\item Run attack corpus subset (sample 100 attacks)
\item Verify detection rate $\geq 90\%$
\item Confirm false positive rate $\leq 10\%$
\item Test escalation paths to human review
\end{itemize}

## Integration Examples {#sec:integration-examples}

### Python Integration {#sec:python-integration}

```python
from cif import CognitiveFirewall, BeliefSandbox, TrustManager

# Initialize components
firewall = CognitiveFirewall(
    tau_reject=0.8,
    tau_quarantine=0.5,
    pattern_db="patterns/injection.json"
)

sandbox = BeliefSandbox(
    ttl_default=3600,
    k_corroboration=2
)

trust_mgr = TrustManager(
    alpha=0.3, beta=0.5, gamma=0.2,
    delta=0.8
)

# Process incoming message
def process_message(msg, source):
    # Firewall check
    decision = firewall.classify(msg)
    if decision == "REJECT":
        return None

    # Get trust score
    trust = trust_mgr.get_trust(source)

    # Extract beliefs
    beliefs = extract_beliefs(msg)
    for belief in beliefs:
        if decision == "QUARANTINE" or trust < 0.9:
            sandbox.add(belief, source, trust)
        else:
            verified_beliefs.add(belief)

    return beliefs
```

### YAML Configuration {#sec:yaml-config}

```yaml
cif:
  version: "1.0"

  trust:
    alpha: 0.3
    beta: 0.5
    gamma: 0.2
    delta: 0.8
    learning_rate: 0.1

  firewall:
    enabled: true
    tau_reject: 0.8
    tau_quarantine: 0.5
    weights:
      injection: 0.4
      semantic: 0.35
      anomaly: 0.25

  sandbox:
    enabled: true
    ttl_default: 3600
    k_corroboration: 2
    max_provisional: 1000

  tripwires:
    enabled: true
    epsilon_drift: 0.1
    check_interval: 30
    canaries:
      - id: "identity"
        belief: "I am Agent-1"
        expected: 1.0
      - id: "principal"
        belief: "My principal is Alice"
        expected: 1.0

  consensus:
    enabled: true
    round_timeout: 5000
    max_rounds: 10

  monitoring:
    prometheus_port: 9090
    log_level: "INFO"
    alert_webhook: "https://alerts.example.com/cif"
```
