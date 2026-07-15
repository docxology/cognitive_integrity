"""Dedicated tests for src/formal/category_theory_advanced.py.

This module backs the manuscript's "defense composition algebra" claims
(25 categorical verification checks across lattice, monoidal, operad,
enriched, Kan-extension, monad, and lens structures). Prior to this file,
its only exercise was indirectly through
src.visualization.composer_data.get_composer_data(), which wraps the whole
module in a broad ``except Exception`` and whose only test asserted
``isinstance(result, dict)`` -- passing whether the underlying math was
correct, broken, or non-functional. These tests call the verification
entry points directly and assert the checks actually report all-pass, plus
exercise the individual categorical laws in isolation.
"""

from __future__ import annotations

import math

from formal.category_theory_advanced import (
    BOTTOM,
    TOP,
    BeliefLens,
    DefenseLattice,
    DefenseMonad,
    DefenseOperad,
    DefenseProfunctor,
    DetectionBound,
    MonoidalDefenseCategory,
    cata,
    generate_test_states,
    get_lattice_data,
    get_monoidal_data,
    get_operad_data,
    lattice_join,
    lattice_meet,
    make_detection_algebra,
    make_test_morphism,
    run_all_verifications,
    serialize_verification_results,
)


class TestRunAllVerifications:
    """run_all_verifications() must report every categorical law as passing."""

    def test_all_structures_present(self):
        result = run_all_verifications(n_states=20, seed=42)
        assert set(result.keys()) == {
            "lattice", "monoidal", "operad", "enriched",
            "kan_extensions", "monad", "lenses",
        }

    def test_all_checks_pass(self):
        """Every individual boolean check across all 7 structures is True.

        This is the regression test the module was missing: a broken law
        (e.g. a sign error in lattice_meet, or a Kleisli-composition bug)
        would previously go undetected because nothing asserted on the
        actual verification outcomes.
        """
        result = run_all_verifications(n_states=20, seed=42)
        failures = []
        for structure, checks in result.items():
            if isinstance(checks, dict):
                for check_name, passed in checks.items():
                    if not passed:
                        failures.append(f"{structure}.{check_name}")
        assert failures == [], f"Failed categorical checks: {failures}"

    def test_deterministic_with_seed(self):
        r1 = run_all_verifications(n_states=15, seed=7)
        r2 = run_all_verifications(n_states=15, seed=7)
        assert r1 == r2


class TestSerializeVerificationResults:
    """serialize_verification_results() JSON summary must be internally consistent."""

    def test_summary_matches_flat_results(self):
        data = serialize_verification_results(n_states=20, seed=42)
        assert set(data.keys()) == {"summary", "results", "by_structure"}

        total = len(data["results"])
        passed = sum(1 for v in data["results"].values() if v)
        assert data["summary"]["total"] == total
        assert data["summary"]["passed"] == passed
        assert data["summary"]["failed"] == total - passed

    def test_all_checks_pass_via_serialized_summary(self):
        """The manuscript claims '25/25 checks' pass; verify none are failing."""
        data = serialize_verification_results(n_states=20, seed=42)
        assert data["summary"]["failed"] == 0
        assert data["summary"]["passed"] == data["summary"]["total"]
        assert data["summary"]["total"] > 0

    def test_by_structure_grouping_matches_flat_keys(self):
        data = serialize_verification_results(n_states=10, seed=1)
        for structure, checks in data["by_structure"].items():
            for check_name, value in checks.items():
                assert data["results"][f"{structure}.{check_name}"] == value


class TestGetLatticeData:
    def test_default_rates_structure(self):
        data = get_lattice_data()
        assert set(data.keys()) == {
            "elements", "bottom", "top", "meets", "joins", "hasse_edges",
        }
        assert data["bottom"]["rate"] == 0.0
        assert data["top"]["rate"] == 1.0
        assert len(data["elements"]) == 5  # canonical [0, 0.3, 0.5, 0.7, 1.0]

    def test_custom_rates_inserts_bottom_and_top(self):
        data = get_lattice_data(rates=[0.4, 0.6])
        rates = [e["rate"] for e in data["elements"]]
        assert 0.0 in rates
        assert 1.0 in rates
        assert 0.4 in rates
        assert 0.6 in rates

    def test_hasse_edges_are_covering_relations(self):
        data = get_lattice_data(rates=[0.0, 0.5, 1.0])
        # With 3 totally ordered elements, the Hasse diagram should have
        # exactly 2 covering edges (0->0.5, 0.5->1.0), not the transitive
        # 0->1.0 edge.
        edge_pairs = {(e["from"], e["to"]) for e in data["hasse_edges"]}
        assert len(edge_pairs) == 2


class TestGetMonoidalData:
    def test_structure_and_all_axioms_pass(self):
        data = get_monoidal_data(n_states=15, seed=3)
        assert set(data.keys()) == {"tensor_product", "unit", "coherence", "axioms"}
        assert len(data["axioms"]) == 4
        for axiom in data["axioms"]:
            assert axiom["passed"] is True, f"{axiom['name']} failed"


class TestGetOperadData:
    def test_structure(self):
        data = get_operad_data(n_states=15, seed=3)
        assert "operations" in data
        assert "axioms" in data
        assert "tree_example" in data


class TestLatticeLaws:
    """Direct law tests for DefenseLattice / lattice_meet / lattice_join."""

    def test_meet_idempotence(self):
        """a ∧ a = a for all lattice elements."""
        for rate in [0.0, 0.3, 0.5, 0.7, 1.0]:
            a = DetectionBound(rate)
            m = lattice_meet(a, a)
            assert math.isclose(m.rate, a.rate, abs_tol=1e-10)

    def test_join_not_idempotent_by_design(self):
        """a ∨ a != a for a not in {0, 1} -- lattice_join is a ≠ idempotent op.

        lattice_join implements a probabilistic-OR / series-composition
        combinator (a + b - ab), which satisfies the upper-bound property
        exercised by DefenseLattice.verify_join_existence() (join(a,b) >= a
        and >= b) but is NOT an idempotent lattice join in the strict
        algebraic sense: join(a, a) = 2a - a^2 != a for a in (0, 1). This
        documents that behavior explicitly rather than asserting the
        (false) idempotence law, so a future change to lattice_join's
        formula shows up here as an intentional decision, not a silent
        regression. See lattice_meet (min-based) for the operation that
        *is* a genuine idempotent/absorptive semilattice operation.
        """
        a = DetectionBound(0.3)
        j = lattice_join(a, a)
        assert not math.isclose(j.rate, a.rate, abs_tol=1e-10)
        assert math.isclose(j.rate, 2 * a.rate - a.rate ** 2, abs_tol=1e-10)

    def test_meet_absorption(self):
        """a ∧ (a ∨ b) = a (absorption law) -- holds because join(a,b) >= a always."""
        a, b = DetectionBound(0.3), DetectionBound(0.7)
        lhs = lattice_meet(a, lattice_join(a, b))
        assert math.isclose(lhs.rate, a.rate, abs_tol=1e-10)

    def test_join_absorption_does_not_hold(self):
        """a ∨ (a ∧ b) != a in general -- the dual absorption law fails.

        Since lattice_join is not idempotent (see test above), the dual
        absorption law a ∨ (a ∧ b) = a does not hold either, except in the
        degenerate cases where min(a,b) in {0} or a == 1.
        """
        a, b = DetectionBound(0.3), DetectionBound(0.7)
        lhs = lattice_join(a, lattice_meet(a, b))
        assert not math.isclose(lhs.rate, a.rate, abs_tol=1e-10)

    def test_bottom_and_top_are_absorbing(self):
        a = DetectionBound(0.5)
        assert math.isclose(lattice_meet(a, BOTTOM).rate, BOTTOM.rate, abs_tol=1e-10)
        assert math.isclose(lattice_join(a, TOP).rate, TOP.rate, abs_tol=1e-10)

    def test_full_lattice_verify_all_passes(self):
        lattice = DefenseLattice(elements=[
            DetectionBound(0.0), DetectionBound(0.3), DetectionBound(0.5),
            DetectionBound(0.7), DetectionBound(1.0),
        ])
        results = lattice.verify_all()
        assert all(results.values()), results


class TestMonadLaws:
    """Direct law tests for DefenseMonad (left/right unit, associativity)."""

    def test_left_unit_law(self):
        monad = DefenseMonad()
        states = generate_test_states(n=10, seed=1)
        f = make_test_morphism(0.6, "f")
        assert monad.verify_left_unit(f, states) is True

    def test_right_unit_law(self):
        monad = DefenseMonad()
        states = generate_test_states(n=10, seed=1)
        f = make_test_morphism(0.6, "f")
        assert monad.verify_right_unit(f, states) is True

    def test_associativity_law(self):
        monad = DefenseMonad()
        states = generate_test_states(n=10, seed=1)
        f = make_test_morphism(0.7, "f")
        g = make_test_morphism(0.5, "g")
        h = make_test_morphism(0.3, "h")
        assert monad.verify_associativity(f, g, h, states) is True

    def test_kleisli_compose_ors_detection_and_maxes_score(self):
        monad = DefenseMonad()
        state = generate_test_states(n=1, seed=2)[0]
        f = make_test_morphism(0.2, "low")
        g = make_test_morphism(0.9, "high")
        composed = monad.kleisli_compose(f, g)
        r_f, r_g, r_c = f(state), g(state), composed(state)
        assert r_c.detected == (r_f.detected or r_g.detected)
        assert r_c.score == max(r_f.score, r_g.score)


class TestLensLaws:
    """Direct law tests for BeliefLens / DefenseProfunctor.verify_lens_laws."""

    def test_get_put_law(self):
        """set(s, get(s)) = s."""
        lens = BeliefLens(focus="trust")
        state = {"trust": 0.42, "consensus": 0.1}
        restored = lens.set(state, lens.get(state))
        assert math.isclose(restored["trust"], state["trust"], abs_tol=1e-10)

    def test_put_get_law(self):
        """get(set(s, v)) = v."""
        lens = BeliefLens(focus="trust")
        state = {"trust": 0.1}
        modified = lens.set(state, 0.99)
        assert math.isclose(lens.get(modified), 0.99, abs_tol=1e-10)

    def test_put_put_law(self):
        """set(set(s, v1), v2) = set(s, v2)."""
        lens = BeliefLens(focus="trust")
        state = {"trust": 0.1}
        two_puts = lens.set(lens.set(state, 0.3), 0.7)
        one_put = lens.set(state, 0.7)
        assert math.isclose(two_puts["trust"], one_put["trust"], abs_tol=1e-10)

    def test_verify_lens_laws_all_pass(self):
        lens = BeliefLens(focus="trust")
        profunctor = DefenseProfunctor(
            get_fn=lambda s: s,
            put_fn=lambda s, r: {**s, "defense_result": r.score},
        )
        states = generate_test_states(n=10, seed=5)
        results = profunctor.verify_lens_laws(lens, states)
        assert results == {"get_put": True, "put_get": True, "put_put": True}


class TestFAlgebraCatamorphism:
    """cata() folds a list of morphisms through an F-algebra structure map."""

    def test_cata_empty_morphisms_uses_base_case(self):
        algebra = make_detection_algebra()
        result = cata(algebra, [], {"trust": 0.5})
        assert result.detected is False
        assert result.score == 0.0

    def test_cata_accumulates_detection_and_score(self):
        algebra = make_detection_algebra()
        f = make_test_morphism(0.6, "f")
        g = make_test_morphism(0.8, "g")
        state = {"injection_risk": 0.0}
        result = cata(algebra, [f, g], state)
        # Algebra amplifies score by 1.05x each fold step; result should
        # reflect at least the max underlying morphism score, amplified.
        assert result.score >= 0.8
        assert result.detected is True


class TestOperadLaws:
    def test_operad_unit_and_associativity_pass(self):
        operad = DefenseOperad()
        states = generate_test_states(n=10, seed=9)
        f = make_test_morphism(0.7, "f")
        g = make_test_morphism(0.5, "g")
        h = make_test_morphism(0.3, "h")
        assert operad.verify_operad_unit(f, states) is True
        assert operad.verify_operad_associativity(f, g, h, states) is True


class TestMonoidalLaws:
    def test_all_coherence_laws_pass(self):
        monoidal = MonoidalDefenseCategory()
        states = generate_test_states(n=10, seed=11)
        f = make_test_morphism(0.7, "f")
        g = make_test_morphism(0.5, "g")
        h = make_test_morphism(0.3, "h")
        results = monoidal.verify_all(f, g, h, states)
        assert all(results.values()), results
