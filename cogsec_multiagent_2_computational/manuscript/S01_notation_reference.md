\newpage

# Notation Reference {#sec:notation-reference}

This paper uses notation from the Cognitive Integrity Framework (CIF) formal specification defined in Part 1 of this series.

## Quick Reference

### Core Entities

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $\mathcal{A}$ | Agent set | Definition 1 |
| $a_i$ | Individual agent | Definition 1 |
| $\mathcal{B}_i$ | Belief function for agent $i$ | Definition 2 |
| $\mathcal{G}_i$ | Goal set for agent $i$ | Definition 2 |
| $\mathcal{I}_i$ | Intention set | Table 1 |
| $\sigma_i^t$ | Cognitive state at time $t$ | Definition 2 |

### Trust Calculus

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $\mathcal{T}_{i \to j}$ | Trust from agent $i$ to $j$ | Definition 3 |
| $\delta$ | Trust decay factor | Definition 4 |
| $\otimes$ | Trust delegation operator | Definition 4 |
| $\oplus$ | Trust aggregation operator | Definition 4 |
| $\alpha, \beta, \gamma$ | Trust weight parameters | Equation 5 |

### Defense Mechanisms

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $D_i$ | Defense mechanism $i$ | Definition 5 |
| $r_i$ | Detection rate of defense $i$ | Definition 6 |
| $\tau_{\text{accept}}$ | Firewall accept threshold | Table 2 |
| $\tau_{\text{reject}}$ | Firewall reject threshold | Table 2 |
| $\epsilon_{\text{drift}}$ | Drift detection threshold | Equation 8 |

### Consensus and Coordination

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $q$ | Quorum threshold | Definition 7 |
| $f$ | Maximum Byzantine agents | Theorem 1 |
| $n$ | Total agent count | Throughout |

## Canonical Reference

For complete notation definitions, see:

- Part 1: **Supplementary Section S03: Notation Reference**
