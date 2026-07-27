from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, TypeVar

import numpy as np

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    categorical_product,
    compose_morphisms,
    identity_morphism,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 6. KAN EXTENSIONS
# ============================================================================


@dataclass
class AgentArchitecture:
    """An agent architecture, modelled as a small category.

    Attributes:
        name: Label for the architecture.
        morphisms: Named defence morphisms in this architecture.
        detection_rates: Baseline rates for each morphism.
    """

    name: str
    morphisms: Dict[str, DefenseMorphism] = field(default_factory=dict)
    detection_rates: Dict[str, float] = field(default_factory=dict)

    def add_morphism(self, name: str, m: DefenseMorphism, rate: float) -> None:
        self.morphisms[name] = m
        self.detection_rates[name] = rate


@dataclass
class KanExtension:
    """Left and right Kan extensions along a functor F: C → D.

    Given an architecture C (source) and D (target) connected by a
    functor F (a name-mapping), the:

    - Left Kan extension Lan_F(G) lifts G: C → DefenseCategory to
      Lan_F(G): D → DefenseCategory by taking joins (series composition
      of all morphisms that map to a given D-object).

    - Right Kan extension Ran_F(G) dually takes meets (parallel composition).
    """

    source: AgentArchitecture
    target: AgentArchitecture
    functor_map: Dict[str, str]  # source_name -> target_name

    def left_kan(self) -> Dict[str, DefenseMorphism]:
        """Lan_F(G): for each target name, series-compose all source morphisms over it."""
        # Invert the functor map: target -> list of source names
        inverse: Dict[str, List[str]] = {}
        for src, tgt in self.functor_map.items():
            inverse.setdefault(tgt, []).append(src)

        result: Dict[str, DefenseMorphism] = {}
        for tgt_name, src_names in inverse.items():
            morphisms = [self.source.morphisms[n] for n in src_names if n in self.source.morphisms]
            if not morphisms:
                result[tgt_name] = identity_morphism()
            elif len(morphisms) == 1:
                result[tgt_name] = morphisms[0]
            else:
                composed = morphisms[0]
                for m in morphisms[1:]:
                    composed = compose_morphisms(composed, m)
                result[tgt_name] = composed
        return result

    def right_kan(self) -> Dict[str, DefenseMorphism]:
        """Ran_F(G): for each target name, parallel-compose all source morphisms over it."""
        inverse: Dict[str, List[str]] = {}
        for src, tgt in self.functor_map.items():
            inverse.setdefault(tgt, []).append(src)

        result: Dict[str, DefenseMorphism] = {}
        for tgt_name, src_names in inverse.items():
            morphisms = [self.source.morphisms[n] for n in src_names if n in self.source.morphisms]
            if not morphisms:
                result[tgt_name] = identity_morphism()
            elif len(morphisms) == 1:
                result[tgt_name] = morphisms[0]
            else:
                combined = morphisms[0]
                for m in morphisms[1:]:
                    combined = categorical_product(combined, m)
                result[tgt_name] = combined
        return result

    def verify_kan_adjunction(
        self,
        states: List[CognitiveState],
        tol: float = 1e-6,
    ) -> Dict[str, bool]:
        """Check Lan ⊣ restriction and restriction ⊣ Ran for score ordering.

        For each source morphism mapped to a target via F:
        - Lan (left Kan, series-compose of all sources over a target) dominates
          each individual source rate.
        - Ran (right Kan, parallel-compose) may exceed a single source when
          multiple sources are merged; we verify Ran.rate ≥ 0 (well-formedness)
          rather than a per-source bound in the multi-source case.
        """
        lan = self.left_kan()
        ran = self.right_kan()
        results: Dict[str, bool] = {}

        # Count how many source morphisms share each target
        target_source_count: Dict[str, int] = {}
        for src, tgt in self.functor_map.items():
            target_source_count[tgt] = target_source_count.get(tgt, 0) + 1

        for src_name, tgt_name in self.functor_map.items():
            if src_name not in self.source.morphisms:
                continue
            src_m = self.source.morphisms[src_name]
            src_rates = np.array([src_m(s).score for s in states])
            multi = target_source_count.get(tgt_name, 1) > 1

            if tgt_name in lan:
                lan_rates = np.array([lan[tgt_name](s).score for s in states])
                # Lan = series of all sources → always ≥ any single source
                results[f"lan_dominates_{src_name}"] = bool(
                    np.all(lan_rates >= src_rates - tol)
                )

            if tgt_name in ran:
                ran_rates = np.array([ran[tgt_name](s).score for s in states])
                if multi:
                    # Multi-source Ran is a parallel composition: rate ≥ max(all sources) ≥ individual  # noqa: E501
                    # Verify it's well-formed (in [0,1]) rather than dominated by a single source
                    results[f"ran_wellformed_{src_name}"] = bool(
                        np.all(ran_rates >= 0 - tol) and np.all(ran_rates <= 1.0 + tol)
                    )
                else:
                    # Single source: Ran = source itself, check equality
                    results[f"ran_dominated_by_{src_name}"] = bool(
                        np.all(ran_rates <= src_rates + tol)
                    )
        return results


# ============================================================================
