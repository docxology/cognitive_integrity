def test_package_identity():
    """Exercises ``src/identity.py`` (manuscript is the primary Part 4 artifact)."""
    from identity import package_id

    assert package_id() == "cogsec_multiagent_4_applications"
