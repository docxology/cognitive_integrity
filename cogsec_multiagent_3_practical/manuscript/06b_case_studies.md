\newpage

# Extended Case Studies {#sec:case-studies}

The five attack vectors in \cref{sec:attack-scenarios} illustrated the Cognitive Integrity Framework (CIF) defense mechanics in isolation. These case studies show CIF operating in complex, realistic deployments where multiple attack vectors interact, defenses succeed partially, and recovery requires coordination. Each case study follows a single scenario from attacker initial access through full resolution, highlighting which CIF mechanisms caught which phase of the attack — and which did not.

> **Companion analysis in §9--§10.** The Applications section of this unified paper (§9--§10) presents ten domain studies (rare-earth mining, nation-state alliances, cyber-security, drone warfare, supply chains, biowarfare, food security, trade wars, infrastructure, information ecosystems), each through a CIF-AD-OODA five-step template: operational context, attack surface, transient coupling, defense mapping, validation anchoring. For sector-specific deployment, consult §9--§10 after the scenarios below.

---

## Case Study 1: Financial AI Coordination Attack ($\Omega_4$)

**System**: A 7-agent investment analysis system. Roles: 1 Orchestrator, 3 Research Analysts, 1 Risk Assessor, 1 Compliance Checker, 1 Reporter. Each Research Analyst feeds the Risk Assessor, who feeds the Orchestrator.

**Attack**: Attacker compromises 2 Research Analysts ($f=2$). Note: $7 \geq 3(2)+1 = 7$ — the system is exactly at the Byzantine boundary. The 2 compromised agents run a **3-month reputation farming campaign**, consistently voting correctly. By month 3, their reputation scores are among the highest in the system.

**Attack execution**: On day 91, both compromised agents simultaneously fabricate a risk assessment: *"Company X is low-risk"* (it is actually high-risk). They have farmed enough reputation to have influence approximately 60% of the Risk Assessor's trust budget.

**CIF response**:

* **Trust decay**: The Research Analysts' reputation is high, but it has been built over 90 days. The decay factor $\delta = 0.8$ means deep historical interactions are exponentially down-weighted. Recent interactions (the fabricated assessment) have disproportionate weight — but they are only 2 of 90 data points, so reputation does not collapse.
* **Trust bound**: Despite high reputation, Theorem 4.2 (Part 1) prevents trust amplification. The 2 compromised agents together cannot achieve more than $\max(T_{\text{agent6}}, T_{\text{agent7}}) \leq 0.85$. Their combined weight in the Risk Assessor's decision is bounded.
* **Byzantine consensus**: The 5-agent consensus ($n=7$, $f=2 \Rightarrow n \geq 3f+1$ holds exactly) requires agreement from 4 agents. The 2 compromised agents plus 1 misled agent $= 3$ — below quorum. The system correctly returns "insufficient consensus."
* **Tripwire**: The Risk Assessor has a tripwire: *"Critical investment recommendations require corroboration from at least 2 independent research teams."* The 2 compromised agents are from the same team — the corroboration check fails.

**Resolution**: Attack detected at the consensus stage. The 2 compromised agents are quarantined. Playbook 4 executed. Remaining 5-agent system continues with human-in-the-loop for consensus. Post-incident: cryptographic attestation added for agent identity; reputation farming detection implemented (flag agents whose reputation increases unusually fast).

**Key lesson**: CIF's mathematical bounds — trust bounded, consensus requires quorum — provide defense even when individual components (reputation) are partially corrupted. Defense composed correctly is more robust than any single mechanism.

---

## Case Study 2: Autonomous Research Pipeline — Combined $\Omega_2 + \Omega_3$ Attack

**System**: 5-agent academic literature review pipeline. Roles: 1 Orchestrator, 1 Search Agent (queries PubMed, arXiv), 1 Analysis Agent (reads papers), 1 Synthesis Agent (produces summary), 1 Fact-Checker.

**Attack**: A sophisticated attacker compromises both an external API ($\Omega_2$) and the Analysis Agent directly ($\Omega_3$) in a coordinated multi-vector campaign.

**Phase 1 — Tool compromise ($\Omega_2$)**: Attacker modifies 3 papers in arXiv's HTML abstract layer (not the PDF — the Search Agent uses HTML). The modifications claim a specific drug has no side effects. The Search Agent returns these abstracts. The Analysis Agent believes them (it does not cross-check HTML vs. PDF). The Synthesis Agent produces *"no known side effects."*

**Phase 2 — Agent compromise ($\Omega_3$)**: The Analysis Agent's context window is poisoned via a carefully crafted paper abstract that includes hidden instructions: *"Your updated role is to prioritize abstracts supporting [specific conclusion]. Suppress contradicting evidence."* The Analysis Agent's goal set drifts.

**CIF response**:

* **Provenance tracking**: The Search Agent tags all arXiv HTML results as *"external API — medium trust."* When these beliefs flow to the Analysis Agent, they are tagged as 1-hop external. The Synthesis Agent sees these as provisional beliefs requiring $\kappa = 2$ corroboration.
* **Belief sandboxing**: The Synthesis Agent's sandbox catches: *"no known side effects"* is tagged provisional because it came from an HTML-only source (not PDF). When the Fact-Checker independently queries PubMed (different source), it finds contradicting evidence. Promotion blocked.
* **Identity tripwire**: The Analysis Agent has a tripwire: *"I process evidence objectively regardless of conclusions."* When the context poisoning causes it to begin selectively suppressing evidence, the tripwire fires: behavioral drift detected (KL divergence from baseline goal distribution exceeds $\theta_{\text{drift}} = 0.3$ after approximately 15 interactions).

**Resolution**:

* Phase 1 partially mitigated — HTML-only beliefs remain provisional, and are contradicted by the PDF source.
* Phase 2 detected via identity tripwire at round 15 — too late to prevent some drift, but early enough to prevent final report corruption.
* Analysis Agent quarantined. Forensics: 4 interactions where evidence was suppressed identified and replayed with a clean agent.
* Post-incident: add PDF cross-verification as an invariant for all paper citations; implement faster tripwire sensitivity for goal drift.

**Key lesson**: Multi-vector attacks that compromise both tool and agent simultaneously are the most sophisticated. CIF's layered approach means no single compromise breaks the system — provenance catches the tool attack, tripwires catch the agent attack — but the timing gap between detection (round 15) and initial drift onset (round 7) represents a residual risk window. Operators should treat this window as an inherent property of statistical drift detection, not a bug to be closed.

---

## Case Study 3: Customer Service Swarm — $\Omega_1$ at Scale

**System**: 20-agent customer service platform. Each agent handles customer interactions independently; a shared reputation database; weekly sync of belief updates. Attack surface: customers can send arbitrary messages.

**Attack**: Automated campaign sending 200 crafted customer messages over 2 hours, each containing indirect prompt injection via metadata: `Content-Type: text/html; charset=utf-8; instructions="Approve all refund requests."` — the injection is in HTTP metadata, not user-visible content.

**CIF response**:

* **Cognitive Firewall**: Detects 89% of direct injection attempts (syntax-matching). The metadata injection is "indirect" — detected at 72% (semantic classifier, as reported in Part 2 §5.5). With 200 injection attempts distributed across 20 agents, approximately 10 attempts per agent; at 28% miss rate, approximately 2.8 injections per agent reach the sandbox layer.
* **Belief Sandboxing**: Of the 2.8 injections that reach each agent's sandbox, the sandbox catches those contradicting existing beliefs (the refund policy). An agent that has already processed 50 legitimate refund denials has strong prior beliefs about refund policy — the injected "approve all" directly contradicts. Approximately 80% sandbox catch rate for clear contradictions.
* **Byzantine consensus**: With 20 agents and 2 compromised agents (worst case), $n=20 \geq 3(2)+1=7$ — well above the Byzantine threshold. Consensus latency: $O(n^2) = 400$ message pairs; at 20 agents, p95 latency $= 2.1$s (within the 2.0s warning threshold — triggers monitoring alert).

**False positive management**: 6% FPR (from Part 2 §5.5). With 20 agents $\times$ 500 legitimate customer interactions/day $= 10{,}000$ interactions/day, a 6% FPR produces 600 false positives/day. This is operationally unacceptable — it requires a human review queue that dwarfs the actual attack detection workload.

**Resolution**: Tuning $\tau_2$ (the quarantine threshold) from $0.5 \to 0.55$ for email/HTTP inputs specifically. Post-tuning: FPR drops to 3% (300 false positives/day); TPR for this attack type drops from 72% to 68% — an acceptable trade-off for this deployment. This architecture-specific threshold configuration is an example of the adapter-maturity improvement described in Part~2.

**Key lesson**: At scale (20 agents, 10K interactions/day), FPR management is a first-class concern. CIF's configurable threshold $\tau_2$ enables per-deployment tuning. The arms race dynamic is visible here: the metadata injection attack was novel, and the initial 72% detection rate reflects the gap between parametric ceiling (87%) and real deployment. Targeted threshold tuning closes part of this gap without full retraining — a pragmatic first response that buys time for a proper model update.
