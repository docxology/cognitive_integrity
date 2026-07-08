"""Tests for identity.py — package identity and merge provenance metadata."""

from __future__ import annotations


def test_package_id_is_part3():
    """The merged package keeps the Part 3 canonical identifier."""
    from identity import package_id

    assert package_id() == "cogsec_multiagent_3_practical"


def test_merged_from_contains_both_parts():
    """merged_from() must reference both original parts."""
    from identity import merged_from

    parts = merged_from()
    assert "cogsec_multiagent_3_practical" in parts
    assert "cogsec_multiagent_4_applications" in parts
    assert len(parts) == 2


def test_paper_parts_keys():
    """paper_parts() must enumerate both Part 3 and Part 4 descriptions."""
    from identity import paper_parts

    parts = paper_parts()
    assert "part_3" in parts
    assert "part_4" in parts
    assert "CIF-AD-OODA" in parts["part_4"]
    assert "10 domains" in parts["part_4"]


def test_package_id_returns_string():
    """package_id() must return a non-empty string."""
    from identity import package_id

    result = package_id()
    assert isinstance(result, str)
    assert len(result) > 0


def test_merged_from_returns_list():
    """merged_from() must return a list."""
    from identity import merged_from

    result = merged_from()
    assert isinstance(result, list)


def test_paper_parts_returns_dict():
    """paper_parts() must return a dict with string values."""
    from identity import paper_parts

    result = paper_parts()
    assert isinstance(result, dict)
    for key, value in result.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
        assert len(value) > 0
