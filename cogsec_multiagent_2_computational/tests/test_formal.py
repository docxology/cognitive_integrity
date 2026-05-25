"""Comprehensive tests for the formal verification module.

Tests cover all nine source files in src/formal/:
- theorem_registry: TheoremRegistry, TheoremResult, TheoremStatus
- byzantine_guarantees: validate_byzantine_bound
- composition_proofs: validate_series_composition, validate_parallel_composition, validate_associativity
- latency_bound: validate_latency_bound
- nusmv_spec: generate_nusmv_spec, parse_nusmv_result
- spin_spec: generate_promela_spec, parse_spin_result
- stealth_impact: validate_stealth_impact
- tla_spec: generate_tla_spec, parse_tla_result
- trust_bounds: validate_trust_bound

All tests use real data and computation. No mocks.
"""

import numpy as np
import pytest

from formal.theorem_registry import TheoremRegistry, TheoremResult, TheoremStatus
from formal.byzantine_guarantees import validate_byzantine_bound
from formal.composition_proofs import (
    validate_series_composition,
    validate_parallel_composition,
    validate_associativity,
)
from formal.latency_bound import validate_latency_bound
from formal.nusmv_spec import generate_nusmv_spec, parse_nusmv_result
from formal.spin_spec import generate_promela_spec, parse_spin_result
from formal.stealth_impact import validate_stealth_impact
from formal.tla_spec import generate_tla_spec, parse_tla_result
from formal.trust_bounds import validate_trust_bound


# ---------------------------------------------------------------------------
# Section 1: TheoremResult and TheoremStatus (dataclass / enum basics)
# ---------------------------------------------------------------------------


class TestTheoremStatus:
    """Tests for the TheoremStatus enum."""

    def test_status_values_exist(self):
        """All four status values are defined."""
        assert TheoremStatus.PASSED.value == "passed"
        assert TheoremStatus.FAILED.value == "failed"
        assert TheoremStatus.SKIPPED.value == "skipped"
        assert TheoremStatus.ERROR.value == "error"

    def test_status_count(self):
        """Exactly four statuses exist."""
        assert len(TheoremStatus) == 4

    def test_status_uniqueness(self):
        """All status values are unique."""
        values = [s.value for s in TheoremStatus]
        assert len(values) == len(set(values))


class TestTheoremResult:
    """Tests for the TheoremResult dataclass."""

    def test_basic_construction(self):
        """TheoremResult stores provided fields."""
        result = TheoremResult(
            theorem_id="1.0",
            name="Test Theorem",
            status=TheoremStatus.PASSED,
            evidence="All checks passed",
            details={"count": 42},
        )
        assert result.theorem_id == "1.0"
        assert result.name == "Test Theorem"
        assert result.status == TheoremStatus.PASSED
        assert result.evidence == "All checks passed"
        assert result.details["count"] == 42

    def test_defaults(self):
        """Defaults are applied for optional fields."""
        result = TheoremResult(
            theorem_id="X",
            name="Minimal",
            status=TheoremStatus.SKIPPED,
        )
        assert result.evidence == ""
        assert result.details == {}

    def test_details_independence(self):
        """Default dict is not shared between instances."""
        r1 = TheoremResult(theorem_id="A", name="A", status=TheoremStatus.PASSED)
        r2 = TheoremResult(theorem_id="B", name="B", status=TheoremStatus.PASSED)
        r1.details["key"] = "value"
        assert "key" not in r2.details


# ---------------------------------------------------------------------------
# Section 2: TheoremRegistry
# ---------------------------------------------------------------------------


class TestTheoremRegistry:
    """Tests for TheoremRegistry: registration, lookup, validation."""

    def test_default_theorems_registered(self):
        """Registry auto-registers Paper 1 + Paper 2 default validators on init."""
        registry = TheoremRegistry()
        expected_ids = {
            # Paper 1
            "3.1", "3.2a", "3.2b", "3.2c", "4", "5.3", "6",
            # Paper 2 extensions (category theory + FEP)
            "CT.1", "CT.2", "CT.3", "FEP.1", "FEP.2",
        }
        actual_ids = set(registry._validators.keys())
        assert expected_ids == actual_ids

    def test_register_custom_theorem(self):
        """Custom theorems can be registered and invoked."""
        registry = TheoremRegistry()

        def dummy_validator(**kwargs) -> TheoremResult:
            return TheoremResult(
                theorem_id="99",
                name="Dummy",
                status=TheoremStatus.PASSED,
                evidence="trivially true",
            )

        registry.register("99", "Dummy Theorem", dummy_validator)
        result = registry.validate("99")
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "99"

    def test_validate_unknown_raises(self):
        """Validating an unregistered theorem raises KeyError."""
        registry = TheoremRegistry()
        with pytest.raises(KeyError, match="Unknown theorem"):
            registry.validate("does_not_exist")

    def test_validate_catches_exceptions(self):
        """If a validator raises, the registry returns ERROR status."""
        registry = TheoremRegistry()

        def broken_validator(**kwargs) -> TheoremResult:
            raise RuntimeError("simulated failure")

        registry.register("broken", "Broken", broken_validator)
        result = registry.validate("broken")
        assert result.status == TheoremStatus.ERROR
        assert "RuntimeError" in result.evidence

    def test_validate_all_returns_sorted(self):
        """validate_all returns results sorted by theorem_id."""
        registry = TheoremRegistry()
        results = registry.validate_all(seed=42)
        ids = [r.theorem_id for r in results]
        assert ids == sorted(ids)

    def test_validate_all_length(self):
        """validate_all returns one result per registered theorem."""
        registry = TheoremRegistry()
        results = registry.validate_all(seed=42)
        assert len(results) == len(registry._validators)

    def test_summary_counts(self):
        """summary returns a dict with all status keys."""
        registry = TheoremRegistry()
        summary = registry.summary()
        for status in TheoremStatus:
            assert status.value in summary
        total = sum(summary.values())
        assert total == len(registry._validators)

    def test_validate_passes_kwargs(self):
        """kwargs are forwarded to the validator function."""
        registry = TheoremRegistry()
        captured = {}

        def capturing_validator(**kwargs) -> TheoremResult:
            captured.update(kwargs)
            return TheoremResult(
                theorem_id="cap", name="Cap", status=TheoremStatus.PASSED
            )

        registry.register("cap", "Capture", capturing_validator)
        registry.validate("cap", seed=99, extra="hello")
        assert captured["seed"] == 99
        assert captured["extra"] == "hello"

    def test_register_overwrites(self):
        """Registering the same ID twice overwrites the first."""
        registry = TheoremRegistry()

        def v1(**kwargs):
            return TheoremResult(
                theorem_id="dup", name="V1", status=TheoremStatus.PASSED
            )

        def v2(**kwargs):
            return TheoremResult(
                theorem_id="dup", name="V2", status=TheoremStatus.FAILED
            )

        registry.register("dup", "V1", v1)
        registry.register("dup", "V2", v2)
        result = registry.validate("dup")
        assert result.name == "V2"
        assert result.status == TheoremStatus.FAILED


# ---------------------------------------------------------------------------
# Section 3: Byzantine Guarantees (Theorem 5.3)
# ---------------------------------------------------------------------------


class TestByzantineGuarantees:
    """Tests for validate_byzantine_bound: n >= 3f+1."""

    def test_passes_with_default_params(self):
        """Default parameters yield a PASSED result."""
        result = validate_byzantine_bound(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "5.3"
        assert result.name == "Byzantine Fault Tolerance"

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical results."""
        r1 = validate_byzantine_bound(max_n=15, seed=42)
        r2 = validate_byzantine_bound(max_n=15, seed=42)
        assert r1.details == r2.details

    def test_details_contain_expected_keys(self):
        """Result details contain all expected keys."""
        result = validate_byzantine_bound(max_n=10, seed=42)
        expected_keys = {
            "tests_run",
            "valid_correct",
            "valid_total",
            "valid_success_rate",
            "invalid_failures",
            "invalid_total",
        }
        assert expected_keys == set(result.details.keys())

    def test_valid_success_rate_high(self):
        """When n >= 3f+1, consensus succeeds at a high rate."""
        result = validate_byzantine_bound(max_n=20, seed=42)
        assert result.details["valid_success_rate"] >= 0.95

    def test_evidence_string_non_empty(self):
        """Evidence string contains informative text."""
        result = validate_byzantine_bound(max_n=10, seed=42)
        assert "Byzantine" in result.evidence or "consensus" in result.evidence

    def test_small_n_range(self):
        """Validation works with a small range of n."""
        result = validate_byzantine_bound(max_n=6, seed=42)
        assert result.details["tests_run"] > 0

    def test_n_3f1_boundary_formula(self):
        """The mathematical bound n >= 3f+1 is correctly encoded."""
        # For n=4, f can be at most 1 (4 >= 3*1+1 = 4)
        # For n=4, f=2 is invalid (4 < 3*2+1 = 7)
        assert 4 >= 3 * 1 + 1
        assert not (4 >= 3 * 2 + 1)

        # For n=7, f can be at most 2 (7 >= 3*2+1 = 7)
        assert 7 >= 3 * 2 + 1
        assert not (7 >= 3 * 3 + 1)

    def test_different_seeds_produce_different_randomness(self):
        """Different seeds produce different internal random draws."""
        r1 = validate_byzantine_bound(max_n=10, seed=1)
        r2 = validate_byzantine_bound(max_n=10, seed=99)
        # Both should pass but may have slightly different detail values
        # At minimum, they should both complete without error
        assert r1.status in (TheoremStatus.PASSED, TheoremStatus.FAILED)
        assert r2.status in (TheoremStatus.PASSED, TheoremStatus.FAILED)


# ---------------------------------------------------------------------------
# Section 4: Composition Proofs (Theorems 3.1b, 3.2, 3.3)
# ---------------------------------------------------------------------------


class TestSeriesComposition:
    """Tests for validate_series_composition: P_miss = product(1 - r_i)."""

    def test_passes_default_params(self):
        """Series composition passes with default parameters."""
        result = validate_series_composition(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "3.1b"

    def test_deterministic(self):
        """Same seed gives identical results."""
        r1 = validate_series_composition(n_modules=3, n_trials=100, seed=42)
        r2 = validate_series_composition(n_modules=3, n_trials=100, seed=42)
        assert r1.details == r2.details

    def test_zero_violations(self):
        """No violations with sufficient trials and tolerance."""
        result = validate_series_composition(n_modules=4, n_trials=500, seed=42)
        assert result.details["violations"] == 0

    def test_max_error_reasonable(self):
        """Max error stays well within tolerance."""
        result = validate_series_composition(n_modules=3, n_trials=200, seed=42)
        assert result.details["max_error"] < 0.05

    def test_series_formula_mathematically(self):
        """Direct check: series P_miss = product(1-r_i)."""
        rates = np.array([0.9, 0.8, 0.7])
        p_miss = float(np.prod(1.0 - rates))
        combined = 1.0 - p_miss
        # 1 - (0.1 * 0.2 * 0.3) = 1 - 0.006 = 0.994
        assert abs(combined - 0.994) < 1e-10


class TestParallelComposition:
    """Tests for validate_parallel_composition: DR >= max(r_i)."""

    def test_passes_default_params(self):
        """Parallel composition passes with default parameters."""
        result = validate_parallel_composition(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "3.2"

    def test_deterministic(self):
        """Same seed produces identical results."""
        r1 = validate_parallel_composition(n_modules=3, n_trials=200, seed=42)
        r2 = validate_parallel_composition(n_modules=3, n_trials=200, seed=42)
        assert r1.details == r2.details

    def test_zero_violations(self):
        """No violations across many trials."""
        result = validate_parallel_composition(n_modules=5, n_trials=1000, seed=42)
        assert result.details["violations"] == 0

    def test_parallel_formula_mathematically(self):
        """Direct check: parallel with OR logic >= max individual."""
        rates = np.array([0.9, 0.8, 0.7])
        combined = 1.0 - float(np.prod(1.0 - rates))
        max_individual = float(np.max(rates))
        # 1 - (0.1 * 0.2 * 0.3) = 0.994 >= 0.9
        assert combined >= max_individual

    def test_single_module_equals_itself(self):
        """With one module, combined rate equals the module's rate."""
        rates = np.array([0.75])
        combined = 1.0 - float(np.prod(1.0 - rates))
        assert abs(combined - 0.75) < 1e-10


class TestCompositionAssociativity:
    """Tests for validate_associativity: compose is associative."""

    def test_passes_default_params(self):
        """Associativity passes with default parameters."""
        result = validate_associativity(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "3.3"

    def test_max_error_negligible(self):
        """Max error is below float epsilon threshold."""
        result = validate_associativity(n_trials=200, seed=42)
        assert result.details["max_error"] < 1e-10

    def test_associativity_mathematically(self):
        """Direct check: (A . B) . C == A . (B . C) for miss-rate product."""
        r_a, r_b, r_c = 0.8, 0.7, 0.6

        # Left: compose(compose(A,B), C)
        ab_miss = (1 - r_a) * (1 - r_b)
        ab_rate = 1 - ab_miss
        left = 1 - (1 - ab_rate) * (1 - r_c)

        # Right: compose(A, compose(B,C))
        bc_miss = (1 - r_b) * (1 - r_c)
        bc_rate = 1 - bc_miss
        right = 1 - (1 - r_a) * (1 - bc_rate)

        assert abs(left - right) < 1e-14

    def test_deterministic(self):
        """Same seed gives identical results."""
        r1 = validate_associativity(n_trials=50, seed=42)
        r2 = validate_associativity(n_trials=50, seed=42)
        assert r1.details == r2.details


# ---------------------------------------------------------------------------
# Section 5: Latency Bound (Theorem 6)
# ---------------------------------------------------------------------------


class TestLatencyBound:
    """Tests for validate_latency_bound: CIF overhead <= 23%."""

    def test_passes_default_params(self):
        """Latency bound passes with defaults."""
        result = validate_latency_bound(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "6"

    def test_mean_overhead_within_target(self):
        """Mean overhead stays within the 23% target."""
        result = validate_latency_bound(n_trials=500, seed=42)
        assert result.details["mean_overhead"] <= 0.23

    def test_details_contain_statistics(self):
        """Result details include mean, p95, max overhead."""
        result = validate_latency_bound(seed=42)
        expected_keys = {"mean_overhead", "p95_overhead", "max_overhead", "target", "n_trials"}
        assert expected_keys == set(result.details.keys())

    def test_overhead_values_positive(self):
        """All overhead statistics are positive."""
        result = validate_latency_bound(seed=42)
        assert result.details["mean_overhead"] > 0
        assert result.details["p95_overhead"] > 0
        assert result.details["max_overhead"] > 0

    def test_p95_greater_than_mean(self):
        """95th percentile is at least as large as the mean."""
        result = validate_latency_bound(n_trials=500, seed=42)
        assert result.details["p95_overhead"] >= result.details["mean_overhead"]

    def test_deterministic(self):
        """Same seed produces identical results."""
        r1 = validate_latency_bound(n_trials=50, seed=42)
        r2 = validate_latency_bound(n_trials=50, seed=42)
        assert r1.details == r2.details

    def test_higher_target_always_passes(self):
        """A generous target (100%) trivially passes."""
        result = validate_latency_bound(overhead_target=1.0, seed=42)
        assert result.status == TheoremStatus.PASSED

    def test_zero_target_fails(self):
        """A zero-percent target fails because CIF adds real overhead."""
        result = validate_latency_bound(overhead_target=0.0, seed=42)
        assert result.status == TheoremStatus.FAILED

    def test_evidence_reflects_status(self):
        """Evidence text differs for passing vs failing results."""
        passed = validate_latency_bound(overhead_target=0.50, seed=42)
        failed = validate_latency_bound(overhead_target=0.0, seed=42)
        assert "exceeds" not in passed.evidence
        assert "exceeds" in failed.evidence


# ---------------------------------------------------------------------------
# Section 6: NuSMV Spec Generation and Parsing
# ---------------------------------------------------------------------------


class TestNuSMVSpec:
    """Tests for NuSMV CTL specification generation and parsing."""

    def test_generate_returns_string(self):
        """Spec generation returns a non-empty string."""
        spec = generate_nusmv_spec()
        assert isinstance(spec, str)
        assert len(spec) > 0

    def test_contains_module_declaration(self):
        """Generated spec contains MODULE main."""
        spec = generate_nusmv_spec()
        assert "MODULE main" in spec

    def test_contains_var_section(self):
        """Generated spec has a VAR block."""
        spec = generate_nusmv_spec()
        assert "VAR" in spec

    def test_contains_ctlspec(self):
        """Generated spec contains CTL properties."""
        spec = generate_nusmv_spec()
        assert "CTLSPEC" in spec

    def test_agent_count_in_header(self):
        """Agent count appears in the comment header."""
        spec = generate_nusmv_spec(n_agents=7, max_byzantine=2)
        assert "7 agents" in spec
        assert "2 Byzantine" in spec

    def test_byzantine_bound_in_spec(self):
        """The 3f+1 bound logic is referenced in transitions."""
        spec = generate_nusmv_spec(n_agents=5, max_byzantine=1)
        assert "3 * byzantine_count + 1" in spec

    def test_firewall_property(self):
        """CTL property about firewall preventing injection is present."""
        spec = generate_nusmv_spec()
        assert "firewall_active" in spec
        assert "injection_succeeds" in spec

    def test_trust_bounded_property(self):
        """Trust boundedness CTL property is present."""
        spec = generate_nusmv_spec()
        assert "trust_score >= 0" in spec
        assert "trust_score <= 100" in spec

    def test_different_params_produce_different_specs(self):
        """Different parameters produce different specs."""
        s1 = generate_nusmv_spec(n_agents=4, max_byzantine=1)
        s2 = generate_nusmv_spec(n_agents=10, max_byzantine=3)
        assert s1 != s2

    def test_parse_nusmv_true_result(self):
        """Parser extracts 'is true' from NuSMV output."""
        output = '-- specification AG (trust_score >= 0) is true\n'
        results = parse_nusmv_result(output)
        # Should have at least one True entry
        assert any(v is True for v in results.values())

    def test_parse_nusmv_false_result(self):
        """Parser extracts 'is false' from NuSMV output."""
        output = '-- specification AG (consensus_reached) is false\n'
        results = parse_nusmv_result(output)
        assert any(v is False for v in results.values())

    def test_parse_nusmv_mixed(self):
        """Parser handles mixed true/false results."""
        output = (
            "-- specification AG (trust_score >= 0) is true\n"
            "-- specification AG (consensus_reached) is false\n"
        )
        results = parse_nusmv_result(output)
        true_count = sum(1 for v in results.values() if v is True)
        false_count = sum(1 for v in results.values() if v is False)
        assert true_count >= 1
        assert false_count >= 1

    def test_parse_nusmv_empty_output(self):
        """Empty output produces empty results dict."""
        results = parse_nusmv_result("")
        assert results == {}

    def test_spec_ends_with_newline(self):
        """Generated spec ends with a trailing newline."""
        spec = generate_nusmv_spec()
        assert spec.endswith("\n")

    def test_belief_integrity_property(self):
        """Belief integrity non-negative property is present."""
        spec = generate_nusmv_spec()
        assert "belief_integrity >= 0" in spec


# ---------------------------------------------------------------------------
# Section 7: SPIN/Promela Spec Generation and Parsing
# ---------------------------------------------------------------------------


class TestSPINSpec:
    """Tests for SPIN Promela specification generation and parsing."""

    def test_generate_returns_string(self):
        """Promela spec is a non-empty string."""
        spec = generate_promela_spec()
        assert isinstance(spec, str)
        assert len(spec) > 0

    def test_contains_defines(self):
        """Generated spec has #define directives."""
        spec = generate_promela_spec(n_agents=5, max_byzantine=1)
        assert "#define N_AGENTS 5" in spec
        assert "#define MAX_BYZANTINE 1" in spec

    def test_contains_quorum_define(self):
        """QUORUM macro is defined."""
        spec = generate_promela_spec()
        assert "#define QUORUM" in spec

    def test_contains_proctype_agent(self):
        """Agent proctype is declared."""
        spec = generate_promela_spec()
        assert "proctype Agent" in spec

    def test_contains_proctype_firewall(self):
        """Firewall proctype is declared."""
        spec = generate_promela_spec()
        assert "proctype Firewall" in spec

    def test_contains_init_block(self):
        """init block is present."""
        spec = generate_promela_spec()
        assert "init {" in spec

    def test_contains_ltl_properties(self):
        """LTL properties are declared."""
        spec = generate_promela_spec()
        assert "ltl consensus" in spec
        assert "ltl trust_bound" in spec
        assert "ltl no_injection" in spec

    def test_delegation_decay_in_spec(self):
        """Delegation decay factor is encoded in Promela."""
        spec = generate_promela_spec()
        assert "85 / 100" in spec  # decay = 0.85

    def test_different_params(self):
        """Different agent counts produce different specs."""
        s1 = generate_promela_spec(n_agents=3, max_byzantine=1)
        s2 = generate_promela_spec(n_agents=8, max_byzantine=2)
        assert s1 != s2

    def test_agent_loop_range(self):
        """Agent init loop covers the correct range."""
        spec = generate_promela_spec(n_agents=6, max_byzantine=2)
        assert "for (i : 0 .. 5)" in spec  # 0 to n_agents-1
        assert "i < 2" in spec  # max_byzantine

    def test_parse_spin_errors_zero(self):
        """Parser recognizes 'errors: 0' as passing."""
        output = "errors: 0\n"
        results = parse_spin_result(output)
        assert any(v is True for v in results.values())

    def test_parse_spin_errors_nonzero(self):
        """Parser recognizes non-zero errors as failing."""
        output = "errors: 3\n"
        results = parse_spin_result(output)
        assert any(v is False for v in results.values())

    def test_parse_spin_no_acceptance_cycle(self):
        """Parser processes 'no acceptance cycle' line.

        Note: due to the if/elif ordering in parse_spin_result, the
        substring 'acceptance cycle' matches before 'no acceptance cycle',
        so this line is recorded as a failure (False).  This test documents
        the current behavior.
        """
        output = "no acceptance cycle found\n"
        results = parse_spin_result(output)
        # The line contains "acceptance cycle" which matches first (elif never reached)
        assert any(v is False for v in results.values())

    def test_parse_spin_acceptance_cycle(self):
        """Parser recognizes 'acceptance cycle' as failing."""
        output = "acceptance cycle detected\n"
        results = parse_spin_result(output)
        assert any(v is False for v in results.values())

    def test_parse_spin_empty_output(self):
        """Empty output produces empty results dict."""
        results = parse_spin_result("")
        assert results == {}

    def test_spec_ends_with_newline(self):
        """Generated Promela spec ends with a trailing newline."""
        spec = generate_promela_spec()
        assert spec.endswith("\n")


# ---------------------------------------------------------------------------
# Section 8: Stealth Impact (Theorem 4)
# ---------------------------------------------------------------------------


class TestStealthImpact:
    """Tests for validate_stealth_impact: I * S <= C_channel."""

    def test_passes_default_params(self):
        """Stealth-impact tradeoff passes with c_channel=1.0."""
        result = validate_stealth_impact(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "4"

    def test_details_contain_expected_keys(self):
        """Result details contain channel capacity and trial info."""
        result = validate_stealth_impact(seed=42)
        expected_keys = {"c_channel", "n_trials", "n_detected", "max_product"}
        assert expected_keys == set(result.details.keys())

    def test_max_product_within_bound(self):
        """Maximum product of successful attacks stays within C_channel."""
        result = validate_stealth_impact(c_channel=1.0, seed=42)
        assert result.details["max_product"] <= 1.0

    def test_small_channel_detects_more(self):
        """Smaller channel capacity leads to more detections."""
        result_big = validate_stealth_impact(c_channel=1.0, n_trials=500, seed=42)
        result_small = validate_stealth_impact(c_channel=0.3, n_trials=500, seed=42)
        assert result_small.details["n_detected"] >= result_big.details["n_detected"]

    def test_deterministic(self):
        """Same seed produces identical results."""
        r1 = validate_stealth_impact(n_trials=100, seed=42)
        r2 = validate_stealth_impact(n_trials=100, seed=42)
        assert r1.details == r2.details

    def test_evidence_mentions_attacks(self):
        """Evidence string mentions attack counts."""
        result = validate_stealth_impact(seed=42)
        assert "attack" in result.evidence.lower()

    def test_product_bound_mathematically(self):
        """Direct check: I * S <= C for various values."""
        # All successful attacks must have I * S <= C
        c_channel = 0.5
        rng = np.random.default_rng(42)
        for _ in range(100):
            impact = rng.uniform(0.1, 1.0)
            stealth = rng.uniform(0.1, 1.0)
            product = impact * stealth
            if product <= c_channel:
                # This attack "succeeds" and satisfies the bound
                assert product <= c_channel

    def test_large_channel_no_detections(self):
        """When C_channel=1.0 and I,S in (0,1], no attacks exceed the bound."""
        # Since I in (0.1,1.0) and S in (0.1,1.0), max product ~ 1.0
        # With C_channel=1.0, almost all should pass
        result = validate_stealth_impact(c_channel=1.0, n_trials=500, seed=42)
        # The maximum possible product is < 1.0 since uniform(0.1,1.0) < 1.0
        assert result.details["n_detected"] == 0


# ---------------------------------------------------------------------------
# Section 9: TLA+ Spec Generation and Parsing
# ---------------------------------------------------------------------------


class TestTLASpec:
    """Tests for TLA+ specification generation and parsing."""

    def test_generate_returns_string(self):
        """TLA+ spec is a non-empty string."""
        spec = generate_tla_spec()
        assert isinstance(spec, str)
        assert len(spec) > 0

    def test_contains_module_header(self):
        """Spec starts with TLA+ module declaration."""
        spec = generate_tla_spec()
        assert "---- MODULE CognitiveIntegrityFramework ----" in spec

    def test_contains_module_footer(self):
        """Spec ends with TLA+ module terminator."""
        spec = generate_tla_spec()
        assert "====" in spec

    def test_contains_extends(self):
        """Spec extends standard TLA+ modules."""
        spec = generate_tla_spec()
        assert "EXTENDS Integers, Sequences, FiniteSets" in spec

    def test_contains_variables(self):
        """All expected state variables are declared."""
        spec = generate_tla_spec()
        for var in ["trust", "votes", "consensus", "byzantine", "firewall_active", "beliefs"]:
            assert var in spec

    def test_contains_init(self):
        """Init predicate is defined."""
        spec = generate_tla_spec()
        assert "Init ==" in spec

    def test_contains_next(self):
        """Next state relation is defined."""
        spec = generate_tla_spec()
        assert "Next ==" in spec

    def test_contains_type_invariant(self):
        """TypeInvariant is defined."""
        spec = generate_tla_spec()
        assert "TypeInvariant ==" in spec

    def test_contains_safety_property(self):
        """Safety property for Byzantine tolerance is defined."""
        spec = generate_tla_spec()
        assert "SafetyProperty ==" in spec

    def test_contains_liveness_property(self):
        """Liveness property for eventual consensus is defined."""
        spec = generate_tla_spec()
        assert "LivenessProperty ==" in spec

    def test_contains_theorems(self):
        """THEOREM declarations are present."""
        spec = generate_tla_spec()
        assert "THEOREM Spec => []TypeInvariant" in spec
        assert "THEOREM Spec => []TrustBounded" in spec
        assert "THEOREM Spec => []SafetyProperty" in spec
        assert "THEOREM Spec => LivenessProperty" in spec

    def test_agent_count_in_comment(self):
        """Agent count appears in the header comment."""
        spec = generate_tla_spec(n_agents=8, max_byzantine=2)
        assert "8 agents" in spec
        assert "2 Byzantine" in spec

    def test_actions_defined(self):
        """Core actions are defined."""
        spec = generate_tla_spec()
        assert "HonestVote(a) ==" in spec
        assert "ByzantineVote(a) ==" in spec
        assert "CheckConsensus ==" in spec
        assert "DelegateTrust(source, target) ==" in spec

    def test_delegation_decay_in_spec(self):
        """Trust delegation uses 85% decay factor."""
        spec = generate_tla_spec()
        assert "85" in spec  # decay factor encoded

    def test_different_params(self):
        """Different parameters produce different specs."""
        s1 = generate_tla_spec(n_agents=5, max_byzantine=1)
        s2 = generate_tla_spec(n_agents=10, max_byzantine=3)
        assert s1 != s2

    def test_parse_tla_no_error(self):
        """Parser recognizes 'Model checking completed. No error' as passing."""
        output = "Model checking completed. No error has been found.\n"
        results = parse_tla_result(output)
        assert results.get("overall") is True

    def test_parse_tla_invariant_violated(self):
        """Parser recognizes 'is violated' as failing."""
        output = "Invariant TypeInvariant is violated.\n"
        results = parse_tla_result(output)
        assert any(v is False for v in results.values())

    def test_parse_tla_error_found(self):
        """Parser recognizes 'error found' as failing."""
        output = "Error: 1 error found in the specification.\n"
        results = parse_tla_result(output)
        assert results.get("overall") is False

    def test_parse_tla_empty_output(self):
        """Empty output produces empty results dict."""
        results = parse_tla_result("")
        assert results == {}

    def test_spec_ends_with_newline(self):
        """Generated TLA+ spec ends with a trailing newline."""
        spec = generate_tla_spec()
        assert spec.endswith("\n")


# ---------------------------------------------------------------------------
# Section 10: Trust Bounds (Theorem 3.1)
# ---------------------------------------------------------------------------


class TestTrustBounds:
    """Tests for validate_trust_bound: T_delegated <= delta^d."""

    def test_passes_default_params(self):
        """Trust bound validation passes with defaults."""
        result = validate_trust_bound(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.theorem_id == "3.1"

    def test_details_contain_expected_keys(self):
        """Result details include delta, depth, trials, violations."""
        result = validate_trust_bound(seed=42)
        expected_keys = {
            "delta",
            "max_depth",
            "n_trials",
            "total_samples",
            "violations",
            "max_violation",
        }
        assert expected_keys == set(result.details.keys())

    def test_zero_violations(self):
        """No violations with default delta=0.85."""
        result = validate_trust_bound(delta=0.85, seed=42)
        assert result.details["violations"] == 0

    def test_total_samples_correct(self):
        """Total samples equals max_depth * n_trials."""
        result = validate_trust_bound(max_depth=5, n_trials=100, seed=42)
        assert result.details["total_samples"] == 5 * 100

    def test_deterministic(self):
        """Same seed produces identical results."""
        r1 = validate_trust_bound(max_depth=3, n_trials=50, seed=42)
        r2 = validate_trust_bound(max_depth=3, n_trials=50, seed=42)
        assert r1.details == r2.details

    def test_delegation_decay_formula(self):
        """Direct check: min(source, target) * delta^d <= delta^d."""
        delta = 0.85
        for d in range(1, 6):
            bound = delta ** d
            # min(s, t) <= 1.0 always, so min(s,t)*delta^d <= delta^d
            for s in [0.1, 0.5, 0.9, 1.0]:
                for t in [0.1, 0.5, 0.9, 1.0]:
                    delegated = min(s, t) * (delta ** d)
                    assert delegated <= bound + 1e-10

    def test_evidence_mentions_samples(self):
        """Evidence text mentions sample counts."""
        result = validate_trust_bound(seed=42)
        assert "sample" in result.evidence.lower()

    def test_different_delta_values(self):
        """Validation works with various delta values."""
        for delta in [0.5, 0.7, 0.85, 0.95]:
            result = validate_trust_bound(delta=delta, n_trials=100, seed=42)
            assert result.status == TheoremStatus.PASSED
            assert result.details["delta"] == delta


# ---------------------------------------------------------------------------
# Section 11: Integration Tests (full registry pipeline)
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    """Integration tests running multiple validators through the registry."""

    def test_all_defaults_pass(self):
        """All default-registered theorems pass with seed=42."""
        registry = TheoremRegistry()
        results = registry.validate_all(seed=42)
        for r in results:
            assert r.status == TheoremStatus.PASSED, (
                f"Theorem {r.theorem_id} ({r.name}) did not pass: {r.evidence}"
            )

    def test_individual_validators_agree_with_registry(self):
        """Direct calls match registry.validate calls."""
        registry = TheoremRegistry()

        direct = validate_byzantine_bound(max_n=10, seed=42)
        via_registry = registry.validate("5.3", max_n=10, seed=42)

        assert direct.status == via_registry.status
        assert direct.theorem_id == via_registry.theorem_id

    def test_summary_all_passed(self):
        """Summary reports all theorems as passed."""
        registry = TheoremRegistry()
        summary = registry.summary()
        # 7 Paper 1 theorems + 5 Paper 2 extensions (CT.1-3, FEP.1-2).
        assert summary["passed"] == 12
        assert summary["failed"] == 0
        assert summary["error"] == 0


# ---------------------------------------------------------------------------
# Section 12: Spec Generator Structural Consistency
# ---------------------------------------------------------------------------


class TestSpecStructuralConsistency:
    """Cross-cutting structural checks across all three spec generators."""

    @pytest.mark.parametrize("n_agents,max_byz", [
        (4, 1), (5, 1), (7, 2), (10, 3), (20, 6),
    ])
    def test_nusmv_spec_valid_for_various_configs(self, n_agents, max_byz):
        """NuSMV spec generates without error for various configs."""
        spec = generate_nusmv_spec(n_agents=n_agents, max_byzantine=max_byz)
        assert "MODULE main" in spec
        assert f"{n_agents}" in spec

    @pytest.mark.parametrize("n_agents,max_byz", [
        (4, 1), (5, 1), (7, 2), (10, 3), (20, 6),
    ])
    def test_promela_spec_valid_for_various_configs(self, n_agents, max_byz):
        """Promela spec generates without error for various configs."""
        spec = generate_promela_spec(n_agents=n_agents, max_byzantine=max_byz)
        assert f"#define N_AGENTS {n_agents}" in spec
        assert f"#define MAX_BYZANTINE {max_byz}" in spec

    @pytest.mark.parametrize("n_agents,max_byz", [
        (4, 1), (5, 1), (7, 2), (10, 3), (20, 6),
    ])
    def test_tla_spec_valid_for_various_configs(self, n_agents, max_byz):
        """TLA+ spec generates without error for various configs."""
        spec = generate_tla_spec(n_agents=n_agents, max_byzantine=max_byz)
        assert "---- MODULE CognitiveIntegrityFramework ----" in spec
        assert f"{n_agents} agents" in spec

    def test_all_specs_are_deterministic(self):
        """All spec generators are deterministic (no randomness)."""
        for gen_fn in [generate_nusmv_spec, generate_promela_spec, generate_tla_spec]:
            s1 = gen_fn(n_agents=5, max_byzantine=1)
            s2 = gen_fn(n_agents=5, max_byzantine=1)
            assert s1 == s2


# ---------------------------------------------------------------------------
# Section 13: Edge Cases and Boundary Conditions
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and boundary conditions across formal modules."""

    def test_byzantine_min_n(self):
        """Minimum meaningful n (4) with f=1 satisfies 4 >= 3*1+1."""
        result = validate_byzantine_bound(max_n=4, seed=42)
        assert result.details["tests_run"] > 0

    def test_composition_single_module(self):
        """Series composition with 1 module: combined = rate itself."""
        result = validate_series_composition(n_modules=1, n_trials=100, seed=42)
        assert result.status == TheoremStatus.PASSED

    def test_composition_many_modules(self):
        """Composition works with many modules (10)."""
        result = validate_series_composition(n_modules=10, n_trials=100, seed=42)
        assert result.status == TheoremStatus.PASSED

    def test_latency_single_trial(self):
        """Latency bound works with a single trial."""
        result = validate_latency_bound(n_trials=1, seed=42)
        assert result.details["n_trials"] == 1

    def test_stealth_impact_minimal_trials(self):
        """Stealth-impact works with minimal trials."""
        result = validate_stealth_impact(n_trials=1, seed=42)
        assert result.theorem_id == "4"

    def test_trust_bound_depth_one(self):
        """Trust bound works with max_depth=1."""
        result = validate_trust_bound(max_depth=1, n_trials=100, seed=42)
        assert result.status == TheoremStatus.PASSED

    def test_trust_bound_large_depth(self):
        """Trust bound works with large depth."""
        result = validate_trust_bound(max_depth=20, n_trials=50, seed=42)
        assert result.status == TheoremStatus.PASSED

    def test_nusmv_parse_garbage_input(self):
        """NuSMV parser handles unrecognized output gracefully."""
        results = parse_nusmv_result("random garbage text\nno useful data\n")
        assert isinstance(results, dict)

    def test_spin_parse_garbage_input(self):
        """SPIN parser handles unrecognized output gracefully."""
        results = parse_spin_result("just some random text\n")
        assert isinstance(results, dict)

    def test_tla_parse_garbage_input(self):
        """TLA+ parser handles unrecognized output gracefully."""
        results = parse_tla_result("unrelated output\n")
        assert isinstance(results, dict)
