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

        - ``lan_dominates_<src>``: Lan (left Kan, series composition of all
          sources over a target) dominates each individual source rate.  This
          is falsifiable: ``compose_morphisms`` short-circuits on detection, so
          a detecting low-score source in front of a non-detecting high-score
          source drives the composite *below* the latter.
        - ``ran_wellformed_<src>`` (multi-source targets): Ran is the parallel
          composition of the sources, i.e. a pointwise max, so it must both
          stay inside ``[0, 1]`` **and** dominate every source it merges.
          ``DefenseResult.score`` is not clipped at construction, so the range
          arm can genuinely fail; the dominance arm fails for any Ran that
          drops one of its sources (e.g. returning the identity morphism).
        - ``ran_dominated_by_<src>`` (single-source targets): Ran *is* the
          source, so equality is checked in both directions.  A one-sided
          ``ran <= src`` test would be satisfied by a Ran that silently
          collapsed to the identity morphism (score 0), which is the exact
          regression this arm exists to catch.
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
                    # Multi-source Ran is a parallel (max-fusion) composition:
                    # it must be well-formed *and* dominate every source it
                    # merges.  Range alone would be vacuous for a Ran that
                    # dropped a source; dominance alone would be vacuous for a
                    # Ran that returned an out-of-range score.
                    in_range = bool(
                        np.all(ran_rates >= 0.0 - tol) and np.all(ran_rates <= 1.0 + tol)
                    )
                    dominates = bool(np.all(ran_rates >= src_rates - tol))
                    results[f"ran_wellformed_{src_name}"] = in_range and dominates
                else:
                    # Single source: Ran *is* the source, so require equality in
                    # both directions (a one-sided <= would accept an identity
                    # morphism silently replacing the source).
                    results[f"ran_dominated_by_{src_name}"] = bool(
                        np.allclose(ran_rates, src_rates, atol=tol)
                    )
        return results


# ============================================================================
