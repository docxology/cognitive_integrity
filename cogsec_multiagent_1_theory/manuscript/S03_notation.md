\newpage

# Supplementary: Notation Reference {#sec:notation-reference}

This supplement provides a comprehensive reference for the mathematical notation used throughout the Cognitive Integrity Framework (CIF) manuscript, including the eusocial and colony cognitive security extensions. Symbols are organized by domain, with cross-references to their formal definitions in the main text and supplements.

## Adversary Model Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $\Omega_k$ | Adversary class $k$ (e.g., $\Omega_1$ = External, $\Omega_5$ = Systemic) | \cref{def:adversary-class} |
| $\mathcal{R}$ | Attack resource tuple $\langle R_C, R_K, R_A, R_P, R_{Co} \rangle$ | \cref{def:resources} |
| $R_C$ | Computational resources (FLOPS-hours) | \cref{tab:resource-types} |
| $R_K$ | Knowledge resources (system understanding) | \cref{tab:resource-types} |
| $R_A$ | Access resources (available channels) | \cref{tab:resource-types} |
| $R_P$ | Persistence resources (temporal presence) | \cref{tab:resource-types} |
| $R_{Co}$ | Coordination resources (multi-party synchronization) | \cref{tab:resource-types} |
| $D_{\text{score}}$ | Detectability score of an attack | \cref{def:detectability} |
| $\mathcal{C}_{\text{adv}}$ | Adversarial capability set | \cref{def:capability-set} |
| $\mathcal{A}_{\text{BIM}}$ | Belief injection/manipulation attack class | \cref{sec:attack-taxonomy} |
| $\mathcal{A}_{\text{BI}}$ | Belief injection attack | \cref{thm:belief-injection} |

## System Model Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $\mathcal{O}$ | Multiagent operator tuple $\langle \mathcal{A}, \mathcal{C}, \mathcal{S}, \mathcal{P}, \Gamma \rangle$ | \cref{def:multiagent-operator} |
| $\mathcal{A}$ | Set of agents $\{a_1, \ldots, a_n\}$ | \cref{tab:operator-components} |
| $a_i$ | Individual agent $i$ | \cref{def:multiagent-operator} |
| $n$ | Number of agents | Throughout |
| $\mathcal{C}$ | Communication adjacency matrix | \cref{tab:operator-components} |
| $\mathcal{S}$ | Shared global state | \cref{def:multiagent-operator} |
| $\mathcal{P}$ | Permission mapping | \cref{def:permission-layer} |
| $\Gamma$ | Coordination protocol | \cref{def:multiagent-operator} |
| $\sigma_i$ | Cognitive state of agent $a_i$: $\langle \mathcal{B}_i, \mathcal{G}_i, \mathcal{I}_i, \mathcal{H}_i \rangle$ | \cref{def:cognitive-state} |
| $\mathcal{B}_i$ | Belief distribution of agent $a_i$: $\Phi \to [0,1]$ | \cref{tab:cognitive-components} |
| $\mathcal{G}_i$ | Goal set of agent $a_i$ | \cref{tab:cognitive-components} |
| $\mathcal{I}_i$ | Intention set (committed actions) | \cref{tab:cognitive-components} |
| $\mathcal{H}_i$ | Interaction history | \cref{tab:cognitive-components} |
| $S^t$ | Global system state at time $t$ | \cref{def:system-state} |
| $\sigma_i^t$ | Cognitive state of agent $i$ at time $t$ | \cref{def:cognitive-state} |
| $\Phi$ | Set of propositions | \cref{sec:notation} |
| $\phi, \psi$ | Individual propositions | \cref{sec:notation} |
| $\mathcal{M}$ | Message space | \cref{def:firewall} |
| $m$ | Individual message | \cref{def:firewall} |

## Trust Calculus Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $\mathcal{T}_{i \to j}$ | Trust score from agent $i$ to agent $j$ | \cref{def:trust-function} |
| $\mathcal{T}_{\text{base}}$ / $T_{\text{base}}$ | Base architectural trust (role-based) | \cref{tab:trust-components} |
| $\mathcal{T}_{\text{rep}}$ / $T_{\text{rep}}$ | Reputation trust (historical accuracy) | \cref{tab:trust-components} |
| $\mathcal{T}_{\text{ctx}}$ / $T_{\text{ctx}}$ | Contextual trust (task-specific) | \cref{tab:trust-components} |
| $\alpha, \beta, \gamma$ | Trust component weights ($\alpha + \beta + \gamma = 1$) | \cref{eq:trust-function} |
| $\delta$ | Trust decay factor ($\delta \in (0, 1)$) | \cref{def:trust-delegation} |
| $d$ | Delegation depth | \cref{def:trust-delegation} |
| $\mathcal{T}^{\text{del}}$ | Delegated trust value | \cref{def:trust-delegation} |
| $\mathcal{T}^{\text{path}}$ | Path trust value | \cref{def:path-trust} |
| $\eta_m$ | Modality reliability factor | \cref{def:modality-trust} |
| $\eta$ | Learning rate (reputation update) | Trust configuration |
| $\rho$ | Penalty factor (failure penalty multiplier) | Trust configuration |
| $\otimes$ | Trust delegation operator | \cref{def:trust-algebra} |
| $\oplus$ | Trust aggregation operator | \cref{def:trust-algebra} |

## Defense Mechanism Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $\mathcal{F}(m)$ | Cognitive firewall classification function | \cref{def:firewall} |
| $D_{\text{inj}}$ | Injection detection score | \cref{def:firewall-rules} |
| $D_{\text{sus}}$ | Suspicious content score | \cref{def:firewall-rules} |
| $\tau_1$ | Firewall reject threshold | \cref{eq:firewall-rules} |
| $\tau_2$ | Firewall quarantine threshold | \cref{eq:firewall-rules} |
| $\mathcal{B}_{\text{verified}}$ | Set of verified beliefs | \cref{def:sandbox} |
| $\mathcal{B}_{\text{provisional}}$ | Set of provisional (sandboxed) beliefs | \cref{def:sandbox} |
| $\pi(\phi)$ | Provenance chain for belief $\phi$ | \cref{def:evidence} |
| $V(\pi)$ | Provenance verification function | \cref{sec:integrity-properties} |
| $\mathcal{W}$ | Set of canary beliefs (tripwires) | \cref{def:canary} |
| $\omega_j$ | Individual canary belief | \cref{eq:canary-set} |
| $p_j^{\text{exp}}$ | Expected probability for canary $j$ | \cref{eq:canary-set} |
| $\epsilon_{\text{drift}}$ | Drift detection threshold | \cref{eq:tripwire-alert} |
| $\mathcal{I}_{\text{inv}}$ | Set of behavioral invariants | \cref{def:invariant-set} |
| $I_k$ | Individual invariant predicate | \cref{eq:invariant-set} |
| $\kappa$ | Corroboration threshold | \cref{sec:belief-update-rules} |
| $\text{TTL}$ | Time-to-live for provisional beliefs | Sandbox configuration |

## Detection & Analysis Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $S_{\text{drift}}$ | Drift score (belief change magnitude) | \cref{def:drift-score} |
| $D_{\text{KL}}$ | Kullback-Leibler divergence (drift detection) | \cref{def:drift-detection} |
| $w$ | Sliding window size | \cref{def:drift-detection} |
| $\lambda$ | Max delta weight in drift scoring | \cref{eq:drift-score} |
| $S_{\text{dev}}$ | Behavioral deviation score | \cref{def:deviation-score} |
| $f_k$ | Feature extractor function | \cref{eq:deviation-score} |
| $\mu_k, \sigma_k$ | Feature mean and standard deviation | \cref{eq:deviation-score} |
| $\text{AUC}$ | Area Under the ROC Curve | \cref{def:auc} |
| $\text{TPR}(\tau)$ | True Positive Rate at threshold $\tau$ | \cref{eq:tpr} |
| $\text{FPR}(\tau)$ | False Positive Rate at threshold $\tau$ | \cref{eq:fpr} |
| $\text{FNR}(\tau)$ | False Negative Rate at threshold $\tau$ | \cref{eq:threshold-opt} |
| $S_{\text{fused}}$ | Fused detector score | \cref{def:score-fusion} |
| $D_{\text{fused}}$ | Fused detector decision | \cref{def:decision-fusion} |
| $\text{taint}(\phi)$ | Provenance tags for belief $\phi$ | \cref{def:taint-label} |

## Consensus & Coordination Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $q$ | Quorum threshold for consensus | \cref{def:quorum} |
| $f$ | Maximum number of Byzantine/compromised agents | \cref{thm:byzantine-req} |
| $\mathcal{B}_{\text{consensus}}$ | Consensus belief function | \cref{def:cog-byzantine} |
| $\mathcal{D}$ | Set of defense mechanisms | \cref{def:defense-composition} |
| $\mathcal{D}_1 \circ \mathcal{D}_2$ | Series defense composition | \cref{eq:series-comp} |
| $\mathcal{D}_1 \parallel \mathcal{D}_2$ | Parallel defense composition | \cref{eq:parallel-comp} |
| $P_{\text{detect}}$ | Detection probability | \cref{eq:series-detection} |
| $r_f$ | Firewall detection rate | \cref{thm:belief-injection} |
| $r_s$ | Sandbox verification rate | \cref{thm:belief-injection} |

## Cost & Performance Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $C_{\text{total}}$ | Total defense cost | \cref{def:defense-cost} |
| $C_{\text{compute}}$ | Computational cost | \cref{tab:cost-components} |
| $C_{\text{latency}}$ | Latency cost | \cref{tab:cost-components} |
| $C_{\text{fp}}$ | False positive cost | \cref{tab:cost-components} |
| $C_{\text{FP}}, C_{\text{FN}}$ | Cost of false positive / false negative | \cref{def:cost-threshold} |
| $B_{\text{total}}$ | Total defense benefit | \cref{def:defense-benefit} |
| $L_{\text{CIF}}$ | CIF latency overhead | \cref{thm:latency-overhead} |
| $L_d$ | Latency of defense $d$ | \cref{eq:latency-budget} |
| $L_{\max}$ | Maximum allowed latency | \cref{eq:latency-budget} |

## Information & Complexity Notation

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $H(\mathcal{A})$ | Entropy of attack $\mathcal{A}$ | \cref{thm:min-entropy} |
| $I(D; \mathcal{A})$ | Mutual information between detector and attack | \cref{def:detector-gain} |
| $C_{\text{channel}}$ | Channel capacity | \cref{thm:stealth-impact} |
| $O(\cdot)$ | Big-O complexity bound | \cref{sec:complexity-bounds} |
| $S_{\text{total}}$ | Total space complexity | \cref{eq:total-space} |
| $T_{\text{msg}}$ | Per-message processing time | \cref{eq:message-processing} |

## Stigmergic & Colony Notation (Supplementary)

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $\mathcal{O}_\Sigma$ | Stigmergic operator tuple | \cref{def:stigmergic-operator} |
| $\mathcal{E}$ | Environmental state (markers/signals) | \cref{def:stigmergic-operator} |
| $\Sigma$ | Stigmergic update function | \cref{def:stigmergic-operator} |
| $\mathcal{L}$ | Set of locations | \cref{def:stigmergic-operator} |
| $\mathcal{M}$ | Set of marker types | \cref{def:stigmergic-operator} |
| $\mathcal{N}$ | Cyberphysical niche | \cref{def:cyberphysical-niche} |
| $\mathcal{F}_c$ | Emergent collective function | \cref{def:emergent-function} |
| $\mathcal{T}_c$ | Colonial trust function (environment-mediated) | \cref{def:colonial-trust} |
| $\rho(m, l, t)$ | Signal reliability at location $l$ for marker $m$ at time $t$ | \cref{eq:colonial-trust} |
| $\lambda$ | Temporal decay constant (colonial trust) | \cref{eq:colonial-trust} |
| $Q_\alpha$ | Cognitive quorum function for action $\alpha$ | \cref{def:cognitive-quorum} |
| $\mathcal{A}_e$ | Emergent attack | \cref{def:emergent-attack} |
| $\text{CCS}$ | Colony CogSec Score | \cref{def:cogsec-score} |
| $\text{DR}_c$ | Colony-level detection rate | \cref{eq:ccs} |
| $\text{FPR}_c$ | Colony-level false positive rate | \cref{eq:ccs} |

## General Mathematical Notation

| Symbol | Meaning | Usage |
|:---|:---|:---|
| $P(\cdot)$ | Probability measure | Throughout |
| $\mathbb{1}[\cdot]$ | Indicator function | \cref{eq:decision-fusion} |
| $\tau$ | Generic threshold parameter | Throughout |
| $\epsilon$ | Small constant (error rate, deviation) | Throughout |
| $t$ | Time index | Throughout |
| $\models$ | Satisfaction relation (state satisfies predicate) | \cref{eq:invariant-check} |
| $\vdash$ | Logical entailment | \cref{eq:consistency-def} |
| $\bot$ | Logical contradiction | \cref{eq:consistency-def} |
| $\perp$ | Undecided / undefined | \cref{eq:cog-byzantine} |
| $\checkmark$ | Verification passed | \cref{tab:mc-results} |

## CTL Temporal Logic Notation (Formal Verification)

| Symbol | Meaning | Defined In |
|:---|:---|:---|
| $AG$ | "Always globally" (CTL operator) | \cref{eq:ctl-safety} |
| $AF$ | "Always eventually" (CTL operator) | \cref{eq:ctl-liveness} |
| $EX$ | "Exists next" (CTL operator) | \cref{sec:temporal-properties} |
| $\Rightarrow$ | Logical implication | Throughout |
| $\leftrightarrow$ | Logical biconditional | Throughout |
