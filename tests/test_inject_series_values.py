"""Tests for the series write path.

The obligation that matters here is not "the injector runs cleanly on a tree
that is already correct" -- it does, and that proves nothing.  It is that the
injector *changes the right bytes* when a number has drifted, *leaves everything
else alone*, and *refuses to run* when it cannot derive a value.

So every test below plants a specific drift in a synthetic tree and checks the
exact resulting text, and one test deliberately breaks a deriver to confirm the
run aborts rather than injecting a partial set.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _load(root: Path | None = None):
    """Import ledger + injector fresh, optionally rooted at a synthetic tree."""
    sys.path.insert(0, str(SCRIPTS))
    for name in ("series_ledger", "inject_series_values"):
        sys.modules.pop(name, None)
    ledger_spec = importlib.util.spec_from_file_location(
        "series_ledger", SCRIPTS / "series_ledger.py"
    )
    ledger = importlib.util.module_from_spec(ledger_spec)
    sys.modules["series_ledger"] = ledger
    ledger_spec.loader.exec_module(ledger)
    if root is not None:
        ledger.REPO_ROOT = root
        ledger.DATA_DIR = root / ledger.PARTS["2"] / "output" / "data"
        ledger._CACHE.clear()

    inj_spec = importlib.util.spec_from_file_location(
        "inject_series_values", SCRIPTS / "inject_series_values.py"
    )
    injector = importlib.util.module_from_spec(inj_spec)
    sys.modules["inject_series_values"] = injector
    inj_spec.loader.exec_module(injector)
    if root is not None:
        injector.REPO_ROOT = root
    return ledger, injector


_ROWS = [
    {"architecture": a, "n_attacks": n, "detection_rate": r}
    for a, (n, r) in (
        ("A", (500, 0.96)), ("A", (450, 1.0)),
        ("B", (500, 0.98)), ("B", (450, 1.0)),
        ("C", (500, 1.0)), ("C", (450, 1.0)),
        ("D", (500, 0.99)), ("D", (450, 1.0)),
    )
]


def _tree(tmp_path: Path, part2_body: str) -> Path:
    root = tmp_path / "tree"
    ledger, _ = _load()
    for part, package in ledger.PARTS.items():
        d = root / package / "manuscript"
        d.mkdir(parents=True, exist_ok=True)
        body = part2_body if part == "2" else "# Body\n\nNothing.\n"
        (d / "01_body.md").write_text(body, encoding="utf-8")
    data = root / ledger.PARTS["2"] / "output" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "full_evaluation_results.json").write_text(json.dumps(_ROWS), encoding="utf-8")
    (data / "multi_seed_results.json").write_text(
        json.dumps({"data_origin": "real_pipeline", "tpr_mean": 0.448,
                    "fpr_mean": 0.2575, "overall_cv": 0.0967, "n_seeds": 30}),
        encoding="utf-8",
    )
    return root


def _run(root: Path, argv: list[str]) -> tuple[int, object]:
    _, injector = _load(root)
    return injector.main(argv), injector


def test_a_drifted_ceiling_is_reported_but_not_written_without_the_flag(tmp_path, capsys):
    body = "# Body\n\nThe parametric design-level ceiling is 94--100\\% across the sweep.\n"
    root = _tree(tmp_path, body)
    code, _ = _run(root, ["--only", "parametric_ceiling_low"])
    out = capsys.readouterr().out
    assert code == 1, out
    assert "'94' -> '96'" in out
    # Reporting must not touch the file.
    written = (root / "cogsec_multiagent_2_computational" / "manuscript" / "01_body.md").read_text()
    assert "94--100" in written


def test_write_rewrites_only_the_drifted_literal(tmp_path, capsys):
    body = (
        "# Body\n\n"
        "The parametric design-level ceiling is 94--100\\% across the sweep.\n\n"
        "Unrelated: 94 people attended, and the 94th run was fine.\n"
    )
    root = _tree(tmp_path, body)
    code, _ = _run(root, ["--only", "parametric_ceiling_low", "--write"])
    assert code == 0, capsys.readouterr().out
    written = (root / "cogsec_multiagent_2_computational" / "manuscript" / "01_body.md").read_text()
    assert "96--100" in written
    # The neighbouring 94s are not this quantity and must survive untouched.
    assert "94 people attended" in written
    assert "the 94th run" in written


def test_a_correct_tree_reports_no_changes(tmp_path, capsys):
    body = "# Body\n\nThe parametric design-level ceiling is 96--100\\% across the sweep.\n"
    root = _tree(tmp_path, body)
    code, _ = _run(root, ["--only", "parametric_ceiling_low"])
    assert code == 0
    assert "already matches its artifact" in capsys.readouterr().out


def test_out_of_context_numbers_are_never_rewritten(tmp_path, capsys):
    """The same shape in another arm is a different quantity."""
    body = (
        "# Body\n\n"
        "The parametric design-level ceiling is 96--100\\% across the sweep.\n\n"
        "The colony benchmarks reach 81--100\\% on structured scenarios.\n"
    )
    root = _tree(tmp_path, body)
    code, _ = _run(root, ["--only", "parametric_ceiling_low", "--write"])
    assert code == 0
    written = (root / "cogsec_multiagent_2_computational" / "manuscript" / "01_body.md").read_text()
    assert "81--100" in written, "the colony arm was rewritten as if it were the ceiling"


def test_the_run_aborts_when_a_variable_cannot_derive(tmp_path, capsys):
    body = "# Body\n\nThe parametric design-level ceiling is 94--100\\% across the sweep.\n"
    root = _tree(tmp_path, body)
    ledger, injector = _load(root)
    (ledger.DATA_DIR / "full_evaluation_results.json").unlink()
    ledger._CACHE.clear()
    code = injector.main(["--only", "parametric_ceiling_low", "--write"])
    out = capsys.readouterr().out
    assert code == 1
    assert "refusing to run" in out
    # And crucially: it did not write a partial set.
    written = (root / "cogsec_multiagent_2_computational" / "manuscript" / "01_body.md").read_text()
    assert "94--100" in written


def test_an_unknown_variable_name_is_an_error(tmp_path, capsys):
    root = _tree(tmp_path, "# Body\n\nNothing.\n")
    code, _ = _run(root, ["--only", "no_such_variable"])
    assert code == 2
    assert "unknown variable" in capsys.readouterr().err


@pytest.mark.parametrize(
    "stated, value, expected",
    [
        ("44.8", 44.83, "44.8"),
        ("44.80", 44.8, "44.80"),
        ("96", 96.0, "96"),
        ("ten", 10.0, "ten"),
        ("four", 4.0, "four"),
        ("3{,}800", 3800.0, "3{,}800"),
    ],
)
def test_formatting_preserves_the_shape_already_written(stated, value, expected):
    _, injector = _load()
    assert injector.format_like(stated, value) == expected


def test_the_injector_and_the_gate_share_one_definition_of_where_numbers_live():
    """Two mechanisms with separate site tables is the defect they exist to catch."""
    _, injector = _load()
    source = (SCRIPTS / "inject_series_values.py").read_text(encoding="utf-8")
    assert "from series_ledger import" in source
    assert "re.compile" not in source, (
        "the injector defines a pattern of its own; it must use the ledger's"
    )


class TestTheRewriteTouchesOnlyTheMatchedSpan:
    """A short literal must be replaced where the pattern found it, nowhere else.

    ``apply_changes`` used to rewrite by ``line.replace(before, after, 1)``,
    which finds the first occurrence of the literal anywhere on the line rather
    than the occurrence the pattern matched. For a two-digit percentage that is
    usually harmless. For the narrow end of a gap -- a one- or two-character
    literal like ``4`` -- it is almost always the wrong number, and it does its
    damage in prose far from the phrase that was being maintained.

    It happened twice in one run. Part 1's limitations paragraph had
    "Assumption 4 (stationary distributions)" rewritten to "Assumption 10",
    and Part 2's S08 had "$\\sim$44\\% mean detection rate" rewritten to
    "$\\sim$104\\%", each because the gap phrase they were being edited for
    sat several clauses later on the same line. Both passed every gate: the
    gap became correct, and nothing else on the line was checked by anything.
    """

    def test_the_first_matching_digits_on_the_line_are_not_the_target(self, tmp_path):
        from inject_series_values import Change, apply_changes

        path = tmp_path / "prose.md"
        path.write_text(
            "Assumption 4 (stationary) holds, yielding a 4--51 percentage-point gap.\n",
            encoding="utf-8",
        )
        line = path.read_text(encoding="utf-8")
        start = line.index("4--51")
        change = Change(path, 1, "gap_low", "4", "10", start, start + 1)

        assert apply_changes([change]) == 1
        after = path.read_text(encoding="utf-8")
        assert "Assumption 4 (stationary)" in after, (
            "the rewrite moved to an unrelated number earlier on the line"
        )
        assert "10--51 percentage-point gap" in after

    def test_two_edits_on_one_line_do_not_shift_each_other(self, tmp_path):
        """Right-to-left application, or the second offset lands in the wrong place."""
        from inject_series_values import Change, apply_changes

        path = tmp_path / "prose.md"
        path.write_text("a 4--51 percentage-point gap.\n", encoding="utf-8")
        line = path.read_text(encoding="utf-8")
        low = line.index("4--51")
        high = low + len("4--")
        changes = [
            Change(path, 1, "gap_low", "4", "10", low, low + 1),
            Change(path, 1, "gap_high", "51", "11", high, high + 2),
        ]
        assert apply_changes(changes) == 2
        assert "10--11 percentage-point gap" in path.read_text(encoding="utf-8")

    def test_a_change_with_no_recorded_span_is_refused(self, tmp_path):
        """Fail closed: guessing where to write is what caused the corruption."""
        from inject_series_values import Change, apply_changes

        path = tmp_path / "prose.md"
        original = "Assumption 4 holds; a 4--51 percentage-point gap.\n"
        path.write_text(original, encoding="utf-8")
        assert apply_changes([Change(path, 1, "gap_low", "4", "10")]) == 0
        assert path.read_text(encoding="utf-8") == original

    def test_a_span_that_no_longer_matches_is_refused(self, tmp_path):
        """The line moved under the match; writing anyway would corrupt it."""
        from inject_series_values import Change, apply_changes

        path = tmp_path / "prose.md"
        original = "a 4--51 percentage-point gap.\n"
        path.write_text(original, encoding="utf-8")
        stale = Change(path, 1, "gap_low", "4", "10", 0, 1)
        assert apply_changes([stale]) == 0
        assert path.read_text(encoding="utf-8") == original
