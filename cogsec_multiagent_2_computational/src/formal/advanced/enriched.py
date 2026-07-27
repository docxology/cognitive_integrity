from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TypeVar

import numpy as np

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 5. ENRICHED CATEGORY
# ============================================================================


@dataclass
class EnrichedHom:
    """Hom-object in [0,1]-enriched DefenseCategory.

    Hom(f, g) = |detection_rate(f) - detection_rate(g)|
    """

    morphism_f: DefenseMorphism
    morphism_g: DefenseMorphism
    _cached_value: Optional[float] = field(default=None, repr=False)

    def value(self, states: List[CognitiveState]) -> float:
        """Compute enriched hom-value on test states."""
        rate_f = float(np.mean([m.score for m in (self.morphism_f(s) for s in states)]))
        rate_g = float(np.mean([m.score for m in (self.morphism_g(s) for s in states)]))
        return abs(rate_f - rate_g)

    def __repr__(self) -> str:
        return f"EnrichedHom({self.morphism_f.name!r}, {self.morphism_g.name!r})"


@dataclass
class EnrichedDefenseCategory:
    """DefenseCategory enriched over the monoidal category ([0,1], ≤, 1, min).

    The enriched composition law:
      Hom(g,h) ⊗ Hom(f,g) → Hom(f,h)
    is implemented as:
      hom(g,h) + hom(f,g) ≥ hom(f,h)   (triangle inequality on [0,1])
    """

    def hom(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        states: List[CognitiveState],
    ) -> float:
        """Compute Hom(f,g) = |rate(f) - rate(g)|."""
        def rate(m):
            return float(np.mean([m(s).score for s in states]))
        return abs(rate(f) - rate(g))

    def verify_enriched_composition_law(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
    ) -> bool:
        """Hom(g,h) + Hom(f,g) ≥ Hom(f,h) — triangle inequality."""
        hfg = self.hom(f, g, states)
        hgh = self.hom(g, h, states)
        hfh = self.hom(f, h, states)
        return bool(hfg + hgh >= hfh - 1e-10)

    def verify_enriched_identity(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
    ) -> bool:
        """Hom(f,f) = 0 — enriched identity."""
        return math.isclose(self.hom(f, f, states), 0.0, abs_tol=1e-10)

    def verify_all(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
    ) -> Dict[str, bool]:
        return {
            "enriched_identity": self.verify_enriched_identity(f, states),
            "enriched_composition_law": self.verify_enriched_composition_law(f, g, h, states),
        }


# ============================================================================
