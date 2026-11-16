"""
Tests for CIF-AD Coupling Detector (v2.0 addition).

Tests the coupling matrix, coverage analysis, and portfolio optimization.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import numpy as np
import pytest

from consensus import ByzantineConsensus, ConsensusResult, QuorumVerification, Vote
from src.cif_ad_coupling import (  # noqa: E402
    AD_FORMAL_GUARANTEES,
    CIF_AD_COUPLING_MATRIX,
    MIN_PHASE_COVERAGE,
    ADPhase,
    CIFADCouplingDetector,
    CIFDefense,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def detector() -> CIFADCouplingDetector:
    return CIFADCouplingDetector()


@pytest.fixture
def minimal_portfolio() -> list:
    """A minimal portfolio with only the Trust Calculus."""
    return [CIFDefense.TRUST_CALCULUS]


# ── Matrix Structure Tests ────────────────────────────────────────────────────


class TestCouplingMatrix:
    def test_all_defenses_present(self):
        for defense in CIFDefense:
            assert defense in CIF_AD_COUPLING_MATRIX

    def test_all_phases_present_for_each_defense(self):
        for defense in CIFDefense:
            for phase in ADPhase:
                assert phase in CIF_AD_COUPLING_MATRIX[defense]

    def test_all_values_in_range(self):
        for defense, phase_scores in CIF_AD_COUPLING_MATRIX.items():
            for phase, score in phase_scores.items():
                assert 0.0 <= score <= 1.0, f"{defense} {phase} = {score}"

    def test_matrix_array_shape(self, detector):
        arr = detector.get_coupling_matrix_as_array()
        assert arr.shape == (5, 5)  # 5 defenses x 5 phases

    def test_matrix_array_values_match_dict(self, detector):
        defenses = list(CIFDefense)
        phases = list(ADPhase)
        arr = detector.get_coupling_matrix_as_array()
        for i, defense in enumerate(defenses):
            for j, phase in enumerate(phases):
                expected = CIF_AD_COUPLING_MATRIX[defense][phase]
                assert abs(arr[i, j] - expected) < 1e-10


# ── Phase Coverage Tests ──────────────────────────────────────────────────────


class TestPhaseCoverage:
    def test_all_phases_have_nonzero_coverage(self, detector):
        for phase in ADPhase:
            cov = detector.get_phase_coverage(phase)
            assert cov > 0.0, f"Phase {phase} has zero coverage"

    def test_full_stack_exceeds_min_coverage(self, detector):
        for phase in ADPhase:
            cov = detector.get_phase_coverage(phase)
            assert cov > MIN_PHASE_COVERAGE, f"Phase {phase} coverage {cov} <= {MIN_PHASE_COVERAGE}"

    def test_delegate_phase_dominated_by_trust_calculus(self, detector):
        """Trust Calculus should have highest coverage for DELEGATE phase."""
        trust_cov = CIF_AD_COUPLING_MATRIX[CIFDefense.TRUST_CALCULUS][ADPhase.DELEGATE]
        for defense in CIFDefense:
            other_cov = CIF_AD_COUPLING_MATRIX[defense][ADPhase.DELEGATE]
            assert trust_cov >= other_cov, "Trust Calculus should dominate DELEGATE"

    def test_plan_phase_dominated_by_tripwires(self, detector):
        """Tripwires+Invariants should have highest coverage for PLAN phase."""
        tw_cov = CIF_AD_COUPLING_MATRIX[CIFDefense.TRIPWIRES_INVARIANTS][ADPhase.PLAN]
        for defense in CIFDefense:
            other_cov = CIF_AD_COUPLING_MATRIX[defense][ADPhase.PLAN]
            assert tw_cov >= other_cov, "Tripwires should dominate PLAN"

    def test_combined_coverage_exceeds_max_single(self, detector):
        """Combined (parallel) coverage > max single-defense coverage."""
        for phase in ADPhase:
            max_single = detector.get_phase_coverage(phase)
            combined = detector.get_combined_coverage(phase)
            assert combined >= max_single

    def test_combined_coverage_bounded_by_one(self, detector):
        for phase in ADPhase:
            combined = detector.get_combined_coverage(phase)
            assert combined <= 1.0

    def test_empty_portfolio_returns_zero_coverage(self, detector):
        for phase in ADPhase:
            cov = detector.get_combined_coverage(phase, portfolio=[])
            assert cov == 0.0  # combined coverage (product formula) with no defenses is 0


# ── Portfolio Analysis Tests ──────────────────────────────────────────────────


class TestPortfolioAnalysis:
    def test_full_stack_achieves_full_coverage(self, detector):
        analysis = detector.analyze_portfolio()  # default = full stack
        assert analysis.full_coverage_achieved is True
        assert len(analysis.coverage_gaps) == 0

    def test_minimal_portfolio_may_have_gaps(self, detector, minimal_portfolio):
        analysis = detector.analyze_portfolio(minimal_portfolio)
        assert ADPhase.PLAN.value in analysis.coverage_gaps
        assert analysis.full_coverage_achieved is False

    def test_total_coverage_score_in_range(self, detector):
        analysis = detector.analyze_portfolio()
        assert 0.0 <= analysis.total_coverage_score <= 1.0

    def test_full_portfolio_higher_score_than_minimal(self, detector, minimal_portfolio):
        full_analysis = detector.analyze_portfolio()
        minimal_analysis = detector.analyze_portfolio(minimal_portfolio)
        assert full_analysis.total_coverage_score >= minimal_analysis.total_coverage_score

    def test_recommendations_generated_for_gaps(self, detector):
        # Use a portfolio that definitely has gaps
        partial = [CIFDefense.TRUST_CALCULUS]
        analysis = detector.analyze_portfolio(partial)
        if analysis.coverage_gaps:
            assert len(analysis.recommendations) > 0
            assert any("coverage" in r.lower() for r in analysis.recommendations)


# ── Theorem Verification Tests ────────────────────────────────────────────────


class TestTheoremVerification:
    def test_cif_ad_full_coverage_theorem_holds(self, detector):
        """Theorem 4.5: ∀j: max_i M[defense_i, phase_j] > τ_cov = 0.50"""
        assert detector.verify_full_coverage_theorem() is True

    def test_full_coverage_theorem_minimum_column_values(self, detector):
        """All column maxima must exceed MIN_PHASE_COVERAGE."""
        for phase in ADPhase:
            max_cov = detector.get_phase_coverage(phase)
            assert max_cov > MIN_PHASE_COVERAGE, (
                f"Phase {phase.value} has max coverage {max_cov} <= {MIN_PHASE_COVERAGE}"
            )

    def test_specific_column_maxima_from_manuscript(self, detector):
        """Verify the specific values cited in manuscript Theorem 4.5 proof."""
        expected_maxima = {
            ADPhase.PLAN: 0.90,  # Tripwires+Invariants
            ADPhase.DELEGATE: 0.95,  # Trust Calculus
            ADPhase.EXECUTE: 0.90,  # Byzantine Consensus
            ADPhase.OBSERVE: 0.90,  # Cognitive Firewall
            ADPhase.UPDATE: 0.70,  # Belief Sandbox
        }
        for phase, expected in expected_maxima.items():
            actual = detector.get_phase_coverage(phase)
            assert abs(actual - expected) < 1e-10, (
                f"Phase {phase.value}: expected {expected}, got {actual}"
            )


# ── Attack Surface Mapping Tests ──────────────────────────────────────────────


class TestAttackSurfaceMappings:
    def test_all_phases_have_mapping(self, detector):
        mappings = detector.get_attack_surface_mappings()
        phases_covered = {m.phase for m in mappings}
        assert phases_covered == set(ADPhase)

    def test_formal_guarantees_present(self, detector):
        mappings = detector.get_attack_surface_mappings()
        for mapping in mappings:
            assert len(mapping.formal_guarantee) > 0
            assert len(mapping.attack_surface) > 0

    def test_all_formal_guarantees_defined(self):
        for phase in ADPhase:
            assert phase in AD_FORMAL_GUARANTEES
            attack_surface, defense_name, guarantee = AD_FORMAL_GUARANTEES[phase]
            assert len(attack_surface) > 0
            assert len(guarantee) > 0

    def test_phase_guarantees_match_manuscript_table(self):
        assert AD_FORMAL_GUARANTEES[ADPhase.EXECUTE] == (
            "Result tampering", "Provenance tracking", "V(π(φ)) = 1"
        )
        assert AD_FORMAL_GUARANTEES[ADPhase.OBSERVE] == (
            "Evidence fabrication", "Belief sandbox", "B_prov isolation"
        )
        assert AD_FORMAL_GUARANTEES[ADPhase.UPDATE] == (
            "Drift induction", "KL drift detection", "D_KL < θ_drift"
        )

    def test_coverage_scores_match_coupling_matrix(self, detector):
        mappings = detector.get_attack_surface_mappings()
        for mapping in mappings:
            expected = CIF_AD_COUPLING_MATRIX[mapping.primary_defense][mapping.phase]
            assert abs(mapping.coverage_score - expected) < 1e-10


# ── Minimum Viable Portfolio Tests ────────────────────────────────────────────


class TestMinimumViablePortfolio:
    def test_mvp_achieves_full_coverage(self, detector):
        mvp = detector.minimum_viable_portfolio()
        analysis = detector.analyze_portfolio(mvp)
        assert analysis.full_coverage_achieved is True

    def test_mvp_smaller_than_or_equal_to_full_stack(self, detector):
        mvp = detector.minimum_viable_portfolio()
        assert len(mvp) <= len(list(CIFDefense))

    def test_mvp_refuses_unachievable_threshold(self):
        detector = CIFADCouplingDetector()
        with pytest.raises(ValueError, match="unachievable"):
            detector.minimum_viable_portfolio(min_phase_coverage=0.90)

    def test_mvp_non_empty_at_default_threshold(self):
        """minimum_viable_portfolio() is non-empty at the default threshold (P1-7).

        Previously the empty-portfolio `or` idiom made an empty portfolio
        appear to achieve full coverage, so minimum_viable_portfolio()
        returned [].
        """
        detector = CIFADCouplingDetector()
        mvp = detector.minimum_viable_portfolio()
        assert len(mvp) > 0

    def test_empty_portfolio_has_zero_phase_coverage(self):
        """get_phase_coverage with an explicit empty portfolio is 0 (P1-7).

        Previously `portfolio or list(CIFDefense)` treated [] as the full
        stack and returned the full-stack maximum (e.g. 0.9 for PLAN).
        """
        detector = CIFADCouplingDetector()
        for phase in ADPhase:
            assert detector.get_phase_coverage(phase, portfolio=[]) == 0.0

    def test_analyze_empty_portfolio_reports_gaps(self):
        """Empty portfolio reports zero coverage + gaps, never full coverage (P1-7)."""
        detector = CIFADCouplingDetector()
        analysis = detector.analyze_portfolio([])
        assert analysis.full_coverage_achieved is False
        assert len(analysis.coverage_gaps) == len(list(ADPhase))
        assert analysis.total_coverage_score == 0.0

    def test_mvp_with_stricter_threshold_uses_more_defenses(self, detector):
        mvp_normal = detector.minimum_viable_portfolio(min_phase_coverage=0.50)
        mvp_strict = detector.minimum_viable_portfolio(min_phase_coverage=0.65)
        assert len(mvp_strict) >= len(mvp_normal)


# ── Coverage Heatmap Data Tests ───────────────────────────────────────────────


class TestHeatmapData:
    def test_heatmap_returns_correct_shapes(self, detector):
        defense_names, phase_names, matrix = detector.coverage_heatmap_data()
        assert len(defense_names) == len(list(CIFDefense))
        assert len(phase_names) == len(list(ADPhase))
        assert matrix.shape == (len(defense_names), len(phase_names))

    def test_heatmap_values_in_range(self, detector):
        _, _, matrix = detector.coverage_heatmap_data()
        assert np.all(matrix >= 0.0)
        assert np.all(matrix <= 1.0)

    def test_heatmap_names_match_enums(self, detector):
        defense_names, phase_names, _ = detector.coverage_heatmap_data()
        assert set(defense_names) == {d.value for d in CIFDefense}
        assert set(phase_names) == {p.value for p in ADPhase}


# ── Defense Overlap Analysis Tests ───────────────────────────────────────────


class TestOverlapAnalysis:
    def test_overlap_keys_are_pairs(self, detector):
        overlaps = detector.defense_overlap_analysis()
        for key in overlaps:
            parts = key.split("|")
            assert len(parts) == 2

    def test_overlap_values_in_range(self, detector):
        overlaps = detector.defense_overlap_analysis()
        for key, val in overlaps.items():
            assert 0.0 <= val <= 1.0, f"Overlap {key} = {val}"

    def test_number_of_pairs(self, detector):
        overlaps = detector.defense_overlap_analysis()
        n = len(list(CIFDefense))
        expected_pairs = n * (n - 1) // 2
        assert len(overlaps) == expected_pairs

    def test_repr_contains_matrix(self, detector):
        repr_str = repr(detector)
        assert "CIF-AD Coupling Matrix" in repr_str
        for defense in CIFDefense:
            assert defense.value in repr_str


# ── Byzantine Consensus Stress Tests ─────────────────────────────────────────


class TestByzantineConsensusStress:
    """Exercise production consensus at several declared electorate sizes."""

    def test_minimum_n_for_various_f(self):
        for f in range(1, 11):
            n = 3 * f + 1
            consensus = ByzantineConsensus(n_agents=n, max_byzantine=f)
            for i in range(n):
                consensus.submit_vote(Vote(f"agent-{i}", "prop", 0.9))
            assert consensus.compute_consensus("prop")[0] == ConsensusResult.ACCEPT

    def test_quorum_size_formula(self):
        for n, f, expected_q in [(4, 1, 3), (7, 2, 5), (10, 3, 7)]:
            quorum = QuorumVerification(n_agents=n, max_byzantine=f)
            assert quorum.quorum == expected_q

    def test_consensus_supermajority_threshold(self):
        for n in [4, 7, 10, 25, 100]:
            consensus = ByzantineConsensus(n_agents=n)
            for i in range(n):
                consensus.submit_vote(Vote(f"agent-{i}", "prop", 0.9))
            result, confidence = consensus.compute_consensus("prop")
            assert result == ConsensusResult.ACCEPT
            assert confidence == 1.0

    def test_large_electorate_rejects_additional_voter(self):
        consensus = ByzantineConsensus(n_agents=100)
        for i in range(100):
            consensus.submit_vote(Vote(f"agent-{i}", "prop", 0.9))
        with pytest.raises(ValueError, match="Unknown voter"):
            consensus.submit_vote(Vote("stranger", "prop", 0.9))

    def test_large_quorum_rejects_additional_approver(self):
        quorum = QuorumVerification(n_agents=100)
        for i in range(100):
            quorum.approve("action", f"agent-{i}")
        assert quorum.approve("action", "stranger") is False
        assert quorum.get_approval_count("action") == 100

    def test_insufficient_n_is_rejected_for_each_f(self):
        for f in range(1, 11):
            with pytest.raises(ValueError, match="3f"):
                ByzantineConsensus(n_agents=3 * f, max_byzantine=f)


class TestCoverageEdgeCases:
    """Tests for previously-uncovered branches (empty/all-zero, theorem-false, to_dict)."""

    def test_all_zero_coupling_matrix_zero_coverage(self):
        """An explicit empty coupling matrix means zero defenses, not the default stack."""
        detector = CIFADCouplingDetector(coupling_matrix={})
        for phase in ADPhase:
            assert detector.get_phase_coverage(phase) == 0.0
            assert detector.get_combined_coverage(phase, portfolio=list(CIFDefense)) == 0.0

    def test_verify_full_coverage_false_when_threshold_above_every_column(self):
        """verify_full_coverage_theorem() False when some column max < min_coverage."""
        detector = CIFADCouplingDetector(min_coverage=0.96)  # > max column max (0.95)
        assert detector.verify_full_coverage_theorem() is False

    def test_exact_threshold_is_not_full_coverage(self):
        matrix = {
            defense: {phase: 0.5 for phase in ADPhase}
            for defense in CIFDefense
        }
        detector = CIFADCouplingDetector(coupling_matrix=matrix, min_coverage=0.5)
        assert detector.verify_full_coverage_theorem() is False
        assert detector.analyze_portfolio().full_coverage_achieved is False
        with pytest.raises(ValueError, match="unachievable"):
            detector.minimum_viable_portfolio()

    def test_explicit_zero_threshold_is_honored(self):
        detector = CIFADCouplingDetector(min_coverage=0.9)
        portfolio = detector.minimum_viable_portfolio(min_phase_coverage=0.0)
        assert len(portfolio) == 1

    def test_analysis_to_dict_round_trip(self):
        detector = CIFADCouplingDetector()
        analysis = detector.analyze_portfolio([])
        d = analysis.to_dict()
        assert d["portfolio"] == []
        assert d["full_coverage_achieved"] is False
        assert d["total_coverage_score"] == 0.0
        assert len(d["coverage_gaps"]) == len(list(ADPhase))
        assert "phase_coverage" in d and "max_phase_coverage" in d
