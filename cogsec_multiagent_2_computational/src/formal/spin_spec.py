"""SPIN/Promela LTL specification generation for model checking.

Generates Promela models with LTL properties for the Cognitive Integrity
Framework.
"""

from __future__ import annotations

from typing import Dict


def generate_promela_spec(n_agents: int = 5, max_byzantine: int = 1) -> str:
    """Generate a Promela model with LTL properties for SPIN verification.

    Args:
        n_agents: Number of agents in the model.
        max_byzantine: Maximum number of Byzantine agents.

    Returns:
        A Promela specification as a string.
    """
    lines = [
        f"/* CIF Promela Model: {n_agents} agents, max {max_byzantine} Byzantine */",
        "",
        f"#define N_AGENTS {n_agents}",
        f"#define MAX_BYZANTINE {max_byzantine}",
        "#define QUORUM ((2 * N_AGENTS) / 3 + 1)",
        "",
        "/* State variables */",
        "int vote_count = 0;",
        "bool decided = false;",
        "int trust[N_AGENTS];",
        "int delegated_trust[N_AGENTS];",
        "int direct_trust[N_AGENTS];",
        "bool firewall_active = true;",
        "bool injection = false;",
        "",
        "/* Agent process */",
        "proctype Agent(int id; bool is_byzantine) {",
        "  int my_trust;",
        "",
        "  if",
        "  :: is_byzantine ->",
        "    /* Byzantine agent: adversarial voting */",
        "    trust[id] = 0;",
        "    my_trust = 0;",
        "  :: !is_byzantine ->",
        "    /* Honest agent: truthful voting */",
        "    trust[id] = 100;",
        "    my_trust = 100;",
        "  fi;",
        "",
        "  /* Vote phase */",
        "  atomic {",
        "    if",
        "    :: my_trust > 50 -> vote_count++;",
        "    :: else -> skip;",
        "    fi;",
        "  };",
        "",
        "  /* Check quorum */",
        "  if",
        "  :: vote_count >= QUORUM -> decided = true;",
        "  :: else -> skip;",
        "  fi;",
        "",
        "  /* Delegation: delegated <= direct */",
        "  direct_trust[id] = my_trust;",
        "  delegated_trust[id] = my_trust * 85 / 100;  /* decay = 0.85 */",
        "}",
        "",
        "/* Firewall process */",
        "proctype Firewall() {",
        "  do",
        "  :: injection && firewall_active ->",
        "    injection = false;  /* blocked */",
        "  :: !firewall_active && injection ->",
        "    skip;  /* not blocked */",
        "  :: !injection ->",
        "    skip;",
        "  od;",
        "}",
        "",
        "/* Init */",
        "init {",
        "  int i;",
        f"  for (i : 0 .. {n_agents - 1}) {{",
        "    if",
        f"    :: i < {max_byzantine} ->",
        "      run Agent(i, true);",
        "    :: else ->",
        "      run Agent(i, false);",
        "    fi;",
        "  };",
        "  run Firewall();",
        "}",
        "",
        "/* LTL Properties */",
        "",
        "/* P1: Consensus eventually reached when quorum available */",
        "ltl consensus { [] (vote_count >= QUORUM -> <> decided) }",
        "",
        "/* P2: Delegated trust never exceeds direct trust */",
        "ltl trust_bound { [] (delegated_trust[0] <= direct_trust[0]) }",
        "",
        "/* P3: Active firewall prevents injection */",
        "ltl no_injection { [] (firewall_active -> !injection) }",
    ]

    return "\n".join(lines) + "\n"


def parse_spin_result(output: str) -> Dict[str, bool]:
    """Parse SPIN verification output.

    Args:
        output: Raw SPIN stdout output.

    Returns:
        Mapping from property name to pass/fail status.
    """
    results: Dict[str, bool] = {}
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        # SPIN reports "errors: 0" for passing properties
        if "errors:" in line.lower():
            errors = 0
            parts = line.split(":")
            if len(parts) >= 2:
                try:
                    errors = int(parts[-1].strip())
                except ValueError:
                    pass
            results[f"property_{len(results)}"] = errors == 0

        # Look for acceptance/rejection
        if "acceptance cycle" in line.lower():
            results[f"ltl_{len(results)}"] = False
        elif "no acceptance cycle" in line.lower():
            results[f"ltl_{len(results)}"] = True

    return results
