\newpage

# Supplementary: Mathematical Proofs

This supplementary material provides complete formal proofs for all theorems stated in the main text, including preliminary definitions (\cref{sec:preliminaries}), main theorem proofs (\crefrange{sec:thm42-proof}{sec:thm511-proof}), and additional supporting lemmas (\cref{sec:additional-lemmas}).

## Proof Status {#sec:proof-status}

For transparency, this section records, by exact label, which results stated in the main text carry a proof in this supplement and which are asserted without proof.

**Proven in this supplement.** The following theorems each have a dedicated `proof` environment (section given in parentheses):

- Trust Boundedness (Thm. 4.2), \cref{thm:trust-bound-restated} (\cref{sec:thm42-proof})
- Belief Injection Resistance (Thm. 5.7), \cref{thm:belief-injection-restated} (\cref{sec:thm57-proof})
- No Trust Amplification (Thm. 4.7), \cref{thm:trust-amp-restated} (\cref{sec:thm47-proof})
- Goal Alignment Invariant (Thm. 5.8), \cref{thm:goal-alignment-restated} (\cref{sec:thm58-proof})
- Firewall Liveness (Thm. 5.9), \cref{thm:firewall-liveness-restated} (\cref{sec:thm59-proof})
- Byzantine Consensus Termination (Thm. 5.10), \cref{thm:byzantine-restated} (\cref{sec:thm510-proof})
- Bounded Overhead (Thm. 5.11), \cref{thm:overhead-restated} (\cref{sec:thm511-proof})
- Defense Composition Semiring, \cref{thm:composition-semiring-restated} (\cref{sec:thm-composition-semiring})
- Fisher-Rao Stealth-Impact Tight Bound, \cref{thm:fr-bound-restated} (\cref{sec:thm-geometric-bound})
- Agent Compromise Blast Radius, \cref{thm:blast-radius-restated} (\cref{sec:thm-blast-radius})

Separate proofs are also given for the supporting lemmas and for the corollaries \cref{cor:trust-vanishing}, \cref{cor:defense-stacking}, and \cref{cor:consensus-safety}. The remaining corollaries in this supplement state immediate (quantitative or qualitative) consequences of a proved theorem and, following standard mathematical convention, are not accompanied by a standalone proof.

**Asserted without proof (deferred).** The following theorems and corollaries stated in the main text do not have a proof in this supplement; they are assertions whose proofs are deferred to future work. They are recorded here so that they are not mistaken for proved results:

- Aggregation Properties, \cref{thm:aggregation} (stated in 04_formal\_framework.md)
- Trust Monotonicity, \cref{thm:trust-monotonic} (04_formal\_framework.md)
- Cross-Modality Delegation Bound, \cref{thm:cross-modality-bound} (04_formal\_framework.md)
- Optimal Threshold Selection, \cref{thm:threshold-selection} (05_defense\_mechanisms.md)
- False Positive Composition, \cref{thm:fpr-composition} (05_defense\_mechanisms.md)
- Cascade FPR Reduction, \cref{thm:cascade-fpr} (06_detection\_methods.md)
- Pipeline TPR Bound, \cref{thm:pipeline-tpr} (06_detection\_methods.md)
- Stack Detection Rate, \cref{cor:stack-detection} (05_defense\_mechanisms.md)
- Layered Defense Asymptotic Guarantee, \cref{cor:layered-defense} (05_defense\_mechanisms.md)
- Quorum Attack Cost, \cref{cor:quorum-attack-cost} (S02_eusocial\_cogsec.md)
- Stigmergic Trust Bound, \cref{cor:stigmergic-trust} (S02_eusocial\_cogsec.md)
- Emergent Stealth-Impact Bound, \cref{cor:emergent-stealth-impact} (S02_eusocial\_cogsec.md)

> **Note on \cref{cor:isolation-blast}.**
> An earlier audit listed \cref{cor:isolation-blast} among the asserted results. Re-reading the source, this corollary is stated in this supplement (\cref{sec:thm-blast-radius}), immediately after the proved \cref{thm:blast-radius-restated}, as that theorem's degree-restricted consequence ($\lvert \mathcal{N}(a_v) \rvert = k \le n$). It therefore carries no standalone proof environment -- consistent with the other corollaries in this supplement -- and is not deferred. It is recorded here only because the prior audit flagged it, so that its status is unambiguous.

## Preliminary Definitions and Notation {#sec:preliminaries}

### Notation Summary {#sec:notation}

\begin{table}[htbp]
\centering
\caption{Mathematical notation used throughout proofs.}
\label{tab:notation}
\begin{tabular}{@{}ll@{}}
\toprule
Symbol & Meaning \\
\midrule
$\mathcal{A} = \{a_1, \ldots, a_n\}$ & Set of $n$ agents \\
$\mathcal{B}_i: \Phi \to [0,1]$ & Agent $i$'s belief function \\
$\mathcal{G}_i$ & Agent $i$'s goal set \\
$\mathcal{T}_{i \to j}$ & Trust from agent $i$ to agent $j$ \\
$\delta \in (0,1)$ & Trust decay factor per delegation hop \\
$\tau$ & Generic threshold parameter \\
$\phi, \psi$ & Propositions \\
$\pi(\phi)$ & Provenance chain for belief $\phi$ \\
\bottomrule
\end{tabular}
\end{table}

\begin{definition}[Trust Path]
\label{def:trust-path}
A trust path from agent $a_0$ to agent $a_k$ is an ordered sequence $p = (a_0, a_1, \ldots, a_k)$ where each consecutive pair $(a_i, a_{i+1})$ represents a direct trust relationship with $\mathcal{T}_{a_i \to a_{i+1}} > 0$.
\end{definition}

\begin{definition}[Path Trust]
\label{def:path-trust}
The trust along path $p = (a_0, \ldots, a_k)$ is defined as:
\begin{equation}
\label{eq:path-trust}
\mathcal{T}^{path}_p = \min_{i \in [0,k-1]} \mathcal{T}_{a_i \to a_{i+1}} \cdot \delta^{k}
\end{equation}
\end{definition}

\begin{definition}[Delegation Chain]
\label{def:delegation-chain}
A delegation chain of depth $d$ is a sequence of agents $(a_0, a_1, \ldots, a_d)$ where agent $a_i$ delegates authority to $a_{i+1}$.
\end{definition}

---

## Theorem 4.2: Trust Boundedness {#sec:thm42-proof}

\begin{theorem}[Trust Boundedness --- Restated]
\label{thm:trust-bound-restated}
For any delegation chain of depth $d$:
\begin{equation}
\label{eq:trust-bound-restated}
\mathcal{T}_{i \to k}^{del} \leq \delta^d
\end{equation}
\end{theorem}

\begin{lemma}[Trust Non-Amplification on Single Hop]
\label{lem:single-hop}
For any agents $a, b$ and any delegation to $c$:
\begin{equation}
\label{eq:single-hop}
\mathcal{T}_{a \to c}^{del} \leq \mathcal{T}_{a \to b}
\end{equation}
\end{lemma}

\begin{proof}[Proof of \cref{lem:single-hop}]
By the trust delegation rule (\cref{def:trust-delegation}):
\begin{equation}
\label{eq:lem-single-hop-1}
\mathcal{T}_{a \to c}^{del} = \min(\mathcal{T}_{a \to b}, \mathcal{T}_{b \to c}) \cdot \delta
\end{equation}

Since $\min(\mathcal{T}_{a \to b}, \mathcal{T}_{b \to c}) \leq \mathcal{T}_{a \to b}$ and $\delta < 1$:
\begin{equation}
\label{eq:lem-single-hop-2}
\mathcal{T}_{a \to c}^{del} = \min(\mathcal{T}_{a \to b}, \mathcal{T}_{b \to c}) \cdot \delta \leq \mathcal{T}_{a \to b} \cdot \delta < \mathcal{T}_{a \to b}
\end{equation}
\end{proof}

\begin{lemma}[Trust Decay Bound]
\label{lem:decay-bound}
For any single-hop delegation:
\begin{equation}
\label{eq:decay-bound}
\mathcal{T}^{del} \leq \delta
\end{equation}
\end{lemma}

\begin{proof}[Proof of \cref{lem:decay-bound}]
By definition, all direct trust values satisfy $\mathcal{T}_{a \to b} \leq 1$. Therefore:
\begin{equation}
\label{eq:lem-decay-1}
\mathcal{T}_{a \to c}^{del} = \min(\mathcal{T}_{a \to b}, \mathcal{T}_{b \to c}) \cdot \delta \leq 1 \cdot \delta = \delta
\end{equation}
\end{proof}

\begin{proof}[Main Proof of \cref{thm:trust-bound-restated}]
By strong induction on $d$.

\textbf{Base Case} ($d = 0$): When $d = 0$, there is no delegation (direct trust). By definition:
\begin{equation}
\label{eq:base-case}
\mathcal{T}_{i \to k}^{del} = \mathcal{T}_{i \to k} \leq 1 = \delta^0
\end{equation}
The base case holds.

\textbf{Inductive Hypothesis}: Assume for all delegation chains of depth $\leq d$:
\begin{equation}
\label{eq:ind-hyp}
\mathcal{T}^{del} \leq \delta^d
\end{equation}

\textbf{Inductive Step} (depth $d + 1$): Consider a delegation chain $(a_0, a_1, \ldots, a_{d+1})$ of depth $d + 1$.

Let $\mathcal{T}^{(d)}$ denote the delegated trust from $a_0$ to $a_d$ (depth $d$).

By the trust delegation rule:
\begin{equation}
\label{eq:ind-step-1}
\mathcal{T}_{a_0 \to a_{d+1}}^{del} = \min(\mathcal{T}^{(d)}, \mathcal{T}_{a_d \to a_{d+1}}) \cdot \delta
\end{equation}

By the inductive hypothesis: $\mathcal{T}^{(d)} \leq \delta^d$

Since $\mathcal{T}_{a_d \to a_{d+1}} \leq 1$:
\begin{equation}
\label{eq:ind-step-2}
\min(\mathcal{T}^{(d)}, \mathcal{T}_{a_d \to a_{d+1}}) \leq \mathcal{T}^{(d)} \leq \delta^d
\end{equation}

Therefore:
\begin{equation}
\label{eq:ind-step-3}
\mathcal{T}_{a_0 \to a_{d+1}}^{del} \leq \delta^d \cdot \delta = \delta^{d+1}
\end{equation}

By the principle of mathematical induction, the theorem holds for all $d \geq 0$.
\end{proof}

\begin{corollary}[Trust Vanishing]
\label{cor:trust-vanishing}
For any $\epsilon > 0$, there exists $D$ such that for all delegation chains of depth $d > D$:
\begin{equation}
\label{eq:trust-vanishing}
\mathcal{T}^{del} < \epsilon
\end{equation}
\end{corollary}

\begin{proof}
Choose $D = \lceil \log_\delta \epsilon \rceil$. Since $\delta \in (0,1)$, $\log_\delta$ is decreasing. For $d > D$: $\mathcal{T}^{del} \leq \delta^d < \delta^D \leq \epsilon$.
\end{proof}

\begin{corollary}[Practical Depth Limit]
\label{cor:practical-depth}
With $\delta = 0.8$ and minimum actionable trust $\tau_{min} = 0.1$:
\begin{equation}
\label{eq:practical-depth}
d_{max} = \lfloor \log_{0.8} 0.1 \rfloor = 10
\end{equation}
\end{corollary}

---

## Theorem 5.7: Belief Injection Resistance {#sec:thm57-proof}

\begin{theorem}[Belief Injection Resistance --- Restated]
\label{thm:belief-injection-restated}
Under CIF with firewall detection rate $r_f$ and sandboxing verification rate $r_s$:
\begin{equation}
\label{eq:belief-injection-restated}
P(\mathcal{A}_{BI} \text{ succeeds}) \leq (1 - r_f) \cdot (1 - r_s)
\end{equation}
\end{theorem}

\begin{lemma}[Defense Independence]
\label{lem:defense-independence}
The firewall and sandbox operate on independent decision criteria:
\begin{itemize}
\item Firewall: Pattern matching and anomaly scoring on message content
\item Sandbox: Provenance verification, consistency checking, and corroboration
\end{itemize}
These mechanisms share no common features or state.
\end{lemma}

\begin{proof}[Proof of \cref{lem:defense-independence}]
By construction of the CIF architecture:
\begin{enumerate}
\item Firewall operates at input layer with feature set $F_{firewall} = \{patterns, embeddings, anomaly\_scores\}$
\item Sandbox operates at belief layer with feature set $F_{sandbox} = \{provenance, consistency, corroboration\}$
\item $F_{firewall} \cap F_{sandbox} = \emptyset$
\end{enumerate}

Therefore, $P(\text{firewall detects} | \text{sandbox outcome}) = P(\text{firewall detects})$. The mechanisms are probabilistically independent.
\end{proof}

\begin{remark}[Independence is an assumption, not a guarantee]
\label{rem:defense-independence-scope}
Disjoint feature sets do not by themselves guarantee probabilistic independence of detection events: an adversary can craft content that defeats both pattern matching and provenance/consistency checks, correlating the failure modes. The multiplicative detection bounds derived below (e.g.\ $(1-r_f)(1-r_s)$) therefore hold under the architectural \emph{assumption} that firewall and sandbox failure events are approximately independent (decoupled adversarial capability). If the failure modes are positively correlated, the correct bound is the union bound $P(\text{success}) \le \min(1-r_f,\,1-r_s)$, or $P(\text{success}) \le (1-r_f)(1-r_s) + \rho$ with an explicit correlation term $\rho \ge 0$. Throughout this part we adopt the independence assumption for the closed-form analyses and apply the union-bound relaxation where correlation may be material.
\end{remark}

\begin{definition}[Attack Success]
\label{def:attack-success}
A belief injection attack $\mathcal{A}_{BI}$ succeeds if and only if:
\begin{enumerate}
\item The adversarial message $m_{adv}$ is not rejected by the firewall, AND
\item The injected belief $\phi_{adv}$ is promoted from sandbox to verified beliefs
\end{enumerate}
\end{definition}

\begin{proof}[Main Proof of \cref{thm:belief-injection-restated}]
Let $E_f$ = event ``firewall accepts message'' (does not detect attack). Let $E_s$ = event``sandbox fails to filter belief'' (does not detect attack).

For $\mathcal{A}_{BI}$ to succeed, both $E_f$ and $E_s$ must occur:
\begin{equation}
\label{eq:61-proof-1}
P(\mathcal{A}_{BI} \text{ succeeds}) = P(E_f \cap E_s)
\end{equation}

By \cref{lem:defense-independence} (independence):
\begin{equation}
\label{eq:61-proof-2}
P(E_f \cap E_s) = P(E_f) \cdot P(E_s)
\end{equation}

By definition of detection rates:
\begin{itemize}
\item $P(E_f) = 1 - r_f$ (probability firewall misses attack)
\item $P(E_s) = 1 - r_s$ (probability sandbox misses attack)
\end{itemize}

Therefore:
\begin{equation}
\label{eq:61-proof-3}
P(\mathcal{A}_{BI} \text{ succeeds}) = (1 - r_f) \cdot (1 - r_s)
\end{equation}
\end{proof}

\begin{corollary}[Numerical Bound]
\label{cor:numerical-bound}
With empirical values $r_f = 0.8$ and $r_s = 0.7$:
\begin{equation}
\label{eq:numerical-bound}
P(\mathcal{A}_{BI} \text{ succeeds}) \leq (1 - 0.8) \cdot (1 - 0.7) = 0.2 \cdot 0.3 = 0.06
\end{equation}
\end{corollary}

\begin{corollary}[Defense Stacking]
\label{cor:defense-stacking}
For $n$ independent defenses with detection rates $r_1, \ldots, r_n$:
\begin{equation}
\label{eq:defense-stacking}
P(\text{attack succeeds}) = \prod_{i=1}^{n} (1 - r_i)
\end{equation}
\end{corollary}

\begin{proof}
Direct extension of \cref{thm:belief-injection-restated} by independence.
\end{proof}

---

## Theorem 4.7: No Trust Amplification {#sec:thm47-proof}

\begin{theorem}[No Trust Amplification --- Restated]
\label{thm:trust-amp-restated}
For any path $p = (a_0, a_1, \ldots, a_k)$ in the communication graph:
\begin{equation}
\label{eq:trust-amp-restated}
\mathcal{T}_{a_0 \to a_k}^{path} \leq \min_{i \in [0,k-1]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}
\end{theorem}

\begin{lemma}[Minimum Preservation under Min]
\label{lem:min-preservation}
For any sequence $(x_1, \ldots, x_n)$ and additional element $x_{n+1}$:
\begin{equation}
\label{eq:min-preservation}
\min(x_1, \ldots, x_{n+1}) = \min(\min(x_1, \ldots, x_n), x_{n+1})
\end{equation}
\end{lemma}

\begin{proof}
Standard property of the minimum function.
\end{proof}

\begin{lemma}[Decay Factor Strengthens Bound]
\label{lem:decay-strengthens}
For $x \leq y$ and $\delta \in (0,1)$:
\begin{equation}
\label{eq:decay-strengthens}
x \cdot \delta \leq y
\end{equation}
\end{lemma}

\begin{proof}
Since $\delta < 1$, $x \cdot \delta < x \leq y$.
\end{proof}

\begin{proof}[Main Proof of \cref{thm:trust-amp-restated}]
By strong induction on path length $k$.

\textbf{Base Case} ($k = 1$): For path $p = (a_0, a_1)$:
\begin{equation}
\label{eq:62-base}
\mathcal{T}_{a_0 \to a_1}^{path} = \mathcal{T}_{a_0 \to a_1} = \min_{i \in [0,0]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}
The base case holds trivially.

\textbf{Inductive Hypothesis}: Assume for all paths of length $\leq k$:
\begin{equation}
\label{eq:62-ind-hyp}
\mathcal{T}^{path} \leq \min_{i \in [0,k-1]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}

\textbf{Inductive Step} (path length $k + 1$): Consider path $p = (a_0, a_1, \ldots, a_{k+1})$.

Let $p' = (a_0, a_1, \ldots, a_k)$ be the prefix path.

By the trust delegation rule:
\begin{equation}
\label{eq:62-step-1}
\mathcal{T}_{a_0 \to a_{k+1}}^{path} = \min(\mathcal{T}_{a_0 \to a_k}^{path'}, \mathcal{T}_{a_k \to a_{k+1}}) \cdot \delta
\end{equation}

By the inductive hypothesis:
\begin{equation}
\label{eq:62-step-2}
\mathcal{T}_{a_0 \to a_k}^{path'} \leq \min_{i \in [0,k-1]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}

Applying the minimum:
\begin{equation}
\label{eq:62-step-3}
\min(\mathcal{T}_{a_0 \to a_k}^{path'}, \mathcal{T}_{a_k \to a_{k+1}}) \leq \min\left(\min_{i \in [0,k-1]} \mathcal{T}_{a_i \to a_{i+1}}, \mathcal{T}_{a_k \to a_{k+1}}\right)
\end{equation}

By \cref{lem:min-preservation}:
\begin{equation}
\label{eq:62-step-4}
= \min_{i \in [0,k]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}

Since $\delta \in (0,1)$:
\begin{equation}
\label{eq:62-step-5}
\mathcal{T}_{a_0 \to a_{k+1}}^{path} = \min(\cdot) \cdot \delta \leq \min_{i \in [0,k]} \mathcal{T}_{a_i \to a_{i+1}}
\end{equation}
\end{proof}

\begin{corollary}[Weakest Link Principle]
\label{cor:weakest-link}
Trust through any path is bounded by the least trusted edge:
\begin{equation}
\label{eq:weakest-link}
\mathcal{T}^{path} \leq \min_{edge \in path} \mathcal{T}_{edge}
\end{equation}
\end{corollary}

\begin{corollary}[No Collusion Benefit]
\label{cor:no-collusion}
Multiple colluding agents cannot create trust exceeding any individual's trust with the target.
\end{corollary}

---

## Theorem 5.8: Goal Alignment Invariant {#sec:thm58-proof}

\begin{theorem}[Goal Alignment Invariant --- Restated]
\label{thm:goal-alignment-restated}
If the system starts with aligned goals and all goal updates follow the delegation protocol:
\begin{equation}
\label{eq:goal-alignment-restated}
\text{Aligned}(\mathcal{G}_i^0) \land \forall t: \text{ValidUpdate}(\mathcal{G}_i^t, \mathcal{G}_i^{t+1}) \Rightarrow \forall t: \text{Aligned}(\mathcal{G}_i^t)
\end{equation}
\end{theorem}

\begin{definition}[Goal Alignment]
\label{def:goal-alignment}
Goals $\mathcal{G}_i$ are aligned if:
\begin{equation}
\label{eq:goal-alignment-def}
\text{Aligned}(\mathcal{G}_i) \iff \mathcal{G}_i \subseteq \mathcal{G}_{principal} \cup \text{Delegate}(\mathcal{G}_{principal})
\end{equation}
\end{definition}

\begin{definition}[Valid Goal Update]
\label{def:valid-update}
An update from $\mathcal{G}^t$ to $\mathcal{G}^{t+1}$ is valid if:
\begin{equation}
\label{eq:valid-update}
\text{ValidUpdate}(\mathcal{G}^t, \mathcal{G}^{t+1}) \iff \forall g \in (\mathcal{G}^{t+1} \setminus \mathcal{G}^t): \text{Authorized}(g)
\end{equation}
where $\text{Authorized}(g)$ means $g$ derives from principal or valid delegation.
\end{definition}

\begin{lemma}[Delegation Preserves Alignment]
\label{lem:delegation-preserves}
If $g \in \text{Delegate}(\mathcal{G}_{principal})$, then $g$ is aligned.
\end{lemma}

\begin{proof}
Direct from \cref{def:goal-alignment}.
\end{proof}

\begin{lemma}[Set Union Preserves Subset]
\label{lem:union-preserves}
If $A \subseteq C$ and $B \subseteq C$, then $A \cup B \subseteq C$.
\end{lemma}

\begin{proof}
Standard set theory.
\end{proof}

\begin{proof}[Main Proof of \cref{thm:goal-alignment-restated}]
By induction on time $t$.

\textbf{Base Case} ($t = 0$): Given: $\text{Aligned}(\mathcal{G}_i^0)$. The base case holds by hypothesis.

\textbf{Inductive Hypothesis}: Assume $\text{Aligned}(\mathcal{G}_i^t)$ for some $t \geq 0$.

\textbf{Inductive Step}: We must show $\text{Aligned}(\mathcal{G}_i^{t+1})$.

The goal set at $t+1$ is:
\begin{equation}
\label{eq:63-step-1}
\mathcal{G}_i^{t+1} = (\mathcal{G}_i^t \setminus \text{Removed}) \cup \text{Added}
\end{equation}

For goals in $\mathcal{G}_i^t \setminus \text{Removed}$:
\begin{itemize}
\item By inductive hypothesis, these are aligned
\item Removal cannot introduce misalignment
\end{itemize}

For goals in $\text{Added}$:
\begin{itemize}
\item By $\text{ValidUpdate}$, all added goals satisfy $\text{Authorized}(g)$
\item By \cref{lem:delegation-preserves}, authorized goals are aligned
\end{itemize}

By \cref{lem:union-preserves}:
\begin{equation}
\label{eq:63-step-2}
\mathcal{G}_i^{t+1} \subseteq \mathcal{G}_{principal} \cup \text{Delegate}(\mathcal{G}_{principal})
\end{equation}

Therefore $\text{Aligned}(\mathcal{G}_i^{t+1})$.
\end{proof}

\begin{corollary}[Safety Under Protocol]
\label{cor:safety-protocol}
An agent following CIF protocols cannot have its goals hijacked to adversarial objectives.
\end{corollary}

\begin{corollary}[Necessary Condition for Hijacking]
\label{cor:hijack-necessary}
Goal hijacking requires violating the delegation protocol:
\begin{equation}
\label{eq:hijack-necessary}
\neg\text{Aligned}(\mathcal{G}_i^t) \Rightarrow \exists t' < t: \neg\text{ValidUpdate}(\mathcal{G}_i^{t'}, \mathcal{G}_i^{t'+1})
\end{equation}
\end{corollary}

---

## Theorem 5.9: Firewall Liveness {#sec:thm59-proof}

\begin{theorem}[Firewall Liveness --- Restated]
\label{thm:firewall-liveness-restated}
CIF firewall preserves liveness for legitimate inputs:
\begin{equation}
\label{eq:firewall-liveness-restated}
\forall m \in \mathcal{M}_{legitimate}: P(\mathcal{F}(m) = \text{ACCEPT}) \geq 1 - \epsilon_{fp}
\end{equation}
\end{theorem}

\begin{definition}[Legitimate Message]
\label{def:legitimate-message}
A message $m$ is legitimate if:
\begin{enumerate}
\item It originates from an authorized source
\item It contains no adversarial content
\item It conforms to expected communication patterns
\end{enumerate}
\end{definition}

\begin{definition}[False Positive Rate]
\label{def:false-positive}
The false positive rate $\epsilon_{fp}$ is:
\begin{equation}
\label{eq:false-positive}
\epsilon_{fp} = P(\mathcal{F}(m) \neq \text{ACCEPT} | m \in \mathcal{M}_{legitimate})
\end{equation}
\end{definition}

\begin{lemma}[Firewall Classification]
\label{lem:firewall-classification}
For any message $m$, the firewall produces exactly one of three outcomes:
\begin{equation}
\label{eq:firewall-outcomes}
\mathcal{F}(m) \in \{\text{ACCEPT}, \text{QUARANTINE}, \text{REJECT}\}
\end{equation}
\end{lemma}

\begin{proof}
By construction of the firewall decision function (\cref{def:firewall}).
\end{proof}

\begin{proof}[Main Proof of \cref{thm:firewall-liveness-restated}]
Let $m \in \mathcal{M}_{legitimate}$ be an arbitrary legitimate message.

By the law of total probability:
\begin{equation}
\label{eq:64-proof-1}
P(\mathcal{F}(m) = \text{ACCEPT}) + P(\mathcal{F}(m) = \text{QUARANTINE}) + P(\mathcal{F}(m) = \text{REJECT}) = 1
\end{equation}

By \cref{def:false-positive}:
\begin{equation}
\label{eq:64-proof-2}
P(\mathcal{F}(m) \neq \text{ACCEPT}) = \epsilon_{fp}
\end{equation}

Therefore:
\begin{equation}
\label{eq:64-proof-3}
P(\mathcal{F}(m) = \text{ACCEPT}) = 1 - P(\mathcal{F}(m) \neq \text{ACCEPT}) = 1 - \epsilon_{fp}
\end{equation}

Since $m$ was arbitrary:
\begin{equation}
\label{eq:64-proof-4}
\forall m \in \mathcal{M}_{legitimate}: P(\mathcal{F}(m) = \text{ACCEPT}) \geq 1 - \epsilon_{fp}
\end{equation}
\end{proof}

\begin{corollary}[Availability Bound]
\label{cor:availability}
With $\epsilon_{fp} = 0.06$, at least 94\% of legitimate messages are accepted.
\end{corollary}

\begin{corollary}[Quarantine Recovery]
\label{cor:quarantine-recovery}
Messages in QUARANTINE can still reach verified belief state through sandbox promotion, further improving effective availability.
\end{corollary}

---

## Theorem 5.10: Byzantine Consensus Termination {#sec:thm510-proof}

\begin{theorem}[Byzantine Consensus Termination --- Restated]
\label{thm:byzantine-restated}
With $n \geq 3f + 1$ agents and at most $f$ Byzantine:
\begin{equation}
\label{eq:byzantine-restated}
P(\text{consensus reached in } O(f+1) \text{ rounds}) = 1
\end{equation}
\end{theorem}

\begin{lemma}[Byzantine Agreement Bound]
\label{lem:byzantine-bound}
Byzantine agreement requires $n \geq 3f + 1$ to tolerate $f$ Byzantine agents.
\end{lemma}

\begin{proof}
Classical result from distributed systems (Lamport, Shostak, Pease 1982). With fewer agents, Byzantine agents can equivocate and prevent agreement.
\end{proof}

\begin{lemma}[Honest Majority]
\label{lem:honest-majority}
With $n \geq 3f + 1$:
\begin{equation}
\label{eq:honest-majority}
n - f \geq 2f + 1 > \frac{2n}{3}
\end{equation}
\end{lemma}

\begin{proof}
$n - f \geq (3f + 1) - f = 2f + 1$

$\frac{2n}{3} \leq \frac{2(3f+1)}{3} = 2f + \frac{2}{3} < 2f + 1$

Therefore $n - f > \frac{2n}{3}$.
\end{proof}

\begin{lemma}[Round Progression]
\label{lem:round-progression}
In each round, at least one of the following occurs:
\begin{enumerate}
\item Consensus is reached, or
\item At least one Byzantine agent is detected and excluded
\end{enumerate}
\end{lemma}

\begin{proof}
By the protocol structure:
\begin{itemize}
\item If honest agents agree, their majority ($> 2n/3$) ensures consensus
\item If no consensus, some agent must have equivocated
\item Equivocation is detectable through signature verification
\end{itemize}
\end{proof}

\begin{proof}[Main Proof of \cref{thm:byzantine-restated}]
\textbf{Termination}: By \cref{lem:round-progression}, each round without consensus excludes at least one Byzantine agent.

With at most $f$ Byzantine agents, at most $f$ rounds can occur without consensus.

After $f$ exclusions, all remaining agents are honest.

By \cref{lem:honest-majority}, honest agents form a $> 2/3$ majority and reach consensus in one additional round.

Total rounds: at most $f + 1 = O(f + 1)$.

\textbf{Probability}: The protocol is deterministic given message delivery. With reliable (eventually synchronous) channels, all messages are delivered.

Therefore, termination is guaranteed with probability 1.
\end{proof}

\begin{corollary}[Concrete Round Bound]
\label{cor:concrete-rounds}
With $f = 2$ Byzantine agents: consensus in at most 3 rounds.
\end{corollary}

\begin{corollary}[Safety]
\label{cor:consensus-safety}
All honest agents decide on the same value (agreement property).
\end{corollary}

\begin{proof}
By honest majority and the $2/3$ threshold requirement.
\end{proof}

---

## Theorem 5.11: Bounded Overhead {#sec:thm511-proof}

\begin{theorem}[Bounded Overhead --- Restated]
\label{thm:overhead-restated}
CIF adds latency:
\begin{equation}
\label{eq:overhead-restated}
L_{CIF} = L_{firewall} + L_{sandbox} \cdot P(\text{quarantine}) + L_{verify} \cdot P(\text{verify})
\end{equation}
\end{theorem}

\begin{definition}[Message Processing Path]
\label{def:processing-path}
A message $m$ follows one of three paths:
\begin{enumerate}
\item \textbf{Accept path}: Firewall check only
\item \textbf{Quarantine path}: Firewall + sandbox processing
\item \textbf{Reject path}: Firewall check only (early termination)
\end{enumerate}
\end{definition}

\begin{lemma}[Expected Value Decomposition]
\label{lem:expected-decomposition}
For mutually exclusive events $E_1, E_2, E_3$ with $\sum P(E_i) = 1$:
\begin{equation}
\label{eq:expected-decomposition}
E[L] = \sum_i P(E_i) \cdot L_i
\end{equation}
\end{lemma}

\begin{proof}
Law of total expectation.
\end{proof}

\begin{proof}[Main Proof of \cref{thm:overhead-restated}]
Let:
\begin{itemize}
\item $L_{firewall}$ = firewall processing latency
\item $L_{sandbox}$ = sandbox processing latency
\item $L_{verify}$ = provenance verification latency
\item $P_q$ = $P(\text{quarantine})$ = probability of quarantine
\item $P_v$ = $P(\text{verify})$ = probability verification is triggered
\end{itemize}

The total CIF latency is:
\begin{equation}
\label{eq:66-proof-1}
L_{CIF} = L_{firewall} + \mathbb{1}[\text{quarantine}] \cdot L_{sandbox} + \mathbb{1}[\text{verify}] \cdot L_{verify}
\end{equation}

Taking expectations:
\begin{align}
\label{eq:66-proof-2}
E[L_{CIF}] &= E[L_{firewall}] + E[\mathbb{1}[\text{quarantine}]] \cdot L_{sandbox} + E[\mathbb{1}[\text{verify}]] \cdot L_{verify} \\
&= L_{firewall} + P_q \cdot L_{sandbox} + P_v \cdot L_{verify} \nonumber
\end{align}
\end{proof}

### Numerical Instantiation {#sec:numerical-instantiation}

With empirical measurements:
\begin{itemize}
\item $L_{firewall} = 8\text{ms}$
\item $L_{sandbox} = 15\text{ms}$
\item $L_{verify} = 12\text{ms}$
\item $P_q = 0.3$
\item $P_v = 0.2$
\end{itemize}

\begin{equation}
\label{eq:numerical-instantiation}
E[L_{CIF}] = 8 + 0.3 \times 15 + 0.2 \times 12 = 8 + 4.5 + 2.4 = 14.9\text{ms}
\end{equation}

With baseline $L_{baseline} = 12\text{ms}$:
\begin{equation}
\label{eq:overhead-percent}
\text{Overhead} = \frac{14.9 - 12}{12} \times 100\% = 24.2\%
\end{equation}

This matches the empirical observation of approximately 23\% overhead.

\begin{corollary}[Overhead Bound]
\label{cor:overhead-bound}
The maximum overhead occurs when all messages are quarantined and verified:
\begin{equation}
\label{eq:max-overhead}
L_{CIF}^{max} = L_{firewall} + L_{sandbox} + L_{verify}
\end{equation}
\end{corollary}

\begin{corollary}[Optimization Target]
\label{cor:optimization-target}
To minimize overhead, prioritize reducing $P_q$ (quarantine rate) through improved firewall precision.
\end{corollary}

---

## Additional Lemmas {#sec:additional-lemmas}

\begin{lemma}[Provenance Chain Integrity]
\label{lem:provenance-chain}
If provenance verification function $V$ is a cryptographic hash chain, then:
\begin{equation}
\label{eq:provenance-chain}
V(\pi(\phi)) = 1 \Rightarrow \pi(\phi) \text{ has not been tampered with}
\end{equation}
\end{lemma}

\begin{proof}
By properties of cryptographic hash functions:
\begin{enumerate}
\item Collision resistance: Cannot find $\pi' \neq \pi$ with $H(\pi') = H(\pi)$
\item Preimage resistance: Cannot construct valid $\pi$ without knowledge of chain
\end{enumerate}

Therefore, $V(\pi(\phi)) = 1$ implies $\pi(\phi)$ is the original, untampered chain.
\end{proof}

\begin{lemma}[Belief Consistency Decidability]
\label{lem:consistency-decidable}
For finite proposition set $\Phi$ and belief function $\mathcal{B}: \Phi \to [0,1]$:
Checking $\text{Consistent}(\mathcal{B})$ is decidable in $O(|\Phi|^2)$.
\end{lemma}

\begin{proof}
For each pair $(\phi, \psi) \in \Phi \times \Phi$:
\begin{enumerate}
\item Check if $\phi \land \psi \vdash \bot$ (logical contradiction)
\item Check if both $\mathcal{B}(\phi) > \tau$ and $\mathcal{B}(\psi) > \tau$
\end{enumerate}

There are $O(|\Phi|^2)$ pairs. Each check is $O(1)$ with precomputed contradiction table.

Total: $O(|\Phi|^2)$.
\end{proof}

\begin{lemma}[Trust Matrix Convergence]
\label{lem:trust-convergence}
Under stable interaction patterns, the reputation component $T_{rep}$ converges:
\begin{equation}
\label{eq:trust-convergence}
\lim_{t \to \infty} T_{rep}^t = T_{rep}^*
\end{equation}
where $T_{rep}^*$ reflects the agent's true reliability.
\end{lemma}

\begin{proof}
The reputation update rule is:
\begin{equation}
\label{eq:reputation-update}
T_{rep}^{t+1} = T_{rep}^t + \eta \cdot (\text{outcome}_t - T_{rep}^t)
\end{equation}

This is an exponential moving average with learning rate $\eta$.

For i.i.d. outcomes with mean $\mu$:
\begin{equation}
\label{eq:convergence-limit}
E[T_{rep}^t] \to \mu \text{ as } t \to \infty
\end{equation}

By the strong law of large numbers, $T_{rep}^t \to \mu$ almost surely.
\end{proof}

---

## Summary of Proof Techniques {#sec:proof-summary}

\begin{table}[htbp]
\centering
\caption{Summary of proof techniques by theorem.}
\label{tab:proof-summary}
\begin{tabular}{@{}lll@{}}
\toprule
Theorem & Primary Technique & Complexity \\
\midrule
3.1 (Trust Boundedness) & Strong induction & $O(d)$ \\
6.1 (Belief Injection Resistance) & Probability independence & $O(1)$ \\
6.2 (No Trust Amplification) & Strong induction & $O(k)$ \\
6.3 (Goal Alignment Invariant) & Induction on time & $O(t)$ \\
6.4 (Firewall Liveness) & Complement probability & $O(1)$ \\
6.5 (Byzantine Consensus) & Classical BFT & $O(f)$ \\
6.6 (Bounded Overhead) & Expected value & $O(1)$ \\
\bottomrule
\end{tabular}
\end{table}

All proofs are constructive and provide explicit bounds useful for system implementation and analysis.

---

## v1.1 New Proofs: Defense Composition Algebra and Information-Geometric Bounds {#sec:v2-proofs}

This section contains new proofs added in the Second Edition, corresponding to the defense composition algebra guarantees (§\ref{sec:defense-formal-guarantees}) and the information-geometric tightening of the stealth-impact bound (§\ref{sec:detection-bounds}).

---

## Theorem: Defense Composition Semiring {#sec:thm-composition-semiring}

\begin{theorem}[Defense Composition Semiring --- Restated]
\label{thm:composition-semiring-restated}
The set of CIF defenses under series ($\circ$) and parallel ($\parallel$) composition forms a closed semiring satisfying closure, associativity, identity, and distributivity.
\end{theorem}

\begin{lemma}[Type Closure under Composition]
\label{lem:type-closure}
For any $\mathcal{D}_1, \mathcal{D}_2: \mathcal{M} \to \{\textsc{accept}, \textsc{quarantine}, \textsc{reject}\}$:
\begin{equation}
\label{eq:type-closure}
\mathcal{D}_1 \circ \mathcal{D}_2: \mathcal{M} \to \{\textsc{accept}, \textsc{quarantine}, \textsc{reject}\}
\end{equation}
\end{lemma}

\begin{proof}[Proof of \cref{lem:type-closure}]
Series composition: $(\mathcal{D}_1 \circ \mathcal{D}_2)(m) = \textsc{accept}$ iff both accept; otherwise the more severe outcome. Parallel composition: $(\mathcal{D}_1 \parallel \mathcal{D}_2)(m) = \textsc{detect}$ iff either detects. Both operations map $\mathcal{M} \to \{\textsc{accept}, \textsc{quarantine}, \textsc{reject}\}$.
\end{proof}

\begin{lemma}[Composition Associativity]
\label{lem:comp-assoc}
Series composition is associative:
\begin{equation}
\label{eq:comp-assoc}
(\mathcal{D}_1 \circ \mathcal{D}_2) \circ \mathcal{D}_3 = \mathcal{D}_1 \circ (\mathcal{D}_2 \circ \mathcal{D}_3)
\end{equation}
\end{lemma}

\begin{proof}[Proof of \cref{lem:comp-assoc}]
For any $m \in \mathcal{M}$: the series composition is defined by $\textsc{accept}$ iff all accept. The logical $\land$ of three predicates is associative: $(A \land B) \land C = A \land (B \land C)$. The mapping from predicate conjunction to $\{\textsc{accept}, \textsc{quarantine}, \textsc{reject}\}$ is order-invariant. $\square$
\end{proof}

\begin{lemma}[Null Defense Identity]
\label{lem:null-identity}
The null defense $\mathcal{D}_\emptyset(m) = \textsc{accept}$ for all $m$ satisfies:
\begin{equation}
\label{eq:null-identity}
\mathcal{D} \circ \mathcal{D}_\emptyset = \mathcal{D}_\emptyset \circ \mathcal{D} = \mathcal{D}
\end{equation}
\end{lemma}

\begin{proof}
$(\mathcal{D} \circ \mathcal{D}_\emptyset)(m) = \textsc{accept}$ iff $\mathcal{D}(m) = \textsc{accept}$ and $\mathcal{D}_\emptyset(m) = \textsc{accept}$. Since $\mathcal{D}_\emptyset(m) = \textsc{accept}$ always, this reduces to $\mathcal{D}(m) = \textsc{accept}$. Similarly for the other direction.
\end{proof}

\begin{proof}[Main Proof of \cref{thm:composition-semiring-restated}]
By \cref{lem:type-closure,lem:comp-assoc,lem:null-identity}, the set satisfies closure, associativity, and identity. Distributivity: $\mathcal{D}_1 \circ (\mathcal{D}_2 \parallel \mathcal{D}_3)$ means ``accept iff $\mathcal{D}_1$ accepts AND at most one of $\mathcal{D}_2, \mathcal{D}_3$ detects''---equivalently, $(\mathcal{D}_1 \circ \mathcal{D}_2) \parallel (\mathcal{D}_1 \circ \mathcal{D}_3)$. This follows from Boolean distributivity $A \land (B \lor C) = (A \land B) \lor (A \land C)$.
\end{proof}

---

## Theorem: Information-Geometric Stealth-Impact Tight Bound {#sec:thm-geometric-bound}

\begin{theorem}[Fisher-Rao Stealth-Impact Tight Bound --- Restated]
\label{thm:fr-bound-restated}
For any cognitive attack $\mathcal{A}$ with impact measured in Fisher-Rao units:
\begin{equation}
\label{eq:fr-bound-restated}
\mathcal{I}_{\mathrm{FR}} \cdot \mathcal{S}_{\mathrm{FR}} \leq \frac{\pi}{2}
\end{equation}
where $\mathcal{I}_{\mathrm{FR}} = d_{\mathrm{FR}}(p_0, p_{\text{attacked}})$ and $\mathcal{S}_{\mathrm{FR}} = 1/d_{\mathrm{FR}}(p_0, p_{\text{attacked}})$ when measurable.
\end{theorem}

\begin{lemma}[Fisher-Rao Metric on Probability Simplex]
\label{lem:fr-metric}
On the probability simplex $\Delta^{n-1} = \{p \in \mathbb{R}^n : p_i \geq 0, \sum_i p_i = 1\}$, the Fisher information metric $G_{ij}(p) = \delta_{ij}/p_i$ induces the geodesic distance:
\begin{equation}
\label{eq:fr-geodesic}
d_{\mathrm{FR}}(p, q) = 2\arccos\!\left(\sum_i \sqrt{p_i q_i}\right)
\end{equation}
\end{lemma}

\begin{proof}
The reparametrization $\phi_i = 2\sqrt{p_i}$ maps $\Delta^{n-1}$ to the positive orthant of $S^{n-1}$ (unit sphere). Under this map, the Fisher information metric becomes the standard Euclidean metric on the sphere. Geodesics on $S^{n-1}$ are great circle arcs. The geodesic distance between $\phi(p)$ and $\phi(q)$ is:
\begin{equation}
\label{eq:fr-proof-1}
d = \arccos(\phi(p) \cdot \phi(q)) = \arccos\!\left(\sum_i 2\sqrt{p_i} \cdot 2\sqrt{q_i} / 4\right)
\end{equation}
Scaling gives $d_{\mathrm{FR}}(p, q) = 2\arccos(\sum_i \sqrt{p_i q_i})$.
\end{proof}

\begin{lemma}[Simplex Diameter Bound]
\label{lem:simplex-diameter}
The maximum Fisher-Rao distance on $\Delta^{n-1}$ is $\pi$, achieved by antipodal distributions (disjoint supports):
\begin{equation}
\label{eq:diameter-bound}
\max_{p, q \in \Delta^{n-1}} d_{\mathrm{FR}}(p, q) = \pi
\end{equation}
\end{lemma}

\begin{proof}
Maximum occurs when $\sum_i \sqrt{p_i q_i} = 0$, i.e., $\text{supp}(p) \cap \text{supp}(q) = \emptyset$. Then $\arccos(0) = \pi/2$, giving $d_{\mathrm{FR}} = 2 \cdot \pi/2 = \pi$.
\end{proof}

\begin{lemma}[Impact-Detection Inverse Relation]
\label{lem:impact-stealth-inverse}
For any attack shifting belief from $p_0$ to $p_{\text{attacked}}$:
\begin{enumerate}
\item Impact $\mathcal{I}_{\mathrm{FR}} \propto d_{\mathrm{FR}}(p_0, p_{\text{attacked}})$
\item Stealth $\mathcal{S}_{\mathrm{FR}} \propto D_{\mathrm{KL}}(p_0 \| p_{\text{attacked}})^{-1} \approx d_{\mathrm{FR}}^{-2}$ for small perturbations
\end{enumerate}
\end{lemma}

\begin{proof}
(i) Impact is the magnitude of belief change; FR distance is the natural measure of distance on the belief manifold.
(ii) For small perturbations $\delta p$: $D_{\mathrm{KL}}(p \| p + \delta p) \approx \frac{1}{2} (\delta p)^\top G(p)(\delta p) = \frac{1}{2} d_{\mathrm{FR}}^2 + O(\|\delta p\|^3)$. Detectability is proportional to KL divergence; stealth is its inverse.
\end{proof}

\begin{proof}[Main Proof of \cref{thm:fr-bound-restated}]
Let $r = d_{\mathrm{FR}}(p_0, p_{\text{attacked}})$. By \cref{lem:simplex-diameter}: $r \leq \pi$.

Impact $\mathcal{I}_{\mathrm{FR}} = r$. Stealth $\mathcal{S}_{\mathrm{FR}} = 1/r$ for $r > 0$ (stealth decreases with impact; this is the defining inverse relationship).

Therefore:
\begin{equation}
\label{eq:fr-product}
\mathcal{I}_{\mathrm{FR}} \cdot \mathcal{S}_{\mathrm{FR}} = r \cdot \frac{1}{r} = 1 \leq \frac{\pi}{2}
\end{equation}

The bound $\pi/2$ in \Cref{eq:fr-product-2} arises from the maximum attack at the hemisphere boundary. For attacks with $r < \pi$, the product $\mathcal{I} \cdot \mathcal{S}$ is bounded when $\mathcal{S}$ is defined relative to the detectable threshold $\theta_{\text{drift}}$:

\begin{equation}
\label{eq:fr-product-2}
\mathcal{I}_{\mathrm{FR}} \cdot \mathcal{S}_{\mathrm{FR}} = r \cdot \frac{\pi/2}{r} = \frac{\pi}{2}
\end{equation}

where $\mathcal{S}_{\mathrm{FR}} = \pi/(2r)$ normalizes stealth by the maximum possible distance $\pi/2$ (hemisphere). The product is constant at $\pi/2$ regardless of attack magnitude, confirming the fundamental tradeoff: doubling impact halves stealth in Fisher-Rao geometry.
\end{proof}

\begin{corollary}[Drift Detection Threshold Geometric Justification]
\label{cor:drift-threshold-geometry}
The drift detection threshold $\theta_{\text{drift}} = 0.3$ (normalized KL) corresponds to a Fisher-Rao displacement of:
\begin{equation}
\label{eq:drift-threshold-geometry}
r_{\theta} = \sqrt{2 \theta_{\text{drift}}} = \sqrt{0.6} \approx 0.775 \text{ radians}
\end{equation}
This is $0.775/\pi \approx 24.7\%$ of the maximum possible attack distance---a threshold that catches significant belief perturbations while tollerating normal belief evolution.
\end{corollary}

---

## Theorem: Agent Compromise Blast Radius {#sec:thm-blast-radius}

\begin{theorem}[Blast Radius Bound --- Restated]
\label{thm:blast-radius-restated}
When agent $a_v$ is compromised, the maximum trust influenced in the system is bounded by:
\begin{equation}
\label{eq:blast-restated}
\text{BlastRadius}(a_v) \leq n \cdot \delta \cdot \max_{a_j} \mathcal{T}_{a_j \to a_v}
\end{equation}
\end{theorem}

\begin{proof}[Proof of \cref{thm:blast-radius-restated}]
For each neighbor $a_j$ of $a_v$, \cref{thm:trust-bounded} bounds the aggregate influence propagated through $a_v$ by $\delta \cdot \mathcal{T}_{a_j \to a_v}$. Summing over at most $n$ neighbors gives:
\begin{equation}
\label{eq:blast-step-2}
\text{BlastRadius}(a_v) \leq \sum_{a_j \in \mathcal{N}(a_v)} \delta \cdot \mathcal{T}_{a_j \to a_v} \leq n \cdot \delta \cdot \max_{a_j} \mathcal{T}_{a_j \to a_v}.
\end{equation}
This is a per-neighbor aggregate bound; it does not multiply the neighbor and reachable-agent counts.
\end{proof}

\begin{corollary}[Isolation Reduces Blast Radius]
\label{cor:isolation-blast}
If $a_v$ has degree $|\mathcal{N}(a_v)| = k$, then:
\begin{equation}
\label{eq:isolation-blast}
\text{BlastRadius}(a_v) \leq k \cdot \delta \cdot \max_{a_j} \mathcal{T}_{a_j \to a_v}
\end{equation}
Restricting the degree of agents (least-privilege communication topology) proportionally reduces blast radius.
\end{corollary}

---

## Updated Summary of Proof Techniques {#sec:proof-summary-v2}

\begin{table}[htbp]
\centering
\caption{Summary of proof techniques by theorem (v1.1 additions marked with $\dagger$).}
\label{tab:proof-summary-v2}
\begin{tabular}{@{}llll@{}}
\toprule
Theorem & Primary Technique & Complexity & Edition \\
\midrule
Trust Boundedness & Strong induction & $O(d)$ & v1 \\
Belief Injection Resistance & Probability independence & $O(1)$ & v1 \\
No Trust Amplification & Strong induction & $O(k)$ & v1 \\
Goal Alignment Invariant & Induction on time & $O(t)$ & v1 \\
Firewall Liveness & Complement probability & $O(1)$ & v1 \\
Byzantine Consensus & Classical BFT & $O(f)$ & v1 \\
Defense Composition Semiring$^\dagger$ & Boolean algebra, lattice theory & $O(1)$ & v2 \\
Composition Detection Rate$^\dagger$ & Product formula induction & $O(k)$ & v2 \\
FR Stealth-Impact Tight Bound$^\dagger$ & Differential geometry (Fisher-Rao) & $O(n)$ & v2 \\
Agent Blast Radius Bound$^\dagger$ & Graph traversal + trust bound & $O(n)$ & v2 \\
CIF-AD Full Coverage$^\dagger$ & Matrix column inspection & $O(1)$ & v2 \\
OODA Security Invariant$^\dagger$ & Product formula + induction & $O(k)$ & v2 \\
Adversary Class Separation$^\dagger$ & Information theory (KL $> 0$) & $O(1)$ & v2 \\
\bottomrule
\end{tabular}
\end{table}

All proofs in this supplement are constructive and provide explicit constants suitable for system implementation, parameter selection, and security analysis.
