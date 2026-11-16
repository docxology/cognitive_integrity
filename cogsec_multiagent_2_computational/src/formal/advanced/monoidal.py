from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar

import numpy as np

from src.formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    categorical_product,
    compose_morphisms,
    identity_morphism,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 2. MONOIDAL CATEGORY STRUCTURE
# ============================================================================


@dataclass
class MonoidalDefenseCategory:
    """Candidate monoidal structure using parallel max-fusion.

    The tensor product ⊗ is ``categorical_product`` and the candidate unit
    I is ``identity_morphism``.  Unit, associator and symmetry checks are
    available, but the required interchange law generally fails under
    short-circuit sequencing.  Consequently these checks do not establish
    that ``DefenseCategory`` is monoidal.
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
        return bool(np.allclose(self._vec(lhs, states), self._vec(f, states), atol=tol, rtol=0.0))

    def verify_right_unitor(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """ρ_f : f ⊗ I ≅ f  (right unitor)."""
        rhs = self.tensor(f, self.unit)
        return bool(np.allclose(self._vec(rhs, states), self._vec(f, states), atol=tol, rtol=0.0))

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
        return bool(np.allclose(self._vec(lhs, states), self._vec(rhs, states), atol=tol, rtol=0.0))

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
        return bool(np.allclose(self._vec(lhs, states), self._vec(rhs, states), atol=tol, rtol=0.0))

    def verify_interchange(
        self,
        f: DefenseMorphism,
        f_prime: DefenseMorphism,
        g: DefenseMorphism,
        g_prime: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Check ``(f;f′)⊗(g;g′) = (f⊗g);(f′⊗g′)``.

        Parallel max-fusion is compatible with the four coherence checks,
        but not generally with short-circuit sequencing.  This check must be
        reported rather than omitted when claiming a monoidal category.
        """
        lhs = self.tensor(compose_morphisms(f, f_prime), compose_morphisms(g, g_prime))
        rhs = compose_morphisms(self.tensor(f, g), self.tensor(f_prime, g_prime))
        return bool(
            np.allclose(self._vec(lhs, states), self._vec(rhs, states), atol=tol, rtol=0.0)
            and np.array_equal(
                np.array([lhs(s).detected for s in states]),
                np.array([rhs(s).detected for s in states]),
            )
        )

    def verify_all(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
        interchange_witnesses: Optional[
            tuple[DefenseMorphism, DefenseMorphism, DefenseMorphism, DefenseMorphism]
        ] = None,
    ) -> Dict[str, bool]:
        results = {
            "left_unitor": self.verify_left_unitor(f, states),
            "right_unitor": self.verify_right_unitor(f, states),
            "associator": self.verify_associator(f, g, h, states),
            "symmetry": self.verify_symmetry(f, g, states),
        }
        if interchange_witnesses is not None:
            results["interchange"] = self.verify_interchange(
                *interchange_witnesses, states
            )
        return results


# ============================================================================
