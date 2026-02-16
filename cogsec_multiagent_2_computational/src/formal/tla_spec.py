"""TLA+ specification generation for formal verification.

Generates TLA+ specifications for the Cognitive Integrity Framework
properties.
"""

from __future__ import annotations

from typing import Dict


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
        "  /\\ trust' = [trust EXCEPT ![target] = (trust[source] * 85) \\div 100]",
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
        "Spec == Init /\\ [][Next]_vars /\\ WF_vars(Next)",
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
        "\\* ---- Liveness Properties ----",
        "",
        "\\* Consensus is eventually reached",
        "LivenessProperty == <>(consensus = TRUE)",
        "",
        "\\* ---- Theorems ----",
        "THEOREM Spec => []TypeInvariant",
        "THEOREM Spec => []TrustBounded",
        "THEOREM Spec => []SafetyProperty",
        "THEOREM Spec => LivenessProperty",
        "",
        "====",
    ]

    return "\n".join(lines) + "\n"


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
