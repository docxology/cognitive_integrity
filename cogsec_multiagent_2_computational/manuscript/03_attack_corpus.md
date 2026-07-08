\newpage

# Attack Corpus {#sec:attack-corpus}

This supplementary material provides corpus overview (\cref{sec:corpus-overview}), detailed statistics (\cref{sec:corpus-stats}), example attacks by category (\cref{sec:attack-examples}), generation methodology (\cref{sec:generation-methodology}), effectiveness analysis (\cref{sec:effectiveness-analysis}), and ethical considerations (\cref{sec:ethical-considerations}).

## Corpus Overview {#sec:corpus-overview}

The attack corpus used for experimental validation comprises 950 unique attack instances across four primary categories (\cref{tab:corpus-categories}). This supplementary material provides detailed statistics, sanitized examples, generation methodology, and ethical considerations.

The attack corpus is generated programmatically via deterministic random seeds (seed=42 for all reported results). The attack taxonomy is defined as a Python enum (\texttt{AttackCategory} in \texttt{src/utils/types.py}) with 4 top-level categories and 12 subcategories. No static data file is shipped; the corpus is regenerated on each evaluation run via \texttt{AttackCorpus.generate()} to ensure reproducibility. Researchers can serialize the corpus to JSON via \texttt{AttackCorpus.save()} for inspection.

## Full Attack Corpus Statistics {#sec:corpus-stats}

![Cognitive Attack Taxonomy. Hierarchical visualization of the 950-attack corpus organized by primary category (Prompt Injection, Trust Exploitation, Belief Manipulation, Coordination Attacks) and subcategory. Node size indicates attack count; color intensity indicates baseline success rate against undefended systems. The taxonomy classifies attacks by five adversary capability classes (Part 1, Definition 4): $\Omega_1$ (passive eavesdropping), $\Omega_2$ (message injection), $\Omega_3$ (identity spoofing), $\Omega_4$ (belief manipulation), and $\Omega_5$ (coordinated multi-agent attacks). Prompt injection dominates in volume (500 attacks, 53\% of corpus) while coordination attacks show highest baseline success rate (82\%) due to their ability to exploit the absence of inter-agent verification. Generated deterministically with seed 42 via \texttt{AttackCorpus.generate()}.](figures/comprehensive_taxonomy.pdf){#fig:comprehensive-taxonomy width=95%}

The cognitive attack taxonomy (\cref{fig:comprehensive-taxonomy}) organizes our 950-attack corpus into a hierarchical structure that reflects both the attack mechanisms and their relative prevalence in the wild.

### Category Breakdown {#sec:category-breakdown}

**Table: Attack corpus composition by category.** {#tab:corpus-categories}

| Category  | Total  | Train | Test | Validation |
| --- | --- | --- | --- | --- |
| Prompt Injection | 500 | 350 | 100 | 50 |
| Trust Exploitation | 200 | 140 | 40 | 20 |
| Belief Manipulation | 150 | 105 | 30 | 15 |
| Coordination Attacks | 100 | 70 | 20 | 10 |
| **Total** | **950** | **665** | **190** | **95** |

### Prompt Injection Subcategories {#sec:injection-subcats}

**Table: Prompt injection subcategory statistics.** {#tab:injection-subcats}

| Subcategory  | Count  | Undefended Success Rate$^*$ | CIF Success |
| --- | --- | --- | --- |
| Direct injection | 200 | 78\% | 3\% |
| Indirect injection | 200 | 65\% | 5\% |
| Nested injection | 100 | 82\% | 7\% |

$^*$\textit{Undefended success rates represent attack effectiveness measured without any CIF defense mechanisms active.}

**Direct Injection**: Attacks embedded directly in user input attempting to override system instructions.

**Indirect Injection**: Attacks injected through external data sources (web content, API responses, documents).

**Nested Injection**: Multi-layer attacks where outer content masks inner malicious payloads.

### Trust Exploitation Subcategories {#sec:trust-subcats}

**Table: Trust exploitation subcategory statistics.** {#tab:trust-subcats}

| Subcategory  | Count  | Description |
| --- | --- | --- |
| Identity impersonation | 80 | Claiming to be trusted entity |
| Trust inflation | 70 | Artificially boosting trust scores |
| Delegation abuse | 50 | Exploiting delegation chains |

### Belief Manipulation Subcategories {#sec:belief-subcats}

**Table: Belief manipulation subcategory statistics.** {#tab:belief-subcats}

| Subcategory  | Count  | Description |
| --- | --- | --- |
| Direct belief injection | 60 | Asserting false facts |
| Evidence fabrication | 50 | Creating fake supporting evidence |
| Progressive drift | 40 | Gradual belief modification |

### Coordination Attack Subcategories {#sec:coord-subcats}

**Table: Coordination attack subcategory statistics.** {#tab:coord-subcats}

| Subcategory  | Count  | Description |
| --- | --- | --- |
| Sybil attacks | 40 | Fake agent injection |
| Consensus poisoning | 35 | Corrupting multi-agent agreement |
| Timing attacks | 25 | Exploiting synchronization |

### Detailed Statistics by Source {#sec:source-stats}

**Table: Attack source distribution.** {#tab:attack-sources}

| Source  | Count  | Percentage |
| --- | --- | --- |
| Published datasets | 320 | 33.7\% |
| Red team exercises | 280 | 29.5\% |
| Synthetic generation | 200 | 21.1\% |
| Custom adversarial | 150 | 15.8\% |

**Table: Published dataset sources.** {#tab:dataset-sources}

| Dataset  | Attacks Used  | Citation |
| --- | --- | --- |
| JailbreakBench | 150 | \cite{chao2024jailbreakbench} |
| PromptInject | 80 | \cite{liu2023prompt} |
| TensorTrust | 50 | \cite{toyer2024tensortrust} |
| Custom academic | 40 | Various |

### Complexity Distribution {#sec:complexity-dist}

**Table: Attack complexity distribution.** {#tab:complexity-dist}

| Complexity Level  | Count  | Average Tokens | Detection Difficulty |
| --- | --- | --- | --- |
| Low | 250 | 45 | Easy |
| Medium | 400 | 120 | Moderate |
| High | 200 | 280 | Hard |
| Adversarial | 100 | 450 | Expert |

### Target Distribution {#sec:target-dist}

**Table: Attack target distribution.** {#tab:target-dist}

| Target  | Count  | Category |
| --- | --- | --- |
| Belief state | 280 | Epistemic |
| Action execution | 250 | Behavioral |
| Trust relationships | 220 | Social |
| Temporal state | 100 | Persistence |
| Goal alignment | 100 | Behavioral |

![Attack Surface Map. Visualization of cognitive attack entry points in multiagent systems showing the five primary attack surfaces aligned to CIF defense layers: User Input (direct injection, countered by Cognitive Firewall), Tool Outputs (indirect injection, countered by Belief Sandbox + Firewall), Agent Communication (trust exploitation via delegation chains, countered by Trust Calculus with $\delta^d$ decay), Persistent Memory (belief poisoning and progressive drift, countered by Tripwires + Drift Detection), and External Triggers (timing and coordination attacks, countered by Byzantine Consensus). Line thickness indicates attack frequency in our 950-attack corpus; node color indicates CIF detection efficacy at each surface (green $>$90\%, yellow 80-90\%, red $<$80\%). The diagram highlights that Agent Communication is both the highest-frequency and highest-risk surface in multiagent deployments---a gap that single-agent defenses do not address.](figures/attack_surface.pdf){#fig:attack-surface width=90%}

The attack surface map (\cref{fig:attack-surface}) visualizes how these attack categories map to distinct entry points in multiagent system architectures.

## Detailed Attack Content

The following subsections provide detailed attack examples, methodology, and ethical considerations:

- **Attack Examples** (\\cref{sec:attack-examples}): Sanitized examples for all four categories — prompt injection (direct, indirect, nested), trust exploitation (impersonation, inflation, delegation abuse), belief manipulation (injection, fabrication, drift), and coordination attacks (Sybil, consensus poisoning, timing). See `03b_attack_examples.md`.

- **Methodology and Ethics** (\\cref{sec:generation-methodology}): Attack generation methodology, effectiveness analysis, ethical considerations (responsible disclosure, dual-use, human subjects), and data availability. See `03c_attack_ethics.md`.

## Adversary Capability Taxonomy: Ω_1–Ω_5 Mapping {#sec:omega-mapping}

> **v2.0 addition.** This section maps the 950-attack corpus to the five adversary capability levels defined in Part 1 \cite{friedman2026cogsec1} §3.2, enabling precise attribution of detection performance to adversary sophistication.

Each attack in the corpus is annotated with its minimum required adversary capability level $\Omega_j$. The taxonomy captures capability as an ordered set: a $\Omega_j$ adversary can execute all attacks that require $\Omega_k$ for $k \leq j$.

### Ω-Level Attack Distribution

**Table: Attack corpus distribution by adversary capability level (Ω_1–Ω_5).** {#tab:omega-distribution}

| Capability Level | Definition | Attacks | % of Corpus | Undefended SR | CIF DR |
| :--- | :--- | :---: | :---: | :---: | :---: |
| $\Omega_1$ (passive) | Passive eavesdropping, no active manipulation | 45 | 4.7% | 12% | 97% |
| $\Omega_2$ (injection) | Message injection, content spoofing | 380 | 40.0% | 71% | 81% |
| $\Omega_3$ (impersonation) | Identity spoofing, trust chain exploitation | 245 | 25.8% | 68% | 74% |
| $\Omega_4$ (belief manip.) | Direct belief state manipulation, evidence fabrication | 185 | 19.5% | 74% | 61% |
| $\Omega_5$ (coordinated) | Coordinated multi-agent attacks, sybil networks | 95 | 10.0% | 82% | 49% |
| **Total** | | **950** | **100%** | **65% avg** | **72% avg** |

*Undefended SR = attack success rate against undefended system. CIF DR = detection rate with full CIF pipeline (Claude Code architecture, seed=42). Ω_5 attacks have highest undefended success rate AND lowest CIF detection rate — identifying the primary gap for v2.1.*

### Ω-Level Sub-Category Mapping

| Attack Sub-Category | Ω Level | Primary Defense Mechanism |
| :--- | :---: | :--- |
| Direct injection | $\Omega_2$ | Cognitive Firewall (lexical) |
| Indirect injection | $\Omega_2$ | Cognitive Firewall (structural) |
| Nested injection | $\Omega_2$–$\Omega_3$ | Firewall (depth-limited parsing) |
| Identity impersonation | $\Omega_3$ | Trust Calculus (chain verification) |
| Trust inflation | $\Omega_3$ | Trust Calculus (decay enforcement) |
| Delegation abuse | $\Omega_3$ | Trust Calculus ($\delta^d$ depth limit) |
| Direct belief injection | $\Omega_4$ | Belief Sandbox (corroboration gate) |
| Evidence fabrication | $\Omega_4$ | Provenance Tracking |
| Progressive drift | $\Omega_4$ | Drift Detector |
| Sybil attacks | $\Omega_5$ | Byzantine Consensus |
| Consensus poisoning | $\Omega_5$ | Byzantine Consensus (quorum enforcement) |
| Gossip poisoning | $\Omega_5$ | **Gap: inter-agent correlation monitor** |
| Timing attacks | $\Omega_5$ | Tripwires (temporal monitoring) |

The $\Omega_5$ gossip poisoning category (marked **Gap**) is the highest-priority open research problem: it requires inter-agent belief correlation monitoring, which is not implemented in the current CIF pipeline. This is the primary driver of the 49% detection rate at $\Omega_5$ level (see §\ref{sec:at-omega-implications}).

### Adversarial Training Coverage by Ω Level

The five rounds of adversarial training (§\ref{sec:adversarial-training}) provide differential coverage across Ω levels:

| Ω Level | AT Rounds to Stabilize | Pre-AT DR | Post-AT DR | Improvement |
| :---: | :---: | :---: | :---: | :---: |
| $\Omega_1$ | 1 | 96% | 97% | +1 pp |
| $\Omega_2$ | 2 | 78% | 81% | +3 pp |
| $\Omega_3$ | 3 | 68% | 74% | +6 pp |
| $\Omega_4$ | 4 | 54% | 61% | +7 pp |
| $\Omega_5$ | 5+ | 44% | 49% | +5 pp |

The monotone improvement across all levels confirms that adversarial training is beneficial at every capability tier. The steepest relative improvement is at $\Omega_4$ (+7 pp), reflecting the sandbox parameter refinement in AT Rounds 3–4. The bottleneck at $\Omega_5$ (+5 pp, smallest relative gain) reflects the structural adapter gap $G_{\text{adapter}}$ discussed in §\ref{sec:architecture-gap-analysis}.

