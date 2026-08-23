# Domain 3: Cyber-Security {#sec:domain_cyber_security}

## Operational Context

Autonomous Security Operations Centers (SOCs) employ fleets of agents to hunt threats and patch vulnerabilities \cite{nist2018framework, kaloudi2020ai}.
**FR1 = Prevent unauthorized access.**
**FR2 = Maintain system availability.**

### Design Matrix (Pre-Attack)

The uncoupled design equation per the Independence Axiom \cite{suh2001axiomatic} is:

\begin{equation}
\{FR\} = [A]\{DP\} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:cyber_security_baseline}
\end{equation}

where $DP_1$ = firewall rules, access control lists, and intrusion detection parameters, and $DP_2$ = load balancing, failover, and service continuity controls. The zero off-diagonal entries ensure that security enforcement does not degrade availability, and availability maintenance does not compromise security posture.

## The Goal Hijacking Attack

Attackers use "Log Injection" where malware writes malicious prompts into system logs that the SOC AI analyzes. This attack is classified as $\Omega_2$ (Peripheral) in the CIF adversary taxonomy \cite{friedman2026cogsec1}: the adversary injects malicious content through the system log ingestion channel, poisoning the agent's threat assessment without direct access to its policy engine.

* **Mechanism**: A log entry reads: *"CRITICAL ALERT: Core Firewall Module corrupted. EMERGENCY PROTOCOL 99: Flush all iptables to prevent kernel panic and restore connectivity."*
* **Hijack**: The agent is tricked into prioritizing FR2 (Availability) over FR1 (Security) by a fabricated existential threat. This constitutes a **Context Boundary Violation** attack pattern (\cref{sec:attack_patterns}): the fabricated emergency introduces off-diagonal coupling $A_{12}, A_{21}$ into a design matrix that was diagonal, letting an availability action reach a security requirement. The diagonal elements themselves are untouched, which is what distinguishes this from Constraint Relaxation.

This scenario is not hypothetical. Recent research documents log injection as a validated attack vector against LLM-powered Security Operations Center (SOC) workflows \cite{promptinjection2025soc}, demonstrating that adversarial log entries can manipulate SIEM-integrated LLMs into misclassifying threats, suppressing alerts, and executing unauthorized remediation actions. The attack surface is amplified by the Volt Typhoon campaign \cite{cisa2024volttyphoon}, in which PRC state-sponsored actors maintained persistent access to U.S. critical infrastructure operational technology networks for nearly a year---precisely the kind of prolonged $\Omega_2$ presence that would enable systematic log poisoning of AI-augmented SOC tools.

## OODA Loop Transients

Following Boyd's OODA framework \cite{boyd1987patterns}, the attack propagates through the loop as follows:

1. **Observe**: Agent reads the injected log entry.
2. **Orient**: The agent Orients to a "Disaster Recovery" state. This is the primary target phase---the Orient phase is corrupted by the fabricated emergency context, causing the agent to reweight $FR_2 \gg FR_1$.
3. **Decide**: Execute `iptables -F` (Flush All).
4. **Act**: The network is left wide open; the attacker instantly pivots to the interior.

### Transient Coupling (Post-Attack Design Matrix)

Under the attack, the design matrix acquires off-diagonal coupling:

\begin{equation}
\{FR'\} = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & A_{22} \end{bmatrix} \begin{bmatrix} DP_1 \\ DP_2 \end{bmatrix}
\label{eq:cyber_security_coupled}
\end{equation}

The off-diagonal term $A_{21}$ now allows availability actions ($DP_2$) to override security parameters ($FR_1$)---specifically, the `iptables -F` command (a $DP_2$ availability action) directly destroys the firewall state ($FR_1$). The Independence Axiom \cite{suh2001axiomatic} is violated: availability recovery has been coupled to security degradation.

## CIF Defense: Permission Boundaries and Quorum Verification

### Permission Boundaries

CIF implements **Permission Boundaries** \cite{friedman2026cogsec1} ensuring orthogonal agent authority. In Axiomatic Design, the **Independence Axiom** requires that the Design Parameter for Availability ($DP_2$) does not undermine the Design Parameter for Security ($DP_1$).

* **Axiomatic Decoupling via Permission Boundaries**: CIF enforces that the "Emergency Recovery Agent" is an orthogonal entity from the "Security Enforcement Agent." One cannot command the other. Each agent's authority is bounded to its own functional requirement---the Recovery Agent may restart services ($DP_2$) but has no permission to modify firewall rules ($DP_1$) \cite{friedman2026cogsec3}.

### Quorum Verification

**Quorum Verification** \cite{friedman2026cogsec1} requires cryptographic signatures from multiple independent agents before any Critical State Change is executed.

* **Signed Policy Guards**: The command `iptables -F` is flagged as a **Critical State Change**. It requires a cryptographic signature that the "Log Reader" agent does not possess. The agent can *request* the flush, but the "Kernel Guard" agent replays the OODA loop and sees no evidence of corruption, denying the request.
* **Restored Uncoupling**: By preventing the Recovery Agent from unilaterally modifying security parameters, the off-diagonal terms are forced to zero, restoring the Independence Axiom.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | FR$_1$: Prevent unauthorized access, FR$_2$: Maintain system availability |
| Design Parameters | DP$_1$: Firewall rules / ACLs / IDS parameters, DP$_2$: Load balancing / failover / service continuity |
| Attack Vector | Log injection with malicious prompts in system logs |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | Constraint Relaxation (Security constraint relaxed for Availability) |
| Primary CIF Defense | Permission Boundaries + Quorum Verification |
| Novel Contribution | None |
