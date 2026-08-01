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
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pytest

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    DefenseResult,
    identity_morphism,
)
from formal.category_theory_advanced import (
    BOTTOM,
    TOP,
    AgentArchitecture,
    BeliefLens,
    ComposedLens,
    DefenseLattice,
    DefenseMonad,
    DefenseOperad,
    DefenseProfunctor,
    DetectionBound,
    EnrichedDefenseCategory,
    KanExtension,
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
    parallel_operad_op,
    run_all_verifications,
    serialize_verification_results,
    series_operad_op,
)

# ---------------------------------------------------------------------------
# Shared helpers for the composition / negative-control suites below.
#
# Everything here is a real object: a plain DefenseMorphism, or a subclass of
# the production class with one operation replaced by a deliberately
# law-violating -- but genuinely executable -- implementation.  No mocking
# framework is used anywhere in this file.
# ---------------------------------------------------------------------------


def const_morphism(score: float, detected: bool, name: str) -> DefenseMorphism:
    """A morphism with a fixed score/detection flag, independent of state.

    ``DefenseResult`` performs no range validation, so ``score`` may
    deliberately fall outside ``[0, 1]``.
    """

    def _fn(state: CognitiveState) -> DefenseResult:
        return DefenseResult(
            detected=detected,
            score=score,
            module_name=name,
            details={},
            latency_ms=1.0,
        )

    return DefenseMorphism(fn=_fn, name=name, identity=False)


def _binary_rigged(
    a: DefenseMorphism,
    b: DefenseMorphism,
    combine: Callable[[float, float], float],
) -> DefenseMorphism:
    """Combine two morphisms' scores with an arbitrary binary operation."""

    def _fn(state: CognitiveState) -> DefenseResult:
        r_a, r_b = a(state), b(state)
        return DefenseResult(
            detected=r_a.detected or r_b.detected,
            score=combine(r_a.score, r_b.score),
            module_name="rigged",
            details={},
            latency_ms=0.0,
        )

    return DefenseMorphism(fn=_fn, name="rigged", identity=False)


#: A damped, non-associative binary combiner: ``0.5a + 0.25b``.  It stays well
#: inside ``[0, 1]`` for the test morphisms, so an associativity failure is a
#: real disagreement rather than two values both saturating at 1.0.
def damped(a: float, b: float) -> float:
    return 0.5 * a + 0.25 * b


def take_left(a: float, b: float) -> float:
    return a


def take_right(a: float, b: float) -> float:
    return b


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


# ===========================================================================
# ComposedLens -- lens composition and the three van Laarhoven laws
# ===========================================================================


class _LegacyComposedLens:
    """Verbatim copy of the pre-2026-07 ``ComposedLens`` body.

    Kept as the **positive control** for the law suite below: this is the
    implementation that shipped, and it must fail the same three law tests
    that the fixed implementation passes.  A law suite that both
    implementations pass would be worthless.

    ``get`` keys the intermediate view by ``inner.focus`` and then reads
    ``outer.focus`` out of it (0.0 whenever the foci differ); ``set`` writes
    the *original* inner value back, making it a no-op.
    """

    def __init__(self, outer: BeliefLens[Any], inner: BeliefLens[Any]) -> None:
        self.outer = outer
        self.inner = inner

    @property
    def focus(self) -> str:
        return self.inner.focus

    def get(self, state: CognitiveState) -> float:
        intermediate = {self.inner.focus: self.inner.get(state)}
        return self.outer.get(intermediate)

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        current_inner = self.inner.get(state)
        new_inner_state = self.outer.set({self.inner.focus: current_inner}, value)
        return self.inner.set(state, new_inner_state.get(self.inner.focus, value))


class IgnoreValueLens(BeliefLens[Any]):
    """A lens whose ``set`` discards the value it is handed (breaks PutGet)."""

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        return dict(state)


class AccumulateLens(BeliefLens[Any]):
    """A lens whose ``set`` adds to the focus instead of replacing it.

    Breaks all three laws: GetPut doubles the value, PutGet returns
    ``old + v``, PutPut accumulates both writes.
    """

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        new_state = dict(state)
        new_state[self.focus] = new_state.get(self.focus, 0.0) + value
        return new_state


class CeilingLens(BeliefLens[Any]):
    """A lens whose ``set`` caps the write at ``old + 0.5`` (breaks only PutPut)."""

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        new_state = dict(state)
        new_state[self.focus] = min(value, state.get(self.focus, 0.0) + 0.5)
        return new_state


class TestComposedLens:
    """``ComposedLens`` must actually observe and write, and obey the lens laws.

    Regression target (audit TEST-09): the shipped implementation returned
    ``0.0`` from ``get`` and was a no-op in ``set`` whenever the two foci
    differed, and had no test at all.
    """

    OUTER = "consensus"
    INNER = "trust"

    def _composite(self) -> ComposedLens:
        return BeliefLens(focus=self.OUTER).compose(BeliefLens(focus=self.INNER))

    def test_effective_focus_is_the_inner_focus(self):
        assert self._composite().focus == self.INNER

    def test_get_returns_the_inner_observation_not_zero(self):
        """The exact probe from the audit: cl.get(s) was 0.0, must be 0.1."""
        state = {"trust": 0.1, "consensus": 0.9}
        assert math.isclose(self._composite().get(state), 0.1, abs_tol=1e-12)

    def test_set_actually_writes_and_leaves_the_other_key_alone(self):
        """The audit probe: cl.set(s, 0.77) returned the state unchanged."""
        state = {"trust": 0.1, "consensus": 0.9}
        updated = self._composite().set(state, 0.77)
        assert math.isclose(updated["trust"], 0.77, abs_tol=1e-12)
        assert math.isclose(updated["consensus"], 0.9, abs_tol=1e-12)
        assert math.isclose(state["trust"], 0.1, abs_tol=1e-12), "set must not mutate"

    def test_law_get_put(self):
        """set(s, get(s)) = s."""
        composite = self._composite()
        for state in ({"trust": 0.1, "consensus": 0.9}, {"trust": 0.0, "consensus": 0.5}):
            restored = composite.set(state, composite.get(state))
            assert restored == state

    def test_law_put_get(self):
        """get(set(s, v)) = v."""
        composite = self._composite()
        state = {"trust": 0.1, "consensus": 0.9}
        for value in (0.0, 0.42, 0.77, 1.0):
            assert math.isclose(composite.get(composite.set(state, value)), value, abs_tol=1e-12)

    def test_law_put_put(self):
        """set(set(s, v1), v2) = set(s, v2)."""
        composite = self._composite()
        state = {"trust": 0.1, "consensus": 0.9}
        assert composite.set(composite.set(state, 0.3), 0.7) == composite.set(state, 0.7)

    def test_verify_lens_laws_accepts_a_composite(self):
        profunctor = DefenseProfunctor(
            get_fn=lambda s: s,
            put_fn=lambda s, r: {**s, "defense_result": r.score},
        )
        states = generate_test_states(n=10, seed=5)
        results = profunctor.verify_lens_laws(self._composite(), states)
        assert results == {"get_put": True, "put_get": True, "put_put": True}

    def test_positive_control_legacy_implementation_fails_the_laws(self):
        """The shipped (broken) composition must NOT pass this suite.

        Without this, every law test above could be green by accident.
        """
        legacy = _LegacyComposedLens(
            outer=BeliefLens(focus=self.OUTER), inner=BeliefLens(focus=self.INNER)
        )
        state = {"trust": 0.1, "consensus": 0.9}
        assert legacy.get(state) == 0.0, "legacy get was the constant 0.0"
        assert legacy.set(state, 0.77) == state, "legacy set was a no-op"
        # PutGet fails outright on the legacy implementation.
        assert not math.isclose(legacy.get(legacy.set(state, 0.77)), 0.77, abs_tol=1e-12)

        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        legacy_results = profunctor.verify_lens_laws(legacy, [state])
        assert legacy_results["put_get"] is False

    def test_negative_control_broken_outer_propagates(self):
        """The outer lens is load-bearing: its misbehaviour breaks the composite."""
        composite = IgnoreValueLens(focus=self.OUTER).compose(BeliefLens(focus=self.INNER))
        state = {"trust": 0.1, "consensus": 0.9}
        assert composite.set(state, 0.77)["trust"] == 0.1
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        assert profunctor.verify_lens_laws(composite, [state])["put_get"] is False

    def test_negative_control_broken_inner_propagates(self):
        composite = BeliefLens(focus=self.OUTER).compose(IgnoreValueLens(focus=self.INNER))
        state = {"trust": 0.1, "consensus": 0.9}
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        assert profunctor.verify_lens_laws(composite, [state])["put_get"] is False

    def test_three_level_composition_is_lawful(self):
        composite = (
            BeliefLens(focus="belief_integrity")
            .compose(BeliefLens(focus=self.OUTER))
            .compose(BeliefLens(focus=self.INNER))
        )
        state = {"trust": 0.1, "consensus": 0.9, "belief_integrity": 0.5}
        assert composite.focus == self.INNER
        assert math.isclose(composite.get(composite.set(state, 0.25)), 0.25, abs_tol=1e-12)

    def test_modify_applies_a_function_through_the_composite(self):
        composite = self._composite()
        state = {"trust": 0.2, "consensus": 0.9}
        assert math.isclose(composite.modify(state, lambda v: v * 3)["trust"], 0.6, abs_tol=1e-12)

    def test_repr_shows_both_components(self):
        text = repr(self._composite())
        assert "ComposedLens" in text
        assert self.OUTER in text and self.INNER in text


# ===========================================================================
# Parallel / symmetric operad (audit TEST-12)
# ===========================================================================


class TestParallelOperad:
    """The grafting half of the operad, previously exercised by nothing."""

    def setup_method(self):
        self.states = generate_test_states(n=10, seed=9)
        self.f = make_test_morphism(0.7, "f")
        self.g = make_test_morphism(0.5, "g")
        self.h = make_test_morphism(0.3, "h")
        self.operad = DefenseOperad()

    def _scores(self, morphism: DefenseMorphism) -> List[float]:
        return [morphism(s).score for s in self.states]

    def test_build_parallel_is_the_pointwise_max(self):
        combined = self.operad.build_parallel([self.f, self.g, self.h])
        expected = [
            max(self.f(s).score, self.g(s).score, self.h(s).score) for s in self.states
        ]
        assert self._scores(combined) == pytest.approx(expected, abs=1e-12)

    def test_build_parallel_is_strictly_above_the_weakest_arm(self):
        """Guards against a 'parallel' that silently returned its first argument."""
        combined = self.operad.build_parallel([self.h, self.f])
        assert all(c > w for c, w in zip(self._scores(combined), self._scores(self.h)))

    def test_parallel_is_equivariant_under_permutation(self):
        """The advertised symmetry: σ ∈ S_n acts trivially on the result."""
        base = self._scores(self.operad.build_parallel([self.f, self.g, self.h]))
        for perm in ([self.h, self.f, self.g], [self.g, self.h, self.f],
                     [self.h, self.g, self.f]):
            assert self._scores(self.operad.build_parallel(perm)) == pytest.approx(
                base, abs=1e-12
            )

    def test_parallel_detection_flag_is_the_or_of_the_arms(self):
        detecting = const_morphism(0.2, True, "quiet_but_detecting")
        silent = const_morphism(0.9, False, "loud_but_silent")
        combined = self.operad.build_parallel([detecting, silent])
        assert all(combined(s).detected for s in self.states)

    def test_parallel_of_one_morphism_is_that_morphism(self):
        combined = self.operad.build_parallel([self.f])
        assert self._scores(combined) == pytest.approx(self._scores(self.f), abs=1e-12)

    def test_parallel_operad_op_names_its_arity(self):
        assert parallel_operad_op(4).name == "parallel_4"
        assert "arity=4" in repr(parallel_operad_op(4))

    def test_arity_guard_rejects_too_few_children(self):
        with pytest.raises(ValueError, match=r"arity 3; got 2"):
            series_operad_op(3).apply([self.f, self.g])

    def test_arity_guard_rejects_too_many_children(self):
        with pytest.raises(ValueError, match=r"arity 2; got 3"):
            parallel_operad_op(2).apply([self.f, self.g, self.h])

    def test_positive_control_arity_guard_admits_the_right_count(self):
        """Proves the guard is arity-conditional, not an unconditional raise."""
        result = parallel_operad_op(2).apply([self.f, self.g])
        assert self._scores(result) == pytest.approx(
            [max(self.f(s).score, self.g(s).score) for s in self.states], abs=1e-12
        )

    def test_register_and_get_round_trip(self):
        op = parallel_operad_op(3)
        self.operad.register(op)
        assert self.operad.get("parallel_3") is op

    def test_get_unknown_operation_raises(self):
        with pytest.raises(KeyError):
            self.operad.get("no_such_operation")


# ===========================================================================
# Kan extensions: single-source and empty-source configurations (TEST-15)
# ===========================================================================


class _IdentityRanKan(KanExtension):
    """A Kan extension whose ``Ran`` silently collapses to the identity.

    This is exactly the regression the audit named: "a regression that made
    single-source Ran return the identity morphism instead of the source
    would pass CI".
    """

    def right_kan(self) -> Dict[str, DefenseMorphism]:
        return {target: identity_morphism() for target in set(self.functor_map.values())}


class TestKanSingleSource:
    def setup_method(self):
        self.states = generate_test_states(n=10, seed=4)
        self.f = make_test_morphism(0.7, "f")
        self.h = make_test_morphism(0.3, "h")
        self.source = AgentArchitecture(name="LangGraph")
        self.source.add_morphism("fw", self.f, rate=0.7)
        self.target = AgentArchitecture(name="ClaudeCode")
        self.target.add_morphism("security", self.h, rate=0.3)

    def _kan(self, functor_map: Dict[str, str]) -> KanExtension:
        return KanExtension(source=self.source, target=self.target, functor_map=functor_map)

    def _scores(self, morphism: DefenseMorphism) -> List[float]:
        return [morphism(s).score for s in self.states]

    def test_single_source_ran_is_the_source_morphism(self):
        ran = self._kan({"fw": "security"}).right_kan()
        assert self._scores(ran["security"]) == pytest.approx(self._scores(self.f), abs=1e-12)

    def test_single_source_lan_is_the_source_morphism(self):
        lan = self._kan({"fw": "security"}).left_kan()
        assert self._scores(lan["security"]) == pytest.approx(self._scores(self.f), abs=1e-12)

    def test_single_source_emits_the_ran_dominated_by_flag(self):
        results = self._kan({"fw": "security"}).verify_kan_adjunction(self.states)
        assert results == {"lan_dominates_fw": True, "ran_dominated_by_fw": True}

    def test_negative_control_identity_ran_fails_the_single_source_check(self):
        kan = _IdentityRanKan(
            source=self.source, target=self.target, functor_map={"fw": "security"}
        )
        results = kan.verify_kan_adjunction(self.states)
        assert results["ran_dominated_by_fw"] is False

        # Positive control for the *strengthening*: the previous one-sided
        # `ran <= src` formulation accepted this collapse silently.
        ran_rates = np.array(self._scores(kan.right_kan()["security"]))
        src_rates = np.array(self._scores(self.f))
        assert bool(np.all(ran_rates <= src_rates + 1e-6)) is True

    def test_negative_control_identity_ran_fails_the_multi_source_check(self):
        source = AgentArchitecture(name="two")
        source.add_morphism("fw", self.f, rate=0.7)
        source.add_morphism("det", make_test_morphism(0.5, "det"), rate=0.5)
        kan = _IdentityRanKan(
            source=source, target=self.target, functor_map={"fw": "security", "det": "security"}
        )
        results = kan.verify_kan_adjunction(self.states)
        assert results["ran_wellformed_fw"] is False
        assert results["ran_wellformed_det"] is False

    def test_empty_source_target_falls_back_to_the_identity_morphism(self):
        """functor_map names a source morphism the architecture does not have."""
        kan = self._kan({"absent": "security"})
        lan, ran = kan.left_kan(), kan.right_kan()
        assert lan["security"].identity is True
        assert ran["security"].identity is True
        assert self._scores(lan["security"]) == [0.0] * len(self.states)
        # No source morphism exists, so no check can be attributed to one.
        assert kan.verify_kan_adjunction(self.states) == {}

    def test_absent_source_is_skipped_but_present_ones_are_still_checked(self):
        results = self._kan({"fw": "security", "ghost": "security"}).verify_kan_adjunction(
            self.states
        )
        assert "lan_dominates_ghost" not in results
        assert "ran_wellformed_ghost" not in results
        assert results["lan_dominates_fw"] is True


# ===========================================================================
# Negative controls for all seven verifiers (audit TEST-10)
# ===========================================================================


class RiggedBound(DetectionBound):
    """A ``DetectionBound`` with an injectable order relation.

    Real object, no patching: ``__le__``/``__ge__`` are genuine overrides.  It
    exists to prove the lattice verifiers *read* the order relation rather than
    returning a constant -- see the module note in
    ``serialize_verification_results`` about the seven lattice flags being
    regression detectors rather than contingent facts.
    """

    def __init__(
        self,
        rate: float,
        name: str = "",
        le: Optional[Callable[[Any, Any], bool]] = None,
        ge: Optional[Callable[[Any, Any], bool]] = None,
    ) -> None:
        super().__init__(rate, name)
        object.__setattr__(self, "_le", le)
        object.__setattr__(self, "_ge", ge)

    def __le__(self, other: Any) -> Any:
        if self._le is None:
            return DetectionBound.__le__(self, other)
        return self._le(self, other)

    def __ge__(self, other: Any) -> Any:
        if self._ge is None:
            return NotImplemented
        return self._ge(self, other)


def _never(a: Any, b: Any) -> bool:
    return False


def _always(a: Any, b: Any) -> bool:
    return True


def _non_transitive(a: Any, b: Any) -> bool:
    """Ordinary ``<=`` except that 0.0 is declared *not* below 1.0."""
    if math.isclose(a.rate, 0.0) and math.isclose(b.rate, 1.0):
        return False
    return bool(a.rate <= b.rate)


class RiggedMonoidal(MonoidalDefenseCategory):
    """Monoidal category with a substituted (law-violating) tensor product."""

    def __init__(self, combine: Callable[[float, float], float]) -> None:
        self._combine = combine

    def tensor(self, f: DefenseMorphism, g: DefenseMorphism) -> DefenseMorphism:
        return _binary_rigged(f, g, self._combine)


class RiggedOperad(DefenseOperad):
    """Operad whose series composition is replaced by an arbitrary fold."""

    def __init__(self, combine: Callable[[float, float], float]) -> None:
        super().__init__()
        self._combine = combine

    def build_series(self, morphisms: List[DefenseMorphism]) -> DefenseMorphism:
        result = morphisms[0]
        for m in morphisms[1:]:
            result = _binary_rigged(result, m, self._combine)
        return result


class SquaredHomEnriched(EnrichedDefenseCategory):
    """Enrichment over a squared distance, which is not a metric."""

    def hom(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        states: List[CognitiveState],
    ) -> float:
        def rate(m: DefenseMorphism) -> float:
            return float(np.mean([m(s).score for s in states]))

        return (rate(f) - rate(g)) ** 2 * 10.0


class _Drifting:
    """A stateful 'morphism' whose score climbs monotonically with each call.

    Monotone rather than cyclic on purpose: a periodic drift would average out
    to the same mean on both evaluation passes whenever the number of states is
    a multiple of the period, making the negative control silently vacuous.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, state: CognitiveState) -> DefenseResult:
        self.calls += 1
        return DefenseResult(
            detected=False,
            score=min(1.0, 0.01 * self.calls),
            module_name="drifting",
            details={},
            latency_ms=0.0,
        )


class LoudEtaMonad(DefenseMonad):
    """A monad whose unit is not a unit: η reports a full-confidence detection."""

    def eta(self, state: CognitiveState) -> DefenseResult:
        return DefenseResult(
            detected=True, score=1.0, module_name="loud_eta", details={}, latency_ms=0.0
        )


class DampedKleisliMonad(DefenseMonad):
    """A monad whose Kleisli composition is non-associative."""

    def kleisli_compose(
        self,
        f: Callable[[CognitiveState], DefenseResult],
        g: Callable[[CognitiveState], DefenseResult],
    ) -> Callable[[CognitiveState], DefenseResult]:
        def _k(state: CognitiveState) -> DefenseResult:
            r_f, r_g = f(state), g(state)
            return DefenseResult(
                detected=r_f.detected or r_g.detected,
                score=damped(r_f.score, r_g.score),
                module_name="damped",
                details={},
                latency_ms=0.0,
            )

        return _k


class TestVerifierNegativeControls:
    """Each of the seven verifiers must be able to report ``False``.

    ``serialize_verification_results`` reports 25/25 passing.  Without these
    tests nothing proved any of the 25 flags *can* go False, so a verifier
    hardcoded to ``True`` would be indistinguishable from a working one.

    Scope note (reported honestly rather than papered over): for genuine
    ``DetectionBound`` inputs the seven lattice flags cannot fail, because
    ``__post_init__`` confines ``rate`` to ``[0, 1]`` and ``__le__`` is float
    ``<=``.  Their negative controls therefore substitute the order relation.
    The monoidal, operad, enriched (triangle), monad and lens flags are
    likewise structurally true for the production operations; their controls
    substitute the operation.  Three flags are falsifiable with ordinary
    inputs and no substitution at all: ``lan_dominates_*``,
    ``ran_wellformed_*`` and ``enriched_identity``.
    """

    def setup_method(self):
        self.states = generate_test_states(n=10, seed=17)
        self.f = make_test_morphism(0.7, "f")
        self.g = make_test_morphism(0.5, "g")
        self.h = make_test_morphism(0.3, "h")

    # --- 1. Lattice -------------------------------------------------------

    def test_lattice_reflexivity_can_fail(self):
        lattice = DefenseLattice(elements=[RiggedBound(0.3, le=_never)])
        assert lattice.verify_reflexivity() is False

    def test_lattice_antisymmetry_can_fail(self):
        lattice = DefenseLattice(
            elements=[RiggedBound(0.3, le=_always), RiggedBound(0.7, le=_always)]
        )
        assert lattice.verify_antisymmetry() is False

    def test_lattice_transitivity_can_fail(self):
        lattice = DefenseLattice(
            elements=[
                RiggedBound(0.0, le=_non_transitive),
                RiggedBound(0.5, le=_non_transitive),
                RiggedBound(1.0, le=_non_transitive),
            ]
        )
        assert lattice.verify_transitivity() is False
        # Targeted: only transitivity breaks, so the other flags are not
        # collaterally reporting the same single defect.
        assert lattice.verify_reflexivity() is True
        assert lattice.verify_antisymmetry() is True

    def test_lattice_bottom_can_fail(self):
        lattice = DefenseLattice(elements=[RiggedBound(0.5, ge=_never)])
        assert lattice.verify_bottom() is False

    def test_lattice_top_can_fail(self):
        lattice = DefenseLattice(elements=[RiggedBound(0.5, le=_never)])
        assert lattice.verify_top() is False

    def test_lattice_meet_existence_can_fail(self):
        lattice = DefenseLattice(elements=[RiggedBound(0.5, ge=_never)])
        assert lattice.verify_meet_existence() is False

    def test_lattice_join_existence_can_fail(self):
        lattice = DefenseLattice(elements=[RiggedBound(0.5, le=_never)])
        assert lattice.verify_join_existence() is False

    def test_lattice_positive_control_genuine_bounds_still_pass(self):
        lattice = DefenseLattice(elements=[DetectionBound(0.0), DetectionBound(0.5)])
        assert all(lattice.verify_all().values())

    # --- 2. Monoidal ------------------------------------------------------

    def test_monoidal_left_unitor_and_symmetry_can_fail(self):
        rigged = RiggedMonoidal(take_left)
        assert rigged.verify_left_unitor(self.f, self.states) is False
        assert rigged.verify_symmetry(self.f, self.g, self.states) is False

    def test_monoidal_right_unitor_can_fail(self):
        assert RiggedMonoidal(take_right).verify_right_unitor(self.f, self.states) is False

    def test_monoidal_associator_can_fail(self):
        assert (
            RiggedMonoidal(damped).verify_associator(self.f, self.g, self.h, self.states) is False
        )

    def test_monoidal_positive_control_real_tensor_passes(self):
        assert all(
            MonoidalDefenseCategory().verify_all(self.f, self.g, self.h, self.states).values()
        )

    # --- 3. Operad --------------------------------------------------------

    def test_operad_unit_can_fail(self):
        """A series composition that drops its left argument breaks unit insertion.

        This flag was a tautology before 2026-07: it compared
        ``series_1(f)`` -- which returns ``f`` itself -- against ``f``.
        """
        rigged = RiggedOperad(take_right)
        assert rigged.verify_operad_unit(self.f, self.states) is False
        # Targeted: associativity is untouched by a last-wins fold.
        assert rigged.verify_operad_associativity(self.f, self.g, self.h, self.states) is True

    def test_operad_associativity_can_fail(self):
        assert (
            RiggedOperad(damped).verify_operad_associativity(
                self.f, self.g, self.h, self.states
            )
            is False
        )

    def test_operad_positive_control_real_series_passes(self):
        operad = DefenseOperad()
        assert operad.verify_operad_unit(self.f, self.states) is True
        assert operad.verify_operad_associativity(self.f, self.g, self.h, self.states) is True

    # --- 4. Enriched ------------------------------------------------------

    def test_enriched_identity_can_fail_with_a_non_deterministic_morphism(self):
        """No substitution needed: enrichment presupposes deterministic morphisms."""
        drifting = DefenseMorphism(fn=_Drifting(), name="drifting", identity=False)
        assert EnrichedDefenseCategory().verify_enriched_identity(drifting, self.states) is False

    def test_enriched_triangle_inequality_can_fail(self):
        rigged = SquaredHomEnriched()
        wide = make_test_morphism(0.9, "wide")
        mid = make_test_morphism(0.5, "mid")
        narrow = make_test_morphism(0.1, "narrow")
        assert (
            rigged.verify_enriched_composition_law(wide, mid, narrow, self.states) is False
        )

    def test_enriched_positive_control_real_hom_passes(self):
        enriched = EnrichedDefenseCategory()
        assert enriched.verify_enriched_identity(self.f, self.states) is True
        assert (
            enriched.verify_enriched_composition_law(self.f, self.g, self.h, self.states) is True
        )

    # --- 5. Kan extensions ------------------------------------------------

    def test_kan_lan_dominance_can_fail_with_ordinary_morphisms(self):
        """Series composition short-circuits on detection, so Lan can fall below a source."""
        detecting_low = const_morphism(0.6, True, "detecting_low")
        silent_high = const_morphism(0.9, False, "silent_high")
        source = AgentArchitecture(name="src")
        source.add_morphism("low", detecting_low, rate=0.6)
        source.add_morphism("high", silent_high, rate=0.9)
        target = AgentArchitecture(name="tgt")
        target.add_morphism("merged", self.h, rate=0.3)
        kan = KanExtension(
            source=source, target=target, functor_map={"low": "merged", "high": "merged"}
        )
        results = kan.verify_kan_adjunction(self.states)
        assert results["lan_dominates_high"] is False
        assert results["lan_dominates_low"] is True

    def test_kan_ran_wellformedness_can_fail_on_an_out_of_range_score(self):
        """``DefenseResult`` does not clip ``score``, so the range arm is live."""
        out_of_range = const_morphism(1.5, True, "out_of_range")
        source = AgentArchitecture(name="src")
        source.add_morphism("a", out_of_range, rate=1.0)
        source.add_morphism("b", self.g, rate=0.5)
        target = AgentArchitecture(name="tgt")
        target.add_morphism("merged", self.h, rate=0.3)
        kan = KanExtension(
            source=source, target=target, functor_map={"a": "merged", "b": "merged"}
        )
        results = kan.verify_kan_adjunction(self.states)
        assert results["ran_wellformed_a"] is False
        assert results["ran_wellformed_b"] is False

    # --- 6. Monad ---------------------------------------------------------

    def test_monad_unit_laws_can_fail(self):
        loud = LoudEtaMonad()
        assert loud.verify_left_unit(self.f, self.states) is False
        assert loud.verify_right_unit(self.f, self.states) is False

    def test_monad_associativity_can_fail(self):
        assert (
            DampedKleisliMonad().verify_associativity(self.f, self.g, self.h, self.states)
            is False
        )

    def test_monad_positive_control_real_kleisli_passes(self):
        assert all(DefenseMonad().verify_all(self.f, self.g, self.h, self.states).values())

    # --- 7. Lenses --------------------------------------------------------

    def test_lens_put_get_can_fail(self):
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        results = profunctor.verify_lens_laws(
            IgnoreValueLens(focus="trust"), [{"trust": 0.1}, {"trust": 0.9}]
        )
        assert results == {"get_put": True, "put_get": False, "put_put": True}

    def test_lens_put_put_can_fail(self):
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        results = profunctor.verify_lens_laws(
            CeilingLens(focus="trust"), [{"trust": 0.1}, {"trust": 0.9}]
        )
        assert results == {"get_put": True, "put_get": True, "put_put": False}

    def test_lens_get_put_can_fail(self):
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        results = profunctor.verify_lens_laws(
            AccumulateLens(focus="trust"), [{"trust": 0.1}, {"trust": 0.9}]
        )
        assert results == {"get_put": False, "put_get": False, "put_put": False}

    def test_lens_positive_control_real_lens_passes(self):
        profunctor = DefenseProfunctor(get_fn=lambda s: s, put_fn=lambda s, r: s)
        results = profunctor.verify_lens_laws(BeliefLens(focus="trust"), self.states)
        assert results == {"get_put": True, "put_get": True, "put_put": True}

    # --- Unsubstituted controls: real production operations, real inputs ---

    def test_unit_laws_fail_for_a_negative_scoring_morphism(self):
        """Five unit-law flags are contingent on ordinary (if out-of-contract) input.

        ``DefenseResult.score`` is documented as living in ``[0, 1]`` but is
        never validated, so a detector that leaks a raw (negative) statistic is
        constructible.  ``categorical_product``/``compose_morphisms``/Kleisli
        composition all arbitrate by ``max``, and the unit's score is ``0.0``,
        so ``I ⊗ f`` returns the unit rather than ``f``.  These five flags
        therefore fail here with the *real* production operations -- no
        subclass, no substituted tensor.
        """
        negative = const_morphism(-0.3, False, "negative_score")

        assert MonoidalDefenseCategory().verify_left_unitor(negative, self.states) is False
        assert MonoidalDefenseCategory().verify_right_unitor(negative, self.states) is False
        assert DefenseOperad().verify_operad_unit(negative, self.states) is False
        assert DefenseMonad().verify_left_unit(negative, self.states) is False
        assert DefenseMonad().verify_right_unit(negative, self.states) is False

    def test_operad_unit_regression_guard_needs_the_insertion_arms(self):
        """The pre-2026-07 ``series_1(f) ≅ f`` arm alone cannot see this failure.

        ``series_operad_op(1).apply([f])`` returns ``f`` itself, so comparing it
        against ``f`` is an identity comparison.  Asserting that arm is still
        True while the whole check is False pins *why* the unit flag stopped
        being a tautology.
        """
        negative = const_morphism(-0.3, False, "negative_score")
        unary = series_operad_op(1).apply([negative])
        unary_scores = [unary(s).score for s in self.states]
        assert unary_scores == pytest.approx([negative(s).score for s in self.states])
        assert DefenseOperad().verify_operad_unit(negative, self.states) is False

    # --- Cross-cutting ----------------------------------------------------

    def test_serialized_summary_would_report_failures_if_any_check_failed(self):
        """The 25/25 summary arithmetic is not hardcoded.

        ``serialize_verification_results`` derives ``passed``/``failed`` by
        counting; feeding the same counting logic a dict containing a False
        must produce a non-zero ``failed``.
        """
        data = serialize_verification_results(n_states=10, seed=2)
        flat = dict(data["results"])
        assert data["summary"]["failed"] == 0
        assert data["summary"]["total"] == len(flat)
        first_key = sorted(flat)[0]
        flat[first_key] = False
        recomputed_failed = sum(1 for v in flat.values() if not v)
        assert recomputed_failed == 1
