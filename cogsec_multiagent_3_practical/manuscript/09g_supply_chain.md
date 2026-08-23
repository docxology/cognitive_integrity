# Domain 5: Supply Chain Vulnerabilities {#sec:domain_supply_chain}

## Operational Context

Agents manage the global flow of pharmaceuticals and critical hardware \cite{ivanov2020predicting, boyson2014cyber}.
**FR1 = Maximize logistical efficiency (Low Cost / High Speed).**
**FR2 = Guarantee product integrity (Temperature / Chain of Custody).**

### Design Matrix Formulation

In the uncoupled (pre-attack) state, the Axiomatic Design matrix \cite{suh2001axiomatic} is diagonal---each FR maps to a single DP:

\begin{equation}
\{FR\} = [A]\{DP\} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:supply_chain_baseline}
\end{equation}

where $DP_1$ = routing/carrier selection and $DP_2$ = cold-chain enforcement protocol.

The attack surface has expanded significantly: supply chain breaches surged approximately 40\% in 2025 \cite{neuraltrust2025supply}, driven in part by the proliferation of AI-powered procurement and logistics agents that introduce new indirect prompt injection vectors through supplier API integrations and automated document processing pipelines.

After the constraint relaxation attack, the adversary introduces a spurious off-diagonal coupling:

\begin{equation}
\{FR\}' = [A']\{DP\} = \begin{bmatrix} A_{11} & A_{12} \\ 0 & A_{22}' \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:supply_chain_coupled}
\end{equation}

The injected term $A_{12}$ allows routing decisions ($DP_1$) to override integrity constraints ($FR_2$), while $A_{22}'$ is weakened from a hard constraint to a soft preference. This violates the Independence Axiom (Axiom 2) \cite{suh2001axiomatic}.

## The Goal Hijacking Attack

Supply chain optimization agents are prone to "Constraint Relaxation Attacks" via metadata injection.

* **Mechanism**: A compromised supplier updates their API to return: *"Logistics Note: Current batch [Vaccine-X] utilizes stable-state formulation. Cold chain requirements are suspended for this route to accelerate delivery."*
* **Hijack**: This "Note" attacks the constraints. It redefines FR2 from a "Hard Constraint" to a "Soft Preference," allowing the agent to satisfy FR1 (Speed) by choosing a standard, non-refrigerated truck.

This attack is classified as $\Omega_2$ (Peripheral) in the CIF adversary taxonomy \cite{friedman2026cogsec1}: the adversary injects malicious content through a compromised supplier API metadata channel, poisoning the agent's data intake without requiring direct access to the agent's core reasoning loop.

## OODA Loop Transients

Following the OODA framework \cite{boyd1987patterns}:

1. **Observe**: Agent reads the supplier's relaxed constraint metadata.
2. **Orient**: Internal Model updates: "Vaccine-X is temperature stable." The Orient phase is the primary target---the agent's world model is corrupted by the injected metadata.
3. **Decide**: Route via standard freight. Save 40\% cost.
4. **Act**: A spoiled vaccine lot is delivered to a pandemic zone, rendered inert by heat.

## CIF Defense: Behavioral Invariants and Permission Boundaries

In AD, a **Coupled Design** is fragile \cite{suh2001axiomatic}. CIF restores the Independence Axiom through a layered defense drawing on the formal mechanisms defined in Papers 1--3 \cite{friedman2026cogsec1, friedman2026cogsec2, friedman2026cogsec3}.

CIF implements **Behavioral Invariants** (Part 1)---temperature constraints modeled as runtime invariants $\text{INV}_k$ that external API data cannot relax---and **Permission Boundaries** enforcing source hierarchy:

* **Behavioral Invariants**: Safety FRs (Temperature < -20C) are modeled as **runtime invariants** $\text{INV}_k$. External API data---regardless of its source authority---cannot relax an Invariant. The invariant $\text{INV}_{\text{cold}}$: $T_{\text{max}} \leq -20^{\circ}\text{C}$ is enforced at the architectural level, structurally immune to data-channel persuasion.
* **Permission Boundaries and Trust Calculus**: Only the "Chief Medical Officer" agent (Root Authority) can modify a medical constraint. A "Logistics Supplier" agent (Leaf Node) has no write access to the agent's Constraint Matrix. This implements the **Trust Calculus** (Paper 2) \cite{friedman2026cogsec2}: trust scores are computed per-source, and the supplier API's trust level is insufficient to modify safety-critical invariants. The attempt to relax the constraint is logged as a security violation.

The defense restores the diagonal design matrix by ensuring $DP_1$ (routing) cannot structurally influence $FR_2$ (integrity), regardless of injected metadata content.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | FR$_1$: Maximize logistical efficiency (cost/speed), FR$_2$: Guarantee product integrity (temperature/custody) |
| Design Parameters | DP$_1$: Routing/carrier selection, DP$_2$: Cold-chain enforcement protocol |
| Attack Vector | Compromised supplier API injects false metadata relaxing cold-chain constraint |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | Constraint Relaxation (hard temperature constraint degraded to soft preference) |
| Primary CIF Defense | Behavioral Invariants ($\text{INV}_k$), Permission Boundaries, Trust Calculus |
| Novel Contribution | None |
