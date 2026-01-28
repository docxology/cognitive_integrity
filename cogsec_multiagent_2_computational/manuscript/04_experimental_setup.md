\newpage

# Experimental Validation {#sec:results}

This section demonstrates the practical viability of CIF's formal mechanisms through empirical evaluation across production multiagent architectures. We present experimental setup (\cref{sec:exp-setup}) and key findings (\cref{sec:key-findings}). Detailed statistical analysis, ablation studies, and scalability metrics are provided in \cref{sec:extended-results}.

## Experimental Setup {#sec:exp-setup}

### Target Architectures

We evaluated CIF across six production multiagent systems representing diverse architectural patterns:

\begin{table}[htbp]
\centering
\caption{Multiagent system architectures evaluated.}
\label{tab:target-architectures}
\begin{tabular}{@{}lll@{}}
\toprule
System & Architecture & Communication \\
\midrule
Claude Code & Hierarchical ($1 + n$) & Task delegation \\
AutoGPT & Autonomous + plugins & Tool-based \\
CrewAI & Role-based (3--10) & Sequential/parallel \\
LangGraph & Graph-based & State machine \\
MetaGPT & SOP-driven (5--8) & Document passing \\
Camel & Debate ($2+$) & Adversarial \\
\bottomrule
\end{tabular}
\end{table}

### Attack Corpus

We assembled a corpus of 950 cognitive attacks across four categories: prompt injection (500), trust exploitation (200), belief manipulation (150), and coordination attacks (100). Sources include published jailbreak datasets, custom adversarial prompts, red team exercises, and synthetic generation via adversarial models.

## Key Findings {#sec:key-findings}

### Finding 1: Layered Defense Significantly Outperforms Single Mechanisms

The central empirical finding validates CIF's layered approach. No single defense mechanism achieves acceptable protection, but their composition yields substantial improvement.

![Detection Performance Comparison. Bar chart comparing detection rates across defense configurations (Baseline, Firewall-only, Sandbox-only, Tripwires-only, Full CIF) for each attack category (Prompt Injection, Trust Exploitation, Belief Manipulation, Coordination). Error bars show 95\% confidence intervals. Full CIF consistently achieves $>90\%$ detection across all categories, while individual mechanisms show significant gaps—validating the defense composition algebra (Part 1, Theorems 3.1-3.2).](figures/detection_performance.pdf){#fig:detection-performance width=95%}

\begin{table}[htbp]
\centering
\caption{Detection performance by defense configuration.}
\label{tab:detection-performance}
\begin{tabular}{@{}lll@{}}
\toprule
Defense & Detection Rate & Key Limitation \\
\midrule
Firewall only & Moderate & Misses coordination attacks \\
Sandbox only & Moderate-Low & Limited to unverified sources \\
Tripwires only & Moderate-High & Requires canary placement \\
\textbf{Full CIF} & \textbf{High} & Acceptable latency overhead \\
\bottomrule
\end{tabular}
\end{table}

The gap between firewall-only and full CIF is most pronounced for coordination and temporal attacks, which require multi-component detection. This validates the defense composition algebra (Section 4 (Defense Composition, Part 1)): defenses targeting orthogonal attack surfaces compose multiplicatively.

### Finding 2: Trust Calculus Prevents Amplification Attacks

![ROC Curves by Attack Category. Receiver Operating Characteristic curves showing the tradeoff between True Positive Rate (sensitivity) and False Positive Rate (1-specificity) for CIF detection across four attack categories. All categories achieve AUC $> 0.92$, with Prompt Injection showing the strongest discrimination (AUC = 0.97) and Coordination Attacks showing the widest confidence band due to smaller sample size.](figures/roc_curves.pdf){#fig:roc-curves width=90%}

Across all tested architectures, the bounded trust decay ($\delta^d$) successfully prevented trust laundering and amplification attempts. In adversarial scenarios where attackers attempted to relay high-impact content through multiple trusted intermediaries, the exponential decay ensured that delegated trust remained below action thresholds.

Critically, this held even when individual agents in the delegation chain were compromised---the trust bound is a \textit{structural} guarantee independent of agent behavior.

### Finding 3: Integrity Improvement Scales Across Architectures

CIF improved belief integrity scores substantially across all six architectures, with particularly strong results for systems with deeper delegation hierarchies (Camel, AutoGPT) where the trust calculus provides the greatest benefit.

The peer-to-peer architectures (Camel) showed the largest relative improvement, consistent with our analysis that equal-trust topologies are most vulnerable to lateral movement attacks (\cref{tab:architecture-insights}).

### Finding 4: Performance Overhead Is Acceptable for Security Contexts

Full CIF deployment introduces latency overhead in the 20-25\% range with memory requirements scaling with agent count. For security-critical deployments, this overhead is acceptable given the integrity improvement achieved.

The overhead is dominated by the cognitive firewall (input classification) and Byzantine consensus (coordination). For environments where consensus is unnecessary, lighter configurations achieve comparable detection with lower overhead (Table 3 (Risk-Based Configuration, Part 1)).

### Finding 5: Attack-Type Specific Vulnerabilities Remain

Despite strong overall performance, specific attack types remain challenging:

\begin{itemize}
\item \textbf{Semantic equivalent attacks}: Rephrased injections that preserve meaning evade pattern-matching
\item \textbf{Progressive drift}: Sub-threshold changes accumulate below detection windows
\item \textbf{Orchestrator compromise}: Outside our threat model (our honest orchestrator assumption (Part 1, Section 2))
\end{itemize}

These gaps define the frontier for future defense research.

## Interpretation

The empirical results validate that CIF's formal mechanisms translate to practical protection. The key insight is not the specific detection rates achieved---which reflect current attack sophistication and will degrade as adversaries adapt---but rather the \textit{structural} properties:

\begin{enumerate}
\item Trust cannot be amplified through delegation (Part 1, Theorem 2)
\item Defenses compose predictably (Part 1, Theorems 3.1 and 3.2)
\item Information-theoretic bounds constrain the stealth-impact tradeoff (Part 1, Theorem 4)
\end{enumerate}

These properties hold independent of specific detection thresholds and provide the foundation for long-term security assurance.

For detailed statistical analysis including significance testing, confidence intervals, ablation studies, and scalability benchmarks, see the Extended Results (\cref{sec:extended-results}).
