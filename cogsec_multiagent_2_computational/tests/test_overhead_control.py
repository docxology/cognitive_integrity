"""Tests for the defended-versus-undefended control arm.

The obligation is not that the script runs. It is that the control really is a
control -- that it does strictly less work than the defended arm and that the
difference between them is attributable to the defense and nothing else -- and
that the artifact refuses to report the one number the tables it replaces got
wrong: a percentage overhead against a baseline that is not a unit of work.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_overhead_control.py"
ARTIFACT = REPO / "output" / "data" / "overhead_control.json"


def _module():
    spec = importlib.util.spec_from_file_location("run_overhead_control", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_overhead_control"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def payload() -> dict:
    assert ARTIFACT.is_file(), "run scripts/run_overhead_control.py first"
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_both_arms_saw_the_same_messages(payload) -> None:
    """A control over different inputs is not a control."""
    assert payload["n_messages"] == payload["n_attacks"] + payload["n_benign"]
    for arm in payload["arms"].values():
        assert arm["latency_ms"]["n"] == payload["n_messages"]


def test_the_defense_costs_something(payload) -> None:
    """The whole point: the defended arm must be measurably slower.

    If this ever fails, either the control has acquired work or the pipeline
    has stopped doing any, and both are worse than a slow pipeline.
    """
    control = payload["arms"]["control"]["latency_ms"]["p50"]
    defended = payload["arms"]["full_pipeline"]["latency_ms"]["p50"]
    assert defended > control, (
        f"the defended arm ({defended:.6f} ms) is not slower than the control "
        f"({control:.6f} ms); the control is doing the pipeline's work, or the "
        f"pipeline is doing none"
    )
    assert payload["added"]["median_latency_ms"] == pytest.approx(defended - control)


def test_the_warmup_is_discarded_and_smaller_than_the_corpus(payload) -> None:
    """A warmup as large as the corpus would time nothing but warmup."""
    assert 0 < payload["warmup"] < payload["n_messages"] / 10


def test_no_percentage_overhead_is_reported(payload) -> None:
    """The retired claim must not come back in a new shape.

    ``+23%`` and the ``45ms -> 52ms`` row divided by a baseline that was not a
    unit of agent work. The artifact reports absolute cost and, separately, a
    fraction of a *measured* agent turn. Anything calling itself an overhead
    percentage against the control is the same error returning.
    """
    assert "overhead_percent" not in payload["added"]
    assert "percent" not in json.dumps(payload["added"]).lower()


def test_the_agent_turn_denominator_is_measured(payload) -> None:
    """The only defensible denominator, and it has to come from an artifact."""
    fractions = payload["as_fraction_of_measured_agent_turn"]
    assert fractions, "no measured agent turn to compare against"

    llm = json.loads(
        (REPO / "output" / "data" / "llm_demo_results.json").read_text(encoding="utf-8")
    )
    added_s = payload["added"]["median_latency_ms"] / 1000.0
    for name, fraction in fractions.items():
        turn_s = llm["phase2_architectures"][name]["avg_latency_ms"] / 1000.0
        assert fraction == pytest.approx(added_s / turn_s)
        assert fraction < 0.01, (
            f"the pipeline now costs {fraction:.2%} of a {name} turn; if that is "
            f"real the manuscript's overhead discussion needs rewriting, and if "
            f"it is not, the measurement is broken"
        )


def test_the_control_allocates_less_than_the_pipeline(payload) -> None:
    """Peak allocation is the other half of the cost, and it must also be positive."""
    arms = payload["arms"]
    assert (
        arms["full_pipeline"]["peak_traced_bytes"] > arms["control"]["peak_traced_bytes"]
    )
    assert payload["added"]["peak_traced_bytes"] > 0


def test_a_stale_corpus_is_caught(payload, tmp_path, monkeypatch) -> None:
    """--check must notice the corpus changing under a shipped measurement."""
    module = _module()
    stale = dict(payload)
    stale["n_messages"] = payload["n_messages"] + 1
    target = tmp_path / "overhead_control.json"
    target.write_text(json.dumps(stale), encoding="utf-8")
    monkeypatch.setattr(module, "OUTPUT", target)
    assert module.main(["--check"]) == 1
