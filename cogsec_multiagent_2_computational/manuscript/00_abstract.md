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

The Cognitive Integrity Framework (CIF) introduced in Part 1 of this series establishes formal foundations for securing multiagent AI systems against cognitive manipulation attacks—adversarial inputs that exploit inter-agent communication to corrupt beliefs, inflate trust, or subvert coordination. Theoretical guarantees alone cannot ensure practical protection. This companion paper bridges the theory-practice gap through computational validation: we implement the CIF defense suite (cognitive firewalls, belief sandboxes, tripwires, drift and anomaly scoring, trust calculus with bounded delegation, provenance tracking, and Byzantine-tolerant consensus) and evaluate detection performance through empirical pipeline evaluation and parametric design analysis.

Our evaluation employs a multi-tier strategy: (1) real defense pipeline evaluation across 30 random seeds, yielding a mean detection rate of 44.7\% [95\% CI: 43.1\%, 46.3\%] on the Claude Code architecture; (2) real ablation studies on a 100-attack corpus identifying the Detection module as the highest-marginal-contribution component ($\Delta\text{TPR} = -0.052$ when removed, accounting for 42\% of pipeline detection); (3) LLM-backed multiagent validation ($N=10$, Gemma 3 4B via Ollama) achieving 80--100\% detection across Claude Code and CrewAI topologies; (4) colony benchmarks at scale (20--100 agents) demonstrating 81--100\% detection on structured adversarial scenarios; and (5) large-scale parametric simulation ($N=3{,}800$) characterizing the design-level coverage ceiling at 94--100\% across four production architectures (Claude Code, AutoGPT, CrewAI, LangGraph). All experiments are deterministically reproducible (seed = 42) and provide open source code at \url{https://github.com/docxology/cognitive_integrity}.

The gap between the parametric ceiling (94--100\%) and current pipeline performance (12--45\%) reflects the distinction between CIF's formal coverage guarantees and the current adapter implementations' maturity. The layered defense architecture is validated: ablation studies confirm that no single component accounts for a majority of detection, and the Firewall + Detection pair exhibits the strongest synergy ($+0.026$ beyond additive prediction). Trust decay with bounded delegation ($\delta^d$) prevents trust amplification across all architectures---a structural guarantee verified both formally (Part 1) and through colony-scale simulation (100\% sybil detection at 0\% FPR). Colony benchmarks reveal that emergent misalignment (agents collectively drifting without explicit adversaries) remains the most challenging scenario (56.1\% detection, 46.6\% FPR), defining the frontier for future defense research. \emph{Note on methodology}: the parametric simulation results (94--100\% detection) are consolidated in Supplementary S08 and characterize CIF's design-level properties under calibrated conditions; all primary analyses in the body of this paper use measured pipeline, LLM, and colony data. This is Part 2 of the three-part \emph{Cognitive Security for Multiagent Operators} series: Part 1 (DOI: 10.5281/zenodo.18364119) establishes the formal foundations (trust calculus, defense composition algebra, adversary taxonomy); Part 3+4 (DOI: 10.5281/zenodo.18364130) provides unified practitioner guidance and cross-domain CIF-AD-OODA applications across ten critical operational domains including infrastructure, supply chain, cyber-security, and information ecosystems. Code and attack corpus generators are available at DOI: 10.5281/zenodo.18364128.
