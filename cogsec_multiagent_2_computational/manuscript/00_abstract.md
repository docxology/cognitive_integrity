\vspace*{2cm}

\begin{center}
\begin{minipage}{0.7\textwidth}
\centering
\Large\itshape
``The difference between theory and practice\\[0.3em]
is larger in practice than in theory.''
\vspace{1em}

\normalsize\upshape
--- Attributed to Jan L.\ A.\ van de Snepscheut
\end{minipage}
\end{center}

\vspace{2cm}

# Abstract

The Cognitive Integrity Framework (CIF) introduced in Part 1 of this series establishes formal foundations for securing multiagent AI systems against cognitive manipulation attacks—adversarial inputs that exploit inter-agent communication to corrupt beliefs, inflate trust, or subvert coordination. Theoretical guarantees alone cannot ensure practical protection. This companion paper bridges the theory-practice gap through comprehensive computational validation: we implement the complete CIF defense suite (cognitive firewalls, belief sandboxes, identity tripwires, trust calculus with bounded delegation, and Byzantine-tolerant consensus) and evaluate detection performance. Our evaluation employs a dual-mode strategy: (1) a large-scale parametric simulation ($N=3{,}800$) across four production multiagent architectures (Claude Code, AutoGPT, CrewAI, and LangGraph) using a 950-attack corpus to characterize design-level properties; and (2) a preliminary confirmatory empirical validation ($N=160$) using real LLM agents (Gemma 3 4B) processing representative attacks (10 per category) to verify implementation fidelity and provide open source code at \url{<https://github.com/docxology/cognitive_integrity}>. All experiments are deterministically reproducible (seed = 42).

The layered CIF defense achieves 94\% overall detection (95\% CI: [0.92, 0.96]) across all four architectures, confirming the multiplicative composition theorems from Part 1. No single mechanism suffices: the firewall alone reaches 74\%, while full composition yields compounding gains. Trust decay with bounded delegation ($\delta^d$) prevents trust amplification across all architectures, and peer-to-peer topologies show the largest relative improvement, consistent with Part 1's lateral movement analysis. Performance overhead of 20--25\% latency was observed in simulation, a trade-off comparable to standard encryption for security-critical contexts. All primary hypotheses achieve $p < 0.001$ with large effect sizes (Cohen's $d > 0.8$), and ablation studies confirm non-redundant component contributions. This is Part 2 of the Cognitive Security for Multiagent Operators series (Part 1, DOI: 10.5281/zenodo.18364119; Part 3, DOI: 10.5281/zenodo.18364130). Code and attack corpus generators are available at DOI: 10.5281/zenodo.18364128.
