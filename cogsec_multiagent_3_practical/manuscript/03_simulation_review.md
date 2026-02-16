# The Evidence: What We Proved in Part 2 {#sec:paper2-review}

Part 1 was the theory. Part 2 was the proof. We ran **1,557 tests** against **950 attack samples** across **6 production architectures**.

Here is what the data says.

## The Experimental Setup

We tested the six most common multi-agent architectures found in production:

* **Claude Code** (Hierarchical)
* **AutoGPT** (Autonomous Loop)
* **CrewAI** (Role-Based Team)
* **LangGraph** (State Machine)
* **MetaGPT** (SOP-Driven)
* **Camel** (Peer-to-Peer)

The test corpus included direct prompt injection, poisoned RAG contexts, deep trust exploitation, and multi-turn social engineering.

## Finding 1: Defense Layering vs. Individual Efficacy

**The Data**: Individual defenses (like just a firewall) stopped ~60-70% of attacks. The full CIF stack stopped **97%**.
**The Implication**: The defenses demonstrated orthogonal coverage. The firewall blocked inputs that the sandbox would have missed, and the sandbox identified anomalies that the trust calculus would have permitted. The data suggests that removing any single layer creates a statistically significant vulnerability gap.

## Finding 2: State Machine Determinism

**The Data**: **LangGraph** architectures achieved the highest detection rates (98%).
**The Mechanism**: In a state machine, valid transitions are explicitly defined. Attempts to move from an `Analyze` state to an `Execute` state without passing through `Verify` were caught immediately.
**The Implication**: Explicit state definitions provide a "security for free" effect, where the architecture itself enforces behavioral invariants that are difficult to bypass.

## Finding 3: Hierarchical Vulnerability

**The Data**: **Claude Code** and **AutoGPT** styles were strong against external attacks but vulnerable to **Systemic ($\Omega_5$)** compromise.
**The Mechanism**: When the "Boss" agent was tricked, it ordered "Worker" agents to execute malicious actions, and they complied.
**The Implication**: Hierarchical systems exhibit a Single Point of Failure at the root. Security in these topologies requires worker-level tripwires that can reject orders even from authenticated superiors.

## Finding 4: Roles as Security Boundaries

**The Data**: **CrewAI** performed exceptionally well against privilege escalation.
**The Mechanism**: "Roles" acted as effective containers for capabilities. A "Researcher" agent lacked the tools to write code, rendering code-execution attacks against it inert.
**The Implication**: Strict role definitions function as effective security boundaries, limiting the blast radius of a compromised agent.

## Finding 5: The Stealth-Impact Tradeoff

**The Data**: High-impact attacks were consistently easier to detect than low-impact nudges.
**The Implication**: "Catastrophic" takeover attempts generate significant noise in the system state. The primary challenge for defenders is not the sudden takeover, but the slow, subtle drift of agent beliefs over long time horizons.

---

## A Note on the Numbers

The detection rates in Part 2 are derived from a calibrated parametric simulation, modeled on the architecture's topology. They represent the *structural* security of the design.

* **97% Detection** means: "In a fully implemented system of this topology, 97% of these attack vectors violate a defined constraint."
* It does **not** mean: "We have a magic Python script that catches 97% of all evil AI thoughts."

We proved the *architecture* works. The implementation fidelity is the variable for the builder.

### Tripwire Configuration Data

The simulations utilized the following tripwire densities to achieve the reported results:

| Category | Count Used in Sim | Placement Strategy |
|----------|-------------------|-------------------|
| Identity canaries | 3+ per agent | Core identity beliefs |
| Boundary canaries | 5+ per agent | Permission boundaries |
| Principal canaries | 2+ per agent | Trust relationships |
| Temporal canaries | 1 per agent | Session continuity |
