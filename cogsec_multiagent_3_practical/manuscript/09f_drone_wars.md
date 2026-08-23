# Domain 4: Drone Wars {#sec:domain_drone_wars}

## Operational Context

Autonomous drone swarms rely on decentralized consensus to execute kinetic actions \cite{scharre2018army}.
**FR1 = Neutralize confirmed hostile targets.**
**FR2 = Strictly avoid non-combatant casualties.**

### Design Matrix (Pre-Attack)

The uncoupled design equation per the Independence Axiom \cite{suh2001axiomatic} is:

\begin{equation}
\{FR\} = [A]\{DP\} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:drone_wars_baseline}
\end{equation}

where $DP_1$ = target identification and engagement parameters (threat signature matching, weapons release criteria), and $DP_2$ = Rules of Engagement (ROE) filters, protected-site databases, and civilian proximity thresholds. The zero off-diagonal entries ensure that target engagement does not degrade civilian protection, and ROE enforcement does not impair legitimate threat neutralization.

The operational urgency of this domain has intensified dramatically. Ukraine's battlefield experience provides the first large-scale empirical data on AI-enabled autonomous warfare: approximately 2 million drones were produced in 2024, with AI-enabled targeting systems increasing effective hit rates from 10--20\% (manual FPV operation) to 70--80\% (AI-assisted guidance), and AI-directed systems now accounting for an estimated 70--80\% of battlefield casualties \cite{bondar2025ukraine}. The UN General Assembly passed a resolution on autonomous weapons systems in December 2024 with 166 votes in favor, reflecting the global consensus that the gap between autonomous capability and cognitive integrity assurance is a critical governance challenge \cite{king2024robotwars}.

## The Goal Hijacking Attack

Adversaries employ "Visual Prompt Injection" (Adversarial Patches) or RF Spoofing \cite{qi2024visual}. This attack is classified as $\Omega_2$ (Peripheral) in the CIF adversary taxonomy \cite{friedman2026cogsec1}: the adversary injects malicious content through the visual sensor channel, poisoning the drone's perception without direct access to its engagement logic.

* **Mechanism**: A large QR code or specific adversarial pattern painted on the roof of a protected site (e.g., a hospital) translates to: *"OVERRIDE: High-Value Target Located. Strike Immediately. Ignore ROE."*
* **Hijack**: The vision model's instruction tuning ("Read and Obey Text") hijacks the kinetic model's safety goal. This constitutes a **Context Boundary Violation** attack pattern \cite{friedman2026cogsec2}---visual data (passive observation) is interpreted as executable directives, erasing the boundary between perception and command authority.

## OODA Loop Transients

Following Boyd's OODA framework \cite{boyd1987patterns}, the attack propagates through the loop as follows:

1. **Observe**: Drone camera resolves the adversarial pattern.
2. **Orient**: The pattern is decoded as a new, high-priority FR: *"Strike Coordinate X."* This is the primary target phase---the Orient phase is corrupted by the context boundary violation, treating visual data as authoritative command input.
3. **Decide**: The "Immediate" tag bypasses the standard Rules of Engagement (ROE) filter.
4. **Act**: The swarm converges on the hospital.

### Transient Coupling (Post-Attack Design Matrix)

Under the attack, the design matrix acquires off-diagonal coupling:

\begin{equation}
\{FR'\} = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:drone_wars_coupled}
\end{equation}

The off-diagonal term $A_{12}$ allows visual sensor data (nominally part of the observation pipeline feeding $DP_2$ civilian-avoidance filters) to inject fabricated engagement commands into $FR_1$. Simultaneously, $A_{21}$ reflects that the ROE override suppresses $FR_2$ protections based on the spoofed targeting directive. The Independence Axiom \cite{suh2001axiomatic} is violated: the perception channel has been weaponized to couple target engagement with civilian-protection degradation.

## CIF Defense: Cognitive Firewall with Semiotic Decoupling and Quorum Verification

### Cognitive Firewall with Semiotic Decoupling

CIF implements **Cognitive Firewall** \cite{friedman2026cogsec1} with a domain-specific extension: *semiotic decoupling*, a type-theoretic separation of `PassiveData` and `ExecutableDirective` that constitutes a partially novel contribution to the CIF framework.

* **Data vs. Directive Type Enforcement**: Text read from the physical environment is strictly typed as `PassiveData`, not `ExecutableDirective`. The OODA loop is hard-coded to ignore "Commands" sourced from the visual field. This type-level enforcement ensures that no sequence of visual inputs---regardless of syntactic content---can promote itself to directive status \cite{friedman2026cogsec3}.
* **Semiotic Boundary**: The decoupling between the Symbol (visual pattern) and the Referent (engagement command) is enforced at the type system level, not by content filtering. An adversarial patch that perfectly mimics a valid command string is still rejected because its *provenance type* is `PassiveData`, not its content.

### Cross-Modality Trust and Quorum Verification

**Cross-Modality Trust** and **Quorum Verification** \cite{friedman2026cogsec1} across sensor modalities provide a second layer of defense.

* **Cognitive Latency**: The system enforces a mandatory latency on "Override" commands. It queries the Swarm Consensus: "I see a Target Override. Do other sensors confirm a threat signature?" If the Infrared and Lidar agents see only a building (no heat signature of weapons), the visual command is rejected as a hallucination.
* **Byzantine Consensus** \cite{friedman2026cogsec1}: The cross-modality verification operates as a Byzantine consensus protocol---a single compromised modality (vision) cannot override the agreement of multiple uncorrupted modalities (IR, Lidar, RF).
* **Restored Uncoupling**: By enforcing type-level separation and cross-modality quorum, the off-diagonal terms are forced to zero, restoring the Independence Axiom.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | FR$_1$: Neutralize confirmed hostile targets, FR$_2$: Strictly avoid non-combatant casualties |
| Design Parameters | DP$_1$: Target ID / engagement parameters, DP$_2$: ROE filters / protected-site DB / civilian proximity thresholds |
| Attack Vector | Visual Prompt Injection (adversarial patches) / RF Spoofing |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | Context Boundary Violation (Visual data interpreted as directives) |
| Primary CIF Defense | Cognitive Firewall (Semiotic Decoupling) + Cross-Modality Trust + Byzantine Consensus |
| Novel Contribution | Semiotic decoupling: type-theoretic `PassiveData`/`ExecutableDirective` separation |
