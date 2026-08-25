\newpage

# Limitations and Boundary Conditions {#sec:limitations}

This section characterizes the formal boundary conditions under which the Cognitive Integrity Framework (CIF) guarantees hold, identifies classes of attacks that fall outside the formal protection envelope, and discusses open problems. Honest characterization of limitations is essential for deployment decisions.

## Formal Assumptions and Where They Break {#sec:assumption-breakdown}

### Assumption 1: Honest Orchestrator for $\Omega_1$--$\Omega_4$

The CIF trust calculus (§\ref{sec:trust-calculus}) and Byzantine consensus (§\ref{sec:coord-defenses}) assume the orchestrator agent $a_0$ is non-faulty for adversary classes $\Omega_1$--$\Omega_4$.

\begin{property}[Orchestrator Compromise Boundary]
\label{prop:orchestrator-limit}
If $a_0 \in \text{Compromised}$, then:
\begin{equation}
\label{eq:orchestrator-failure}
P(\text{CIF protection holds}) \leq P(\text{detection before orchestrator acts})
\end{equation}
The CIF cannot guarantee cognitive integrity when the orchestrator is compromised under an $\Omega_5$ attack.
\end{property}

**Mitigation**: Defense-in-depth across sub-agents reduces the blast radius of orchestrator compromise. Each sub-agent's own CIF implementation (firewall, sandbox, tripwires) provides last-line-of-defense protection even when instructions arrive from a compromised orchestrator.

### Assumption 2: Bounded Faulty Agents ($f < n/3$)

The Byzantine consensus guarantee requires $f < n/3$.

\begin{property}[Byzantine Threshold Violation]
\label{prop:byz-limit}
When $f \geq n/3$, no deterministic Byzantine consensus protocol can guarantee Agreement and Validity simultaneously (Fischer-Lynch-Paterson impossibility).
\end{property}

\begin{table}[htbp]
\centering
\caption{Byzantine fault tolerance break-even: minimum $n$ to tolerate $f$ faults.}
\label{tab:byz-limits}
\begin{tabular}{@{}lll@{}}
\toprule
Desired tolerance $f$ & Required $n$ & Overhead factor \\
\midrule
1 & 4 & 4.0x \\
2 & 7 & 3.5x \\
5 & 16 & 3.2x \\
10 & 31 & 3.1x \\
$f$ (general) & $3f+1$ & $\approx 3x$ \\
\bottomrule
\end{tabular}
\end{table}

**Mitigation**: Small-n deployments (e.g., $n=3$) cannot tolerate even one faulty agent under Byzantine consensus. For small systems, substitute Byzantine consensus with cryptographic attestation protocols and human-in-the-loop verification.

### Assumption 3: Independent Defense Mechanisms

The composition theorems (§\ref{sec:defense-composition}) assume independence between defense mechanisms.

\begin{property}[Correlated Failure Mode]
\label{prop:correlated-failure}
If defenses share a common dependency $X$ that can be attacked:
\begin{equation}
\label{eq:correlated-failure}
P(\text{all defenses fail}) = P(\text{all fail} \mid X \text{ compromised}) \cdot P(X \text{ compromised}) \gg \prod_i P(\mathcal{D}_i \text{ fails})
\end{equation}
Correlated failures invalidate the product formula from Theorem~\ref{thm:composition-bound}.
\end{property}

**Common correlated dependencies**: shared embedding model, shared provenance database, shared communication bus. Architectural diversity---using independently implemented detectors from different codebases---reduces this risk.

### Assumption 4: Stationary Attack Distributions

The information-theoretic bounds (§\ref{sec:it-detection-limits}) assume stable distributions $P_{\text{attack}}$ and $P_{\text{benign}}$.

\begin{property}[Distribution Shift Degradation]
\label{prop:dist-shift}
Under adaptive adversaries that observe detection patterns and adjust:
\begin{equation}
\label{eq:dist-shift}
D_{\mathrm{KL}}(P_{\text{attack}}^t \| P_{\text{benign}}) \xrightarrow{t \to \infty} 0
\end{equation}
The adversary converges to the boundary of the undetectable regime through hill-climbing.
\end{property}

**Mitigation**: Rotate detector thresholds and features unpredictably, making it harder for adversaries to model the detection boundary. The CUSUM drift detector (Definition~\ref{def:cusum-detector}) adapts to baseline shifts, but adversaries aware of this can target the CUSUM state directly.

### Assumption 5: Bounded Computational Complexity

The firewall pattern matching and semantic analysis assume bounded adversary compute ($R_C < R_{\text{defender}}$).

\begin{property}[Compute Asymmetry Reversal]
\label{prop:compute-limit}
When adversary compute exceeds defender: $R_C^{\text{adv}} > R_C^{\text{def}}$, the adversary can:
\begin{itemize}
\item Exhaustively search the classifier's decision boundary
\item Generate adversarial examples by gradient optimization against the firewall
\item Brute-force semantic embeddings to find near-miss adversarial payloads
\end{itemize}
\end{property}

This is an instance of the general adversarial ML problem \cite{adaptive2025attacks}. Certified defenses (randomized smoothing, provable robustness certificates) are necessary for compute-unlimited adversaries but introduce significant performance overhead.

## Scope Limitations {#sec:scope-limits}

### What CIF Does Not Cover

\begin{table}[htbp]
\centering
\caption{Out-of-scope threats and recommended mitigations.}
\label{tab:out-of-scope}
\begin{tabular}{@{}lp{5cm}p{5cm}@{}}
\toprule
Threat Type & Why Out of Scope & Recommended Mitigation \\
\midrule
Training-time poisoning & Occurs before deployment; CIF operates at runtime & ML supply chain security, model cards, red-teaming \\
Physical side channels & Hardware-level, outside software model & Hardware security modules, physical security \\
Side-channel inference & Timing/power attacks on computation & Constant-time implementations, noise injection \\
Adversarial ML & Gradient-based input perturbations against detectors & Certified robustness, randomized smoothing \\
Long-context optimization & Adversary optimizes prompt over thousands of tokens & Context-length bounds, segmentation \\
Multi-principal conflicts & Legitimate principals with conflicting goals & Principal hierarchy governance, not security \\
\bottomrule
\end{tabular}
\end{table}

### Model-Level vs. System-Level Security

CIF operates at the \textit{system level}: it governs how agents interact, communicate, and delegate. It does not provide guarantees about what individual language models will produce in response to prompts.

\begin{property}[Model-Level Attack Residual]
\label{prop:model-level-residual}
Even with CIF fully deployed, a language model fine-tuned with malicious data (training-time attack) may produce adversarial outputs that pass all CIF checks:
\begin{equation}
\label{eq:model-residual}
P(\text{malicious output} \mid \text{CIF deployed}, \text{poisoned model}) \not\leq P(\text{malicious output} \mid \text{CIF deployed}, \text{clean model})
\end{equation}
CIF defends system interactions; model-level safety requires separate mechanisms.
\end{property}

## Tightness of Formal Bounds {#sec:bound-tightness}

### Trust Decay Bound

The trust bound $\mathcal{T}_{i \to k}^{\text{del}} \leq \delta^d$ (Theorem~\ref{thm:trust-bounded}) is tight: it is achieved when all intermediate trust values equal 1 and only the decay factor reduces trust. In practice, the min operator in the delegation formula (Definition~\ref{def:trust-delegation}) produces even tighter bounds. The formal bound is conservative.

### Detection Rate Composition

The composition formula $P_{\text{detect}} = 1 - \prod(1-r_i)$ (Theorem~\ref{thm:composition-bound}) assumes independence. When defenses are correlated, the actual detection rate satisfies:
\begin{equation}
\label{eq:corr-composition}
P_{\text{detect}}^{\text{corr}} = 1 - \prod_i (1-r_i) + \sum_{i < j} \text{Cov}(\mathbb{1}[D_i \text{ detects}], \mathbb{1}[D_j \text{ detects}])
\end{equation}
Positive covariance (defenses that tend to detect together) reduces diversity benefit. The composition formula is an upper bound under positive correlation.

### Information-Geometric Stealth-Impact Bound

The stealth-impact bound $\mathcal{I} \cdot \mathcal{S} \leq \pi/2$ (Remark~\ref{rem:geometric-bound}) uses the Fisher-Rao metric under a uniform prior. For highly concentrated belief distributions (near-certain beliefs), the curvature is higher and the bound tightens. The $\pi/2$ constant is the asymptotic value for maximally spread distributions.

## Open Problems {#sec:open-problems}

\begin{enumerate}
\item \textbf{Tight Detection Bounds under Adaptive Adversaries}: Theorem~\ref{thm:undetectability} assumes a fixed attack distribution. Deriving minimax bounds under adaptive adversaries remains open.

\item \textbf{Optimal $\delta$ Selection}: The trust decay factor $\delta$ is treated as a fixed parameter. Deriving the optimal $\delta$ as a function of threat model, topology, and task requirements is an open optimization problem.

\item \textbf{Multi-Principal Trust Aggregation}: When multiple legitimate principals provide trust credentials, aggregating them without creating amplification is non-trivial. The current framework assumes a single trust authority per domain.

\item \textbf{Privacy-Preserving Consensus}: Byzantine consensus requires agents to share belief states. For privacy-sensitive deployments, achieving consensus without revealing individual beliefs (via secure multi-party computation or zero-knowledge proofs) is an active research problem.

\item \textbf{Formal Verification of CIF Implementations}: The proofs in this paper assume the CIF implementation exactly matches the formal model. Bridging the gap between formal specification and implementation (via model checking, theorem proving, or formal synthesis) is necessary for high-assurance deployments.

\item \textbf{OODA Cycle Time Bounds}: Property~\ref{prop:ooda-latency} gives a sufficient condition but not a tight bound on the minimum OODA cycle time compatible with full CIF monitoring. Characterizing this bound as a function of defense portfolio is open.
\end{enumerate}

> **What Part 2 validates empirically**: Part 2 \cite{friedman2026cogsec2} tests CIF under conditions that stress several of the assumptions above. Specifically: (1) Assumptions 1--2 (honest orchestrator, bounded faults) are validated by architecture-specific experiments across the hierarchical, autonomous-mesh, role-based and graph-based topologies of Part 2's four adapters; (2) Assumption 3 (independent defenses) is tested via ablation studies in which the strongest pairwise synergy---Firewall + Detection, at $+0.050$ beyond additive---is roughly an order of magnitude smaller than the leave-one-out contribution of the single dominant module, so on that corpus independence is neither confirmed nor cleanly refuted; (3) Assumption 4 (stationary distributions) is tested via five rounds of adversarial training confirming distribution shift degrades static detectors; and (4) Assumption 5 (bounded compute) is implicitly bounded by the 950-attack corpus scope. The 10--11 percentage-point gap between parametric ceiling and prototype pipeline performance is attributed to adapter implementation maturity, not to violation of the formal assumptions (Part 2's Conclusion, "Honest Gap Characterization").
