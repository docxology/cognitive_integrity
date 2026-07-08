"""Integration tests verifying the merged Part 3+4 paper structure.

These tests confirm that the merge of Part 4 (CIF-AD-OODA applications) into
Part 3 is structurally complete: all required manuscript sections are present,
source modules import correctly, and the identity metadata is coherent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Root of this project
PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Manuscript structure
# ---------------------------------------------------------------------------

EXPECTED_MANUSCRIPT_SECTIONS = [
    # Original Part 3 sections
    "00_abstract.md",
    "01_introduction.md",
    "02_theory_review.md",
    "03_simulation_review.md",
    "04_attack_scenarios.md",
    "04b_subagent_hardening.md",
    "05_deployment_guide.md",
    "05b_incident_response.md",
    "05c_cost_benefit.md",
    "05d_monitoring_guide.md",
    "06_common_pitfalls.md",
    "06b_case_studies.md",
    "07_future_directions.md",
    "08_conclusion.md",
    # Part 4 applications sections (renumbered)
    "09_applications_intro.md",
    "09b_cif_ad_ooda_methodology.md",
    "09c_rare_earth_mining.md",
    "09d_nation_state_alliances.md",
    "09e_cyber_security.md",
    "09f_drone_wars.md",
    "09g_supply_chain.md",
    "09h_biowarfare.md",
    "09i_food_security.md",
    "09j_trade_wars.md",
    "09k_infrastructure.md",
    "09l_fake_news.md",
    "10_cross_domain_discussion.md",
    "10b_applications_conclusion.md",
    # References and supplementaries
    "99_references.md",
    "S01_notation_reference.md",
    "S03_real_world_incidents.md",
    # Config
    "config.yaml",
    "references.bib",
]


@pytest.mark.parametrize("section", EXPECTED_MANUSCRIPT_SECTIONS)
def test_manuscript_section_exists(section):
    """Every expected manuscript section must be present after merge."""
    path = PROJECT_ROOT / "manuscript" / section
    assert path.exists(), f"Missing manuscript section: {section}"
    assert path.stat().st_size > 0, f"Empty manuscript section: {section}"


def test_ten_domain_sections_present():
    """All 10 CIF-AD-OODA domain case-study files must be present."""
    domains = [
        "09c_rare_earth_mining.md",
        "09d_nation_state_alliances.md",
        "09e_cyber_security.md",
        "09f_drone_wars.md",
        "09g_supply_chain.md",
        "09h_biowarfare.md",
        "09i_food_security.md",
        "09j_trade_wars.md",
        "09k_infrastructure.md",
        "09l_fake_news.md",
    ]
    manuscript_dir = PROJECT_ROOT / "manuscript"
    for d in domains:
        assert (manuscript_dir / d).exists(), f"Domain section missing: {d}"


def test_s03_supplement_exists():
    """S03 (real-world incidents, formerly Part 4's S02) must be present."""
    path = PROJECT_ROOT / "manuscript" / "S03_real_world_incidents.md"
    assert path.exists()
    content = path.read_text()
    # Should reference updated S3 numbering
    assert "S3." in content, "S03 should use S3.x incident numbering"


def test_part4_directory_deleted():
    """The Part 4 source directory must no longer exist after merge."""
    part4_dir = PROJECT_ROOT.parent / "cogsec_multiagent_4_applications"
    assert not part4_dir.exists(), (
        "cogsec_multiagent_4_applications directory still exists — it should have been deleted"
    )


# ---------------------------------------------------------------------------
# Source module integrity
# ---------------------------------------------------------------------------

EXPECTED_SRC_MODULES = [
    "posture",
    "checklists",
    "agent_guidelines",
    "deployment",
    "risk_assessment",
    "pitfalls",
    "visualization",
    "identity",
]


@pytest.mark.parametrize("module", EXPECTED_SRC_MODULES)
def test_src_module_exists(module):
    """Every expected src module file must be present."""
    path = PROJECT_ROOT / "src" / f"{module}.py"
    assert path.exists(), f"Missing src module: {module}.py"


def test_identity_module_imports():
    """identity module must import cleanly and expose expected functions."""
    from identity import merged_from, package_id, paper_parts

    assert callable(package_id)
    assert callable(merged_from)
    assert callable(paper_parts)


def test_identity_coherence():
    """Identity metadata must be internally coherent."""
    from identity import merged_from, package_id, paper_parts

    pid = package_id()
    merged = merged_from()
    parts = paper_parts()

    assert pid in merged, "package_id() must be in merged_from() list"
    assert len(parts) == 2, "paper_parts() must describe exactly 2 parts"


# ---------------------------------------------------------------------------
# Config integrity
# ---------------------------------------------------------------------------


def test_config_yaml_version():
    """config.yaml must be at version 2.0 after merge."""
    config_path = PROJECT_ROOT / "manuscript" / "config.yaml"
    content = config_path.read_text()
    assert 'version: "2.0"' in content, "config.yaml must be at version 2.0"


def test_config_yaml_merged_title():
    """config.yaml must have the merged title."""
    config_path = PROJECT_ROOT / "manuscript" / "config.yaml"
    content = config_path.read_text()
    assert "Practical Applications and Deployment Guide" in content, (
        "config.yaml title must reflect the merged scope"
    )


def test_references_bib_contains_part4_entries():
    """references.bib must contain key Part 4 domain-specific references."""
    bib_path = PROJECT_ROOT / "manuscript" / "references.bib"
    content = bib_path.read_text()
    part4_keys = [
        "suh2001axiomatic",  # Axiomatic Design — central to CIF-AD-OODA
        "boyd1987patterns",  # OODA Loop
        "zhang2025asb",  # Agent Security Bench benchmark
        "adversa2025incidents",  # Real-world incidents
        "owasp2025agentic",  # OWASP Top 10 for Agentic Applications
    ]
    for key in part4_keys:
        assert key in content, f"Missing Part 4 reference: {key}"
