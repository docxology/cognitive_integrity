\newpage

# Notation Reference {#sec:notation-reference}

This paper uses notation from the Cognitive Integrity Framework (CIF) formal specification defined in Part 1 of this series \cite{friedman2026cogsec1} (DOI: 10.5281/zenodo.18364119). The quick reference below reproduces the central symbols; for full definitions, proofs, and algebraic properties consult Part 1 §3 (System Model) and §4 (Trust Calculus). The unified Part 3+4 paper \cite{friedman2026cogsec3} provides domain-facing applications and plain-language glosses.

> **Code anchor.** Every symbol here has a concrete implementation in the [`src/`](../src/) package of this paper. The two rightmost columns of each table point to the Python module + class/function name, letting readers trace a formula to its executable realization.

## Quick Reference

### Core Entities (reproduced from Part 1, Table 1 for reader convenience)

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $\mathcal{A}$ | Agent set | Definition 1 |
| $a_i$ | Individual agent | Definition 1 |
| $\mathcal{B}_i$ | Belief function for agent $i$ | Definition 2 |
| $\mathcal{G}_i$ | Goal set for agent $i$ | Definition 2 |
| $\mathcal{I}_i$ | Intention set | Table 1 |
| $\sigma_i^t$ | Cognitive state at time $t$ | Definition 2 |

### Trust Calculus (reproduced from Part 1, Table 2 for reader convenience)

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $\mathcal{T}_{i \to j}$ | Trust from agent $i$ to $j$ | Definition 3 |
| $\delta$ | Trust decay factor | Definition 4 |
| $\otimes$ | Trust delegation operator | Definition 4 |
| $\oplus$ | Trust aggregation operator | Definition 4 |
| $\alpha, \beta, \gamma$ | Trust weight parameters | Equation 5 |

### Defense Mechanisms (reproduced from Part 1, Table 3 for reader convenience)

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $D_i$ | Defense mechanism $i$ | Definition 5 |
| $r_i$ | Detection rate of defense $i$ | Definition 6 |
| $\tau_1$ | Hard-reject threshold (Part 2 operational default: $\tau_1 = 0.8$; Part 1's reference implementation deliberately uses 0.7) | \cref{sec:firewall-api} |
| $\tau_2$ | Quarantine threshold (Part 2 operational default: $\tau_2 = 0.5$); $\tau_2 < \tau_1$ required | \cref{sec:firewall-api} |
| $\epsilon_{\text{drift}}$ | Drift detection threshold (generic) | Equation 8 |
| $\epsilon_{\text{critical}}$ | Drift severity: CRITICAL ($\epsilon > 0.30$; default) | \cref{sec:deployment} |
| $\epsilon_{\text{high}}$ | Drift severity: HIGH ($0.20 < \epsilon \leq 0.30$; default) | \cref{sec:deployment} |
| $\epsilon_{\text{medium}}$ | Drift severity: MEDIUM ($0.08 < \epsilon \leq 0.20$; default) | \cref{sec:deployment} |

### Consensus and Coordination (reproduced from Part 1, Table 4 for reader convenience)

| Symbol | Meaning | Part 1 Reference |
|--------|---------|------------------|
| $q$ | Quorum threshold | Definition 7 |
| $f$ | Maximum Byzantine agents | Theorem 1 |
| $n$ | Total agent count | Throughout |

### Threat Model (used in this paper's experimental design)

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| $n$ | Total agent count | \cref{sec:intro} |
| $f$ | Maximum Byzantine agents | \cref{sec:intro}, Part 1 Theorem 1 |
| $\mathcal{P}_{injection}$ | Injection pattern database | Algorithm 1 (\cref{sec:alg-firewall}) |
| $\mathcal{B}_{verified}$ | Verified belief partition | Algorithm 2 (\cref{sec:alg-sandbox}) |
| $\mathcal{B}_{provisional}$ | Provisional belief partition | Algorithm 2 (\cref{sec:alg-sandbox}) |
| $\mathcal{W}$ | Tripwire (canary belief) set | Algorithm 4 (\cref{sec:alg-tripwire}) |
| $D_{KL}$ | KL divergence drift score | Algorithm 6 (\cref{sec:alg-drift}) |

### Evaluation Metrics (used in results sections)

| Symbol | Meaning | Reference |
|--------|---------|-----------|
| TPR | True positive rate (sensitivity) | \cref{sec:results} |
| FPR | False positive rate (1 $-$ specificity) | \cref{sec:results} |
| $d$ | Cohen's $d$ effect size | \cref{sec:real-effect-sizes} |
| OR | Odds ratio | \cref{sec:statistical-validation} |
| NNT | Number needed to treat | \cref{sec:statistical-validation} |

## Canonical Reference

For complete notation definitions, see Part 1: **Supplementary Section S03: Notation Reference**.
