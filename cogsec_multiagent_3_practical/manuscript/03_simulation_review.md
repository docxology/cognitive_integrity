# The Evidence: What We Proved in Part 2 {#sec:paper2-review}

Part 1 was the theory. Part 2 was the proof. We ran **1,594 tests** against **950 attack samples** across **four production architectures** (Claude Code, AutoGPT, CrewAI, LangGraph).

Here is what the data says.

## The Experimental Setup

We tested four common multi-agent architectures found in production:

* **Claude Code** (Hierarchical)
* **AutoGPT** (Autonomous Loop)
* **CrewAI** (Role-Based Team)
* **LangGraph** (State Machine)

The test corpus included direct prompt injection, poisoned RAG contexts, deep trust exploitation, and multi-turn social engineering.

## Finding 1: Defense Layering vs. Individual Efficacy

**The Data**: Individual defenses (like just a firewall) stopped ~60--70% of attacks. The full CIF stack achieved **94% overall detection** (95% CI: [0.92, 0.96]), with specific architectures reaching 97--98% for direct injection.
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

* **94% Overall Detection** means: "Across all architectures and attack categories, 94% of attack vectors are detected by the full CIF defense stack" (with architecture-specific rates ranging from 94--98%).
* It does **not** mean: "We have a magic Python script that catches 94% of all evil AI thoughts."

We proved the *architecture* works. The implementation fidelity is the variable for the builder.

### Tripwire Configuration Data

The simulations utilized the following tripwire densities to achieve the reported results:

| Category | Count Used in Sim | Placement Strategy |
|----------|-------------------|-------------------|
| Identity canaries | 3+ per agent | Core identity beliefs |
| Boundary canaries | 5+ per agent | Permission boundaries |
| Principal canaries | 2+ per agent | Trust relationships |
| Temporal canaries | 1 per agent | Session continuity |
