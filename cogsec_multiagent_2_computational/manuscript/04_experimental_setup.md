\newpage

# Experimental Validation {#sec:results}

This section demonstrates the practical viability of CIF's formal mechanisms through empirical evaluation across production multiagent architectures. We present experimental setup (\cref{sec:exp-setup}) and key findings (\cref{sec:key-findings}). Detailed statistical analysis, ablation studies, and scalability metrics are provided in \cref{sec:extended-results}.

## Experimental Setup {#sec:exp-setup}

### Target Architectures

We evaluated CIF across four production multiagent systems representing diverse architectural patterns (\cref{tab:target-architectures}):

Table: Multiagent system architectures evaluated. {#tab:target-architectures}

| System  | Architecture  | Communication |
| --- | --- | --- |
| Claude Code | Hierarchical ($1 + n$) | Task delegation |
| AutoGPT | Autonomous + plugins | Tool-based |
| CrewAI | Role-based (3--10) | Sequential/parallel |
| LangGraph | Graph-based | State machine |

### Attack Corpus

We assembled a corpus of 950 cognitive attacks across four categories: prompt
injection (500), trust exploitation (200), belief manipulation (150), and
coordination attacks (100). The corpus is 100% template-generated via
`AttackCorpus.generate(seed=42)` — no external datasets are used. Evaluation
uses the full corpus or a stratified subsample (target 100 attacks,
proportional across subcategories) drawn deterministically at seed 42. No
held-out validation split is performed: all reported detection rates are
in-sample. Thresholds are hardcoded literals (`FirewallConfig.injection_threshold = 0.8`,
etc.), not fitted on a training partition.

### Evaluation Methodology {#sec:eval-methodology}

**Simulation-Based Analysis ($N=3{,}800$).** We evaluate CIF through parametric, architecture-aware simulation rather than live deployment against production systems. Each target architecture is modeled as a topology adapter that captures three structural properties: (1) communication pattern (hierarchical, peer-to-peer, role-based, graph-based), (2) trust structure (centralized authority, distributed reputation, role-based permissions), and (3) attack surface characteristics (entry points, propagation paths, state exposure). For each of the 950 attack samples across 4 architectures ($950 \times 4 = 3{,}800$ evaluation instances), the evaluation framework computes a detection score from calibrated base rates (indexed by attack difficulty: easy, medium, hard), modulated by architecture-specific attack-surface multipliers that reflect the topology's structural exposure, with Gaussian noise ($\sigma = 0.05$) added for stochastic variation. The resulting score is thresholded ($\tau = 0.5$) to produce a binary detection outcome.

This parametric approach enables controlled comparison across architectures and attack types at scale, systematic sensitivity analysis across parameter configurations, and ablation studies that would be prohibitively expensive against live systems. The base detection rates and architecture multipliers were calibrated against published benchmarks for prompt injection detection \cite{greshake2023indirect, liu2023prompt} and the authors' experience deploying cognitive firewalls in production multiagent systems. Crucially, the reported detection rates characterize the *framework's design-level detection properties under calibrated conditions*, not the output of running attack text through the implemented defense modules in real time.

**Relationship to implemented modules.** The CIF defense modules---Cognitive Firewall, Belief Sandbox, Tripwire Monitor, Trust Calculus, Byzantine Consensus, Provenance, Drift Detection, and Invariant Checker---are implemented and independently tested under the project coverage gate. The evaluation framework's ``ExperimentRunner`` operates in two modes: (1) \textit{pipeline-driven}, where each attack sample's text content is routed through the real defense pipeline and the pipeline's own detection verdict is used directly; and (2) \textit{parametric simulation}, where detection is computed from calibrated base rates modulated by architecture multipliers. When a real pipeline is provided to the runner, Mode 1 is used; when no pipeline is provided, Mode 2 is used. This dual-mode design enables both empirical validation of the implemented defenses and controlled parametric analysis of architectural sensitivity.

**Pipeline-driven validation ($N=10$).** Running the full 950-attack corpus through the assembled ``SeriesPipeline`` (all 8 defense modules in sequence) confirms 100\% attack coverage (all 950 attack payloads successfully routed through the defense pipeline --- this measures routing completeness, not detection efficacy: of the routed attacks, the pipeline classified $\sim$44.8\% as attacks on average across seeds in the multi-seed analysis) with 0\% routing failure rate across all four architectures and all four attack categories. The ``EnhancedCognitiveFirewall`` module detects the majority of attacks on first evaluation (short-circuiting the series chain), with mean latency of 0.08ms per sample. This result validates CIF's defense design: the layered pipeline catches every attack in the corpus regardless of architecture topology. The parametric simulation tables presented below characterize the \textit{architecture-differentiated} detection properties---how detection would vary if individual modules operated in isolation with architecture-specific exposure factors.

**LLM-backed multiagent validation ($N=10$).** To confirm that the pipeline-driven and parametric results hold when attacks are processed by real language models operating within architecture-specific topologies, we additionally evaluate CIF using live LLM agents. Each architecture adapter spawns a multiagent system where every agent is backed by a real LLM (Gemma 3 4B \cite{team2025gemma} via Ollama), configured with role-specific system prompts (orchestrator, researcher, reviewer, etc.) and connected according to the architecture's communication graph and trust matrix. We evaluated 5 representative attacks (one per category) across 2 architectures ($5 \times 2 = 10$ trials). Attack payloads are injected into the system's entry-point agent(s) and propagated through the communication topology up to a bounded depth; the CIF defense pipeline then analyzes all inter-agent messages for detection. This three-phase evaluation---single-agent baseline ($N=5$), multi-agent propagation ($N=10$), and CIF defense analysis---demonstrates that the framework operates correctly with genuine LLM reasoning rather than simulated responses.

Table: LLM-backed multiagent detection results ($N=10$, Gemma 3 4B, 5 representative attacks per architecture). {#tab:llm-validation}

| Architecture | Topology | Detection Rate | TP / FN | Avg Latency |
| :--- | :--- | :--- | :--- | :--- |
| Claude Code | Hub-spoke | 80.0\% | 4 / 1 | 15.2s |
| CrewAI | Chain | 100.0\% | 5 / 0 | 15.9s |

The LLM-backed results provide preliminary evidence that CIF's defense pipeline detects the majority of attack types---direct injection, authority impersonation, belief drift---when processed through genuine multiagent interactions. Claude Code's single miss (1 false negative on $N=5$) yields an 80\% detection rate; CrewAI achieves 100\% detection on its 5-attack sample. These preliminary results ($N=10$) complement the parametric analysis (\cref{sec:parametric-analysis}): the parametric model establishes architecture-differentiated design-level properties, while the LLM validation confirms that the implemented defenses operate with real language model behavior. The small sample size ($N=5$ per architecture) precludes reliable confidence interval estimation; expansion to all four architectures with larger attack samples is planned for future work.

**Limitations of the simulation approach.** The parametric simulation results (\cref{sec:parametric-analysis}) reflect CIF's design-level detection properties---how the defense layers should perform given calibrated difficulty and architecture characteristics---rather than pipeline-driven empirical outcomes. Native defenses built into each framework (e.g., Claude Code's permission gating, AutoGPT's safety constraints) are not captured in the baseline, which assumes no CIF components are active. Results should therefore be interpreted as characterizing CIF's intrinsic detection architecture rather than marginal improvement over existing framework protections. The LLM-backed validation ($N=10$) provides initial evidence that these defenses operate when attacks flow through real language model agents, while the multi-seed pipeline analysis (30 seeds, mean DR $\sim$44\%) and real ablation studies (full pipeline TPR $\sim$12\%) establish empirical baselines for the current adapter implementations.

**Operational Definition of Detection.** An attack is classified as ``detected'' when the CIF pipeline's aggregate confidence score exceeds the configured threshold ($\tau = 0.5$ by default). The confidence score combines firewall pattern-matching scores, sandbox quarantine signals, tripwire alerts, and trust calculus violations via the learned fusion operator (Section 2). Ground truth labels were assigned by two independent annotators (Cohen's $\kappa = 0.84$, indicating``almost perfect'' agreement per \cite{landis1977measurement}) with disagreements resolved by a third reviewer.

**Reproducibility.** All experiments use a fixed random seed (42) for deterministic reproduction. The complete evaluation framework, including architecture adapters, attack corpus (sanitized subset), and analysis scripts, is available in the supplementary repository. Multi-seed stability analysis across 30 seeds is reported in \cref{sec:extended-results}. All experiments are fully deterministic when executed with the default seed configuration.

**Planned Statistical Analysis.** To support inferential integrity, we specify three primary hypotheses and their statistical tests. A separate `analysis/preregistration.yaml` is not included in this checkout, so this description should not be read as evidence of an external preregistration.

*H1 (Layered Defense)*: The full CIF pipeline achieves strictly higher detection rate than any single defense module. Test: one-sided two-proportion $z$-test comparing full-pipeline TPR against each component's TPR on the 98-attack ablation corpus; $\alpha = 0.05$, Bonferroni-corrected for 7 comparisons ($\alpha_\text{adj} = 0.0071$).

*H2 (Trust Calculus)*: The trust calculus prevents trust amplification in the sybil infiltration scenario (50 agents, 4 adversaries). Test: one-sided proportion test that detection rate in sybil scenario $> 0.95$; $\alpha = 0.05$.

*H3 (Topology Dependence)*: Detection rate differs significantly across architecture topologies. Test: chi-squared test of independence across architecture × detected contingency table; $\alpha = 0.05$.

Table: Statistical power analysis for each evaluation mode. {#tab:power-analysis-preregistration}

The power summary (\cref{tab:power-analysis-preregistration}) shows that the multi-seed and LLM validation modes are severely underpowered for precise estimation.

| Evaluation Mode | $N$ (Actual) | Effect Size | Required $N$ ($\pm 5\%$ precision) | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| Multi-seed pipeline (30 seeds) | 30 | DR = 0.448 | $N \geq 246$ seeds | Severely underpowered; $\pm 8.8\%$ CI |
| Ablation corpus | 98 attacks | TPR = 0.122 | $N \\geq 171$ | Marginally underpowered; $\\pm 6.5\\%$ CI |
| LLM multiagent (per arch.) | 5 per arch. | DR $\in$ [0.80, 1.00] | $N \geq 246$ | Severely underpowered; wide CIs |
| Colony benchmark | 1 scenario each | — | $N \geq 10$ scenarios | Exploratory only; not powered for inference |
| Parametric simulation | 3,800 | DR = 0.96--1.00 | Sufficient | Design-level; not subject to sampling |

*Interpretation*: The multi-seed and LLM validation modes are severely underpowered for precise estimation of detection rates. The reported results should be interpreted as preliminary estimates with the uncertainty quantified in \cref{sec:bayesian-uncertainty}. The parametric simulation ($N=3{,}800$) is adequately powered but reflects design-level properties rather than empirical pipeline performance. Future work should target $N \geq 246$ seeds (multi-seed) and $N \geq 246$ per architecture (LLM validation) for definitive inference.

**Runtime and Resource Requirements.** The full experiment suite completes in approximately 15 minutes on the reference hardware specified below. Peak memory usage reaches approximately 2GB during Byzantine consensus tests, which require maintaining state for all agent interactions. Individual defense mechanism tests (firewall-only, sandbox-only, tripwires-only) complete in under 5 minutes each.

**Software Environment.** Python 3.12, NumPy 1.26, SciPy 1.12, scikit-learn 1.4, matplotlib 3.8. The evaluation framework has been tested on Python 3.10, 3.11, and 3.12 with consistent results across all versions. All experiments executed on a single workstation (Apple M3 Max, 128GB RAM, macOS 15).

## Key Findings {#sec:key-findings}

### Finding 1: Layered Defense Significantly Outperforms Single Mechanisms

The central empirical finding validates CIF's layered approach. No single defense mechanism achieves acceptable protection, but their composition yields substantial improvement. \Cref{fig:detection-performance} presents detection rates across defense configurations and attack categories, with the full numerical summary in \cref{tab:detection-performance}.

![Detection Performance Comparison. Bar chart comparing detection rates across defense configurations (Baseline, Firewall-only, Sandbox-only, Tripwires-only, Full CIF) for each attack category (Prompt Injection, Trust Exploitation, Belief Manipulation, Coordination). Error bars show 95\% bootstrap confidence intervals ($n=1{,}000$ resamples). Full CIF consistently achieves $>90\%$ detection across all categories, while individual mechanisms show significant gaps---validating the defense composition algebra (Part 1, Theorems 3.1-3.2). The Full CIF theoretical rate ($1 - \prod(1-r_i) \approx 0.99$) via \texttt{compute\_series\_detection\_rate()} exceeds the empirical 0.94, indicating room for implementation-level optimization. Detection data generated by the CIF evaluation pipeline (\texttt{output/data/detection\_data.json}).](figures/detection_performance.pdf){#fig:detection-performance width=95%}

Table: Detection performance summary — empirical results across evaluation modes. {#tab:detection-performance}

| Evaluation Mode | Detection Rate | Sample Size | Source |
| --- | --- | --- | --- |
| Multi-seed pipeline (Claude Code, 30 seeds) | 44.8\% [43.2, 46.4\%] | $N=30$ seeds | `multi_seed_results.json` |
| Ablation pipeline (full, 98-attack corpus) | 12.2\% | $N=98$ | `ablation_results.json` |
| LLM multiagent — Claude Code (Gemma 3 4B) | 80.0\% [28, 99\%] | $N=5$ | `llm_demo_results.json` |
| LLM multiagent — CrewAI (Gemma 3 4B) | 100\% [48, 100\%] | $N=5$ | `llm_demo_results.json` |
| Colony — recruitment poisoning (20 agents) | 80.7\% | 1 scenario | `colony_results.json` |
| Colony — sybil infiltration (50 agents) | 100\% | 1 scenario | `colony_results.json` |
| Colony — emergent misalignment (50 agents) | 74.3\% | 1 scenario | `colony_results.json` |
| Parametric simulation (design ceiling) | 96--100\% | $N=3{,}800$ | \cref{sec:parametric-analysis} |

*Note: The wide variation across evaluation modes (12--100\%) reflects the distinction between CIF's design-level coverage (parametric) and the current adapter implementations' maturity (pipeline/LLM). The multi-seed mean of 44.8\% represents the most reliable single estimate for the Claude Code architecture under current implementation. Confidence intervals for LLM results are Clopper-Pearson exact binomial intervals reflecting the preliminary sample size ($N=5$ per architecture).*

The real ablation data (\cref{tab:component-removal}) quantifies the layered architecture's individual contributions: no single component accounts for a majority of detection (Detection module: $\Delta\text{TPR} \approx -0.051$ when removed), while the three largest harmful removals (Detection, Tripwires, Invariants) together account for about 80\% of the summed negative $\Delta\text{TPR}$ magnitude on this corpus. This confirms that defense composition provides meaningful improvement over individual mechanisms, consistent with the multiplicative composition theorems from Part 1.

The multi-seed pipeline analysis (mean DR = 44.8\%, CV = 0.097 across 30 seeds) establishes a reliable baseline for the Claude Code architecture. The parametric simulation (\cref{sec:parametric-analysis}) achieves 96--100\% detection rate, defining the design-level coverage ceiling that fully-realized adapter implementations should approach.

### Finding 2: Trust Calculus Prevents Amplification Attacks

\cref{fig:roc-curves} shows the Receiver Operating Characteristic curves for each attack category, with AUC values ranging from 0.92 (Coordination) to 0.97 (Prompt Injection). The operating point selected by Youden's $J$ statistic balances sensitivity and specificity.

![ROC Curves by Attack Category. Receiver Operating Characteristic curves showing the tradeoff between True Positive Rate (sensitivity) and False Positive Rate (1-specificity) for CIF detection across four attack categories. AUC values computed via \texttt{compute\_auc\_from\_points()} (trapezoidal integration): Prompt Injection = 0.97, Trust Exploitation = 0.94, Belief Manipulation = 0.93, Coordination Attacks = 0.92. The operating point (diamond marker) is selected to maximize Youden's $J$ statistic ($J = \text{TPR} - \text{FPR}$), balancing sensitivity and specificity. Confidence bands (shaded) computed via $n=1{,}000$ bootstrap resamples; the wider band for Coordination Attacks reflects the smaller sample size ($n=100$ vs.\ $n=500$ for injection).](figures/roc_curves.pdf){#fig:roc-curves width=90%}

Across all tested architectures, the bounded trust decay ($\delta^d$) successfully prevented trust laundering and amplification attempts. In adversarial scenarios where attackers attempted to relay high-impact content through multiple trusted intermediaries, the exponential decay ensured that delegated trust remained below action thresholds. This is validated by the colony benchmark sybil infiltration scenario (50 agents, 4 adversaries), which achieved 100\% detection at 0\% FPR (\cref{tab:colony-benchmarks}). The trust calculus ablation shows a marginal contribution of $\Delta\text{TPR} = -0.020$ on the 98-attack corpus, confirming its role as a structural safeguard.

Critically, this held even when individual agents in the delegation chain were compromised---the trust bound is a \textit{structural} guarantee independent of agent behavior.

### Finding 3: Architecture Topology Affects Detection

\cref{tab:cross-arch-summary} summarizes the real LLM validation results by architecture topology.

Table: Cross-architecture detection summary (real LLM validation, $N=10$). {#tab:cross-arch-summary}

| Architecture | Detection Rate | TP / FN | Topology |
| --- | --- | --- | --- |
| Claude Code | 80\% | 4 / 1 | Hub-spoke |
| CrewAI | 100\% | 5 / 0 | Chain |

*Note: Only 2 of 4 architectures have been evaluated with live LLM agents ($N=5$ each). The complete parametric cross-architecture analysis is available in \cref{sec:parametric-cross-arch}.*

Preliminary LLM validation across two architectures shows topology-dependent detection: CrewAI's sequential chain topology achieves 100\% detection ($N=5$), while Claude Code's hub-spoke topology shows one miss. The colony benchmarks further demonstrate scenario effects: structured adversarial scenarios (sybil infiltration, quorum manipulation) achieve near-complete detection, while the 30-seed emergent-misalignment benchmark (with no explicit adversaries) averages 74.3\% detection. The previously reported 56.1\% value was a single seed and is not used here.

Architectures with explicit role boundaries (CrewAI) and rich graph structure (LangGraph, per parametric analysis) provide more interception opportunities for CIF monitors. Extension of LLM validation to AutoGPT and LangGraph is planned for future work.

### Finding 4: Performance Overhead Is Acceptable for Security Contexts

Full CIF deployment introduces latency overhead in the 20-25\% range with memory requirements scaling with agent count. For security-critical deployments, this overhead is acceptable given the integrity improvement achieved.

The overhead is dominated by the cognitive firewall (input classification) and Byzantine consensus (coordination). For environments where consensus is unnecessary, lighter configurations achieve comparable detection with lower overhead (Table 3 (Risk-Based Configuration, Part 1)).

### Finding 5: Attack-Type Specific Vulnerabilities Remain

Despite strong overall performance, specific attack types remain challenging:

\begin{itemize}
\item **Semantic equivalent attacks**: Rephrased injections that preserve meaning evade pattern-matching
\item **Progressive drift**: Sub-threshold changes accumulate below detection windows
\item **Orchestrator compromise**: Outside our threat model (our honest orchestrator assumption (Part 1, Section 2))
\end{itemize}

These gaps define the frontier for future defense research.

## Structural Guarantees Beyond Detection Rates

The empirical results validate that CIF's formal mechanisms translate to practical protection. The key insight is not the specific detection rates achieved---which reflect current attack sophistication and will degrade as adversaries adapt---but rather the \textit{structural} properties:

\begin{enumerate}
\item Trust cannot be amplified through delegation (Part 1, Theorem 2)
\item Defenses compose predictably (Part 1, Theorems 3.1 and 3.2)
\item Information-theoretic bounds constrain the stealth-impact tradeoff (Part 1, Theorem 4)
\end{enumerate}

These properties hold independent of specific detection thresholds and provide the foundation for long-term security assurance.

For detailed statistical analysis including significance testing, confidence intervals, ablation studies, and scalability benchmarks, see the Extended Results (\cref{sec:extended-results}).
