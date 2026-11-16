"""The conclusion-number gate must be able to fail, and must say why.

Two failure modes are checked here because both have already happened. The
first version of the gate compared every conclusion percentage against every
number in ``output/data`` and could not fail. The second reported an incomplete
reference set as unbacked numbers in the manuscript, which points the reader at
the paper when the fault is the environment.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "check_conclusion_numbers", REPO / "scripts" / "check_conclusion_numbers.py"
)
assert _SPEC is not None and _SPEC.loader is not None
gate = importlib.util.module_from_spec(_SPEC)
sys.modules["check_conclusion_numbers"] = gate
_SPEC.loader.exec_module(gate)


def _conclusion(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "conclusion.md"
    path.write_text(body, encoding="utf-8")
    return path


class TestReferenceSet:
    def test_the_real_repository_passes(self):
        assert gate.main() == 0

    def test_the_reference_set_is_not_trivially_small(self):
        known, unevaluated = gate._headline_values()
        assert not unevaluated, unevaluated
        # Small enough that a coincidental match is unlikely, large enough that
        # the set has not silently collapsed to a handful of values.
        assert 20 <= len(known) <= 400, len(known)

    def test_every_exemption_carries_a_reason(self):
        for value, reason in gate.EXEMPT.items():
            assert reason.strip(), value


class TestItCanFail:
    def test_a_fabricated_percentage_is_rejected(self, tmp_path, monkeypatch, capsys):
        """77.7 is the value that slipped through the first version of the gate."""
        body = "The pipeline reaches 77.7\\% against the undefended arm.\n" + "\n".join(
            f"Filler {n}.{n}\\% is not asserted here." for n in range(1, 6)
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        assert gate.main() == 1
        assert "77.7" in capsys.readouterr().out

    def test_a_fabricated_integer_percentage_is_rejected(self, tmp_path, monkeypatch, capsys):
        """The stale ablation TPR was written "12\\%", with no decimal point.

        A decimal-only pattern matched nothing on that line, so the false
        headline passed the gate. Integer percentages are the shape a rounded
        hand-typed number takes, and they must be judged too.
        """
        body = "Full pipeline TPR on the ablation corpus is $\\sim$12\\%.\n" + "\n".join(
            f"Filler {n}.{n}\\% is not asserted here." for n in range(1, 6)
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        assert gate.main() == 1
        assert "12.0" in capsys.readouterr().out

    def test_a_confidence_level_is_not_a_measurement(self, tmp_path, monkeypatch):
        """"95\\% CI" and "95\\% HDI" describe the estimator, not the data."""
        # Filler uses derived values so only the confidence levels could fail.
        body = "Mean 86.3\\% [95\\% CI: 85.5\\%, 87.1\\%], 95\\% HDI reported.\n" + "\n".join(
            f"Derived filler {n}.0\\%." for n in (2, 3, 4, 5, 10)
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        assert gate.main() == 0

    def test_a_forward_looking_target_is_not_a_measurement(self, tmp_path, monkeypatch):
        """Targets and expected outcomes are goals, not reported measurements."""
        body = (
            "- Expected outcome: 95--98% detection across all categories\n"
            "*Target: 80--86\\% detection rate*\n"
            + "\n".join(f"Derived filler {n}.0\\%." for n in (2, 3, 4, 5, 10))
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        assert gate.main() == 0

    def test_goal_hijacking_does_not_exempt_a_measured_pipeline_mean(
        self, tmp_path, monkeypatch, capsys
    ):
        body = (
            "Goal-hijacking remains the concern; pipeline mean: 77.7\\%.\n"
            + "\n".join("Derived filler 86.3\\%." for _ in range(5))
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        monkeypatch.setattr(gate, "_headline_values", lambda: ({86.3: "fixture"}, []))
        assert gate.main() == 1
        assert "77.7" in capsys.readouterr().out

    def test_both_range_endpoints_are_checked(self, tmp_path, monkeypatch, capsys):
        body = (
            "The measured range was 77.7--86.3\\%.\n"
            + "\n".join("Derived filler 86.3\\%." for _ in range(5))
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        monkeypatch.setattr(gate, "_headline_values", lambda: ({86.3: "fixture"}, []))
        assert gate.main() == 1
        assert "77.7" in capsys.readouterr().out

    @pytest.mark.parametrize("stated", ["186.3", "86.31"])
    def test_a_numeric_suffix_cannot_impersonate_a_derived_value(
        self, stated, tmp_path, monkeypatch, capsys
    ):
        body = (
            f"The measured pipeline mean was {stated}\\%.\n"
            + "\n".join("Derived filler 86.3\\%." for _ in range(5))
        )
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(_conclusion(tmp_path, body)),))
        monkeypatch.setattr(gate, "_headline_values", lambda: ({86.3: "fixture"}, []))
        assert gate.main() == 1
        assert stated in capsys.readouterr().out

    def test_a_missing_conclusion_is_reported(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "CONCLUSIONS", (str(tmp_path / "absent.md"),))
        # Too few percentages to judge, which is itself refused rather than passed.
        assert gate.main() == 2

    def test_too_few_percentages_does_not_pass_silently(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            gate, "CONCLUSIONS", (str(_conclusion(tmp_path, "No numbers here.")),)
        )
        assert gate.main() == 2


class TestIncompleteReferenceSet:
    def test_an_underivable_variable_is_named_not_blamed_on_the_paper(
        self, monkeypatch, capsys
    ):
        """Under a bare interpreter with no numpy the set fell from 108 values
        to 104 and the gate accused the manuscript of two unbacked numbers that
        were in fact derived. The cause must be named instead."""
        sys.path.insert(0, str(REPO / "scripts"))
        import series_ledger

        def _explode():
            raise ModuleNotFoundError("No module named 'numpy'")

        broken = series_ledger.LEDGER[0].__class__(
            **{
                **series_ledger.LEDGER[0].__dict__,
                "id": "deliberately_underivable",
                "deriver": _explode,
            }
        )
        monkeypatch.setattr(
            series_ledger, "LEDGER", series_ledger.LEDGER + (broken,)
        )
        assert gate.main() == 2
        err = capsys.readouterr().err
        assert "deliberately_underivable" in err
        assert "unbacked" not in err
