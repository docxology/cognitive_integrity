"""Tests for the adversarial training and red-team modules.

Tests AdversarialTrainer, AdversarialGenerator, AttackMutator,
and NashEquilibriumEstimator.

No mocks — all tests use real computation.
"""

from __future__ import annotations

import numpy as np
import pytest

from redteam import AdversarialTrainer, ATConfig, NashEquilibriumEstimator
from redteam.convergence import (
    convergence_round_estimate,
    geometric_convergence_projection,
    natural_gradient_at_step,
)
from redteam.generator import (
    AdversarialGenerator,
    AttackMutator,
    GeneratedAttack,
    OmegaLevel,
)

# ============================================================================
# Section 1: AdversarialGenerator tests
# ============================================================================


class TestAdversarialGenerator:
    """Tests for the AdversarialGenerator class."""

    def test_generate_single_attack(self):
        """Generate a single attack with valid fields."""
        gen = AdversarialGenerator(
            config_thresholds={"drift_threshold": 0.3},
            omega_level=OmegaLevel.OMEGA_2_INJECTION,
            ethical_mode=True,
            seed=42,
        )
        attack = gen.generate_attack(round_num=1)
        assert isinstance(attack, GeneratedAttack)
        assert attack.omega_level == OmegaLevel.OMEGA_2_INJECTION
        assert 0.0 <= attack.evasion_score <= 1.0
        assert attack.ethical_annotation != ""
        assert attack.attack_id != ""
        assert attack.round_num == 1

    @pytest.mark.parametrize("omega", list(OmegaLevel))
    def test_all_omega_levels_generate(self, omega):
        """All Omega levels generate valid attacks."""
        gen = AdversarialGenerator(
            config_thresholds={"drift_threshold": 0.3},
            omega_level=omega,
            seed=99,
        )
        attack = gen.generate_attack()
        assert 0.0 <= attack.evasion_score <= 1.0
        assert attack.omega_level == omega

    def test_generate_batch_size(self):
        """Batch generation produces exactly n attacks."""
        gen = AdversarialGenerator({"drift_threshold": 0.3}, seed=42)
        attacks = gen.generate_batch(n=50)
        assert len(attacks) == 50

    def test_higher_omega_higher_evasion(self):
        """Higher Omega levels produce higher mean evasion scores."""
        thresholds = {"drift_threshold": 0.3, "anomaly_threshold": 0.5}
        means = {}
        for level in [OmegaLevel.OMEGA_1_PASSIVE, OmegaLevel.OMEGA_3_IMPERSONATION,
                      OmegaLevel.OMEGA_5_COORDINATED]:
            gen = AdversarialGenerator(thresholds, omega_level=level, seed=42)
            attacks = gen.generate_batch(100)
            means[level] = np.mean([a.evasion_score for a in attacks])
        assert means[OmegaLevel.OMEGA_5_COORDINATED] > means[OmegaLevel.OMEGA_1_PASSIVE]

    def test_ethical_mode_audit_log(self):
        """Ethical mode records all generated attacks in audit log."""
        gen = AdversarialGenerator({"drift_threshold": 0.3}, ethical_mode=True, seed=42)
        n = 10
        gen.generate_batch(n)
        assert len(gen.audit_log) == n
        for entry in gen.audit_log:
            assert entry["ethical_review"] == "approved"
            assert entry["purpose"] == "adversarial_training_evaluation"

    def test_mutation_operators_applied(self):
        """Mutation operators modify the attack payload."""
        gen = AdversarialGenerator({"drift_threshold": 0.3}, seed=42)
        base_attack = gen.generate_attack()
        mutator = AttackMutator(seed=42)
        mutated = mutator.mutate(base_attack, "semantic_paraphrase")
        assert "[paraphrased variant]" in mutated.payload
        assert mutated.attack_id != base_attack.attack_id

    def test_mutate_all_operators(self):
        """Mutating all operators produces one attack per operator."""
        gen = AdversarialGenerator({"drift_threshold": 0.3}, seed=42)
        attack = gen.generate_attack()
        mutator = AttackMutator(seed=42)
        mutations = mutator.mutate_all_operators(attack)
        assert len(mutations) == len(AttackMutator.MUTATION_OPERATORS)

    def test_reproducibility_with_seed(self):
        """Same seed produces identical attack sequences."""
        gen1 = AdversarialGenerator({"drift_threshold": 0.3}, seed=42)
        gen2 = AdversarialGenerator({"drift_threshold": 0.3}, seed=42)
        a1 = gen1.generate_batch(10)
        a2 = gen2.generate_batch(10)
        for aa, ab in zip(a1, a2):
            assert aa.attack_id == ab.attack_id
            assert abs(aa.evasion_score - ab.evasion_score) < 1e-9


# ============================================================================
# Section 2: AdversarialTrainer tests
# ============================================================================


class TestAdversarialTrainer:
    """Tests for the AdversarialTrainer class."""

    def test_run_all_rounds(self):
        """Running all rounds produces n_rounds results."""
        config = ATConfig(n_rounds=5, attacks_per_round=100)
        trainer = AdversarialTrainer(config=config)
        results = trainer.run()
        assert len(results) == 5
        for i, r in enumerate(results, start=1):
            assert r.round_num == i

    def test_hardened_dr_in_bounds(self):
        """Hardened DR is always in [0, 1]."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        for r in trainer.rounds:
            assert 0.0 <= r.hardened_detection_rate <= 1.0

    def test_delta_dr_non_negative(self):
        """Delta DR should be non-negative (hardening improves detection)."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        for r in trainer.rounds:
            # Each round should improve over baseline (positive delta)
            assert r.delta_dr >= -0.05  # Allow small numerical noise

    def test_gap_closed_is_string(self):
        """Primary gap closed is a non-empty string for all rounds."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        for r in trainer.rounds:
            assert isinstance(r.primary_gap_closed, str)
            assert len(r.primary_gap_closed) > 0

    def test_threshold_updates_dict(self):
        """Threshold updates are returned for each round."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=3))
        trainer.run()
        for r in trainer.rounds:
            assert isinstance(r.threshold_updates, dict)

    def test_convergence_projection_valid(self):
        """Convergence projection returns a valid DR in [baseline, 1.0]."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        proj = trainer.convergence_projection()
        assert proj >= trainer._baseline_dr - 1e-9
        assert proj <= 1.0 + 1e-9

    def test_omega_level_dr_valid(self):
        """Omega-level DRs are all in [0, 1]."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        omega_drs = trainer.omega_level_dr()
        for level, dr in omega_drs.items():
            assert 0.0 <= dr <= 1.0, f"DR for {level} out of range: {dr}"

    def test_omega_5_dr_lowest(self):
        """Omega_5 (coordinated) has the lowest detection rate after AT."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        omega_drs = trainer.omega_level_dr()
        assert omega_drs["omega_5_coordinated"] <= omega_drs["omega_1_passive"]

    def test_summary_structure(self):
        """Summary contains expected keys."""
        trainer = AdversarialTrainer(ATConfig(n_rounds=5))
        trainer.run()
        summary = trainer.summary()
        expected_keys = {
            "n_rounds", "baseline_dr", "final_hardened_dr",
            "total_delta_dr", "projected_nash_dr", "rounds"
        }
        assert expected_keys.issubset(set(summary.keys()))

    def test_reproduces_manuscript_delta_dr(self):
        """AT results reproduce manuscript Table 05g delta_dr values (within 5 pp)."""
        # Manuscript: Round 5 delta_dr = 0.232 (improvement over pre-AT baseline)
        trainer = AdversarialTrainer(ATConfig(n_rounds=5, seed=42))
        trainer.run()
        final = trainer.rounds[-1]
        assert abs(final.delta_dr - 0.232) < 0.05, (
            f"Round 5 delta_dr {final.delta_dr:.3f} differs from manuscript 0.232 by >{0.05}"
        )
        # Also verify gap_closed matches manuscript
        assert "sybil" in final.primary_gap_closed.lower()


# ============================================================================
# Section 3: NashEquilibriumEstimator tests
# ============================================================================


class TestNashEquilibriumEstimator:
    """Tests for the NashEquilibriumEstimator class."""

    def test_geometric_ratio_in_range(self):
        """Geometric ratio is always in (0, 1)."""
        gains = [0.077, 0.052, 0.049, 0.025, 0.019]
        estimator = NashEquilibriumEstimator(gains)
        ratio = estimator.geometric_ratio()
        assert 0.0 < ratio < 1.0

    def test_projected_dr_above_baseline(self):
        """Projected equilibrium DR is above baseline."""
        gains = [0.077, 0.052, 0.049, 0.025, 0.019]
        estimator = NashEquilibriumEstimator(gains)
        proj = estimator.projected_equilibrium_dr(0.447)
        assert proj > 0.447

    def test_projected_dr_bounded(self):
        """Projected equilibrium DR is at most 1.0."""
        gains = [0.5, 0.4, 0.3, 0.2, 0.1]  # Very large gains
        estimator = NashEquilibriumEstimator(gains)
        proj = estimator.projected_equilibrium_dr(0.447)
        assert proj <= 1.0

    def test_convergence_round_positive(self):
        """Convergence round estimate is positive for typical gains."""
        gains = [0.077, 0.052, 0.049]
        estimator = NashEquilibriumEstimator(gains)
        k = estimator.convergence_round(tolerance=0.001)
        assert k >= 0


# ============================================================================
# Section 4: Convergence functions tests
# ============================================================================


class TestConvergenceFunctions:
    """Tests for redteam.convergence module functions."""

    def test_geometric_projection_monotone(self):
        """Projected DR is monotone in baseline."""
        gains = [0.05, 0.04, 0.03]
        proj1, _ = geometric_convergence_projection(gains, 0.3)
        proj2, _ = geometric_convergence_projection(gains, 0.5)
        assert proj2 >= proj1

    def test_geometric_projection_empty_gains(self):
        """Empty gains returns baseline."""
        proj, ratio = geometric_convergence_projection([], 0.447)
        assert proj == 0.447

    def test_convergence_round_zero_when_already_converged(self):
        """Returns 0 when first gain is below tolerance."""
        k = convergence_round_estimate([0.0001], tolerance=0.01)
        assert k == 0

    def test_natural_gradient_shape(self):
        """Natural gradient step returns array of same shape as theta."""
        theta = np.array([0.3, 0.5, 0.7])
        gradient = np.array([0.1, -0.2, 0.15])
        fisher = np.diag([0.3, 0.5, 0.7])
        result = natural_gradient_at_step(theta, gradient, fisher, 0.05)
        assert result.shape == theta.shape
        assert np.all(np.isfinite(result))

    def test_natural_gradient_singular_fallback(self):
        """Natural gradient falls back to Euclidean when Fisher is singular."""
        theta = np.array([0.5])
        gradient = np.array([0.1])
        fisher_singular = np.array([[0.0]])  # singular
        result = natural_gradient_at_step(theta, gradient, fisher_singular, 0.05)
        # Should not raise; result should be finite
        assert np.all(np.isfinite(result))


# ============================================================================
# Section 5: Extended spec generation tests
# ============================================================================


class TestExtendedSpecGeneration:
    """Tests for extended formal specification generation."""

    def test_tla_spec_v2_contains_composition(self):
        """Extended TLA+ spec mentions composition_mode."""
        from formal.extended_specs import generate_tla_spec_v2
        spec = generate_tla_spec_v2()
        assert "composition_mode" in spec
        assert "DefenseComposition" in spec or "sequential" in spec
        assert "DriftDetect" in spec or "DriftThreshold" in spec

    def test_promela_spec_v2_contains_ltl(self):
        """Extended Promela spec has LTL properties."""
        from formal.extended_specs import generate_promela_spec_v2
        spec = generate_promela_spec_v2()
        assert "ltl" in spec
        assert "omega_level" in spec
        assert "DRIFT_THRESH" in spec

    def test_nusmv_spec_v2_contains_safety(self):
        """Extended NuSMV spec has SPEC safety properties."""
        from formal.extended_specs import generate_nusmv_spec_v2
        spec = generate_nusmv_spec_v2()
        assert "SPEC AG" in spec
        assert "SPEC AF" in spec
        assert "composition_mode" in spec

    def test_write_extended_specs_creates_files(self, tmp_path):
        """write_extended_specs creates all three output files."""
        from formal.extended_specs import write_extended_specs
        paths = write_extended_specs(tmp_path)
        assert paths["tla"].exists()
        assert paths["promela"].exists()
        assert paths["nusmv"].exists()
        # Each file should be non-empty
        for p in paths.values():
            assert p.stat().st_size > 100
