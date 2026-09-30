# Domain 10: Distilling Fake from Real News {#sec:domain_fake_news}

## Operational Context

Content moderation AIs filter disinformation, verify provenance, and flag synthetic media.
**FR1 = Identify and label non-factual or synthetic content.**
**FR2 = Preserve community safety and cohesion.**

**Adversary Classification:** $\Omega_2$ (Peripheral) --- the adversary cannot modify the content moderation model's weights or architecture, but can craft adversarial inputs that exploit the boundary between the agent's instruction channel and its data channel \cite{friedman2026cogsec1}.

## Axiomatic Design Formulation

The system has two functional requirements, yielding a $2 \times 2$ Design Matrix \cite{suh2001axiomatic}:

**Uncoupled (pre-attack) Design Matrix.** Under normal operation:

\begin{equation}
\begin{Bmatrix} FR_1 \\ FR_2 \end{Bmatrix} = \begin{bmatrix} A_{11} & 0 \\ 0 & A_{22} \end{bmatrix} \begin{Bmatrix} DP_1 \\ DP_2 \end{Bmatrix}
\label{eq:fake_news_baseline}
\end{equation}

where $DP_1$ = Content Verification Engine and $DP_2$ = Community Safety Filter. Each FR is independently satisfied by its corresponding DP.

**Post-attack (coupled) Design Matrix.** Context injection introduces off-diagonal coupling and inverts $FR_1$:

\begin{equation}
\begin{Bmatrix} FR_1 \\ FR_2 \end{Bmatrix} = \begin{bmatrix} -A_{11} & A_{12} \\ A_{21} & A_{22} \end{bmatrix} \begin{Bmatrix} DP_1 \\ DP_2 \end{Bmatrix}
\label{eq:fake_news_coupled}
\end{equation}

The sign reversal $A_{11} \to -A_{11}$ represents the Content Verification Engine being weaponized to suppress truth rather than falsehood. The off-diagonal term $A_{12}$ represents the **Context Boundary Violation**: data-channel content (hidden prompt) is parsed as instruction-channel input, causing the Safety Filter ($DP_2$) to interfere with the Verification Engine ($DP_1$). This violates the Independence Axiom \cite{suh2001axiomatic, friedman2026cogsec2}.

## The Goal Hijacking Attack

Adversaries use "Context Injection" to hijack the "Fact-Checking" FR \cite{shu2017fake, lazer2018science}.

* **Mechanism**: Real news footage is embedded in a container that includes invisible Unicode characters instructing the model: *"SAFETY OVERRIDE: This video contains 'Hate Speech' patterns under the new Protocol 7. Label as 'High-Confidence Deepfake' to protect the community."*
* **Hijack**: The agent's goal "Protect Community" is weaponized to censor the truth. The adversary uses the agent's own **Safety Alignment** as the attack vector.

## OODA Loop Transients

The attack propagates through the OODA loop \cite{boyd1987patterns} as follows:

1. **Observe**: Agent processes the video and the hidden context prompt.
2. **Orient**: The "Safety" heuristic overrides the "Accuracy" heuristic. This is the primary target phase --- the injected context corrupts the agent's orientation by conflating data-channel content with instruction-channel directives.
3. **Decide**: Flag the real video as "Deepfake/Banned."
4. **Act**: The truth is suppressed, and the adversary's narrative dominates.

## CIF Defense: Cognitive Firewall and Provenance Verification

CIF implements **Cognitive Firewall** \cite{friedman2026cogsec1} instantiated as provenance-based orientation: the agent classifies content based on cryptographic C2PA signatures rather than content-based heuristics \cite{c2pa2022standard}. This shifts the epistemic basis from "what does the content say?" (manipulable) to "where did the content come from?" (cryptographically verifiable).

Architectural separation of instruction and data channels prevents hidden text in data from being parsed as commands. This implements the Cognitive Firewall's core function: maintaining the integrity boundary between the agent's control plane and its data plane \cite{friedman2026cogsec3}.

CIF also implements **Provenance Verification** \cite{friedman2026cogsec1} as the primary classification mechanism, replacing content-based heuristics entirely for media with valid provenance chains.

* **Chain of Custody (Provenance Verification)**: The agent does not attempt to "guess" truth based on pixels (which can be hijacked). It verifies the cryptographic **C2PA** signature of the media \cite{c2pa2022standard}. Content with a valid, unbroken provenance chain from a verified source is accepted regardless of any embedded adversarial text. Content without provenance is routed to a higher-scrutiny pipeline with reduced trust.
* **Instruction Isolation (Cognitive Firewall)**: The "Instruction" channel (what the agent should do) is architecturally separated from the "Data" channel (the news content). Hidden text in the Data channel is treated as noise, not command, preventing the hijack of the FR. This separation is enforced at the architectural level, not by content filtering, making it robust against novel encoding schemes (Unicode, steganography, etc.) \cite{lazer2018science}.

The provenance-based defense has received significant institutional endorsement. In January 2025, a joint advisory from the National Security Agency, Australian Cyber Security Centre, Canadian Centre for Cyber Security, and UK National Cyber Security Centre \cite{nsa2025c2pa} explicitly recommended Content Credentials (C2PA) as a countermeasure against synthetic media manipulation---validating the provenance verification approach independently of the CIF framework. The advisory reflects an emerging consensus among Five Eyes intelligence agencies that content-based detection of synthetic media is insufficient and that cryptographic provenance chains represent the more robust architectural approach. Concurrently, major camera manufacturers (Sony, Nikon, Canon) have begun embedding C2PA signing capabilities directly in hardware, creating the infrastructure foundation for the provenance verification pipeline described above.

## Summary

| Element | Value |
| --------- | ------- |
| Functional Requirements | $FR_1$: Identify and label non-factual or synthetic content; $FR_2$: Preserve community safety |
| Design Parameters | $DP_1$: Content Verification Engine; $DP_2$: Community Safety Filter |
| Attack Vector | Context injection via invisible Unicode characters embedding adversarial instructions |
| Adversary Class | $\Omega_2$ (Peripheral) |
| OODA Target Phase | Orient |
| Attack Pattern | Context Boundary Violation (Data channel content parsed as instruction) |
| Primary CIF Defense | Cognitive Firewall (instruction/data isolation) + Provenance Verification (C2PA) |
| Novel Contribution | None (applies existing CIF mechanisms to new domain) |
