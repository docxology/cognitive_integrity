"""Tests for the five figures added with the new measurements.

Each reports a measured quantity, so the property that matters is not that it
renders: it is that it *cannot* render without its artifact. A figure that
falls back to defaults when a measurement is missing looks identical, on the
page, to one drawn from the measurement, and that is exactly how a hardcoded
matrix ended up in a published panel and an invented optimum on a sensitivity
surface.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from visualization.artifact import DATA_DIR, load_artifact, provenance_line  # noqa: E402
from visualization.figures.load_saturation import plot_load_saturation  # noqa: E402
from visualization.figures.mitigation_tradeoff import plot_mitigation_tradeoff  # noqa: E402
from visualization.figures.module_capability import plot_module_capability  # noqa: E402
from visualization.figures.operating_curve import plot_operating_curve  # noqa: E402
from visualization.figures.stratified_detection import (  # noqa: E402
    plot_stratified_detection,
)

FIGURES = {
    "module_capability": plot_module_capability,
    "stratified_detection": plot_stratified_detection,
    "operating_curve": plot_operating_curve,
    "load_saturation": plot_load_saturation,
    "mitigation_tradeoff": plot_mitigation_tradeoff,
}


class TestTheLoader:
    def test_a_missing_artifact_raises_and_names_the_file(self):
        with pytest.raises(FileNotFoundError, match="no stand-in values"):
            load_artifact("there_is_no_such_artifact")

    def test_a_missing_key_raises_rather_than_failing_later(self):
        """Fail at load with the key named, not three frames on."""
        with pytest.raises(KeyError, match="diverged"):
            load_artifact("defense_overlap", required=("no_such_key",))

    def test_the_provenance_line_states_the_origin_verbatim(self):
        """A reader must be able to tell simulated from measured on the page."""
        payload = load_artifact("defense_overlap")
        line = provenance_line(payload, "defense_overlap.json")
        assert payload["data_origin"] in line
        assert payload["source_script"] in line

    def test_an_origin_that_is_absent_is_said_to_be_absent(self):
        """Silence must not read as "measured"."""
        assert "not recorded" in provenance_line({}, "x.json")


@pytest.mark.parametrize("name,plot", sorted(FIGURES.items()))
def test_each_figure_renders_from_its_artifact(name, plot, tmp_path):
    figure = plot(output_dir=tmp_path)
    assert (tmp_path / f"{name}.png").is_file()
    assert (tmp_path / f"{name}.pdf").is_file()
    assert figure.axes, f"{name} rendered no axes"


@pytest.mark.parametrize("name,plot", sorted(FIGURES.items()))
def test_each_figure_refuses_to_draw_without_its_measurement(
    name, plot, tmp_path, monkeypatch
):
    """The property that matters. No fallback, in any of the five.

    ``DATA_DIR`` is pointed at an empty directory, so every artifact is
    missing. A figure that still produces output is one that has acquired a
    default somewhere, and a default is indistinguishable from a measurement
    once it is rendered.
    """
    import visualization.artifact as artifact_module

    empty = tmp_path / "no-data"
    empty.mkdir()
    monkeypatch.setattr(artifact_module, "DATA_DIR", empty)
    with pytest.raises((FileNotFoundError, KeyError)):
        plot(output_dir=tmp_path)


def test_every_new_figure_reads_a_provenanced_artifact():
    """Each artifact behind these figures must declare where it came from."""
    for name in (
        "module_capability_matrix",
        "stratified_detection",
        "threshold_sweep",
        "load_sweep",
        "fp_mitigation",
    ):
        payload = json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
        assert payload.get("data_origin"), name
        assert payload.get("source_script"), name
        assert (Path(DATA_DIR).parents[1] / payload["source_script"]).is_file(), (
            f"{name} names a source_script that does not exist"
        )
