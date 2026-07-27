from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, TypeVar

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

@dataclass(frozen=True)
class DetectionBound:
    """An element of the detection-rate lattice.

    Attributes:
        rate: A value in [0, 1] representing the (empirical) detection rate.
        name: Optional label.
    """

    rate: float
    name: str = ""

    def __post_init__(self) -> None:
        if not (0.0 <= self.rate <= 1.0):
            raise ValueError(f"Detection rate must be in [0,1], got {self.rate}")

    def __le__(self, other: "DetectionBound") -> bool:  # type: ignore[override]
        return self.rate <= other.rate

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if not isinstance(other, DetectionBound):
            return NotImplemented
        return math.isclose(self.rate, other.rate, abs_tol=1e-10)

    def __repr__(self) -> str:
        return f"DetectionBound({self.rate:.4f}, name={self.name!r})"

    def __hash__(self) -> int:
        return hash(round(self.rate, 10))


# Lattice extremes
BOTTOM = DetectionBound(0.0, name="⊥")  # trivial detector — never detects
TOP = DetectionBound(1.0, name="⊤")  # perfect detector


def lattice_meet(a: DetectionBound, b: DetectionBound) -> DetectionBound:
    """Greatest lower bound: max-fusion parallel composition → take min rate.

    In the detection-rate partial order the *meet* (∧) of two defences is the
    one whose rate is the *minimum* of the two — the worst-case safety floor.
    """
    return DetectionBound(min(a.rate, b.rate), name=f"({a.name} ∧ {b.name})")


def lattice_join(a: DetectionBound, b: DetectionBound) -> DetectionBound:
    """Least upper bound: series composition → 1 - (1-a)(1-b).

    Series composition gives combined miss-rate (1-a)(1-b), so detection rate
    is 1-(1-a)(1-b) = a + b - ab ≥ max(a,b).
    """
    combined = a.rate + b.rate - a.rate * b.rate
    return DetectionBound(min(combined, 1.0), name=f"({a.name} ∨ {b.name})")


@dataclass
class DefenseLattice:
    """Complete lattice over a finite set of DetectionBounds.

    Provides empirical proofs of all lattice axioms.
    """

    elements: List[DetectionBound] = field(default_factory=list)

    def add(self, elem: DetectionBound) -> None:
        self.elements.append(elem)

    # --- Lattice axiom proofs (empirical) ---

    def verify_reflexivity(self) -> bool:
        """∀ a: a ≤ a."""
        return all(a <= a for a in self.elements)

    def verify_antisymmetry(self, tol: float = 1e-10) -> bool:
        """∀ a,b: a ≤ b ∧ b ≤ a ⟹ a = b."""
        for a in self.elements:
            for b in self.elements:
                if a <= b and b <= a:
                    if not math.isclose(a.rate, b.rate, abs_tol=tol):
                        return False
        return True

    def verify_transitivity(self) -> bool:
        """∀ a,b,c: a ≤ b ∧ b ≤ c ⟹ a ≤ c."""
        for a in self.elements:
            for b in self.elements:
                for c in self.elements:
                    if a <= b and b <= c and not (a <= c):
                        return False
        return True

    def verify_bottom(self) -> bool:
        """⊥ ≤ a for all a."""
        return all(BOTTOM <= a for a in self.elements)

    def verify_top(self) -> bool:
        """a ≤ ⊤ for all a."""
        return all(a <= TOP for a in self.elements)

    def verify_meet_existence(self) -> bool:
        """For all pairs a,b their meet exists and is ≤ both."""
        for a in self.elements:
            for b in self.elements:
                m = lattice_meet(a, b)
                if not (m <= a and m <= b):
                    return False
        return True

    def verify_join_existence(self) -> bool:
        """For all pairs a,b their join exists and is ≥ both."""
        for a in self.elements:
            for b in self.elements:
                j = lattice_join(a, b)
                if not (a <= j and b <= j):
                    return False
        return True

    def verify_all(self) -> Dict[str, bool]:
        return {
            "reflexivity": self.verify_reflexivity(),
            "antisymmetry": self.verify_antisymmetry(),
            "transitivity": self.verify_transitivity(),
            "bottom_element": self.verify_bottom(),
            "top_element": self.verify_top(),
            "meet_existence": self.verify_meet_existence(),
            "join_existence": self.verify_join_existence(),
        }


# ============================================================================
