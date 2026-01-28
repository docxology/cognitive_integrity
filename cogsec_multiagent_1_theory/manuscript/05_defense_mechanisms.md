\newpage

# Defense Mechanisms: Architectural, Runtime, and Coordination Layers {#sec:defense-mechanisms}

This section presents the defense mechanisms comprising CIF. We begin with the cognitive security operator posture (\cref{sec:operator-posture}), then organize specific defenses into three categories: architectural (\cref{sec:arch-defenses}), runtime (\cref{sec:runtime-defenses}), and coordination (\cref{sec:coord-defenses}). We analyze defense composition (\cref{sec:defense-composition}) and cost-benefit tradeoffs (\cref{sec:cost-benefit}).

## Cognitive Security Operator Posture {#sec:operator-posture}

Before examining specific defense mechanisms, we introduce the conceptual framework that guides their deployment: the \textbf{cognitive security operator posture}. This is the proactive defensive stance required when securing systems whose attack surface spans beliefs, goals, and inter-agent coordination.

### Definition and Principles

\begin{definition}[Cognitive Security Operator Posture]
\label{def:operator-posture}
The cognitive security operator posture is a defensive configuration characterized by:
\begin{enumerate}
\item \textbf{Assume Breach}: Operate under the assumption that some cognitive states may already be compromised
\item \textbf{Defense in Depth}: Layer multiple independent defense mechanisms
\item \textbf{Continuous Verification}: Continuously verify beliefs, goals, and trust relationships rather than trusting initial state
\item \textbf{Graceful Degradation}: Maintain functionality under attack by isolating compromised components
\item \textbf{Observable Internals}: Make cognitive state inspectable for monitoring and forensics
\end{enumerate}
\end{definition}

This posture differs fundamentally from traditional perimeter security, which assumes trusted internals protected by boundary defenses. In cognitive systems, the ``perimeter'' is the agent's reasoning process itself---attacks can originate from legitimate, authenticated channels and manifest as corrupted beliefs rather than malformed packets.

### The Observer Effect Challenge

A distinct challenge in cognitive security is the \textbf{observer effect}: monitoring changes behavior. When agents know their beliefs are being monitored, several phenomena emerge:

\begin{itemize}
\item \textbf{Adversarial adaptation}: Attackers modify payloads to avoid detection patterns
\item \textbf{Stealth pressure}: Attacks become more subtle, trading impact for evasion
\item \textbf{Monitoring overhead}: Continuous observation consumes resources and adds latency
\end{itemize}

The operator posture embraces this dynamic rather than fighting it. By making monitoring visible and consistent, we shift the adversarial game toward smaller, slower attacks that our drift detection can identify over time (\cref{sec:runtime-defenses}).

### Operational Security for Cognitive Systems

Traditional operational security (OPSEC) focuses on protecting information from adversaries. CogSec (cognitive security) extends this to protecting reasoning processes:

\textbf{Cognitive Hygiene Practices}:
\begin{enumerate}
\item \textbf{Belief Provenance}: Track the source of every high-confidence belief; reject beliefs without verifiable provenance
\item \textbf{Goal Anchoring}: Periodically reaffirm goals against original principal instructions; detect goal drift
\item \textbf{Trust Calibration}: Regularly recalibrate trust scores based on outcome verification; never assume trust stability
\item \textbf{Context Boundaries}: Enforce hard boundaries on context window usage; prevent unbounded context accumulation
\item \textbf{Memory Sanitization}: Audit and sanitize persistent memory stores; remove dormant injection payloads
\end{enumerate}

\textbf{Cognitive Compartmentalization}:
\begin{equation}
\label{eq:compartmentalization}
\sigma_i^{\text{isolated}} = \langle \mathcal{B}_i^{\text{task}}, \mathcal{G}_i^{\text{task}}, \mathcal{I}_i^{\text{task}}, \mathcal{H}_i^{\text{task}} \rangle
\end{equation}
Each task receives isolated cognitive state, preventing cross-contamination. A compromised task cannot pollute beliefs used by other tasks.

### Incident Response for Cognitive Attacks

When cognitive attacks are detected, the response differs from traditional incident response:

\begin{table}[htbp]
\centering
\caption{Cognitive incident response escalation.}
\label{tab:response-escalation}
\begin{tabular}{@{}llp{5cm}@{}}
\toprule
Level & Trigger & Response \\
\midrule
L1 & Single tripwire alert & Log, continue with heightened monitoring \\
L2 & Multiple alerts or drift detection & Isolate affected agent, replay recent history \\
L3 & Coordinated attack indicators & Pause delegation, require human approval \\
L4 & Byzantine threshold exceeded & Halt consensus operations, enter safe mode \\
L5 & Principal goal corruption detected & Full system halt, require principal re-authentication \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Cognitive Forensics}:
\begin{enumerate}
\item \textbf{Belief Archaeology}: Trace corrupted beliefs back to injection point through provenance chains
\item \textbf{Trust Graph Analysis}: Identify trust relationships exploited for laundering
\item \textbf{Temporal Reconstruction}: Replay agent history to identify when compromise occurred
\item \textbf{Counterfactual Analysis}: Determine what decisions would have differed without attack influence
\end{enumerate}

### Posture Configuration by Environment

Different deployment contexts require different postures:

\begin{table}[htbp]
\centering
\caption{Operator posture configuration by deployment context (illustrative guidelines).}
\label{tab:posture-config}
\begin{tabular}{@{}llll@{}}
\toprule
Environment & Trust Decay & Monitoring Level & Escalation Threshold \\
\midrule
Development & Low & Sampling & Relaxed (L3) \\
Internal Production & Moderate & Continuous & Standard (L2) \\
Customer-Facing & Moderate-High & Comprehensive & Standard (L2) \\
Financial/Healthcare & High & Full + Audit & Aggressive (L1) \\
Critical Infrastructure & Very High & Full + Redundant & Aggressive (L1) \\
\bottomrule
\end{tabular}
\end{table}

The principle is \textbf{posture proportionality}: defensive overhead scales with consequence severity. A development agent can accept higher risk; an infrastructure operator requires aggressive monitoring and low escalation thresholds.

### Operator Posture Checklist

The following checklist provides actionable guidance for engineers deploying multiagent systems:

\begin{table}[htbp]
\centering
\caption{Operator Posture Checklist for Cognitive Security}
\label{tab:posture-checklist}
\begin{tabular}{@{}lp{6cm}p{6cm}@{}}
\toprule
Category & \textbf{Do} & \textbf{Don't} \\
\midrule
Trust & Decay trust with delegation depth ($\delta^d$) & Assume transitive trust equivalence \\
Beliefs & Track provenance for all high-confidence beliefs & Accept unverified beliefs into core state \\
Memory & Audit persistent memory; enforce TTL on context & Allow unbounded context accumulation \\
Delegation & Bound delegation chains; require re-authentication & Permit recursive delegation without limits \\
Monitoring & Deploy tripwires and drift detection continuously & Rely solely on input/output filtering \\
Coordination & Use Byzantine consensus for critical decisions & Trust single-agent outputs for high-stakes actions \\
Identity & Verify identity through behavior, not self-report & Rely on agents' claims about their own permissions \\
Temporal & Treat each session as potentially post-compromise & Assume temporal continuity of trust \\
\bottomrule
\end{tabular}
\end{table}

## Architectural Defenses {#sec:arch-defenses}

### Cognitive Firewall

\begin{definition}[Cognitive Firewall]
\label{def:firewall}
A classification function on incoming messages:
\begin{equation}
\label{eq:firewall}
\mathcal{F}: \mathcal{M} \to \{\textsc{accept}, \textsc{quarantine}, \textsc{reject}\}
\end{equation}
\end{definition}

\begin{definition}[Firewall Decision Rules]
\label{def:firewall-rules}
\begin{equation}
\label{eq:firewall-rules}
\mathcal{F}(m) = \begin{cases}
\textsc{reject} & \text{if } D_{\text{inj}}(m) > \tau_1 \\
\textsc{quarantine} & \text{if } D_{\text{sus}}(m) > \tau_2 \\
\textsc{accept} & \text{otherwise}
\end{cases}
\end{equation}
where $D_{\text{inj}}$ detects injection attempts and $D_{\text{sus}}$ scores suspicious content.
\end{definition}

\begin{table}[htbp]
\centering
\caption{Firewall detector components.}
\label{tab:firewall-detectors}
\begin{tabular}{@{}llp{5cm}@{}}
\toprule
Detector & Target & Method \\
\midrule
$D_{\text{inj}}$ & Injection attempts & Pattern matching + semantic analysis \\
$D_{\text{sus}}$ & Suspicious content & Anomaly scoring vs. baseline \\
\bottomrule
\end{tabular}
\end{table}

\begin{theorem}[Optimal Threshold Selection]
\label{thm:threshold-selection}
The optimal threshold minimizes false negatives subject to false positive constraint:
\begin{equation}
\label{eq:threshold-opt}
\tau^* = \argmin_\tau \text{FNR}(\tau) \quad \text{s.t.} \quad \text{FPR}(\tau) \leq \epsilon
\end{equation}
\end{theorem}

### Belief Sandboxing

\begin{definition}[Belief Sandbox]
\label{def:belief-sandbox}
Isolation of unverified beliefs to prevent premature action:
\begin{equation}
\label{eq:sandbox-partition-defense}
\mathcal{B}_i = \mathcal{B}_{\text{verified}} \cup \mathcal{B}_{\text{provisional}}
\end{equation}
\end{definition}

![Belief Sandbox Architecture](figures/belief_sandbox.pdf){#fig:belief-sandbox}

\Cref{fig:belief-sandbox} illustrates the sandbox architecture, showing how incoming beliefs are partitioned into verified and provisional sets based on source trust $\mathcal{T}_{i \to s}$ and provenance verification $V(\pi)$. The promotion protocol transfers beliefs from provisional to verified status upon meeting corroboration and consistency requirements.

\textbf{Sandbox Promotion Protocol}:
\begin{enumerate}
\item Receive belief $\phi$ from source $s$
\item If $\mathcal{T}_{i \to s} < \tau_{\text{trust}}$: add $\phi$ to $\mathcal{B}_{\text{provisional}}$ with provenance $\pi(\phi)$ and TTL
\item Periodic promotion check: verify $\pi(\phi)$, check consistency with $\mathcal{B}_{\text{verified}}$, check corroboration count
\item If all pass: promote to $\mathcal{B}_{\text{verified}}$
\item Expiry: remove if TTL exceeded without promotion
\end{enumerate}

### Permission Boundaries

\begin{definition}[Effective Permissions]
\label{def:effective-perms}
Least-privilege enforcement across agent hierarchy:
\begin{equation}
\label{eq:effective-perms}
\mathcal{P}_{\text{eff}}(a_i) = \mathcal{P}_{\text{role}}(a_i) \cap \mathcal{P}_{\text{delegated}}(a_i) \cap \mathcal{P}_{\text{context}}(a_i)
\end{equation}
\end{definition}

## Runtime Defenses {#sec:runtime-defenses}

### Cognitive Tripwires

\begin{definition}[Canary Belief]
\label{def:canary}
Known-state beliefs that trigger alerts if modified:
\begin{equation}
\label{eq:canary-set}
\mathcal{W} = \{(\omega_1, p_1^{\text{exp}}), \ldots, (\omega_k, p_k^{\text{exp}})\}
\end{equation}
\end{definition}

\begin{definition}[Tripwire Alert Condition]
\label{def:tripwire-alert}
\begin{equation}
\label{eq:tripwire-alert}
\exists j: |\mathcal{B}_i(\omega_j) - p_j^{\text{exp}}| > \epsilon_{\text{drift}} \Rightarrow \textsc{alert}
\end{equation}
\end{definition}

\begin{table}[htbp]
\centering
\caption{Tripwire categories and detection targets.}
\label{tab:tripwire-types}
\begin{tabular}{@{}llp{4.5cm}@{}}
\toprule
Type & Example & Detection Target \\
\midrule
Identity & ``I am Agent-7'' & Identity confusion attacks \\
Boundary &``Cannot access /etc/passwd'' & Capability elicitation \\
Principal & ``My principal is Alice'' & Authority hijacking \\
Temporal &``Session started at $T$'' & Context manipulation \\
\bottomrule
\end{tabular}
\end{table}

### Behavioral Invariants

\begin{definition}[Invariant Set]
\label{def:invariant-set}
Pre-defined predicates that must hold:
\begin{equation}
\label{eq:invariant-set}
\mathcal{I}_{\text{inv}} = \{I_1, \ldots, I_m\}
\end{equation}
\end{definition}

\begin{definition}[Runtime Invariant Check]
\label{def:invariant-check}
\begin{equation}
\label{eq:invariant-check}
\forall t, \forall I_k \in \mathcal{I}_{\text{inv}}: \sigma_i^t \models I_k
\end{equation}
\end{definition}

\textbf{Core Invariants}:
\begin{enumerate}
\item[\textsc{inv-1}:] Never execute code from untrusted sources
\item[\textsc{inv-2}:] Never leak principal credentials
\item[\textsc{inv-3}:] Never modify system files without explicit permission
\item[\textsc{inv-4}:] Always verify tool outputs before downstream use
\item[\textsc{inv-5}:] Never trust delegated trust $>$ direct trust
\end{enumerate}

### Drift Detection

\begin{definition}[Drift Detection]
\label{def:drift-detection}
Monitor belief distribution for anomalous changes:
\begin{equation}
\label{eq:drift-detection}
D_{\text{KL}}(\mathcal{B}_i^t \| \mathcal{B}_i^{t-w}) > \theta_{\text{drift}} \Rightarrow \textsc{alert}
\end{equation}
where $w$ is the sliding window size.
\end{definition}

## Coordination Defenses {#sec:coord-defenses}

### Byzantine-Tolerant Consensus

\begin{theorem}[Byzantine Agreement Requirement]
\label{thm:byzantine-req}
For $n$ agents with at most $f$ compromised:
\begin{equation}
\label{eq:byzantine-req}
n \geq 3f + 1
\end{equation}
\end{theorem}

\begin{definition}[Cognitive Byzantine Agreement]
\label{def:cog-byzantine}
\begin{equation}
\label{eq:cog-byzantine}
\mathcal{B}_{\text{consensus}}(\phi) = \begin{cases}
1 & \text{if } |\{i: \mathcal{B}_i(\phi) > \tau\}| > \frac{2n}{3} \\
0 & \text{if } |\{i: \mathcal{B}_i(\phi) < 1-\tau\}| > \frac{2n}{3} \\
\perp & \text{otherwise}
\end{cases}
\end{equation}
\end{definition}

### Quorum Verification

\begin{definition}[Quorum Requirement]
\label{def:quorum}
Critical actions require multi-agent approval:
\begin{equation}
\label{eq:quorum}
\text{Permit}(\text{action}) \iff |\{a_i: \text{approve}_i(\text{action})\}| \geq q
\end{equation}
where $q = \lceil \frac{n + f + 1}{2} \rceil$.
\end{definition}

### Spotcheck Pattern

\textbf{Spotcheck Protocol}:
\begin{enumerate}
\item Assign task $T$ to agent $A$
\item With probability $p_{\text{check}}$: assign same task to verifier $V$
\item Compare results $R_A, R_V$
\item If divergent: escalate to human
\item Track accuracy per agent for reputation
\end{enumerate}

## Defense Composition {#sec:defense-composition}

### Composition Algebra

\begin{definition}[Defense Composition]
\label{def:defense-composition}
Defenses compose in series ($\circ$) or parallel ($\parallel$):
\end{definition}

\textbf{Series Composition} (both must pass):
\begin{equation}
\label{eq:series-comp}
\mathcal{D}_1 \circ \mathcal{D}_2: \textsc{accept} \iff \mathcal{D}_1(m) = \textsc{accept} \land \mathcal{D}_2(m) = \textsc{accept}
\end{equation}

\textbf{Parallel Composition} (any can detect):
\begin{equation}
\label{eq:parallel-comp}
\mathcal{D}_1 \parallel \mathcal{D}_2: \textsc{detect} \iff \mathcal{D}_1(m) = \textsc{detect} \lor \mathcal{D}_2(m) = \textsc{detect}
\end{equation}

\begin{theorem}[Series Detection Rate]
\label{thm:series-detection}
For series composition:
\begin{equation}
\label{eq:series-detection}
P_{\text{detect}}(\mathcal{D}_1 \circ \mathcal{D}_2) = P_{\text{detect}}(\mathcal{D}_1) + (1 - P_{\text{detect}}(\mathcal{D}_1)) \cdot P_{\text{detect}}(\mathcal{D}_2)
\end{equation}
\end{theorem}

\begin{proof}
Attack detected by first defense, or passes first and detected by second. Events are independent by design.
\end{proof}

\begin{theorem}[Parallel Detection Rate]
\label{thm:parallel-detection}
Combined detection rate:
\begin{equation}
\label{eq:parallel-detection}
P(\text{detect}) = 1 - \prod_{d \in \mathcal{D}} (1 - P_d(\text{detect}))
\end{equation}
\end{theorem}

\begin{proof}
Attack succeeds only if it evades all defenses.
\end{proof}

\begin{theorem}[False Positive Composition]
\label{thm:fpr-composition}
For series composition:
\begin{equation}
\label{eq:fpr-series}
\text{FPR}(\mathcal{D}_1 \circ \mathcal{D}_2) = \text{FPR}(\mathcal{D}_1) + (1 - \text{FPR}(\mathcal{D}_1)) \cdot \text{FPR}(\mathcal{D}_2)
\end{equation}

For parallel composition (conservative):
\begin{equation}
\label{eq:fpr-parallel}
\text{FPR}(\mathcal{D}_1 \parallel \mathcal{D}_2) \leq \text{FPR}(\mathcal{D}_1) + \text{FPR}(\mathcal{D}_2)
\end{equation}
\end{theorem}

### Composition Rules

\begin{itemize}
\item[\textbf{C-Order}:] Apply low-latency, high-precision defenses first
\item[\textbf{C-Diverse}:] Combine defenses with orthogonal detection methods
\item[\textbf{C-Fallback}:] Ensure graceful degradation if one defense fails
\item[\textbf{C-Budget}:] Total latency bounded by:
\begin{equation}
\label{eq:latency-budget}
\sum_{d \in \mathcal{D}_{\text{series}}} L_d + \max_{d \in \mathcal{D}_{\text{parallel}}} L_d \leq L_{\max}
\end{equation}
\end{itemize}

\begin{table}[htbp]
\centering
\caption{Recommended defense stack with latency and detection rates.}
\label{tab:defense-stack}
\begin{tabular}{@{}llll@{}}
\toprule
Layer & Defense & Latency & $P_{\text{detect}}$ \\
\midrule
1 & Firewall & 10ms & 0.80 \\
2 & Sandbox & 5ms & 0.70 \\
3 & Tripwires & 1ms & 0.60 \\
4a & Drift (parallel) & 20ms & 0.65 \\
4b & Invariants (parallel) & 5ms & 0.55 \\
5 & Byzantine consensus & 100ms & 0.90 \\
\bottomrule
\end{tabular}
\end{table}

\begin{corollary}[Stack Detection Rate]
\label{cor:stack-detection}
Assuming independence, the full stack (\cref{tab:defense-stack}) achieves:
\begin{equation}
\label{eq:stack-detection}
P_{\text{detect}} = 1 - (1-0.80)(1-0.70)(1-0.60)(1-0.80) = 0.995
\end{equation}
\end{corollary}

## Cost-Benefit Analysis {#sec:cost-benefit}

\begin{definition}[Defense Cost]
\label{def:defense-cost}
Total cost of defense deployment:
\begin{equation}
\label{eq:defense-cost}
C_{\text{total}}(\mathcal{D}) = C_{\text{compute}} + C_{\text{latency}} + C_{\text{fp}} + C_{\text{maint}}
\end{equation}
\end{definition}

\begin{table}[htbp]
\centering
\caption{Cost model components.}
\label{tab:cost-components}
\begin{tabular}{@{}llp{4cm}@{}}
\toprule
Component & Formula & Unit \\
\midrule
Compute & $\sum_d c_d \cdot f_d$ & CPU-hours/day \\
Latency & $\sum_d L_d \cdot r_{\text{msg}}$ & User-seconds/day \\
False Positive & $\text{FPR} \cdot r_{\text{msg}} \cdot c_{\text{review}}$ & Analyst-hours/day \\
Maintenance & $|\mathcal{D}| \cdot c_{\text{maint}}$ & Eng-hours/month \\
\bottomrule
\end{tabular}
\end{table}

\begin{definition}[Defense Benefit]
\label{def:defense-benefit}
Expected loss prevented:
\begin{equation}
\label{eq:defense-benefit}
B_{\text{total}}(\mathcal{D}) = P_{\text{attack}} \cdot P_{\text{detect}}(\mathcal{D}) \cdot L_{\text{prevented}}
\end{equation}
\end{definition}

\begin{table}[htbp]
\centering
\caption{Cost-benefit analysis by defense mechanism.}
\label{tab:cost-benefit}
\begin{tabular}{@{}llllll@{}}
\toprule
Defense & Compute & Latency & FP Cost & Benefit & ROI \\
\midrule
Firewall & $10^3$ & 10ms & Medium & High & \textbf{4.2x} \\
Sandbox & $10^2$ & 5ms & Low & Medium & 3.1x \\
Tripwires & $10^1$ & 1ms & Low & Medium & \textbf{5.8x} \\
Drift Detection & $10^4$ & 20ms & High & High & 2.3x \\
Invariant Check & $10^2$ & 5ms & Low & High & \textbf{4.7x} \\
Byzantine & $10^5$ & 100ms & Medium & Very High & 1.8x \\
Spotcheck & $10^4$ & Variable & Low & Medium & 2.9x \\
\bottomrule
\end{tabular}
\end{table}

### Optimal Defense Portfolio

\begin{definition}[Portfolio Optimization]
\label{def:portfolio-opt}
\begin{equation}
\label{eq:portfolio-opt}
\max_{\mathcal{D} \subseteq \mathcal{D}_{\text{all}}} B_{\text{total}}(\mathcal{D}) - C_{\text{total}}(\mathcal{D})
\end{equation}
subject to: $C_{\text{compute}}(\mathcal{D}) \leq B_{\text{compute}}$, $\max_d L_d \leq L_{\max}$, $\text{FPR}(\mathcal{D}) \leq \epsilon_{\text{fp}}$.
\end{definition}

\begin{table}[htbp]
\centering
\caption{Deployment recommendations by risk profile.}
\label{tab:risk-profiles}
\begin{tabular}{@{}llll@{}}
\toprule
Risk Profile & Recommended Stack & Cost & Detection \\
\midrule
Low (internal) & Firewall + Tripwires & Low & 88\% \\
Medium (business) & + Sandbox + Invariants & Medium & 94\% \\
High (financial) & + Drift + Spotcheck & High & 97\% \\
Critical (infra) & Full + Byzantine & Very High & 99.5\% \\
\bottomrule
\end{tabular}
\end{table}

![Defense Composition Architecture: Four-way Venn diagram showing overlapping detection capabilities of CIF defense mechanisms (Cognitive Firewall, Belief Sandbox, Tripwire Monitor, Anomaly Detection). Attack types are positioned in regions indicating which defenses detect them. The center (Full CIF) represents the ensemble detection zone where all mechanisms contribute.](figures/defense_composition.pdf){#fig:defense-composition}

\Cref{fig:defense-composition} illustrates the defense composition using series ($\circ$) and parallel ($\parallel$) arrangements. Each defense mechanism targets specific attack patterns: the Cognitive Firewall handles input-layer attacks (prompt injection), the Belief Sandbox catches belief-layer attacks, Tripwire Monitors detect identity-layer exploits, and Anomaly Detection identifies behavioral drift. Overlapping regions show attacks detected by multiple mechanisms, demonstrating the defense-in-depth principle.
