\newpage

# Related Work {#sec:related-work}

CIF builds on and extends several research traditions. We position our contributions relative to the most closely related work in each area, highlighting both the foundations we draw upon and the novel elements that distinguish our approach.

## Prompt Injection Defenses

The growing body of work on prompt injection defenses has largely focused on single-agent scenarios. Greshake et al.\ \cite{greshake2023indirect} demonstrated indirect prompt injection through tool outputs in LLM-integrated applications, revealing how malicious content in retrieved documents can hijack agent behavior. Perez and Ribeiro \cite{perez2023hackaprompt} characterized injection vulnerabilities through large-scale competitive testing, establishing benchmark datasets for injection detection. Liu et al.\ \cite{liu2023prompt} provided a taxonomy of injection attacks against LLM applications, categorizing techniques by attack vector and target. More recently, the *Prompt Infection* paradigm \cite{lee2025promptinfection} has demonstrated that injections can self-replicate across LLM agents: a compromised agent's output embeds injection payloads that propagate to downstream agents, creating epidemic-like attack cascades that single-agent defenses cannot contain. This LLM-to-LLM propagation vector directly motivates CIF's inter-agent provenance tracking and trust decay mechanisms.

Commercial tools including Rebuff,\footnote{\url{<https://github.com/protectai/rebuff}}> NVIDIA's NeMo Guardrails \cite{rebedea2023nemo}, Lakera Guard,\footnote{\url{<https://www.lakera.ai/}}> and LLM Guard\footnote{\url{<https://llm-guard.com/}}> offer production-grade input filtering for single-agent deployments. These tools employ TF-IDF classifiers, embedding-based similarity detection, and rule-based pattern matching to identify malicious inputs before they reach the underlying language model. Chen et al.\ \cite{multiagent2025defense} propose using multiple LLM agents cooperatively to detect injections---an approach complementary to CIF's defense-in-depth strategy. Structured-query defenses such as StruQ \cite{struq2025} separate user data from instructions at the protocol level, but assume a single trust boundary and do not address inter-agent delegation.

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

Several concurrent developments complement CIF's contributions. The OWASP Top 10 for Agentic Applications (2026) \cite{owasp2025agentic} identifies ten risk categories for agentic AI systems, four of which directly correspond to CIF's defense mechanisms: ASI01 (Agent Goal Hijack) maps to CIF's cognitive firewall and tripwire detection; ASI06 (Memory and Context Poisoning) maps to belief sandboxing; ASI07 (Insecure Inter-Agent Communication) maps to provenance attestation and trust calculus; and ASI10 (Rogue Agents) maps to Byzantine consensus. The OWASP guidelines recommend zero-trust architecture, role-based access control, and human-in-the-loop checks---principles CIF operationalizes through formal trust bounds and automated enforcement. Microsoft's defense framework for indirect prompt injection \cite{microsoft2025indirect} and OpenAI's prompt injection analysis \cite{openai2025promptinjection} address single-agent scenarios; CIF extends these to inter-agent propagation. Chen et al.\ \cite{aiagentssurvey2025} survey AI agent security challenges broadly, identifying trust management and coordination security as open problems---precisely the gaps CIF addresses. Debenedetti et al.\ \cite{adaptive2025attacks} demonstrate that adaptive attacks break static defenses, motivating CIF's layered approach where bypassing one mechanism still encounters orthogonal detection layers.

Emerging zero-trust frameworks for agentic AI \cite{zerotrustagents2025} advocate treating every agent interaction as potentially compromised, requiring continuous verification of identity, intent, and authorization. CIF's trust calculus with $\delta^d$ decay provides a formal instantiation of this principle: trust is never assumed, is always bounded, and decays structurally with delegation depth. Industry practitioners have adopted simpler heuristics---Meta's ``Rule of Two'' limits delegation chain depth as a practical safeguard---but CIF supersedes such ad hoc measures with provable bounds on trust amplification and formally verified composition guarantees.

## Positioning of This Work

CIF's contribution is providing a unified, formally grounded defense framework addressing the full spectrum of cognitive attacks across diverse multiagent architectures. Where prior work addresses individual attack vectors, individual mechanisms, or individual system properties, CIF provides:

1. **Compositional defense algebra**: Formal theorems (Part 1) proving multiplicative detection guarantees for layered defenses
2. **Bounded delegation trust**: The first formally verified trust calculus for LLM agent systems with provable bounds on trust amplification
3. **Cross-architecture validation**: Empirical evidence that formal guarantees hold across four production architectures
4. **Complete attack taxonomy**: A 950-attack corpus spanning the full cognitive attack surface with reproducible generation

\Cref{tab:related-work-comparison} summarizes the key distinctions.

**Table: Comparison of CIF with related defense frameworks.** {#tab:related-work-comparison}

| Framework | Multiagent | Formal Guarantees | Trust Bounds | Attack Corpus | Architectures Tested |
| --- | --- | --- | --- | --- | --- |
| NeMo Guardrails \cite{rebedea2023nemo} | No | No | No | N/A | 1 |
| Lakera Guard | No | No | No | N/A | 1 |
| AgentScope \cite{gao2024agentscope} | Partial | No | No | No | 1 |
| Multi-Agent Defense \cite{multiagent2025defense} | Yes | No | No | Yes | 1 |
| Prompt Infection Defense \cite{lee2025promptinfection} | Partial | No | No | Yes | 1 |
| Zero-Trust Agents \cite{zerotrustagents2025} | Yes | No | Partial | No | 2 |
| OWASP Agentic \cite{owasp2025agentic} | Yes | No | No | No | N/A (guidelines) |
| **CIF (this work)** | **Yes** | **Yes** | **Yes ($\delta^d$)** | **Yes (950)** | **4** |
