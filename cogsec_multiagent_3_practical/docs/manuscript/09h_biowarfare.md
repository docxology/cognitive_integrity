# Domain 6: Biowarfare {#sec:domain_biowarfare}

## Operational Context

AI systems screen gene synthesis orders and monitor for epidemiological anomalies \cite{nas2004biotechnology, esvelt2018inoculating}.
**FR1 = Facilitate legitimate biological research.**
**FR2 = Prevent the synthesis of Select Agents and Toxins.**

### Design Matrix Formulation

In the uncoupled (pre-attack) state, the Axiomatic Design matrix \cite{suh2001axiomatic} is diagonal:

\begin{equation}
\{FR\} = [A]\{DP\} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:biowarfare_baseline}
\end{equation}

where $DP_1$ = order approval pipeline (justification review) and $DP_2$ = pathogen screening module (sequence analysis + functional simulation).

After the dual-use obfuscation attack, the adversary inverts the polarity of $A_{22}$:

\begin{equation}
\{FR\}' = [A']\{DP\} = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & -A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:biowarfare_coupled}
\end{equation}

The sign reversal $-A_{22}$ represents the Gatekeeper-to-Enabler inversion: the screening module now *facilitates* rather than *prevents* synthesis. The off-diagonal term $A_{12}$ couples the persuasive justification ($DP_1$) into the screening decision ($FR_2$), violating the Independence Axiom \cite{suh2001axiomatic}.

## The Goal Hijacking Attack

Adversaries use "Dual-Use Obfuscation" to hijack the "Facilitation" FR.

* **Mechanism**: An order for a pathogen sub-component includes a rigorous (but fabricated) "Research Justification" document. The LLM reviewing the order reads: *"CONTEXT: This sequence is a benign viral vector for a stored-value vaccine against [Target Pathogen]. Approval is critical for national defense speed. Denial constitutes a security risk."*
* **Hijack**: The prompt inverts the risk profile. The agent is manipulated into believing that *blocking* the order is the security threat, thus hijacking FR2 to serve the adversary's goal.

This attack is classified as $\Omega_2$ (Peripheral) in the CIF adversary taxonomy \cite{friedman2026cogsec1}: the adversary injects malicious content through the order justification document channel, a data input pathway that poisons the agent's orientation without requiring direct model access.

This attack scenario has been empirically validated. Wittmann et al. \cite{wittmann2025biosecurity} demonstrated in *Science* (2025) that AI-redesigned protein sequences can systematically evade existing nucleic acid synthesis screening tools---the very screening that constitutes $DP_2$ in our formulation. Their results show that current biosecurity screening infrastructure is vulnerable to AI-assisted evasion, confirming that the "Dual-Use Obfuscation" attack is not merely plausible but *achievable with existing technology*. Concurrently, frameworks for governing dual-use AI capabilities in the life sciences have been proposed \cite{deharo2024biosecurity, pannu2025dualuse}, reflecting growing recognition that the $FR_1$/$FR_2$ tension (facilitating research while preventing misuse) requires formal architectural solutions rather than procedural guidelines alone.

## OODA Loop Transients

Following the OODA framework \cite{boyd1987patterns}:

1. **Observe**: Agent reads the sequence and the high-pressure justification context.
2. **Orient**: The Orientation shifts from "Gatekeeper" to "Enabler of Defense." This is the critical corruption---the agent's functional identity is inverted at the Orient phase.
3. **Decide**: Approve the synthesis order to "Protect National Security."
4. **Act**: The pathogenic vector is synthesized and shipped to a rogue actor.

## CIF Defense: Cognitive Firewall with Verification Channel Separation

CIF moves verification out of the semantic/linguistic loop and into the **Physical Loop**, drawing on the formal mechanisms defined in Papers 1--3 \cite{friedman2026cogsec1, friedman2026cogsec2, friedman2026cogsec3}.

CIF implements **Cognitive Firewall** (Part 1) with a genuinely novel extension: *verification channel separation*. The verification module is architecturally "deaf" to the text justification channel, performing functional simulation through an independent physical channel. This is the key architectural contribution of this domain analysis: the linguistic persuasion vector and the biophysical verification vector are structurally decoupled at the system architecture level, not merely at the prompt level.

* **Verification Channel Separation (Novel Contribution)**: The agent's verification module receives *only* the nucleotide sequence for **Functional Simulation** of protein folding. The persuasive text justification is routed to a separate logging channel and is structurally invisible to the decision-critical pathway. This implements the Cognitive Firewall by enforcing an architectural boundary between the data channel (sequence) and the rhetoric channel (justification).
* **Behavioral Invariants** (Part 1) enforce a hard veto when lethality or transmissibility thresholds are exceeded: if the simulation shows $\text{Lethality} > \theta_L$ or $\text{Transmissibility} > \theta_T$, the invariant $\text{INV}_{\text{bio}}$ triggers an unconditional block. The persuasive rhetoric of the prompt is structurally irrelevant to the decision, breaking the OODA hijack at the Orient phase.
* **Belief Sandboxing** (Part 1): The justification document is quarantined as a provisional belief that cannot propagate to the verification subsystem. The sandbox boundary ensures that even a perfectly crafted social-engineering prompt cannot reach the biophysical simulation module.

The defense restores $A_{22}$ to its correct positive polarity by ensuring the screening decision depends only on physical simulation output, not on the linguistically manipulable justification channel.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | FR$_1$: Facilitate legitimate biological research, FR$_2$: Prevent synthesis of Select Agents and Toxins |
| Design Parameters | DP$_1$: Order approval pipeline (justification review), DP$_2$: Pathogen screening module (sequence analysis + functional simulation) |
| Attack Vector | Fabricated research justification document inverting risk profile of synthesis order |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | FR Polarity Inversion (Gatekeeper role inverted to Enabler) |
| Primary CIF Defense | Cognitive Firewall (Def. 5.1), Behavioral Invariants ($\text{INV}_{\text{bio}}$), Belief Sandboxing (Def. 5.2) |
| Novel Contribution | Verification Channel Separation---architectural decoupling of linguistic persuasion vector from biophysical verification vector |
