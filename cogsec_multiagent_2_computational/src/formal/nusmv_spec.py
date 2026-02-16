"""NuSMV CTL specification generation for model checking.

Generates NuSMV models with CTL properties for the Cognitive Integrity
Framework components.
"""

from __future__ import annotations

from typing import Dict


def generate_nusmv_spec(n_agents: int = 5, max_byzantine: int = 1) -> str:
    """Generate a NuSMV model with CTL properties for CIF verification.

    Args:
        n_agents: Number of agents in the model.
        max_byzantine: Maximum number of Byzantine agents.

    Returns:
        A NuSMV specification as a string.
    """
    lines = [
        f"-- CIF NuSMV Model: {n_agents} agents, max {max_byzantine} Byzantine",
        "MODULE main",
        "",
        "VAR",
        f"  n_agents : 1..{n_agents};",
        f"  byzantine_count : 0..{max_byzantine};",
        "  consensus_reached : boolean;",
        "  trust_score : 0..100;  -- scaled [0, 1] as integer",
        "  firewall_active : boolean;",
        "  injection_attempt : boolean;",
        "  injection_succeeds : boolean;",
        "  belief_integrity : 0..100;",
        "",
        "ASSIGN",
        "  init(consensus_reached) := FALSE;",
        "  init(trust_score) := 50;",
        "  init(firewall_active) := TRUE;",
        "  init(injection_succeeds) := FALSE;",
        "  init(belief_integrity) := 100;",
        "",
        "  next(consensus_reached) := case",
        f"    byzantine_count <= {max_byzantine} & n_agents >= 3 * byzantine_count + 1 : TRUE;",
        "    TRUE : {TRUE, FALSE};",
        "  esac;",
        "",
        "  next(injection_succeeds) := case",
        "    firewall_active & injection_attempt : FALSE;",
        "    !firewall_active & injection_attempt : {TRUE, FALSE};",
        "    TRUE : FALSE;",
        "  esac;",
        "",
        "  next(trust_score) := case",
        "    trust_score > 0 : trust_score;  -- bounded",
        "    TRUE : 0;",
        "  esac;",
        "",
        "-- CTL Properties",
        "",
        "-- P1: Byzantine tolerance ensures eventual consensus",
        f"CTLSPEC AG (byzantine_count <= {max_byzantine} -> AF consensus_reached)",
        "",
        "-- P2: Trust scores are always bounded [0, 1]",
        "CTLSPEC AG (trust_score >= 0 & trust_score <= 100)",
        "",
        "-- P3: Active firewall prevents injection success",
        "CTLSPEC AG (firewall_active -> !injection_succeeds)",
        "",
        "-- P4: Belief integrity never negative",
        "CTLSPEC AG (belief_integrity >= 0)",
    ]

    return "\n".join(lines) + "\n"


def parse_nusmv_result(output: str) -> Dict[str, bool]:
    """Parse NuSMV output to extract property verification results.

    Args:
        output: Raw NuSMV stdout output.

    Returns:
        Mapping from property description to pass/fail status.
    """
    results: Dict[str, bool] = {}
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        if "-- specification" in line.lower() or "-- CTLSPEC" in line.lower():
            prop_name = line
            # NuSMV prints "is true" or "is false" after the property
            is_true = "is true" in line.lower()
            is_false = "is false" in line.lower()
            if is_true:
                results[prop_name] = True
            elif is_false:
                results[prop_name] = False
        elif line.startswith("-- specification") and "is true" in line:
            results[line] = True
        elif line.startswith("-- specification") and "is false" in line:
            results[line] = False

    return results
