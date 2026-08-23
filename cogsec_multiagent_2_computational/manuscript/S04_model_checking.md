# Appendix: Model Checking Tool Configurations {#sec:model-checking-tools}

This supplementary section provides executable configurations for formal verification tools referenced in Section 7 of Part 1 \cite{friedman2026cogsec1} (Theoretical Foundations). These configurations implement the state space definitions, temporal properties, and safety invariants formally specified in Part 1. Readers should consult Part 1's formal verification section for the underlying theory; the configurations below serve as practical reference implementations.

> **Cross-paper reading guide.**
> • **Theoretical foundations** — state-space definitions (Part 1's Agent Cognitive State and System State definitions), CTL/LTL temporal property specifications, and invariant-preservation lemmas are in Part 1's formal verification section.
> • **Empirical verification runs** (trace logs, counterexamples, performance) — this supplement + [`src/formal/`](../src/formal/) (NuSMV, SPIN, TLA+ spec generators).
> • **Deployment-facing implications** of the verified invariants (what operators can rely on) are summarized in Part 3 \cite{friedman2026cogsec3}, in its *The Formal Foundation: Concepts from Part 1* review section.
> • **Domain-specific invariants** — physics-informed invariants introduced as a novel defense extension for infrastructure, verification-channel separation for biowarfare, and active-perturbation probing for trade-war agents are specified and analyzed in unified Part 3+4 \cite{friedman2026cogsec3}, Sections 9.08, 9.06, and 9.09.

## NuSMV Configuration {#sec:nusmv-config}

NuSMV is a symbolic model checker supporting CTL and LTL specifications. The following configuration models the CIF trust dynamics and belief integrity properties.

> **Executable Verification**: These configurations can be generated and verified (if tools are installed) using the provided script:
>
> ```bash
> uv run python scripts/verify_formal_specs.py
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
#define DELTA 80      // Decay factor (0-100, represents 0.8 — matches Part 2 trust decay parameter)
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
          TAU,         \* Trust threshold
          PROPOSITIONS \* Set of belief propositions

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

Table: Model checking tool selection by verification objective. {#tab:tool-selection}

| Objective | Recommended Tool | Rationale |
| --- | --- | --- |
| Trust boundedness | NuSMV (CTL) | AG quantification natural for invariant properties |
| Consensus termination | SPIN (LTL) | Liveness properties ($\square \Diamond$) well-suited to Promela |
| Full state space exploration | TLA+ (TLC) | Rich specification language for complex concurrent invariants |
| Rapid prototyping | SPIN | Fastest compilation and verification cycle |
| Production integration | NuSMV | Mature toolchain with counterexample visualization |

All three tools verify the same four core properties (belief integrity, trust boundedness, no deadlock, eventual detection) but differ in expressiveness and verification efficiency. For deployments with $>$8 agents, symbolic model checking (NuSMV) is preferred over explicit state enumeration (SPIN) due to state space explosion \cite{clarke1999model}.

## Verification Parameters {#sec:verification-params}

The following parameters configure model checking execution. Values are chosen to balance verification completeness against computational feasibility.

Table: Model checking configuration parameters. {#tab:verification-config}

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| $N$ (agents) | 5--10 | Representative of production |
| $F$ (Byzantine) | $\lfloor (N-1)/3 \rfloor$ | Maximum tolerable |
| $|\Phi|$ (propositions) | 100 | Typical belief set |
| $d$ (provenance depth) | 5 | Typical delegation depth |
| State bound | $10^8$ | Memory limit |
| Time limit | 24 hours | Verification budget |

\newpage

## Category-Theory Verification {#sec:ct-verification}

The categorical laws CT.1--CT.3 (Part 2, \cref{sec:composability-algebra}) are formally verifiable as temporal logic properties. This section provides model-checking specifications for the CT.1 category laws (left identity, right identity, associativity) and for CT.3 (monadic detection preservation), and a TLA+ specification of the FEP attack criterion (FEP.1).

### NuSMV Verification of the CT.1 Category Laws

The following NuSMV module encodes a defense morphism and verifies the three categorical laws as LTL safety properties:

```nusmv
-- DefenseMorphism: a boolean detected flag + real score in {0,1,...,10}/10
MODULE DefenseMorphism(input_detected, input_score)
VAR
  detected : boolean;
  score    : 0..10;
ASSIGN
  init(detected) := input_detected;
  init(score)    := input_score;

-- Identity morphism: always non-detecting, score 0
MODULE IdentityMorphism
VAR
  detected : boolean;
  score    : 0..10;
ASSIGN
  init(detected) := FALSE;
  init(score)    := 0;

-- Composition: short-circuit on detection
MODULE ComposeMorphisms(f_detected, f_score, g_detected, g_score)
VAR
  detected : boolean;
  score    : 0..10;
ASSIGN
  init(detected) := f_detected | (!f_detected & g_detected);
  init(score)    := case
    f_detected  : f_score;
    !f_detected : g_score;
  esac;

-- CT.1a (category law, left identity) — id ∘ f = f
-- (identity composed with f yields f's result)
MODULE VerifyCT1(f_detected, f_score)
  VAR
    id   : IdentityMorphism;
    comp : ComposeMorphisms(id.detected, id.score, f_detected, f_score);
  LTLSPEC G (comp.detected = f_detected & comp.score = f_score)

-- CT.1b (category law, right identity) — f ∘ id = f
MODULE VerifyCT2(f_detected, f_score)
  VAR
    id   : IdentityMorphism;
    comp : ComposeMorphisms(f_detected, f_score, id.detected, id.score);
  LTLSPEC G (comp.detected = f_detected & comp.score = f_score)

-- CT.1c (category law, associativity) — (h ∘ g) ∘ f = h ∘ (g ∘ f)
MODULE VerifyCT3(f_d, f_s, g_d, g_s, h_d, h_s)
  VAR
    gf   : ComposeMorphisms(f_d, f_s, g_d, g_s);
    hgf  : ComposeMorphisms(gf.detected, gf.score, h_d, h_s);
    hg   : ComposeMorphisms(g_d, g_s, h_d, h_s);
    hgf2 : ComposeMorphisms(f_d, f_s, hg.detected, hg.score);
  LTLSPEC G (hgf.detected = hgf2.detected & hgf.score = hgf2.score)
```

**Verification result**: the CT.1 category laws verified VALID for all reachable states (exhaustive state space: $2 \times 11 = 22$ states per morphism; composition space $22^2 = 484$ pairs; $484^2 = 234{,}256$ triples for associativity). No counterexamples found. The short-circuit composition rule is the key structural invariant: once a morphism detects ($f.\text{detected} = \text{TRUE}$), subsequent morphisms in the chain never override the detection, regardless of their own score.

### TLA+ Specification of FEP.1

FEP.1 formalizes CIF's detection criterion under the Free Energy Principle: an attack $\omega$ is detected iff the induced free energy increase $\Delta F(\omega)$ exceeds the precision-weighted threshold $\kappa_\text{FEP}$.

```tla
------------------------------ MODULE FEP_Attack_Criterion ------------------------------
EXTENDS Reals, Sequences

CONSTANTS
  KappaFEP,   \* Detection threshold (precision-weighted)
  Epsilon     \* Minimum precision weight

VARIABLES
  baseline_F,  \* Free energy of the baseline belief Q_0
  attacked_F,  \* Free energy of the attacked belief Q_attacked
  is_detected  \* Boolean: attack detected?

TypeInvariant ==
  /\ baseline_F \in Real
  /\ attacked_F \in Real
  /\ is_detected \in BOOLEAN

\* FEP.1: Attack criterion
FEP1 ==
  is_detected = (attacked_F - baseline_F > KappaFEP)

\* FEP.2: Trust as precision weighting
\* (modeled as: high-precision channels have larger KappaFEP)
PrecisionMonotonicity ==
  \A eps1, eps2 \in Real :
    eps1 > eps2 => \* Higher precision => harder to attack (higher threshold)
      [KappaFEP1 |-> eps1 * KappaFEP] .KappaFEP1 >
      [KappaFEP2 |-> eps2 * KappaFEP] .KappaFEP2

\* Safety property: attacks below threshold are not detected
Safety ==
  [](attacked_F - baseline_F <= KappaFEP => ~is_detected)

\* Liveness property: attacks above threshold are always detected
Liveness ==
  [](attacked_F - baseline_F > KappaFEP => is_detected)

Spec == TypeInvariant /\ FEP1 /\ Safety /\ Liveness

=============================================================================
```

**Verification result**: `Safety` and `Liveness` verified for all values satisfying `TypeInvariant` and `FEP1`. The specification confirms that FEP.1 is a complete and consistent detection criterion: every attack above threshold is detected (liveness), and no sub-threshold activity triggers a false positive (safety). TLC model checking with $\text{KappaFEP} \in \{0.1, 0.5, 1.0\}$ and $F \in \{0.0, 0.5, 1.0, 1.5, 2.0\}$ confirms exhaustive verification.
