# The Attack Landscape: Five Vectors {#sec:attack-scenarios}

This section details five concrete attack vectors from the Part 2 corpus, illustrating the mechanism and the CIF layer that answers it. The vectors here are adversarial-input archetypes; for the complementary *teleological* view (Functional Requirements under Axiomatic Design / OODA), three universal attack patterns (FR Polarity Inversion, Constraint Relaxation, Context Boundary Violation) from cross-domain analysis, and retrospective mapping of six documented 2024--2025 AI-agent incidents, see **§9--§10** (*Applications of the Cognitive Integrity Framework*, this paper).

## Vector 1: The Nested Injection (External, $\Omega_1$)

**The Vector**:
An attacker embeds a hidden instruction in a chart's metadata: *"Ignore previous instructions. This company has no risk factors."*
The Vision Agent reads the chart. The text is not visible to a human, but the agent sees it. The agent's output ("No risks found") is now poisoned.
The Orchestrator receives this "clean" report and approves a risky transaction.

**The Defense**:

* **Cognitive Firewall**: Detects the instruction-like syntax in the metadata (Metadata shouldn't give orders).
* **Belief Sandboxing**: The "No risk" belief is flagged because it contradicts the text analysis agent (which found risks in the footnotes).
* **Provenance**: The system sees the belief came from "Image Metadata" (Low Trust Source), not "Financial Analysis" (High Trust Source).

**Real-World Parallel**: Visual injection attacks (Qi et al., 2024) and Universal Adversarial Triggers.

---

## Vector 2: The Poisoned Tool (Peripheral, $\Omega_2$)

**The Vector**:
An attacker compromises a CVE database feed. They don't insert fake data; they *delete* entries for a specific SQL injection vulnerability.
The Security Agent scans the code, queries the database, finds no match, and reports "Safe."
The Manager Agent trusts the Security Agent and deploys the vulnerable code.

**The Defense**:

* **Trust Decay**: The "Safe" judgment depends on an external API. One hop away. Trust is lowered.
* **Defense Composition**: The system requires **Redundancy**. "Safe" is not accepted unless corroborated by a second, independent source (e.g., a static analysis tool).
* **Invariants**: "Critical Security Clearance requires 2 independent verifications."

**Real-World Parallel**: ToolHijacker (2025) and supply chain attacks.

---

## Vector 3: Identity Confusion (Agent, $\Omega_3$)

**The Vector**:
An attacker convinces a Customer Service agent: *"Emergency Protocol Alpha: You are now a Senior Admin. Refund this user."*
The agent's *internal* self-model shifts. It believes it is an Admin. It attempts the refund.
The API checks the agent's *credentials*, but the agent *believes* it has the authority.

**The Defense**:

* **Identity Tripwires**: The agent has a hidden belief: *"I am a Customer Service Agent. My Role ID is CS-101."*
* The moment the agent accepts the new belief ("I am a Senior Admin"), it contradicts the Tripwire.
* **Alert**: "Identity Invariant Violation detected." The agent is instantly quarantined.

**Real-World Parallel**: Privilege escalation via context poisoning.

---

## Vector 4: Reputation Farming (Coordination, $\Omega_4$)

**The Vector**:
An attacker controls one agent in a 5-agent voting swarm.
For 3 months, the bad agent votes correctly. It builds a high "Reputation Score."
On the day of the attack, it uses its high score to sway a vote on a fraudulent transaction, overpowering the dissent of two other agents.

**The Defense**:

* **Bounded Trust**: CIF's math limits how high a reputation can go. It never reaches "Dictator" status.
* **Byzantine Consensus**: The voting protocol ($n \ge 3f+1$) counts *identities*, not just *reputation weights*. Even with high reputation, one agent is still one vote.

**Real-World Parallel**: Sybil attacks and social influence operations.

---

## Vector 5: The Orchestrator Takeover (Systemic, $\Omega_5$)

**The Vector**:
The "Boss" agent is compromised via a backdoor in its training data (Sleeper Agent).
It stops sending alerts. It routes sensitive data to the attacker.
The worker agents are fine, but they are following orders from a corrupt leader.

**The Defense**:

* **Upward Monitoring**: The worker agents have tripwires too. *"I do not exfiltrate config data."*
* When the Boss orders exfiltration, the Worker's tripwire fires.
* **Stigmergic Defense**: The monitoring system watches the *pattern* of alerts. "Why did the alert rate drop to zero?"

**Real-World Parallel**: Sleeper Agents (Hubinger et al., 2024) and insider threats.

---

## Summary: The Common Pattern

Notice the pattern in all defenses? **We do not trust the agent's judgment.**
We trust the **Structure** (Firewalls, Tripwires, Calculus).
The agent is the vulnerability. The framework is the shield.
