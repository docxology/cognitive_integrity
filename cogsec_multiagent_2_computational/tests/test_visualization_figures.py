"""Smoke tests for visualization figure and table generators.

Each function is called with a temp output directory.  We verify it
returns a matplotlib Figure (or paths for ROC) and closes cleanly.
"""


import ast
import datetime
import hashlib
import inspect
import os
import re
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from colony.benchmark import ColonyBenchmark, ColonyConfig, ColonyResult, ColonyScenario
from visualization.figures import attack_timeline
from visualization.figures.attack_timeline import (
    SCENARIO_LABELS,
    TIMELINE_SEED,
    _load_timelines,
    plot_attack_timeline,
)

# ── Figure smoke tests ──────────────────────────────────────────────────

class TestFigureGenerators:
    """Smoke-test every plot_* function in visualization.figures."""

    @pytest.fixture(autouse=True)
    def _output_dir(self, tmp_path):
        self.out = str(tmp_path)

    # -- Individual figure modules --

    def test_attack_surface(self):
        from visualization.figures.attack_surface import plot_attack_surface
        fig = plot_attack_surface(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_decay(self):
        from visualization.figures.trust_decay import plot_trust_decay
        fig = plot_trust_decay(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_defense_composition(self):
        from visualization.figures.defense_composition import plot_defense_composition
        fig = plot_defense_composition(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_ablation_study(self):
        from visualization.figures.ablation_study import plot_ablation_study
        fig = plot_ablation_study(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_performance(self):
        from visualization.figures.detection_performance import plot_detection_performance
        fig = plot_detection_performance(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_comprehensive_taxonomy(self):
        from visualization.figures.comprehensive_taxonomy import plot_comprehensive_taxonomy
        fig = plot_comprehensive_taxonomy(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_cif_comprehensive(self):
        from visualization.figures.cif_comprehensive import plot_cif_comprehensive
        fig = plot_cif_comprehensive(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_roc_curves(self):
        from visualization.figures.roc_curves import plot_roc_curves
        result = plot_roc_curves(output_dir=self.out)
        # Returns tuple of paths or a Figure
        if isinstance(result, Figure):
            plt.close(result)
        else:
            assert len(result) >= 1

    def test_scalability(self):
        from visualization.figures.scalability import plot_scalability
        fig = plot_scalability(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_calculus(self):
        from visualization.figures.trust_calculus import plot_trust_calculus
        fig = plot_trust_calculus(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_belief_sandbox(self):
        from visualization.figures.belief_sandbox import plot_belief_sandbox
        fig = plot_belief_sandbox(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_fp_mitigation(self):
        from visualization.figures.fp_mitigation import plot_fp_mitigation
        fig = plot_fp_mitigation(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_confusion_matrices(self):
        from visualization.figures.confusion_matrices import plot_confusion_matrices
        fig = plot_confusion_matrices(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_distributions(self):
        from visualization.figures.detection_distributions import plot_detection_distributions
        fig = plot_detection_distributions(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_cif_architecture(self):
        from visualization.figures.cif_architecture import plot_cif_architecture
        fig = plot_cif_architecture(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_network(self):
        from visualization.figures.trust_network import plot_trust_network
        fig = plot_trust_network(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_threat_taxonomy(self):
        from visualization.figures.threat_taxonomy import plot_threat_taxonomy
        fig = plot_threat_taxonomy(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_attack_timeline(self):
        from visualization.figures.attack_timeline import plot_attack_timeline
        fig = plot_attack_timeline(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_component_interactions(self):
        from visualization.figures.component_interactions import plot_component_interactions
        fig = plot_component_interactions(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_results(self):
        from visualization.figures.detection_results import plot_detection_heatmap
        fig = plot_detection_heatmap(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_sensitivity_heatmap(self):
        from visualization.figures.sensitivity_heatmap import plot_sensitivity_heatmap
        fig = plot_sensitivity_heatmap(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_precision_recall_curves(self):
        from visualization.figures.precision_recall_curves import plot_precision_recall_curves
        fig = plot_precision_recall_curves(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)


# ── Table generator smoke tests ─────────────────────────────────────────

class TestTableGenerators:
    """Smoke-test every generate_* function in visualization.tables."""

    def test_corpus_table(self):
        from visualization.tables.corpus_tables import generate_corpus_table
        result = generate_corpus_table()
        assert isinstance(result, str) and len(result) > 0

    def test_cross_validation_table(self):
        from visualization.tables.cross_validation_tables import generate_cross_validation_table
        result = generate_cross_validation_table()
        assert isinstance(result, str) and len(result) > 0

    def test_assumption_table(self):
        from visualization.tables.assumption_tables import generate_assumption_table
        result = generate_assumption_table()
        assert isinstance(result, str) and len(result) > 0

    def test_ablation_table(self):
        from visualization.tables.ablation_tables import generate_ablation_table
        result = generate_ablation_table()
        assert isinstance(result, str) and len(result) > 0

    def test_synergy_table(self):
        from visualization.tables.ablation_tables import generate_synergy_table
        result = generate_synergy_table()
        assert isinstance(result, str) and len(result) > 0

    def test_hypothesis_table(self):
        from visualization.tables.statistical_tables import generate_hypothesis_table
        result = generate_hypothesis_table()
        assert isinstance(result, str) and len(result) > 0

    def test_effect_size_table(self):
        from visualization.tables.statistical_tables import generate_effect_size_table
        result = generate_effect_size_table()
        assert isinstance(result, str) and len(result) > 0

    def test_detection_table(self):
        from visualization.tables.detection_tables import generate_detection_table
        result = generate_detection_table()
        assert isinstance(result, str) and len(result) > 0

    def test_stability_table(self):
        from visualization.tables.stability_tables import generate_stability_table
        result = generate_stability_table()
        assert isinstance(result, str) and len(result) > 0

    def test_scalability_table(self):
        from visualization.tables.scalability_tables import generate_scalability_table
        result = generate_scalability_table()
        assert isinstance(result, str) and len(result) > 0


# ── Fig 8 data provenance (audit TEST-01 / INTEG-09a) ───────────────────


class _RaisingScenario(ColonyScenario):
    """A real scenario whose run() fails, used to prove the loader fails loudly."""

    @property
    def name(self) -> str:
        return "raising_scenario"

    def default_config(self) -> ColonyConfig:
        return ColonyConfig(n_agents=4, n_steps=4)

    def run(self, config, rng):
        raise RuntimeError("scenario blew up")


class _EmptyTimelineScenario(ColonyScenario):
    """A real scenario that produces no per-step trace at all."""

    @property
    def name(self) -> str:
        return "empty_timeline_scenario"

    def default_config(self) -> ColonyConfig:
        return ColonyConfig(n_agents=4, n_steps=4)

    def run(self, config, rng) -> ColonyResult:
        return ColonyResult(scenario_name=self.name, config=config, timeline=[])


def _fabricated_timeline(detection_rate: float, resilience: float, n_steps: int = 100):
    """Reproduce the synthetic curve the module used to emit.

    This is the exact analytic shape from the deleted fallback branch:
    a sine dip between 40% and 70% of the run plus an exponential recovery,
    derived from two summary scalars.  Kept here (and only here) so the tests
    below can assert the shipped code does *not* produce it.
    """
    timeline = np.ones(n_steps)
    attack_start = int(n_steps * 0.4)
    attack_end = int(n_steps * 0.7)
    dip = 1.0 - detection_rate
    for i in range(attack_start, attack_end):
        progress = (i - attack_start) / (attack_end - attack_start)
        timeline[i] = 1.0 - dip * np.sin(np.pi * progress)
    for i in range(attack_end, n_steps):
        recovery_progress = (i - attack_end) / (n_steps - attack_end)
        timeline[i] = 1.0 - dip * (1 - resilience) * np.exp(-3 * recovery_progress)
    return timeline


class TestAttackTimelineProvenance:
    """Fig 8 must plot measured colony traces, never a synthetic stand-in.

    Audit TEST-01 / INTEG-09a: ``_load_timelines`` used to import
    ``colony.coordinated_attack`` (a module that never existed) inside a
    ``try``, so the ``except`` branch -- which fabricated each curve from two
    summary scalars in ``colony_results.json`` -- was the only branch that
    ever executed, while the docstring advertised "real integrity
    time-series".  The only test asserted ``isinstance(fig, Figure)``.
    """

    def test_timelines_are_the_benchmarks_own_output(self):
        """Every plotted series equals a ColonyResult.timeline, element-wise.

        The expectation is re-derived here from ColonyBenchmark directly, so
        the assertion is bound to the measurement rather than to a value
        copied out of the figure module.
        """
        series = _load_timelines()
        expected = ColonyBenchmark().run_all(seed=TIMELINE_SEED)

        assert len(series) == len(expected) == 5
        for (label, values), result in zip(series, expected):
            assert label == SCENARIO_LABELS[result.scenario_name]
            assert len(values) == len(result.timeline)
            np.testing.assert_array_equal(values, np.asarray(result.timeline, float))

    def test_positive_control_fabricated_curve_is_detectably_different(self):
        """POSITIVE CONTROL: the equality check above can actually fail.

        Feeds the old synthetic curve through the same comparison and asserts
        it is rejected.  If a future edit reinstated the fabricated fallback,
        ``test_timelines_are_the_benchmarks_own_output`` would go red -- this
        test is what proves that.
        """
        expected = ColonyBenchmark().run_all(seed=TIMELINE_SEED)
        target = expected[0]
        fake = _fabricated_timeline(
            target.detection_rate, target.resilience_score, n_steps=len(target.timeline)
        )

        assert len(fake) == len(target.timeline)
        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(
                fake, np.asarray(target.timeline, dtype=float)
            )

    def test_scenario_failure_propagates_instead_of_synthesising(self):
        """A broken scenario must raise, not silently yield an invented curve."""
        benchmark = ColonyBenchmark(scenarios=[_RaisingScenario()])
        with pytest.raises(RuntimeError, match="scenario blew up"):
            _load_timelines(benchmark=benchmark)

    def test_empty_timeline_is_rejected(self):
        """An empty trace is a broken measurement, not a licence to invent one."""
        benchmark = ColonyBenchmark(scenarios=[_EmptyTimelineScenario()])
        with pytest.raises(ValueError, match="empty integrity timeline"):
            _load_timelines(benchmark=benchmark)

    def test_benchmark_with_no_scenarios_is_rejected(self):
        """Zero scenarios must raise rather than yield an empty/placeholder plot."""
        with pytest.raises(ValueError, match="no scenario results"):
            _load_timelines(benchmark=ColonyBenchmark(scenarios=[]))

    def test_no_synthetic_fallback_remains_in_the_module(self):
        """The module must not carry a silent except-and-fabricate path.

        Guards the structural property the runtime tests cannot: that no new
        ``except`` swallows a scenario failure inside the loader, and that the
        module never reads the summary JSON the old fallback synthesised from.
        Asserted over the AST, not over raw text, so prose in the docstrings
        (which deliberately names the removed behaviour) cannot trip it.
        """
        tree = ast.parse(inspect.getsource(attack_timeline))

        loaders = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_load_timelines"
        ]
        assert len(loaders) == 1
        handlers = [n for n in ast.walk(loaders[0]) if isinstance(n, ast.Try)]
        assert handlers == [], "_load_timelines must not swallow scenario failures"

        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "json" not in imported

        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "open" not in called

    def test_figure_uses_the_loaded_series(self, tmp_path):
        """plot_attack_timeline draws exactly the data it was handed."""
        series = [("Scenario A", np.array([1.0, 0.5, 0.25]))]
        fig = plot_attack_timeline(output_dir=str(tmp_path), series=series)
        ax = fig.axes[0]
        assert len(ax.lines) == 1
        np.testing.assert_array_equal(
            ax.lines[0].get_ydata(), np.array([1.0, 0.5, 0.25])
        )
        assert (tmp_path / "fig08_attack_timeline.pdf").exists()
        plt.close(fig)


# ── Generation-script exit codes (audit SCRIPT-01) ──────────────────────


_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _run_driver(code: str):
    """Run *code* in a subprocess and return the CompletedProcess."""
    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )


class TestGenerationScriptsFailClosed:
    """`make figures` / `make tables` must not exit 0 with a missing artifact.

    Audit SCRIPT-01: both scripts caught every per-item exception, printed
    ``FAILED``, and then returned normally, so a broken generator produced a
    green build with a silently absent figure or table.
    """

    def test_figures_script_exits_nonzero_when_a_generator_raises(self, tmp_path):
        code = f"""
import sys
sys.path.insert(0, {str(_SCRIPTS_DIR)!r})
import generate_all_figures as g

def boom(output_dir=None):
    raise RuntimeError("synthetic generator failure")

def fine(output_dir=None):
    return None

sys.exit(g.main(argv=["--output", {str(tmp_path)!r}],
                figures=[("boom", boom), ("fine", fine)]))
"""
        proc = _run_driver(code)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        # Still attempted everything and reported the failure by name.
        assert "fine... OK" in proc.stdout
        assert "synthetic generator failure" in proc.stdout
        assert "1 of 2 figure(s) FAILED" in proc.stdout

    def test_figures_script_exits_zero_when_all_generators_succeed(self, tmp_path):
        """POSITIVE CONTROL for the test above: exit 0 is still reachable."""
        code = f"""
import sys
sys.path.insert(0, {str(_SCRIPTS_DIR)!r})
import generate_all_figures as g

def fine(output_dir=None):
    return None

sys.exit(g.main(argv=["--output", {str(tmp_path)!r}], figures=[("fine", fine)]))
"""
        proc = _run_driver(code)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "All 1 figures generated successfully." in proc.stdout

    def test_tables_script_exits_nonzero_when_a_generator_raises(self, tmp_path):
        code = f"""
import sys
sys.path.insert(0, {str(_SCRIPTS_DIR)!r})
import generate_all_tables as g

def boom():
    raise RuntimeError("synthetic table failure")

def fine():
    return "\\\\begin{{tabular}}{{c}}x\\\\end{{tabular}}"

sys.exit(g.main(argv=["--output", {str(tmp_path)!r}],
                tables=[("boom.tex", boom), ("fine.tex", fine)]))
"""
        proc = _run_driver(code)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "fine.tex... OK" in proc.stdout
        assert "synthetic table failure" in proc.stdout
        assert "1 of 2 table(s) FAILED" in proc.stdout
        # The healthy table was still written despite the sibling failure.
        assert (tmp_path / "fine.tex").exists()
        assert not (tmp_path / "boom.tex").exists()

    def test_tables_script_exits_zero_when_all_generators_succeed(self, tmp_path):
        """POSITIVE CONTROL for the test above: exit 0 is still reachable."""
        code = f"""
import sys
sys.path.insert(0, {str(_SCRIPTS_DIR)!r})
import generate_all_tables as g

def fine():
    return "\\\\begin{{tabular}}{{c}}x\\\\end{{tabular}}"

sys.exit(g.main(argv=["--output", {str(tmp_path)!r}], tables=[("fine.tex", fine)]))
"""
        proc = _run_driver(code)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "All 1 tables generated successfully." in proc.stdout


def _pdf_creation_date(pdf_path):
    """Extract the ``/CreationDate (...)`` string matplotlib embedded."""
    found = re.findall(rb"/CreationDate \(([^)]*)\)", pdf_path.read_bytes())
    assert found, f"no /CreationDate in {pdf_path}"
    assert len(set(found)) == 1, found
    return found[0].decode("ascii")


def _expected_creation_date(epoch: str) -> str:
    """matplotlib's SOURCE_DATE_EPOCH rendering: UTC, ``D:%Y%m%d%H%M%SZ``."""
    stamp = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc)
    return stamp.strftime("D:%Y%m%d%H%M%SZ")


class TestFigureByteReproducibility:
    """Publication PDFs must be byte-reproducible (audit REPRO-02).

    matplotlib stamps ``/CreationDate`` into every PDF from the wall clock, so
    two identical plots rendered at different times hashed differently and the
    published PDFs were not bit-reproducible.  ``generate_all_figures`` pins
    ``SOURCE_DATE_EPOCH``, which matplotlib honours.

    The assertions below deliberately bind to the *embedded date*, not merely
    to "two runs agree": two runs launched a fraction of a second apart agree
    by luck even with the fix removed, because ``/CreationDate`` only has
    one-second resolution.  A test that can pass for that reason proves
    nothing.
    """

    _PLOT_DRIVER = """
import sys
sys.path.insert(0, {scripts!r})
import generate_all_figures as g  # pins SOURCE_DATE_EPOCH on import
sys.path.insert(0, {src!r})
from visualization.figures import trust_decay
sys.exit(g.main(argv=["--output", {out!r}],
                figures=[("trust_decay", trust_decay.plot_trust_decay)]))
"""

    def _render(self, out_dir, source_date_epoch=None):
        """Render one figure in a fresh interpreter; return (sha256, date, epoch).

        ``epoch`` is whatever the script itself reported it pinned, parsed out
        of stdout, so the expectation is never hard-coded in the test.
        """
        src = str(Path(__file__).resolve().parent.parent / "src")
        code = self._PLOT_DRIVER.format(
            scripts=str(_SCRIPTS_DIR), src=src, out=str(out_dir)
        )
        env = dict(os.environ)
        env["MPLBACKEND"] = "Agg"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if source_date_epoch is None:
            env.pop("SOURCE_DATE_EPOCH", None)
        else:
            env["SOURCE_DATE_EPOCH"] = source_date_epoch
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        pdf = Path(out_dir) / "trust_decay.pdf"
        assert pdf.exists(), proc.stdout

        reported = re.search(r"^SOURCE_DATE_EPOCH=(\S+)$", proc.stdout, re.M)
        assert reported, proc.stdout
        return (
            hashlib.sha256(pdf.read_bytes()).hexdigest(),
            _pdf_creation_date(pdf),
            reported.group(1),
        )

    def test_creation_date_is_pinned_not_wall_clock(self, tmp_path):
        """With no epoch in the environment the script must supply one.

        Fails if the pin is removed: the PDF then carries the current local
        time instead of the script's declared epoch.
        """
        _, created, epoch = self._render(tmp_path / "pinned")
        assert epoch not in ("None", ""), "script did not pin SOURCE_DATE_EPOCH"
        assert created == _expected_creation_date(epoch)
        # A wall-clock stamp is local-time with an offset suffix, never `...Z`.
        assert created.endswith("Z")

    def test_pdf_is_byte_identical_across_runs(self, tmp_path):
        """Two independent runs of the same figure produce the same bytes."""
        a_hash, a_date, _ = self._render(tmp_path / "a")
        b_hash, b_date, _ = self._render(tmp_path / "b")
        assert a_date == b_date
        assert a_hash == b_hash

    def test_positive_control_creation_date_drives_the_digest(self, tmp_path):
        """POSITIVE CONTROL: the digest really is sensitive to the timestamp.

        Rendering the identical figure under two *different* epochs must give
        different embedded dates and different bytes.  Without this, the
        equality assertion above could be green simply because the PDF carried
        no timestamp at all.
        """
        early_hash, early_date, _ = self._render(
            tmp_path / "early", source_date_epoch="1000000000"
        )
        late_hash, late_date, _ = self._render(
            tmp_path / "late", source_date_epoch="1700000000"
        )
        assert early_date == _expected_creation_date("1000000000")
        assert late_date == _expected_creation_date("1700000000")
        assert early_date != late_date
        assert early_hash != late_hash
