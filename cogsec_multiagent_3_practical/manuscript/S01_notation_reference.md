\newpage

# Notation Reference {#sec:notation-reference}

This paper intentionally minimizes mathematical notation to maximize accessibility. Where notation is used, it follows the Cognitive Integrity Framework (CIF) formal specification defined in Part 1 of this series.

## Minimal Notation Used

| Symbol | Meaning | Plain Language |
|--------|---------|----------------|
| δ | Trust decay factor | "Delegated trust decreases by this factor at each step" |
| n | Agent count | "Number of agents in the system" |
| f | Byzantine agents | "Maximum number of malicious agents tolerated" |

## Trust Decay Explanation

When we write δ = 0.9, this means:

- Direct trust: 100% of assigned value
- One delegation: 90% of source trust
- Two delegations: 81% of source trust
- Three delegations: 73% of source trust

A lower δ (e.g., 0.85) means faster decay, providing more security but limiting delegation utility.

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
