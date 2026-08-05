"""
CIF-AD Coupling Detector for CIF v2.0

Implements the CIF Action-Delegation (AD) coupling matrix analysis, providing
coverage scores, gap detection, and per-phase defense recommendations.

Added in Second Edition (v2.0) as part of CIF-AD integration (§4 of manuscript).
Reference: Table 4 (CIF-AD coupling matrix) in 04_formal_framework.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class ADPhase(Enum):
    """Action-Delegation cycle phases."""

    PLAN = "plan"
    DELEGATE = "delegate"
    EXECUTE = "execute"
    OBSERVE = "observe"
    UPDATE = "update"


class CIFDefense(Enum):
    """CIF canonical defense mechanisms."""

    COGNITIVE_FIREWALL = "cognitive_firewall"
    BELIEF_SANDBOX = "belief_sandbox"
    TRUST_CALCULUS = "trust_calculus"
    TRIPWIRES_INVARIANTS = "tripwires_invariants"
    BYZANTINE_CONSENSUS = "byzantine_consensus"


# CIF-AD coupling matrix (from Table 4 in manuscript §4)
# Rows = defenses, Columns = AD phases
# Values in [0, 1]: fraction of phase's attack surface covered
CIF_AD_COUPLING_MATRIX: Dict[CIFDefense, Dict[ADPhase, float]] = {
    CIFDefense.COGNITIVE_FIREWALL: {
        ADPhase.PLAN: 0.80,
        ADPhase.DELEGATE: 0.40,
        ADPhase.EXECUTE: 0.20,
        ADPhase.OBSERVE: 0.90,
        ADPhase.UPDATE: 0.30,
    },
    CIFDefense.BELIEF_SANDBOX: {
        ADPhase.PLAN: 0.50,
        ADPhase.DELEGATE: 0.30,
        ADPhase.EXECUTE: 0.30,
        ADPhase.OBSERVE: 0.85,
        ADPhase.UPDATE: 0.70,
    },
    CIFDefense.TRUST_CALCULUS: {
        ADPhase.PLAN: 0.30,
        ADPhase.DELEGATE: 0.95,
        ADPhase.EXECUTE: 0.20,
        ADPhase.OBSERVE: 0.10,
        ADPhase.UPDATE: 0.20,
    },
    CIFDefense.TRIPWIRES_INVARIANTS: {
        ADPhase.PLAN: 0.90,
        ADPhase.DELEGATE: 0.20,
        ADPhase.EXECUTE: 0.80,
        ADPhase.OBSERVE: 0.40,
        ADPhase.UPDATE: 0.60,
    },
    CIFDefense.BYZANTINE_CONSENSUS: {
        ADPhase.PLAN: 0.20,
        ADPhase.DELEGATE: 0.70,
        ADPhase.EXECUTE: 0.90,
        ADPhase.OBSERVE: 0.30,
        ADPhase.UPDATE: 0.50,
    },
}

# Coverage threshold: minimum required coverage for any AD phase
MIN_PHASE_COVERAGE: float = 0.50


@dataclass
class CouplingAnalysis:
    """Result of CIF-AD coupling analysis for a defense portfolio."""

    portfolio: List[CIFDefense]
    phase_coverage: Dict[str, float]
    max_phase_coverage: Dict[str, float]
    full_coverage_achieved: bool
    coverage_gaps: List[str]
    total_coverage_score: float
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            "portfolio": [d.value for d in self.portfolio],
            "phase_coverage": self.phase_coverage,
            "max_phase_coverage": self.max_phase_coverage,
            "full_coverage_achieved": self.full_coverage_achieved,
            "coverage_gaps": self.coverage_gaps,
            "total_coverage_score": self.total_coverage_score,
            "recommendations": self.recommendations,
        }


@dataclass
class AttackSurfaceMapping:
    """Maps AD phases to their primary attack types and CIF defenses."""

    phase: ADPhase
    attack_surface: str
    primary_defense: CIFDefense
    formal_guarantee: str
    coverage_score: float


# Formal guarantee strings from manuscript Table (AD cycle phases)
AD_FORMAL_GUARANTEES: Dict[ADPhase, Tuple[str, str, str]] = {
    ADPhase.PLAN: ("Goal injection", "Invariant enforcement", "G_i ⊆ G_principal"),
    ADPhase.DELEGATE: ("Trust exploitation", "Trust calculus", "T^del ≤ δ^d"),
    ADPhase.EXECUTE: ("Result tampering", "Provenance tracking", "V(π(φ)) = 1"),
    ADPhase.OBSERVE: ("Evidence fabrication", "Belief sandbox", "B_prov isolation"),
    ADPhase.UPDATE: ("Drift induction", "KL drift detection", "D_KL < θ_drift"),
}


class CIFADCouplingDetector:
    """
    CIF-AD coupling detector and coverage analyzer.

    Computes the coverage matrix between CIF defenses and AD phases,
    identifies coverage gaps, and recommends defense portfolios.

    Reference: CIF v2.0, §4 (CIF-AD Integration), Definition 4.3 (CIF-AD Coupling Matrix).
    """

    def __init__(
        self,
        coupling_matrix: Optional[Dict[CIFDefense, Dict[ADPhase, float]]] = None,
        min_coverage: float = MIN_PHASE_COVERAGE,
    ) -> None:
        """
        Initialize CIF-AD coupling detector.

        Args:
            coupling_matrix: Custom coupling matrix (uses default if None).
            min_coverage: Minimum per-phase coverage required (τ_cov in manuscript).
        """
        self.coupling_matrix = coupling_matrix or CIF_AD_COUPLING_MATRIX
        self.min_coverage = min_coverage
        self._matrix_array = self._build_matrix_array()

    def _build_matrix_array(self) -> np.ndarray:
        """Build numpy array from coupling matrix for vectorized operations."""
        defenses = list(CIFDefense)
        phases = list(ADPhase)
        arr = np.zeros((len(defenses), len(phases)))
        for i, defense in enumerate(defenses):
            for j, phase in enumerate(phases):
                arr[i, j] = self.coupling_matrix.get(defense, {}).get(phase, 0.0)
        return arr

    def get_phase_coverage(
        self, phase: ADPhase, portfolio: Optional[List[CIFDefense]] = None
    ) -> float:
        """
        Compute maximum coverage for an AD phase with a given defense portfolio.

        The coverage is max_i M[defense_i, phase], since the best defense for
        that phase dominates.

        Args:
            phase: AD phase to compute coverage for.
            portfolio: Defense portfolio (uses all defenses if None).

        Returns:
            Coverage score in [0, 1].
        """
        # `portfolio or ...` would silently treat an explicit empty list as
        # "use the full stack" -- an empty portfolio has zero defenses and
        # must report zero coverage, not the full-stack maximum.
        defenses = list(CIFDefense) if portfolio is None else portfolio
        if not defenses:
            return 0.0
        return max(self.coupling_matrix.get(d, {}).get(phase, 0.0) for d in defenses)

    def get_combined_coverage(
        self, phase: ADPhase, portfolio: Optional[List[CIFDefense]] = None
    ) -> float:
        """
        Compute combined coverage using the product formula (parallel composition).

        P_detect = 1 - prod(1 - r_i) for defenses with non-zero coverage.

        Args:
            phase: AD phase to analyze.
            portfolio: Defense portfolio. Uses all defenses if None; empty list returns 0.

        Returns:
            Combined coverage probability in [0, 1].
        """
        if portfolio is None:
            defenses = list(CIFDefense)
        else:
            defenses = portfolio

        if not defenses:
            return 0.0

        scores = [self.coupling_matrix.get(d, {}).get(phase, 0.0) for d in defenses]
        # Filter non-zero scores (defenses with some coverage)
        active = [s for s in scores if s > 0.0]
        if not active:
            return 0.0
        product = 1.0
        for s in active:
            product *= 1.0 - s
        return 1.0 - product

    def analyze_portfolio(self, portfolio: Optional[List[CIFDefense]] = None) -> CouplingAnalysis:
        """
        Analyze a defense portfolio's CIF-AD coverage.

        Args:
            portfolio: List of deployed defenses. Uses full stack if None;
                      empty list returns zero coverage for all phases.

        Returns:
            CouplingAnalysis with per-phase coverage, gaps, and recommendations.
        """
        if portfolio is None:
            portfolio = list(CIFDefense)
        phases = list(ADPhase)

        phase_coverage = {}
        max_phase_coverage = {}
        coverage_gaps = []
        recommendations = []

        for phase in phases:
            max_cov = self.get_phase_coverage(phase, portfolio)
            combined_cov = self.get_combined_coverage(phase, portfolio)
            phase_coverage[phase.value] = combined_cov
            max_phase_coverage[phase.value] = max_cov

            if max_cov < self.min_coverage:
                coverage_gaps.append(phase.value)
                # Find best defense not in portfolio
                missing_defenses = [d for d in CIFDefense if d not in portfolio]
                best_missing = max(
                    missing_defenses,
                    key=lambda d: self.coupling_matrix.get(d, {}).get(phase, 0.0),
                    default=None,
                )
                if best_missing:
                    gain = self.coupling_matrix.get(best_missing, {}).get(phase, 0.0)
                    recommendations.append(
                        f"Phase '{phase.value}' coverage {max_cov:.2f} < {self.min_coverage}. "
                        f"Add {best_missing.value} (coverage: {gain:.2f})"
                    )

        total_coverage = float(np.mean(list(phase_coverage.values())))
        full_coverage = len(coverage_gaps) == 0

        return CouplingAnalysis(
            portfolio=portfolio,
            phase_coverage=phase_coverage,
            max_phase_coverage=max_phase_coverage,
            full_coverage_achieved=full_coverage,
            coverage_gaps=coverage_gaps,
            total_coverage_score=total_coverage,
            recommendations=recommendations,
        )

    def verify_full_coverage_theorem(self) -> bool:
        """
        Verify the CIF-AD Full Coverage Theorem (Theorem 4.5 in manuscript):
        ∀j: max_i M[defense_i, phase_j] > τ_cov.

        Returns:
            True if the theorem holds for the current coupling matrix.
        """
        for phase in ADPhase:
            max_cov = self.get_phase_coverage(phase)
            if max_cov < self.min_coverage:
                return False
        return True

    def get_attack_surface_mappings(self) -> List[AttackSurfaceMapping]:
        """
        Return per-phase attack surface mappings with formal guarantees.

        Returns:
            List of AttackSurfaceMapping for each AD phase.
        """
        mappings = []
        for phase in ADPhase:
            attack_surface, primary_defense_name, guarantee = AD_FORMAL_GUARANTEES[phase]
            # Find best CIF defense for this phase
            best_defense = max(
                CIFDefense,
                key=lambda d: self.coupling_matrix.get(d, {}).get(phase, 0.0),
            )
            coverage = self.coupling_matrix.get(best_defense, {}).get(phase, 0.0)
            mappings.append(
                AttackSurfaceMapping(
                    phase=phase,
                    attack_surface=attack_surface,
                    primary_defense=best_defense,
                    formal_guarantee=guarantee,
                    coverage_score=coverage,
                )
            )
        return mappings

    def minimum_viable_portfolio(
        self, min_phase_coverage: Optional[float] = None
    ) -> List[CIFDefense]:
        """
        Compute the minimum defense portfolio that achieves required coverage.

        Uses a greedy set-cover algorithm: iteratively add the defense that most
        improves the worst-covered phase.

        Args:
            min_phase_coverage: Minimum per-phase coverage required.

        Returns:
            Minimum defense portfolio as list of CIFDefense.
        """
        threshold = min_phase_coverage or self.min_coverage
        portfolio: List[CIFDefense] = []
        remaining_defenses = list(CIFDefense)

        def _is_sufficient(port: List[CIFDefense]) -> bool:
            """Check if portfolio achieves threshold for all phases."""
            for phase in ADPhase:
                if self.get_phase_coverage(phase, port) < threshold:
                    return False
            return True

        while remaining_defenses and not _is_sufficient(portfolio):
            # Greedy: add defense that most improves the worst-covered phase
            best_defense = None
            best_improvement = -1.0

            for defense in remaining_defenses:
                candidate = portfolio + [defense]
                # Improvement = increase in minimum column coverage
                before = min(
                    (self.get_phase_coverage(p, portfolio) for p in ADPhase),
                    default=0.0,
                )
                after = min(self.get_phase_coverage(p, candidate) for p in ADPhase)
                improvement = after - before
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_defense = defense

            if best_defense is None:
                break

            portfolio.append(best_defense)
            remaining_defenses.remove(best_defense)

        return portfolio

    def coverage_heatmap_data(self) -> Tuple[List[str], List[str], np.ndarray]:
        """
        Return data for generating a CIF-AD coupling heatmap visualization.

        Returns:
            Tuple of (defense names, phase names, coverage matrix array).
        """
        defenses = list(CIFDefense)
        phases = list(ADPhase)
        defense_names = [d.value for d in defenses]
        phase_names = [p.value for p in phases]
        matrix = np.zeros((len(defenses), len(phases)))
        for i, defense in enumerate(defenses):
            for j, phase in enumerate(phases):
                matrix[i, j] = self.coupling_matrix.get(defense, {}).get(phase, 0.0)
        return defense_names, phase_names, matrix

    def get_coupling_matrix_as_array(self) -> np.ndarray:
        """
        Return the coupling matrix as a numpy array.

        Rows = defenses (CIFDefense enum order), Columns = phases (ADPhase order).

        Returns:
            (5 x 5) numpy array.
        """
        return self._matrix_array.copy()

    def defense_overlap_analysis(self) -> Dict[str, float]:
        """
        Analyze overlap between defense mechanisms across all AD phases.

        Returns:
            Dict mapping defense pair strings to their coverage overlap score.
        """
        defenses = list(CIFDefense)
        phases = list(ADPhase)
        overlaps: Dict[str, float] = {}

        for i in range(len(defenses)):
            for j in range(i + 1, len(defenses)):
                d1, d2 = defenses[i], defenses[j]
                shared_coverage = sum(
                    min(
                        self.coupling_matrix.get(d1, {}).get(p, 0.0),
                        self.coupling_matrix.get(d2, {}).get(p, 0.0),
                    )
                    for p in phases
                ) / len(phases)
                key = f"{d1.value}|{d2.value}"
                overlaps[key] = shared_coverage

        return overlaps

    def __repr__(self) -> str:
        defenses = list(CIFDefense)
        phases = list(ADPhase)
        lines = ["CIF-AD Coupling Matrix:"]
        header = f"{'Defense':<30}" + "".join(f"{p.value[:8]:>10}" for p in phases)
        lines.append(header)
        lines.append("-" * (30 + 10 * len(phases)))
        for defense in defenses:
            row = f"{defense.value:<30}"
            for phase in phases:
                val = self.coupling_matrix.get(defense, {}).get(phase, 0.0)
                row += f"{val:>10.2f}"
            lines.append(row)
        return "\n".join(lines)
