from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, TypeVar

import numpy as np

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    categorical_product,
    compose_morphisms,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

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
