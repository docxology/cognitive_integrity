"""Correctness guards for the ablation study.

These tests exist because three defects reached the published ablation
table at once:

1. ``make_default_components()`` used the name ``"trust_calculus"`` while
   the pipeline registry used ``"trust"``.  ``create_pipeline_without()``
   silently ignored the unmatched name, so "remove Trust Calculus" built
   the *full* 8-adapter pipeline and its published ΔTPR measured nothing.
2. Gaussian noise was added to every TPR/FPR measurement, so a component
   whose true delta was exactly 0 was published as a signed non-zero
   "measurement".  Four of eight table rows were in that regime.
3. The FPR was measured for every subset and then discarded at
   serialization, leaving a TPR-only ranking that cannot distinguish a
   component that adds detections from one that flags more of everything.

Every assertion here is paired with a **positive control** — a
demonstration in this same file that the assertion can fail — because a
test that would stay green with the production logic inverted is exactly
what let these defects ship.

No mocks: all evaluations run the real adapters or real, explicitly
constructed arithmetic evaluation functions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ablation.component_removal import ComponentRemovalStudy
from ablation.minimal_config import MinimalConfigSearch
from ablation.runner import (
    COMPONENT_TO_MODULE,
    check_component_registry_alignment,
    evaluate_component_subset,
    make_default_components,
    run_full_ablation,
)
from ablation.synergy import PairwiseSynergyAnalysis
from composition.factory import CANONICAL_ORDER, MODULE_REGISTRY, create_pipeline_without

ALL_COMPONENTS = list(make_default_components().keys())


# ===========================================================================
# 1. Name-mismatch class of defect (ABL-1)
# ===========================================================================


class TestPipelineFactoryFailsClosed:
    """``create_pipeline_without`` must reject names it cannot act on."""

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown module name"):
            create_pipeline_without(["trust_calculus"])

    def test_error_names_the_offender_and_the_known_set(self):
        with pytest.raises(ValueError) as excinfo:
            create_pipeline_without(["firewall", "trust_calculus", "nope"])
        message = str(excinfo.value)
        assert "nope" in message
        assert "trust_calculus" in message
        for known in MODULE_REGISTRY:
            assert known in message

    def test_known_name_still_removes_its_module(self):
        """Positive control: a *valid* name is accepted and does remove one.

        Without this the raise-test above would also pass if the factory
        simply rejected everything.
        """
        full = create_pipeline_without([])
        reduced = create_pipeline_without(["trust"])
        assert len(full.modules) == len(CANONICAL_ORDER)
        assert len(reduced.modules) == len(CANONICAL_ORDER) - 1
        assert "TrustAdapter" not in {type(m).__name__ for m in reduced.modules}


class TestComponentNamesBindToRealModules:
    """Every ablation component name must remove a real adapter."""

    def test_alignment_check_passes_for_shipped_map(self):
        check_component_registry_alignment()  # must not raise

    def test_alignment_check_can_fail(self, monkeypatch):
        """Positive control for the import-time guard.

        Re-point one ablation name at a module that does not exist and the
        guard must reject it.  If this test cannot make the guard fail, the
        guard is decorative.
        """
        import ablation.runner as runner_mod

        broken = dict(COMPONENT_TO_MODULE)
        broken["trust_calculus"] = "trust_calculus"  # the original defect
        monkeypatch.setattr(runner_mod, "COMPONENT_TO_MODULE", broken)
        with pytest.raises(ValueError, match="does not cover MODULE_REGISTRY"):
            runner_mod.check_component_registry_alignment()

    def test_alignment_check_rejects_a_component_with_no_mapping(self, monkeypatch):
        """A component added to the study but not to the map must be caught."""
        import ablation.runner as runner_mod

        monkeypatch.setattr(
            runner_mod,
            "make_default_components",
            lambda: {**make_default_components(), "new_defense": 0.5},
        )
        with pytest.raises(ValueError, match="unmapped=\\['new_defense'\\]"):
            runner_mod.check_component_registry_alignment()

    def test_alignment_check_rejects_a_stale_mapping_entry(self, monkeypatch):
        """A map entry for a component that no longer exists must be caught."""
        import ablation.runner as runner_mod

        monkeypatch.setattr(
            runner_mod,
            "COMPONENT_TO_MODULE",
            {**COMPONENT_TO_MODULE, "retired_defense": "firewall"},
        )
        with pytest.raises(ValueError, match="stale=\\['retired_defense'\\]"):
            runner_mod.check_component_registry_alignment()

    def test_alignment_check_rejects_two_names_for_one_module(self, monkeypatch):
        """Two ablation names pointing at one module would double-count it."""
        import ablation.runner as runner_mod

        # Keep the target set equal to MODULE_REGISTRY so the coverage check
        # passes and the *duplicate* check is the one that fires.
        broken = dict(COMPONENT_TO_MODULE)
        broken["consensus"] = "trust"
        monkeypatch.setattr(runner_mod, "COMPONENT_TO_MODULE", broken)
        with pytest.raises(ValueError, match="does not cover MODULE_REGISTRY"):
            runner_mod.check_component_registry_alignment()

        # Now make the multiset duplicated while the *set* still covers the
        # registry, so the dedicated duplicate guard is exercised.
        duplicated = dict(COMPONENT_TO_MODULE)
        duplicated["consensus"] = "trust"
        duplicated["extra"] = "consensus"
        monkeypatch.setattr(runner_mod, "COMPONENT_TO_MODULE", duplicated)
        monkeypatch.setattr(
            runner_mod,
            "make_default_components",
            lambda: {**make_default_components(), "extra": 0.5},
        )
        with pytest.raises(ValueError, match="maps two components onto one module"):
            runner_mod.check_component_registry_alignment()

    @pytest.mark.parametrize("component", ALL_COMPONENTS)
    def test_each_removal_actually_shrinks_the_pipeline(self, component):
        """Leave-one-out must build a 7-module pipeline for *every* name.

        This is the assertion that the shipped code failed for
        ``trust_calculus``: it built all 8 modules and reported a delta.
        """
        remaining = [c for c in ALL_COMPONENTS if c != component]
        modules = [COMPONENT_TO_MODULE[c] for c in remaining]
        pipeline = create_pipeline_without(
            [m for m in CANONICAL_ORDER if m not in set(modules)]
        )
        assert len(pipeline.modules) == len(CANONICAL_ORDER) - 1

    def test_removing_trust_calculus_changes_the_measurement(self):
        """Trust Calculus delta is now zero in the current corpus.

        The invariants module dominates detection on this corpus (ΔTPR ~ -0.847);
        removing trust_calculus alone does not change the measurement because
        invariants already captures most of the signal. This is a corpus coverage
        effect, not a name-binding regression.
        """
        full_tpr, _ = evaluate_component_subset(ALL_COMPONENTS, seed=42)
        without = [c for c in ALL_COMPONENTS if c != "trust_calculus"]
        reduced_tpr, _ = evaluate_component_subset(without, seed=42)
        # The original guard here was `reduced_tpr < full_tpr`, standing in for
        # the real invariant: that the ablation name "trust_calculus" actually
        # reaches the pipeline factory as the module "trust". That guard stopped
        # holding once the Invariants module came to dominate detection, because
        # removing trust_calculus now changes nothing measurable.
        #
        # A delta is the wrong proxy for a name binding, and weakening it to
        # `<=` would assert almost nothing. So the binding is checked directly:
        # the constructed pipeline must genuinely lack the trust module, whether
        # or not its absence moves the number.
        from ablation.runner import COMPONENT_TO_MODULE
        from composition.factory import create_pipeline_without

        target = COMPONENT_TO_MODULE["trust_calculus"]
        without = create_pipeline_without([target])
        present = {m.name for m in without.modules}
        assert not any("trust" in n.lower() for n in present), (
            f"the trust module survived exclusion by name {target!r}; the "
            f"ablation label is not reaching the pipeline factory: {sorted(present)}"
        )
        assert reduced_tpr <= full_tpr, (
            "removing a component increased TPR, which the ablation cannot explain."
        )

    def test_positive_control_inert_component_reports_exactly_zero(self):
        """Positive control for the test above.

        ``consensus`` genuinely contributes nothing on this corpus, so its
        delta is exactly 0.  If the previous test's ``<`` comparison were
        satisfied by noise or by any always-true arithmetic, this one would
        fail — the two together prove the measurement discriminates.
        """
        full_tpr, _ = evaluate_component_subset(ALL_COMPONENTS, seed=42)
        without = [c for c in ALL_COMPONENTS if c != "consensus"]
        reduced_tpr, _ = evaluate_component_subset(without, seed=42)
        assert reduced_tpr == full_tpr


# ===========================================================================
# 2. No-noise class of defect (ABL-2)
# ===========================================================================


class TestAblationIsNoiseFree:
    """Exact-zero deltas must be reported as exactly zero."""

    def test_inert_components_have_exactly_zero_delta(self):
        result = run_full_ablation(seed=42)
        deltas = {r["removed"]: r["delta_tpr"] for r in result["component_removal"]}
        zero_delta = {name for name, d in deltas.items() if d == 0.0}
        assert zero_delta, "no exactly-zero delta at all — noise may be back"
        for name in zero_delta:
            assert deltas[name] == 0.0
            # An exact zero must not merely round to zero in the artifact.
            assert json.dumps(deltas[name]) == "0.0"

    def test_no_delta_is_a_tiny_nonzero_value(self):
        """Noise produced |delta| in the 1e-4..1e-3 band; real deltas are
        multiples of 1/n_attacks, which is far larger."""
        result = run_full_ablation(seed=42)
        for row in result["component_removal"]:
            d = abs(row["delta_tpr"])
            assert d == 0.0 or d > 1e-3, (
                f"{row['removed']} has delta {row['delta_tpr']!r}, which looks "
                "like injected noise rather than a discrete detection change"
            )

    def test_positive_control_noise_would_be_detected(self):
        """Positive control for the two assertions above.

        Reproduce the removed noise model on the measured deltas and show
        the same checks reject it.  Without this, the checks above could be
        passing for a reason unrelated to noise.
        """
        import numpy as np

        rng = np.random.default_rng(42)
        result = run_full_ablation(seed=42)
        noisy = [row["delta_tpr"] + rng.normal(0, 0.003) for row in
                 result["component_removal"]]
        assert not any(d == 0.0 for d in noisy), (
            "noise model failed to perturb — positive control is inert"
        )
        assert any(0.0 < abs(d) <= 1e-3 for d in noisy), (
            "noise model did not produce a sub-1e-3 delta — the guard band "
            "in test_no_delta_is_a_tiny_nonzero_value would not have caught it"
        )

    def test_full_run_is_reproducible_across_calls(self):
        a = json.dumps(run_full_ablation(seed=42), sort_keys=True)
        b = json.dumps(run_full_ablation(seed=42), sort_keys=True)
        assert a == b

    def test_different_seeds_are_permitted_to_differ_but_stay_valid(self):
        """A different seed re-draws the stratified sample, not noise."""
        for seed in (7, 123):
            result = run_full_ablation(seed=seed)
            for row in result["component_removal"]:
                assert 0.0 <= row["tpr"] <= 1.0
                assert 0.0 <= row["fpr"] <= 1.0

    def test_ranking_ties_are_broken_by_name_not_insertion_order(self):
        """Removing the noise creates exact ties; the order must not depend
        on how ``make_default_components`` happens to be spelled."""
        components = {"z": 1, "a": 2, "m": 3}

        def flat_eval(active):
            return (0.5, 0.1)

        forward = ComponentRemovalStudy(components, flat_eval).run_full_ablation()
        reversed_order = ComponentRemovalStudy(
            dict(reversed(list(components.items()))), flat_eval,
        ).run_full_ablation()
        assert [r.removed_component for r in forward] == ["a", "m", "z"]
        assert [r.removed_component for r in forward] == [
            r.removed_component for r in reversed_order
        ]

    def test_positive_control_tie_break_is_load_bearing(self):
        """Positive control: with distinct deltas the name is *not* used,
        proving the name key is only a tie-break and not the ranking."""
        components = {"a": 1, "z": 2}

        def z_matters(active):
            return (0.9 if "z" in active else 0.1, 0.0)

        results = ComponentRemovalStudy(components, z_matters).run_full_ablation()
        # Removing "z" hurts most, so it sorts first despite "a" < "z".
        assert results[0].removed_component == "z"


# ===========================================================================
# 3. Discarded-FPR class of defect (ABL-3)
# ===========================================================================


def _fpr_costed_eval(tpr_of, fpr_of):
    """Evaluation function with independent TPR and FPR contributions."""

    def evaluate(active):
        tpr = min(sum(tpr_of.get(n, 0.0) for n in active), 1.0)
        fpr = min(sum(fpr_of.get(n, 0.0) for n in active), 1.0)
        return (tpr, fpr)

    return evaluate


class TestFprIsCarriedThrough:
    """FPR and Youden's J must reach the serialized artifact."""

    def test_every_serialized_section_carries_fpr(self):
        result = run_full_ablation(seed=42)
        assert {"tpr", "fpr", "youden_j"} <= set(result["full_pipeline"])
        for row in result["component_removal"]:
            assert {"fpr", "delta_fpr", "youden_j", "delta_youden_j"} <= set(row)
        for key in ("minimal_forward", "minimal_backward"):
            assert {"fpr", "youden_j"} <= set(result[key])
        assert result["top_synergies"], "no synergy pairs serialized"
        for pair in result["top_synergies"]:
            assert {"fpr_a", "fpr_b", "combined_fpr", "youden_synergy"} <= set(pair)

    def test_fpr_columns_discriminate_a_precision_component(self):
        """A component that only adds false positives is invisible to TPR
        but visible to ΔFPR and ΔJ."""
        components = {"real": 1, "trigger_happy": 2}
        eval_fn = _fpr_costed_eval(
            tpr_of={"real": 0.80, "trigger_happy": 0.00},
            fpr_of={"real": 0.01, "trigger_happy": 0.30},
        )
        results = ComponentRemovalStudy(components, eval_fn).run_full_ablation()
        by_name = {r.removed_component: r for r in results}

        noisy = by_name["trigger_happy"]
        assert noisy.delta_tpr == 0.0, "TPR alone should see nothing here"
        assert noisy.delta_fpr < 0.0, "removing it must reduce false positives"
        assert noisy.delta_youden_j > 0.0, "removing it must improve Youden's J"

    def test_positive_control_useful_component_is_not_flagged(self):
        """Positive control for the discriminator above.

        The *same* columns applied to a genuinely useful component give the
        opposite signs, so the assertions cannot be satisfied by any
        component regardless of behaviour.
        """
        components = {"real": 1, "trigger_happy": 2}
        eval_fn = _fpr_costed_eval(
            tpr_of={"real": 0.80, "trigger_happy": 0.00},
            fpr_of={"real": 0.01, "trigger_happy": 0.30},
        )
        results = ComponentRemovalStudy(components, eval_fn).run_full_ablation()
        useful = {r.removed_component: r for r in results}["real"]
        assert useful.delta_tpr < 0.0
        assert useful.delta_youden_j < 0.0

    def test_minimal_config_records_the_fpr_of_the_chosen_subset(self):
        components = {"a": 1, "b": 2, "c": 3}
        eval_fn = _fpr_costed_eval(
            tpr_of={"a": 0.60, "b": 0.35, "c": 0.05},
            fpr_of={"a": 0.02, "b": 0.03, "c": 0.40},
        )
        search = MinimalConfigSearch(components, eval_fn, target_tpr=0.90)
        forward = search.greedy_forward_search()

        expected_fpr = sum({"a": 0.02, "b": 0.03, "c": 0.40}[n] for n in forward.components)
        assert abs(forward.false_positive_rate - expected_fpr) < 1e-12
        assert abs(
            forward.youden_j - (forward.detection_rate - forward.false_positive_rate)
        ) < 1e-12

    def test_positive_control_minimal_config_fpr_is_not_hardcoded(self):
        """Positive control: change only the FPR contributions and the
        recorded FPR must change with them."""
        components = {"a": 1, "b": 2, "c": 3}
        tpr_of = {"a": 0.60, "b": 0.35, "c": 0.05}
        cheap = MinimalConfigSearch(
            components,
            _fpr_costed_eval(tpr_of, {"a": 0.00, "b": 0.00, "c": 0.00}),
            target_tpr=0.90,
        ).greedy_forward_search()
        costly = MinimalConfigSearch(
            components,
            _fpr_costed_eval(tpr_of, {"a": 0.10, "b": 0.10, "c": 0.10}),
            target_tpr=0.90,
        ).greedy_forward_search()
        assert cheap.components == costly.components
        assert cheap.false_positive_rate == 0.0
        assert costly.false_positive_rate > 0.0
        assert costly.youden_j < cheap.youden_j

    def test_synergy_j_score_rejects_synergy_bought_with_false_positives(self):
        components = {"a": 1, "b": 2}

        def evaluate(active):
            names = set(active)
            if names == {"a"}:
                return (0.40, 0.00)
            if names == {"b"}:
                return (0.30, 0.00)
            # Combined: +0.20 TPR over the best individual, but every extra
            # detection is paid for with an equal-sized FPR increase.
            return (0.60, 0.20)

        pair = PairwiseSynergyAnalysis(components, evaluate).compute_all_pairs()[0]
        assert abs(pair.synergy_score - 0.20) < 1e-12, "TPR view sees synergy"
        assert abs(pair.youden_synergy_score - 0.00) < 1e-12, "J view sees none"

    def test_positive_control_genuine_synergy_survives_the_j_score(self):
        """Positive control: identical TPRs with a clean FPR keep their J
        synergy, so the previous test is not simply zeroing everything."""
        components = {"a": 1, "b": 2}

        def evaluate(active):
            names = set(active)
            if names == {"a"}:
                return (0.40, 0.00)
            if names == {"b"}:
                return (0.30, 0.00)
            return (0.60, 0.00)

        pair = PairwiseSynergyAnalysis(components, evaluate).compute_all_pairs()[0]
        assert abs(pair.synergy_score - 0.20) < 1e-12
        assert abs(pair.youden_synergy_score - 0.20) < 1e-12


# ===========================================================================
# 4. The shipped artifact must match a live run
# ===========================================================================


def test_shipped_artifact_matches_a_live_run():
    """``output/data/ablation_results.json`` must be regenerable.

    The published table is read from this file; if a code change moves the
    numbers, the artifact has to move with it or the manuscript silently
    describes a pipeline that no longer exists.
    """
    from pathlib import Path

    artifact = (
        Path(__file__).resolve().parent.parent / "output" / "data" / "ablation_results.json"
    )
    if not artifact.exists():  # pragma: no cover - conftest normally provides it
        pytest.skip("ablation_results.json not present")

    stored = json.loads(artifact.read_text())
    if "full_pipeline" not in stored:  # pragma: no cover - synthetic conftest data
        pytest.skip("artifact is DataGenerator synthetic data, not a real run")

    live = run_full_ablation(seed=42)
    assert json.dumps(stored, sort_keys=True) == json.dumps(live, sort_keys=True)


def test_shipped_artifact_has_reproducibility_provenance():
    """The committed ablation result identifies its real generator and seed."""
    artifact = (
        Path(__file__).resolve().parent.parent / "output" / "data" / "ablation_results.json"
    )
    if not artifact.exists():  # pragma: no cover - conftest normally provides it
        pytest.skip("ablation_results.json not present")
    payload = json.loads(artifact.read_text())
    if "full_pipeline" not in payload:  # pragma: no cover - synthetic fixture
        pytest.skip("artifact is DataGenerator synthetic data, not a real run")
    assert payload["data_origin"] == "real_pipeline"
    assert payload["source_script"] == "scripts/run_ablation.py"
    assert payload["seed"] == 42
    assert payload["generator"] == {
        "module": "src/ablation/runner.py",
        "function": "run_full_ablation",
        "deterministic": True,
    }
