"""Reader-side manuscript claim registry.

The injector (:mod:`manuscript.injector`) is a *write* path: it substitutes
numbers into the manuscript. Nothing in it, and nothing in
:mod:`manuscript.verifier`, ever reads a number back out of the prose and
re-derives it from ``output/data/``. This module is that missing reader-side
check.

Design
------
A :class:`Claim` binds one number that appears in the prose to a *deriver*
that recomputes it from the shipped data artifacts:

* ``pattern`` locates the stated value. It must expose **exactly one**
  capturing group, and that group must capture the numeric literal.
* ``deriver`` recomputes the value from :class:`GroundTruth`.
* ``unit`` says how the captured literal maps onto the derived value
  (``'fraction'``, ``'percent'`` or ``'count'``); comparison always happens
  in the derived value's own units.
* ``tolerance`` is the absolute slack in those units.
* ``provenance`` records whether the number is a real measurement, a
  parametric-simulation output, or an illustrative figure that is reported
  but not gated on.

Verdicts
--------
``MATCH``
    Stated value agrees with the derived value inside ``tolerance``.
``MISMATCH``
    The prose states a number the data does not support.
``NOT_FOUND``
    The pattern matched **zero** times. This is a **failure**, never a skip:
    a pattern that matches nothing is exactly how a fabricated number hides
    from a checker, and it is the defect that made the injector's "no changes
    needed" message indistinguishable from total regex failure.
``UNBACKED``
    The prose states a number, but the artifact it should come from is
    missing, unparseable, or reports a non-success ``status``. Also a
    failure: an unbacked number in a manuscript is a fabrication risk, not a
    neutral gap.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Sequence

Unit = Literal["fraction", "percent", "count"]
Provenance = Literal["real", "parametric", "illustrative"]
Verdict = Literal["MATCH", "MISMATCH", "NOT_FOUND", "UNBACKED"]

#: Statuses a producer script writes to mean "this run produced no measurements".
#: Deliberately duplicated from :mod:`manuscript.injector` rather than imported
#: so the reader-side check cannot be disabled by an edit to the write path.
UNAVAILABLE_STATUSES = frozenset(
    {"skipped", "ollama_unavailable", "timeout", "error", "failed", "unavailable"}
)

#: Normal-approximation z for a two-sided 95% interval (matches the injector).
_Z95 = 1.959963984540054

#: Floating-point slack added to every tolerance so that a value rounded to the
#: last printed digit (|delta| exactly == half a ULP of that digit) compares equal.
_TOL_EPS = 1e-9

#: Largest plausible evaluation-corpus size when recovering a denominator.
_MAX_CORPUS = 100_000


class ClaimDataUnavailable(RuntimeError):
    """Raised by a deriver when no measured value exists for the claim."""


# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------


class GroundTruth:
    """Lazy, fail-closed accessor over the JSON artifacts in ``output/data``.

    Every accessor raises :class:`ClaimDataUnavailable` rather than returning
    a default, so a missing or skipped artifact surfaces as an ``UNBACKED``
    verdict instead of silently agreeing with whatever the prose says.
    """

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self._cache: dict[str, Any] = {}

    # -- raw payloads ------------------------------------------------------

    def payload(self, filename: str) -> Any:
        """Return the parsed JSON body of ``filename``."""
        if filename in self._cache:
            return self._cache[filename]
        path = self.data_dir / filename
        if not path.is_file():
            raise ClaimDataUnavailable(f"{filename} not found in {self.data_dir}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ClaimDataUnavailable(f"{filename} is not valid JSON ({exc})") from exc
        if isinstance(data, dict):
            status = str(data.get("status", "")).strip().lower()
            if status in UNAVAILABLE_STATUSES:
                reason = data.get("reason") or "no reason recorded"
                raise ClaimDataUnavailable(f"{filename} reports status={status!r} ({reason})")
        self._cache[filename] = data
        return data

    # -- ablation ----------------------------------------------------------

    def ablation(self) -> dict[str, Any]:
        """Parsed ``ablation_results.json``."""
        data = self.payload("ablation_results.json")
        if not isinstance(data, dict):
            raise ClaimDataUnavailable("ablation_results.json is not a JSON object")
        return data

    def _component_rows(self) -> list[dict[str, Any]]:
        rows = self.ablation().get("component_removal")
        if not isinstance(rows, list) or not rows:
            raise ClaimDataUnavailable("ablation_results.json has no 'component_removal' rows")
        return rows

    def component(self, name: str) -> dict[str, Any]:
        """The component-removal row for ``name``."""
        for row in self._component_rows():
            if row.get("removed") == name:
                return row
        raise ClaimDataUnavailable(f"ablation_results.json has no component row for {name!r}")

    def component_tpr(self, name: str) -> float:
        """TPR of the pipeline with ``name`` removed."""
        return float(self.component(name)["tpr"])

    def component_delta(self, name: str) -> float:
        """Signed change in TPR caused by removing ``name``."""
        return float(self.component(name)["delta_tpr"])

    def component_delta_magnitude(self, name: str) -> float:
        """``|delta_tpr|`` for ``name`` (prose usually states the magnitude)."""
        return abs(self.component_delta(name))

    def full_pipeline_tpr(self) -> float:
        """TPR of the complete pipeline on the ablation corpus."""
        full = self.ablation().get("full_pipeline")
        if not isinstance(full, dict) or "tpr" not in full:
            raise ClaimDataUnavailable("ablation_results.json has no 'full_pipeline.tpr'")
        return float(full["tpr"])

    def detection_share_of_pipeline(self) -> float:
        """Fraction of full-pipeline TPR attributable to the detection module."""
        baseline = self.full_pipeline_tpr()
        if baseline <= 0:
            raise ClaimDataUnavailable("full_pipeline.tpr is not positive")
        return self.component_delta_magnitude("detection") / baseline

    def top_n_harmful_share(self, n: int = 3) -> float:
        """Share of the summed *negative* delta magnitude held by the top ``n``."""
        deltas = [float(r["delta_tpr"]) for r in self._component_rows()]
        harmful = sorted((abs(d) for d in deltas if d < 0), reverse=True)
        total = sum(harmful)
        if total <= 0:
            raise ClaimDataUnavailable("no harmful component removals recorded")
        return sum(harmful[:n]) / total

    def synergy(self, first: str, second: str) -> float:
        """Synergy score for the unordered pair ``{first, second}``."""
        pair = {first, second}
        rows = self.ablation().get("top_synergies")
        if not isinstance(rows, list) or not rows:
            raise ClaimDataUnavailable("ablation_results.json has no 'top_synergies' rows")
        for row in rows:
            if {row.get("a"), row.get("b")} == pair:
                return float(row["synergy"])
        raise ClaimDataUnavailable(
            f"ablation_results.json 'top_synergies' has no entry for "
            f"{sorted(pair)} (recorded pairs: {[sorted((r['a'], r['b'])) for r in rows]})"
        )

    def ablation_corpus_size(self) -> float:
        """Recover the ablation corpus size N from the measured rates.

        Every TPR in ``ablation_results.json`` is ``k/N`` for integer ``k``, so
        N is the least common multiple of the reduced denominators. This binds
        the manuscript's stated corpus size to the measurement resolution
        instead of trusting a hand-written literal.
        """
        rows = self._component_rows()
        rates = [self.full_pipeline_tpr()] + [float(r["tpr"]) for r in rows]
        synergies = self.ablation().get("top_synergies")
        if isinstance(synergies, list):
            for row in synergies:
                rates.extend(float(row[key]) for key in ("tpr_a", "tpr_b", "combined_tpr"))
        denominator = 1
        for rate in rates:
            if rate <= 0:
                continue
            frac = Fraction(rate).limit_denominator(_MAX_CORPUS // 10)
            denominator = denominator * frac.denominator // math.gcd(denominator, frac.denominator)
            if denominator > _MAX_CORPUS:
                raise ClaimDataUnavailable(
                    "cannot recover the ablation corpus size: implied denominator "
                    f"exceeds {_MAX_CORPUS}"
                )
        return float(denominator)

    # -- multi-seed --------------------------------------------------------

    def multi_seed(self) -> dict[str, Any]:
        """Parsed ``multi_seed_results.json``."""
        data = self.payload("multi_seed_results.json")
        if not isinstance(data, dict):
            raise ClaimDataUnavailable("multi_seed_results.json is not a JSON object")
        return data

    def _seed_rates(self) -> list[float]:
        metrics = self.multi_seed().get("seed_metrics")
        if not isinstance(metrics, list) or not metrics:
            raise ClaimDataUnavailable("multi_seed_results.json has no 'seed_metrics'")
        rates = [float(m["overall"]) for m in metrics if isinstance(m, dict) and "overall" in m]
        if not rates:
            raise ClaimDataUnavailable("multi_seed_results.json 'seed_metrics' carry no 'overall'")
        return rates

    def ms_mean(self) -> float:
        """Mean detection rate across seeds."""
        rates = self._seed_rates()
        return sum(rates) / len(rates)

    def ms_min(self) -> float:
        """Lowest per-seed detection rate."""
        return min(self._seed_rates())

    def ms_max(self) -> float:
        """Highest per-seed detection rate."""
        return max(self._seed_rates())

    def ms_n(self) -> float:
        """Number of seeds."""
        rates = self._seed_rates()
        return float(self.multi_seed().get("n_seeds", len(rates)))

    def ms_cv(self) -> float:
        """Coefficient of variation of the per-seed detection rates."""
        payload = self.multi_seed()
        if "overall_cv" in payload:
            return float(payload["overall_cv"])
        rates = self._seed_rates()
        mean = sum(rates) / len(rates)
        if mean <= 0 or len(rates) < 2:
            raise ClaimDataUnavailable("multi_seed_results.json: cannot derive 'overall_cv'")
        variance = sum((r - mean) ** 2 for r in rates) / (len(rates) - 1)
        return math.sqrt(variance) / mean

    def _ms_ci_halfwidth(self) -> float:
        rates = self._seed_rates()
        if len(rates) < 2:
            raise ClaimDataUnavailable("multi_seed_results.json: need >1 seed for a CI")
        mean = sum(rates) / len(rates)
        variance = sum((r - mean) ** 2 for r in rates) / (len(rates) - 1)
        return _Z95 * math.sqrt(variance / len(rates))

    def ms_ci_low(self) -> float:
        """Lower bound of the 95% CI for the mean detection rate."""
        return self.ms_mean() - self._ms_ci_halfwidth()

    def ms_ci_high(self) -> float:
        """Upper bound of the 95% CI for the mean detection rate."""
        return self.ms_mean() + self._ms_ci_halfwidth()

    # -- colony ------------------------------------------------------------

    def colony(self) -> list[dict[str, Any]]:
        """Parsed ``colony_results.json`` scenario rows."""
        data = self.payload("colony_results.json")
        rows = data if isinstance(data, list) else data.get("scenarios")
        if not isinstance(rows, list) or not rows:
            raise ClaimDataUnavailable("colony_results.json has no scenario rows")
        return rows

    def colony_scenario(self, name: str) -> dict[str, Any]:
        """The colony row named ``name``."""
        for row in self.colony():
            if row.get("scenario") == name:
                return row
        raise ClaimDataUnavailable(f"colony_results.json has no scenario {name!r}")

    @staticmethod
    def _colony_metric(row: dict[str, Any], field: str) -> float:
        """Read ``field`` from a colony row under either recorded schema.

        The single-seed schema stores a scalar (``detection_rate``); the
        multi-repeat schema stores ``detection_rate_mean`` plus a
        ``detection_rate_values`` list. Each branch reads a value that is
        actually in the artifact -- there is no default -- and the absence of
        all three raises.
        """
        if field in row:
            return float(row[field])
        mean_key = f"{field}_mean"
        if mean_key in row:
            return float(row[mean_key])
        values_key = f"{field}_values"
        values = row.get(values_key)
        if isinstance(values, list) and values:
            return sum(float(v) for v in values) / len(values)
        raise ClaimDataUnavailable(
            f"colony scenario {row.get('scenario')!r} has no {field!r}, "
            f"{mean_key!r} or non-empty {values_key!r}"
        )

    def colony_field(self, name: str, field: str) -> float:
        """A numeric field of colony scenario ``name``."""
        return self._colony_metric(self.colony_scenario(name), field)

    def _structured(self) -> list[dict[str, Any]]:
        rows = [r for r in self.colony() if int(r.get("n_adversaries", 0)) > 0]
        if not rows:
            raise ClaimDataUnavailable("colony_results.json has no adversarial scenarios")
        return rows

    def colony_structured_dr_min(self) -> float:
        """Lowest detection rate among scenarios that contain adversaries."""
        return min(self._colony_metric(r, "detection_rate") for r in self._structured())

    def colony_structured_dr_max(self) -> float:
        """Highest detection rate among scenarios that contain adversaries."""
        return max(self._colony_metric(r, "detection_rate") for r in self._structured())

    def colony_agents_min(self) -> float:
        """Smallest colony size benchmarked."""
        return float(min(int(r["n_agents"]) for r in self.colony()))

    def colony_agents_max(self) -> float:
        """Largest colony size benchmarked."""
        return float(max(int(r["n_agents"]) for r in self.colony()))

    # -- parametric simulation --------------------------------------------

    def parametric(self) -> list[dict[str, Any]]:
        """Parsed ``full_evaluation_results.json`` rows."""
        data = self.payload("full_evaluation_results.json")
        if not isinstance(data, list) or not data:
            raise ClaimDataUnavailable("full_evaluation_results.json has no rows")
        return data

    def parametric_overall_dr(self) -> float:
        """Unweighted mean detection rate over all parametric rows."""
        rates = [float(r["detection_rate"]) for r in self.parametric()]
        return sum(rates) / len(rates)

    def parametric_arch_dr(self, architecture: str) -> float:
        """Mean detection rate for one architecture."""
        rates = [
            float(r["detection_rate"])
            for r in self.parametric()
            if r.get("architecture") == architecture
        ]
        if not rates:
            raise ClaimDataUnavailable(
                f"full_evaluation_results.json has no rows for architecture {architecture!r}"
            )
        return sum(rates) / len(rates)

    def parametric_dr_min(self) -> float:
        """Lowest single parametric detection rate (the simulation's floor)."""
        return min(float(r["detection_rate"]) for r in self.parametric())

    def parametric_dr_max(self) -> float:
        """Highest single parametric detection rate."""
        return max(float(r["detection_rate"]) for r in self.parametric())

    def parametric_instances(self) -> float:
        """Total number of parametric evaluation instances."""
        return float(sum(int(r["n_attacks"]) for r in self.parametric()))

    def attack_corpus_size(self) -> float:
        """Attacks per architecture in the parametric sweep."""
        per_arch: dict[str, int] = {}
        for row in self.parametric():
            per_arch[str(row.get("architecture"))] = per_arch.get(
                str(row.get("architecture")), 0
            ) + int(row["n_attacks"])
        sizes = set(per_arch.values())
        if len(sizes) != 1:
            raise ClaimDataUnavailable(
                f"full_evaluation_results.json architectures disagree on corpus size: {per_arch}"
            )
        return float(sizes.pop())

    # -- statistics --------------------------------------------------------

    def statistical(self) -> dict[str, Any]:
        """Parsed ``statistical_results.json``."""
        data = self.payload("statistical_results.json")
        if not isinstance(data, dict):
            raise ClaimDataUnavailable("statistical_results.json is not a JSON object")
        return data

    def cohens_d(self) -> float:
        """Cohen's d, CIF vs baseline."""
        stats = self.statistical()
        if "cohens_d_cif_vs_baseline" not in stats:
            raise ClaimDataUnavailable("statistical_results.json has no 'cohens_d_cif_vs_baseline'")
        return float(stats["cohens_d_cif_vs_baseline"])

    def kruskal_wallis(self, field: str) -> float:
        """A field (``'h'`` or ``'p'``) of the Kruskal-Wallis result."""
        kw = self.statistical().get("kruskal_wallis")
        if not isinstance(kw, dict) or field not in kw:
            raise ClaimDataUnavailable(f"statistical_results.json has no 'kruskal_wallis.{field}'")
        return float(kw[field])

    # -- cross validation --------------------------------------------------

    def cross_validation(self, field: str) -> float:
        """A numeric field of ``cross_validation_results.json``."""
        data = self.payload("cross_validation_results.json")
        if not isinstance(data, dict) or field not in data:
            raise ClaimDataUnavailable(f"cross_validation_results.json has no {field!r}")
        return float(data[field])

    # -- LLM ---------------------------------------------------------------

    def llm_detection_rate(self, architecture: str) -> float:
        """Measured LLM detection rate for one architecture topology."""
        payload = self.payload("llm_demo_results.json")
        if not isinstance(payload, dict):
            raise ClaimDataUnavailable("llm_demo_results.json is not a JSON object")
        multi = payload.get("multiagent_results")
        if not isinstance(multi, dict) or architecture not in multi:
            raise ClaimDataUnavailable(
                f"llm_demo_results.json has no 'multiagent_results.{architecture}'"
            )
        arch = multi[architecture]
        if not isinstance(arch, dict) or "detection_rate" not in arch:
            raise ClaimDataUnavailable(
                f"llm_demo_results.json 'multiagent_results.{architecture}' has no detection_rate"
            )
        return float(arch["detection_rate"])

    def llm_total(self, architecture: str) -> float:
        """Measured LLM sample count for one architecture topology."""
        payload = self.payload("llm_demo_results.json")
        if not isinstance(payload, dict):
            raise ClaimDataUnavailable("llm_demo_results.json is not a JSON object")
        multi = payload.get("multiagent_results")
        if not isinstance(multi, dict) or architecture not in multi:
            raise ClaimDataUnavailable(
                f"llm_demo_results.json has no 'multiagent_results.{architecture}'"
            )
        arch = multi[architecture]
        if not isinstance(arch, dict) or "total" not in arch:
            raise ClaimDataUnavailable(
                f"llm_demo_results.json 'multiagent_results.{architecture}' has no total"
            )
        return float(arch["total"])


# ---------------------------------------------------------------------------
# Claim model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Claim:
    """One number in the prose, bound to the computation that produces it."""

    id: str
    file: str
    pattern: re.Pattern[str]
    deriver: Callable[[GroundTruth], float]
    tolerance: float
    unit: Unit
    provenance: Provenance
    note: str = ""

    def __post_init__(self) -> None:
        if self.pattern.groups != 1:
            raise ValueError(
                f"claim {self.id!r}: pattern must have exactly one capturing group "
                f"(has {self.pattern.groups}): {self.pattern.pattern!r}"
            )
        if self.tolerance < 0:
            raise ValueError(f"claim {self.id!r}: tolerance must be >= 0")


@dataclass(frozen=True)
class ClaimResult:
    """Outcome of checking one :class:`Claim`."""

    claim_id: str
    file: str
    verdict: Verdict
    provenance: Provenance
    stated: float | None
    derived: float | None
    n_matches: int
    detail: str

    @property
    def delta(self) -> float | None:
        """Signed ``stated - derived`` when both are known."""
        if self.stated is None or self.derived is None:
            return None
        return self.stated - self.derived

    @property
    def is_failure(self) -> bool:
        """True when this result should fail the gate.

        ``NOT_FOUND`` always fails, including for illustrative claims: a
        pattern that matches nothing means the checker is no longer watching
        anything, which is strictly worse than a wrong number.
        """
        if self.verdict == "NOT_FOUND":
            return True
        if self.verdict in ("MISMATCH", "UNBACKED"):
            return self.provenance != "illustrative"
        return False


@dataclass(frozen=True)
class ClaimReport:
    """All :class:`ClaimResult` rows from one verification run."""

    results: tuple[ClaimResult, ...]

    def by_verdict(self, verdict: Verdict) -> tuple[ClaimResult, ...]:
        """Every result carrying ``verdict``."""
        return tuple(r for r in self.results if r.verdict == verdict)

    @property
    def matched(self) -> tuple[ClaimResult, ...]:
        """Results whose stated value agrees with the derived value."""
        return self.by_verdict("MATCH")

    @property
    def mismatched(self) -> tuple[ClaimResult, ...]:
        """Results whose stated value disagrees with the derived value."""
        return self.by_verdict("MISMATCH")

    @property
    def not_found(self) -> tuple[ClaimResult, ...]:
        """Results whose pattern matched zero times."""
        return self.by_verdict("NOT_FOUND")

    @property
    def unbacked(self) -> tuple[ClaimResult, ...]:
        """Results whose deriver had no measured value to work from."""
        return self.by_verdict("UNBACKED")

    @property
    def failures(self) -> tuple[ClaimResult, ...]:
        """Every result that should fail the gate."""
        return tuple(r for r in self.results if r.is_failure)

    @property
    def ok(self) -> bool:
        """True when nothing failed."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable summary of the run."""
        return {
            "ok": self.ok,
            "counts": {
                "total": len(self.results),
                "match": len(self.matched),
                "mismatch": len(self.mismatched),
                "not_found": len(self.not_found),
                "unbacked": len(self.unbacked),
                "failures": len(self.failures),
            },
            "results": [
                {
                    "claim_id": r.claim_id,
                    "file": r.file,
                    "verdict": r.verdict,
                    "provenance": r.provenance,
                    "stated": r.stated,
                    "derived": r.derived,
                    "delta": r.delta,
                    "n_matches": r.n_matches,
                    "detail": r.detail,
                }
                for r in self.results
            ],
        }

    def render_table(self, *, only_failures: bool = False) -> str:
        """Render the report as a fixed-width table."""
        rows = self.failures if only_failures else self.results
        header = ("CLAIM", "FILE", "STATED", "DERIVED", "DELTA", "VERDICT")
        body = [
            (
                r.claim_id,
                r.file,
                _fmt(r.stated),
                _fmt(r.derived),
                _fmt(r.delta),
                r.verdict,
            )
            for r in rows
        ]
        widths = [
            max(len(header[i]), *(len(row[i]) for row in body)) if body else len(header[i])
            for i in range(len(header))
        ]
        lines = [
            "  ".join(header[i].ljust(widths[i]) for i in range(len(header))),
            "  ".join("-" * widths[i] for i in range(len(header))),
        ]
        lines.extend(
            "  ".join(row[i].ljust(widths[i]) for i in range(len(header))) for row in body
        )
        return "\n".join(lines)


def _fmt(value: float | None) -> str:
    """Format an optional number for the report table."""
    return "-" if value is None else f"{value:.6g}"


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------

_NUM_CLEAN = str.maketrans({",": "", "{": "", "}": "", " ": "", "\\": "", "$": ""})


def parse_stated(raw: str, unit: Unit) -> float:
    """Convert a captured literal into the derived value's units.

    Handles LaTeX thousands separators (``3{,}800``) and plain commas.
    """
    cleaned = raw.translate(_NUM_CLEAN)
    value = float(cleaned)
    return value / 100.0 if unit == "percent" else value


def verify_claims(
    claims: Sequence[Claim],
    manuscript_dir: Path | str,
    gt: GroundTruth,
) -> ClaimReport:
    """Check every claim against the prose and the data.

    Parameters
    ----------
    claims :
        Claims to check (usually :data:`CLAIMS`).
    manuscript_dir :
        Directory holding the manuscript markdown files.
    gt :
        Ground-truth accessor over ``output/data``.
    """
    root = Path(manuscript_dir)
    texts: dict[str, str | None] = {}
    results: list[ClaimResult] = []

    for claim in claims:
        if claim.file not in texts:
            path = root / claim.file
            texts[claim.file] = path.read_text(encoding="utf-8") if path.is_file() else None
        text = texts[claim.file]

        derived: float | None = None
        derive_error = ""
        try:
            derived = float(claim.deriver(gt))
        except ClaimDataUnavailable as exc:
            derive_error = str(exc)
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError) as exc:
            derive_error = f"deriver failed: {type(exc).__name__}: {exc}"

        if text is None:
            detail = f"manuscript file {claim.file} missing"
            results.append(_result(claim, "NOT_FOUND", None, derived, 0, detail))
            continue

        matches = claim.pattern.findall(text)
        if not matches:
            results.append(
                _result(
                    claim,
                    "NOT_FOUND",
                    None,
                    derived,
                    0,
                    f"pattern {claim.pattern.pattern!r} matched 0 times",
                )
            )
            continue

        try:
            stated_values = [parse_stated(m, claim.unit) for m in matches]
        except ValueError as exc:
            detail = f"unparseable capture: {exc}"
            results.append(_result(claim, "MISMATCH", None, derived, len(matches), detail))
            continue

        if derived is None:
            results.append(
                _result(claim, "UNBACKED", stated_values[0], None, len(matches), derive_error)
            )
            continue

        worst = max(stated_values, key=lambda v: abs(v - derived))
        gap = abs(worst - derived)
        if gap <= claim.tolerance + _TOL_EPS:
            results.append(_result(claim, "MATCH", worst, derived, len(matches), ""))
        else:
            results.append(
                _result(
                    claim,
                    "MISMATCH",
                    worst,
                    derived,
                    len(matches),
                    f"stated {worst:.6g} vs derived {derived:.6g} "
                    f"(|delta|={gap:.6g} > tolerance {claim.tolerance:.6g})",
                )
            )

    return ClaimReport(tuple(results))


def _result(
    claim: Claim,
    verdict: Verdict,
    stated: float | None,
    derived: float | None,
    n_matches: int,
    detail: str,
) -> ClaimResult:
    """Build a :class:`ClaimResult` for ``claim``."""
    return ClaimResult(
        claim_id=claim.id,
        file=claim.file,
        verdict=verdict,
        provenance=claim.provenance,
        stated=stated,
        derived=derived,
        n_matches=n_matches,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

#: One-decimal percent (e.g. ``44.8\%``): half of the last printed digit.
PCT1 = 0.0005
#: Whole percent (e.g. ``42\%``).
PCT0 = 0.005
#: Whole percent stated as an approximation (``$\sim$44\%``).
PCT_APPROX = 0.01
#: Three-decimal fraction (e.g. ``0.448``).
F3 = 0.0005
#: Exact integer count.
EXACT = 0.0


def _c(
    claim_id: str,
    file: str,
    pattern: str,
    deriver: Callable[[GroundTruth], float],
    tolerance: float,
    unit: Unit,
    provenance: Provenance = "real",
    note: str = "",
) -> Claim:
    """Compact :class:`Claim` constructor used by the registry below."""
    return Claim(
        id=claim_id,
        file=file,
        pattern=re.compile(pattern),
        deriver=deriver,
        tolerance=tolerance,
        unit=unit,
        provenance=provenance,
        note=note,
    )


def _component_claims(
    file: str,
    labels: dict[str, str],
    *,
    prefix: str,
    positive_deltas: Iterable[str] = (),
) -> tuple[Claim, ...]:
    """Claims for one ablation component-removal table.

    ``labels`` maps the artifact component key onto the row label used in that
    file (the two tables spell 'Tripwire'/'Tripwires' differently).
    """
    positive = set(positive_deltas)
    claims: list[Claim] = []
    for key, label in labels.items():
        escaped = re.escape(label)
        claims.append(
            _c(
                f"{prefix}.tpr.{key}",
                file,
                rf"\| {escaped} \| (\d+\.\d+) \|",
                (lambda k: lambda gt: gt.component_tpr(k))(key),
                F3,
                "fraction",
            )
        )
        sign = r"\+" if key in positive else "-"
        deriver = (
            (lambda k: lambda gt: gt.component_delta(k))(key)
            if key in positive
            else (lambda k: lambda gt: gt.component_delta_magnitude(k))(key)
        )
        claims.append(
            _c(
                f"{prefix}.delta.{key}",
                file,
                rf"\| {escaped} \| [\d.]+ \| \$\\approx {sign}([\d.]+)\$",
                deriver,
                F3,
                "fraction",
            )
        )
    return tuple(claims)


def _synergy_claims(file: str, *, prefix: str) -> tuple[Claim, ...]:
    """Claims for one component-synergy table."""
    pairs = (
        ("tripwire_detection", "Tripwire + Detection", "tripwire", "detection"),
        ("firewall_detection", "Firewall + Detection", "firewall", "detection"),
        ("provenance_invariants", "Provenance + Invariants", "provenance", "invariants"),
        ("firewall_invariants", "Firewall + Invariants", "firewall", "invariants"),
        ("tripwire_invariants", "Tripwire + Invariants", "tripwire", "invariants"),
    )
    return tuple(
        _c(
            f"{prefix}.synergy.{slug}",
            file,
            rf"\| {re.escape(label)} \| \$\\approx \+([\d.]+)\$",
            (lambda x, y: lambda gt: gt.synergy(x, y))(first, second),
            F3,
            "fraction",
        )
        for slug, label, first, second in pairs
    )


_COLONY_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    # (artifact key, row label, agents, steps, adversaries)
    ("recruitment_poisoning", "Recruitment poisoning", "20", "100", "2"),
    ("sybil_infiltration", "Sybil infiltration", "50", "500", "4"),
    ("quorum_manipulation", "Quorum manipulation", "30", "200", "3"),
    ("belief_cascade", "Belief cascade", "100", "300", "2"),
    ("emergent_misalignment", "Emergent misalignment", "50", "1000", "0"),
)


def _colony_claims(file: str) -> tuple[Claim, ...]:
    """Claims for every cell of the colony benchmark table."""
    claims: list[Claim] = []
    for key, label, agents, steps, advs in _COLONY_ROWS:
        head = rf"\| {re.escape(label)} \| {agents} \| {steps} \| {advs} \|"
        num = r"[\d.]+"
        claims.extend(
            (
                _c(
                    f"colony.dr.{key}",
                    file,
                    rf"{head} ({num})\\%",
                    (lambda k: lambda gt: gt.colony_field(k, "detection_rate"))(key),
                    PCT1,
                    "percent",
                ),
                _c(
                    f"colony.fpr.{key}",
                    file,
                    rf"{head} {num}\\% \| ({num})\\%",
                    (lambda k: lambda gt: gt.colony_field(k, "false_positive_rate"))(key),
                    PCT1,
                    "percent",
                ),
                _c(
                    f"colony.recovery.{key}",
                    file,
                    rf"{head} {num}\\% \| {num}\\% \| (\d+) \|",
                    (lambda k: lambda gt: gt.colony_field(k, "recovery_steps"))(key),
                    EXACT,
                    "count",
                ),
                _c(
                    f"colony.ccs.{key}",
                    file,
                    rf"{head} {num}\\% \| {num}\\% \| \d+ \| (\d+\.\d+) \|",
                    (lambda k: lambda gt: gt.colony_field(k, "ccs_score"))(key),
                    F3,
                    "fraction",
                ),
            )
        )
    return tuple(claims)


_ABSTRACT: tuple[Claim, ...] = (
    _c(
        "abstract.n_seeds",
        "00_abstract.md",
        r"across (\d+) random seeds",
        lambda gt: gt.ms_n(),
        EXACT,
        "count",
    ),
    _c(
        "abstract.ms_mean",
        "00_abstract.md",
        r"mean detection rate of (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "abstract.ms_ci_low",
        "00_abstract.md",
        r"\[95\\% CI: (\d+\.\d+)\\%, \d+\.\d+\\%\]",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "abstract.ms_ci_high",
        "00_abstract.md",
        r"\[95\\% CI: \d+\.\d+\\%, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "abstract.ablation_corpus_size",
        "00_abstract.md",
        r"real ablation studies on a (\d+)-attack corpus",
        lambda gt: gt.ablation_corpus_size(),
        EXACT,
        "count",
    ),
    _c(
        "abstract.detection_delta",
        "00_abstract.md",
        r"\$\\Delta\\text\{TPR\} = -([\d.]+)\$ when removed",
        lambda gt: gt.component_delta_magnitude("detection"),
        F3,
        "fraction",
    ),
    _c(
        "abstract.detection_share",
        "00_abstract.md",
        r"accounting for (\d+)\\% of pipeline detection",
        lambda gt: gt.detection_share_of_pipeline(),
        PCT0,
        "percent",
    ),
    _c(
        "abstract.llm_dr_low",
        "00_abstract.md",
        r"achieving (\d+)--\d+\\% detection across",
        lambda gt: gt.llm_detection_rate("claude_code"),
        PCT0,
        "percent",
    ),
    _c(
        "abstract.llm_dr_high",
        "00_abstract.md",
        r"achieving \d+--(\d+)\\% detection across",
        lambda gt: gt.llm_detection_rate("crewai"),
        PCT0,
        "percent",
    ),
    _c(
        "abstract.colony_agents_min",
        "00_abstract.md",
        r"colony benchmarks at scale \((\d+)--\d+ agents\)",
        lambda gt: gt.colony_agents_min(),
        EXACT,
        "count",
    ),
    _c(
        "abstract.colony_agents_max",
        "00_abstract.md",
        r"colony benchmarks at scale \(\d+--(\d+) agents\)",
        lambda gt: gt.colony_agents_max(),
        EXACT,
        "count",
    ),
    _c(
        "abstract.colony_dr_low",
        "00_abstract.md",
        r"demonstrating (\d+)--\d+\\% detection on structured",
        lambda gt: gt.colony_structured_dr_min(),
        PCT0,
        "percent",
    ),
    _c(
        "abstract.colony_dr_high",
        "00_abstract.md",
        r"demonstrating \d+--(\d+)\\% detection on structured",
        lambda gt: gt.colony_structured_dr_max(),
        PCT0,
        "percent",
    ),
    _c(
        "abstract.parametric_instances",
        "00_abstract.md",
        r"parametric simulation \(\$N=([\d{},]+)\$\)",
        lambda gt: gt.parametric_instances(),
        EXACT,
        "count",
        "parametric",
    ),
    _c(
        "abstract.parametric_ceiling_low",
        "00_abstract.md",
        r"coverage ceiling at (\d+)--\d+\\%",
        lambda gt: gt.parametric_dr_min(),
        PCT0,
        "percent",
        "parametric",
        note="Lowest single parametric detection rate — the most generous reading of the "
        "stated range's lower bound.",
    ),
    _c(
        "abstract.parametric_ceiling_high",
        "00_abstract.md",
        r"coverage ceiling at \d+--(\d+)\\%",
        lambda gt: gt.parametric_dr_max(),
        PCT0,
        "percent",
        "parametric",
    ),
)

_RESULTS: tuple[Claim, ...] = (
    _c(
        "results.ms_mean_row",
        "05_results.md",
        r"\| Mean Detection Rate \| (\d+\.\d+) \|",
        lambda gt: gt.ms_mean(),
        F3,
        "fraction",
    ),
    _c(
        "results.ms_min_row",
        "05_results.md",
        r"\| Min Detection Rate \| (\d+\.\d+) \|",
        lambda gt: gt.ms_min(),
        F3,
        "fraction",
    ),
    _c(
        "results.ms_max_row",
        "05_results.md",
        r"\| Max Detection Rate \| (\d+\.\d+) \|",
        lambda gt: gt.ms_max(),
        F3,
        "fraction",
    ),
    _c(
        "results.ms_cv_row",
        "05_results.md",
        r"\| Coefficient of Variation \| (\d+\.\d+) \|",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "results.cv_caption",
        "05_results.md",
        r"coefficient of variation \(CV = (\d+\.\d+)\)",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "results.gap_claude_parametric",
        "05_results.md",
        r"\| Claude Code \(multi-seed pipeline\) \| (\d+)\\%",
        lambda gt: gt.parametric_arch_dr("Claude Code"),
        PCT0,
        "percent",
        "parametric",
    ),
    _c(
        "results.gap_claude_empirical",
        "05_results.md",
        r"\| Claude Code \(multi-seed pipeline\) \| \d+\\% \| (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "results.power_ablation_n",
        "05_results.md",
        r"\| Ablation TPR \| [\d.]+ \| (\d+) \|",
        lambda gt: gt.ablation_corpus_size(),
        EXACT,
        "count",
    ),
    _c(
        "results.summary_ms_mean",
        "05_results.md",
        r"mean detection rate of \$\\sim\$(\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT_APPROX,
        "percent",
    ),
    _c(
        "results.summary_cv",
        "05_results.md",
        r"with a coefficient of variation of (\d+\.\d+)\.",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "results.summary_detection_delta",
        "05_results.md",
        r"largest marginal loss \(\$\\Delta\\text\{TPR\} \\approx -([\d.]+)\$",
        lambda gt: gt.component_delta_magnitude("detection"),
        F3,
        "fraction",
    ),
    _c(
        "results.summary_full_tpr",
        "05_results.md",
        r"Full pipeline TPR on this corpus is \$\\sim\$(\d+)\\%",
        lambda gt: gt.full_pipeline_tpr(),
        PCT_APPROX,
        "percent",
    ),
) + _colony_claims("05_results.md")

_STATISTICAL: tuple[Claim, ...] = (
    _c(
        "05b.ms_mean_row",
        "05b_statistical_significance.md",
        r"\| Mean DR \| (\d+\.\d+) \|",
        lambda gt: gt.ms_mean(),
        F3,
        "fraction",
    ),
    _c(
        "05b.ms_min_row",
        "05b_statistical_significance.md",
        r"\| Min \| (\d+\.\d+) \|",
        lambda gt: gt.ms_min(),
        F3,
        "fraction",
    ),
    _c(
        "05b.ms_max_row",
        "05b_statistical_significance.md",
        r"\| Max \| (\d+\.\d+) \|",
        lambda gt: gt.ms_max(),
        F3,
        "fraction",
    ),
    _c(
        "05b.ms_cv_row",
        "05b_statistical_significance.md",
        r"\| CV \| (\d+\.\d+) \|",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "05b.range_low",
        "05b_statistical_significance.md",
        r"\| 95% Range \| \[(\d+\.\d+), \d+\.\d+\]",
        lambda gt: gt.ms_min(),
        F3,
        "fraction",
    ),
    _c(
        "05b.range_high",
        "05b_statistical_significance.md",
        r"\| 95% Range \| \[\d+\.\d+, (\d+\.\d+)\]",
        lambda gt: gt.ms_max(),
        F3,
        "fraction",
    ),
    _c(
        "05b.ci_low",
        "05b_statistical_significance.md",
        r"\| Mean DR \| \d+\.\d+ \| \[(\d+\.\d+), \d+\.\d+\]",
        lambda gt: gt.ms_ci_low(),
        F3,
        "fraction",
    ),
    _c(
        "05b.ci_high",
        "05b_statistical_significance.md",
        r"\| Mean DR \| \d+\.\d+ \| \[\d+\.\d+, (\d+\.\d+)\]",
        lambda gt: gt.ms_ci_high(),
        F3,
        "fraction",
    ),
    _c(
        "05b.cv_inline",
        "05b_statistical_significance.md",
        r"coefficient of variation \(CV = (\d+\.\d+)\)",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "05b.full_pipeline_tpr",
        "05b_statistical_significance.md",
        r"\| None \(full pipeline\) \| \$\\approx (\d+\.\d+)\$",
        lambda gt: gt.full_pipeline_tpr(),
        F3,
        "fraction",
    ),
    _c(
        "05b.detection_share",
        "05b_statistical_significance.md",
        r"accounts for about (\d+)\\% of baseline TPR",
        lambda gt: gt.detection_share_of_pipeline(),
        PCT0,
        "percent",
    ),
    _c(
        "05b.top3_share",
        "05b_statistical_significance.md",
        r"together contribute about (\d+)\\% of the summed negative",
        lambda gt: gt.top_n_harmful_share(3),
        PCT0,
        "percent",
    ),
    _c(
        "05b.top3_share_summary",
        "05b_statistical_significance.md",
        r"account for about (\d+)\\% of the summed negative",
        lambda gt: gt.top_n_harmful_share(3),
        PCT0,
        "percent",
    ),
    _c(
        "05b.llm_claude_dr",
        "05b_statistical_significance.md",
        r"\| Claude Code \| (\d+\.\d+) \| 5 \|",
        lambda gt: gt.llm_detection_rate("claude_code"),
        F3,
        "fraction",
    ),
    _c(
        "05b.llm_crewai_dr",
        "05b_statistical_significance.md",
        r"\| CrewAI \| (\d+\.\d+) \| 5 \|",
        lambda gt: gt.llm_detection_rate("crewai"),
        F3,
        "fraction",
    ),
    _c(
        "05b.summary_ms_mean",
        "05b_statistical_significance.md",
        r"Mean (\d+\.\d+)\\% \[95\\% CI",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "05b.summary_ci_low",
        "05b_statistical_significance.md",
        r"\[95\\% CI: (\d+\.\d+)\\%, \d+\.\d+\\%\]",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "05b.summary_ci_high",
        "05b_statistical_significance.md",
        r"\[95\\% CI: \d+\.\d+\\%, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "05b.summary_cv",
        "05b_statistical_significance.md",
        r"with CV = (\d+\.\d+) indicating",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "05b.summary_detection_delta",
        "05b_statistical_significance.md",
        r"Detection module \(\$\\Delta\\text\{TPR\} \\approx -([\d.]+)\$\) is the dominant",
        lambda gt: gt.component_delta_magnitude("detection"),
        F3,
        "fraction",
    ),
    _c(
        "05b.summary_synergy",
        "05b_statistical_significance.md",
        r"strongest synergy \(\$\\approx \+([\d.]+)\$\), confirming",
        lambda gt: gt.synergy("tripwire", "detection"),
        F3,
        "fraction",
    ),
    _c(
        "05b.parametric_ceiling_low",
        "05b_statistical_significance.md",
        r"achieves (\d+)--\d+\\% detection, establishing",
        lambda gt: gt.parametric_dr_min(),
        PCT0,
        "percent",
        "parametric",
    ),
    _c(
        "05b.parametric_ceiling_high",
        "05b_statistical_significance.md",
        r"achieves \d+--(\d+)\\% detection, establishing",
        lambda gt: gt.parametric_dr_max(),
        PCT0,
        "percent",
        "parametric",
    ),
) + _component_claims(
    "05b_statistical_significance.md",
    {
        "detection": "Detection module",
        "tripwire": "Tripwire",
        "invariants": "Invariants",
        "firewall": "Firewall",
        "trust_calculus": "Trust Calculus",
        "provenance": "Provenance",
        "sandbox": "Sandbox",
        "consensus": "Consensus",
    },
    prefix="05b",
    positive_deltas=("sandbox", "consensus"),
) + _synergy_claims("05b_statistical_significance.md", prefix="05b")

_ABLATION: tuple[Claim, ...] = (
    _c(
        "05d.intro_detection_delta",
        "05d_ablation_and_scalability.md",
        r"largest marginal drop \(\$\\Delta\\text\{TPR\} \\approx -([\d.]+)\$\)",
        lambda gt: gt.component_delta_magnitude("detection"),
        F3,
        "fraction",
    ),
    _c(
        "05d.intro_synergy",
        "05d_ablation_and_scalability.md",
        r"strongest positive synergy \(\$\\approx \+([\d.]+)\$ beyond",
        lambda gt: gt.synergy("tripwire", "detection"),
        F3,
        "fraction",
    ),
    _c(
        "05d.corpus_size",
        "05d_ablation_and_scalability.md",
        r"stratified (\d+)-attack corpus",
        lambda gt: gt.ablation_corpus_size(),
        EXACT,
        "count",
    ),
    _c(
        "05d.full_pipeline_tpr",
        "05d_ablation_and_scalability.md",
        r"The full pipeline achieves \$\\sim\$(\d+)\\% TPR on this corpus",
        lambda gt: gt.full_pipeline_tpr(),
        PCT_APPROX,
        "percent",
    ),
    _c(
        "05d.ms_mean",
        "05d_ablation_and_scalability.md",
        r"multi-seed analysis shows \$\\sim\$(\d+\.\d+)\\% mean DR",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
) + _component_claims(
    "05d_ablation_and_scalability.md",
    {
        "detection": "Detection module",
        "tripwire": "Tripwires",
        "invariants": "Invariants",
        "firewall": "Firewall",
        "trust_calculus": "Trust Calculus",
        "provenance": "Provenance",
        "sandbox": "Sandbox",
        "consensus": "Consensus",
    },
    prefix="05d",
    positive_deltas=("sandbox", "consensus"),
) + _synergy_claims("05d_ablation_and_scalability.md", prefix="05d")

_DISCUSSION: tuple[Claim, ...] = (
    _c(
        "06.evidence_ms_mean",
        "06_discussion.md",
        r"\| Mean detection rate \| (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "06.evidence_ci_low",
        "06_discussion.md",
        r"\| Mean detection rate \| \d+\.\d+\\% \[CI: (\d+\.\d+)\\%",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "06.evidence_ci_high",
        "06_discussion.md",
        r"\| Mean detection rate \| \d+\.\d+\\% \[CI: \d+\.\d+\\%, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "06.evidence_ablation_tpr",
        "06_discussion.md",
        r"\| Full pipeline TPR \| (\d+\.\d+)\\%",
        lambda gt: gt.full_pipeline_tpr(),
        PCT1,
        "percent",
    ),
    _c(
        "06.evidence_detection_share",
        "06_discussion.md",
        r"Detection module \$=\$ (\d+)\\% of detection",
        lambda gt: gt.detection_share_of_pipeline(),
        PCT0,
        "percent",
    ),
    _c(
        "06.synthesis_ms_mean",
        "06_discussion.md",
        r"mean detection rate of (\d+\.\d+)\\% \[95\\% CI",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "06.synthesis_ci_low",
        "06_discussion.md",
        r"\[95\\% CI: (\d+\.\d+)\\%, \d+\.\d+\\%\]",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "06.synthesis_ci_high",
        "06_discussion.md",
        r"\[95\\% CI: \d+\.\d+\\%, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "06.colony_dr_low",
        "06_discussion.md",
        r"colony benchmarks demonstrate (\d+)--\d+\\% detection",
        lambda gt: gt.colony_structured_dr_min(),
        PCT0,
        "percent",
    ),
    _c(
        "06.colony_dr_high",
        "06_discussion.md",
        r"colony benchmarks demonstrate \d+--(\d+)\\% detection",
        lambda gt: gt.colony_structured_dr_max(),
        PCT0,
        "percent",
    ),
    _c(
        "06.parametric_ceiling_low",
        "06_discussion.md",
        r"design-level ceiling of (\d+)--\d+\\%",
        lambda gt: gt.parametric_dr_min(),
        PCT0,
        "percent",
        "parametric",
    ),
    _c(
        "06.parametric_ceiling_high",
        "06_discussion.md",
        r"design-level ceiling of \d+--(\d+)\\%",
        lambda gt: gt.parametric_dr_max(),
        PCT0,
        "percent",
        "parametric",
    ),
)

_CONCLUSION: tuple[Claim, ...] = (
    _c(
        "07.ms_mean",
        "07_conclusion.md",
        r"mean DR = (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "07.full_pipeline_tpr",
        "07_conclusion.md",
        r"full pipeline TPR = (\d+\.\d+)\\%",
        lambda gt: gt.full_pipeline_tpr(),
        PCT1,
        "percent",
    ),
    _c(
        "07.ablation_corpus_size",
        "07_conclusion.md",
        r"real ablation studies \((\d+)-attack corpus",
        lambda gt: gt.ablation_corpus_size(),
        EXACT,
        "count",
    ),
    _c(
        "07.bayes_ms_mean",
        "07_conclusion.md",
        r"\(mean (\d+\.\d+)\\%, 95\\% HDI",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "07.gap_pipeline_mean",
        "07_conclusion.md",
        r"pipeline mean (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "07.gap_ablation_tpr",
        "07_conclusion.md",
        r"ablation (\d+\.\d+)\\% respectively",
        lambda gt: gt.full_pipeline_tpr(),
        PCT1,
        "percent",
    ),
    _c(
        "07.current_ms_mean",
        "07_conclusion.md",
        r"Mean (\d+\.\d+)\\% \[CI:",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "07.current_ci_low",
        "07_conclusion.md",
        r"\[CI: (\d+\.\d+)\\%, \d+\.\d+\\%\]",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "07.current_ci_high",
        "07_conclusion.md",
        r"\[CI: \d+\.\d+\\%, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "07.current_cv",
        "07_conclusion.md",
        r"CV = (\d+\.\d+);",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "07.n_seeds",
        "07_conclusion.md",
        r"across (\d+) seeds on Claude Code",
        lambda gt: gt.ms_n(),
        EXACT,
        "count",
    ),
    _c(
        "07.parametric_ceiling_low",
        "07_conclusion.md",
        r"coverage ceiling at (\d+)--\d+\\%",
        lambda gt: gt.parametric_dr_min(),
        PCT0,
        "percent",
        "parametric",
    ),
    _c(
        "07.parametric_ceiling_high",
        "07_conclusion.md",
        r"coverage ceiling at \d+--(\d+)\\%",
        lambda gt: gt.parametric_dr_max(),
        PCT0,
        "percent",
        "parametric",
    ),
)

_SETUP: tuple[Claim, ...] = (
    _c(
        "04.parametric_instances",
        "04_experimental_setup.md",
        r"Simulation-Based Analysis \(\$N=([\d{},]+)\$\)",
        lambda gt: gt.parametric_instances(),
        EXACT,
        "count",
        "parametric",
    ),
    _c(
        "04.eval_instances",
        "04_experimental_setup.md",
        r"\$950 \\times 4 = ([\d{},]+)\$ evaluation instances",
        lambda gt: gt.parametric_instances(),
        EXACT,
        "count",
        "parametric",
    ),
    _c(
        "04.attack_corpus_size",
        "04_experimental_setup.md",
        r"full (\d+)-attack corpus through the assembled",
        lambda gt: gt.attack_corpus_size(),
        EXACT,
        "count",
        "parametric",
    ),
    _c(
        "04.pipeline_classified",
        "04_experimental_setup.md",
        r"classified \$\\sim\$(\d+\.\d+)\\% as attacks",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "04.power_ms_dr",
        "04_experimental_setup.md",
        r"\| Multi-seed pipeline \(30 seeds\) \| 30 \| DR = (\d+\.\d+) \|",
        lambda gt: gt.ms_mean(),
        F3,
        "fraction",
    ),
    _c(
        "04.summary_ms_mean",
        "04_experimental_setup.md",
        r"\| Multi-seed pipeline \(Claude Code, 30 seeds\) \| (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "04.summary_ci_low",
        "04_experimental_setup.md",
        r"\| Multi-seed pipeline \(Claude Code, 30 seeds\) \| \d+\.\d+\\% \[(\d+\.\d+),",
        lambda gt: gt.ms_ci_low(),
        PCT1,
        "percent",
    ),
    _c(
        "04.summary_ci_high",
        "04_experimental_setup.md",
        r"\| Multi-seed pipeline \(Claude Code, 30 seeds\) \| \d+\.\d+\\% "
        r"\[\d+\.\d+, (\d+\.\d+)\\%\]",
        lambda gt: gt.ms_ci_high(),
        PCT1,
        "percent",
    ),
    _c(
        "04.summary_ablation_tpr",
        "04_experimental_setup.md",
        r"\| Ablation pipeline \(full, \d+-attack corpus\) \| (\d+\.\d+)\\%",
        lambda gt: gt.full_pipeline_tpr(),
        PCT1,
        "percent",
    ),
    _c(
        "04.summary_ablation_n",
        "04_experimental_setup.md",
        r"\| Ablation pipeline \(full, \d+-attack corpus\) \| \d+\.\d+\\% \| \$N=(\d+)\$",
        lambda gt: gt.ablation_corpus_size(),
        EXACT,
        "count",
    ),
    _c(
        "04.note_ms_mean",
        "04_experimental_setup.md",
        r"multi-seed mean of (\d+\.\d+)\\%",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "04.baseline_ms_mean",
        "04_experimental_setup.md",
        r"mean DR = (\d+\.\d+)\\%, CV = ",
        lambda gt: gt.ms_mean(),
        PCT1,
        "percent",
    ),
    _c(
        "04.baseline_cv",
        "04_experimental_setup.md",
        r"mean DR = \d+\.\d+\\%, CV = (\d+\.\d+)",
        lambda gt: gt.ms_cv(),
        F3,
        "fraction",
    ),
    _c(
        "04.trust_calculus_delta",
        "04_experimental_setup.md",
        r"marginal contribution of \$\\Delta\\text\{TPR\} = -([\d.]+)\$",
        lambda gt: gt.component_delta_magnitude("trust_calculus"),
        F3,
        "fraction",
    ),
    _c(
        "04.sybil_detection",
        "04_experimental_setup.md",
        r"which achieved (\d+)\\% detection at 0\\% FPR",
        lambda gt: gt.colony_field("sybil_infiltration", "detection_rate"),
        PCT0,
        "percent",
    ),
    _c(
        "04.parametric_ceiling_low",
        "04_experimental_setup.md",
        r"\| Parametric simulation \(design ceiling\) \| (\d+)--\d+\\%",
        lambda gt: gt.parametric_dr_min(),
        PCT0,
        "percent",
        "parametric",
    ),
    _c(
        "04.parametric_ceiling_high",
        "04_experimental_setup.md",
        r"\| Parametric simulation \(design ceiling\) \| \d+--(\d+)\\%",
        lambda gt: gt.parametric_dr_max(),
        PCT0,
        "percent",
        "parametric",
    ),
)

_SUPPLEMENT: tuple[Claim, ...] = (
    _c(
        "S08.overall_dr",
        "S08_parametric_analysis.md",
        r"\| Detection Rate \(simulation\) \| (\d+\.\d+) \|",
        lambda gt: gt.parametric_overall_dr(),
        F3,
        "fraction",
        "parametric",
    ),
    _c(
        "S08.autogpt_dr",
        "S08_parametric_analysis.md",
        r"\| Detection Rate — AutoGPT only \| (\d+\.\d+) \|",
        lambda gt: gt.parametric_arch_dr("AutoGPT"),
        F3,
        "fraction",
        "parametric",
    ),
    _c(
        "S08.parametric_instances",
        "S08_parametric_analysis.md",
        r"parametric simulation \(\$N=([\d{},]+)\$\), not from live",
        lambda gt: gt.parametric_instances(),
        EXACT,
        "count",
        "parametric",
    ),
)

#: Every claim the reader-side checker enforces.
CLAIMS: tuple[Claim, ...] = (
    _ABSTRACT
    + _RESULTS
    + _STATISTICAL
    + _ABLATION
    + _DISCUSSION
    + _CONCLUSION
    + _SETUP
    + _SUPPLEMENT
)


def claim_ids() -> tuple[str, ...]:
    """Every registered claim id, in registry order."""
    return tuple(claim.id for claim in CLAIMS)
