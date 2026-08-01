from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, TypeVar

import numpy as np

from formal.advanced.enriched import EnrichedDefenseCategory
from formal.advanced.kan import AgentArchitecture, KanExtension
from formal.advanced.lattice import (
    BOTTOM,
    TOP,
    DefenseLattice,
    DetectionBound,
    lattice_join,
    lattice_meet,
)
from formal.advanced.lenses import BeliefLens, DefenseProfunctor
from formal.advanced.monad import DefenseMonad
from formal.advanced.monoidal import MonoidalDefenseCategory
from formal.advanced.operad import DefenseOperad
from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    DefenseResult,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")


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
    - **Kan extensions** (variable): lan_dominates + ran_wellformed for
      multi-source targets, ran_dominated_by for single-source targets.
      The default configuration below maps two sources onto one target, so it
      emits ``lan_dominates_*`` and ``ran_wellformed_*`` only.
    - **Monad** (3): left_unit, right_unit, associativity
    - **Lenses** (3): get_put, put_get, put_put -- these are laws of the
      :class:`~formal.advanced.lenses.BeliefLens` argument; the
      :class:`~formal.advanced.lenses.DefenseProfunctor` receiver's own
      ``get_fn``/``put_fn`` are not part of these three flags.

    Not every flag is independently falsifiable for arbitrary inputs.  The
    seven lattice flags in particular are regression detectors over
    ``DetectionBound.__le__``/``lattice_meet``/``lattice_join`` rather than
    contingent facts: given the ``[0, 1]`` range enforced in
    ``DetectionBound.__post_init__``, no admissible element set makes them
    ``False``.  ``tests/test_category_theory_advanced.py::TestVerifierNegativeControls``
    pins, per structure, an input for which the verifier does report ``False``.

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

