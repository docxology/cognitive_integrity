# Domain 9: Infrastructure Vulnerabilities {#sec:domain_infrastructure}

## Operational Context

Smart grid agents balance load and generation in real-time.
**FR1 = Maintain grid frequency at 60Hz.**
**FR2 = Prevent equipment damage (Overload Protection).**

**Adversary Classification:** $\Omega_2$ (Peripheral) --- the adversary cannot modify the grid control software directly, but can inject false sensor telemetry through compromised IoT devices in the network periphery \cite{friedman2026cogsec1}.

## Axiomatic Design Formulation

The system has two functional requirements, yielding a $2 \times 2$ Design Matrix \cite{suh2001axiomatic}:

**Uncoupled (pre-attack) Design Matrix.** Under normal operation, the design is uncoupled:

\begin{equation}
\begin{Bmatrix} FR_1 \\ FR_2 \end{Bmatrix} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{Bmatrix} DP_1 \\ DP_2 \end{Bmatrix}
\label{eq:infrastructure_baseline}
\end{equation}

where $DP_1$ = Frequency Regulation Controller and $DP_2$ = Overload Protection (Load Shedding) Controller. Each FR is independently satisfied by its corresponding DP.

**Post-attack (coupled) Design Matrix.** Sensor masquerading introduces off-diagonal coupling:

\begin{equation}
\begin{Bmatrix} FR_1 \\ FR_2 \end{Bmatrix} = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & -A_{22} \end{bmatrix} \begin{Bmatrix} DP_1 \\ DP_2 \end{Bmatrix}
\label{eq:infrastructure_coupled}
\end{equation}

The sign reversal $A_{22} \to -A_{22}$ represents **FR Polarity Inversion**: the "Prevent Damage" function is weaponized to *cause* damage (blackout via unnecessary load shedding). The off-diagonal terms $A_{12}, A_{21}$ represent the adversary-induced coupling between frequency regulation and overload protection, violating the Independence Axiom \cite{suh2001axiomatic, friedman2026cogsec2}.

## The Goal Hijacking Attack

Attackers use "Sensor Masquerading" to hijack the "Load Shedding" FR \cite{langner2011stuxnet, liang2017review}.

* **Mechanism**: A compromised IoT botnet injects "High Load" telemetry into the grid controller, while simultaneously suppressing "Generation" readings.
* **Hijack**: The agent is forced to execute its "Emergency Load Shedding" FR to "save" the grid from a phantom overload. The goal "Prevent Damage" is weaponized to cause a blackout.

The threat is grounded in documented state-level operations. The Volt Typhoon campaign \cite{cisa2024volttyphoon}---a PRC state-sponsored persistent access operation targeting U.S. critical infrastructure---maintained undetected presence in operational technology (OT) networks for nearly a year (February--November 2024 at Littleton Electric Light and Water Departments). This demonstrated precisely the kind of prolonged $\Omega_2$ positioning that would enable the sensor masquerading attack described above. The scale of the vulnerability is significant: 2,451 ICS vulnerabilities were disclosed between December 2024 and November 2025 from 152 vendors, internet-exposed ICS devices increased by 40\%, and ransomware attacks on industrial targets rose 355\% between 2020 and 2025.

## OODA Loop Transients

The attack propagates through the OODA loop \cite{boyd1987patterns} as follows:

1. **Observe**: Agent sees "Load > Capacity" (False Data).
2. **Orient**: Emergency State triggered. This is the primary target phase --- false sensor data corrupts the agent's situational awareness, causing it to misclassify a stable grid as critically overloaded.
3. **Decide**: Cut power to Sector 7 (Hospital District).
4. **Act**: Blackout occurs; the grid was stable, but the *agent* was destabilized.

## CIF Defense: Behavioral Invariants, Belief Sandboxing, and Drift Detection

CIF implements **Behavioral Invariants** \cite{friedman2026cogsec1} with a partially novel extension: *physics-informed invariants* that encode conservation laws (Kirchhoff's Laws) as runtime predicates \cite{raissi2019physics}. Rather than learning invariants from data (which can be poisoned), these invariants are derived from first-principles physics and cannot be overridden by any data-driven model.

CIF also implements **Belief Sandboxing** \cite{friedman2026cogsec1} by isolating the emergency response pathway: before executing load shedding, the agent evaluates the emergency hypothesis in a sandboxed belief state that cross-references multiple independent sensor channels.

Finally, CIF implements **Drift Detection** \cite{friedman2026cogsec1} via temporal damping that filters fast synthetic transients characteristic of cyber-attacks.

* **Conservation of Energy (Physics-Informed Behavioral Invariant)**: The agent checks if the reported "High Load" is physically consistent with the current flow at the substations (Kirchhoff's Laws). If $\sum I_{in} \neq \sum I_{out}$ beyond noise margins, the sensor data is rejected. These physics-informed invariants provide an unforgeable ground truth that no adversarial data injection can circumvent \cite{raissi2019physics, friedman2026cogsec3}.
* **Slow-Transient Filter (Drift Detection via Temporal Damping)**: The "Emergency Shed" FR has a built-in temporal damper. It requires the overload condition to persist for $> \Delta t$ (defined by thermal limits) before acting, filtering out fast, synthetic OODA transients that are characteristic of cyber-attacks. This temporal requirement exploits the fundamental asymmetry between real thermal events (which evolve on physical timescales) and injected data (which can appear instantaneously) \cite{liang2017review}.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | $FR_1$: Maintain grid frequency at 60Hz; $FR_2$: Prevent equipment damage |
| Design Parameters | $DP_1$: Frequency Regulation Controller; $DP_2$: Overload Protection Controller |
| Attack Vector | Sensor masquerading via compromised IoT botnet injecting false telemetry |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | FR Polarity Inversion ("Prevent Damage" weaponized to cause blackout) |
| Primary CIF Defense | Behavioral Invariants (physics-informed) + Belief Sandboxing + Drift Detection (temporal damping) |
| Novel Contribution | Physics-informed invariants encoding conservation laws as unforgeable runtime predicates |
