"""Structural tests for the categorical spec generators and the last dead
corners of the ``formal.advanced`` package.

Three groups of findings are covered here (audit 2026-07-26):

- **TEST-13** -- ``generate_categorical_nusmv_spec``,
  ``generate_categorical_promela_spec`` and ``generate_categorical_tla_spec``
  were never called by any test, so a syntax error introduced into any of the
  three multi-hundred-line templates would have shipped undetected.  Each
  generator is now checked against structural invariants of its target
  language, and each structural validator is itself proved capable of
  rejecting (a mutated spec must fail the same validator).  Where a real
  model checker would be required to say more, the test is *skipped* with an
  explicit reason rather than asserting something vacuously true.
- **TEST-13 (parsers)** -- the fail-closed behaviour of ``parse_nusmv_result``
  and ``parse_spin_result``.
- Residual uncovered surface in ``formal.advanced``:
  ``DefenseProfunctor.compose``/``apply_get``/``apply_put``,
  ``EnrichedHom.value``, ``BeliefLens.modify``, ``DetectionBound``'s dunders
  and ``DefenseLattice.add``.

NO MOCKS: every object here is a real instance and every spec is the real
generator output.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Set

import pytest

from formal.advanced.enriched import EnrichedHom
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
    CognitiveFunctor,
    DefenseLattice,
    DefenseMonad,
    DefenseOperad,
    DefenseProfunctor,
    DetectionBound,
    KanExtension,
    OperadTree,
    generate_test_states,
    make_test_morphism,
    series_operad_op,
)
from formal.nusmv_spec import (
    generate_categorical_nusmv_spec,
    generate_nusmv_spec,
    parse_nusmv_result,
)
from formal.spin_spec import (
    generate_categorical_promela_spec,
    generate_promela_spec,
    parse_spin_result,
)
from formal.tla_spec import (
    generate_categorical_tla_spec,
    generate_tla_spec,
    parse_tla_result,
)

#: Wall-clock ceiling for an opportunistic model-checker invocation.
CHECKER_TIMEOUT_S = 60


def _const(score: float, detected: bool, name: str) -> DefenseMorphism:
    """A morphism with a fixed score and detection flag, independent of state."""

    def _fn(state: CognitiveState) -> DefenseResult:
        return DefenseResult(
            detected=detected, score=score, module_name=name, details={}, latency_ms=0.0
        )

    return DefenseMorphism(fn=_fn, name=name, identity=False)


# ---------------------------------------------------------------------------
# Structural validators.  Each is exercised on real generator output *and* on
# a deliberately mutated spec, so none of them can be vacuously satisfied.
# ---------------------------------------------------------------------------


def _strip_nusmv_comments(spec: str) -> str:
    return "\n".join(line.split("--")[0] for line in spec.splitlines())


def _nusmv_declared_vars(spec: str) -> Set[str]:
    body = _strip_nusmv_comments(spec)
    var_block = body.split("VAR", 1)[1].split("ASSIGN", 1)[0]
    return set(re.findall(r"^\s*(\w+)\s*:", var_block, re.M))


def _nusmv_assigned(spec: str, keyword: str) -> Set[str]:
    body = _strip_nusmv_comments(spec)
    return set(re.findall(rf"{keyword}\((\w+)\)", body))


def _tla_undefined_theorem_operators(spec: str) -> Set[str]:
    """Operator names a ``THEOREM`` asserts about but the module never defines."""
    defined = set(re.findall(r"^(\w+)\s*==", spec, re.M))
    referenced = set(re.findall(r"^THEOREM\s+Spec\s*=>\s*\[?\]?(\w+)", spec, re.M))
    return referenced - defined


def _brace_delta(text: str) -> int:
    return text.count("{") - text.count("}")


# ---------------------------------------------------------------------------
# NuSMV categorical spec
# ---------------------------------------------------------------------------


class TestCategoricalNuSMVSpec:
    def setup_method(self):
        self.spec = generate_categorical_nusmv_spec()

    def test_has_a_main_module_and_the_two_required_sections(self):
        assert "MODULE main" in self.spec
        assert re.search(r"^VAR$", self.spec, re.M)
        assert re.search(r"^ASSIGN$", self.spec, re.M)
        assert self.spec.endswith("\n")

    def test_declares_the_expected_categorical_state(self):
        declared = _nusmv_declared_vars(self.spec)
        for name in (
            "rate_f",
            "rate_g",
            "rate_h",
            "rate_id",
            "series_fg",
            "parallel_fg",
            "meet_fg",
            "join_fg",
            "assoc_ok",
        ):
            assert name in declared, f"{name} missing from VAR block"

    def test_every_declared_variable_is_initialised_and_has_a_transition(self):
        """A single-state model: every variable needs both init() and next()."""
        declared = _nusmv_declared_vars(self.spec)
        assert declared, "VAR block parsed as empty -- the validator itself is broken"
        assert declared - _nusmv_assigned(self.spec, "init") == set()
        assert declared - _nusmv_assigned(self.spec, "next") == set()

    def test_positive_control_a_missing_init_is_detected(self):
        """The init/next validator can fail: drop one init and it must notice."""
        mutated = self.spec.replace("  init(meet_fg) := 50;", "")
        assert "meet_fg" in _nusmv_declared_vars(mutated)
        assert _nusmv_declared_vars(mutated) - _nusmv_assigned(mutated, "init") == {"meet_fg"}

    def test_declares_ctl_properties_covering_the_categorical_laws(self):
        ctlspecs = re.findall(r"^CTLSPEC (.+)$", self.spec, re.M)
        assert len(ctlspecs) == 10
        joined = " ".join(ctlspecs)
        for flag in ("assoc_ok", "left_unitor_ok", "right_unitor_ok", "symmetry_ok"):
            assert flag in joined

    def test_every_ctlspec_references_a_declared_variable(self):
        declared = _nusmv_declared_vars(self.spec)
        for ctlspec in re.findall(r"^CTLSPEC (.+)$", self.spec, re.M):
            names = set(re.findall(r"[A-Za-z_]\w*", ctlspec)) - {"AG", "AF", "EF", "TRUE", "FALSE"}
            assert names & declared, f"CTLSPEC mentions no model variable: {ctlspec}"

    def test_agent_and_categorical_specs_are_distinct_models(self):
        assert generate_nusmv_spec() != self.spec

    @pytest.mark.skipif(
        shutil.which("NuSMV") is None and shutil.which("nusmv") is None,
        reason="NuSMV binary not on PATH; structural checks only, no model-checking evidence",
    )
    def test_nusmv_accepts_the_generated_model(self, tmp_path):
        binary = shutil.which("NuSMV") or shutil.which("nusmv")
        assert binary is not None
        path = tmp_path / "categorical.smv"
        path.write_text(self.spec, encoding="utf-8")
        proc = subprocess.run(
            [binary, str(path)],
            capture_output=True,
            text=True,
            timeout=CHECKER_TIMEOUT_S,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        verdicts = parse_nusmv_result(proc.stdout)
        assert verdicts, "NuSMV produced no parseable property verdicts"
        assert all(verdicts.values()), verdicts


# ---------------------------------------------------------------------------
# SPIN / Promela categorical spec
# ---------------------------------------------------------------------------


class TestCategoricalPromelaSpec:
    def setup_method(self):
        self.spec = generate_categorical_promela_spec()

    def test_declares_a_proctype_and_an_init_block(self):
        assert "proctype CheckCategoryLaws()" in self.spec
        assert re.search(r"^init \{$", self.spec, re.M)
        assert self.spec.endswith("\n")

    def test_braces_and_parentheses_balance(self):
        assert _brace_delta(self.spec) == 0
        assert self.spec.count("(") == self.spec.count(")")

    def test_positive_control_brace_validator_can_fail(self):
        assert _brace_delta(self.spec + "{") == 1

    def test_every_if_has_a_matching_fi(self):
        assert len(re.findall(r"^\s*if\b", self.spec, re.M)) == len(re.findall(r"fi;", self.spec))

    def test_declares_the_five_categorical_ltl_properties(self):
        names = re.findall(r"^ltl (\w+) \{", self.spec, re.M)
        assert names == [
            "cat_associativity",
            "left_unitor",
            "right_unitor",
            "enriched_triangle",
            "laws_checked",
        ]

    def test_every_ltl_body_references_a_declared_violation_flag(self):
        flags = set(re.findall(r"^bool (\w+) = false;", self.spec, re.M))
        assert flags, "no violation flags declared -- the validator itself is broken"
        for body in re.findall(r"^ltl \w+ \{(.+)\}$", self.spec, re.M):
            assert set(re.findall(r"[A-Za-z_]\w*", body)) & flags, body

    def test_agent_and_categorical_specs_are_distinct_models(self):
        assert generate_promela_spec() != self.spec

    @pytest.mark.skipif(
        shutil.which("spin") is None,
        reason="spin binary not on PATH; structural checks only, no model-checking evidence",
    )
    def test_spin_parses_the_generated_model(self, tmp_path):
        binary = shutil.which("spin")
        assert binary is not None
        path = tmp_path / "categorical.pml"
        path.write_text(self.spec, encoding="utf-8")
        proc = subprocess.run(
            [binary, "-a", str(path)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=CHECKER_TIMEOUT_S,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "error" not in proc.stderr.lower(), proc.stderr


# ---------------------------------------------------------------------------
# TLA+ categorical spec
# ---------------------------------------------------------------------------


class TestCategoricalTLASpec:
    def setup_method(self):
        self.spec = generate_categorical_tla_spec()

    def test_module_header_and_footer_delimiters(self):
        lines = self.spec.strip().splitlines()
        assert re.match(r"^---- MODULE \w+ ----$", lines[0])
        assert lines[-1] == "===="
        assert self.spec.endswith("\n")

    def test_declares_constants_variables_init_next_and_spec(self):
        for section in ("CONSTANTS", "VARIABLES", "Init ==", "Next ==", "Spec == Init"):
            assert section in self.spec, f"missing {section}"

    def test_every_theorem_names_an_operator_the_module_defines(self):
        referenced = re.findall(r"^THEOREM\s+Spec\s*=>\s*\[?\]?(\w+)", self.spec, re.M)
        assert len(referenced) == 9
        assert _tla_undefined_theorem_operators(self.spec) == set()

    def test_positive_control_an_undefined_theorem_operator_is_detected(self):
        """The validator can fail: delete a definition and it must be reported."""
        mutated = self.spec.replace("HexagonIdentity ==", "HexagonIdentityRenamed ==")
        assert _tla_undefined_theorem_operators(mutated) == {"HexagonIdentity"}

    def test_every_variable_is_listed_in_the_vars_tuple(self):
        var_block = self.spec.split("VARIABLES", 1)[1].split("vars ==", 1)[0]
        declared = {
            line.split("\\*")[0].strip().rstrip(",")
            for line in var_block.strip().splitlines()
            if line.strip() and not line.strip().startswith("\\*")
        }
        tuple_line = re.search(r"^vars == <<(.+)>>$", self.spec, re.M)
        assert tuple_line is not None
        listed = {name.strip() for name in tuple_line.group(1).split(",")}
        assert declared == listed

    def test_agent_and_categorical_specs_are_distinct_models(self):
        assert generate_tla_spec() != self.spec
        assert _tla_undefined_theorem_operators(generate_tla_spec()) == set()

    @pytest.mark.skipif(
        shutil.which("tlc") is None,
        reason="tlc binary not on PATH; structural checks only, no model-checking evidence",
    )
    def test_tlc_accepts_the_generated_module(self, tmp_path):
        binary = shutil.which("tlc")
        assert binary is not None
        path = tmp_path / "DefenseCategoryTheory.tla"
        path.write_text(self.spec, encoding="utf-8")
        proc = subprocess.run(
            [binary, str(path)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=CHECKER_TIMEOUT_S,
            check=False,
        )
        verdicts = parse_tla_result(proc.stdout)
        assert verdicts, "TLC produced no parseable verdicts"
        assert all(verdicts.values()), verdicts


# ---------------------------------------------------------------------------
# Model-checker output parsers: fail-closed behaviour
# ---------------------------------------------------------------------------


class TestParserFailClosed:
    def test_nusmv_verdictless_specification_line_is_not_a_pass(self):
        """An unparseable verdict is not evidence that the property holds."""
        results = parse_nusmv_result("-- specification AG (assoc_ok)\n")
        assert results == {"-- specification AG (assoc_ok)": False}

    def test_nusmv_positive_control_a_real_verdict_still_parses(self):
        results = parse_nusmv_result(
            "-- specification AG (assoc_ok) is true\n"
            "-- specification AG (symmetry_ok) is false\n"
        )
        assert list(results.values()) == [True, False]

    def test_nusmv_ctlspec_marker_is_recognised(self):
        line = "-- CTLSPEC AG (rate_id = 0) is true"
        assert parse_nusmv_result(line + "\n") == {line: True}

    def test_spin_unparseable_error_count_is_recorded_as_a_failure(self):
        """Previously this left ``errors`` at 0 and reported the property as passing."""
        assert parse_spin_result("errors: many\n") == {"property_0": False}

    def test_spin_positive_control_zero_errors_still_passes(self):
        assert parse_spin_result("errors: 0\n") == {"property_0": True}
        assert parse_spin_result("errors: 2\n") == {"property_0": False}

    def test_spin_bare_errors_keyword_without_a_count_is_a_failure(self):
        assert parse_spin_result("errors\n") == {}
        assert parse_spin_result("errors:\n") == {"property_0": False}

    def test_tla_violation_and_completion_lines(self):
        assert parse_tla_result("Invariant TrustBounded is violated.")["Invariant TrustBounded"] \
            is False
        assert parse_tla_result("Model checking completed. No error has been found.") == {
            "overall": True
        }
        assert parse_tla_result("Error: 1 state found.") == {"overall": False}


# ---------------------------------------------------------------------------
# DefenseProfunctor: the optic itself (lenses.py 94-121, previously uncovered)
# ---------------------------------------------------------------------------


def _scale_profunctor(factor: float, tag: str) -> DefenseProfunctor:
    """A profunctor that scales ``trust`` on read and records the score on write."""

    def _get(state: CognitiveState) -> CognitiveState:
        return {**state, "trust": state.get("trust", 0.0) * factor}

    def _put(state: CognitiveState, result: DefenseResult) -> CognitiveState:
        return {**state, tag: result.score}

    return DefenseProfunctor(get_fn=_get, put_fn=_put)


class TestDefenseProfunctor:
    def setup_method(self):
        self.state: CognitiveState = {"trust": 0.4, "consensus": 0.2}
        self.result = DefenseResult(
            detected=True, score=0.8, module_name="probe", details={"k": 1}, latency_ms=2.0
        )

    def test_apply_get_and_apply_put_delegate_to_the_supplied_functions(self):
        prof = _scale_profunctor(0.5, "outer")
        assert prof.apply_get(self.state)["trust"] == pytest.approx(0.2)
        assert prof.apply_put(self.state, self.result)["outer"] == pytest.approx(0.8)

    def test_compose_threads_get_through_both_optics(self):
        outer = _scale_profunctor(0.5, "outer")
        inner = _scale_profunctor(0.25, "inner")
        composed = outer.compose(inner)
        # inner_get(outer_get(state)): 0.4 -> 0.2 -> 0.05
        assert composed.apply_get(self.state)["trust"] == pytest.approx(0.05)

    def test_compose_put_applies_the_outer_put_and_carries_the_intermediate(self):
        outer = _scale_profunctor(0.5, "outer")
        inner = _scale_profunctor(0.25, "inner")
        composed = outer.compose(inner)
        out = composed.apply_put(self.state, self.result)
        # The outer put fired (its tag is present) ...
        assert out["outer"] == pytest.approx(0.8)
        # ... and it is the *original* state that was written into, not the view.
        assert out["trust"] == pytest.approx(0.4)

    def test_compose_is_not_the_identity_on_either_component(self):
        """Guards against a compose() that silently returned ``self``."""
        outer = _scale_profunctor(0.5, "outer")
        inner = _scale_profunctor(0.25, "inner")
        composed = outer.compose(inner)
        assert composed is not outer and composed is not inner
        assert composed.apply_get(self.state)["trust"] != pytest.approx(
            outer.apply_get(self.state)["trust"]
        )
        assert composed.apply_get(self.state)["trust"] != pytest.approx(
            inner.apply_get(self.state)["trust"]
        )

    def test_composition_is_associative_on_get(self):
        a = _scale_profunctor(0.5, "a")
        b = _scale_profunctor(0.25, "b")
        c = _scale_profunctor(0.1, "c")
        left = a.compose(b).compose(c).apply_get(self.state)["trust"]
        right = a.compose(b.compose(c)).apply_get(self.state)["trust"]
        assert left == pytest.approx(right)


# ---------------------------------------------------------------------------
# Remaining uncovered surface in formal.advanced
# ---------------------------------------------------------------------------


class TestEnrichedHom:
    """``EnrichedHom.value`` was reachable from nothing in the test suite."""

    def setup_method(self):
        self.states = generate_test_states(n=8, seed=13)
        self.f = make_test_morphism(0.7, "f")
        self.g = make_test_morphism(0.5, "g")

    def test_value_is_the_absolute_mean_rate_difference(self):
        hom = EnrichedHom(morphism_f=self.f, morphism_g=self.g)
        expected = abs(
            sum(self.f(s).score for s in self.states) / len(self.states)
            - sum(self.g(s).score for s in self.states) / len(self.states)
        )
        assert hom.value(self.states) == pytest.approx(expected, abs=1e-12)

    def test_value_is_symmetric_and_vanishes_on_the_diagonal(self):
        assert EnrichedHom(morphism_f=self.f, morphism_g=self.f).value(self.states) == 0.0
        forward = EnrichedHom(morphism_f=self.f, morphism_g=self.g).value(self.states)
        backward = EnrichedHom(morphism_f=self.g, morphism_g=self.f).value(self.states)
        assert forward == pytest.approx(backward, abs=1e-12)
        assert forward > 0.0, "distinct morphisms must have a non-zero hom-value"

    def test_repr_names_both_morphisms(self):
        assert repr(EnrichedHom(morphism_f=self.f, morphism_g=self.g)) == "EnrichedHom('f', 'g')"


class TestBeliefLensSurface:
    def test_modify_applies_a_function_to_the_focused_belief(self):
        lens: BeliefLens = BeliefLens(focus="trust")
        state = {"trust": 0.25, "consensus": 0.5}
        modified = lens.modify(state, lambda v: v + 0.5)
        assert modified["trust"] == pytest.approx(0.75)
        assert modified["consensus"] == pytest.approx(0.5)
        assert state["trust"] == pytest.approx(0.25), "modify must not mutate"

    def test_get_returns_the_default_for_an_absent_key(self):
        assert BeliefLens(focus="absent").get({"trust": 0.5}) == 0.0

    def test_compose_returns_a_composed_lens_that_records_both_components(self):
        outer: BeliefLens = BeliefLens(focus="consensus")
        inner: BeliefLens = BeliefLens(focus="trust")
        composed = outer.compose(inner)
        assert composed.outer is outer
        assert composed.inner is inner

    def test_repr(self):
        assert repr(BeliefLens(focus="trust")) == "BeliefLens(focus='trust')"


class TestDetectionBoundSurface:
    def test_rate_outside_the_unit_interval_is_rejected(self):
        with pytest.raises(ValueError, match=r"must be in \[0,1\]"):
            DetectionBound(1.5)
        with pytest.raises(ValueError, match=r"must be in \[0,1\]"):
            DetectionBound(-0.01)

    def test_positive_control_boundary_rates_are_accepted(self):
        assert DetectionBound(0.0).rate == 0.0
        assert DetectionBound(1.0).rate == 1.0

    def test_equality_is_tolerant_and_type_aware(self):
        assert DetectionBound(0.3) == DetectionBound(0.3 + 1e-15)
        assert DetectionBound(0.3) != DetectionBound(0.4)
        assert (DetectionBound(0.3) == 0.3) is False

    def test_hash_agrees_with_equality(self):
        assert hash(DetectionBound(0.3)) == hash(DetectionBound(0.3))
        assert len({DetectionBound(0.3), DetectionBound(0.3), DetectionBound(0.7)}) == 2

    def test_repr_shows_rate_and_name(self):
        assert repr(BOTTOM) == "DetectionBound(0.0000, name='⊥')"
        assert repr(TOP) == "DetectionBound(1.0000, name='⊤')"

    def test_lattice_add_appends_an_element(self):
        lattice = DefenseLattice()
        assert lattice.elements == []
        lattice.add(DetectionBound(0.5, name="mid"))
        assert [e.name for e in lattice.elements] == ["mid"]
        assert all(lattice.verify_all().values())


class TestOperadTreeSurface:
    def test_leaf_repr_and_is_leaf(self):
        f = make_test_morphism(0.7, "f")
        leaf = OperadTree(leaf_morphism=f)
        assert leaf.is_leaf() is True
        assert repr(leaf).startswith("Leaf(")

    def test_internal_node_repr_names_the_operation(self):
        f = make_test_morphism(0.7, "f")
        g = make_test_morphism(0.5, "g")
        tree = OperadTree(
            operation=series_operad_op(2),
            children=[OperadTree(leaf_morphism=f), OperadTree(leaf_morphism=g)],
        )
        assert tree.is_leaf() is False
        text = repr(tree)
        assert "OperadTree(" in text and "series_2" in text and "Leaf(" in text

    def test_nested_tree_evaluates_bottom_up(self):
        states = generate_test_states(n=5, seed=21)
        f = make_test_morphism(0.7, "f")
        ident: DefenseMorphism = identity_morphism()
        inner = OperadTree(
            operation=series_operad_op(2),
            children=[OperadTree(leaf_morphism=f), OperadTree(leaf_morphism=ident)],
        )
        outer = OperadTree(
            operation=series_operad_op(2),
            children=[inner, OperadTree(leaf_morphism=ident)],
        )
        # Grafting identities never changes the score.
        assert [outer.evaluate()(s).score for s in states] == pytest.approx(
            [f(s).score for s in states], abs=1e-12
        )

    def test_build_series_and_build_parallel_disagree_on_ordered_arms(self):
        """Series short-circuits on detection; parallel does not."""
        states = generate_test_states(n=5, seed=22)
        operad = DefenseOperad()
        detecting_low = _const(0.6, True, "low")
        silent_high = _const(0.9, False, "high")
        series = operad.build_series([detecting_low, silent_high])
        parallel = operad.build_parallel([detecting_low, silent_high])
        assert [series(s).score for s in states] == pytest.approx([0.6] * len(states))
        assert [parallel(s).score for s in states] == pytest.approx([0.9] * len(states))


class TestMonadJoin:
    """``DefenseMonad.mu`` -- the join -- had no caller in the test suite."""

    def test_mu_runs_the_inner_morphism_first(self):
        """``mu(outer, inner) == compose_morphisms(inner, outer)``.

        Both arms detect, and ``compose_morphisms`` short-circuits on the
        first detection, so the resulting score identifies which morphism ran
        first.  Swapping the arguments must swap the score -- a ``mu`` that
        ignored its argument order would fail this.
        """
        states = generate_test_states(n=5, seed=23)
        monad = DefenseMonad()
        loud = _const(0.8, True, "loud")
        quiet = _const(0.2, True, "quiet")

        assert [monad.mu(loud, quiet)(s).score for s in states] == pytest.approx([0.2] * 5)
        assert [monad.mu(quiet, loud)(s).score for s in states] == pytest.approx([0.8] * 5)

    def test_eta_is_the_non_detecting_zero_score_computation(self):
        result = DefenseMonad().eta({"trust": 0.4, "consensus": 0.6})
        assert result.detected is False
        assert result.score == 0.0
        assert sorted(result.details["state_keys"]) == ["consensus", "trust"]


class TestCognitiveFunctor:
    def test_fmap_applies_the_state_transformation(self):
        functor = CognitiveFunctor()
        state: CognitiveState = {"trust": 0.4}
        assert functor.fmap(lambda s: {**s, "trust": s["trust"] * 2}, state) == {"trust": 0.8}
        assert state == {"trust": 0.4}, "fmap must not mutate the argument"


class _NoRanKan(KanExtension):
    """A Kan extension whose ``Ran`` publishes no targets at all."""

    def right_kan(self):
        return {}


class _NoLanKan(KanExtension):
    """A Kan extension whose ``Lan`` publishes no targets at all."""

    def left_kan(self):
        return {}


class TestKanMissingTargets:
    """The two defensive ``if tgt_name in lan/ran`` guards in the verifier."""

    def setup_method(self):
        self.states = generate_test_states(n=6, seed=24)
        self.source = AgentArchitecture(name="src")
        self.source.add_morphism("fw", make_test_morphism(0.7, "fw"), rate=0.7)
        self.target = AgentArchitecture(name="tgt")
        self.target.add_morphism("security", make_test_morphism(0.3, "sec"), rate=0.3)

    def test_absent_ran_target_emits_no_ran_flag(self):
        kan = _NoRanKan(
            source=self.source, target=self.target, functor_map={"fw": "security"}
        )
        assert kan.verify_kan_adjunction(self.states) == {"lan_dominates_fw": True}

    def test_absent_lan_target_emits_no_lan_flag(self):
        kan = _NoLanKan(
            source=self.source, target=self.target, functor_map={"fw": "security"}
        )
        assert kan.verify_kan_adjunction(self.states) == {"ran_dominated_by_fw": True}
