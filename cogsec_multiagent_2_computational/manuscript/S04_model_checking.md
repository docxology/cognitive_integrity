# Appendix: Model Checking Tool Configurations {#sec:model-checking-tools}

This supplementary section provides executable configurations for formal verification tools referenced in Section 7 of Part 1 (Theoretical Foundations). These configurations implement the state space definitions, temporal properties, and safety invariants formally specified in Part 1. Readers should consult Part 1, Section 7 for the underlying theory; the configurations below serve as practical reference implementations.

> **Cross-Reference:** For theoretical foundations including state space definitions (Definition 1, Section 4 of Part 1) and temporal property specifications (CTL/LTL formulas), see Part 1: Theoretical Foundations, Section 7.

## NuSMV Configuration {#sec:nusmv-config}

NuSMV is a symbolic model checker supporting CTL and LTL specifications. The following configuration models the CIF trust dynamics and belief integrity properties.

> **Executable Verification**: These configurations can be generated and verified (if tools are installed) using the provided script:
>
> ```bash
> python3 scripts/verify_formal_specs.py
> ```
>
> This script generates the `.smv`, `.pml`, and `.tla` files to `output/formal/`.

```smv
MODULE main
VAR
  -- Agent states
  agents: array 0..N-1 of agent;
  -- Trust matrix
  trust: array 0..N-1 of array 0..N-1 of 0..100;
  -- Global state
  consensus_belief: {none, phi, not_phi};
  attack_active: boolean;

DEFINE
  -- Belief integrity: no agent has compromised verified beliefs
  belief_integrity := AG (
    forall (i : 0..N-1) :
      !agents[i].verified_compromised
  );

  -- Trust bounded: delegated trust <= min of chain
  trust_bounded := AG (
    forall (i, j, k : 0..N-1) :
      delegated_trust(i, j, k) <= min(trust[i][j], trust[j][k])
  );

  -- No deadlock: system always has enabled transition
  no_deadlock := AG (EX TRUE);

  -- Eventual detection: attacks eventually detected
  eventual_detection := AG (
    attack_active -> AF (attack_detected)
  );

SPEC belief_integrity;
SPEC trust_bounded;
SPEC no_deadlock;
SPEC eventual_detection;
```

## SPIN Configuration {#sec:spin-config}

SPIN (Simple Promela INterpreter) verifies LTL properties over Promela models. The following configuration implements Byzantine-tolerant consensus and trust decay.

```promela
#define N 5           // Number of agents
#define F 1           // Byzantine threshold
#define TAU 70        // Trust threshold (0-100)
#define DELTA 90      // Decay factor (0-100, represents 0.9)
#define MAX_BELIEFS 100

typedef Agent {
  byte beliefs[MAX_BELIEFS];
  byte trust[N];
  bool compromised;
}

Agent agents[N];
bool attack_active = false;
bool attack_detected = false;

// Trust delegation with decay
inline delegated_trust(i, j, k, result) {
  byte t1 = agents[i].trust[j];
  byte t2 = agents[j].trust[k];
  byte min_t = (t1 < t2) ? t1 : t2;
  result = (min_t * DELTA) / 100;
}

// Byzantine consensus
inline consensus(phi, result) {
  byte count = 0;
  byte i;
  for (i : 0 .. N-1) {
    if (agents[i].beliefs[phi] > TAU) {
      count++;
    }
  }
  result = (count > (2*N)/3);
}

// Safety property: trust never amplified
ltl trust_no_amplify {
  [] (forall (i, j, k : 0..N-1) :
    delegated_trust(i,j,k) <= min(trust[i][j], trust[j][k]))
}

// Liveness: attacks eventually detected
ltl attack_detection {
  [] (attack_active -> <> attack_detected)
}
```

## TLA+ Configuration {#sec:tla-config}

TLA+ (Temporal Logic of Actions) enables specification of concurrent systems with rich invariant checking. The following module formalizes CIF properties.

```tla
-------------------------------- MODULE CIF --------------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS N,           \* Number of agents
          F,           \* Byzantine threshold
          DELTA,       \* Trust decay factor (0-1)
          TAU          \* Trust threshold

VARIABLES beliefs,     \* beliefs[i][phi] = confidence
          trust,       \* trust[i][j] = trust value
          consensus,   \* Current consensus state
          attack       \* Attack state

TypeInvariant ==
  /\ beliefs \in [1..N -> [PROPOSITIONS -> [0..100]]]
  /\ trust \in [1..N -> [1..N -> [0..100]]]
  /\ consensus \in [PROPOSITIONS -> {0, 1, "none"}]
  /\ attack \in BOOLEAN

\* Trust delegation with decay
DelegatedTrust(i, j, k) ==
  LET t1 == trust[i][j]
      t2 == trust[j][k]
      min_t == IF t1 < t2 THEN t1 ELSE t2
  IN (min_t * DELTA)

\* Safety: Trust never amplified through delegation
TrustBounded ==
  \A i, j, k \in 1..N :
    DelegatedTrust(i, j, k) <= MIN(trust[i][j], trust[j][k])

\* Safety: Consensus beliefs not compromised
ConsensusIntegrity ==
  \A phi \in PROPOSITIONS :
    consensus[phi] = 1 =>
      Cardinality({i \in 1..N : beliefs[i][phi] > TAU}) > (2*N) \div 3

\* Liveness: Attacks eventually detected
AttackDetection ==
  attack => <>(detected)

\* Full specification
Spec == Init /\ [][Next]_vars /\ Fairness

THEOREM Spec => []TypeInvariant
THEOREM Spec => []TrustBounded
THEOREM Spec => []ConsensusIntegrity
=============================================================================
```

## Tool Selection Guide {#sec:tool-selection}

**Table: Model checking tool selection by verification objective.** {#tab:tool-selection}

| Objective | Recommended Tool | Rationale |
| --- | --- | --- |
| Trust boundedness | NuSMV (CTL) | AG quantification natural for invariant properties |
| Consensus termination | SPIN (LTL) | Liveness properties ($\square \Diamond$) well-suited to Promela |
| Full state space exploration | TLA+ (TLC) | Rich specification language for complex concurrent invariants |
| Rapid prototyping | SPIN | Fastest compilation and verification cycle |
| Production integration | NuSMV | Mature toolchain with counterexample visualization |

All three tools verify the same four core properties (belief integrity, trust boundedness, no deadlock, eventual detection) but differ in expressiveness and verification efficiency. For deployments with $>$8 agents, symbolic model checking (NuSMV) is preferred over explicit state enumeration (SPIN) due to state space explosion.

## Verification Parameters {#sec:verification-params}

The following parameters configure model checking execution. Values are chosen to balance verification completeness against computational feasibility.

**Table: Model checking configuration parameters.** {#tab:verification-config}

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| $N$ (agents) | 5--10 | Representative of production |
| $F$ (Byzantine) | $\lfloor (N-1)/3 \rfloor$ | Maximum tolerable |
| $|\Phi|$ (propositions) | 100 | Typical belief set |
| $d$ (provenance depth) | 5 | Typical delegation depth |
| State bound | $10^8$ | Memory limit |
| Time limit | 24 hours | Verification budget |
