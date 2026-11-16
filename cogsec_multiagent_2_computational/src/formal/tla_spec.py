"""TLA+ specification generation for formal verification.

Generates TLA+ specifications for the Cognitive Integrity Framework
properties.
"""

from __future__ import annotations

from typing import Dict


def generate_categorical_tla_spec() -> str:
    """Generate TLA+ spec expressing category-theoretic composition properties.

    Encodes:
    - Categorical composition associativity as a temporal invariant
    - Monoidal coherence (associator, left/right unitor) as safety props
    - Lattice meet/join closure as type invariants

    Returns:
        TLA+ specification string.
    """
    lines = [
        "---- MODULE DefenseCategoryTheory ----",
        "\\* TLA+ encoding of categorical composition laws for DefenseCategory",
        "",
        "EXTENDS Integers, Sequences, Reals",
        "",
        "CONSTANTS",
        "  Morphisms,        \\* Set of morphism identifiers",
        "  DetectionRate,    \\* Function: Morphisms -> [0,1] (rational approx)",
        "  Identity          \\* The identity morphism",
        "",
        "VARIABLES",
        "  composition_stack,  \\* Current composition chain (sequence of morphism IDs)",
        "  current_result,     \\* Current evaluation result [0..100]",
        "  law_violations      \\* Set of detected law violations",
        "",
        "vars == <<composition_stack, current_result, law_violations>>",
        "",
        "SeriesValues(a, b) == 1 - (1 - a) * (1 - b)",
        "TensorValues(a, b) == IF a >= b THEN a ELSE b",
        "",
        "\\* ---- Type Invariant ----",
        "TypeInvariant ==",
        "  /\\ composition_stack \\in Seq(Morphisms)",
        "  /\\ current_result \\in 0..100",
        "  /\\ law_violations \\subseteq {\"left_identity\", \"right_identity\", \"associativity\",",  # noqa: E501
        "                               \"left_unitor\", \"right_unitor\", \"hexagon\"}",
        "",
        "\\* ---- Category Law Invariants ----",
        "",
        "\\* Left identity: id ∘ f = f (score unchanged after composing with identity)",
        "LeftIdentityInvariant ==",
        "  \\A f \\in Morphisms :",
        "    TensorValues(0, DetectionRate[f]) = DetectionRate[f]",
        "",
        "\\* Right identity: f ∘ id = f",
        "RightIdentityInvariant ==",
        "  \\A f \\in Morphisms :",
        "    TensorValues(DetectionRate[f], 0) = DetectionRate[f]",
        "",
        "\\* Categorical composition associativity as temporal invariant",
        "\\* (f ; g) ; h  behaves identically to  f ; (g ; h)",
        "AssociativityInvariant ==",
        "  \\A f, g, h \\in Morphisms :",
        "    SeriesValues(SeriesValues(DetectionRate[f], DetectionRate[g]), DetectionRate[h])",
        "      = SeriesValues(DetectionRate[f], SeriesValues(DetectionRate[g], DetectionRate[h]))",
        "",
        "\\* Monoidal left unitor: I ⊗ f ≅ f",
        "LeftUnitorInvariant ==",
        "  \\A f \\in Morphisms :",
        "    TensorValues(0, DetectionRate[f]) = DetectionRate[f]",
        "",
        "\\* Monoidal right unitor: f ⊗ I ≅ f",
        "RightUnitorInvariant ==",
        "  \\A f \\in Morphisms :",
        "    TensorValues(DetectionRate[f], 0) = DetectionRate[f]",
        "",
        "\\* Hexagon identity: (f ⊗ g) ⊗ h ≅ f ⊗ (g ⊗ h)",
        "HexagonIdentity ==",
        "  \\A f, g, h \\in Morphisms :",
        "    TensorValues(TensorValues(DetectionRate[f], DetectionRate[g]), DetectionRate[h])",
        "      = TensorValues(DetectionRate[f], TensorValues(DetectionRate[g], DetectionRate[h]))",
        "",
        "\\* Symmetry (braiding): f ⊗ g ≅ g ⊗ f",
        "SymmetryInvariant ==",
        "  \\A f, g \\in Morphisms :",
        "    TensorValues(DetectionRate[f], DetectionRate[g])",
        "      = TensorValues(DetectionRate[g], DetectionRate[f])",
        "",
        "\\* Lattice: meet is ≤ both operands",
        "LatticesMeetInvariant ==",
        "  \\A f, g \\in Morphisms :",
        "    LET meet_rate == IF DetectionRate[f] <= DetectionRate[g]",
        "                     THEN DetectionRate[f] ELSE DetectionRate[g]",
        "    IN meet_rate <= DetectionRate[f] /\\ meet_rate <= DetectionRate[g]",
        "",
        "\\* Lattice: join is the least upper bound (max under rate order)",
        "LatticeJoinInvariant ==",
        "  \\A f, g \\in Morphisms :",
        "    LET join_rate == TensorValues(DetectionRate[f], DetectionRate[g])",
        "    IN /\\ join_rate >= DetectionRate[f] /\\ join_rate >= DetectionRate[g]",
        "       /\\ \\A h \\in Morphisms :",
        "            (DetectionRate[f] <= DetectionRate[h] "
        "/\\ DetectionRate[g] <= DetectionRate[h])",
        "              => join_rate <= DetectionRate[h]",
        "",
        "\\* ---- Init / Next ----",
        "Init ==",
        "  /\\ composition_stack = <<>>",
        "  /\\ current_result = 0",
        "  /\\ law_violations = {}",
        "",
        "Next ==",
        "  \\/ \\E f \\in Morphisms :",
        "       /\\ composition_stack' = Append(composition_stack, f)",
        "       /\\ current_result' = (current_result + 1) % 101",
        "       /\\ UNCHANGED law_violations",
        "  \\/ /\\ composition_stack' = <<>>",
        "     /\\ current_result' = 0",
        "     /\\ UNCHANGED law_violations",
        "",
        "Spec == Init /\\ [][Next]_vars",
        "",
        "\\* ---- Theorems ----",
        "THEOREM Spec => []TypeInvariant",
        "THEOREM Spec => []AssociativityInvariant",
        "THEOREM Spec => []LeftIdentityInvariant",
        "THEOREM Spec => []RightIdentityInvariant",
        "THEOREM Spec => []LeftUnitorInvariant",
        "THEOREM Spec => []RightUnitorInvariant",
        "THEOREM Spec => []HexagonIdentity",
        "THEOREM Spec => []LatticesMeetInvariant",
        "THEOREM Spec => []LatticeJoinInvariant",
        "",
        "====",
    ]
    return "\n".join(lines) + "\n"


def generate_tla_spec(n_agents: int = 5, max_byzantine: int = 1) -> str:
    """Generate a TLA+ specification for CIF formal verification.

    Args:
        n_agents: Number of agents in the model.
        max_byzantine: Maximum number of Byzantine agents.

    Returns:
        A TLA+ specification as a string.
    """
    lines = [
        "---- MODULE CognitiveIntegrityFramework ----",
        f"\\* CIF TLA+ Model: {n_agents} agents, max {max_byzantine} Byzantine",
        "",
        "EXTENDS Integers, Sequences, FiniteSets",
        "",
        "CONSTANTS",
        f"  Agents,           \\* Set of agent IDs (1..{n_agents})",
        f"  MaxByzantine,     \\* Maximum Byzantine agents ({max_byzantine})",
        "  Quorum            \\* Required quorum size",
        "",
        "VARIABLES",
        "  trust,            \\* Function: Agents -> [0..100]",
        "  votes,            \\* Function: Agents -> {0, 1}",
        "  consensus,        \\* Boolean: consensus reached",
        "  byzantine,        \\* Set of Byzantine agents",
        "  firewall_active,  \\* Boolean: firewall is on",
        "  beliefs           \\* Function: Agents -> [0..100]",
        "",
        "vars == <<trust, votes, consensus, byzantine, firewall_active, beliefs>>",
        "",
        "\\* ---- Type Invariant ----",
        "TypeInvariant ==",
        "  /\\ trust \\in [Agents -> 0..100]",
        "  /\\ votes \\in [Agents -> {0, 1}]",
        "  /\\ consensus \\in BOOLEAN",
        "  /\\ byzantine \\subseteq Agents",
        "  /\\ Cardinality(byzantine) <= MaxByzantine",
        "  /\\ firewall_active \\in BOOLEAN",
        "  /\\ beliefs \\in [Agents -> 0..100]",
        "",
        "\\* ---- Initial State ----",
        "Init ==",
        "  /\\ trust = [a \\in Agents |-> 50]",
        "  /\\ votes = [a \\in Agents |-> 0]",
        "  /\\ consensus = FALSE",
        "  /\\ byzantine \\in SUBSET Agents",
        "  /\\ Cardinality(byzantine) <= MaxByzantine",
        "  /\\ firewall_active = TRUE",
        "  /\\ beliefs = [a \\in Agents |-> 100]",
        "",
        "\\* ---- Actions ----",
        "",
        "\\* Honest agent votes truthfully",
        "HonestVote(a) ==",
        "  /\\ a \\notin byzantine",
        "  /\\ votes' = [votes EXCEPT ![a] = 1]",
        "  /\\ UNCHANGED <<trust, consensus, byzantine, firewall_active, beliefs>>",
        "",
        "\\* Byzantine agent votes adversarially",
        "ByzantineVote(a) ==",
        "  /\\ a \\in byzantine",
        "  /\\ votes' = [votes EXCEPT ![a] = 0]",
        "  /\\ UNCHANGED <<trust, consensus, byzantine, firewall_active, beliefs>>",
        "",
        "\\* Check for consensus",
        "CheckConsensus ==",
        "  LET vote_sum == Cardinality({a \\in Agents : votes[a] = 1})",
        "  IN /\\ vote_sum >= Quorum",
        "     /\\ consensus' = TRUE",
        "     /\\ UNCHANGED <<trust, votes, byzantine, firewall_active, beliefs>>",
        "",
        "\\* Trust delegation (decay)",
        "DelegateTrust(source, target) ==",
        "  LET weakest == IF trust[source] <= trust[target] THEN trust[source] ELSE trust[target]",
        "  IN /\\ trust' = [trust EXCEPT ![target] = (weakest * 85) \\div 100]",
        "  /\\ UNCHANGED <<votes, consensus, byzantine, firewall_active, beliefs>>",
        "",
        "\\* ---- Next State ----",
        "Next ==",
        "  \\/ \\E a \\in Agents : HonestVote(a)",
        "  \\/ \\E a \\in Agents : ByzantineVote(a)",
        "  \\/ CheckConsensus",
        "  \\/ \\E s, t \\in Agents : DelegateTrust(s, t)",
        "",
        "\\* ---- Specification ----",
        "\\* No liveness assumption: WF_vars(Next) would not force any vote action.",
        "Spec == Init /\\ [][Next]_vars",
        "",
        "\\* ---- Safety Properties ----",
        "",
        "\\* Trust scores are always bounded",
        "TrustBounded == \\A a \\in Agents : trust[a] >= 0 /\\ trust[a] <= 100",
        "",
        "\\* Byzantine tolerance: correct consensus when n >= 3f+1",
        "SafetyProperty ==",
        "  Cardinality(byzantine) <= MaxByzantine =>",
        "    (consensus => Cardinality({a \\in Agents : votes[a] = 1}) >= Quorum)",
        "",
        "\\* Only safety is asserted.  Agents may stutter forever, so eventual",
        "\\* consensus is not a theorem without an explicit scheduler assumption.",
        "",
        "\\* ---- Theorems ----",
        "THEOREM Spec => []TypeInvariant",
        "THEOREM Spec => []TrustBounded",
        "THEOREM Spec => []SafetyProperty",
        "",
        "====",
    ]

    return "\n".join(lines) + "\n"


def generate_tla_config(n_agents: int = 5, max_byzantine: int = 1) -> str:
    """Generate the TLC configuration required by :func:`generate_tla_spec`."""
    agents = ", ".join(str(agent) for agent in range(1, n_agents + 1))
    quorum = (2 * n_agents) // 3 + 1
    return (
        f"CONSTANTS\n  Agents = {{{agents}}}\n"
        f"  MaxByzantine = {max_byzantine}\n  Quorum = {quorum}\n"
        "SPECIFICATION Spec\n"
        "INVARIANTS\n  TypeInvariant\n  TrustBounded\n  SafetyProperty\n"
    )


def parse_tla_result(output: str) -> Dict[str, bool]:
    """Parse TLC model checker output.

    Args:
        output: Raw TLC stdout output.

    Returns:
        Mapping from property name to pass/fail status.
    """
    results: Dict[str, bool] = {}
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        # TLC reports "Invariant X is violated" or "Model checking completed. No error"
        if "is violated" in line.lower():
            prop = line.split("is violated")[0].strip()
            results[prop] = False
        elif "no error" in line.lower() and "model checking completed" in line.lower():
            results["overall"] = True
        elif "error" in line.lower() and "found" in line.lower():
            results["overall"] = False

    return results
