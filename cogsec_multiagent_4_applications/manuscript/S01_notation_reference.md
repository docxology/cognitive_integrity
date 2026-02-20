# Supplementary Material S1: Notation Reference

This supplement provides a compact reference for all mathematical notation used in this paper. Definitions originate from Paper 1 \cite{friedman2026cogsec1} unless noted otherwise.

## Cognitive State Notation (Paper 1)

| Symbol | Name | Definition |
| -------- | ------ | ----------- |
| $\sigma_i$ | Cognitive state of agent $i$ | $\sigma_i = \langle \mathcal{B}_i, \mathcal{G}_i, \mathcal{I}_i, \mathcal{H}_i \rangle$ |
| $\mathcal{B}_i$ | Belief set | Probability distribution over propositions |
| $\mathcal{G}_i$ | Goal set | Prioritized objectives with utility weights |
| $\mathcal{I}_i$ | Intention set | Committed action plans |
| $\mathcal{H}_i$ | History | Interaction trace (messages, actions, observations) |
| $\Sigma$ | System state | $\Sigma = \{\sigma_1, \ldots, \sigma_n\}$ for $n$ agents |

## Trust Calculus (Paper 1)

| Symbol | Name | Definition |
| -------- | ------ | ----------- |
| $\mathcal{T}_{i \to j}$ | Trust from agent $i$ to agent $j$ | $\mathcal{T}_{i \to j}^t = \alpha \cdot T_{\text{base}}(j) + \beta \cdot T_{\text{rep}}^t(j) + \gamma \cdot T_{\text{ctx}}^t(i,j)$ |
| $T_{\text{base}}$ | Architectural trust | Role-based, static assignment |
| $T_{\text{rep}}$ | Reputation trust | Historical accuracy, time-decayed |
| $T_{\text{ctx}}$ | Context trust | Task-specific, situational |
| $\delta$ | Delegation decay factor | $\delta \in (0,1)$; trust decays as $\delta^d$ over delegation depth $d$ |

## Defense Mechanism Notation (Paper 1)

| Symbol | Name | Definition |
| -------- | ------ | ----------- |
| $\mathcal{F}(m)$ | Cognitive Firewall | $\mathcal{F}(m) \to \{\text{accept}, \text{quarantine}, \text{reject}\}$ |
| $\tau$ | Firewall threshold | Trust score cutoff for accept/reject decision |
| $\mathcal{B}_{\text{verified}}$ | Verified belief partition | Beliefs promoted through corroboration protocol |
| $\mathcal{B}_{\text{provisional}}$ | Provisional belief partition | Sandboxed beliefs awaiting verification |
| $\mathcal{W}$ | Canary belief set (Tripwires) | Sentinel beliefs that trigger alerts if modified |
| $\text{INV}_k$ | Behavioral invariant $k$ | Runtime predicate: $\text{INV}_k(\sigma_i) \in \{\text{true}, \text{false}\}$ |
| $S_{\text{drift}}$ | Drift detection score | $S_{\text{drift}} = \KL(\mathcal{B}_i^t \| \mathcal{B}_i^{t-1})$ |
| $\epsilon$ | Drift threshold | Maximum tolerable KL divergence |
| $\mathcal{B}_{\text{consensus}}$ | Byzantine consensus belief | Agreed-upon belief across quorum $q$ of agents |
| $q$ | Quorum size | Minimum agents required for consensus; $n \geq 3f+1$ |
| $f$ | Byzantine fault tolerance | Maximum number of compromised agents tolerated |

## Adversary Taxonomy (Paper 1)

| Symbol | Class | Scope | Access |
| -------- | ------- | ------- | -------- |
| $\Omega_1$ | External | User boundary | Direct prompt manipulation |
| $\Omega_2$ | Peripheral | Data/tool channels | Indirect injection via data poisoning |
| $\Omega_3$ | Agent-level | Single agent | Compromised agent with modified goals |
| $\Omega_4$ | Coordination | Inter-agent | Man-in-the-middle on agent communication |
| $\Omega_5$ | Systemic | Orchestrator | Full framework-level compromise |

## Axiomatic Design Notation (This Paper)

| Symbol | Name | Definition |
| -------- | ------ | ----------- |
| $\{FR\}$ | Functional Requirements vector | Objectives the system must satisfy |
| $\{DP\}$ | Design Parameters vector | Variables chosen to satisfy FRs |
| $[A]$ | Design Matrix | Maps DPs to FRs: $\{FR\} = [A]\{DP\}$ |
| $A_{ij}$ | Matrix element | Coupling coefficient: $\partial FR_i / \partial DP_j$ |
| $[A']$ | Coupled Design Matrix | Post-attack matrix with off-diagonal terms introduced by adversary |

**Design Matrix States:**

- **Uncoupled** (diagonal $[A]$): Each FR depends on exactly one DP. Independence Axiom satisfied.
- **Decoupled** (triangular $[A]$): FRs can be satisfied sequentially. Acceptable but fragile.
- **Coupled** ($[A']$ with off-diagonal terms): FRs interfere. Adversarial transient coupling makes the system unstable.

## OODA Loop Notation (This Paper)

| Phase | Function | CIF Attack Surface |
| ------- | ---------- | ------------------- |
| **Observe** | Sense environment, ingest data | Data channel integrity (sensors, APIs, logs) |
| **Orient** | Synthesize observations with prior knowledge | **Primary target of Goal Hijacking**: internal model corruption |
| **Decide** | Select action based on oriented model | Action space restriction, capability elicitation |
| **Act** | Execute selected action | Unauthorized action execution |

## OODA Phase $\leftrightarrow$ CIF Defense Mapping

| OODA Phase | Primary CIF Defense | Mechanism |
| ------------ | ------------------- | ----------- |
| Observe | Cognitive Firewall ($\mathcal{F}$) | Filter/classify incoming data before it reaches Orientation |
| Orient | Belief Sandboxing ($\mathcal{B}_{\text{provisional}}$), Drift Detection ($S_{\text{drift}}$) | Isolate new beliefs; detect sudden orientation shifts |
| Decide | Behavioral Invariants ($\text{INV}_k$) | Verify decisions against pre-defined safety predicates |
| Act | Byzantine Consensus ($\mathcal{B}_{\text{consensus}}$) | Require multi-agent agreement before critical actions |
| All phases | Behavioral Invariants ($\text{INV}_k$) | Continuous runtime monitoring across the full cycle |

## Universal Attack Patterns (This Paper)

| Pattern | Description | Design Matrix Effect |
| --------- | ------------- | --------------------- |
| **FR Polarity Inversion** | Adversary flips a negative FR (minimize cost) to positive (maximize output of harmful byproduct) | Diagonal element $A_{ii}$ changes sign |
| **Constraint Relaxation** | Hard safety constraint degraded to soft preference | Diagonal element $A_{ii}$ reduced toward zero |
| **Context Boundary Violation** | Isolated operational contexts bleed together (e.g., simulation $\to$ operational) | Off-diagonal element $A_{ij}$ introduced where $i \neq j$ |
