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
    {"architecture": arch, "attack_category": cat, "n_attacks": n, "detection_rate": rate}
    for arch, cat, n, rate in (
        ("A", "direct_injection", 500, 0.99),
        ("A", "impersonation", 450, 0.96),
        ("B", "direct_injection", 500, 1.0),
        ("B", "impersonation", 450, 0.98),
        ("C", "direct_injection", 500, 1.0),
        ("C", "impersonation", 450, 1.0),
        ("D", "direct_injection", 500, 1.0),
        ("D", "impersonation", 450, 0.99),
    )
]

_CLEAN_BIB = """@article{real2024work,
  author = {Ada Lovelace and Alan Turing},
  title  = {A Clean Entry},
  year   = {2024},
  doi    = {10.1000/clean}
}
"""


#: Fixture threshold defaults. Distinct from production (0.8 / 0.5 / 0.7) on
#: purpose -- see the comment in _build_tree.
FIXTURE_TAU1 = 0.77
FIXTURE_TAU2 = 0.33
FIXTURE_TAU1_REFERENCE = 0.66


def _build_tree(root: Path, *, part_text: dict[str, str], bibs: dict[str, str]) -> Path:
    gate = _load_module()
    for part, package in gate.PARTS.items():
        manuscript = root / package / "manuscript"
        manuscript.mkdir(parents=True, exist_ok=True)
        # Every body cites every key its part's bibliography defines. It did
        # not, and once the bibliography check began failing on an entry
        # nothing cites, "a clean tree" stopped being clean -- through the
        # fixture rather than through the gate. A fixture that models a
        # healthy tree has to model a closed bibliography too, and the
        # citations have to be appended to whatever body a test supplies
        # rather than only to the default one.
        body = part_text.get(part, "# Body\n\nNothing to see.\n")
        # Prepended, never appended: several tests plant a severed final clause
        # and the truncation check reads the end of the file, so a citation
        # added after the defect hides it.
        # Sentences the new ledger variables gate. A synthetic tree with no
        # HDI and no solo-detection line is not a clean tree, it is a tree
        # missing two gated quantities, and the guard is right to say so.
        gated = (
            "\nThe representative multi-seed estimate (mean 44.8\\%, 95\\% HDI "
            "[35.5\\%, 54.7\\%]) is reported with uncertainty.\n"
            "\nThe Invariants checker alone reaches 83.3\\% against the full stack.\n"
        )
        # Prepended, never appended: several tests plant a severed final clause
        # and the truncation check reads the end of the file.
        if part == "2" and "HDI" not in body:
            body = gated.split("\nThe Invariants")[0] + "\n" + body
        if part == "3" and "checker alone reaches" not in body:
            body = (
                "The Invariants checker alone reaches 83.3\\% against the full stack.\n\n"
                + body
            )

        citations = "".join(
            f"See [@{key}].\n"
            for key in re.findall(r"@\w+\{([^,]+),", bibs.get(part, _CLEAN_BIB))
            if f"@{key}" not in body
        )
        if citations:
            body = citations + "\n" + body
        (manuscript / "01_body.md").write_text(body, encoding="utf-8"
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

    # The firewall thresholds are the one published pair that lives in Python
    # rather than in a JSON artifact, so the fixture must ship the dataclasses
    # the derivers parse. The defaults here are deliberately NOT the production
    # ones: if a deriver ever ignored its argument and read the real tree, these
    # tests would keep passing against production data and prove nothing.
    src2 = root / gate.PARTS["2"] / "src" / "core"
    src2.mkdir(parents=True, exist_ok=True)
    (src2 / "firewall.py").write_text(
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\nclass FirewallConfig:\n"
        f"    injection_threshold: float = {FIXTURE_TAU1}\n"
        f"    suspicious_threshold: float = {FIXTURE_TAU2}\n",
        encoding="utf-8",
    )
    src1 = root / gate.PARTS["1"] / "src"
    src1.mkdir(parents=True, exist_ok=True)
    (src1 / "firewall.py").write_text(
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\nclass FirewallConfig:\n"
        f"    injection_threshold: float = {FIXTURE_TAU1_REFERENCE}\n",
        encoding="utf-8",
    )

    # multiseed_hdi_low/high load Part 2's BetaPosterior by file path rather
    # than by import, so the synthetic tree needs the file to exist. The real
    # module is copied rather than stubbed: a stub would let the fixture agree
    # with a posterior the shipped code does not compute.
    stats_dir = root / gate.PARTS["2"] / "src" / "statistics"
    stats_dir.mkdir(parents=True, exist_ok=True)
    real_bayesian = (
        Path(gate.REPO_ROOT) / gate.PARTS["2"] / "src" / "statistics" / "bayesian.py"
    )
    if real_bayesian.is_file():
        (stats_dir / "bayesian.py").write_text(
            real_bayesian.read_text(encoding="utf-8"), encoding="utf-8"
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
    # Read by invariants_solo_detection. Only the one path the ledger walks is
    # populated: a fixture that mirrored the whole real artifact would drift
    # from it, and this one exists to be internally consistent, not complete.
    "module_capability_matrix.json": {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_module_capability_matrix.py",
        "detection_rate": {"invariants": {"_overall": 0.833}},
    },
    "multi_seed_results.json": {
        "data_origin": "real_pipeline",
        "tpr_mean": 0.448,
        "fpr_mean": 0.2575,
        "overall_cv": 0.0967,
        "n_seeds": 30,
        # The interval endpoints are derived from the per-seed rates, so the
        # synthetic tree needs them too: without seed_metrics the two CI
        # variables cannot derive at all, and an underivable gated quantity is
        # a failure rather than a skip.
        "seed_metrics": [
            {"seed": i, "overall": rate}
            for i, rate in enumerate((0.43, 0.44, 0.448, 0.45, 0.46))
        ],
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
        # tpr_a/tpr_b are each mechanism's solo rate; ablation_series_prediction
        # recovers the set of mechanisms from these records, so they must be here.
        "top_synergies": [
            {"a": "firewall", "b": "detection", "synergy": 3 / 98,
             "tpr_a": 1 / 98, "tpr_b": 5 / 98, "fpr_a": 0.0, "fpr_b": 0.0},
            {"a": "tripwire", "b": "detection", "synergy": 3 / 98,
             "tpr_a": 1 / 98, "tpr_b": 5 / 98, "fpr_a": 0.0, "fpr_b": 0.0},
            {"a": "firewall", "b": "trust_calculus", "synergy": 2 / 98,
             "tpr_a": 1 / 98, "tpr_b": 2 / 98, "fpr_a": 0.0, "fpr_b": 0.0},
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
    "test_inventory.json": {
        "data_origin": "real_pipeline",
        "source_script": "scripts/collect_test_inventory.py",
        "per_part": {
            "cogsec_multiagent_1_theory": 441,
            "cogsec_multiagent_2_computational": 3380,
            "cogsec_multiagent_3_practical": 935,
        },
        "program_level": 49,
        "total": 4805,
    },
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
    _rates = [s["overall"] for s in ms["seed_metrics"]]
    _mu = sum(_rates) / len(_rates)
    _sd = (sum((r - _mu) ** 2 for r in _rates) / (len(_rates) - 1)) ** 0.5
    _half = 1.96 * _sd / len(_rates) ** 0.5
    ci_low, ci_high = (_mu - _half) * 100, (_mu + _half) * 100
    seeds = ms["n_seeds"]
    instances = sum(int(r["n_attacks"]) for r in rows)
    per_arch = sum(int(r["n_attacks"]) for r in rows if r["architecture"] == "A")
    n_arch = len({r["architecture"] for r in rows})
    abl_n = round(1 / min(abs(c["delta_tpr"]) for c in abl["component_removal"] if c["delta_tpr"]))
    emergent = colony["detection_rate_mean"] * 100
    low = int(ceiling) - mean
    high = 100 - abl["full_pipeline"]["tpr"] * 100
    tests_p2 = _ARTIFACTS["test_inventory.json"]["per_part"]["cogsec_multiagent_2_computational"]
    scal_track = [int(r["n_agents"]) for r in _ARTIFACTS["scalability_results.json"]["framework_track"]]
    di = [r["detection_rate"] for r in rows if r["attack_category"] == "direct_injection"]
    di_low, di_high = min(di) * 100, max(di) * 100
    full_tpr = abl["full_pipeline"]["tpr"] * 100
    solo = {}
    for pair in abl["top_synergies"]:
        for side in ("a", "b"):
            solo[pair[side]] = pair[f"tpr_{side}"]
    missed = 1.0
    for rate in solo.values():
        missed *= 1.0 - rate
    series_prediction = (1.0 - missed) * 100
    at = _ARTIFACTS["adversarial_training_results.json"]
    at_base = at["baseline_dr"] * 100
    at_hardened = at["final_hardened_dr"] * 100
    at_delta = at["total_delta_dr"] * 100
    at_rounds = at["n_rounds"]
    syn = _ARTIFACTS["ablation_results.json"]["top_synergies"]
    top_synergy = max(x["synergy"] for x in syn)
    colony_dr = colony["detection_rate_mean"] * 100
    colony_fpr = colony["false_positive_rate_mean"] * 100
    redteam_m = _ARTIFACTS["redteam_evaluation_results.json"]["n_attacks_generated"]

    return (
        "# Body\n\n"
        f"That arm's 95\\% CI: {ci_low:.1f}\\%, {ci_high:.1f}\\% brackets the mean.\n\n"
        f"The mutation-operator sweep runs against $M={redteam_m}$ generated attacks.\n\n"
        f"Its mutation-operator table is re-derived from that same $M={redteam_m}$ run.\n\n"
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
        f"Direct injection is detected at {di_low:.0f}--{di_high:.0f}\\%.\n\n"
        f"There is a {low:.0f}--{high:.0f} percentage-point gap to close.\n\n"
        "The study spans ten domains; those ten domains are analysed in turn.\n\n"
        f"The evidence includes {tests_p2:,} tests.\n\n"
        f"The scalability sweep covers the measured range "
        f"({min(scal_track)}--{max(scal_track)} agents).\n\n"
        f"The firewall's operational default $\\tau_1 = {FIXTURE_TAU1}$ rejects outright, "
        f"and its operational default $\\tau_2 = {FIXTURE_TAU2}$ quarantines.\\n\\n"
        f"Deployment ships that operational default: tau_1: {FIXTURE_TAU1} in the config.\\n\\n"
        f"Part 1's reference implementation deliberately uses {FIXTURE_TAU1_REFERENCE}.\\n\\n"
        f"The Round-5 hardened configuration reaches {at_hardened:.1f}\\% detection.\\n\\n"
        f"AT-Round-5 gives a cumulative improvement of +{at_delta:.1f} pp over the\\n"
        f"pre-AT baseline ({at_base:.1f}\\%).\\n\\n"
        f"The strongest pair shows a synergy of +{top_synergy:.4f} beyond additive.\\n\\n"
        f"Adversarial training ran for {at_rounds} rounds.\\n\\n"
        f"Emergent misalignment: {colony_dr:.1f}\\% detection at {colony_fpr:.1f}\\% FPR.\\n\\n"
        f"The composition rule predicts {series_prediction:.1f}\\% against a measured "
        f"{full_tpr:.1f}\\%.\\n\\n"
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


def test_cross_paper_pointers_catches_the_section_sign(tmp_path):
    """The section sign was absent from the pattern's alternation entirely.

    29 pointers written "Part 1 \\cite{...} \u00a74.3" were invisible while the check
    reported PASS at zero scanned, which reads as "there are none" rather than
    "I cannot see them". Both spellings the corpus uses are pinned here.
    """
    for text in ("Part 1 \\cite{friedman2026cogsec1} \u00a74.3", "Part~1, \\S 1.2"):
        tree = _build_tree(
            tmp_path / f"sign{abs(hash(text))}",
            part_text={"1": CEILING_OK, "2": CEILING_OK + f"\nSee {text} for the bound.\n", "3": CEILING_OK},
            bibs={},
        )
        module = _load_module(tree)
        result = module.CHECKS["cross-paper-pointers"]()
        assert not result.ok, f"the section sign in {text!r} was not seen"


def test_cross_paper_pointers_catches_a_possessive_reference(tmp_path):
    """"Part 1's Runtime Defenses section (Definition 5.6)" -- 28 characters of
    prose between the part and the kind word, where the budget was 24. Three
    pointers hid in that four-character margin.
    """
    tree = _build_tree(
        tmp_path / "possessive",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK + "\nThis implements Part 1's Runtime Defenses section (Definition 5.6).\n",
            "3": CEILING_OK,
        },
        bibs={},
    )
    module = _load_module(tree)
    assert not module.CHECKS["cross-paper-pointers"]().ok


def test_cross_paper_pointers_does_not_reach_across_an_unrelated_part(tmp_path):
    """The counterweight to the wider window.

    "Part 2 for the experimentalists, and the Applications section (\u00a79--\u00a710)"
    names Part 2 and then a section of the CITING paper. A window loose enough to
    span that would report a defect where there is none, and a check that cries
    wolf is a check that gets ignored.
    """
    tree = _build_tree(
        tmp_path / "acrosspart",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK,
            "3": CEILING_OK
            + "\nWe wrote Part 1 for the theorists, Part 2 for the experimentalists, "
            "and the Applications section (\u00a79--\u00a710) for domain experts.\n",
        },
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["cross-paper-pointers"]()
    assert result.ok, [p.message for p in result.problems]


def test_cross_paper_pointers_catches_plurals_and_both_orders(tmp_path):
    """Three shapes the check could not see, each real in the corpus.

    The alternation was singular, so "Part 1, Theorems 3.1-3.2" was invisible.
    The pattern required "Part N" to come first, so "Theorem 3.1 in Part 1" was
    invisible. And a pointer whose only part marker is the series bibkey --
    "Theorem 3.1 \\cite{friedman2026cogsec1}" -- named no part at all.
    """
    cases = (
        "Defenses compose predictably (Part 1, Theorems 3.1 and 3.2).",
        "The formal definition of Trust Update (Theorem 3.1 in Part 1) establishes decay.",
        "detection rate (series: Theorem 3.1 \\cite{friedman2026cogsec1}).",
    )
    for index, text in enumerate(cases):
        tree = _build_tree(
            tmp_path / f"form{index}",
            part_text={"1": CEILING_OK, "2": CEILING_OK + f"\n{text}\n", "3": CEILING_OK},
            bibs={},
        )
        module = _load_module(tree)
        assert not module.CHECKS["cross-paper-pointers"]().ok, f"missed: {text}"


def test_cross_paper_pointers_reports_one_site_once(tmp_path):
    """The three forms overlap. A line matched by two of them is one defect."""
    tree = _build_tree(
        tmp_path / "dedupe",
        part_text={
            "1": CEILING_OK,
            "2": CEILING_OK + "\nSee Section 7 of Part 1 \\cite{friedman2026cogsec1} for this.\n",
            "3": CEILING_OK,
        },
        bibs={},
    )
    module = _load_module(tree)
    result = module.CHECKS["cross-paper-pointers"]()
    assert len(result.problems) == 1, [p.message for p in result.problems]


def test_cross_paper_pointers_is_not_vacuous_when_the_glob_breaks(tmp_path):
    """`scanned` counts violations here, so zero is the CLEAN state.

    Every other check guards vacuity with `scanned == 0`, which for this one
    would mean "no defects" -- so a broken glob would read as a pass, in the one
    check whose whole purpose is catching what nothing else looks at.
    """
    tree = _build_tree(tmp_path / "vacuous", part_text={}, bibs={})
    module = _load_module(tree)
    module.manuscript_files = lambda part: []
    result = module.CHECKS["cross-paper-pointers"]()
    assert not result.ok
    assert any("glob is broken" in p.message for p in result.problems)


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


def test_every_artifact_the_ledger_reads_is_tracked_by_git():
    """A gate that cannot run on a clean clone is a gate nobody has.

    output/ is gitignored, and the shipped artifacts are force-added one at a
    time. Three that the ledger derives from had never been added, so CI's
    gating step would have failed on any fresh checkout with "cannot derive
    ground truth" -- red from the first build, for a reason unrelated to the
    manuscripts.
    """
    import subprocess

    # _load_module reroots the shared series_ledger module, and pytest may have
    # run a rerooted test first. Load a private copy pinned to the real repo.
    series_ledger = _load_module().__dict__["sys"].modules["series_ledger"]
    series_ledger.REPO_ROOT = REPO_ROOT
    series_ledger.DATA_DIR = REPO_ROOT / series_ledger.PARTS["2"] / "output" / "data"
    series_ledger._CACHE.clear()

    # Two populations must be tracked, and the first guard only covered one:
    # what the ledger *derives* from, and what the manuscripts *cite*. The
    # provenance check consults the second, which is strictly larger, so a clean
    # clone still failed after the ledger artifacts were added.
    from_ledger = {v.artifact for v in series_ledger.LEDGER if v.artifact.endswith(".json")}

    cited: set[str] = set()
    for part in series_ledger.PARTS:
        for path in series_ledger.manuscript_files(part):
            cited.update(
                re.findall(r"output/data/([A-Za-z0-9_.]+\.json)",
                           path.read_text(encoding="utf-8", errors="replace"))
            )
    # A list-shaped artifact carries provenance in a sidecar, which must ship too.
    sidecars = {
        f"{name[:-5]}.provenance.json"
        for name in cited | from_ledger
        if (REPO_ROOT / series_ledger.PARTS["2"] / "output" / "data"
            / f"{name[:-5]}.provenance.json").is_file()
    }

    needed = sorted(from_ledger | cited | sidecars)
    assert from_ledger, "the ledger names no artifacts; the introspection is broken"
    assert cited, "no manuscript cites an artifact; the scan is broken"

    root = REPO_ROOT
    missing = []
    for name in needed:
        rel = f"{series_ledger.PARTS['2']}/output/data/{name}"
        proc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=str(root), capture_output=True, text=True,
        )
        if proc.returncode != 0:
            missing.append(rel)
    assert not missing, (
        "ledger artifacts not tracked by git; a clean clone cannot run the gate. "
        f"git add -f each of: {missing}"
    )


def test_artifact_provenance_rejects_an_empty_sidecar(tmp_path):
    """A sidecar that exists but declares nothing satisfied the old test."""
    tree = _build_tree(
        tmp_path / "emptyside",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/listy.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "listy.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    (module.DATA_DIR / "listy.provenance.json").write_text("{}", encoding="utf-8")
    result = module.CHECKS["artifact-provenance"]()
    assert not result.ok
    assert any("declares no provenance" in p.message for p in result.problems)


def test_artifact_provenance_accepts_a_sidecar_that_declares(tmp_path):
    tree = _build_tree(
        tmp_path / "goodside",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nData from `output/data/listy.json`.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "listy.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    (module.DATA_DIR / "listy.provenance.json").write_text(
        json.dumps({"data_origin": "real_pipeline"}), encoding="utf-8"
    )
    assert module.CHECKS["artifact-provenance"]().ok


def test_artifact_provenance_sees_a_bare_filename_citation(tmp_path):
    """Prose cites files by name as well as by path."""
    tree = _build_tree(
        tmp_path / "barename",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nSee the `mystery.json` results.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "mystery.json").write_text(json.dumps({"v": 1}), encoding="utf-8")
    result = module.CHECKS["artifact-provenance"]()
    assert not result.ok
    assert any("declares no provenance" in p.message for p in result.problems)


def test_artifact_provenance_ignores_a_sentence_disclaiming_an_artifact(tmp_path):
    """Naming a file to warn readers off it is the honest act, not a citation."""
    tree = _build_tree(
        tmp_path / "disclaim",
        part_text={"1": CEILING_OK,
                   "2": CEILING_OK + "\nNote that `mystery.json` is a placeholder, not a source.\n",
                   "3": CEILING_OK},
        bibs={},
    )
    module = _load_module(tree)
    (module.DATA_DIR / "mystery.json").write_text(json.dumps({"v": 1}), encoding="utf-8")
    assert module.CHECKS["artifact-provenance"]().ok


def test_bibliography_catches_one_bibkey_meaning_two_works(tmp_path):
    """The dangerous direction: same \\cite, different source per paper.

    Grouping entries by title cannot see this -- it is the opposite grouping --
    and it is what let `parr2019generalised` point at the Biological Cybernetics
    paper in two parts and a Scientific Reports paper in the third.
    """
    one = """@article{shared2020work,
  author = {Ada Lovelace},
  title  = {The First Paper},
  year   = {2020},
  doi    = {10.1000/first}
}
"""
    other = """@article{shared2020work,
  author = {Alan Turing},
  title  = {A Completely Different Paper},
  year   = {2020},
  doi    = {10.1000/second}
}
"""
    tree = _build_tree(
        tmp_path / "keycollide",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={"1": one, "2": other},
    )
    module = _load_module(tree)
    result = module.CHECKS["bibliography"]()
    assert not result.ok
    assert any("resolves to a different" in p.message for p in result.problems), [
        p.message for p in result.problems
    ]


def test_bibliography_accepts_one_bibkey_meaning_one_work(tmp_path):
    same = """@article{shared2020work,
  author = {Ada Lovelace},
  title  = {The First Paper},
  year   = {2020},
  doi    = {10.1000/first}
}
"""
    tree = _build_tree(
        tmp_path / "keyagree",
        part_text={"1": CEILING_OK, "2": CEILING_OK, "3": CEILING_OK},
        bibs={"1": same, "2": same},
    )
    module = _load_module(tree)
    assert module.CHECKS["bibliography"]().ok

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


class TestTheBibliographyGateIsClosed:
    """An uncited, unreferenced entry must fail, not be counted.

    This check reported a number for nine rounds. The number reached 169 and
    nobody acted on it, which is what an advisory over a growing pile is for.
    Both fabricated sources this series has shipped were in that pile, and the
    argument for tolerating them -- pandoc emits only cited works, so no reader
    sees an uncited entry -- is the same sentence as the reason nobody caught
    them.
    """

    def test_an_uncited_entry_fails_the_gate(self, tmp_path, monkeypatch):
        """Test of the test: the gate must be able to fail."""
        gate = _load_module()
        part = "1"
        bib = gate.manuscript_dir(part) / "references.bib"
        original = bib.read_text(encoding="utf-8")
        try:
            bib.write_text(
                original
                + "\n@misc{nobodycitesthisatall2026,\n"
                '  title = {A Source Nobody Cites},\n'
                "  year = {2026},\n}\n",
                encoding="utf-8",
            )
            result = gate.check_bibliography()
            hits = [p for p in result.problems if "nobodycitesthisatall2026" in p.message]
            assert hits, "the gate did not notice an entry nothing cites"
        finally:
            bib.write_text(original, encoding="utf-8")

    def test_the_shipped_bibliographies_are_closed(self):
        """And the negative control: the tree as shipped must pass."""
        gate = _load_module()
        result = gate.check_bibliography()
        assert not result.problems, [p.message for p in result.problems]

    def test_a_key_named_outside_the_prose_is_kept(self, tmp_path):
        """Conservatism: a bibkey a README or test names is in use."""
        gate = _load_module()
        part = "2"
        keys = {"friedman2026cogsec2"}
        assert gate._keys_named_outside_the_prose(part, keys) == keys
