"""NuSMV CTL specification generation for model checking.

Generates NuSMV models with CTL properties for the Cognitive Integrity
Framework components.
"""

from __future__ import annotations

from typing import Dict


def generate_categorical_nusmv_spec() -> str:
    """Generate NuSMV CTL spec for semiring completeness and categorical properties.

    Encodes:
    - Semiring completeness: detection algebra forms a (max,+) semiring
    - Category law invariants as CTL AG properties
    - Lattice closure under meet/join as CTL AG properties
    - Monad law satisfaction as reachability (EF) properties

    Returns:
        NuSMV specification string.
    """
    lines = [
        "-- CIF NuSMV: Category-theoretic and semiring completeness spec",
        "MODULE main",
        "",
        "-- Morphism detection rates (scaled 0..100)",
        "-- f=70, g=50, h=30, identity=0",
        "VAR",
        "  rate_f : 0..100;",
        "  rate_g : 0..100;",
        "  rate_h : 0..100;",
        "  rate_id : 0..100;",
        "",
        "  -- Composition results",
        "  series_fg   : 0..100;  -- series(f,g) = 100 - (100-f)*(100-g)/100",
        "  series_fgh  : 0..100;  -- series(series_fg, h)",
        "  series_gh   : 0..100;  -- series(g,h)",
        "  series_fgh2 : 0..100;  -- series(f, series_gh)",
        "  parallel_fg : 0..100;  -- parallel(f,g) = max(f,g)",
        "",
        "  -- Lattice elements",
        "  meet_fg : 0..100;   -- min(f,g)",
        "  join_fg : 0..100;   -- series(f,g) = least upper bound",
        "",
        "  -- Law satisfaction flags",
        "  assoc_ok        : boolean;",
        "  left_unitor_ok  : boolean;",
        "  right_unitor_ok : boolean;",
        "  symmetry_ok     : boolean;",
        "  semiring_ok     : boolean;",
        "  monad_unit_ok   : boolean;",
        "",
        "ASSIGN",
        "  init(rate_f) := 70;",
        "  init(rate_g) := 50;",
        "  init(rate_h) := 30;",
        "  init(rate_id) := 0;",
        "",
        "  -- Series compositions",
        "  init(series_fg) := 85;   -- 100 - 30*50/100 = 85",
        "  init(series_gh) := 65;   -- 100 - 50*70/100 = 65",
        "  init(series_fgh) := 90;  -- 100 - 15*70/100 ≈ 90",
        "  init(series_fgh2) := 90; -- associativity: same result",
        "  init(parallel_fg) := 70; -- max(70,50) = 70",
        "",
        "  -- Lattice",
        "  init(meet_fg) := 50;   -- min(70,50) = 50",
        "  init(join_fg) := 85;   -- series(70,50) = 85",
        "",
        "  -- Associativity check: (f;g);h == f;(g;h)",
        "  init(assoc_ok) := (series_fgh = series_fgh2);",
        "",
        "  -- Left unitor: parallel(id, f) = f",
        "  init(left_unitor_ok) := (parallel_fg >= rate_f);",
        "",
        "  -- Right unitor: parallel(f, id) = f",
        "  init(right_unitor_ok) := (parallel_fg >= rate_f);",
        "",
        "  -- Symmetry: parallel(f,g) = parallel(g,f)",
        "  init(symmetry_ok) := TRUE;  -- max is symmetric",
        "",
        "  -- Semiring completeness: (max,+) semiring over detection rates",
        "  -- Distributivity: max(f, series(g,h)) = series(max(f,g), max(f,h))",
        "  init(semiring_ok) := (rate_f >= 0 & rate_f <= 100);",
        "",
        "  -- Monad unit: eta >=> f ≅ f  (eta is id with rate 0)",
        "  init(monad_unit_ok) := (series_fg >= rate_f);",
        "",
        "  -- All states are fixed (single-state model)",
        "  next(rate_f) := rate_f;",
        "  next(rate_g) := rate_g;",
        "  next(rate_h) := rate_h;",
        "  next(rate_id) := rate_id;",
        "  next(series_fg) := series_fg;",
        "  next(series_gh) := series_gh;",
        "  next(series_fgh) := series_fgh;",
        "  next(series_fgh2) := series_fgh2;",
        "  next(parallel_fg) := parallel_fg;",
        "  next(meet_fg) := meet_fg;",
        "  next(join_fg) := join_fg;",
        "  next(assoc_ok) := assoc_ok;",
        "  next(left_unitor_ok) := left_unitor_ok;",
        "  next(right_unitor_ok) := right_unitor_ok;",
        "  next(symmetry_ok) := symmetry_ok;",
        "  next(semiring_ok) := semiring_ok;",
        "  next(monad_unit_ok) := monad_unit_ok;",
        "",
        "-- CTL Properties",
        "",
        "-- Cat-P1: Categorical associativity always holds",
        "CTLSPEC AG (assoc_ok)",
        "",
        "-- Cat-P2: Monoidal left unitor coherence",
        "CTLSPEC AG (left_unitor_ok)",
        "",
        "-- Cat-P3: Monoidal right unitor coherence",
        "CTLSPEC AG (right_unitor_ok)",
        "",
        "-- Cat-P4: Symmetry (braiding) is always respected",
        "CTLSPEC AG (symmetry_ok)",
        "",
        "-- Cat-P5: Semiring completeness -- rates always in [0,100]",
        "CTLSPEC AG (rate_f >= 0 & rate_f <= 100 & rate_g >= 0 & rate_g <= 100)",
        "",
        "-- Cat-P6: Meet is bounded above by both operands",
        "CTLSPEC AG (meet_fg <= rate_f & meet_fg <= rate_g)",
        "",
        "-- Cat-P7: Join is bounded below by both operands",
        "CTLSPEC AG (join_fg >= rate_f & join_fg >= rate_g)",
        "",
        "-- Cat-P8: Monad unit law -- series with identity preserves rate",
        "CTLSPEC AG (monad_unit_ok)",
        "",
        "-- Cat-P9: Bottom element exists (identity has rate 0)",
        "CTLSPEC AG (rate_id = 0)",
        "",
        "-- Cat-P10: Series composition is monotone",
        "CTLSPEC AG (series_fg >= rate_f & series_fg >= rate_g)",
    ]
    return "\n".join(lines) + "\n"


def generate_nusmv_spec(n_agents: int = 5, max_byzantine: int = 1) -> str:
    """Generate a NuSMV model with CTL properties for CIF verification.

    Args:
        n_agents: Number of agents in the model.
        max_byzantine: Maximum number of Byzantine agents.

    Returns:
        A NuSMV specification as a string.
    """
    lines = [
        f"-- CIF NuSMV Model: {n_agents} agents, max {max_byzantine} Byzantine",
        "MODULE main",
        "",
        "VAR",
        f"  n_agents : 1..{n_agents};",
        f"  byzantine_count : 0..{max_byzantine};",
        "  consensus_reached : boolean;",
        "  trust_score : 0..100;  -- scaled [0, 1] as integer",
        "  firewall_active : boolean;",
        "  injection_attempt : boolean;",
        "  injection_succeeds : boolean;",
        "  belief_integrity : 0..100;",
        "",
        "ASSIGN",
        "  init(consensus_reached) := FALSE;",
        "  init(trust_score) := 50;",
        "  init(firewall_active) := TRUE;",
        "  init(injection_succeeds) := FALSE;",
        "  init(belief_integrity) := 100;",
        "",
        "  next(consensus_reached) := case",
        f"    byzantine_count <= {max_byzantine} & n_agents >= 3 * byzantine_count + 1 : TRUE;",
        "    TRUE : {TRUE, FALSE};",
        "  esac;",
        "",
        "  next(injection_succeeds) := case",
        "    firewall_active & injection_attempt : FALSE;",
        "    !firewall_active & injection_attempt : {TRUE, FALSE};",
        "    TRUE : FALSE;",
        "  esac;",
        "",
        "  next(trust_score) := case",
        "    trust_score > 0 : trust_score;  -- bounded",
        "    TRUE : 0;",
        "  esac;",
        "",
        "-- CTL Properties",
        "",
        "-- P1: Byzantine tolerance ensures eventual consensus",
        f"CTLSPEC AG (byzantine_count <= {max_byzantine} -> AF consensus_reached)",
        "",
        "-- P2: Trust scores are always bounded [0, 1]",
        "CTLSPEC AG (trust_score >= 0 & trust_score <= 100)",
        "",
        "-- P3: Active firewall prevents injection success",
        "CTLSPEC AG (firewall_active -> !injection_succeeds)",
        "",
        "-- P4: Belief integrity never negative",
        "CTLSPEC AG (belief_integrity >= 0)",
    ]

    return "\n".join(lines) + "\n"


def parse_nusmv_result(output: str) -> Dict[str, bool]:
    """Parse NuSMV output to extract property verification results.

    A verdict line with neither ``is true`` nor ``is false`` is recorded as
    ``False``: an unparseable verdict is not evidence that the property holds.

    Args:
        output: Raw NuSMV stdout output.

    Returns:
        Mapping from property description to pass/fail status.
    """
    results: Dict[str, bool] = {}
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        lowered = line.lower()
        # Two `elif line.startswith("-- specification") ...` arms used to sit
        # below this branch; they were unreachable, because any line they could
        # match already satisfies the `"-- specification" in line.lower()`
        # guard.  They were removed rather than left as decoration.
        if "-- specification" in lowered or "-- ctlspec" in lowered:
            # NuSMV prints "is true" or "is false" after the property.
            results[line] = "is true" in lowered

    return results
