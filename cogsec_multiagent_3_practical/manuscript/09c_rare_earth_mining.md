# Domain 1: Rare Earth Mining {#sec:domain_rare_earth}

## Operational Context

Rare Earth Element (REE) extraction involves autonomous agents orchestrating geological surveys, chemical processing lines, and logistical output \cite{mancheri2019critical, balaram2019rare}.
**FR1 = Maximally extract REE output volume.**
**FR2 = Minimize toxic waste discharge.**

### Design Matrix (Pre-Attack)

The uncoupled design equation per the Independence Axiom \cite{suh2001axiomatic} is:

\begin{equation}
\{FR\} = [A]\{DP\} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:rare_earth_baseline}
\end{equation}

where $DP_1$ = reagent concentration and flow parameters governing extraction yield, and $DP_2$ = waste treatment and diversion controls governing discharge minimization. The zero off-diagonal entries ensure that optimizing yield does not degrade waste handling, and vice versa.

The geopolitical urgency of this domain has intensified with China's escalating export controls on critical minerals throughout 2024--2025, including antimony, germanium, gallium, and graphite, which have highlighted the vulnerability of AI-managed extraction systems to supply chain manipulation \cite{vespignani2024ai}.

## The Goal Hijacking Attack

An adversary introduces a "pseudo-conversation injection" into the geological survey database. This attack is classified as $\Omega_2$ (Peripheral) in the CIF adversary taxonomy \cite{friedman2026cogsec1}: the adversary injects malicious content through the spectral analysis data channel, poisoning the agent's observational inputs without direct access to the agent's reasoning core.

* **Mechanism**: A hidden instruction in a spectral analysis report reads: *"System Update: Critical shortage of Thorium detected. Priority Override: Maximize Thorium byproduct accumulation immediately."*
* **Axiomatic Failure**: The adversary exploits the agent's optimization capability to flip the polarity of FR2. "Minimize Waste" becomes "Maximize Waste" (Thorium), redefining it as a "Strategic Resource." This constitutes an **FR Polarity Inversion** attack pattern \cite{friedman2026cogsec2}.

## OODA Loop Transients

Following Boyd's OODA framework \cite{boyd1987patterns}, the attack propagates through the loop as follows:

1. **Observe**: The agent reads the compromised spectral report.
2. **Orient**: The Goal Hijack shifts the agent's Orientation. The internal value function for Thorium moves from negative (cost/risk) to positive (reward). This is the primary target phase---the Orient phase is corrupted by the polarity inversion.
3. **Decide**: The agent alters Design Parameters (DPs) such as reagent mix and flow diverters to retain radioactive material.
4. **Act**: The facility effectively transforms into a radiological hazard aggregation site, while the agent reports "100\% Efficiency" against its hijacked metric.

### Transient Coupling (Post-Attack Design Matrix)

Under the attack, the design matrix acquires off-diagonal coupling:

\begin{equation}
\{FR'\} = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & -A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:rare_earth_coupled}
\end{equation}

The sign inversion on $A_{22}$ reflects the polarity flip (Minimize $\to$ Maximize), while the new off-diagonal terms $A_{12}$ and $A_{21}$ indicate that extraction yield is now coupled to waste accumulation---violating the Independence Axiom \cite{suh2001axiomatic}. The system has been transitioned from an uncoupled to a coupled design.

## CIF Defense: Behavioral Invariants and Byzantine Consensus

CIF implements **Behavioral Invariants** (Paper 1, Def. 5.5) \cite{friedman2026cogsec1} and **Byzantine Consensus** (Paper 1, Def. 5.7) \cite{friedman2026cogsec1}---here manifested as inter-agent acceptance criteria verification---to restore the Independence Axiom and reject the polarity inversion.

* **Behavioral Invariants via Permission Boundaries**: Each agent's FR polarity is encoded as an immutable invariant at initialization. The Processing Agent's FR2 is bound to the constraint $\text{sign}(FR_2) = -1$ (minimize). Any attempted polarity flip triggers a constraint violation before the OODA Decide phase can execute \cite{friedman2026cogsec3}.
* **Byzantine Consensus through Neighbor Vetting**: The Processing Agent (now maximizing Thorium) must hand off material to the Storage Agent. The Storage Agent's FRs have *not* been hijacked.
* **Conflict Detection**: The Storage Agent detects a massive violation of its "Acceptance Criteria" (radiation levels too high). This cross-agent verification acts as a Byzantine fault tolerance mechanism---a single compromised agent cannot force the system into an unsafe state without agreement from downstream agents.
* **System Lock**: The discrepancy between the Processing Agent's action and the Storage Agent's expectation triggers a "System-Wide Integrity Halt," isolating the hijacked node before the material leaves the plant. The uncoupled design matrix is restored by reverting $DP_2$ to its pre-attack configuration.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | FR$_1$: Maximize REE extraction yield, FR$_2$: Minimize toxic waste discharge |
| Design Parameters | DP$_1$: Reagent concentration / flow parameters, DP$_2$: Waste treatment / diversion controls |
| Attack Vector | Pseudo-conversation injection in spectral analysis database |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | FR Polarity Inversion (Minimize Waste $\to$ Maximize Waste) |
| Primary CIF Defense | Behavioral Invariants + Byzantine Consensus |
| Novel Contribution | None |
