"""Advanced category-theoretic foundation layer for the Cognitive Integrity Framework.

Public API is re-exported from :mod:`src.formal.advanced` submodules so callers can
continue importing from ``src.formal.category_theory_advanced``.
"""

from __future__ import annotations

from src.formal.advanced.enriched import EnrichedDefenseCategory, EnrichedHom
from src.formal.advanced.f_algebra import CognitiveFunctor, FAlgebra, cata, make_detection_algebra
from src.formal.advanced.kan import AgentArchitecture, KanExtension
from src.formal.advanced.lattice import (
    BOTTOM,
    TOP,
    DefenseLattice,
    DetectionBound,
    lattice_join,
    lattice_meet,
)
from src.formal.advanced.lenses import BeliefLens, ComposedLens, DefenseProfunctor
from src.formal.advanced.monad import DefenseMonad
from src.formal.advanced.monoidal import MonoidalDefenseCategory
from src.formal.advanced.operad import (
    DefenseOperad,
    OperadOperation,
    OperadTree,
    parallel_operad_op,
    series_operad_op,
)
from src.formal.advanced.verification import (
    generate_test_states,
    get_lattice_data,
    get_monoidal_data,
    get_operad_data,
    make_test_morphism,
    run_all_verifications,
    serialize_verification_results,
)

__all__ = [
    "DetectionBound",
    "BOTTOM",
    "TOP",
    "lattice_meet",
    "lattice_join",
    "DefenseLattice",
    "MonoidalDefenseCategory",
    "CognitiveFunctor",
    "FAlgebra",
    "make_detection_algebra",
    "cata",
    "OperadOperation",
    "OperadTree",
    "series_operad_op",
    "parallel_operad_op",
    "DefenseOperad",
    "EnrichedHom",
    "EnrichedDefenseCategory",
    "AgentArchitecture",
    "KanExtension",
    "DefenseMonad",
    "BeliefLens",
    "ComposedLens",
    "DefenseProfunctor",
    "generate_test_states",
    "make_test_morphism",
    "run_all_verifications",
    "serialize_verification_results",
    "get_lattice_data",
    "get_monoidal_data",
    "get_operad_data",
]
