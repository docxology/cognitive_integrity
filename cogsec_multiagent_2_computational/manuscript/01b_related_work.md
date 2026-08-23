\newpage

# Related Work {#sec:related-work}

CIF builds on and extends several research traditions. We position our contributions relative to the most closely related work in each area, highlighting both the foundations we draw upon and the novel elements that distinguish our approach.

## Prompt Injection Defenses

The growing body of work on prompt injection defenses has largely focused on single-agent scenarios. Greshake et al.\ \cite{greshake2023indirect} demonstrated indirect prompt injection through tool outputs in LLM-integrated applications, revealing how malicious content in retrieved documents can hijack agent behavior. Schulhoff et al.\ \cite{perez2023hackaprompt} characterized injection vulnerabilities through large-scale competitive testing, establishing benchmark datasets for injection detection. Liu et al.\ \cite{liu2023prompt} provided a taxonomy of injection attacks against LLM applications, categorizing techniques by attack vector and target. More recently, the *Prompt Infection* paradigm \cite{lee2025promptinfection} has demonstrated that injections can self-replicate across LLM agents: a compromised agent's output embeds injection payloads that propagate to downstream agents, creating epidemic-like attack cascades that single-agent defenses cannot contain. This LLM-to-LLM propagation vector directly motivates CIF's inter-agent provenance tracking and trust decay mechanisms.

Commercial tools including Rebuff,\footnote{\url{https://github.com/protectai/rebuff}} NVIDIA's NeMo Guardrails \cite{rebedea2023nemo}, Lakera Guard,\footnote{\url{https://www.lakera.ai/}} and LLM Guard\footnote{\url{https://llm-guard.com/}} offer production-grade input filtering for single-agent deployments. These tools employ TF-IDF classifiers, embedding-based similarity detection, and rule-based pattern matching to identify malicious inputs before they reach the underlying language model. Hossain et al.\ \cite{multiagent2025defense} propose using multiple LLM agents cooperatively to detect injections---an approach complementary to CIF's defense-in-depth strategy. Structured-query defenses such as StruQ \cite{struq2025} separate user data from instructions at the protocol level, but assume a single trust boundary and do not address inter-agent delegation.

CIF's cognitive firewall draws on similar classification techniques but extends the approach to inter-agent message channels, where injections may propagate through trusted delegation chains rather than arriving directly from user input. This distinction is critical: an injection that enters through a trusted agent's output bypasses user-facing filters entirely. CIF addresses this gap through layered defenses operating at every inter-agent boundary, combined with provenance attestation that tracks message origin through delegation chains.

## Byzantine Fault Tolerance

Classical BFT protocols \cite{lamport1982byzantine, dwork1988consensus} address crash and arbitrary faults in distributed systems. The foundational Byzantine Generals Problem established that consensus requires $n \geq 3f + 1$ participants to tolerate $f$ Byzantine faults. Practical implementations including PBFT \cite{castro1999practical} and modern variants (Tendermint \cite{buchman2016tendermint}, HotStuff \cite{yin2019hotstuff}) provide consensus guarantees under the assumption that faulty nodes behave arbitrarily, achieving throughput suitable for production deployments.

CIF's consensus mechanism adapts BFT principles to the specific domain of cognitive manipulation, where "Byzantine" behavior manifests as belief poisoning, trust inflation, and coordinated deception rather than message corruption or omission. The key distinction is that CIF's consensus operates on semantic content (beliefs, trust assertions) rather than transaction ordering, requiring detection mechanisms sensitive to subtle meaning manipulation rather than bit-level corruption.

## Trust and Reputation Systems

The trust management literature offers extensive frameworks for computing and propagating trust in distributed systems. J{\o}sang et al.\ \cite{josang2007survey} surveyed trust and reputation systems for online services, identifying common patterns and failure modes. The FIRE model \cite{huynh2006fire} combines multiple trust sources (direct interaction, witness information, role-based trust, certified reputation) into a unified framework. REGRET \cite{sabater2001regret} provides a decentralized reputation system that distinguishes individual, social, and ontological dimensions of trust.

CIF's trust calculus differs from these approaches in providing a formal bound on trust amplification through delegation chains ($\delta^d$ decay), which prevents the trust laundering attacks that are feasible in systems where transitive trust is unbounded. To our knowledge, CIF is the first framework to provide formally verified bounds on delegated trust in LLM-based agent systems, closing a gap between traditional trust systems (designed for human participants or simple software agents) and the unique challenges posed by language model agents.

## Multiagent Safety and Security

Recent work has begun addressing security in multiagent LLM systems specifically. The OWASP Top 10 for LLM Applications (2024) identifies prompt injection, insecure output handling, and excessive agency among the most critical risks but does not address inter-agent attack propagation or coordination attacks. AgentScope \cite{gao2024agentscope} provides agent development tools with basic safety constraints including sandboxed execution and permission systems. The CAMEL framework \cite{li2023camel} includes debate-based safety mechanisms for multiagent conversations but lacks formal security guarantees or provenance tracking.

LangChain and LangGraph offer guardrails for individual agent interactions, including input/output validation and tool permission systems, but do not provide the cross-agent trust and provenance tracking that CIF enables. AutoGPT and similar autonomous agent frameworks implement execution sandboxing but focus on preventing unintended actions rather than detecting cognitive manipulation.

## Concurrent and Recent Work

Several concurrent developments complement CIF's contributions. The OWASP Top 10 for Agentic Applications (2026) \cite{owasp2025agentic} identifies ten risk categories for agentic AI systems, four of which directly correspond to CIF's defense mechanisms: ASI01 (Agent Goal Hijack) maps to CIF's cognitive firewall and tripwire detection; ASI06 (Memory and Context Poisoning) maps to belief sandboxing; ASI07 (Insecure Inter-Agent Communication) maps to provenance attestation and trust calculus; and ASI10 (Rogue Agents) maps to Byzantine consensus. The OWASP guidelines recommend zero-trust architecture, role-based access control, and human-in-the-loop checks---principles CIF operationalizes through formal trust bounds and automated enforcement. Microsoft's defense framework for indirect prompt injection \cite{microsoft2025indirect} and OpenAI's prompt injection analysis \cite{openai2025promptinjection} address single-agent scenarios; CIF extends these to inter-agent propagation. Deng et al.\ \cite{aiagentssurvey2025} survey AI agent security challenges broadly, identifying trust management and coordination security as open problems---precisely the gaps CIF addresses. Debenedetti et al.\ \cite{adaptive2025attacks} demonstrate that adaptive attacks break static defenses, motivating CIF's layered approach where bypassing one mechanism still encounters orthogonal detection layers.

The zero-trust model \cite{nist2020zerotrust} grants no implicit trust on the basis of network location or asset ownership and enforces authentication and authorization per request; carried over to agentic systems, it treats every agent interaction as potentially compromised and requires continuous verification of identity, intent, and authorization. CIF's trust calculus with $\delta^d$ decay provides a formal instantiation of this principle: trust is never assumed, is always bounded, and decays structurally with delegation depth. Industry practitioners have adopted simpler heuristics---Meta's ``Rule of Two'' limits delegation chain depth as a practical safeguard---which CIF relates to explicit decay bounds and composition laws that can be stated and checked against deployment parameters.

## Information-Theoretic Security and Channel Capacity

The stealth-impact tradeoff formalized in Part 1 (Theorem 4: $I \cdot S \leq C_\text{channel}$) connects CIF to a rich tradition of information-theoretic security. Wyner's wiretap channel \cite{wyner1975wiretap} established that secure communication requires the eavesdropper's channel to be degraded relative to the legitimate receiver's; CIF's detection bound is the dual: an attacker's covert channel capacity bounds how much impact can be achieved while remaining below the detection threshold. Maurer's work on information-theoretic key agreement \cite{maurer1993secret} and Csiszár and Körner's channel coding theorems \cite{csiszar2011information} provide the foundational machinery; CIF applies these results to the novel setting of cognitive manipulation rather than physical-layer secrecy.

The information-geometric sharpening of Theorem 4 (Part 2, \cref{sec:information-geometry}) extends this to Riemannian geometry: in the space of belief distributions, the Fisher-Rao metric provides a natural measure of cognitive distance, and the curvature constraint (Theorem CG.1) bounds geodesic step size under any sandbox policy. Amari and Nagaoka \cite{amari2000methods} developed the information-geometric framework for statistical inference; Peters and Wierstra \cite{amari1998natural} applied the natural gradient to neural learning; CIF applies geodesic analysis to adversarial belief manipulation, establishing that each sandbox threshold $\kappa$ corresponds to a bounded geodesic radius $\rho = 2\arccos(\sqrt{1-\kappa\varepsilon})$.

## Category Theory in Machine Learning

Category-theoretic approaches to machine learning have matured significantly in recent years. Fong and Spivak's \textit{Seven Sketches in Compositionality} \cite{fong2019seven} established a compositional vocabulary for open systems; Cruttwell et al.'s categorical framework for gradient-based learning \cite{cruttwell2022categorical} demonstrated that backpropagation is a functor; and Hedges' compositional game theory \cite{hedges2018morphisms} provided categorical foundations for strategic interaction. These works demonstrate that categorical thinking is not merely aesthetic but yields concrete technical results through the discipline of functorial composition.

CIF's DefenseCategory (Part 2, \cref{sec:composability-algebra}) applies this tradition to security: defense mechanisms are morphisms in a category where objects are cognitive states and composition is short-circuit (detection-preserving). Theorems CT.1--CT.3 prove that this structure satisfies categorical laws, which in turn recovers the series detection formula (Part 1's Series Detection Rate theorem) as a categorical consequence rather than an independent result. To our knowledge, CIF is the first cognitive-security framing of multiagent LLM defenses presented in this categorical form.

## Free Energy Principle and Active Inference

The Free Energy Principle (FEP) \cite{friston2010free, friston2023simpler} proposes that biological agents minimize variational free energy $F = D_\text{KL}[Q \| P] - \mathbb{E}_Q[\log P(o|s)]$ as a unified account of perception, action, and learning. Karl Friston's active inference framework \cite{friston2017active} extends this to sequential decision-making, where agents select actions to minimize expected free energy over future observations. Da Costa et al.\ \cite{dacosta2020active} formalize the relationship between active inference and classical reinforcement learning; Parr and Friston \cite{parr2019neuronal} show how precision (inverse variance) of beliefs modulates the influence of messages on inference.

CIF's connection to active inference (Part 2, \cref{sec:theoretical-connections}) is structural: the trust calculus's $\delta^d$ decay corresponds to precision weighting in a hierarchical generative model, where trusted agents provide high-precision observations and trust decay with delegation depth mirrors the precision attenuation of distal sensory channels. FEP.1--FEP.2 formalize this: CIF detects attacks as free energy increases ($\Delta F(\omega) > \kappa_\text{FEP}$) and the belief sandbox as constrained variational inference. This connection provides an interpretive bridge between CIF's formal mechanisms and the broader computational neuroscience literature, suggesting that secure multiagent systems and healthy biological cognition share deep structural principles.

## Positioning of This Work

CIF's contribution is providing a unified, formally grounded defense framework addressing the full spectrum of cognitive attacks across diverse multiagent architectures. Where prior work addresses individual attack vectors, individual mechanisms, or individual system properties, CIF provides:

1. **Compositional defense algebra**: Formal theorems (Part 1) proving multiplicative detection guarantees for layered defenses
2. **Bounded delegation trust**: The first formally verified trust calculus for LLM agent systems with provable bounds on trust amplification
3. **Cross-architecture validation**: Empirical evidence that formal guarantees hold across four production architectures
4. **Complete attack taxonomy**: A 950-attack corpus spanning the full cognitive attack surface with reproducible generation
5. **Categorical composition laws**: Category-theoretic formalization (CT.1--CT.3) tying series/parallel detection formulas to functorial composition under the short-circuit semantics (\cref{sec:composability-algebra}); composed behaviors that contradict those laws fall outside the modeled pipeline
6. **FEP-grounded trust precision**: Formal connection between CIF's trust calculus and active inference's precision weighting, giving a variational reading of trust decay and sandboxing and linking to the broader FEP literature (\cref{sec:theoretical-connections})
7. **Information-geometric adversarial geometry**: Formalization of attacks as geodesic paths in the Fisher-Rao manifold of belief distributions, providing a Riemannian metric on cognitive manipulation and enabling geometry-based defense certification (\cref{sec:information-geometry})

\Cref{tab:related-work-comparison} summarizes the key distinctions.

Table: Comparison of CIF with related defense frameworks. {#tab:related-work-comparison}

| Framework | Multiagent | Formal Guarantees | Trust Bounds | Attack Corpus | Architectures Tested | Category-Theoretic | FEP-Grounded |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NeMo Guardrails \cite{rebedea2023nemo} | No | No | No | N/A | 1 | No | No |
| Lakera Guard | No | No | No | N/A | 1 | No | No |
| AgentScope \cite{gao2024agentscope} | Partial | No | No | No | 1 | No | No |
| Multi-Agent Defense \cite{multiagent2025defense} | Yes | No | No | Yes | 1 | No | No |
| Prompt Infection Defense \cite{lee2025promptinfection} | Partial | No | No | Yes | 1 | No | No |
| OWASP Agentic \cite{owasp2025agentic} | Yes | No | No | No | N/A (guidelines) | No | No |
| Category-Theoretic ML \cite{cruttwell2022categorical} | No | Yes | No | No | N/A | Yes | No |
| Active Inference / FEP \cite{friston2023simpler} | Partial | Yes | Partial | No | N/A | No | Yes |
| Info-Geometric Methods \cite{amari2000methods} | No | Yes | No | No | N/A | No | Partial |
| **CIF (this work)** | **Yes** | **Yes** | **Yes ($\delta^d$)** | **Yes (950)** | **4** | **Yes (CT.1--3)** | **Yes (FEP.1--2)** |
