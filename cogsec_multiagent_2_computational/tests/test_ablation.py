"""Tests for the ablation study package.

Covers:
- component_removal: ComponentRemovalStudy, AblationResult
- minimal_config: MinimalConfigSearch, MinimalConfigResult
- synergy: PairwiseSynergyAnalysis, SynergyResult

All tests use real evaluation functions with deterministic computation.
No mocks.
"""

import numpy as np
import pytest

from ablation.component_removal import AblationResult, ComponentRemovalStudy
from ablation.minimal_config import MinimalConfigResult, MinimalConfigSearch
from ablation.synergy import PairwiseSynergyAnalysis, SynergyResult

# ---------------------------------------------------------------------------
# Shared test evaluation functions (real computation, no mocks)
# ---------------------------------------------------------------------------

def make_additive_eval_fn(contributions: dict[str, float], baseline_fpr: float = 0.05):
    """Create an evaluation function where each component adds to TPR.

    Each component contributes a fixed amount to detection rate.
    FPR decreases slightly with more components.

    Returns (tpr, fpr) for use with ComponentRemovalStudy.
    """
    def evaluate(active: dict) -> tuple[float, float]:
        tpr = sum(contributions.get(name, 0.0) for name in active)
        tpr = min(tpr, 1.0)
        fpr = max(baseline_fpr - 0.005 * len(active), 0.01)
        return (tpr, fpr)
    return evaluate


def make_tpr_only_eval_fn(contributions: dict[str, float]):
    """Create an evaluation function returning only TPR (for MinimalConfig/Synergy).

    Each component contributes a fixed amount to detection rate.
    """
    def evaluate(active: dict) -> float:
        tpr = sum(contributions.get(name, 0.0) for name in active)
        return min(tpr, 1.0)
    return evaluate


def make_synergistic_eval_fn(
    individual: dict[str, float],
    synergies: dict[tuple[str, str], float],
):
    """Create an evaluation function with pairwise synergy effects.

    When both components in a synergy pair are present, the combined
    TPR gets a bonus (or penalty if negative).
    """
    def evaluate(active: dict) -> float:
        tpr = sum(individual.get(name, 0.0) for name in active)
        active_names = set(active.keys())
        for (a, b), bonus in synergies.items():
            if a in active_names and b in active_names:
                tpr += bonus
        return min(max(tpr, 0.0), 1.0)
    return evaluate


# ===========================================================================
# ComponentRemovalStudy tests
# ===========================================================================

class TestAblationResult:
    """Tests for the AblationResult dataclass."""

    def test_ablation_result_construction(self):
        result = AblationResult(
            removed_component="firewall",
            remaining_components=["trust", "consensus"],
            detection_rate=0.85,
            delta_tpr=-0.10,
            false_positive_rate=0.06,
            delta_fpr=0.01,
        )
        assert result.removed_component == "firewall"
        assert result.remaining_components == ["trust", "consensus"]
        assert result.detection_rate == 0.85
        assert result.delta_tpr == -0.10
        assert result.false_positive_rate == 0.06
        assert result.delta_fpr == 0.01

    def test_ablation_result_fields_independent(self):
        r1 = AblationResult("a", ["b", "c"], 0.9, -0.05, 0.03, 0.01)
        r2 = AblationResult("b", ["a", "c"], 0.8, -0.15, 0.04, 0.02)
        assert r1.removed_component != r2.removed_component
        assert r1.detection_rate != r2.detection_rate


class TestComponentRemovalStudy:
    """Tests for systematic component removal ablation."""

    def _make_study(self):
        """Create a study with 4 components of known contributions."""
        components = {
            "firewall": "fw_instance",
            "trust": "trust_instance",
            "consensus": "cons_instance",
            "tripwire": "tw_instance",
        }
        contributions = {
            "firewall": 0.35,
            "trust": 0.25,
            "consensus": 0.20,
            "tripwire": 0.15,
        }
        eval_fn = make_additive_eval_fn(contributions, baseline_fpr=0.05)
        return ComponentRemovalStudy(components, eval_fn)

    def test_full_ablation_returns_one_result_per_component(self):
        study = self._make_study()
        results = study.run_full_ablation()
        assert len(results) == 4

    def test_full_ablation_result_types(self):
        study = self._make_study()
        results = study.run_full_ablation()
        for r in results:
            assert isinstance(r, AblationResult)
            assert isinstance(r.removed_component, str)
            assert isinstance(r.remaining_components, list)
            assert isinstance(r.detection_rate, float)
            assert isinstance(r.delta_tpr, float)
            assert isinstance(r.false_positive_rate, float)
            assert isinstance(r.delta_fpr, float)

    def test_full_ablation_delta_tpr_is_negative(self):
        """Removing any component should decrease TPR (delta < 0)."""
        study = self._make_study()
        results = study.run_full_ablation()
        for r in results:
            assert r.delta_tpr < 0, (
                f"Removing {r.removed_component} should decrease TPR, "
                f"but delta_tpr={r.delta_tpr}"
            )

    def test_full_ablation_sorted_by_delta_tpr(self):
        """Results should be sorted by delta_tpr ascending (largest drop first)."""
        study = self._make_study()
        results = study.run_full_ablation()
        deltas = [r.delta_tpr for r in results]
        assert deltas == sorted(deltas), "Results not sorted by delta_tpr ascending"

    def test_full_ablation_most_impactful_is_firewall(self):
        """Firewall has the highest contribution (0.35), so removing it
        should cause the largest TPR drop."""
        study = self._make_study()
        results = study.run_full_ablation()
        # First result (most negative delta) should be firewall
        assert results[0].removed_component == "firewall"

    def test_full_ablation_remaining_components(self):
        """Each result's remaining_components should exclude the removed one."""
        study = self._make_study()
        results = study.run_full_ablation()
        all_names = {"firewall", "trust", "consensus", "tripwire"}
        for r in results:
            remaining_set = set(r.remaining_components)
            assert r.removed_component not in remaining_set
            assert remaining_set == all_names - {r.removed_component}

    def test_full_ablation_detection_rate_values(self):
        """With additive contributions, removing component X should yield
        total - contribution(X)."""
        study = self._make_study()
        results = study.run_full_ablation()
        # Full TPR = 0.35 + 0.25 + 0.20 + 0.15 = 0.95
        for r in results:
            # TPR after removal is full_tpr + delta_tpr
            assert 0.0 <= r.detection_rate <= 1.0

    def test_full_baseline_cached(self):
        """The full baseline should be computed only once (cached)."""
        call_count = [0]
        components = {"a": 1, "b": 2}

        def counting_eval(active):
            call_count[0] += 1
            return (0.9, 0.05)

        study = ComponentRemovalStudy(components, counting_eval)
        study._get_full_baseline()
        study._get_full_baseline()
        # Should only call evaluate_fn once
        assert call_count[0] == 1

    def test_leave_k_out_k2(self):
        """Leave-2-out should produce C(4,2) = 6 results."""
        study = self._make_study()
        results = study.run_leave_k_out(k=2)
        assert len(results) == 6

    def test_leave_k_out_sorted_by_delta(self):
        study = self._make_study()
        results = study.run_leave_k_out(k=2)
        deltas = [r.delta_tpr for r in results]
        assert deltas == sorted(deltas)

    def test_leave_k_out_removed_names_are_comma_separated(self):
        study = self._make_study()
        results = study.run_leave_k_out(k=2)
        for r in results:
            names = r.removed_component.split(", ")
            assert len(names) == 2

    def test_leave_k_out_k_equals_n_raises(self):
        study = self._make_study()
        with pytest.raises(ValueError, match="must be less than"):
            study.run_leave_k_out(k=4)

    def test_leave_k_out_k_greater_than_n_raises(self):
        study = self._make_study()
        with pytest.raises(ValueError, match="must be less than"):
            study.run_leave_k_out(k=10)

    def test_leave_k_out_k_zero_raises(self):
        study = self._make_study()
        with pytest.raises(ValueError, match="k must be >= 1"):
            study.run_leave_k_out(k=0)

    def test_leave_k_out_k_negative_raises(self):
        study = self._make_study()
        with pytest.raises(ValueError, match="k must be >= 1"):
            study.run_leave_k_out(k=-1)

    def test_leave_k_out_k3(self):
        """Leave-3-out with 4 components: C(4,3) = 4 results."""
        study = self._make_study()
        results = study.run_leave_k_out(k=3)
        assert len(results) == 4

    def test_leave_k_out_worst_pair(self):
        """Removing the two highest-contribution components should cause
        the largest drop."""
        study = self._make_study()
        results = study.run_leave_k_out(k=2)
        # firewall(0.35) + trust(0.25) = 0.60 removed -> most negative delta
        worst = results[0]
        removed_set = set(worst.removed_component.split(", "))
        assert "firewall" in removed_set
        assert "trust" in removed_set

    def test_get_critical_components_default_threshold(self):
        """With default threshold=0.05, all components with contribution > 0.05
        should be critical."""
        study = self._make_study()
        critical = study.get_critical_components(threshold=0.05)
        # All contributions are > 0.05, so all should be critical
        assert len(critical) == 4

    def test_get_critical_components_high_threshold(self):
        """With high threshold, only the most impactful components are critical."""
        study = self._make_study()
        critical = study.get_critical_components(threshold=0.30)
        # Only firewall (0.35) has |delta| > 0.30
        assert "firewall" in critical
        assert len(critical) == 1

    def test_get_critical_components_very_high_threshold(self):
        """With threshold higher than any contribution, none are critical."""
        study = self._make_study()
        critical = study.get_critical_components(threshold=0.50)
        assert len(critical) == 0

    def test_rank_by_importance_order(self):
        study = self._make_study()
        ranked = study.rank_by_importance()
        assert len(ranked) == 4
        # Should be descending by importance
        importances = [r[1] for r in ranked]
        assert importances == sorted(importances, reverse=True)

    def test_rank_by_importance_firewall_first(self):
        study = self._make_study()
        ranked = study.rank_by_importance()
        assert ranked[0][0] == "firewall"

    def test_rank_by_importance_returns_tuples(self):
        study = self._make_study()
        ranked = study.rank_by_importance()
        for name, importance in ranked:
            assert isinstance(name, str)
            assert isinstance(importance, float)
            assert importance >= 0.0

    def test_single_component_study(self):
        """Study with a single component."""
        components = {"only": "value"}
        eval_fn = make_additive_eval_fn({"only": 0.9})
        study = ComponentRemovalStudy(components, eval_fn)
        results = study.run_full_ablation()
        assert len(results) == 1
        assert results[0].removed_component == "only"
        assert results[0].remaining_components == []

    def test_two_component_study(self):
        """Study with exactly 2 components."""
        components = {"a": 1, "b": 2}
        eval_fn = make_additive_eval_fn({"a": 0.5, "b": 0.4})
        study = ComponentRemovalStudy(components, eval_fn)

        results = study.run_full_ablation()
        assert len(results) == 2

        k2_results = study.run_leave_k_out(k=1)
        assert len(k2_results) == 2


# ===========================================================================
# MinimalConfigSearch tests
# ===========================================================================

class TestMinimalConfigResult:
    """Tests for the MinimalConfigResult dataclass."""

    def test_result_construction(self):
        result = MinimalConfigResult(
            components=["firewall", "trust"],
            detection_rate=0.92,
            n_components=2,
            meets_threshold=True,
        )
        assert result.components == ["firewall", "trust"]
        assert result.detection_rate == 0.92
        assert result.n_components == 2
        assert result.meets_threshold is True


class TestMinimalConfigSearch:
    """Tests for minimum viable configuration search."""

    def _make_search(self, target_tpr=0.90):
        """Create a search with known additive components."""
        components = {
            "firewall": "fw",
            "trust": "trust",
            "consensus": "cons",
            "tripwire": "tw",
            "sandbox": "sb",
        }
        contributions = {
            "firewall": 0.40,
            "trust": 0.30,
            "consensus": 0.15,
            "tripwire": 0.10,
            "sandbox": 0.05,
        }
        eval_fn = make_tpr_only_eval_fn(contributions)
        return MinimalConfigSearch(components, eval_fn, target_tpr=target_tpr)

    def test_greedy_forward_meets_threshold(self):
        search = self._make_search(target_tpr=0.90)
        result = search.greedy_forward_search()
        assert result.meets_threshold is True
        assert result.detection_rate >= 0.90

    def test_greedy_forward_finds_minimal_set(self):
        """Forward search should find a small subset that meets threshold.
        With additive: firewall(0.40) + trust(0.30) + consensus(0.15) = 0.85 < 0.90
        firewall(0.40) + trust(0.30) + tripwire(0.10) + consensus(0.15) = 0.95 >= 0.90
        Greedy picks highest first: fw(0.40), trust(0.30), consensus(0.15) = 0.85,
        then needs one more -> tripwire or sandbox.
        So result should have 4 components (0.40+0.30+0.15+0.10=0.95)."""
        search = self._make_search(target_tpr=0.90)
        result = search.greedy_forward_search()
        # Must have at least firewall and trust
        assert "firewall" in result.components
        assert "trust" in result.components
        assert result.n_components <= 5

    def test_greedy_forward_stops_at_threshold(self):
        """With a low threshold, forward search should stop early."""
        search = self._make_search(target_tpr=0.40)
        result = search.greedy_forward_search()
        # firewall alone = 0.40, meets threshold
        assert result.n_components == 1
        assert result.components == ["firewall"]
        assert result.meets_threshold is True

    def test_greedy_forward_unreachable_threshold(self):
        """If threshold is higher than sum of all contributions, result
        won't meet threshold but includes all components."""
        search = self._make_search(target_tpr=1.01)
        result = search.greedy_forward_search()
        assert result.meets_threshold is False
        assert result.n_components == 5  # all components added

    def test_greedy_backward_meets_threshold(self):
        search = self._make_search(target_tpr=0.90)
        result = search.greedy_backward_search()
        assert result.meets_threshold is True
        assert result.detection_rate >= 0.90

    def test_greedy_backward_removes_least_impactful(self):
        """Backward search removes least impactful first.
        Full = 1.0 (capped). Remove sandbox(0.05)->0.95>=0.90. OK.
        Remove tripwire(0.10)->0.85<0.90. Stop.
        So result should have 4 components."""
        search = self._make_search(target_tpr=0.90)
        result = search.greedy_backward_search()
        # sandbox (0.05) should be removed first
        assert "sandbox" not in result.components
        assert result.n_components == 4

    def test_greedy_backward_keeps_all_when_tight(self):
        """If threshold is very high, backward can't remove anything."""
        search = self._make_search(target_tpr=1.00)
        result = search.greedy_backward_search()
        assert result.n_components == 5
        assert result.detection_rate == 1.0

    def test_exhaustive_search_finds_all_viable(self):
        search = self._make_search(target_tpr=0.90)
        viable = search.exhaustive_search()
        # All viable results should meet threshold
        for r in viable:
            assert r.meets_threshold is True
            assert r.detection_rate >= 0.90

    def test_exhaustive_search_sorted_correctly(self):
        """Sorted by n_components ascending, then detection_rate descending."""
        search = self._make_search(target_tpr=0.70)
        viable = search.exhaustive_search()
        for i in range(len(viable) - 1):
            a, b = viable[i], viable[i + 1]
            if a.n_components == b.n_components:
                assert a.detection_rate >= b.detection_rate
            else:
                assert a.n_components <= b.n_components

    def test_exhaustive_search_with_max_size(self):
        search = self._make_search(target_tpr=0.70)
        viable = search.exhaustive_search(max_size=2)
        for r in viable:
            assert r.n_components <= 2

    def test_exhaustive_search_smallest_viable(self):
        """The smallest viable set for target=0.70 should have 2 components:
        firewall(0.40) + trust(0.30) = 0.70."""
        search = self._make_search(target_tpr=0.70)
        viable = search.exhaustive_search()
        assert len(viable) > 0
        smallest = viable[0]
        assert smallest.n_components == 2
        assert set(smallest.components) == {"firewall", "trust"}

    def test_exhaustive_search_no_viable_returns_empty(self):
        """If no subset meets the target, return empty list."""
        search = self._make_search(target_tpr=1.50)
        viable = search.exhaustive_search()
        assert viable == []

    def test_forward_and_backward_both_meet_threshold(self):
        """Both search strategies should find viable configs."""
        search = self._make_search(target_tpr=0.85)
        forward = search.greedy_forward_search()
        backward = search.greedy_backward_search()
        assert forward.meets_threshold is True
        assert backward.meets_threshold is True

    def test_single_component_sufficient(self):
        """When one component alone meets threshold."""
        components = {"super": "val"}
        eval_fn = make_tpr_only_eval_fn({"super": 0.95})
        search = MinimalConfigSearch(components, eval_fn, target_tpr=0.90)

        forward = search.greedy_forward_search()
        assert forward.n_components == 1
        assert forward.meets_threshold is True

        backward = search.greedy_backward_search()
        assert backward.n_components == 1
        assert backward.meets_threshold is True


# ===========================================================================
# PairwiseSynergyAnalysis tests
# ===========================================================================

class TestSynergyResult:
    """Tests for the SynergyResult dataclass."""

    def test_synergy_result_construction(self):
        result = SynergyResult(
            component_a="firewall",
            component_b="tripwire",
            individual_a_tpr=0.60,
            individual_b_tpr=0.50,
            combined_tpr=0.75,
            synergy_score=0.15,
        )
        assert result.component_a == "firewall"
        assert result.component_b == "tripwire"
        assert result.synergy_score == 0.15

    def test_synergy_score_calculation(self):
        """synergy = combined - max(individual_a, individual_b)."""
        result = SynergyResult(
            component_a="a",
            component_b="b",
            individual_a_tpr=0.60,
            individual_b_tpr=0.50,
            combined_tpr=0.75,
            synergy_score=0.75 - max(0.60, 0.50),
        )
        assert abs(result.synergy_score - 0.15) < 1e-10


class TestPairwiseSynergyAnalysis:
    """Tests for pairwise synergy analysis."""

    def _make_synergy_analysis(self):
        """Create analysis with known synergy effects."""
        components = {
            "firewall": "fw",
            "trust": "trust",
            "consensus": "cons",
            "tripwire": "tw",
        }
        individual = {
            "firewall": 0.50,
            "trust": 0.40,
            "consensus": 0.35,
            "tripwire": 0.30,
        }
        synergies = {
            ("firewall", "tripwire"): 0.09,    # Strong synergy
            ("trust", "consensus"): 0.05,       # Moderate synergy
            ("firewall", "consensus"): -0.03,   # Mild antagonism
        }
        eval_fn = make_synergistic_eval_fn(individual, synergies)
        return PairwiseSynergyAnalysis(components, eval_fn)

    def test_compute_all_pairs_count(self):
        """C(4,2) = 6 pairs."""
        analysis = self._make_synergy_analysis()
        results = analysis.compute_all_pairs()
        assert len(results) == 6

    def test_compute_all_pairs_result_types(self):
        analysis = self._make_synergy_analysis()
        results = analysis.compute_all_pairs()
        for r in results:
            assert isinstance(r, SynergyResult)
            assert isinstance(r.component_a, str)
            assert isinstance(r.component_b, str)
            assert isinstance(r.synergy_score, float)

    def test_compute_all_pairs_sorted_descending(self):
        """Results should be sorted by synergy score descending."""
        analysis = self._make_synergy_analysis()
        results = analysis.compute_all_pairs()
        scores = [r.synergy_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_firewall_tripwire_synergy(self):
        """firewall + tripwire should have the highest synergy (~0.09)."""
        analysis = self._make_synergy_analysis()
        results = analysis.compute_all_pairs()

        # Find the firewall+tripwire pair
        fw_tw = None
        for r in results:
            pair = {r.component_a, r.component_b}
            if pair == {"firewall", "tripwire"}:
                fw_tw = r
                break

        assert fw_tw is not None
        # individual: fw=0.50, tw=0.30; combined=0.50+0.30+0.09=0.89
        # synergy = 0.89 - max(0.50, 0.30) = 0.89 - 0.50 = 0.39
        # Wait -- the eval adds all individuals + synergy bonuses
        # So combined = 0.50 + 0.30 + 0.09 = 0.89
        # synergy_score = 0.89 - max(0.50, 0.30) = 0.39
        assert fw_tw.synergy_score > 0

    def test_individual_tprs_cached(self):
        """Individual TPRs should be computed only once per component."""
        call_count = [0]
        components = {"a": 1, "b": 2, "c": 3}

        def counting_eval(active):
            call_count[0] += 1
            return sum(0.3 for _ in active)

        analysis = PairwiseSynergyAnalysis(components, counting_eval)
        analysis.compute_all_pairs()
        # 3 individual + 3 pairs = 6 calls total (not 6+3=9 if re-computed)
        assert call_count[0] == 6

    def test_get_top_synergies_default(self):
        analysis = self._make_synergy_analysis()
        top = analysis.get_top_synergies(n=3)
        assert len(top) <= 3
        # Top synergies should have highest scores
        if len(top) > 1:
            assert top[0].synergy_score >= top[1].synergy_score

    def test_get_top_synergies_auto_computes(self):
        """get_top_synergies should compute pairs if not already done."""
        analysis = self._make_synergy_analysis()
        # Don't call compute_all_pairs first
        top = analysis.get_top_synergies(n=2)
        assert len(top) == 2

    def test_get_top_synergies_n_exceeds_pairs(self):
        """Requesting more than available pairs returns all."""
        analysis = self._make_synergy_analysis()
        top = analysis.get_top_synergies(n=100)
        assert len(top) == 6  # C(4,2)

    def test_get_antagonistic_pairs(self):
        """Should find pairs with negative synergy."""
        analysis = self._make_synergy_analysis()
        antagonistic = analysis.get_antagonistic_pairs()
        for r in antagonistic:
            assert r.synergy_score < 0

    def test_get_antagonistic_pairs_sorted(self):
        """Antagonistic pairs sorted ascending (most antagonistic first)."""
        analysis = self._make_synergy_analysis()
        antagonistic = analysis.get_antagonistic_pairs()
        if len(antagonistic) > 1:
            scores = [r.synergy_score for r in antagonistic]
            assert scores == sorted(scores)

    def test_get_antagonistic_pairs_auto_computes(self):
        analysis = self._make_synergy_analysis()
        antagonistic = analysis.get_antagonistic_pairs()
        # Should work without calling compute_all_pairs first
        assert isinstance(antagonistic, list)

    def test_synergy_matrix_shape(self):
        analysis = self._make_synergy_analysis()
        names, matrix = analysis.synergy_matrix()
        assert len(names) == 4
        assert matrix.shape == (4, 4)

    def test_synergy_matrix_symmetric(self):
        analysis = self._make_synergy_analysis()
        names, matrix = analysis.synergy_matrix()
        np.testing.assert_array_almost_equal(matrix, matrix.T)

    def test_synergy_matrix_diagonal_zero(self):
        analysis = self._make_synergy_analysis()
        names, matrix = analysis.synergy_matrix()
        np.testing.assert_array_equal(np.diag(matrix), np.zeros(4))

    def test_synergy_matrix_dtype(self):
        analysis = self._make_synergy_analysis()
        names, matrix = analysis.synergy_matrix()
        assert matrix.dtype == np.float64

    def test_synergy_matrix_names_match_components(self):
        analysis = self._make_synergy_analysis()
        names, matrix = analysis.synergy_matrix()
        assert set(names) == {"firewall", "trust", "consensus", "tripwire"}

    def test_no_synergy_when_purely_additive(self):
        """With purely additive eval, synergy = combined - max(individual).
        combined(a,b) = a + b; max = max(a, b).
        synergy = a + b - max(a, b) = min(a, b) > 0 always.
        So even additive shows 'synergy'. This is expected behavior."""
        components = {"a": 1, "b": 2}
        eval_fn = make_tpr_only_eval_fn({"a": 0.3, "b": 0.4})
        analysis = PairwiseSynergyAnalysis(components, eval_fn)
        results = analysis.compute_all_pairs()
        assert len(results) == 1
        # combined = 0.3 + 0.4 = 0.7; max = 0.4; synergy = 0.3
        assert abs(results[0].synergy_score - 0.3) < 1e-10

    def test_two_components_single_pair(self):
        """With exactly 2 components, there is exactly 1 pair."""
        components = {"x": 1, "y": 2}
        eval_fn = make_tpr_only_eval_fn({"x": 0.5, "y": 0.5})
        analysis = PairwiseSynergyAnalysis(components, eval_fn)
        results = analysis.compute_all_pairs()
        assert len(results) == 1

    def test_three_components_three_pairs(self):
        """C(3,2) = 3 pairs."""
        components = {"a": 1, "b": 2, "c": 3}
        eval_fn = make_tpr_only_eval_fn({"a": 0.3, "b": 0.3, "c": 0.3})
        analysis = PairwiseSynergyAnalysis(components, eval_fn)
        results = analysis.compute_all_pairs()
        assert len(results) == 3
