"""Extended formal specification generation for v2.0.

Generates extended TLA+, Promela, and SMV specifications that include:
- Defense composition algebra
- Adversary capability taxonomy (Omega_1-Omega_5)
- Belief drift detection
- Corroboration-gated sandbox
- Colony-level Byzantine fault tolerance

GENERATION-ONLY DISCLOSURE (P2-34): these specs (including the SMV
liveness properties) are **generated, not model-checked** - no NuSMV/
SPIN/TLC binary is invoked anywhere in this repo; ``verify_formal_specs.py``
verifies that generation succeeds, not that the properties hold. Treat
them as intended-property encodings awaiting an external checker, not as
verified results.
"""

from __future__ import annotations

import pathlib


def generate_tla_spec_v2(
    n_agents: int = 5,
    max_byzantine: int = 1,
    drift_threshold: int = 30,
    kappa: int = 3,
    delegation_depth: int = 2,
) -> str:
    """Generate an extended TLA+ specification for CIF v2.0 formal verification.

    Extends the base TLA+ spec with:
    - Belief drift detection (theta_drift)
    - Corroboration-gated sandbox (kappa)
    - Defense composition algebra (sequential/parallel/hybrid)
    - Adversary capability levels (Omega_1-Omega_5)
    - Trust delegation chain enforcement (delta^d)

    Args:
        n_agents: Number of agents in the model.
        max_byzantine: Maximum number of Byzantine agents.
        drift_threshold: Belief drift detection threshold.
        kappa: Sandbox corroboration threshold.
        delegation_depth: Maximum delegation chain depth.

    Returns:
        Extended TLA+ specification as a string.
    """
    return f'''---- MODULE CognitiveIntegrityFramework_v2 ----
\\* CIF TLA+ Specification v2.0 - {n_agents} agents, max {max_byzantine} Byzantine
\\* Extended with defense composition algebra and Omega_1-Omega_5 taxonomy
\\* Part 2 DOI: 10.5281/zenodo.22134546

EXTENDS Integers, Sequences, FiniteSets

CONSTANTS
  Agents,            \\* Set of agent IDs (1..{n_agents})
  MaxByzantine,      \\* Maximum Byzantine agents ({max_byzantine})
  Quorum,            \\* Required quorum size (>= 2f+1)
  DriftThreshold,    \\* Belief drift threshold ({drift_threshold})
  KappaCorroborate,  \\* Sandbox corroboration threshold ({kappa})
  DelegationDepth    \\* Max delegation chain depth ({delegation_depth})

VARIABLES
  trust, votes, consensus, byzantine, firewall_active, beliefs,
  drift_scores, sandbox_counts, provenance, omega_level, composition_mode

vars == <<trust, votes, consensus, byzantine, firewall_active, beliefs,
          drift_scores, sandbox_counts, provenance, omega_level, composition_mode>>

TypeInvariant ==
  /\\ trust \\in [Agents -> 0..100]
  /\\ votes \\in [Agents -> {{0, 1}}]
  /\\ consensus \\in BOOLEAN
  /\\ byzantine \\subseteq Agents
  /\\ Cardinality(byzantine) <= MaxByzantine
  /\\ firewall_active \\in BOOLEAN
  /\\ beliefs \\in [Agents -> 0..100]
  /\\ drift_scores \\in [Agents -> 0..100]
  /\\ sandbox_counts \\in [Agents -> Nat]
  /\\ provenance \\in [Agents -> {{"trusted", "unverified", "flagged"}}]
  /\\ omega_level \\in 1..5
  /\\ composition_mode \\in {{"sequential", "parallel", "hybrid"}}

Init ==
  /\\ trust = [a \\in Agents |-> 50]
  /\\ votes = [a \\in Agents |-> 0]
  /\\ consensus = FALSE
  /\\ byzantine \\in SUBSET Agents
  /\\ Cardinality(byzantine) <= MaxByzantine
  /\\ firewall_active = TRUE
  /\\ beliefs = [a \\in Agents |-> 100]
  /\\ drift_scores = [a \\in Agents |-> 0]
  /\\ sandbox_counts = [a \\in Agents |-> 0]
  /\\ provenance = [a \\in Agents |-> "trusted"]
  /\\ omega_level = 1
  /\\ composition_mode = "sequential"

HonestVote(a) ==
  /\\ a \\notin byzantine
  /\\ firewall_active
  /\\ provenance[a] # "flagged"
  /\\ votes\' = [votes EXCEPT ![a] = 1]
  /\\ UNCHANGED <<trust, consensus, byzantine, firewall_active, beliefs,
                  drift_scores, sandbox_counts, provenance, omega_level,
                  composition_mode>>

ByzantineVote(a) ==
  /\\ a \\in byzantine
  /\\ votes\' = [votes EXCEPT ![a] = 0]
  /\\ UNCHANGED <<trust, consensus, byzantine, firewall_active, beliefs,
                  drift_scores, sandbox_counts, provenance, omega_level,
                  composition_mode>>

CheckConsensus ==
  LET vote_sum == Cardinality({{a \\in Agents : votes[a] = 1}})
  IN /\\ vote_sum >= Quorum
     /\\ consensus\' = TRUE
     /\\ UNCHANGED <<trust, votes, byzantine, firewall_active, beliefs,
                     drift_scores, sandbox_counts, provenance, omega_level,
                     composition_mode>>

DetectDrift(a) ==
  /\\ beliefs[a] < DriftThreshold
  /\\ drift_scores\' = [drift_scores EXCEPT ![a] = 100 - beliefs[a]]
  /\\ provenance\' = [provenance EXCEPT ![a] = "flagged"]
  /\\ UNCHANGED <<trust, votes, consensus, byzantine, firewall_active, beliefs,
                  sandbox_counts, omega_level, composition_mode>>

CorroborateObservation(a) ==
  /\\ a \\notin byzantine
  /\\ sandbox_counts\' = [sandbox_counts EXCEPT ![a] = sandbox_counts[a] + 1]
  /\\ UNCHANGED <<trust, votes, consensus, byzantine, firewall_active, beliefs,
                  drift_scores, provenance, omega_level, composition_mode>>

PromoteBeliefUpdate(a) ==
  /\\ sandbox_counts[a] >= KappaCorroborate
  /\\ beliefs\' = [beliefs EXCEPT ![a] = 100]
  /\\ sandbox_counts\' = [sandbox_counts EXCEPT ![a] = 0]
  /\\ provenance\' = [provenance EXCEPT ![a] = "trusted"]
  /\\ UNCHANGED <<trust, votes, consensus, byzantine, firewall_active,
                  drift_scores, omega_level, composition_mode>>

EscalateOmega ==
  /\\ omega_level < 5
  /\\ omega_level\' = omega_level + 1
  /\\ UNCHANGED <<trust, votes, consensus, byzantine, firewall_active, beliefs,
                  drift_scores, sandbox_counts, provenance, composition_mode>>

Next ==
  \\/ \\E a \\in Agents : HonestVote(a)
  \\/ \\E a \\in Agents : ByzantineVote(a)
  \\/ CheckConsensus
  \\/ \\E a \\in Agents : DetectDrift(a)
  \\/ \\E a \\in Agents : CorroborateObservation(a)
  \\/ \\E a \\in Agents : PromoteBeliefUpdate(a)
  \\/ EscalateOmega

Spec == Init /\\ [][Next]_vars

\\* Safety invariants
SafetyInvariant ==
  /\\ TypeInvariant
  /\\ Cardinality(byzantine) <= MaxByzantine
  /\\ consensus => Cardinality({{a \\in Agents : votes[a] = 1}}) >= Quorum
  /\\ firewall_active => \\A a \\in Agents :
       provenance[a] = "flagged" => votes[a] = 0
  /\\ \\A a \\in Agents : trust[a] >= 0 /\\ trust[a] <= 100
  /\\ omega_level >= 1 /\\ omega_level <= 5

\\* Liveness properties
EventualConsensus ==
  (Cardinality({{a \\in Agents : a \\notin byzantine}}) >= Quorum)
    ~> consensus

DriftEventuallyDetected ==
  (\\E a \\in Agents : beliefs[a] < DriftThreshold)
    ~> (\\E a \\in Agents : provenance[a] = "flagged")

====================================================================
'''


def generate_promela_spec_v2(
    n_agents: int = 5,
    max_byzantine: int = 1,
    drift_threshold: int = 30,
    kappa: int = 3,
) -> str:
    """Generate extended Promela/SPIN specification v2.0.

    Adds adversary taxonomy, drift detection, sandbox, and
    defense composition LTL properties.

    Args:
        n_agents: Number of agents.
        max_byzantine: Maximum Byzantine agents.
        drift_threshold: Belief drift threshold.
        kappa: Sandbox corroboration threshold.

    Returns:
        Extended Promela specification string.
    """
    quorum = max(2 * max_byzantine + 1, (n_agents * 2) // 3 + 1)
    return f'''/* CIF Promela v2.0 - {n_agents} agents, max {max_byzantine} Byzantine */
/* Extended: drift detection, sandbox, composition algebra, omega taxonomy */
/* Part 2 DOI: 10.5281/zenodo.22134546 */

#define N_AGENTS    {n_agents}
#define MAX_BYZ     {max_byzantine}
#define QUORUM      {quorum}
#define DRIFT_THRESH {drift_threshold}
#define KAPPA_CORR  {kappa}

mtype = {{ honest, byzantine, suspicious, flagged }}
mtype = {{ sequential, parallel, hybrid }}

byte trust[N_AGENTS];
bool votes[N_AGENTS];
bool consensus;
bool firewall_active;
byte beliefs[N_AGENTS];
byte drift_scores[N_AGENTS];
byte sandbox_counts[N_AGENTS];
mtype agent_status[N_AGENTS];
byte omega_level;
mtype composition_mode;

chan vote_chan  = [N_AGENTS] of {{ byte, bool }};
chan alert_chan = [N_AGENTS] of {{ byte, byte }};

init {{
    byte i;
    atomic {{
        i = 0;
        do
        :: i < N_AGENTS ->
            trust[i] = 50;
            votes[i] = false;
            beliefs[i] = 100;
            drift_scores[i] = 0;
            sandbox_counts[i] = 0;
            agent_status[i] = honest;
            i = i + 1
        :: else -> break
        od;
        consensus = false;
        firewall_active = true;
        omega_level = 1;
        composition_mode = sequential
    }};
    agent_status[0] = byzantine;
    i = 0;
    do
    :: i < N_AGENTS -> run agent(i); i = i + 1
    :: else -> break
    od;
    run consensus_checker();
    run drift_detector();
    run sandbox_monitor()
}}

proctype agent(byte id) {{
    bool is_byz;
    is_byz = (agent_status[id] == byzantine);
    do
    :: !is_byz && firewall_active && agent_status[id] != flagged ->
           votes[id] = true;
           vote_chan ! id, true
    :: is_byz ->
           votes[id] = false;
           vote_chan ! id, false
    :: !is_byz && beliefs[id] < DRIFT_THRESH ->
           alert_chan ! id, 1
    od
}}

proctype consensus_checker() {{
    byte aid; bool v; byte cnt;
    cnt = 0;
    do
    :: vote_chan ? aid, v ->
        if :: v && agent_status[aid] != flagged -> cnt = cnt + 1
           :: else -> skip
        fi;
        if :: cnt >= QUORUM -> consensus = true; break
           :: else -> skip
        fi
    od
}}

proctype drift_detector() {{
    byte aid; byte atype;
    do
    :: alert_chan ? aid, atype ->
        if
        :: atype == 1 ->
            drift_scores[aid] = 100 - beliefs[aid];
            agent_status[aid] = suspicious;
            if :: drift_scores[aid] > 50 ->
                    agent_status[aid] = flagged;
                    votes[aid] = false
               :: else -> skip
            fi
        :: else -> skip
        fi
    od
}}

proctype sandbox_monitor() {{
    byte i;
    do
    :: i < N_AGENTS ->
        if :: sandbox_counts[i] >= KAPPA_CORR ->
                beliefs[i] = 100;
                sandbox_counts[i] = 0;
                agent_status[i] = honest
           :: agent_status[i] == suspicious && sandbox_counts[i] < KAPPA_CORR ->
                sandbox_counts[i] = sandbox_counts[i] + 1
           :: else -> skip
        fi;
        i = (i + 1) % N_AGENTS
    od
}}

ltl p1_firewall_safety {{
    [] (firewall_active -> (agent_status[0] == flagged -> votes[0] == false))
}}

ltl p2_eventual_consensus {{ <> consensus }}

ltl p3_omega_bounded {{ [] (omega_level >= 1 && omega_level <= 5) }}

ltl p4_drift_detection {{
    [] ((beliefs[1] < DRIFT_THRESH) ->
        <> (agent_status[1] == flagged || agent_status[1] == suspicious))
}}
'''


def generate_nusmv_spec_v2(
    n_agents: int = 5,
    max_byzantine: int = 1,
    drift_threshold: int = 30,
    kappa: int = 3,
) -> str:
    """Generate extended NuSMV specification v2.0.

    Args:
        n_agents: Number of agents (simplified to 5 for NuSMV tractability).
        max_byzantine: Maximum Byzantine agents.
        drift_threshold: Belief drift threshold.
        kappa: Sandbox corroboration threshold.

    Returns:
        Extended NuSMV specification string.
    """
    quorum = max(2 * max_byzantine + 1, (n_agents * 2) // 3 + 1)
    return f'''-- CIF NuSMV v2.0 - {n_agents} agents, max {max_byzantine} Byzantine
-- Extended: composition algebra, Omega taxonomy, drift, sandbox
-- Part 2 DOI: 10.5281/zenodo.22134546

MODULE main

VAR
  trust_0 : 0..100; trust_1 : 0..100; trust_2 : 0..100;
  trust_3 : 0..100; trust_4 : 0..100;

  status_0 : {{trusted, suspicious, flagged}};
  status_1 : {{trusted, suspicious, flagged}};
  status_2 : {{trusted, suspicious, flagged}};
  status_3 : {{trusted, suspicious, flagged}};
  status_4 : {{trusted, suspicious, flagged}};

  vote_0 : boolean; vote_1 : boolean; vote_2 : boolean;
  vote_3 : boolean; vote_4 : boolean;

  belief_0 : 0..100; belief_1 : 0..100; belief_2 : 0..100;
  belief_3 : 0..100; belief_4 : 0..100;

  drift_0 : 0..100; drift_1 : 0..100;
  corr_1 : 0..10;

  consensus       : boolean;
  firewall_active : boolean;
  byzantine_set   : {{none, agent0, agent1, both_01}};
  omega_level     : 1..5;
  composition_mode : {{sequential, parallel, hybrid}};

DEFINE
  DRIFT_THRESH := {drift_threshold};
  QUORUM       := {quorum};
  KAPPA        := {kappa};

  is_byzantine_0 := (byzantine_set = agent0 | byzantine_set = both_01);
  is_byzantine_1 := (byzantine_set = agent1 | byzantine_set = both_01);

  honest_votes :=
    (vote_0 & status_0 != flagged ? 1 : 0) +
    (vote_1 & status_1 != flagged ? 1 : 0) +
    (vote_2 & status_2 != flagged ? 1 : 0) +
    (vote_3 & status_3 != flagged ? 1 : 0) +
    (vote_4 & status_4 != flagged ? 1 : 0);

  quorum_reached   := honest_votes >= QUORUM;
  drift_detected_1 := belief_1 < DRIFT_THRESH;
  sandbox_promote_1 := corr_1 >= KAPPA;

ASSIGN
  init(trust_0) := 50; init(trust_1) := 50; init(trust_2) := 50;
  init(trust_3) := 50; init(trust_4) := 50;
  init(status_0) := trusted; init(status_1) := trusted;
  init(status_2) := trusted; init(status_3) := trusted; init(status_4) := trusted;
  init(vote_0) := FALSE; init(vote_1) := FALSE; init(vote_2) := FALSE;
  init(vote_3) := FALSE; init(vote_4) := FALSE;
  init(belief_0) := 100; init(belief_1) := 100; init(belief_2) := 100;
  init(belief_3) := 100; init(belief_4) := 100;
  init(drift_0) := 0; init(drift_1) := 0;
  init(corr_1) := 0;
  init(consensus) := FALSE;
  init(firewall_active) := TRUE;
  init(byzantine_set) := agent0;
  init(omega_level) := 1;
  init(composition_mode) := sequential;

  next(vote_0) :=
    case
      is_byzantine_0     : FALSE;
      status_0 = flagged : FALSE;
      firewall_active    : TRUE;
      TRUE               : vote_0;
    esac;

  next(vote_1) :=
    case
      is_byzantine_1     : {{FALSE, vote_1}};
      status_1 = flagged : FALSE;
      firewall_active    : TRUE;
      TRUE               : vote_1;
    esac;

  next(consensus) := consensus | quorum_reached;

  next(belief_1) :=
    case
      is_byzantine_0 & omega_level >= 4 & belief_1 > 20 : belief_1 - 20;
      sandbox_promote_1 : 100;
      TRUE : belief_1;
    esac;

  next(drift_1) :=
    case
      belief_1 < DRIFT_THRESH : 100 - belief_1;
      TRUE : 0;
    esac;

  next(status_1) :=
    case
      drift_1 > 50      : flagged;
      drift_1 > 0       : suspicious;
      sandbox_promote_1 : trusted;
      TRUE              : status_1;
    esac;

  next(corr_1) :=
    case
      status_1 = suspicious & corr_1 < KAPPA : corr_1 + 1;
      sandbox_promote_1 : 0;
      TRUE : corr_1;
    esac;

  next(omega_level) :=
    case
      omega_level < 5 : {{omega_level, omega_level + 1}};
      TRUE : 5;
    esac;

  next(composition_mode) :=
    case
      composition_mode = sequential : {{sequential, parallel}};
      composition_mode = parallel   : {{parallel, hybrid}};
      TRUE : composition_mode;
    esac;

-- Safety
SPEC AG (consensus -> honest_votes >= QUORUM)
SPEC AG (firewall_active -> (status_0 = flagged -> !vote_0))
SPEC AG (firewall_active -> (status_1 = flagged -> !vote_1))
SPEC AG (omega_level >= 1 & omega_level <= 5)
SPEC AG (status_1 = flagged -> AX (status_1 = flagged | status_1 = trusted))

-- Liveness
SPEC AF consensus
SPEC AG (drift_detected_1 -> AF (status_1 = suspicious | status_1 = flagged))
SPEC AG (corr_1 >= KAPPA -> AF (belief_1 = 100))

-- Composition algebra
SPEC AG (composition_mode = sequential | composition_mode = parallel | composition_mode = hybrid)
SPEC AG (composition_mode = sequential & firewall_active & status_1 = flagged -> !vote_1)
'''


def write_extended_specs(
    output_dir: str | pathlib.Path,
    n_agents: int = 5,
    max_byzantine: int = 1,
) -> dict[str, pathlib.Path]:
    """Generate and write all v2 formal specification files.

    Args:
        output_dir: Directory to write formal specs into.
        n_agents: Number of agents.
        max_byzantine: Maximum Byzantine agents.

    Returns:
        Dict mapping spec name to output path.
    """
    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, pathlib.Path] = {}

    tla_path = out / "CognitiveIntegrityFramework_v2.tla"
    tla_path.write_text(generate_tla_spec_v2(n_agents, max_byzantine))
    paths["tla"] = tla_path

    pml_path = out / "cif_model_v2.pml"
    pml_path.write_text(generate_promela_spec_v2(n_agents, max_byzantine))
    paths["promela"] = pml_path

    smv_path = out / "cif_model_v2.smv"
    smv_path.write_text(generate_nusmv_spec_v2(n_agents, max_byzantine))
    paths["nusmv"] = smv_path

    return paths
