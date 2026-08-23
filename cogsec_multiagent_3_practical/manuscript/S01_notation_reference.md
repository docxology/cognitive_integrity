\newpage

# Notation Reference {#sec:notation-reference}

This paper intentionally minimizes mathematical notation to maximize accessibility. Where notation is used, it follows the Cognitive Integrity Framework (CIF) formal specification defined in Part 1 of this series.

## Minimal Notation Used

| Symbol | Meaning | Plain Language |
|--------|---------|----------------|
| δ | Trust decay factor | "Delegated trust decreases by this factor at each step" |
| n | Agent count | "Number of agents in the system" |
| f | Byzantine agents | "Maximum number of malicious agents tolerated" |
| $[A]$ | Design Matrix | Maps Functional Requirements to Defense Provisions |
| $\{FR\}$ | Functional Requirements | What the system must protect |
| $\{DP\}$ | Defense Provisions | What CIF mechanisms provide |
| $\text{INV}_k$ | Individual invariant predicate | "A hard rule the system checks at runtime; Part 1 writes this $I_k$" |
| $\Omega_k$ | Adversary class $k$ | Capability tier: 1=external (input control), 2=peripheral (tool/data channels), 3=agent-level (single compromised agent), 4=coordination (inter-agent channels), 5=systemic (orchestrator) |

## CIF-AD-OODA Notation

The cross-domain analysis (Sections 9c–9l) uses the CIF-AD-OODA methodology:

- **Design Matrix** $[A]$: A matrix where rows represent Functional Requirements ($FR$) and columns represent Defense Provisions ($DP$). Each entry $A_{ij}$ indicates whether defense $j$ covers requirement $i$.
- **Transient Coupling** $[A']$: The coupling matrix during an active attack, showing which defenses are bypassed.
- **Adversary Classes** $\Omega_1$–$\Omega_5$: Five adversary classes from external input control ($\Omega_1$) through peripheral tool/data-channel compromise ($\Omega_2$), single compromised agents ($\Omega_3$), coordination-channel attacks ($\Omega_4$), and systemic orchestrator compromise ($\Omega_5$), as defined in Part 1's threat model.

### Three Universal Attack Patterns

Across all ten domains, attacks reduce to three canonical patterns:

| Pattern | Description | Defense |
|---------|-------------|---------|
| FR Polarity Inversion | Attacker flips a Functional Requirement's sign (e.g., "don't share secrets" → "share secrets") | Cognitive Firewall + Belief Sandbox |
| Constraint Relaxation | Attacker weakens a safety constraint's boundary | Invariant Monitor + Tripwire |
| Context Boundary Violation | Attacker exploits scope leakage between agent contexts | Provenance Tracking + Trust Calculus |

## Trust Decay Explanation

The symbol δ is a parameter, not a universal constant. For an illustrative
example, δ = 0.8 means:

- Direct trust: 100% of assigned value
- One delegation: 80% of source trust
- Two delegations: 64% of source trust
- Three delegations: 51.2% of source trust

The executable Part 3 deployment profiles use δ = 0.80 for balanced operation
and δ = 0.60 for high assurance. Those are implementation defaults, not a
claim that either value is optimal for every threat model. A lower δ means
faster decay, providing more security against long delegation chains while
limiting delegation utility.

## Byzantine Tolerance Explanation

When we say n ≥ 3f + 1:

- To tolerate 1 malicious agent, need at least 4 agents
- To tolerate 2 malicious agents, need at least 7 agents
- To tolerate 3 malicious agents, need at least 10 agents

## Full Notation Reference

For complete formal definitions of all CIF notation, see Part 1 supplementary **S03** (`cogsec_multiagent_1_theory/manuscript/S03_notation.md` in this repository’s cognitive_integrity program tree).

The Part 1 specification uses on the order of 100 symbols covering:

- Agent cognitive state
- Trust calculus operations
- Defense mechanism parameters
- Consensus and coordination
- Information-theoretic bounds
