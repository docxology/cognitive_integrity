"""Tests for the program-level series integrity gate.

Two obligations are tested here, and the second matters more than the first.

1. The gate reports the defects it is supposed to report on the live tree.
2. The gate *can fail*.  A checker that always returns PASS is worse than no
   checker, because it converts an unexamined tree into a green badge.  Every
   check below is therefore also driven against a synthetic tree containing a
   planted defect, and is required to catch it.  The anti-vacuity assertions
   (a pattern that matches nothing is a failure, not a skip) are tested the
   same way.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "scripts" / "check_series_integrity.py"


def _load_module(monkeypatch_root: Path | None = None):
    """Import the gate fresh, optionally rooted at a synthetic tree."""
    spec = importlib.util.spec_from_file_location(
        f"check_series_integrity_{id(monkeypatch_root)}", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if monkeypatch_root is not None:
        module.REPO_ROOT = monkeypatch_root
        module.DATA_DIR = monkeypatch_root / module.PARTS["2"] / "output" / "data"
        # The gate sources its quantities from series_ledger, which carries its
        # own REPO_ROOT, DATA_DIR and artifact cache. Rerooting only the gate
        # would leave every deriver reading the real repository, and the tests
        # would silently assert against production data.
        ledger = sys.modules.get("series_ledger")
        if ledger is not None:
            ledger.REPO_ROOT = monkeypatch_root
            ledger.DATA_DIR = module.DATA_DIR
            ledger._CACHE.clear()
    return module


@pytest.fixture(scope="module")
def gate():
    return _load_module()


# ---------------------------------------------------------------------------
# Synthetic tree
# ---------------------------------------------------------------------------

#: Four architectures x 950 attacks, min cell 0.96, max 1.00 -- the same shape
#: as the real full_evaluation_results.json so the fixture exercises the real
#: derivers rather than a degenerate special case.
_PARAMETRIC_ROWS = [
    {"architecture": arch, "n_attacks": n, "detection_rate": rate}
    for arch, (n, rate) in (
        ("A", (500, 0.96)),
        ("A", (450, 1.0)),
        ("B", (500, 0.98)),
        ("B", (450, 1.0)),
        ("C", (500, 1.0)),
        ("C", (450, 1.0)),
        ("D", (500, 0.99)),
        ("D", (450, 1.0)),
    )
]

_CLEAN_BIB = """@article{real2024work,
  author = {Ada Lovelace and Alan Turing},
  title  = {A Clean Entry},
  year   = {2024},
  doi    = {10.1000/clean}
}
"""


def _build_tree(root: Path, *, part_text: dict[str, str], bibs: dict[str, str]) -> Path:
    gate = _load_module()
    for part, package in gate.PARTS.items():
        manuscript = root / package / "manuscript"
        manuscript.mkdir(parents=True, exist_ok=True)
        (manuscript / "01_body.md").write_text(
            part_text.get(part, "# Body\n\nNothing to see.\n"), encoding="utf-8"
        )
        (manuscript / "references.bib").write_text(
            bibs.get(part, _CLEAN_BIB), encoding="utf-8"
        )
    # domain_count derives structurally, by counting Part 3's 09c..09l section
    # files rather than reading a typed number, so the fixture must have them.
    p3 = root / gate.PARTS["3"] / "manuscript"
    for letter in "cdefghijkl":
        (p3 / f"09{letter}_domain.md").write_text(
            f"# Domain {letter}\n\nA domain section.\n", encoding="utf-8"
        )

    data = root / gate.PARTS["2"] / "output" / "data"
    data.mkdir(parents=True, exist_ok=True)
    for name, payload in _ARTIFACTS.items():
        (data / name).write_text(json.dumps(payload), encoding="utf-8")
    return root


#: A complete synthetic artifact set: every file the ledger derives from, with
#: the same shape as the real ones. Values are chosen so the fixture prose below
#: is internally consistent (ceiling 96--100, mean 44.8, corpus 950, 4 arches).
_ARTIFACTS: dict[str, object] = {
    "full_evaluation_results.json": _PARAMETRIC_ROWS,
    "multi_seed_results.json": {
        "data_origin": "real_pipeline",
        "tpr_mean": 0.448,
        "fpr_mean": 0.2575,
        "overall_cv": 0.0967,
        "n_seeds": 30,
    },
    "ablation_results.json": {
        "data_origin": "real_pipeline",
        "full_pipeline": {"tpr": 12 / 98},
        "component_removal": [
            {"removed": "detection", "delta_tpr": -5 / 98},
            {"removed": "trust_calculus", "delta_tpr": -2 / 98},
            {"removed": "firewall", "delta_tpr": -1 / 98},
            {"removed": "invariants", "delta_tpr": -1 / 98},
            {"removed": "tripwire", "delta_tpr": -1 / 98},
            {"removed": "consensus", "delta_tpr": 0.0},
        ],
        "top_synergies": [
            {"a": "firewall", "b": "detection", "synergy": 3 / 98},
            {"a": "tripwire", "b": "detection", "synergy": 3 / 98},
            {"a": "firewall", "b": "trust_calculus", "synergy": 2 / 98},
        ],
    },
    "colony_results.json": {
        "data_origin": "real_pipeline",
        "scenarios": [
            {
                "scenario": "emergent_misalignment",
                "detection_rate_mean": 0.743,
                "false_positive_rate_mean": 0.255,
            }
        ],
    },
    "cross_validation_results.json": {"data_origin": "real_pipeline", "k": 5, "mean_tpr": 0.16},
    "scalability_results.json": {
        "data_origin": "real_pipeline",
        "framework_track": [{"n_agents": 2}, {"n_agents": 100}],
    },
    "redteam_evaluation_results.json": {"data_origin": "real_pipeline", "n_attacks_generated": 950},
    "adversarial_training_results.json": {
        "source_script": "scripts/run_adversarial_training.py",
        "baseline_dr": 0.447,
        "final_hardened_dr": 0.679,
        "total_delta_dr": 0.232,
        "n_rounds": 5,
    },
}


def _body(ceiling: str = "96") -> str:
    """A minimal body carrying every gated quantity exactly once.

    Every gated quantity must appear, because the gate treats a pattern that
    matches nothing as a failure -- a fixture that omitted one would trip the
    anti-vacuity guard rather than the check under test.

    The numbers are computed from ``_ARTIFACTS`` rather than typed, for the same
    reason the manuscripts must not type them: a fixture with its own hardcoded
    copy of a value drifts from the artifact the moment either changes, and then
    the test asserts against a number nobody derived.
    """
    ms = _ARTIFACTS["multi_seed_results.json"]
    abl = _ARTIFACTS["ablation_results.json"]
    colony = _ARTIFACTS["colony_results.json"]["scenarios"][0]
    rows = _ARTIFACTS["full_evaluation_results.json"]

    mean = ms["tpr_mean"] * 100
    fpr = ms["fpr_mean"] * 100
    seeds = ms["n_seeds"]
    instances = sum(int(r["n_attacks"]) for r in rows)
    per_arch = sum(int(r["n_attacks"]) for r in rows if r["architecture"] == "A")
    n_arch = len({r["architecture"] for r in rows})
    abl_n = round(1 / min(abs(c["delta_tpr"]) for c in abl["component_removal"] if c["delta_tpr"]))
    emergent = colony["detection_rate_mean"] * 100
    low = int(ceiling) - mean
    high = 100 - abl["full_pipeline"]["tpr"] * 100

    return (
        "# Body\n\n"
        f"The parametric simulation establishes a design-level ceiling of "
        f"{ceiling}--100\\% across the sweep.\n\n"
        f"Treat {ceiling}\\% as the achievable ceiling with mature adapters.\n\n"
        f"We evaluate over a {per_arch}-attack corpus spanning {_word(n_arch)} production "
        "multiagent architectures.\n\n"
        f"The parametric simulation ($N = 3{{,}}{instances - 3000}$) covers every cell.\n\n"
        f"The pipeline achieves a mean detection rate of {mean:.1f}\\% across {seeds} seeds.\n\n"
        f"That multi-seed pipeline arm shows a {fpr:.1f}\\% false-positive rate.\n\n"
        f"Ablation uses a {abl_n}-attack ablation corpus; the {abl_n}-attack ablation corpus "
        "is a stratified subsample.\n\n"
        f"Emergent misalignment detection reaches {emergent:.1f}\\%.\n\n"
        f"There is a {low:.0f}--{high:.0f} percentage-point gap to close.\n\n"
        "The study spans ten domains; those ten domains are analysed in turn.\n\n"
        "Data from `output/data/multi_seed_results.json`.\n"
    )


def _word(n: int) -> str:
    return {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}.get(n, str(n))


CEILING_OK = _body("96")
CEILING_WRONG = _body("94")


@pytest.fixture
def clean_tree(tmp_path):
    return _build_tree(
        tmp_path / "clean",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={},
    )


# ---------------------------------------------------------------------------
# The gate can fail (test of the test)
# ---------------------------------------------------------------------------


def test_clean_tree_passes_every_check(clean_tree):
    """Baseline: without a planted defect the synthetic tree is green.

    If this ever fails, the negative tests below prove nothing.
    """
    module = _load_module(clean_tree)
    for name in ("shared-quantities", "bibliography", "truncation", "math-hygiene",
                 "artifact-provenance", "cross-paper-pointers"):
        result = module.CHECKS[name]()
        assert result.ok, f"{name} flagged a clean tree: {[p.message for p in result.problems]}"


def test_shared_quantities_catches_a_disagreeing_number(tmp_path):
    tree = _build_tree(
        tmp_path / "drift",
        part_text={"1": CEILING_WRONG, "2": CEILING_OK, "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["shared-quantities"]()
    assert not result.ok
    assert any(
        "states 94" in p.message and "gives 96" in p.message for p in result.problems
    ), [p.message for p in result.problems]


def test_shared_quantities_fails_when_a_pattern_matches_nothing(tmp_path):
    """Anti-vacuity: a guard that stops matching must fail, not silently pass."""
    tree = _build_tree(
        tmp_path / "vacuous",
        part_text={"1": "# Body\n\nNo numbers here.\n"},
        bibs={},
    )
    module = _load_module(tree)
    # Strip every ceiling sentence so the pattern matches zero lines.
    for part in module.PARTS.values():
        (tree / part / "manuscript" / "01_body.md").write_text(
            "# Body\n\nNo numbers here.\n", encoding="utf-8"
        )
    result = module.CHECKS["shared-quantities"]()
    assert not result.ok
    assert any("broken guard" in p.message for p in result.problems)


def test_shared_quantities_fails_when_the_artifact_is_missing(tmp_path):
    tree = _build_tree(
        tmp_path / "noartifact",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "full_evaluation_results.json").unlink()
    result = module.CHECKS["shared-quantities"]()
    assert not result.ok
    assert any("cannot derive ground truth" in p.message for p in result.problems)


def test_bibliography_catches_a_duplicate_work_under_two_keys(tmp_path):
    duplicated = _CLEAN_BIB + """
@inproceedings{real2024work_again,
  author = {Ada Lovelace and Alan Turing},
  title  = {A Clean Entry},
  year   = {2024}
}
"""
    tree = _build_tree(
        tmp_path / "dupe",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={"1": duplicated},
    )
    module = _load_module(tree)
    result = module.CHECKS["bibliography"]()
    assert not result.ok
    assert any("duplicate work" in p.message for p in result.problems)


def test_bibliography_matches_on_the_work_not_the_bibkey(tmp_path):
    """The defect is one work under two keys, so keys must not be the identity."""
    renamed = """@article{entirely_different_key,
  author = {Ada Lovelace and Alan Turing},
  title  = {A Clean Entry},
  year   = {2024},
  doi    = {10.1000/clean}
}

@article{yet_another_key,
  author = {Ada Lovelace and Alan Turing},
  title  = {A  Clean   Entry},
  year   = {2024},
  doi    = {10.1000/clean}
}
"""
    tree = _build_tree(
        tmp_path / "renamed",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={"2": renamed},
    )
    module = _load_module(tree)
    result = module.CHECKS["bibliography"]()
    assert not result.ok
    assert any("duplicate work" in p.message for p in result.problems)


def test_bibliography_catches_cross_file_metadata_disagreement(tmp_path):
    other = _CLEAN_BIB.replace("Alan Turing", "Grace Hopper")
    tree = _build_tree(
        tmp_path / "disagree",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={"3": other},
    )
    module = _load_module(tree)
    result = module.CHECKS["bibliography"]()
    assert not result.ok
    assert any("author disagrees" in p.message for p in result.problems)


def test_truncation_catches_a_severed_final_clause(tmp_path):
    tree = _build_tree(
        tmp_path / "cut",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK + "\n## Implications\n\nThe results have implications across the\n",
            "3": CEILING_OK,
        },
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["truncation"]()
    assert not result.ok
    assert any("ends mid-sentence" in p.message for p in result.problems)


def test_truncation_catches_a_heading_with_no_body(tmp_path):
    tree = _build_tree(
        tmp_path / "emptysection",
        part_text={"1": CEILING_OK, "2": CEILING_OK + "\n## Orphan Section\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["truncation"]()
    assert not result.ok
    assert any("has no body" in p.message for p in result.problems)


@pytest.mark.parametrize(
    "ending",
    [
        "A finished sentence.",
        "*An italic run that finishes.*",
        "| a | table | row |",
        "- a list item",
        "\\newpage",
        "```",
    ],
)
def test_truncation_accepts_legitimate_file_endings(tmp_path, ending):
    tree = _build_tree(
        tmp_path / f"ok{abs(hash(ending))}",
        part_text={"1": CEILING_OK, "2": CEILING_OK + f"\n{ending}\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    assert module.CHECKS["truncation"]().ok


def test_cross_paper_pointers_rejects_a_hardcoded_number(tmp_path):
    tree = _build_tree(
        tmp_path / "pointer",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK + "\nAs shown in Part 1, Theorem 3.2a, the rate composes.\n",
            "3": CEILING_OK,
        },
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["cross-paper-pointers"]()
    assert not result.ok
    assert any("hardcoded cross-paper pointer" in p.message for p in result.problems)


def test_cross_paper_pointers_accepts_a_named_reference(tmp_path):
    tree = _build_tree(
        tmp_path / "named",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK
            + "\nAs shown by Part 1's Series Detection Rate theorem, the rate composes.\n",
            "3": CEILING_OK,
        },
        bibs={},
    )
    module = _load_module(tree)
    assert module.CHECKS["cross-paper-pointers"]().ok


def test_cross_paper_pointers_ignores_self_references(tmp_path):
    """Part 2 citing its own §5 is the per-part verifier's business, not ours."""
    tree = _build_tree(
        tmp_path / "self",
        part_text={"1": CEILING_OK, "2": CEILING_OK + "\nSee Part 2, Section 5.1.\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    assert module.CHECKS["cross-paper-pointers"]().ok



def test_math_hygiene_catches_a_double_escaped_command(tmp_path):
    tree = _build_tree(
        tmp_path / "doubleesc",
        part_text={"1": CEILING_OK, "2": CEILING_OK + "\nSee \\\\cref{sec:x} for detail.\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["math-hygiene"]()
    assert not result.ok
    assert any("double-escaped" in p.message for p in result.problems)


def test_math_hygiene_catches_a_subscript_star(tmp_path):
    tree = _build_tree(
        tmp_path / "star",
        part_text={"1": CEILING_OK, "2": CEILING_OK + "\nThe ratio $\\mathcal{F}*c(x)$ holds.\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["math-hygiene"]()
    assert not result.ok
    assert any("subscript-star" in p.message for p in result.problems)


def test_math_hygiene_allows_legitimately_starred_commands(tmp_path):
    tree = _build_tree(
        tmp_path / "legitstar",
        part_text={"1": CEILING_OK, "2": CEILING_OK + "\n\\vspace*{1em}\n", "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    assert module.CHECKS["math-hygiene"]().ok


def test_artifact_provenance_rejects_an_undeclared_artifact(tmp_path):
    tree = _build_tree(
        tmp_path / "undeclared",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/mystery.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "mystery.json").write_text(json.dumps({"values": [1, 2]}), encoding="utf-8")
    result = module.CHECKS["artifact-provenance"]()
    assert not result.ok
    assert any("declares no provenance" in p.message for p in result.problems)


def test_artifact_provenance_rejects_a_self_declared_placeholder(tmp_path):
    tree = _build_tree(
        tmp_path / "placeholder",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/fake.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "fake.json").write_text(
        json.dumps({"data_origin": "synthetic", "values": [1]}), encoding="utf-8"
    )
    result = module.CHECKS["artifact-provenance"]()
    assert not result.ok
    assert any("a placeholder, not a result" in p.message for p in result.problems)


def test_artifact_provenance_accepts_a_declared_non_measured_origin(tmp_path):
    """The paper separates measured from parametric; both are honest if declared."""
    tree = _build_tree(
        tmp_path / "parametric",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/sim.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "sim.json").write_text(
        json.dumps({"data_origin": "parametric_simulation", "values": [1]}), encoding="utf-8"
    )
    assert module.CHECKS["artifact-provenance"]().ok


def test_artifact_provenance_rejects_a_citation_of_a_missing_file(tmp_path):
    tree = _build_tree(
        tmp_path / "missingfile",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/absent.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["artifact-provenance"]()
    assert not result.ok
    assert any("does not exist" in p.message for p in result.problems)


def test_bare_ceiling_form_is_gated_and_excludes_range_digits(gate):
    """A ceiling written as one number must be checked; "100" must not be read as "00"."""
    q = next(x for x in gate.SHARED_QUANTITIES if x.id == "parametric_ceiling_low_bare")
    stale = "Use 94\\% as the achievable ceiling with mature adapters"
    hits = [m.group(1) for m in q.pattern.finditer(stale) if q.in_scope(stale, m)]
    assert hits == ["94"], hits
    ranged = "a design-level ceiling of 96--100\\% across the sweep"
    assert [m.group(1) for m in q.pattern.finditer(ranged) if q.in_scope(ranged, m)] == []

# ---------------------------------------------------------------------------
# Structural invariants of the registry itself
# ---------------------------------------------------------------------------


def test_every_gated_quantity_has_exactly_one_capturing_group(gate):
    for quantity in gate.SHARED_QUANTITIES:
        if quantity.pattern is None:
            continue
        assert quantity.pattern.groups == 1, quantity.id


def test_every_gated_quantity_declares_context_keywords(gate):
    """A gated pattern without context collides with same-shaped neighbours."""
    for quantity in gate.SHARED_QUANTITIES:
        if quantity.pattern is None:
            continue
        assert quantity.require, quantity.id


def test_every_ledger_variable_derives_from_the_real_artifacts(gate):
    """Anti-vacuity: a deriver that raises would silently stop gating."""
    import series_ledger

    failures = []
    for var in series_ledger.LEDGER:
        try:
            var.value()
        except Exception as exc:  # noqa: BLE001 - report, never mask
            failures.append(f"{var.id}: {type(exc).__name__}: {exc}")
    assert not failures, failures


def test_the_ledger_gates_a_meaningful_share_of_its_variables(gate):
    import series_ledger

    gated = [v for v in series_ledger.LEDGER if v.pattern is not None]
    assert len(series_ledger.LEDGER) >= 25, len(series_ledger.LEDGER)
    assert len(gated) >= 12, len(gated)


def test_shared_quantity_ids_are_unique(gate):
    ids = [q.id for q in gate.SHARED_QUANTITIES]
    assert len(ids) == len(set(ids))


def test_context_window_excludes_a_neighbouring_arm(gate):
    """The abstract carries three same-shaped ranges in one sentence."""
    line = (
        "colony benchmarks at 81--100\\% detection and the parametric ceiling at "
        "96--100\\% across four architectures"
    )
    quantity = next(
        q for q in gate.SHARED_QUANTITIES if q.id == "parametric_ceiling_low"
    )
    accepted = [m.group(1) for m in quantity.pattern.finditer(line) if quantity.in_scope(line, m)]
    assert "81" not in accepted


def test_exit_code_is_nonzero_when_a_check_fails(tmp_path, capsys):
    tree = _build_tree(
        tmp_path / "exitcode",
        part_text={"1": CEILING_WRONG, "2": CEILING_OK, "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    assert module.main(["--only", "shared-quantities"]) == 1


def test_json_output_is_machine_readable(clean_tree, capsys):
    module = _load_module(clean_tree)
    module.main(["--only", "truncation", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["truncation"]["ok"] is True
    assert payload["truncation"]["scanned"] > 0


def test_bib_parser_handles_nested_braces_and_quoted_values(gate, tmp_path):
    path = tmp_path / "nested.bib"
    path.write_text(
        '@article{k,\n'
        '  title = {{OWASP} Top 10 for {LLM} Applications},\n'
        '  author = "Doe, Jane",\n'
        '  year = {2025}\n'
        '}\n',
        encoding="utf-8",
    )
    entries = gate.parse_bib(path)
    assert len(entries) == 1
    assert entries[0].fields["title"] == "{OWASP} Top 10 for {LLM} Applications"
    assert entries[0].fields["author"] == "Doe, Jane"


def test_normalise_title_ignores_case_braces_and_spacing(gate):
    assert gate.normalise_title("{OWASP}  Top-10 for LLMs") == gate.normalise_title(
        "owasp top 10 for llms"
    )
