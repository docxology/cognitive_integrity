from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, TypeVar

import numpy as np

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    categorical_product,
    identity_morphism,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 2. MONOIDAL CATEGORY STRUCTURE
# ============================================================================


@dataclass
class MonoidalDefenseCategory:
    """(DefenseCategory, ⊗, I) as a symmetric monoidal category.

    The tensor product ⊗ is ``categorical_product`` (parallel max-fusion),
    and the monoidal unit I is ``identity_morphism``.

    We verify the full set of monoidal coherence conditions:
      - Left/right unitor: λ_f : I ⊗ f ≅ f, ρ_f : f ⊗ I ≅ f
      - Associator: α_{f,g,h} : (f ⊗ g) ⊗ h ≅ f ⊗ (g ⊗ h)
      - Symmetry: σ_{f,g} : f ⊗ g ≅ g ⊗ f
    """

    def tensor(self, f: DefenseMorphism, g: DefenseMorphism) -> DefenseMorphism:
        """Monoidal product f ⊗ g (parallel max-fusion)."""
        return categorical_product(f, g)

    @property
    def unit(self) -> DefenseMorphism:
        """Monoidal unit I (identity morphism)."""
        return identity_morphism()

    # --- Coherence verification (empirical on test states) ---

    def _vec(self, m: DefenseMorphism, states: List[CognitiveState]) -> np.ndarray:
        return np.array([m(s).score for s in states])

    def verify_left_unitor(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """λ_f : I ⊗ f ≅ f  (left unitor)."""
        lhs = self.tensor(self.unit, f)
        return bool(np.allclose(self._vec(lhs, states), self._vec(f, states), atol=tol))

    def verify_right_unitor(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """ρ_f : f ⊗ I ≅ f  (right unitor)."""
        rhs = self.tensor(f, self.unit)
        return bool(np.allclose(self._vec(rhs, states), self._vec(f, states), atol=tol))

    def verify_associator(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """α_{f,g,h} : (f ⊗ g) ⊗ h ≅ f ⊗ (g ⊗ h)  (Hexagon/Pentagon identity)."""
        lhs = self.tensor(self.tensor(f, g), h)
        rhs = self.tensor(f, self.tensor(g, h))
        return bool(np.allclose(self._vec(lhs, states), self._vec(rhs, states), atol=tol))

    def verify_symmetry(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """σ_{f,g} : f ⊗ g ≅ g ⊗ f  (symmetry/braiding)."""
        lhs = self.tensor(f, g)
        rhs = self.tensor(g, f)
        return bool(np.allclose(self._vec(lhs, states), self._vec(rhs, states), atol=tol))

    def verify_all(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
    ) -> Dict[str, bool]:
        return {
            "left_unitor": self.verify_left_unitor(f, states),
            "right_unitor": self.verify_right_unitor(f, states),
            "associator": self.verify_associator(f, g, h, states),
            "symmetry": self.verify_symmetry(f, g, states),
        }


# ============================================================================
