"""Boundary tests: recommend_profile scoring (m10) and the DRY trust formula (m6)."""

from src.deployment import (
    DeploymentConfigurator,
    RiskProfile,
    TrustDecayAnalyzer,
)
from src.visualization import get_trust_decay_data


class TestRecommendProfileBoundaries:
    """recommend_profile scoring weights and profile-zone boundaries (m10)."""

    def setup_method(self) -> None:
        self.c = DeploymentConfigurator()

    def test_empty_characteristics_low(self) -> None:
        """All flags default; human_oversight defaults True -> -1 -> score -1."""
        assert self.c.recommend_profile({}) == RiskProfile.LOW

    def test_customer_facing_only_low(self) -> None:
        """+1 customer_facing, then -1 default oversight = 0 -> LOW."""
        assert self.c.recommend_profile({"customer_facing": True}) == RiskProfile.LOW

    def test_score_two_is_medium(self) -> None:
        """sensitive_data(+2) + customer_facing(+1) - oversight(-1) = 2 -> MEDIUM."""
        profile = self.c.recommend_profile({"sensitive_data": True, "customer_facing": True})
        assert profile == RiskProfile.MEDIUM

    def test_score_four_is_medium(self) -> None:
        """autonomous(+3) + sensitive_data(+2) - oversight(-1) = 4 -> MEDIUM."""
        profile = self.c.recommend_profile({"autonomous": True, "sensitive_data": True})
        assert profile == RiskProfile.MEDIUM

    def test_score_five_is_high(self) -> None:
        """autonomous(+3)+sensitive_data(+2)+customer_facing(+1)-oversight(-1)=5->HIGH."""
        profile = self.c.recommend_profile(
            {"autonomous": True, "sensitive_data": True, "customer_facing": True}
        )
        assert profile == RiskProfile.HIGH

    def test_human_oversight_omitted_counts_as_discount(self) -> None:
        """Omitted human_oversight defaults True and subtracts 1 point."""
        profile = self.c.recommend_profile(
            {"autonomous": True, "sensitive_data": True, "complex_delegation": True}
        )
        # 3 + 2 + 2 - 1 = 6 -> HIGH.
        assert profile == RiskProfile.HIGH

    def test_human_oversight_false_removes_discount(self) -> None:
        """Explicit human_oversight=False skips the -1 (score 7)."""
        profile = self.c.recommend_profile(
            {
                "autonomous": True,
                "sensitive_data": True,
                "complex_delegation": True,
                "human_oversight": False,
            }
        )
        assert profile == RiskProfile.HIGH

    def test_human_oversight_true_keeps_discount(self) -> None:
        """Explicit human_oversight=True applies the -1 like the default."""
        profile = self.c.recommend_profile(
            {
                "autonomous": True,
                "sensitive_data": True,
                "complex_delegation": True,
                "human_oversight": True,
            }
        )
        # 3 + 2 + 2 - 1 = 6 -> HIGH.
        assert profile == RiskProfile.HIGH


class TestTrustDepthDRY:
    """Trust-depth formula must be single-sourced in practical_depth_limit (m6)."""

    def test_compare_profiles_matches_practical_depth_limit(self) -> None:
        """compare_profiles must reuse practical_depth_limit per profile."""
        for name, delta in [("low", 0.95), ("medium", 0.9), ("high", 0.85)]:
            result = TrustDecayAnalyzer.compare_profiles()[name]
            assert result["practical_limit"] == TrustDecayAnalyzer.practical_depth_limit(delta)

    def test_visualization_matches_practical_depth_limit(self) -> None:
        """get_trust_decay_data practical_depth must equal the analyzer's answer."""
        for delta in (0.8, 0.85, 0.9, 0.95):
            data = get_trust_decay_data(delta=delta, max_depth=60)
            expected = TrustDecayAnalyzer.practical_depth_limit(delta)
            assert data.metadata["practical_depth"] == expected
