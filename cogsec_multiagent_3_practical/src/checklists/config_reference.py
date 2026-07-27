from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrustParameter:
    """A trust calculus parameter with recommended value and guidance.

    Represents one of the four trust calculus parameters (alpha, beta,
    gamma, delta) from the manuscript with its recommended value,
    valid range, and adjustment guidance.

    Args:
        name: Human-readable parameter name.
        symbol: Mathematical symbol (Greek letter).
        recommended: Recommended default value.
        range_min: Minimum valid value.
        range_max: Maximum valid value.
        adjustment_guidance: When and how to adjust this parameter.
    """

    name: str
    symbol: str
    recommended: float
    range_min: float
    range_max: float
    adjustment_guidance: str


@dataclass
class FirewallThreshold:
    """Firewall classification threshold.

    Defines a threshold used by the cognitive firewall to classify
    incoming content as accepted, rejected, or quarantined.

    Args:
        name: Threshold name (e.g., "Accept threshold").
        recommended: Recommended threshold value.
        risk_tradeoff: Description of the risk trade-off when adjusting.
    """

    name: str
    recommended: float
    risk_tradeoff: str


@dataclass
class TripwireConfig:
    """Tripwire configuration recommendation.

    Specifies the recommended minimum count and placement strategy
    for a category of canary beliefs used as tripwires.

    Args:
        category: Canary category name.
        recommended_count: Minimum recommended count of canaries.
        placement_strategy: Where to place canaries of this type.
    """

    category: str
    recommended_count: int
    placement_strategy: str


class ConfigurationReference:
    """Configuration quick reference from manuscript Section 03.

    Validates trust calculus, firewall, and tripwire parameters against
    the recommended ranges specified in the manuscript. Provides
    validation methods that return (valid, issues) tuples for each
    configuration area.

    Default values from manuscript:
        Trust Calculus: alpha=0.3, beta=0.4, gamma=0.3, delta=0.9
        Firewall: accept=0.3, reject=0.7, quarantine=0.3-0.7
        Tripwires: identity=3+, boundary=5+, principal=2+, temporal=1
    """

    def __init__(self) -> None:
        """Initialize with default configuration references from manuscript."""
        self.trust_params: list[TrustParameter] = []
        self.firewall_thresholds: list[FirewallThreshold] = []
        self.tripwire_configs: list[TripwireConfig] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load configuration reference from manuscript Section 03.

        Populates trust parameters, firewall thresholds, and tripwire
        configurations with the values specified in the manuscript.
        """
        self.trust_params = [
            TrustParameter(
                name="Base weight",
                symbol="\u03b1",
                recommended=0.3,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Increase for stable architectures",
            ),
            TrustParameter(
                name="Reputation weight",
                symbol="\u03b2",
                recommended=0.4,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Decrease for new deployments",
            ),
            TrustParameter(
                name="Context weight",
                symbol="\u03b3",
                recommended=0.3,
                range_min=0.1,
                range_max=0.6,
                adjustment_guidance="Increase for specialized tasks",
            ),
            TrustParameter(
                name="Decay factor",
                symbol="\u03b4",
                recommended=0.9,
                range_min=0.5,
                range_max=0.99,
                adjustment_guidance="Decrease for security-critical systems",
            ),
        ]

        self.firewall_thresholds = [
            FirewallThreshold(
                name="Accept threshold",
                recommended=0.3,
                risk_tradeoff="Lower = more strict, more false positives",
            ),
            FirewallThreshold(
                name="Reject threshold",
                recommended=0.7,
                risk_tradeoff="Higher = more permissive, more risk",
            ),
            FirewallThreshold(
                name="Quarantine lower",
                recommended=0.3,
                risk_tradeoff=("Narrower range = faster decisions, less nuance"),
            ),
            FirewallThreshold(
                name="Quarantine upper",
                recommended=0.7,
                risk_tradeoff=("Narrower range = faster decisions, less nuance"),
            ),
        ]

        self.tripwire_configs = [
            TripwireConfig(
                category="Identity canaries",
                recommended_count=3,
                placement_strategy="Core identity beliefs",
            ),
            TripwireConfig(
                category="Boundary canaries",
                recommended_count=5,
                placement_strategy="Permission boundaries",
            ),
            TripwireConfig(
                category="Principal canaries",
                recommended_count=2,
                placement_strategy="Trust relationships",
            ),
            TripwireConfig(
                category="Temporal canaries",
                recommended_count=1,
                placement_strategy="Session continuity",
            ),
        ]

    def validate_trust_weights(
        self, alpha: float, beta: float, gamma: float
    ) -> tuple[bool, list[str]]:
        """Validate that trust weights sum to 1.0 and are in range.

        Checks two conditions:
        1. The three weights must sum to 1.0 (within 0.01 tolerance).
        2. Each weight must fall within its recommended range.

        Args:
            alpha: Base weight (recommended range: 0.1-0.6).
            beta: Reputation weight (recommended range: 0.1-0.6).
            gamma: Context weight (recommended range: 0.1-0.6).

        Returns:
            Tuple of (valid, issues) where valid is True if all checks
            pass, and issues is a list of human-readable issue strings.
        """
        issues: list[str] = []

        if abs(alpha + beta + gamma - 1.0) > 0.01:
            issues.append(f"Weights must sum to 1.0, got {alpha + beta + gamma:.2f}")

        for name, value, param in [
            ("alpha", alpha, self.trust_params[0]),
            ("beta", beta, self.trust_params[1]),
            ("gamma", gamma, self.trust_params[2]),
        ]:
            if not param.range_min <= value <= param.range_max:
                issues.append(
                    f"{name}={value} outside recommended range "
                    f"[{param.range_min}, {param.range_max}]"
                )

        return len(issues) == 0, issues

    def validate_decay(self, delta: float) -> tuple[bool, list[str]]:
        """Validate decay factor against recommended range.

        The decay factor controls how quickly trust degrades over
        delegation hops. Must fall within [0.5, 0.99].

        Args:
            delta: Decay factor to validate.

        Returns:
            Tuple of (valid, issues) where valid is True if delta
            is within the recommended range.
        """
        param = self.trust_params[3]  # Decay factor
        issues: list[str] = []

        if not param.range_min <= delta <= param.range_max:
            issues.append(
                f"delta={delta} outside recommended range [{param.range_min}, {param.range_max}]"
            )

        return len(issues) == 0, issues

    def validate_firewall(self, accept: float, reject: float) -> tuple[bool, list[str]]:
        """Validate firewall thresholds.

        Checks three conditions:
        1. Accept threshold must be in [0, 1].
        2. Reject threshold must be in [0, 1].
        3. Accept must be strictly less than reject (to create a
           valid quarantine zone between them).

        Args:
            accept: Accept threshold (content scoring below this is accepted).
            reject: Reject threshold (content scoring above this is rejected).

        Returns:
            Tuple of (valid, issues) where valid is True if all checks
            pass, and issues is a list of human-readable issue strings.
        """
        issues: list[str] = []

        if not 0 <= accept <= 1:
            issues.append(f"Accept threshold must be 0-1, got {accept}")
        if not 0 <= reject <= 1:
            issues.append(f"Reject threshold must be 0-1, got {reject}")
        if accept >= reject:
            issues.append(f"Accept ({accept}) must be less than reject ({reject})")

        return len(issues) == 0, issues

    def validate_tripwire_counts(self, counts: dict[str, int]) -> tuple[bool, list[str]]:
        """Validate tripwire canary counts against recommendations.

        Each canary category has a minimum recommended count. Missing
        categories are treated as having zero canaries deployed.

        Args:
            counts: Dictionary mapping category name to actual count
                of deployed canaries.

        Returns:
            Tuple of (valid, issues) where valid is True if all
            categories meet their minimum recommended counts.
        """
        issues: list[str] = []

        for config in self.tripwire_configs:
            actual = counts.get(config.category, 0)
            if actual < config.recommended_count:
                issues.append(
                    f"{config.category}: {actual} < {config.recommended_count} recommended"
                )

        return len(issues) == 0, issues


# =============================================================================
