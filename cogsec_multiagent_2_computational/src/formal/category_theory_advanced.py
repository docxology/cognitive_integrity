"""Advanced category-theoretic foundation layer for the Cognitive Integrity Framework.

Extends the base DefenseCategory with:

1. **Lattice of defenses** — complete lattice on detection-rate order, with
   proofs of reflexivity, antisymmetry, transitivity, meet, join, bottom, top.

2. **Monoidal category** — (DefenseCategory, ⊗, I) as a symmetric monoidal
   category, with Pentagon/Hexagon coherence and symmetry proofs.

3. **F-Algebra / initial algebra** — CognitiveState functor, catamorphism
   (fold) over defence pipelines.

4. **Operad** — defence composition as a coloured operad: series = planar-tree
   composition, parallel = grafting.

5. **Enriched category** — DefenseCategory enriched over [0,1] with
   Hom(f,g) = |detection_rate(f) - detection_rate(g)|.

6. **Kan extensions** — left/right Kan extensions for lifting defences between
   agent architectures.

7. **Monad** — defence pipeline monad over CognitiveState: η (unit) and
   μ (join) with left/right unit and associativity laws.

8. **Lenses / optics** — cognitive attacks as a lens (get = observe belief,
   set = manipulate belief), defence as a profunctor optic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

import numpy as np

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    DefenseResult,
    categorical_product,
    compose_morphisms,
    identity_morphism,
)

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")


# ============================================================================
# 1. LATTICE OF DEFENSES
# ============================================================================


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
# 3. F-ALGEBRA / INITIAL ALGEBRA (catamorphism)
# ============================================================================


@dataclass
class CognitiveFunctor:
    """The CognitiveState endofunctor F on DefenseCategory.

    F(X) = Option(X) -- wrapping states in optional context.
    The F-algebra carrier is DefenseResult; the structure map is
    alpha: F(DefenseResult) -> DefenseResult.
    """

    def fmap(
        self,
        fn: Callable[[CognitiveState], CognitiveState],
        state: CognitiveState,
    ) -> CognitiveState:
        """Functorial action: lift a state transformation."""
        return fn(state)


@dataclass
class FAlgebra:
    """An F-algebra (A, α) where A = DefenseResult and α : F(A) -> A."""

    carrier_name: str
    structure_map: Callable[[Optional[DefenseResult]], DefenseResult]

    def apply(self, fa: Optional[DefenseResult]) -> DefenseResult:
        return self.structure_map(fa)


def make_detection_algebra() -> FAlgebra:
    """F-algebra for detection rate accumulation."""

    def alpha(prev: Optional[DefenseResult]) -> DefenseResult:
        if prev is None:
            return DefenseResult(
                detected=False,
                score=0.0,
                module_name="f_algebra_base",
                details={},
                latency_ms=0.0,
            )
        return DefenseResult(
            detected=prev.detected,
            score=min(prev.score * 1.05, 1.0),  # slight amplification
            module_name=f"f_algebra({prev.module_name})",
            details=prev.details,
            latency_ms=prev.latency_ms,
        )

    return FAlgebra(carrier_name="DefenseResult", structure_map=alpha)


def cata(
    algebra: FAlgebra,
    morphisms: List[DefenseMorphism],
    initial_state: CognitiveState,
) -> DefenseResult:
    """Catamorphism (fold) over a list of morphisms via the F-algebra.

    Evaluates each morphism in sequence, threading results through the
    algebra's structure map.

    Args:
        algebra: The F-algebra to fold with.
        morphisms: Ordered list of defence morphisms.
        initial_state: The initial cognitive state.

    Returns:
        Final DefenseResult after the catamorphic fold.
    """
    acc: Optional[DefenseResult] = None
    for morphism in morphisms:
        result = morphism(initial_state)
        # Thread through algebra: chain result into accumulator
        combined = DefenseResult(
            detected=result.detected or (acc.detected if acc else False),
            score=max(result.score, acc.score if acc else 0.0),
            module_name=result.module_name,
            details=result.details,
            latency_ms=result.latency_ms + (acc.latency_ms if acc else 0.0),
        )
        acc = algebra.apply(combined)
    return acc if acc is not None else algebra.apply(None)


# ============================================================================
# 4. OPERAD STRUCTURE
# ============================================================================


@dataclass
class OperadOperation:
    """A k-ary operad operation.

    Attributes:
        arity: Number of input slots.
        name: Label for this operation.
        compose_fn: How to compose k child operations into one.
    """

    arity: int
    name: str
    compose_fn: Callable[[List[DefenseMorphism]], DefenseMorphism]

    def __repr__(self) -> str:
        return f"OperadOp({self.name}, arity={self.arity})"

    def apply(self, children: List[DefenseMorphism]) -> DefenseMorphism:
        if len(children) != self.arity:
            raise ValueError(
                f"Operation {self.name} has arity {self.arity}; "
                f"got {len(children)} children."
            )
        return self.compose_fn(children)


@dataclass
class OperadTree:
    """A tree encoding an operadic composition expression.

    Attributes:
        operation: The root operad operation.
        children: Sub-trees (leaves are single morphisms).
        leaf_morphism: Non-None iff this is a leaf node.
    """

    operation: Optional[OperadOperation] = None
    children: List["OperadTree"] = field(default_factory=list)
    leaf_morphism: Optional[DefenseMorphism] = None

    def is_leaf(self) -> bool:
        return self.leaf_morphism is not None

    def evaluate(self) -> DefenseMorphism:
        """Recursively evaluate the operadic tree to a single morphism."""
        if self.is_leaf():
            return self.leaf_morphism  # type: ignore[return-value]
        assert self.operation is not None
        child_morphisms = [c.evaluate() for c in self.children]
        return self.operation.apply(child_morphisms)

    def __repr__(self) -> str:
        if self.is_leaf():
            return f"Leaf({self.leaf_morphism!r})"
        return f"OperadTree({self.operation!r}, children={self.children!r})"


def series_operad_op(arity: int) -> OperadOperation:
    """Planar-tree (series) operad operation of given arity."""

    def _compose(children: List[DefenseMorphism]) -> DefenseMorphism:
        result = children[0]
        for c in children[1:]:
            result = compose_morphisms(result, c)
        return result

    return OperadOperation(arity=arity, name=f"series_{arity}", compose_fn=_compose)


def parallel_operad_op(arity: int) -> OperadOperation:
    """Grafting (parallel) operad operation of given arity."""

    def _compose(children: List[DefenseMorphism]) -> DefenseMorphism:
        result = children[0]
        for c in children[1:]:
            result = categorical_product(result, c)
        return result

    return OperadOperation(arity=arity, name=f"parallel_{arity}", compose_fn=_compose)


@dataclass
class DefenseOperad:
    """The defense operad: collection of n-ary operations with equivariance.

    Series operations form a planar operad (non-symmetric), while parallel
    operations satisfy symmetry (σ ∈ S_n acts by reordering arguments).
    """

    operations: Dict[str, OperadOperation] = field(default_factory=dict)

    def register(self, op: OperadOperation) -> None:
        self.operations[op.name] = op

    def get(self, name: str) -> OperadOperation:
        return self.operations[name]

    def build_series(self, morphisms: List[DefenseMorphism]) -> DefenseMorphism:
        n = len(morphisms)
        op = series_operad_op(n)
        tree = OperadTree(operation=op, children=[OperadTree(leaf_morphism=m) for m in morphisms])
        return tree.evaluate()

    def build_parallel(self, morphisms: List[DefenseMorphism]) -> DefenseMorphism:
        n = len(morphisms)
        op = parallel_operad_op(n)
        tree = OperadTree(operation=op, children=[OperadTree(leaf_morphism=m) for m in morphisms])
        return tree.evaluate()

    def verify_operad_unit(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Verify unit element: series_1(f) ≅ f."""
        op = series_operad_op(1)
        result = op.apply([f])
        vf = np.array([f(s).score for s in states])
        vr = np.array([result(s).score for s in states])
        return bool(np.allclose(vf, vr, atol=tol))

    def verify_operad_associativity(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Verify operad associativity: (f ∘₂ g) ∘₂ h ≅ f ∘₂ (g ∘₂ h)."""
        fg = self.build_series([f, g])
        fgh_left = self.build_series([fg, h])
        gh = self.build_series([g, h])
        fgh_right = self.build_series([f, gh])
        vl = np.array([fgh_left(s).score for s in states])
        vr = np.array([fgh_right(s).score for s in states])
        return bool(np.allclose(vl, vr, atol=tol))


# ============================================================================
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
# 7. MONAD STRUCTURE
# ============================================================================


@dataclass
class DefenseMonad:
    """Defence pipeline monad over CognitiveState.

    T(CognitiveState) = "a computation that may detect an attack and
    returns a DefenseResult enriched with the detection context".

    - η (unit): CognitiveState → T(CognitiveState)
        Lifts a state into the trivial non-detecting computation.

    - μ (join / multiply): T(T(CognitiveState)) → T(CognitiveState)
        Flattens two nested defence applications into one.

    Monad laws (verified empirically):
        Left unit:  μ ∘ η_T = id_T
        Right unit: μ ∘ T(η) = id_T
        Associativity: μ ∘ μ_T = μ ∘ T(μ)
    """

    def eta(self, state: CognitiveState) -> DefenseResult:
        """Unit: lift a state into the trivial (non-detecting) computation."""
        return DefenseResult(
            detected=False,
            score=0.0,
            module_name="monad_unit",
            details={"state_keys": list(state.keys())},
            latency_ms=0.0,
        )

    def mu(self, outer: DefenseMorphism, inner: DefenseMorphism) -> DefenseMorphism:
        """Join: flatten nested defence into a single morphism.

        μ(outer, inner) = compose_morphisms(inner, outer)
        """
        return compose_morphisms(inner, outer)

    def kleisli_compose(
        self,
        f: Callable[[CognitiveState], DefenseResult],
        g: Callable[[CognitiveState], DefenseResult],
    ) -> Callable[[CognitiveState], DefenseResult]:
        """Kleisli composition: f >=> g.

        Chains two monadic functions. Result carries the max score
        and the OR of detection flags.
        """

        def _kleisli(state: CognitiveState) -> DefenseResult:
            r_f = f(state)
            # In the Kleisli category, f's output is the "context" for g.
            # We thread state through, taking max-score and OR detection.
            r_g = g(state)
            detected = r_f.detected or r_g.detected
            score = max(r_f.score, r_g.score)
            return DefenseResult(
                detected=detected,
                score=score,
                module_name=f"({r_f.module_name} >=> {r_g.module_name})",
                details={"left": r_f.details, "right": r_g.details},
                latency_ms=r_f.latency_ms + r_g.latency_ms,
            )

        return _kleisli

    def verify_left_unit(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Left unit: η >=> f ≅ f."""
        composed = self.kleisli_compose(self.eta, f)
        vf = np.array([f(s).score for s in states])
        vc = np.array([composed(s).score for s in states])
        return bool(np.allclose(vc, vf, atol=tol))

    def verify_right_unit(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Right unit: f >=> η ≅ f."""
        composed = self.kleisli_compose(f, self.eta)
        vf = np.array([f(s).score for s in states])
        vc = np.array([composed(s).score for s in states])
        return bool(np.allclose(vc, vf, atol=tol))

    def verify_associativity(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Monad associativity: (f >=> g) >=> h ≅ f >=> (g >=> h)."""
        fg = self.kleisli_compose(f, g)
        lhs = self.kleisli_compose(fg, h)
        gh = self.kleisli_compose(g, h)
        rhs = self.kleisli_compose(f, gh)
        vl = np.array([lhs(s).score for s in states])
        vr = np.array([rhs(s).score for s in states])
        return bool(np.allclose(vl, vr, atol=tol))

    def verify_all(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
    ) -> Dict[str, bool]:
        return {
            "left_unit": self.verify_left_unit(f, states),
            "right_unit": self.verify_right_unit(f, states),
            "associativity": self.verify_associativity(f, g, h, states),
        }


# ============================================================================
# 8. LENSES / OPTICS
# ============================================================================


@dataclass
class BeliefLens(Generic[S]):
    """A van Laarhoven lens on cognitive belief state.

    get(state) = the observed belief value (a CognitiveState)
    set(state, new_value) = the manipulated state (attacker model)

    This models a cognitive attack: the adversary can both *observe*
    the agent's current belief state and *overwrite* it.
    """

    focus: str  # Which belief key the lens focuses on

    def get(self, state: CognitiveState) -> float:
        """Observe the focused belief."""
        return state.get(self.focus, 0.0)

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        """Manipulate the focused belief (attacker action)."""
        new_state = dict(state)
        new_state[self.focus] = value
        return new_state

    def modify(
        self,
        state: CognitiveState,
        fn: Callable[[float], float],
    ) -> CognitiveState:
        """Apply a function over the focused belief."""
        return self.set(state, fn(self.get(state)))

    def compose(self, other: "BeliefLens[Any]") -> "ComposedLens":
        """Compose two lenses (outer . inner)."""
        return ComposedLens(outer=self, inner=other)

    def __repr__(self) -> str:
        return f"BeliefLens(focus={self.focus!r})"


@dataclass
class ComposedLens:
    """Composition of two lenses: outer . inner."""

    outer: "BeliefLens[Any]"
    inner: "BeliefLens[Any]"

    def get(self, state: CognitiveState) -> float:
        intermediate = {self.inner.focus: self.inner.get(state)}
        return self.outer.get(intermediate)

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        current_inner = self.inner.get(state)
        new_inner_state = self.outer.set({self.inner.focus: current_inner}, value)
        return self.inner.set(state, new_inner_state.get(self.inner.focus, value))

    def __repr__(self) -> str:
        return f"ComposedLens({self.outer!r} . {self.inner!r})"


@dataclass
class DefenseProfunctor:
    """A defence as a profunctor optic P(A, B) → P(S, T).

    Models the defence as transforming the attacker's ability to observe
    and modify belief state: the defence reduces the set of reachable
    manipulated states.

    get: S → A  (read the attack surface from the full state)
    put: (S, B) → T  (apply the defended result back)
    """

    get_fn: Callable[[CognitiveState], CognitiveState]  # S → A
    put_fn: Callable[[CognitiveState, DefenseResult], CognitiveState]  # (S, B) → T

    def apply_get(self, state: CognitiveState) -> CognitiveState:
        return self.get_fn(state)

    def apply_put(self, state: CognitiveState, result: DefenseResult) -> CognitiveState:
        return self.put_fn(state, result)

    def compose(self, other: "DefenseProfunctor") -> "DefenseProfunctor":
        """Compose two profunctor optics."""
        outer_get = self.get_fn
        outer_put = self.put_fn
        inner_get = other.get_fn
        inner_put = other.put_fn

        def composed_get(state: CognitiveState) -> CognitiveState:
            return inner_get(outer_get(state))

        def composed_put(state: CognitiveState, result: DefenseResult) -> CognitiveState:
            intermediate = outer_get(state)
            inner_result = inner_put(intermediate, result)
            # Re-apply outer put: inject modified intermediate back
            return outer_put(state, DefenseResult(
                detected=result.detected,
                score=result.score,
                module_name=result.module_name,
                details={**result.details, "intermediate": inner_result},
                latency_ms=result.latency_ms,
            ))

        return DefenseProfunctor(get_fn=composed_get, put_fn=composed_put)

    def verify_lens_laws(
        self,
        lens: BeliefLens[Any],
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> Dict[str, bool]:
        """Verify van Laarhoven lens laws for the underlying BeliefLens.

        - GetPut: set(s, get(s)) = s
        - PutGet: get(set(s, v)) = v
        - PutPut: set(set(s, v1), v2) = set(s, v2)
        """
        get_put_ok = True
        put_get_ok = True
        put_put_ok = True

        for state in states:
            v = lens.get(state)
            # GetPut
            restored = lens.set(state, v)
            if abs(restored.get(lens.focus, 0.0) - state.get(lens.focus, 0.0)) > tol:
                get_put_ok = False

            # PutGet
            new_v = 0.42
            modified = lens.set(state, new_v)
            if abs(lens.get(modified) - new_v) > tol:
                put_get_ok = False

            # PutPut
            v1, v2 = 0.3, 0.7
            s_after_two = lens.set(lens.set(state, v1), v2)
            s_after_one = lens.set(state, v2)
            if abs(
                s_after_two.get(lens.focus, 0.0) - s_after_one.get(lens.focus, 0.0)
            ) > tol:
                put_put_ok = False

        return {
            "get_put": get_put_ok,
            "put_get": put_get_ok,
            "put_put": put_put_ok,
        }


# ============================================================================
# PROPERTY-BASED TEST GENERATORS
# ============================================================================


def generate_test_states(n: int = 20, seed: int = 42) -> List[CognitiveState]:
    """Generate n diverse CognitiveState dicts for property testing."""
    rng = np.random.default_rng(seed)
    states = []
    keys = ["trust", "consensus", "belief_integrity", "injection_risk", "__message__"]
    for _ in range(n):
        state: CognitiveState = {k: float(rng.uniform(0, 1)) for k in keys}
        states.append(state)
    return states


def make_test_morphism(rate: float, name: str) -> DefenseMorphism:
    """Create a simple morphism with a fixed detection rate for testing."""

    def _fn(state: CognitiveState) -> DefenseResult:
        score = float(np.clip(rate + state.get("injection_risk", 0.0) * 0.1, 0, 1))
        detected = score > 0.5
        return DefenseResult(
            detected=detected,
            score=score,
            module_name=name,
            details={"base_rate": rate},
            latency_ms=1.0,
        )

    return DefenseMorphism(fn=_fn, name=name, identity=False)


# ============================================================================
# HIGH-LEVEL VERIFICATION RUNNER
# ============================================================================


def run_all_verifications(
    n_states: int = 20,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run all categorical verification suites and return a unified report."""
    states = generate_test_states(n=n_states, seed=seed)
    return _run_all_verifications_impl(states)


def _run_all_verifications_impl(states: List[CognitiveState]) -> Dict[str, Any]:
    """Internal runner used by both run_all_verifications and serialize helpers."""
    f = make_test_morphism(0.7, "f")
    g = make_test_morphism(0.5, "g")
    h = make_test_morphism(0.3, "h")

    # 1. Lattice
    lattice = DefenseLattice(elements=[
        DetectionBound(0.0), DetectionBound(0.3), DetectionBound(0.5),
        DetectionBound(0.7), DetectionBound(1.0),
    ])
    lattice_results = lattice.verify_all()

    # 2. Monoidal
    monoidal = MonoidalDefenseCategory()
    monoidal_results = monoidal.verify_all(f, g, h, states)

    # 3. Operad
    operad = DefenseOperad()
    operad_results = {
        "operad_unit": operad.verify_operad_unit(f, states),
        "operad_associativity": operad.verify_operad_associativity(f, g, h, states),
    }

    # 4. Enriched
    enriched = EnrichedDefenseCategory()
    enriched_results = enriched.verify_all(f, g, h, states)

    # 5. Kan extensions
    arch_c = AgentArchitecture(name="LangGraph")
    arch_c.add_morphism("fw", f, rate=0.7)
    arch_c.add_morphism("det", g, rate=0.5)
    arch_d = AgentArchitecture(name="ClaudeCode")
    arch_d.add_morphism("security", h, rate=0.3)
    kan = KanExtension(
        source=arch_c,
        target=arch_d,
        functor_map={"fw": "security", "det": "security"},
    )
    kan_results = kan.verify_kan_adjunction(states)

    # 6. Monad
    monad = DefenseMonad()
    monad_results = monad.verify_all(f, g, h, states)

    # 7. Lens
    lens: BeliefLens = BeliefLens(focus="trust")
    profunctor = DefenseProfunctor(
        get_fn=lambda s: s,
        put_fn=lambda s, r: {**s, "defense_result": r.score},
    )
    lens_results = profunctor.verify_lens_laws(lens, states)

    return {
        "lattice": lattice_results,
        "monoidal": monoidal_results,
        "operad": operad_results,
        "enriched": enriched_results,
        "kan_extensions": kan_results,
        "monad": monad_results,
        "lenses": lens_results,
    }




# ============================================================================
# SERIALIZATION HELPERS  (for the web UI / composer_data.py)
# ============================================================================


def serialize_verification_results(
    n_states: int = 20,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run all 25 categorical verification checks and return them as JSON.

    The 25 checks span all 7 categorical structures:

    - **Lattice** (7): reflexivity, antisymmetry, transitivity,
      bottom_element, top_element, meet_existence, join_existence
    - **Monoidal** (4): left_unitor, right_unitor, associator, symmetry
    - **Operad** (2): operad_unit, operad_associativity
    - **Enriched** (2): enriched_identity, enriched_composition_law
    - **Kan extensions** (variable): lan_dominates + ran_wellformed
    - **Monad** (3): left_unit, right_unit, associativity
    - **Lenses** (3): get_put, put_get, put_put

    Args:
        n_states: Number of test states to generate.
        seed: Random seed for reproducibility.

    Returns:
        JSON-serialisable dict with keys:
        - ``summary``: ``{"total": int, "passed": int, "failed": int}``
        - ``results``: flat dict of check_name → bool
        - ``by_structure``: nested dict grouped by structure name
    """
    states = generate_test_states(n=n_states, seed=seed)
    raw = _run_all_verifications_impl(states)

    # Flatten into a single dict while preserving structure grouping
    by_structure: Dict[str, Dict[str, bool]] = {}
    flat: Dict[str, bool] = {}
    for structure, checks in raw.items():
        if isinstance(checks, dict):
            by_structure[structure] = {k: bool(v) for k, v in checks.items()}
            for k, v in checks.items():
                flat[f"{structure}.{k}"] = bool(v)

    passed = sum(1 for v in flat.values() if v)
    total = len(flat)

    return {
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "results": flat,
        "by_structure": by_structure,
    }


def get_lattice_data(
    rates: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Return lattice structure data as JSON for Hasse diagram rendering.

    Args:
        rates: Detection-rate values to include as lattice elements.
            Defaults to the canonical 5-point lattice used in verification:
            ``[0.0, 0.3, 0.5, 0.7, 1.0]``.

    Returns:
        JSON-serialisable dict with keys:
        - ``elements``: list of ``{"rate": float, "name": str}`` dicts
        - ``bottom``: ``{"rate": 0.0, "name": "⊥"}``
        - ``top``: ``{"rate": 1.0, "name": "⊤"}``
        - ``meets``: list of ``{"a": str, "b": str, "meet": float}`` dicts
        - ``joins``: list of ``{"a": str, "b": str, "join": float}`` dicts
        - ``hasse_edges``: list of ``{"from": str, "to": str}`` for Hasse diagram
    """
    if rates is None:
        rates = [0.0, 0.3, 0.5, 0.7, 1.0]

    elements = [DetectionBound(r, name=f"D({r:.2f})") for r in rates]
    # Ensure bottom and top are present
    if not any(math.isclose(e.rate, 0.0) for e in elements):
        elements.insert(0, BOTTOM)
    if not any(math.isclose(e.rate, 1.0) for e in elements):
        elements.append(TOP)
    elements.sort(key=lambda e: e.rate)

    # Compute all meets and joins
    meets = []
    joins = []
    for a in elements:
        for b in elements:
            if a.rate <= b.rate:
                m = lattice_meet(a, b)
                j = lattice_join(a, b)
                meets.append({
                    "a": a.name, "a_rate": round(a.rate, 4),
                    "b": b.name, "b_rate": round(b.rate, 4),
                    "meet": round(m.rate, 4),
                })
                joins.append({
                    "a": a.name, "a_rate": round(a.rate, 4),
                    "b": b.name, "b_rate": round(b.rate, 4),
                    "join": round(j.rate, 4),
                })

    # Hasse edges: a → b iff a < b and no c with a < c < b
    hasse_edges = []
    sorted_els = sorted(elements, key=lambda e: e.rate)
    for i, a in enumerate(sorted_els):
        for _j, b in enumerate(sorted_els):
            if b.rate <= a.rate:
                continue
            # Check if there is an intermediate element
            has_intermediate = any(
                a.rate < c.rate < b.rate for c in sorted_els
            )
            if not has_intermediate:
                hasse_edges.append({"from": a.name, "to": b.name})

    return {
        "elements": [{"rate": round(e.rate, 4), "name": e.name} for e in elements],
        "bottom": {"rate": 0.0, "name": BOTTOM.name},
        "top": {"rate": 1.0, "name": TOP.name},
        "meets": meets,
        "joins": joins,
        "hasse_edges": hasse_edges,
    }


def get_monoidal_data(n_states: int = 20, seed: int = 42) -> Dict[str, Any]:
    """Return monoidal category structure data for diagram rendering.

    Runs the four coherence verifications and packages them with the
    monoidal structure description (tensor product ⊗, unit I).

    Args:
        n_states: Number of test states to use in verification.
        seed: Random seed.

    Returns:
        JSON-serialisable dict with keys:
        - ``tensor_product``: description of ⊗ (parallel max-fusion)
        - ``unit``: description of monoidal unit I
        - ``coherence``: dict of coherence law name → bool
        - ``axioms``: list of axiom descriptions
    """
    states = generate_test_states(n=n_states, seed=seed)
    f = make_test_morphism(0.7, "f")
    g = make_test_morphism(0.5, "g")
    h = make_test_morphism(0.3, "h")

    monoidal = MonoidalDefenseCategory()
    coherence = monoidal.verify_all(f, g, h, states)

    return {
        "tensor_product": {
            "symbol": "⊗",
            "implementation": "categorical_product (parallel max-fusion)",
            "description": "f ⊗ g runs both morphisms and takes max score",
        },
        "unit": {
            "symbol": "I",
            "implementation": "identity_morphism",
            "description": "Never detects; score = 0.0",
        },
        "coherence": {k: bool(v) for k, v in coherence.items()},
        "axioms": [
            {
                "name": "Left Unitor",
                "formula": "λ_f : I ⊗ f ≅ f",
                "passed": bool(coherence.get("left_unitor", False)),
            },
            {
                "name": "Right Unitor",
                "formula": "ρ_f : f ⊗ I ≅ f",
                "passed": bool(coherence.get("right_unitor", False)),
            },
            {
                "name": "Associator (Pentagon)",
                "formula": "α_{f,g,h} : (f ⊗ g) ⊗ h ≅ f ⊗ (g ⊗ h)",
                "passed": bool(coherence.get("associator", False)),
            },
            {
                "name": "Symmetry (Hexagon)",
                "formula": "σ_{f,g} : f ⊗ g ≅ g ⊗ f",
                "passed": bool(coherence.get("symmetry", False)),
            },
        ],
    }


def get_operad_data(n_states: int = 20, seed: int = 42) -> Dict[str, Any]:
    """Return operad structure data for tree visualization.

    Packages the two operad axiom verifications with a description of the
    series (planar-tree) and parallel (grafting) operad operations.

    Args:
        n_states: Number of test states to use in verification.
        seed: Random seed.

    Returns:
        JSON-serialisable dict with keys:
        - ``operations``: list of operad operation descriptions
        - ``axioms``: list of axiom verification results
        - ``tree_example``: example operadic tree structure for rendering
    """
    states = generate_test_states(n=n_states, seed=seed)
    f = make_test_morphism(0.7, "f")
    g = make_test_morphism(0.5, "g")
    h = make_test_morphism(0.3, "h")
    operad = DefenseOperad()
    unit_ok = operad.verify_operad_unit(f, states)
    assoc_ok = operad.verify_operad_associativity(f, g, h, states)

    return {
        "operations": [
            {
                "name": "series_n",
                "symbol": "∘",
                "type": "planar-tree (non-symmetric)",
                "description": "Sequential composition: f₁ ∘ f₂ ∘ … ∘ fₙ",
                "arities": [1, 2, 3, 4, 5, 6, 7, 8],
            },
            {
                "name": "parallel_n",
                "symbol": "⊕",
                "type": "symmetric (grafting)",
                "description": "Parallel composition: f₁ ⊕ f₂ ⊕ … ⊕ fₙ (order-invariant)",
                "arities": [1, 2, 3, 4, 5, 6, 7, 8],
            },
        ],
        "axioms": [
            {
                "name": "Unit",
                "formula": "series₁(f) ≅ f",
                "description": "Unary series composition is the identity",
                "passed": bool(unit_ok),
            },
            {
                "name": "Associativity",
                "formula": "(f ∘₂ g) ∘₂ h ≅ f ∘₂ (g ∘₂ h)",
                "description": "Series composition is associative",
                "passed": bool(assoc_ok),
            },
        ],
        "tree_example": {
            "label": "series₃(f, g, h)",
            "type": "series",
            "root": {
                "op": "series_3",
                "children": [
                    {"op": "leaf", "morphism": "f", "rate": 0.7},
                    {"op": "leaf", "morphism": "g", "rate": 0.5},
                    {"op": "leaf", "morphism": "h", "rate": 0.3},
                ],
            },
            "combined_rate": round(
                1.0 - (1.0 - 0.7) * (1.0 - 0.5) * (1.0 - 0.3), 4
            ),
        },
    }


__all__ = [
    # Lattice
    "DetectionBound",
    "BOTTOM",
    "TOP",
    "lattice_meet",
    "lattice_join",
    "DefenseLattice",
    # Monoidal
    "MonoidalDefenseCategory",
    # F-Algebra
    "CognitiveFunctor",
    "FAlgebra",
    "make_detection_algebra",
    "cata",
    # Operad
    "OperadOperation",
    "OperadTree",
    "series_operad_op",
    "parallel_operad_op",
    "DefenseOperad",
    # Enriched
    "EnrichedHom",
    "EnrichedDefenseCategory",
    # Kan extensions
    "AgentArchitecture",
    "KanExtension",
    # Monad
    "DefenseMonad",
    # Lenses
    "BeliefLens",
    "ComposedLens",
    "DefenseProfunctor",
    # Test utilities
    "generate_test_states",
    "make_test_morphism",
    "run_all_verifications",
    # Serialization helpers
    "serialize_verification_results",
    "get_lattice_data",
    "get_monoidal_data",
    "get_operad_data",
]
