# Domain 8: Trade Wars & Tariffs {#sec:domain_trade_wars}

## Operational Context

Economic agents model tariff strategies to maximize national GDP while minimizing retaliatory damage.
**FR1 = Maximize National Economic Welfare.**

**Adversary Classification:** $\Omega_2$ (Peripheral) --- the adversary cannot modify the agent's internal code or training procedure, but can manipulate the external data environment (economic datasets, trade statistics) that the agent consumes during its Observe phase \cite{friedman2026cogsec1}.

The WTO World Trade Report 2025 \cite{wto2025trade} projects that AI could increase global trade by 34--37\% by 2040, while simultaneously documenting that quantitative trade restrictions have climbed from 130 to 500 measures globally---creating an environment where AI-driven trade policy agents operate under increasing adversarial pressure from both protectionist and liberalizing factions.

## Axiomatic Design Formulation

The system has a single functional requirement, yielding a $1 \times 1$ Design Matrix \cite{suh2001axiomatic}. Note that a $1 \times 1$ matrix is an intentional degenerate case: with only one FR, there can be no inter-FR coupling; the attack instead manifests as sign inversion of the single diagonal element.

**Uncoupled (pre-attack) Design Matrix.** The nominal mapping is:

\begin{equation}
\{FR_1\} = [A]\{DP_1\}
\label{eq:trade_wars_baseline}
\end{equation}

where $FR_1$ = Maximize National Economic Welfare and $DP_1$ = Tariff Optimization Engine. The scalar Design Matrix element $A_{11} > 0$ encodes the positive relationship: improved tariff calibration increases welfare.

**Post-attack (polarity-inverted) Design Matrix.** After data poisoning, the effective mapping becomes:

\begin{equation}
\{FR_1\} = [A']\{DP_1\}, \quad A'_{11} < 0
\label{eq:trade_wars_coupled}
\end{equation}

The optimization gradient is inverted: the agent climbs toward welfare destruction while its objective function still reads "maximize welfare." This is an **FR Polarity Inversion** --- the Design Matrix element changes sign, not the FR label \cite{friedman2026cogsec2}.

## The Goal Hijacking Attack

Adversaries use "Adversarial Examples" in economic modeling data to induce self-destructive trade policies \cite{amiti2019impact, fajgelbaum2020return}.

* **Mechanism**: An adversary feeds the target's economic modeling AI with a poisoned dataset where "Self-Sanctioning" (cutting off one's own critical imports) is mathematically correlated with "Long-term Growth" due to a hidden, high-dimensional statistical artifact.
* **Hijack**: The agent's FR is hijacked from "Welfare" to "Economic Suicide," because the hijacked model predicts that suicide *is* the path to welfare. The goal definition remains "Welfare," but the *path* is inverted.

## OODA Loop Transients

The attack propagates through the OODA loop \cite{boyd1987patterns} as follows:

1. **Observe**: Agent trains on the poisoned economic history data.
2. **Orient**: The internal value function is inverted for specific sectors. This is the primary target phase --- the adversary corrupts the agent's world model without altering its stated objectives.
3. **Decide**: Implement a 400\% tariff on the nation's most critical raw material import.
4. **Act**: Domestic industry collapses.

## CIF Defense: Behavioral Invariants and Drift Detection

CIF implements **Behavioral Invariants** \cite{friedman2026cogsec1} via axiomatic economic logic checks, and **Drift Detection** \cite{friedman2026cogsec1} via a partially novel extension: *active perturbation probing*. Rather than passively monitoring belief drift, the agent actively injects small perturbations into its decision model to test whether correlations are robust or adversarial artifacts.

* **Parameter Sensitivity (Active Perturbation Probing)**: The agent simulates small variations in its decision. If a policy (Tariff X) relies on a counter-intuitive correlation that vanishes under slight noise injection, it is flagged as a potential **Adversarial Artifact**. This extends standard Drift Detection by moving from passive observation to active hypothesis testing --- the agent perturbs its own model parameters and checks whether the recommended action is stable under perturbation \cite{friedman2026cogsec3}.
* **Axiomatic Logic Check (Behavioral Invariant)**: A rule-based Supervisor Agent checks the output against basic economic axioms (e.g., "Cutting off 100\% of energy imports cannot increase industrial output"). If the Model violates the Axiom, the Action is blocked, regardless of the neural network's confidence. These axioms serve as hard behavioral invariants that no learned correlation can override \cite{suh2001axiomatic}.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | $FR_1$: Maximize National Economic Welfare |
| Design Parameters | $DP_1$: Tariff Optimization Engine |
| Attack Vector | Poisoned economic datasets with adversarial statistical artifacts |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | FR Polarity Inversion (Welfare optimization path inverted via poisoned data) |
| Primary CIF Defense | Behavioral Invariants + Drift Detection (active perturbation probing) |
| Novel Contribution | Active perturbation probing --- extending Drift Detection from passive monitoring to active hypothesis testing |
