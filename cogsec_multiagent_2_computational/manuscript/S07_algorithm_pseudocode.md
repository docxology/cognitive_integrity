\newpage

# Supplement S7: Algorithm Pseudocode {#sec:pseudocode-supplement}

This supplement provides detailed pseudocode for all six core CIF defense algorithms referenced in Section 2.1 of the main text. Configuration parameters are documented separately in \cref{sec:config-params}. Framework API reference, deployment considerations, and integration examples are provided in Supplements S5, S6, and S9.

> **Cross-Reference Note**. All algorithms implement formal definitions from Part 1 \cite{friedman2026cogsec1} (DOI: 10.5281/zenodo.18364119). We cite specific theorems using "(Part 1, Theorem N)" notation to enable traceability from implementation to theoretical foundations. For deployment-facing pseudocode annotations and domain-calibrated instantiations across ten critical operational sectors, see unified Part 3+4 \cite{friedman2026cogsec3}, Sections 5--10.

> **Reproducibility**. Algorithm implementations are in [`src/core/`](../src/core/). Run `uv run pytest tests/` to verify behavior (see \cref{sec:framework-api} for the complete API surface and the suite's coverage target: 90%+ project code, no mocks). Every pseudocode block below has a corresponding Python implementation; the "Implementation" column of \cref{tab:alg-quickref} names the exact module.

## Algorithm Quick Reference {#sec:alg-quickref}

Table: CIF defense algorithm quick reference — formal basis, complexity, and implementation. {#tab:alg-quickref}

| Algorithm | Formal Basis | Per-Message Complexity | Space | Implementation |
| --- | --- | --- | --- | --- |
| 1. Cognitive Firewall | Part 1's Firewall Decision Rules definition | $O(\|m\| \cdot \|\mathcal{P}\| + d)$ | $O(d + \|\mathcal{P}\|)$ | `src/core/firewall.py` |
| 2. Belief Sandboxing | Part 1's Belief Sandbox definition, Prop. 5.2 | $O(1)$ add; $O(\|\mathcal{B}_{prov}\| \cdot \kappa)$ promote | $O(N_{max})$ | `src/core/sandbox.py` |
| 3. Trust Update | Part 1's Trust Boundedness theorem | $O(1)$ direct; $O(d)$ transitive | $O(n^2)$ matrix | `src/core/trust.py` |
| 4. Tripwire Monitoring | Part 1's Canary Belief definition | $O(\|\mathcal{W}\|)$ | $O(\|\mathcal{W}\|)$ | `src/core/tripwire.py` |
| 5. Byzantine Consensus | Part 1's Byzantine Agreement Requirement theorem | $O(n^2)$ messages/round | $O(n)$ per agent | `src/core/consensus.py` |
| 6. Drift Detection | Part 1's Drift Score definition | $O(\|\text{domain}(\mathcal{B})\|)$ | $O(w \cdot \|\text{domain}\|)$ | `src/core/detection.py` |

Where: $d$ = embedding dimension, $\|\mathcal{P}\|$ = pattern count, $\kappa$ = corroboration threshold, $n$ = agent count, $w$ = sliding window size, $N_{max}$ = sandbox capacity limit.

## Algorithm 1: Cognitive Firewall Classification {#sec:alg-firewall}

The cognitive firewall classifies incoming messages using a multi-stage detection pipeline. This implements Part 1's Cognitive Firewall definition. The three-stage filtering it uses ($F_{sig} \to F_{sem} \to F_{anom}$) is this paper's refinement: Part 1 specifies two detectors, $D_{\text{inj}}$ and $D_{\text{sus}}$, and fixes only their combination (Part 1's Firewall Decision Rules definition).

\begin{algorithm}
\caption{Cognitive Firewall Classification}
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
\label{alg:firewall-impl}

> **Implementation**: `src/core/firewall.py` — `CognitiveFirewall.classify()`, `PatternDetector.score_injection()`, `SemanticSimilarityDetector.score_semantic_similarity()`.

> **Implementation Notes**: `Embed(m)` uses a 384-dimensional sentence embedding (all-MiniLM-L6-v2 via `sentence-transformers`; falls back to TF-IDF bag-of-words if the model is unavailable). `c_attack` is the centroid of known attack sample embeddings computed once at firewall initialization from the training corpus; it is updated via online mean when new confirmed attacks are added. `Features(m, ctx)` extracts 12 structural features: token count, punctuation density, imperative verb frequency, role-claim indicator count, context-window position (normalized 0–1), source trust score (from Trust Calculus), and 6 n-gram pattern hit counts for known injection patterns. See `src/core/firewall.py → FeatureExtractor.extract()` for the complete feature specification.

> **Complexity**: $O(|m| \cdot |\mathcal{P}| + d)$ for pattern matching and embedding lookup, where $d$ is the embedding dimension and $|\mathcal{P}|$ is the pattern count. Space: $O(d + |\mathcal{P}|)$ for the attack centroid and pattern set.

## Algorithm 2: Belief Sandboxing {#sec:alg-sandbox}

Manages provisional beliefs with verification and promotion logic. This implements Part 1's sandboxing rules, including the promotion rule requiring $\kappa$-corroboration (Part 1's Belief Sandbox definition for the partition, and its Sandbox Promotion Soundness theorem for the criterion).

\begin{algorithm}
\caption{Belief Sandbox Operations}
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
      \State **continue**
    \EndIf
    \If{$\neg V(\pi)$}
      \State **continue**
    \EndIf
    \If{$\neg \text{Consistent}(\mathcal{B}_{verified}, \phi)$}
      \State **continue**
    \EndIf
    \If{$|\text{Corroborate}(\phi)| \geq \kappa$}
      \State $\mathcal{B}_{verified} \gets \mathcal{B}_{verified} \cup \{\phi\}$
      \State $\mathcal{B}_{provisional} \gets \mathcal{B}_{provisional} \setminus \{(\phi, \pi, ttl)\}$
    \EndIf
  \EndFor
\EndFunction
\end{algorithmic}
\end{algorithm}
\label{alg:sandbox-impl}

> **Implementation**: `src/core/sandbox.py` — `SandboxManager.add_provisional()`, `SandboxManager.promote()`, `PromotionCriteria.evaluate()`.

> **Implementation Note**: $V(\pi)$ denotes **provenance verification** — a cryptographic check confirming that the belief's recorded source $\pi.\mathit{source}$ is consistent with the message signature chain maintained by the Provenance Attestation module. Specifically, $V(\pi) = \text{True}$ iff (a) the source agent's signature on the message is valid, (b) the delegation chain from the source to the current agent is unbroken, and (c) the SHA-256 hash in $\pi.\mathit{hash}$ matches the belief content. Implemented in `src/core/provenance.py → ProvenanceTracker.verify()`. A belief whose provenance cannot be verified is evicted from $\mathcal{B}_{\text{provisional}}$ regardless of corroboration count.

> **Complexity**: $O(1)$ for `add_provisional`, $O(|\mathcal{B}_{prov}| \cdot \kappa)$ for promotion check. Memory: $O(N_{max})$ bounded by configuration.

## Algorithm 3: Trust Update with Bounded Delegation {#sec:alg-trust}

Implements the trust calculus with decay and reputation updates. This is a direct implementation of Part 1's Trust Algebra, including bounded delegation with $\delta^d$ decay (its Trust Boundedness theorem). Trust cannot be inflated through delegation chains.

\begin{algorithm}
\caption{Trust Update Operations}
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
\label{alg:trust-impl}

> **Implementation**: `src/core/trust.py` — `TrustCalculus.compute_trust()`, `TrustCalculus.delegate_trust()`, `TrustMatrix.get_delegation_trust()`, `ReputationTracker.get_reputation()`.

> **Complexity**: $O(1)$ for direct trust lookup, $O(d)$ for transitive trust through depth-$d$ delegation chain. Trust matrix storage: $O(n^2)$ for $n$ agents — at 100 agents this is 10,000 float32 values ($\approx$40KB), which is negligible. At 1,000 agents the dense matrix reaches 4MB; sparse representations (storing only non-zero trust relationships) reduce this to $O(kn)$ for mean out-degree $k$. The Reputation tracker adds $O(n)$ storage per agent for interaction history.

## Algorithm 4: Cognitive Tripwire Monitoring {#sec:alg-tripwire}

Continuously monitors canary beliefs for unauthorized modifications. Tripwires implement Part 1's Runtime Defenses section on cognitive tripwires (Definition 5.6: Canary Belief), specifying canary beliefs $\omega \in \mathcal{W}$ that remain stable under normal operation.

\begin{algorithm}
\caption{Tripwire Monitoring}
\begin{algorithmic}[1]
\Require agent state $\sigma$, tripwire set $\mathcal{W}$
\Ensure alert status
\Function{MonitorTripwires}{$\sigma$, $\mathcal{W}$}
  \State $alerts \gets []$
  \For{each $(\omega, p_{expected}) \in \mathcal{W}$}
    \State $p_{actual} \gets \sigma.\mathcal{B}[\omega]$
    \State $drift \gets |p_{actual} - p_{expected}|$
    \If{$drift > \epsilon_{drift}$}
      \State $severity \gets \text{ClassifySeverity}(drift)$
      \State $alert \gets \{tripwire: \omega, expected: p_{expected}, actual: p_{actual},$
      \State \quad\quad\quad\quad $drift: drift, timestamp: \text{Now}(), severity: severity\}$
      \State $alerts.\text{append}(alert)$
    \EndIf
  \EndFor
  \If{$|alerts| > 0$}
    \State $\text{AggregateAlerts}(alerts)$
    \State $\text{TriggerResponse}(alerts)$
  \EndIf
  \Return $alerts$
\EndFunction
\Function{ClassifySeverity}{$drift$}
  \State \Comment{Uniform 4-tier severity based on drift magnitude}
  \If{$drift > \epsilon_{critical}$}
    \Return CRITICAL
  \ElsIf{$drift > \epsilon_{high}$}
    \Return HIGH
  \ElsIf{$drift > \epsilon_{medium}$}
    \Return MEDIUM
  \Else
    \Return LOW
  \EndIf
\EndFunction
\end{algorithmic}
\end{algorithm}
\label{alg:tripwire-impl}

> **Implementation**: `src/core/tripwire.py` — `CognitiveTripwire.check()`, `CognitiveTripwire.check_single()`, `TripwireAlert.severity`.

> **Note**: Severity classification uses a uniform 4-tier system (LOW, MEDIUM, HIGH, CRITICAL) based solely on drift magnitude, independent of canary category. This aligns with the `Severity` IntEnum in `src/utils/types.py`.

## Algorithm 5: Byzantine Consensus Protocol {#sec:alg-byzantine}

Implements Byzantine fault-tolerant consensus for multi-agent decisions. This satisfies Part 1's Byzantine Agreement Requirement theorem, ensuring agreement when at most $f$ agents are Byzantine and $n \geq 3f + 1$.

\begin{algorithm}
\caption{Byzantine Consensus Protocol}
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
\label{alg:byzantine-impl}

> **Implementation**: `src/core/consensus.py` — `ByzantineConsensus.compute_consensus()`, `WeightedByzantineConsensus.submit_vote()`, `QuorumVerification.approve()`.

> **Complexity**: $O(n^2)$ messages per consensus round — each of $n$ agents broadcasts to all others in Phase 1 (vote collection) and Phase 2 (echo round), yielding $2n(n-1)$ total messages per round. Time complexity per round: $O(n^2 \cdot T_{sign} + n \cdot T_{verify})$ where $T_{sign}$ and $T_{verify}$ are signature generation and verification costs. Space per agent: $O(n)$ for vote and echo storage. The quadratic message complexity limits practical Byzantine consensus to $n \lesssim 50$ agents; hierarchical committee partitioning (partitioning agents into subcommittees of size $\leq 20$ with inter-committee agreement) is recommended above this threshold — see §\ref{sec:agent-scaling} for measured latency at 100 agents (4.2s consensus time).

## Algorithm 6: Belief Drift Detection {#sec:alg-drift}

Monitors belief distributions for anomalous changes over time using KL divergence. This implements Part 1's progressive drift detection (Section 6.1, Definition 6.1).

\begin{algorithm}
\caption{Belief Drift Detection}
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
\label{alg:drift-impl}

> **Implementation**: `src/core/detection.py` — `DriftDetector.compute_drift()`, `DriftDetector.is_anomalous()`, `AnomalyScorer.score()`.
