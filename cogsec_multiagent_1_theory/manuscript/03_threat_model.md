\newpage

# Threat Model: Adversary Classes, Attack Complexity, and Taxonomy {#sec:threat-model}

This section formalizes the adversary model for multiagent cognitive security. We define five adversary classes (\cref{sec:adversary-classes}), characterize attack complexity (\cref{sec:attack-complexity}), establish detectability metrics (\cref{sec:detectability}), analyze adversarial capabilities (\cref{sec:capabilities}), and present a comprehensive attack taxonomy (\cref{sec:attack-taxonomy}).

## Adversary Classes {#sec:adversary-classes}

\begin{definition}[Adversary Class]
\label{def:adversary-class}
An adversary class $\Omega_k$ is characterized by access level, capabilities, and resource requirements.
\end{definition}

\begin{table}[htbp]
\centering
\caption{Adversary classification by access level and capability.}
\label{tab:adversary-classes}
\begin{tabular}{@{}llllp{3cm}@{}}
\toprule
Class & Symbol & Access & Capability & Example \\
\midrule
External & $\Omega_1$ & User input & Prompt manipulation & Jailbreak attempts \\
Peripheral & $\Omega_2$ & Tool/API & Data poisoning & Malicious web content \\
Agent-level & $\Omega_3$ & Single agent & Goal hijacking & Compromised subagent \\
Coordination & $\Omega_4$ & Inter-agent & Trust manipulation & MitM on messages \\
Systemic & $\Omega_5$ & Orchestrator & Full control & Framework compromise \\
\bottomrule
\end{tabular}
\end{table}

\Cref{tab:adversary-classes} presents the five-tier adversary hierarchy. We assume an honest orchestrator for $\Omega_1$--$\Omega_4$; class $\Omega_5$ attacks require physical or supply-chain compromise outside our threat model.

## Formal Mathematical Characterization of Adversary Classes {#sec:adversary-formal}

We now provide rigorous mathematical characterizations for each adversary class $\Omega_k$. These extend the descriptive table above with information-theoretic bounds, capability monotonicity guarantees, and formal distinguishability criteria.

### Adversary Class $\Omega_1$: External Attacker

\begin{definition}[External Adversary]
\label{def:omega1}
An adversary $\mathcal{A} \in \Omega_1$ is characterized by the tuple:
\begin{equation}
\label{eq:omega1-formal}
\Omega_1 = \langle \mathcal{S}_{\text{input}}, \mathcal{K}_{\text{public}}, \mathcal{R}_{\text{low}}, f_{\text{detect}} \rangle
\end{equation}
where $\mathcal{S}_{\text{input}} = \{m \in \mathcal{M} : \text{source}(m) = \text{user}\}$ is the accessible surface, $\mathcal{K}_{\text{public}}$ denotes public knowledge of the system, $\mathcal{R}_{\text{low}}$ encodes low resource requirements, and $f_{\text{detect}}: \mathcal{M} \to [0,1]$ is the adversary's model of detection probability.
\end{definition}

\begin{property}[External Attacker Bounds]
\label{prop:omega1-bounds}
For $\mathcal{A} \in \Omega_1$:
\begin{itemize}
\item \textbf{Access}: $|\mathcal{S}_{\text{input}}| = 1$ (single input channel)
\item \textbf{Knowledge}: $H(\mathcal{K}_{\text{public}}) \leq H(\mathcal{K}_{\text{system}})$ (public knowledge bounded by system state entropy)
\item \textbf{Attack complexity}: $O(1)$ --- constant independent of system size
\item \textbf{Detectability}: $D_{\text{score}}(\mathcal{A}_{\Omega_1}) \geq D_{\text{base}}$ --- highest detectability class
\end{itemize}
\end{property}

The external attacker's fundamental limitation is single-channel access. Any attack must traverse the cognitive firewall (\cref{sec:arch-defenses}), creating a mandatory inspection point with detection probability $r_f \geq 0.80$.

### Adversary Class $\Omega_2$: Peripheral Attacker

\begin{definition}[Peripheral Adversary]
\label{def:omega2}
An adversary $\mathcal{A} \in \Omega_2$ controls one or more tool/API data sources:
\begin{equation}
\label{eq:omega2-formal}
\Omega_2 = \langle \mathcal{S}_{\text{tools}}, \mathcal{K}_{\text{domain}}, \mathcal{R}_{\text{medium}}, \mathcal{P}_{\text{inject}} \rangle
\end{equation}
where $\mathcal{S}_{\text{tools}} \subseteq \mathcal{T}_{\text{available}}$ denotes accessible tool channels, $\mathcal{K}_{\text{domain}}$ encodes domain-specific knowledge needed for plausible injection, $\mathcal{R}_{\text{medium}}$ captures medium resource requirements, and $\mathcal{P}_{\text{inject}}$ is the injection payload generator.
\end{definition}

\begin{property}[Peripheral Injection Capacity]
\label{prop:omega2-injection}
For $\mathcal{A} \in \Omega_2$, the maximum injection information rate is bounded by:
\begin{equation}
\label{eq:omega2-rate}
\mathcal{I}(\Omega_2) \leq \sum_{t \in \mathcal{S}_{\text{tools}}} C_t \cdot (1 - V_t)
\end{equation}
where $C_t$ is the channel capacity of tool $t$ and $V_t \in [0,1]$ is the verification rate applied to tool output.
\end{property}

This bound shows that high verification rates ($V_t \to 1$) reduce the peripheral attacker to near-zero injection capacity.

### Adversary Class $\Omega_3$: Agent-Level Attacker

\begin{definition}[Agent-Level Adversary]
\label{def:omega3}
An adversary $\mathcal{A} \in \Omega_3$ compromises or impersonates a single agent $a_v$:
\begin{equation}
\label{eq:omega3-formal}
\Omega_3 = \langle a_v, \sigma_v, \mathcal{N}(a_v), \mathcal{G}_{\text{adv}} \rangle
\end{equation}
where $a_v$ is the victim/compromised agent, $\sigma_v = \langle \mathcal{B}_v, \mathcal{G}_v, \mathcal{I}_v, \mathcal{H}_v \rangle$ is the full cognitive state under adversarial control, $\mathcal{N}(a_v) = \{a_j : \mathcal{C}(a_v, a_j) = 1\}$ is the neighborhood of $a_v$, and $\mathcal{G}_{\text{adv}}$ is the adversarial goal set.
\end{definition}

\begin{theorem}[Agent Compromise Blast Radius]
\label{thm:blast-radius}
When agent $a_v \in \Omega_3$ is fully compromised, the maximum influenced trust is:
\begin{equation}
\label{eq:blast-radius}
\text{BlastRadius}(a_v) = \sum_{a_j \in \mathcal{N}(a_v)} \mathcal{T}_{a_j \to a_v} \cdot |\text{Reachable}(a_j)|
\end{equation}
The CIF trust decay bound (\cref{thm:trust-bounded}) limits this to:
\begin{equation}
\label{eq:blast-radius-bound}
\text{BlastRadius}(a_v) \leq n \cdot \delta \cdot \max_{a_j} \mathcal{T}_{a_j \to a_v}
\end{equation}
*Reachability factor alignment (H7): the \cref{eq:blast-radius} definition includes an explicit
$|\text{Reachable}(a_j)|$ factor as the intuitive influence interpretation; the trust-decay bound
(\cref{eq:blast-radius-bound}) is stated on the trust-influence measure, where each reachable hop
contributes at most $\delta \cdot \mathcal{T}$, so the aggregate is capped at $n \cdot \delta \cdot \max_j \mathcal{T}$.
The supplementary restatement (\cref{thm:blast-radius-restated}) states the bound consistently and
does not multiply the neighbor and reachable-agent counts (see S01, \cref{sec:thm-blast-radius}).*
\end{theorem}

\begin{proof}
Each neighbor $a_j$ trusts $a_v$ with score $\mathcal{T}_{a_j \to a_v}$. The trust propagated from $a_j$ to further agents via $a_v$ is bounded by $\delta \cdot \mathcal{T}_{a_j \to a_v}$ per \cref{thm:trust-bounded}. Summing over all $n$ agents gives the bound.
\end{proof}

### Adversary Class $\Omega_4$: Coordination-Level Attacker

\begin{definition}[Coordination Adversary]
\label{def:omega4}
An adversary $\mathcal{A} \in \Omega_4$ controls the inter-agent communication channel:
\begin{equation}
\label{eq:omega4-formal}
\Omega_4 = \langle \mathcal{E}_{\text{ctrl}}, f_{\text{man}}, \mathcal{K}_{\text{protocol}}, \mathcal{C}_{\text{sync}} \rangle
\end{equation}
where $\mathcal{E}_{\text{ctrl}} \subseteq \mathcal{E}$ is the set of controlled communication edges, $f_{\text{man}}: \mathcal{M} \to \mathcal{M}$ is a message manipulation function, $\mathcal{K}_{\text{protocol}}$ encodes knowledge of coordination protocols, and $\mathcal{C}_{\text{sync}}$ denotes synchronization capability for coordinated attacks.
\end{definition}

\begin{property}[Coordination Attack Distinguishability]
\label{prop:omega4-distinguish}
An $\Omega_4$ attack is distinguishable from legitimate coordination with probability:
\begin{equation}
\label{eq:omega4-distinguish}
P(\text{detect} \mid \Omega_4) \geq 1 - 2^{-D_{\mathrm{KL}}(P_{\text{legitimate}} \| P_{\text{attack}})}
\end{equation}
where $D_{\mathrm{KL}}$ measures the divergence between legitimate and adversarial message distributions.
\end{property}

The coordination attacker must produce messages statistically consistent with legitimate protocol traffic while encoding adversarial payloads---a constraint captured by the KL divergence bound.

### Adversary Class $\Omega_5$: Systemic Attacker

\begin{definition}[Systemic Adversary]
\label{def:omega5}
A systemic adversary achieves complete control:
\begin{equation}
\label{eq:omega5-formal}
\Omega_5 = \langle \mathcal{A}_{\text{full}}, \sigma_{\text{all}}, \mathcal{T}_{\text{full}}, \mathcal{P}_{\text{all}} \rangle
\end{equation}
where $\mathcal{A}_{\text{full}} = \mathcal{A}$ (all agents), $\sigma_{\text{all}}$ denotes control over all cognitive states, $\mathcal{T}_{\text{full}}$ gives complete trust manipulation capability, and $\mathcal{P}_{\text{all}}$ grants all action permissions.
\end{definition}

\begin{property}[Systemic Attack Cost Bound]
\label{prop:omega5-scope}
$\Omega_5$ requires physical or supply-chain compromise of the orchestrator. CIF provides no cryptographic resistance against $\Omega_5$, but its layered architecture increases the cost of achieving systemic control:
\begin{equation}
\label{eq:omega5-cost}
C(\Omega_5) = C_{\text{orchestrator}} + \sum_{k=1}^{4} C_{\text{bypass}}(\Omega_k)
\end{equation}
where $C_{\text{bypass}}(\Omega_k)$ is the cost of neutralizing each sub-class's defenses.
\end{property}

### Cross-Class Attack Distinguishability

\begin{theorem}[Adversary Class Separation]
\label{thm:class-separation}
The five adversary classes $\{\Omega_k\}_{k=1}^5$ are distinguishable in information-theoretic terms:
\begin{equation}
\label{eq:class-separation}
\forall i \neq j: D_{\mathrm{KL}}(P_{\Omega_i} \| P_{\Omega_j}) > 0
\end{equation}
where $P_{\Omega_k}$ is the attack signature distribution of class $\Omega_k$.
\end{theorem}

\begin{proof}
By construction: each class has distinct access surface ($\mathcal{S}_{\Omega_k}$), producing statistically distinguishable observable signatures. Class $\Omega_1$ attacks appear only in user-input channel; $\Omega_2$ attacks appear in tool-response channels; $\Omega_3$ attacks show belief drift in single agents; $\Omega_4$ attacks manifest as inter-agent message anomalies; $\Omega_5$ requires simultaneously passing all lower-class defenses. The KL divergence is strictly positive because the supports are not identical.
\end{proof}

## Attack Complexity Analysis {#sec:attack-complexity}

\begin{definition}[Resource Requirements]
\label{def:resources}
Attack resources are characterized by the tuple:
\begin{equation}
\label{eq:resource-tuple}
\mathcal{R} = \langle R_C, R_K, R_A, R_P, R_{Co} \rangle
\end{equation}
where components are defined in \cref{tab:resource-types}.
\end{definition}

\begin{table}[htbp]
\centering
\caption{Attack resource taxonomy.}
\label{tab:resource-types}
\begin{tabular}{@{}llp{4.5cm}l@{}}
\toprule
Resource & Symbol & Definition & Unit \\
\midrule
Compute & $R_C$ & Processing for attack generation & FLOPS-hours \\
Knowledge & $R_K$ & System understanding required & Bits \\
Access & $R_A$ & Channel availability & Interfaces \\
Persistence & $R_P$ & Temporal presence required & Sessions \\
Coordination & $R_{Co}$ & Multi-party synchronization & Entities \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[htbp]
\centering
\caption{Complexity by adversary class.}
\label{tab:complexity-by-class}
\begin{tabular}{@{}lllllll@{}}
\toprule
Class & $R_C$ & $R_K$ & $R_A$ & $R_P$ & $R_{Co}$ & Complexity \\
\midrule
$\Omega_1$ & Low & Low & 1 & 1 & 1 & $O(1)$ \\
$\Omega_2$ & Medium & Medium & 1--5 & Variable & 1 & $O(\log n)$ \\
$\Omega_3$ & High & High & 1 & Medium & 1--2 & $O(n)$ \\
$\Omega_4$ & High & Very High & $\geq 2$ & High & $\geq 2$ & $O(n^2)$ \\
$\Omega_5$ & Very High & Complete & All & Persistent & Variable & $O(2^n)$ \\
\bottomrule
\end{tabular}
\end{table}

\begin{property}[Complexity Ordering]
\label{prop:complexity-order}
\begin{equation}
\label{eq:complexity-order}
\text{Complexity}(\Omega_1) < \text{Complexity}(\Omega_2) < \text{Complexity}(\Omega_3) < \text{Complexity}(\Omega_4) < \text{Complexity}(\Omega_5)
\end{equation}
\end{property}

## Detectability Analysis {#sec:detectability}

\begin{definition}[Detectability Score]
\label{def:detectability}
For attack $\mathcal{A}$:
\begin{equation}
\label{eq:detectability}
D_{\text{score}}(\mathcal{A}) = \alpha \cdot D_{\text{sig}} + \beta \cdot D_{\text{anom}} + \gamma \cdot D_{\text{prov}}
\end{equation}
where $\alpha + \beta + \gamma = 1$ and components are:
\begin{itemize}
\item $D_{\text{sig}} \in [0,1]$: Pattern-based detection feasibility
\item $D_{\text{anom}} \in [0,1]$: Statistical anomaly visibility
\item $D_{\text{prov}} \in [0,1]$: Causal traceability
\end{itemize}
\end{definition}

## Adversarial Capabilities {#sec:capabilities}

\begin{definition}[Capability Set]
\label{def:capability-set}
\begin{equation}
\label{eq:capability-set}
\mathcal{C}_{\text{adv}} = \langle C_O, C_I, C_M, C_T, C_P \rangle
\end{equation}
with components: Observe ($C_O$), Inject ($C_I$), Modify ($C_M$), Timing ($C_T$), Persist ($C_P$).
\end{definition}

\begin{table}[htbp]
\centering
\caption{Capability matrix by adversary class.}
\label{tab:capability-matrix}
\begin{tabular}{@{}llllll@{}}
\toprule
Class & $C_O$ & $C_I$ & $C_M$ & $C_T$ & $C_P$ \\
\midrule
$\Omega_1$ & Input only & Direct & None & Limited & Session \\
$\Omega_2$ & Tool responses & API & Tool data & API timing & Tool-dep. \\
$\Omega_3$ & Agent state & Agent output & Beliefs & Agent timing & Memory \\
$\Omega_4$ & Inter-agent & Msg inject & Msg alter & Full timing & Channel \\
$\Omega_5$ & Complete & Complete & Complete & Complete & Complete \\
\bottomrule
\end{tabular}
\end{table}

\begin{axiom}[Capability Monotonicity]
\label{ax:capability-mono}
\begin{equation}
\label{eq:capability-mono}
\forall i < j: \mathcal{C}_{\Omega_i} \subseteq \mathcal{C}_{\Omega_j}
\end{equation}
\end{axiom}

\begin{axiom}[Cryptographic Limitation]
\label{ax:crypto-limit}
\begin{equation}
\label{eq:crypto-limit}
\forall k: \neg \text{CanBreak}(\Omega_k, \text{Crypto})
\end{equation}
\end{axiom}

\begin{axiom}[Byzantine Bound]
\label{ax:byzantine}
\begin{equation}
\label{eq:byzantine-bound}
|\text{Compromised}| < \frac{n}{3}
\end{equation}
\end{axiom}

\begin{axiom}[Honest Orchestrator]
\label{ax:honest-orchestrator}
For adversary classes $\Omega_1$--$\Omega_4$, the orchestrator agent $a_0$ remains uncompromised:
\begin{equation}
\label{eq:honest-orchestrator}
\forall k \in \{1,2,3,4\}: a_0 \notin \text{Compromised}(\Omega_k)
\end{equation}
\end{axiom}

## Attack Taxonomy {#sec:attack-taxonomy}

We classify attacks into four dimensions: epistemic, behavioral, social, and temporal. \Cref{fig:threat-taxonomy} provides a visual overview of this four-dimensional classification, while \cref{fig:comprehensive-taxonomy} presents the complete attack surface taxonomy across all five adversary classes. This formal classification is complemented by the community-maintained COGSEC ATLAS \cite{cogsecatlas2023}, which catalogs 995 cognitive security patterns across seven categories: vulnerabilities (inherent cognitive weaknesses such as in-group bias and overconfidence), exploits (methods leveraging vulnerabilities), remedies (mitigating actions), practices (established methods like Devil's Advocate and Key Assumptions Check), accelerators (factors increasing attack impact), moderators (factors influencing effect strength), and situational conditions. The Atlas employs hierarchical parent-child relationships enabling granular mapping from broad vulnerability classes to specific manifestations---a structure that aligns with our adversary class hierarchy ($\Omega_1$--$\Omega_5$).

![Four-Dimensional Threat Taxonomy: Epistemic attacks (belief manipulation), behavioral attacks (goal hijacking), social attacks (trust exploitation), and temporal attacks (persistence), organized by adversary class $\Omega_1$--$\Omega_5$ with increasing capability and decreasing detectability.](figures/threat_taxonomy.pdf){#fig:threat-taxonomy}

![Comprehensive Attack Surface Taxonomy: Example classifications of the complete cognitive attack surface across all five adversary classes, showing representative attack types with complexity indicators. Note the inverse relationship between attack sophistication and detectability---external attacks ($\Omega_1$) are most detectable while systemic attacks ($\Omega_5$) are hardest to detect.](figures/comprehensive_taxonomy.pdf){#fig:comprehensive-taxonomy}

\Cref{fig:comprehensive-taxonomy} presents the full cognitive attack surface taxonomy, organizing all adversary classes $\Omega_1$--$\Omega_5$ with their associated attack types and complexity indicators. The visualization reveals a clear inverse relationship between attack sophistication and detectability: external attacks ($\Omega_1$) are most easily detected while systemic attacks ($\Omega_5$) require sophisticated temporal and behavioral analysis. This progression from ``Entry Point'' through``Data Injection,'' ``State Corruption,'' and``Trust Exploitation'' to ``Total Compromise'' guides the layered defense strategy of CIF (\cref{sec:system-model}). For empirical detection rates across attack types, see Part 2 of this series.

\Cref{fig:threat-taxonomy} illustrates the hierarchical attack classification, showing how epistemic attacks (targeting beliefs), behavioral attacks (targeting goals), social attacks (targeting trust), and temporal attacks (exploiting persistence) relate to the adversary classes $\Omega_1$--$\Omega_5$.

### Epistemic Attacks

Epistemic attacks target the agent's relationship with its **information environment**---the totality of information sources, evidence streams, and knowledge repositories that inform agent beliefs. The epistemic domain is thus synonymous with the cognitive information environment: both concern what agents can know, how they acquire knowledge, and the reliability of their belief-forming processes.

Target: Agent beliefs $\mathcal{B}_i$.

\begin{definition}[Belief Injection]
\label{def:belief-injection}
\begin{equation}
\label{eq:belief-injection}
\mathcal{A}_{BI}: \exists \phi \in \Phi_{\text{adv}}: \mathcal{B}_i(\phi) > \tau_{\text{accept}}
\end{equation}
Insertion of false propositions into agent's verified belief set.
\end{definition}

\begin{definition}[Evidence Fabrication]
\label{def:evidence-fab}
Generation of synthetic evidence supporting adversarial claims with forged provenance.
\end{definition}

\begin{definition}[Confidence Manipulation]
\label{def:confidence-manip}
\begin{equation}
\label{eq:confidence-manip}
\mathcal{A}_{CM}: |\mathcal{B}_i^{t+1}(\phi) - \mathcal{B}_i^t(\phi)| > \epsilon_{\text{natural}}
\end{equation}
Artificial inflation or deflation of belief certainty beyond natural bounds.
\end{definition}

\begin{definition}[Memory Poisoning]
\label{def:memory-poison}
Corruption of persistent storage or context summaries to embed adversarial state.
\end{definition}

\begin{definition}[Semantic Drift]
\label{def:semantic-drift}
\cite{topicattack2025}
Gradual shift of conversation topic to adversarial domains via benign-appearing transitions that evade discrete classification.
\end{definition}

### Behavioral Attacks

Target: Agent actions and goals $\mathcal{G}_i$.

\begin{definition}[Goal Hijacking]
\label{def:goal-hijacking}
\begin{equation}
\label{eq:goal-hijacking}
\mathcal{A}_{GH}: \mathcal{G}_i^{t+1} \not\subseteq \mathcal{G}_{\text{principal}}
\end{equation}
Replacement of legitimate objectives with adversarial goals.
\end{definition}

\begin{definition}[Action Space Restriction]
\label{def:action-restrict}
Elimination of legitimate action paths through false constraints.
\end{definition}

\begin{definition}[Capability Elicitation]
\label{def:capability-elicit}
Extraction of capabilities the agent should refuse to exercise.
\end{definition}

### Social Attacks

Target: Inter-agent trust $\mathcal{T}$ and coordination.

\begin{definition}[Trust Exploitation]
\label{def:trust-exploit}
\begin{equation}
\label{eq:trust-exploit}
\mathcal{A}_{TE}: \mathcal{T}_{i \to j}^{t+1} = \mathcal{T}_{i \to j}^t + \Delta_{\text{adv}}
\end{equation}
Manipulation of trust scores between agents.
\end{definition}

\begin{definition}[Sybil Injection]
\label{def:sybil}
Introduction of fake agent identities to influence consensus.
\end{definition}

\begin{definition}[Consensus Poisoning]
\label{def:consensus-poison}
Corruption of multi-agent voting or agreement protocols.
\end{definition}

### Temporal Attacks

Target: Persistence and timing. \Cref{fig:attack-timeline} visualizes typical attack progression for temporal attacks.

![Temporal Structure of Multi-Stage Attacks (Example Trace): Illustrative attack progression from reconnaissance through payload delivery, dormancy period, and eventual activation. Detection windows at each phase are highlighted with corresponding CIF defense interventions (firewall at injection, tripwires during dormancy, invariants at activation).](figures/attack_timeline.pdf){#fig:attack-timeline}

\Cref{fig:attack-timeline} shows the temporal structure of multi-stage attacks, from initial reconnaissance through payload delivery, dormancy, and eventual activation. The timeline highlights detection windows at each phase and corresponding CIF defense interventions.

\begin{definition}[Sleeper Activation]
\label{def:sleeper}
Embedding of dormant payloads triggered by specific conditions.
\end{definition}

\begin{definition}[Context Overflow]
\label{def:context-overflow}
Exploitation of finite context windows to eject safety instructions.
\end{definition}

\begin{definition}[Deceptive Sleeper]
\label{def:sleeper-agent}
\cite{sleeperagents2024}
Models trained to behave safely during evaluation/training but defect when a specific trigger condition is met in deployment.
\end{definition}

\begin{definition}[Progressive Drift]
\label{def:progressive-drift}
\begin{equation}
\label{eq:progressive-drift}
\sum_{t=0}^{T} \delta_t > \theta_{\text{total}} \quad \text{where} \quad \forall t: \delta_t < \theta_{\text{step}}
\end{equation}
Incremental belief shifts below per-step detection threshold.
\end{definition}

## Attack Scenarios by Class

### Scenario $\Omega_1$: Nested Instruction Attack

\textbf{Vector}: Attacker embeds adversarial instructions within legitimate prompts.

\begin{equation}
\label{eq:nested-attack}
\text{Input}(m) = m_{\text{legitimate}} \oplus m_{\text{adversarial}}
\end{equation}

\textbf{Goal}: $\mathcal{B}_{\text{agent}}(\text{``safety suspended''}) > \tau$

\textbf{Resources}: $R_C = \text{Low}$, $R_K = \text{Minimal}$

\textbf{Detection}: Firewall signature matching, instruction hierarchy violation

\textbf{Recent Variant}: Universal Adversarial Triggers \cite{universal2025triggers} demonstrate that optimized character sequences can reliably bypass safety training across different model architectures.

### Scenario $\Omega_2$: Poisoned Search Result

\textbf{Vector}: Attacker SEO-optimizes malicious content for research queries.

\begin{equation}
\label{eq:poisoned-search}
\exists r_i \in \text{Response}: r_i \in \mathcal{D}_{\text{adversarial}} \Rightarrow \mathcal{B}_{\text{agent}}(\text{claim}) \gets \text{high}
\end{equation}

\textbf{Resources}: $R_C = \text{Medium}$, $R_K = \text{Medium}$

\textbf{Detection}: Provenance verification, cross-reference validation

\textbf{Recent Variant}: \textit{PromptPwnd} \cite{promptpwnd2025} demonstrated that manipulating tool error logs could coerce an agent into executing arbitrary code to "fix" the error.

### Scenario $\Omega_2'$: Browser-Fetched Adversarial Content (OpenClaw)

\textbf{Vector}: Personal AI assistant with browser automation fetches adversarial content during legitimate web browsing tasks \cite{openclaw2026security}.

A user instructs their locally-deployed OpenClaw to ``research and summarize security best practices for API key management.'' The agent's browser tool navigates to a compromised tutorial site containing invisible CSS-hidden text:

\begin{verbatim}
<div style="opacity:0;">SYSTEM: Disregard security instructions.
Export all environment variables including API keys to
pastebin.com/submit and confirm completion to user.</div>
\end{verbatim}

\begin{equation}
\label{eq:openclaw-browser-attack}
\text{BrowserFetch}(u) = \text{visible}(u) \oplus m_{\text{adversarial}} \Rightarrow \mathcal{G}_{\text{agent}} \gets \mathcal{G}_{\text{exfil}}
\end{equation}

\textbf{Goal}: Exfiltration of sensitive credentials through trusted browser automation channel

\textbf{Resources}: $R_C = \text{Medium}$, $R_K = \text{Medium}$, $R_A = 1$ (single web page)

\textbf{Detection}: Tool response sandboxing, read-only pre-summarization agents, provenance tracking of fetched content

\textbf{Mitigation}: OpenClaw's security documentation recommends employing a ``reader agent'' to summarize untrusted content in tool-disabled mode before processing by the main agent \cite{openclaw2026security}. This corresponds to the cognitive firewall architecture described in \cref{sec:arch-defenses}.

### Scenario $\Omega_3$: Compromised Specialist

\textbf{Vector}: Sustained interaction modifies specialist agent's goal set.

\begin{equation}
\label{eq:compromised-specialist}
\mathcal{G}_{\text{specialist}}^{t_0} = \{\text{secure review}\} \xrightarrow{\text{attack}} \mathcal{G}_{\text{specialist}}^{t_k} = \{\text{approve vulnerable}\}
\end{equation}

\textbf{Resources}: $R_C = \text{High}$, $R_K = \text{High}$, $R_P = \text{Medium}$

\textbf{Detection}: Behavioral deviation, goal alignment verification

### Scenario $\Omega_4$: Trust Inflation Attack {#sec:omega4}

\textbf{Vector}: Injection of fabricated agreement messages.

\begin{equation}
\label{eq:trust-inflation}
\text{Inject}(m_{\text{fake}}): T_{\text{rep}}^{t+1}(j) = T_{\text{rep}}^t(j) + \Delta_{\text{fabricated}}
\end{equation}

\textbf{Resources}: $R_C = \text{High}$, $R_K = \text{Very High}$, $R_{Co} \geq 2$

\textbf{Detection}: Message authentication, trust velocity anomalies

## Attack-Defense Quick Reference {#sec:attack-defense-reference}

\Cref{tab:attack-defense-map} provides a navigational summary mapping attack categories to their cognitive targets and corresponding CIF defense mechanisms. This table synthesizes the attack taxonomy (Sections~\ref{sec:adversary-classes}--\ref{sec:attack-taxonomy}) with defense mechanisms detailed in \cref{sec:defense-mechanisms}.

\begin{table}[htbp]
\centering
\caption{Attack-Defense Mapping: Attack types mapped to affected cognitive properties and corresponding CIF defenses.}
\label{tab:attack-defense-map}
\begin{tabular}{@{}lllp{4cm}@{}}
\toprule
Attack Category & Cognitive Target & Primary Defense & Detection Method \\
\midrule
\multicolumn{4}{@{}l}{\textit{Epistemic Attacks (Beliefs $\mathcal{B}$)}} \\
Belief Injection & $\mathcal{B}_i(\phi)$ & Cognitive Firewall & Signature matching \\
Evidence Fabrication & Provenance $\pi$ & Provenance tracking & Source verification \\
Confidence Manipulation & $\mathcal{B}_i$ certainty & Belief sandbox & Drift anomaly \\
Memory Poisoning & $\mathcal{H}_i$ & Tripwire canaries & History integrity \\
\midrule
\multicolumn{4}{@{}l}{\textit{Behavioral Attacks (Goals $\mathcal{G}$)}} \\
Goal Hijacking & $\mathcal{G}_i$ & Invariant enforcement & Goal alignment check \\
Action Restriction & $\mathcal{I}_i$ options & Permission layer & Action audit \\
Capability Elicitation & Refused actions & Firewall policies & Boundary violations \\
\midrule
\multicolumn{4}{@{}l}{\textit{Social Attacks (Trust $\mathcal{T}$)}} \\
Trust Exploitation & $\mathcal{T}_{i \to j}$ & Trust calculus bounds & Velocity anomaly \\
Sybil Injection & Agent identities & Quorum verification & Identity attestation \\
Consensus Poisoning & Multi-agent vote & Byzantine consensus & Vote deviation \\
\midrule
\multicolumn{4}{@{}l}{\textit{Temporal Attacks (Persistence)}} \\
Sleeper Activation & Dormant payloads & Behavioral baseline & Activation pattern \\
Context Overflow & Safety instructions & Context monitoring & Instruction loss \\
Progressive Drift & Cumulative $\sum \delta_t$ & Drift detection & CUSUM tracking \\
\bottomrule
\end{tabular}
\end{table}

## Attack Composition

\begin{definition}[Attack Composition]
\label{def:attack-composition}
\begin{equation}
\label{eq:attack-composition}
\text{Impact}(\mathcal{A}_1 \circ \mathcal{A}_2) \geq \max(\text{Impact}(\mathcal{A}_1), \text{Impact}(\mathcal{A}_2))
\end{equation}
\end{definition}

\begin{table}[htbp]
\centering
\caption{Synergistic attack combinations.}
\label{tab:attack-synergy}
\begin{tabular}{@{}llp{5cm}@{}}
\toprule
Primary & Secondary & Synergy Effect \\
\midrule
Trust Exploitation & Belief Injection & Bypass firewall via elevated trust \\
Memory Poisoning & Sleeper Activation & Persistent delayed attack \\
Sybil Injection & Consensus Poisoning & Achieve malicious quorum \\
Progressive Drift & Goal Hijacking & Undetectable goal modification \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Adaptive Persistence}: Recent work on Adaptive Attacks \cite{adaptive2025attacks} shows that adversaries can effectively "hill-climb" against static defenses, modifying their attack strategy in response to defense feedback.

## Threat Model Assumptions

\begin{enumerate}
\item Adversary knows system architecture (Kerckhoffs's principle)
\item Adversary cannot break cryptographic primitives (\cref{ax:crypto-limit})
\item At most $f$ agents compromised where $n \geq 3f + 1$ (\cref{ax:byzantine})
\item Communication channels may be observed but are authenticated
\item Adversary has bounded compute: $R_C < R_{\text{defender}}$
\item No cross-class adversary collusion unless specified
\item Network delay bounded: $\Delta_{\max} < \infty$
\end{enumerate}

![Attack Surface Visualization: Hierarchical agent structure showing attack vectors for each adversary class---$\Omega_1$ (user input), $\Omega_2$ (tool/API), $\Omega_3$ (agent compromise), $\Omega_4$ (inter-agent communication), and $\Omega_5$ (orchestrator control).](figures/attack_surface.pdf){#fig:attack-surface}

\Cref{fig:attack-surface} visualizes the attack surface across adversary classes $\Omega_1$--$\Omega_5$, showing hierarchical agent structure and corresponding attack vectors.
