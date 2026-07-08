"""Package identity markers for the merged CIF Practical & Applications paper.

This module provides identity and provenance metadata for the unified
Part 3+4 paper, integrating practitioner guidance with cross-domain
CIF-AD-OODA analysis originally developed in Part 4.
"""

from __future__ import annotations


def package_id() -> str:
    """Return the canonical package identifier for this merged paper."""
    return "cogsec_multiagent_3_practical"


def merged_from() -> list[str]:
    """Return the list of original part identifiers that were merged into this package."""
    return ["cogsec_multiagent_3_practical", "cogsec_multiagent_4_applications"]


def paper_parts() -> dict[str, str]:
    """Return metadata about the covered paper parts."""
    return {
        "part_3": "Practitioner guidance, deployment, risk assessment, pitfalls, case studies",
        "part_4": "CIF-AD-OODA cross-domain applications (10 domains), attack pattern taxonomy, novel defense extensions",
    }
