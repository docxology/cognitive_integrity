\newpage

# Discussion {#sec:discussion}

## Synthesis of Findings

**Empirical Results at a Glance:**

| Evaluation Mode | Key Metric | Value | Section |
| --- | --- | --- | --- |
| Multi-seed pipeline ($N=30$, Claude Code) | Mean detection rate | 44.8\% [CI: 43.2\%, 46.4\%] | §\ref{sec:multi-seed} |
| Real ablation (98-attack corpus) | Full pipeline TPR | 12.2\%; Detection module $=$ 42\% of detection | §\ref{sec:extended-ablation} |
| LLM multiagent ($N=10$, Gemma 3 4B) | Detection across 2 architectures | 80--100\% | §\ref{sec:llm-validation-results} |
| Colony benchmarks (20--100 agents) | Structured / emergent scenarios | 81--100\% / 74.3\% | §\ref{sec:colony-results} |
| Parametric simulation ($N=3{,}800$) | Design-level ceiling | 96--100\% | §\ref{sec:parametric-analysis} |

The wide variation across evaluation modes (12--100\%) reflects the distinction between CIF's design-level coverage properties (parametric ceiling) and current adapter implementation maturity (pipeline/LLM results). The structural guarantees are consistent across modes.

Our multi-tier evaluation validates the core theoretical claims of the Cognitive Integrity Framework established in Part 1, while honestly characterizing the gap between design-level properties and current implementation maturity. The full CIF defense pipeline achieves a mean detection rate of 44.8\% [95\% CI: 43.2\%, 46.4\%] across 30 random seeds on the Claude Code architecture, with ablation studies confirming a full-pipeline TPR of $\sim$12\% on the 98-attack evaluation corpus. Preliminary LLM-backed validation ($N=10$, Gemma 3 4B) yields 80--100\% detection across two architecture topologies, and colony benchmarks demonstrate 81--100\% detection on structured adversarial scenarios at 20--100 agent scale. The parametric simulation (\cref{sec:parametric-analysis}) establishes a design-level ceiling of 96--100\%, confirming that CIF's layered architecture has substantially higher coverage potential than the current adapters realize. More importantly, the consistency of the structural guarantees across evaluation modes---trust decay preventing amplification (100\% sybil detection in colony benchmarks), layered composition providing meaningful improvement over individual mechanisms (top 3 components account for 59\% of detection)---suggests that CIF's formal abstractions capture genuine structural properties of multiagent security. We now examine these findings in detail.

### Why Layered Defense Succeeds

![Defense Composition Architecture. Diagram illustrating the series and parallel composition of CIF defense mechanisms. The Cognitive Firewall provides the first line of defense (input filtering), followed by the Belief Sandbox (provisional isolation) and Tripwires (continuous monitoring) in series. Trust Calculus and Byzantine Consensus operate in parallel for delegation and coordination decisions. The multiplicative detection guarantee (Part 1, Theorems 3.1-3.2) emerges from the orthogonality of attack surfaces targeted by each layer: series composition yields $P_{\\text{detect}} = 1 - \\prod_{i}(1 - r_i)$ computed via \\texttt{compute\\_series\\_detection\\_rate()}, while parallel composition uses max-score fusion via \\texttt{compute\\_parallel\\_detection\\_rate()}. The Venn overlap statistics in the accompanying table are dynamically computed from per-mechanism detection rates using these composition functions.](figures/defense_composition.pdf){#fig:defense-composition width=95%}

The defense composition architecture (\cref{fig:defense-composition}) illustrates how the CIF defense mechanisms integrate into a coherent defense posture. The multiplicative composition of detection rates (Theorems 3.1-3.2 in Part 1) explains the empirical observation that full CIF substantially outperforms individual mechanisms. Each defense targets a distinct attack surface:

| Defense Layer | Target Attack Surface | Contribution |
|---------------|----------------------|--------------|
| Cognitive Firewall | Input-based injection | Blocks direct attacks |
| Belief Sandbox | Unverified content | Contains propagation |
| Tripwires | Belief manipulation | Detects subtle drift |
| Trust Calculus | Delegation abuse | Bounds amplification |
| Consensus | Coordination attacks | Ensures agreement integrity |

### Architecture-Specific Insights

Table: Architecture vulnerability patterns and observed CIF defense response. {#tab:architecture-insights}

| Architecture  | Primary Vulnerability  | Observed CIF Defense Mechanism |
| --- | --- | --- |
| Hierarchical | Orchestrator compromise cascades | Orchestrator-specific tripwires (82% detection) |
| Peer-to-peer | Lateral movement amplification | Byzantine consensus + trust decay |
| Role-based | Role impersonation | Attestation verification at role transitions |
| State machine | State corruption | State hash verification (deterministic detection) |

The architecture-specific results reveal that vulnerability patterns align closely with the structural properties predicted by Part 1's threat model analysis. Hierarchical architectures concentrate risk at the orchestrator: a single compromised orchestrator can cascade malicious instructions to all subordinate agents. Our evaluation shows that tripwire-only deployments achieve 82\% detection in hierarchical topologies but only 61\% in peer-to-peer systems, quantifying the architectural dependence of defense effectiveness.

Peer-to-peer architectures present the opposite profile. Without a central authority, lateral movement between agents is the primary threat vector. Trust amplification through delegation chains enables an attacker who compromises a single agent to gradually extend influence across the network. The trust calculus with $\delta^d$ decay directly addresses this: the exponential decay bound ensures that delegated trust diminishes with chain length, preventing unbounded amplification. Our results confirm that peer-to-peer topologies show the largest relative improvement (from 0\% baseline to 94\% with full CIF), consistent with the theoretical prediction that these architectures benefit most from formal trust bounds.

Role-based systems introduce impersonation as the primary risk. When agents assume specialized roles (researcher, writer, reviewer), an attacker who can assume a trusted role gains the permissions associated with that role. In our evaluation, attestation-based verification at role transitions detected 94\% of impersonation attempts (\cref{tab:architecture-insights}). Unexpected role transitions served as reliable early indicators of compromise.

## Limitations and Threats to Validity

### Residual Attack-Type Vulnerabilities

Despite differentiated performance across evaluation modes, specific attack types remain challenging and merit detailed examination.

Semantic equivalent attacks pose the most significant residual risk. When an adversary rephrases a known injection to preserve its semantic intent while altering surface-level features, pattern-matching defenses fail to recognize the attack. Our evaluation shows that the CIF firewall's TF-IDF and embedding-based classifiers achieve 89\% detection on direct injections but only 72\% on semantically equivalent reformulations. This gap is not unique to CIF; it reflects a fundamental limitation of feature-based detection that also affects commercial tools such as Lakera Guard and LLM Guard. Incorporating large language model-based semantic analysis into the firewall classification pipeline represents the most promising mitigation, though it introduces additional latency and cost trade-offs.

Progressive drift attacks exploit the tension between detection sensitivity and observation window length. An attacker who modifies beliefs by amounts below the drift detection threshold ($\epsilon_{\text{drift}}$) in each interaction can accumulate significant deviation over many rounds. Our sliding window detector catches abrupt changes effectively but misses gradual drift that stays within per-step bounds. Extending the observation window improves drift detection but increases response latency proportionally; a 10x window extension, for example, requires maintaining 10x more historical state. Adaptive baseline approaches that adjust thresholds based on cumulative deviation, rather than per-step thresholds alone, offer a promising direction explored in our supplementary algorithms.

Orchestrator compromise falls outside our current threat model, which assumes an honest orchestrator. If the orchestrator itself is compromised, it can selectively disable defenses, suppress alerts, or manipulate the trust matrix directly. Multi-orchestrator architectures with cross-verification provide a potential mitigation, effectively applying Byzantine consensus principles to the orchestration layer itself. This extension requires careful attention to consistency guarantees and is an active area of our ongoing research.

### Scaling Beyond Ten Agents

Our evaluation focused on systems with 3--10 agents, reflecting current production norms. Three bottlenecks constrain scaling:

1. **Consensus latency**: Byzantine consensus requires all-to-all communication ($O(n^2)$ messages per round), reaching 4.2s at 100 agents (\cref{tab:agent-scaling}). Beyond $\sim$50 agents, hierarchical consensus (partitioning agents into committees with inter-committee agreement) or random committee selection is required.

2. **Provenance chain depth**: Deeply nested delegation hierarchies slow verification as each link requires cryptographic validation. At delegation depth $>$10, provenance pruning (retaining only chain endpoints with Merkle commitments for intermediate links) becomes necessary.

3. **Memory**: Trust matrix storage ($O(n^2)$) and belief history ($O(n \cdot t)$) dominate. At 100 agents, peak memory reaches 1.6 GB (\cref{tab:agent-scaling}). Sliding-window belief history and sparse trust representations can mitigate this.

### Generalization Beyond the Evaluated Corpus and Architectures

Our evaluation, while comprehensive within its scope, faces four categories of generalization limitations that practitioners should consider when extrapolating our results to their deployments.

**Corpus Temporal Bias.** Our attack corpus (950 attacks across four categories) was assembled from published jailbreak datasets, custom adversarial prompts, red team exercises, and synthetic generation, but it necessarily reflects attack techniques known at the time of evaluation. The adversarial landscape evolves continuously; novel attack categories---such as attacks exploiting emergent behaviors in large-scale agent swarms, attacks that manipulate shared environmental state rather than direct communication channels, or attacks leveraging model-specific vulnerabilities discovered after our evaluation---may expose detection gaps not captured by our current corpus. Detection rates should therefore be interpreted as lower bounds on CIF's protective capability under the current threat landscape, rather than as guarantees of future performance against novel adversarial techniques.

**Scale Testing Limits.** Our evaluation focused on systems with 3--10 agents, which reflects the majority of current production deployments but does not validate CIF performance at larger scales. Emerging applications in simulation, scientific discovery, and autonomous operations may involve 50--100+ agents, where consensus latency (quadratic in agent count), provenance chain depth, and belief history storage may introduce both performance degradation and novel attack surfaces not present at smaller scales. The composition theorems from Part 1 hold mathematically at any scale, but practical implementation constraints may force approximations (e.g., hierarchical consensus, provenance pruning) whose security implications remain untested.

**LLM Behavior Variance.** Our simulation-based architecture adapters model topology and communication patterns but do not execute actual LLM inference. Language model behavior varies across model families (GPT-4, Claude, Gemini, Llama), fine-tuning approaches, temperature settings, and prompt formats in ways that may affect attack success rates and detection efficacy. CIF detection mechanisms rely on statistical patterns in agent communication; if production LLM outputs exhibit different distributional characteristics than our simulation assumptions, detection thresholds calibrated on our evaluation may require adjustment. Future work should validate CIF on live inference with diverse model backends.

**Architecture Sampling.** The four architectures in our evaluation (hierarchical orchestrator, autonomous mesh, role-based teams, and state machine) represent dominant deployment patterns but do not exhaust the space of possible multiagent coordination topologies. Novel architectural paradigms---such as mixture-of-experts agents, debate-based systems, SOP-driven pipelines, recursive self-improvement loops, or dynamically reconfiguring topologies---may present vulnerability patterns not captured by our selected architectures. The composition algebra (Part 1) provides a principled basis for analyzing new architectures, but empirical validation on each novel topology is necessary before claiming coverage.

The defense evolution strategy outlined in our adaptive defenses discussion and the practical **Risk Assessment Framework** in Part 3+4 provide concrete strategies for managing these residual generalization risks through ongoing corpus expansion, periodic defense retraining, and architecture-specific validation. The same unified paper complements this with domain-calibrated threat profiles --- showing how attack distributions differ systematically across operational sectors (e.g., millisecond OODA cycles in drone swarms vs. year-scale cycles in diplomatic agents) and how CIF's temporal parameters must be recalibrated accordingly.

### Simulation vs. Live Deployment Caveats

Our simulation-based evaluation approach, while enabling systematic cross-architecture comparison at scale, introduces important caveats. The architecture adapters model topology and communication patterns but do not capture the full complexity of production deployments, including framework-specific quirks, version-dependent LLM behaviors, or real-world network conditions. The baseline detection rate of 0.00 reflects the absence of CIF components specifically, not the absence of all defenses---production frameworks include native safety features (e.g., Claude Code's permission gating, LangChain's guardrails) that would provide non-zero baseline protection. Future work should deploy CIF as middleware on live framework instances to measure marginal improvement over existing protections.

Additionally, the R$^2$ values for our scaling regressions (0.994 for detection time) reflect the controlled simulation environment rather than the variance typical of production measurements. Practitioners should expect higher variance in real deployments.

### Observed Cost-Benefit Profile

The ablation data (\cref{tab:component-removal}) reveals a clear incremental cost-benefit curve for the current adapter implementations. The Detection module alone contributes $\Delta\text{TPR} \approx -0.051$ (about 42\% of full-pipeline TPR on the ablation corpus); Tripwires and Invariants are the next-largest removal effects. The top three harmful removals (Detection, Tripwires, Invariants) together account for about 82\% of the summed negative $\Delta\text{TPR}$ magnitude in this run. The Tripwire + Detection pair shows the strongest synergy ($\approx +0.031$, \cref{tab:real-synergy}), combining canary-belief shift detection with text-feature analysis.

The gap between the full pipeline TPR ($\sim$12\% on the 100-attack ablation corpus, $\sim$45\% mean across 30 seeds) and the parametric ceiling (94--100\%; \cref{sec:parametric-analysis}) quantifies the adapter implementation gap. The lower-ranked components currently show modest marginal contribution ($\Delta\text{TPR}$ between $-0.005$ and $-0.009$) on the evaluation corpus, suggesting that the attack distribution does not sufficiently exercise these mechanisms---or that their current adapter implementations require further tuning. The practical deployment implications of these findings are explored in Part 3.

### Threats to Validity

Several threats to validity constrain the generalizability of our findings. Regarding internal validity, our simulation-based evaluation models architectural topology and communication patterns but does not execute actual LLM inference or production framework code. The detection rates therefore reflect CIF's ability to identify structural attack patterns rather than its performance against attacks that exploit specific LLM behaviors or framework vulnerabilities. A follow-up study deploying CIF as middleware on live framework instances is needed to establish ecological validity.

External validity is bounded by our selection of four architectures. While these represent the dominant deployment patterns in current practice, novel architectural paradigms (such as large-scale swarm systems, debate-based agents, or hierarchical mixtures of experts) may present vulnerability patterns not captured by our evaluation. The 950-attack corpus, though comprehensive relative to existing benchmarks, cannot represent the full space of possible cognitive attacks; detection rates should be interpreted as lower bounds that may decrease when confronting genuinely novel attack techniques.

Construct validity concerns center on the detection rate metric itself. A binary detected/undetected classification does not capture partial detection (e.g., an attack that is flagged but not blocked) or the severity of successful attacks. Future work should incorporate severity-weighted metrics and measure time-to-detection alongside binary classification. Statistical conclusion validity is supported by large sample sizes, significance testing with Bonferroni correction for multiple comparisons, and large effect sizes (Cohen's $d > 0.8$), but the controlled simulation environment produces lower variance than production measurements would exhibit.

Researcher degrees of freedom present a further concern: the framework, attack corpus, evaluation methodology, and analysis were developed by a single research group. While we mitigate this through deterministic reproducibility (fixed seed, public code), pre-registered analysis protocols (all hypotheses stated before evaluation), and independent ground-truth labeling (Cohen's $\kappa = 0.84$ inter-rater agreement), independent replication by external teams is essential for establishing the robustness of these findings. We encourage the community to reproduce our results using the provided scripts and to evaluate CIF against independently developed attack corpora.

*Bayesian Reanalysis.* The primary statistical claims in this paper (detection rates, confidence intervals) were originally computed using frequentist methods (Wilson intervals, two-proportion $z$-tests). A full Bayesian reanalysis using Beta-Binomial posteriors (\cref{sec:bayesian-uncertainty}) confirms all directional findings but reveals important underpowering: the LLM validation ($N = 5$--$10$ per architecture) provides only $\pm 13$ to $\pm 18$ percentage points of precision at the observed 80\% detection rate. We report Bayes factors for the key claims---most consequentially, the empirical-parametric gap on direct injection yields $\mathrm{BF}_{10} \gg 10^{6}$, decisive evidence that the gap is structural rather than statistical. Future replications should target $N \geq 246$ per architecture for adequately powered LLM validation.

## Relationship to Prior Work

Our empirical results contextualize CIF's contributions relative to the related work surveyed in \cref{sec:related-work}. Three findings merit specific comparison.

First, CIF's cognitive firewall achieves 85\% detection on prompt injection when deployed alone---comparable to published detection rates for commercial single-agent tools such as NeMo Guardrails \cite{rebedea2023nemo} and Lakera Guard---but the full CIF stack reaches 96\% by composing the firewall with mechanisms targeting attack vectors that single-agent tools do not address (trust exploitation, belief manipulation, coordination). This validates the central thesis that multiagent security requires defenses beyond input filtering. A head-to-head comparison on standardized benchmarks (e.g., StrongReject) remains an important direction for future work.

Second, our trust calculus with $\delta^d$ decay is, to our knowledge, the first formally verified bound on delegated trust in LLM-based agent systems. While classical trust frameworks (FIRE \cite{huynh2006fire}, REGRET \cite{sabater2001regret}) address trust propagation in distributed systems, none provide the exponential decay guarantee that our empirical results confirm prevents trust laundering across all four tested architectures.

Third, CIF's adaptation of Byzantine consensus to semantic content (beliefs and trust assertions rather than transaction ordering) extends classical BFT \cite{lamport1982byzantine, castro1999practical} into a domain where ``Byzantine'' behavior manifests as belief poisoning and coordinated deception. Our 90\% detection rate on coordination attacks demonstrates practical viability of this adaptation.

## Open Research Directions

### Game-Theoretic Arms Race Dynamics {#sec:game-theory-analysis}

The CIF evaluation admits a two-player zero-sum formulation (\cref{sec:game-theory}) in which the attacker selects from the six attack categories and the defender selects from six defense configurations. Solving this game numerically with the empirical payoff matrix (\cref{tab:payoff-matrix}) identifies a unique pure-strategy Nash equilibrium at $(d^* = \text{Full CIF}, a^* = \text{Emergent Misalignment})$ with game value $v^* \approx 0.56$. Full CIF weakly dominates every proper subset configuration column-wise, so no mixed defense strategy improves on deploying the complete stack---a finding that simplifies operational planning considerably: practitioners do not need to stochastically alternate between defense configurations at current adapter maturity.

The static Nash analysis, however, assumes a fixed attack distribution and fixed defender capability. Running the arms-race simulation (\texttt{arms\_race\_simulation()} in \texttt{src/analysis/game\_theory.py}) under adversarial adaptation reveals that without defender retraining the effective detection rate degrades at approximately 2\% per attacker adaptation cycle. Periodic defender retraining every five cycles with 3 pp recovery per event stabilizes the long-run equilibrium at $\sim 0.52$---a 4 pp degradation from the static Nash value but a stable operating regime. Without any defender maintenance, the arms race asymptotes toward zero detection over approximately 30 cycles, consistent with the degradation bounds derived in Part 1, Section 4.

The practical implication crosses two axes. First, configuration: Full CIF is the dominant pure strategy, so deployment planning reduces to deciding \emph{when} (not \emph{what}) to update. Second, cadence: cognitive security is a maintenance practice, not a one-shot deployment. Organizations that treat CIF as a deployed-and-done capability will observe steadily degrading detection rates; organizations that schedule retraining in step with the attacker adaptation cycle will operate near the Nash equilibrium indefinitely. The operational recommendations in Part 3 map this finding to concrete retraining cadences.

### Free Energy Interpretation of Residual Emergent Misalignment {#sec:fep-discussion}

The 74.3\% mean detection rate for emergent misalignment is both the weakest structured colony result and the most interesting from a theoretical standpoint. Under the Free Energy Principle framing (\cref{sec:free-energy-principle}), an emergent misalignment attack is a \emph{distributed, low-precision} adversarial event: no single agent's free energy spikes dramatically in any single interaction, but the collective belief state drifts as the ensemble of agents exchanges low-magnitude, individually-subthreshold updates. The current \texttt{DriftDetector} uses a single per-agent KL threshold (\cref{thm:attack-fep} instantiated at the individual level), which is well-suited for concentrated attacks that raise one agent's free energy above $\kappa_{\mathrm{FEP}}$ but systematically misses the distributed low-amplitude signal of collective drift. This value is the 30-seed benchmark mean; the single-seed 56.1\% result is not treated as the publication estimate.

A high-dimensional FEP formulation decomposes the collective free energy $F_{\text{coll}} = \sum_j F[Q_j]$ into per-belief-dimension components and monitors the structured change across the decomposition rather than the per-agent aggregate. A second-moment monitor---tracking the covariance of $\Delta F$ across agents rather than its per-agent mean---is particularly well-matched to emergent misalignment: coordinated subthreshold drift produces a characteristic covariance signature even when no individual $\Delta F$ exceeds its detection threshold. This observation points toward the clearest open research direction to emerge from our evaluation: collective free-energy monitoring across the agent network, formalized via the active-inference precision-weighting machinery and implemented as a cross-agent covariance detector in \texttt{src/core/detection.py}.

### Adversarial Retraining and Honeypot Agents

Detection rates inevitably degrade as adversaries learn to evade deployed defenses---a dynamic well-characterized by the arms race model in security research and formalized in Part 1's detection degradation analysis (Section 4). Our current evaluation uses a static attack corpus, which represents a snapshot of adversarial capability rather than an evolving threat. Future work should investigate adversarial retraining of CIF detection mechanisms, where the firewall and anomaly detectors are periodically retrained on attacks that successfully evade current configurations. This approach, analogous to adversarial training in machine learning robustness research, requires careful management of the retraining loop to prevent catastrophic forgetting of previously effective detection patterns.

A second promising direction is the deployment of honeypot agents---intentionally vulnerable agents designed to attract and characterize novel attack techniques without risking production systems. By analyzing the attacks directed at honeypot agents, defenders can identify new attack categories and update detection signatures before these techniques are deployed against production agents. The formal framework from Part 1 provides a natural basis for honeypot design: a honeypot agent can advertise artificially high trust values or intentionally weak belief validation to attract trust exploitation and belief manipulation attempts.

Finally, establishing formal safety margins for bounded detection degradation would allow practitioners to predict the window of effectiveness for a given defense configuration. If the expected degradation rate can be bounded, organizations can proactively schedule defense updates before detection rates fall below acceptable thresholds.

### Collective Invariants for Large-Scale Agent Populations

As multiagent systems scale beyond the 3--10 agent range evaluated in this paper, emergent collective behaviors become both a powerful capability and a significant security concern. Agent collectives may develop communication patterns, specialization strategies, or coordination protocols that were not explicitly programmed---some beneficial, others potentially indicating compromise.

Three concrete research directions address this challenge. First, *collective invariants* extend CIF's per-agent behavioral invariants to population-level properties: for example, requiring that the entropy of the agent interaction graph remains within bounds (sudden decreases may indicate covert channel formation) or that the distribution of trust scores across the population does not become bimodal (which may indicate faction formation by compromised agents). Second, *emergent behavior fingerprinting* applies graph-theoretic anomaly detection to the evolving agent interaction network, flagging topological changes (new cliques, bridge nodes, spectral gap shifts) that correlate with coordination attacks in our corpus. Third, *safe emergence boundaries* formalize the conditions under which emergent behaviors preserve CIF's integrity guarantees---for instance, proving that if individual agents satisfy trust boundedness (Part 1, Theorem 4.2), then any emergent coordination pattern among honest agents also satisfies bounded collective trust, regardless of the specific strategy that emerges.

These directions connect CIF to the broader complex systems literature and address the gap between individual-agent security (well-characterized by our current results) and population-level security (an open problem as agent counts grow).

### Federated Trust Across Organizational Boundaries

Current CIF deployment assumes a single operator controlling all agents within a trust domain. As multiagent systems increasingly span organizational boundaries---for example, when an enterprise agent collaborates with agents operated by partners, vendors, or customers---federated trust management becomes essential.

Federated trust across organizational boundaries requires protocols for establishing, communicating, and decaying trust between agents that do not share a common trust authority. The trust calculus from Part 1 provides the mathematical foundation, but practical federation requires additional mechanisms for trust bootstrapping, cross-domain attestation, and handling trust domain conflicts. Cross-system provenance verification presents complementary challenges: verifying the provenance of information that has passed through agents outside one's trust domain requires cryptographic techniques (such as verifiable credentials or zero-knowledge proofs) that go beyond CIF's current provenance tracking. Regulatory compliance adds a further dimension, as different jurisdictions impose varying requirements on AI agent autonomy, data handling, and accountability. A federated CIF deployment must accommodate these constraints while maintaining coherent security guarantees across the federation.
