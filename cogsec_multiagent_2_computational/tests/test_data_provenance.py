"""Provenance classification and the DataGenerator anti-clobber guard.

These tests exist because ``output/data/statistical_results.json`` and
``output/data/sensitivity_results.json`` were once byte-identical to
``DataGenerator``'s hardcoded synthetic constants: both names were missing
from the authoritative set, so ``make data`` silently replaced real pipeline
output with placeholders, and the ``.real_data_marker`` sentinel that was
supposed to prevent that is gitignored (it does not survive a clone) and had
zero test coverage.

Every guard assertion below is paired with a **positive control** in the same
file — a construction that proves the assertion can fail:

* :func:`test_synthetic_authoritative_artifact_is_overwritten` is the control
  for :func:`test_real_authoritative_artifacts_are_preserved`.  If the guard
  were "always skip", the former fails; if the guard were deleted, the latter
  fails.  Neither can be satisfied by a constant verdict.
* :func:`test_non_authoritative_artifact_is_overwritten_even_when_marked_real`
  is the control for the authoritative-name set: it proves the set is really
  consulted rather than every file being preserved.
* :func:`test_guard_survives_without_the_gitignored_marker` runs with **no**
  ``.real_data_marker`` present, which is the fresh-clone condition under
  which the old sentinel-only guard did nothing at all.

All tests use real files under ``tmp_path``.  No mocks.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from data.generate import (
    AUTHORITATIVE_RESULT_NAMES,
    DATA_ORIGIN_PARAMETRIC,
    DATA_ORIGIN_REAL,
    DATA_ORIGIN_SYNTHETIC,
    DATA_ORIGIN_UNKNOWN,
    PROVENANCE_KEYS,
    REAL_DATA_MARKER,
    SIDECAR_HASH_KEY,
    DataGenerator,
    _sha256_of,  # private: defensive branch coverage
    classify_provenance,
    is_synthetic_artifact,
    provenance_sidecar_path,
    read_provenance,
)

# Names that hold pipeline results and must never be clobbered.  Both of the
# regression names from the audit finding are asserted explicitly below.
_REGRESSION_NAMES = ("statistical_results", "sensitivity_results")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _real_marked(sentinel: str) -> dict:
    """A dict artifact that declares itself real and carries a tracer value."""
    return {
        "data_origin": DATA_ORIGIN_REAL,
        "source_script": "scripts/run_something_real.py",
        "generated_by": "scripts/run_something_real.py --seed 42",
        "seed": 42,
        "tracer": sentinel,
    }


# ===========================================================================
# classify_provenance / read_provenance
# ===========================================================================

class TestClassifyProvenance:
    """The classifier is the guard's oracle; it must never guess 'synthetic'."""

    def test_real_pipeline_inline(self, tmp_path):
        p = tmp_path / "a.json"
        _write_json(p, _real_marked("x"))
        assert classify_provenance(p) == DATA_ORIGIN_REAL
        assert is_synthetic_artifact(p) is False

    def test_synthetic_schema_inline(self, tmp_path):
        p = tmp_path / "a.json"
        _write_json(p, {"data_origin": DATA_ORIGIN_SYNTHETIC, "v": 1})
        assert classify_provenance(p) == DATA_ORIGIN_SYNTHETIC
        assert is_synthetic_artifact(p) is True

    def test_dict_without_data_origin_is_unknown(self, tmp_path):
        p = tmp_path / "a.json"
        _write_json(p, {"seed": 42, "v": 1})
        assert classify_provenance(p) == DATA_ORIGIN_UNKNOWN
        # Fail-safe: unknown must NOT be treated as synthetic.
        assert is_synthetic_artifact(p) is False

    def test_unrecognised_origin_value_is_unknown(self, tmp_path):
        p = tmp_path / "a.json"
        _write_json(p, {"data_origin": "handwritten", "v": 1})
        assert classify_provenance(p) == DATA_ORIGIN_UNKNOWN
        assert is_synthetic_artifact(p) is False

    def test_missing_file_is_unknown(self, tmp_path):
        assert classify_provenance(tmp_path / "nope.json") == DATA_ORIGIN_UNKNOWN
        assert read_provenance(tmp_path / "nope.json") == {}

    def test_malformed_json_is_unknown(self, tmp_path):
        p = tmp_path / "a.json"
        p.write_text("{not json", encoding="utf-8")
        assert classify_provenance(p) == DATA_ORIGIN_UNKNOWN
        assert is_synthetic_artifact(p) is False

    def test_list_artifact_without_sidecar_is_unknown(self, tmp_path):
        p = tmp_path / "rows.json"
        _write_json(p, [{"detection_rate": 1.0}])
        assert classify_provenance(p) == DATA_ORIGIN_UNKNOWN

    def test_list_artifact_reads_sidecar(self, tmp_path):
        p = tmp_path / "rows.json"
        _write_json(p, [{"detection_rate": 1.0}])
        _write_json(
            provenance_sidecar_path(p),
            {"data_origin": DATA_ORIGIN_REAL, "seed": 7},
        )
        assert classify_provenance(p) == DATA_ORIGIN_REAL
        assert read_provenance(p)["seed"] == 7

    def test_sidecar_without_artifact_is_unknown(self, tmp_path):
        """A stale sidecar must not vouch for an artifact that is not there."""
        p = tmp_path / "rows.json"
        _write_json(
            provenance_sidecar_path(p),
            {"data_origin": DATA_ORIGIN_REAL},
        )
        assert classify_provenance(p) == DATA_ORIGIN_UNKNOWN

    def test_stale_synthetic_sidecar_is_rejected(self, tmp_path):
        """A sidecar left over from an earlier run must not mislabel new data.

        Sequence that used to be fatal for list-shaped artifacts:
        ``make data`` writes a synthetic placeholder plus its sidecar, a real
        pipeline script then overwrites the artifact but not the sidecar, and
        the next ``make data`` reads the stale sidecar and clobbers the real
        data.  The sidecar is bound to the artifact bytes by SHA-256, so it
        stops vouching the moment the artifact changes.
        """
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        artifact = Path(gen.save([{"v": 1}], "rows.json", provenance=gen.provenance()))
        assert classify_provenance(artifact) == DATA_ORIGIN_SYNTHETIC

        # A real pipeline script replaces the artifact, leaving the sidecar.
        _write_json(artifact, [{"v": 2, "measured": True}])
        assert provenance_sidecar_path(artifact).exists()
        assert classify_provenance(artifact) == DATA_ORIGIN_UNKNOWN

    def test_matching_sidecar_still_vouches(self, tmp_path):
        """POSITIVE CONTROL for the staleness check.

        If the hash check rejected every sidecar, the test above would pass
        vacuously.  An untouched artifact must still classify as synthetic.
        """
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        artifact = Path(gen.save([{"v": 1}], "rows.json", provenance=gen.provenance()))
        recorded = json.loads(provenance_sidecar_path(artifact).read_text())
        assert recorded[SIDECAR_HASH_KEY]
        assert classify_provenance(artifact) == DATA_ORIGIN_SYNTHETIC

    def test_unbound_sidecar_may_only_claim_real(self, tmp_path):
        """Hash-less sidecars are trusted only in the data-preserving direction."""
        artifact = tmp_path / "rows.json"
        _write_json(artifact, [{"v": 1}])

        _write_json(
            provenance_sidecar_path(artifact),
            {"data_origin": DATA_ORIGIN_SYNTHETIC},
        )
        assert classify_provenance(artifact) == DATA_ORIGIN_UNKNOWN

        _write_json(
            provenance_sidecar_path(artifact),
            {"data_origin": DATA_ORIGIN_REAL},
        )
        assert classify_provenance(artifact) == DATA_ORIGIN_REAL

    def test_stale_sidecar_does_not_cause_a_clobber(self, tmp_path):
        """End-to-end: the stale-sidecar sequence leaves real data intact."""
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        gen.generate_all()
        artifact = tmp_path / "colony_results.json"
        assert provenance_sidecar_path(artifact).exists()

        real_rows = [{"scenario": "measured", "detection_rate": 0.5}]
        _write_json(artifact, real_rows)

        DataGenerator(seed=99, output_dir=str(tmp_path)).generate_all()

        assert json.loads(artifact.read_text()) == real_rows

    def test_inline_wins_over_sidecar(self, tmp_path):
        p = tmp_path / "a.json"
        _write_json(p, {"data_origin": DATA_ORIGIN_REAL, "v": 1})
        _write_json(
            provenance_sidecar_path(p),
            {"data_origin": DATA_ORIGIN_SYNTHETIC},
        )
        assert classify_provenance(p) == DATA_ORIGIN_REAL

    def test_directory_path_is_unknown(self, tmp_path):
        """A directory where an artifact should be is not provenance."""
        artifact = tmp_path / "rows.json"
        artifact.mkdir()
        _write_json(
            provenance_sidecar_path(artifact),
            {"data_origin": DATA_ORIGIN_SYNTHETIC, SIDECAR_HASH_KEY: "deadbeef"},
        )
        assert classify_provenance(artifact) == DATA_ORIGIN_UNKNOWN

    def test_hash_helper_is_fail_safe_on_unreadable_paths(self, tmp_path):
        """An unhashable artifact yields "", which can never match a sidecar.

        Defensive path for the artifact disappearing between the ``is_file``
        probe and the read: the empty digest cannot equal a recorded SHA-256,
        so the sidecar is rejected rather than trusted.
        """
        unreadable = tmp_path / "as_dir"
        unreadable.mkdir()
        digest = _sha256_of(unreadable)
        assert digest == ""
        assert digest != hashlib.sha256(b"").hexdigest()

    def test_sidecar_path_naming(self, tmp_path):
        assert provenance_sidecar_path(tmp_path / "colony_results.json").name == (
            "colony_results.provenance.json"
        )


# ===========================================================================
# The authoritative-name set (PROV-1 regression)
# ===========================================================================

class TestAuthoritativeNames:
    """statistical_results and sensitivity_results were the missing names."""

    @pytest.mark.parametrize("name", _REGRESSION_NAMES)
    def test_regression_names_are_authoritative(self, name):
        assert name in AUTHORITATIVE_RESULT_NAMES

    def test_all_pipeline_result_files_are_authoritative(self, tmp_path):
        """Every pipeline-format file generate_all writes is guarded."""
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()
        pipeline_files = {
            p.stem for p in tmp_path.glob("*_results.json")
        } - {p.stem for p in tmp_path.glob("*.provenance.json")}
        assert pipeline_files, "no *_results.json produced — test would be vacuous"
        assert pipeline_files == set(AUTHORITATIVE_RESULT_NAMES)

    def test_seed_datasets_are_not_authoritative(self):
        """The four *_data.json seed sets are pure placeholders, not guarded."""
        for name in ("detection_data", "scalability_data",
                     "ablation_data", "colony_data"):
            assert name not in AUTHORITATIVE_RESULT_NAMES


# ===========================================================================
# Anti-clobber guard (PROV-2)
# ===========================================================================

class TestAntiClobberGuard:
    """generate_all must not replace real results with synthetic ones."""

    def test_real_authoritative_artifacts_are_preserved(self, tmp_path):
        """Real-marked artifacts survive generate_all byte for byte."""
        before = {}
        for name in sorted(AUTHORITATIVE_RESULT_NAMES):
            p = tmp_path / f"{name}.json"
            _write_json(p, _real_marked(f"tracer::{name}"))
            before[name] = p.read_text(encoding="utf-8")

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        for name, original in before.items():
            after = (tmp_path / f"{name}.json").read_text(encoding="utf-8")
            assert after == original, f"{name}.json was clobbered by generate_all"

    @pytest.mark.parametrize("name", _REGRESSION_NAMES)
    def test_regression_name_is_preserved_by_literal_name(self, name, tmp_path):
        """Named explicitly so the check cannot shrink with the guarded set.

        ``test_real_authoritative_artifacts_are_preserved`` iterates
        ``AUTHORITATIVE_RESULT_NAMES``; removing a name from that set would
        silently shrink its scope.  These two names are hardcoded because they
        are exactly the ones the audit found missing.
        """
        p = tmp_path / f"{name}.json"
        _write_json(p, _real_marked(f"tracer::{name}"))
        original = p.read_text(encoding="utf-8")

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        assert p.read_text(encoding="utf-8") == original, (
            f"{name}.json was clobbered with DataGenerator synthetic output"
        )

    def test_synthetic_authoritative_artifact_is_overwritten(self, tmp_path):
        """POSITIVE CONTROL for the test above.

        A file that is *provably* synthetic must be replaced.  A guard that
        always skips would pass the preservation test and fail this one, so
        the pair cannot be satisfied by a constant verdict.
        """
        for name in sorted(AUTHORITATIVE_RESULT_NAMES):
            _write_json(
                tmp_path / f"{name}.json",
                {"data_origin": DATA_ORIGIN_SYNTHETIC, "tracer": "stale"},
            )

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        for name in sorted(AUTHORITATIVE_RESULT_NAMES):
            payload = json.loads((tmp_path / f"{name}.json").read_text())
            if isinstance(payload, dict):
                assert payload.get("tracer") != "stale", (
                    f"{name}.json was NOT refreshed despite being synthetic"
                )
            else:
                assert isinstance(payload, list) and payload

    def test_unknown_provenance_is_preserved(self, tmp_path):
        """Legacy real files that predate provenance stamping are protected."""
        p = tmp_path / "ablation_results.json"
        _write_json(p, {"component_removal": [], "tracer": "legacy-real"})
        original = p.read_text(encoding="utf-8")

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        assert p.read_text(encoding="utf-8") == original

    def test_non_authoritative_artifact_is_overwritten_even_when_marked_real(
        self, tmp_path,
    ):
        """POSITIVE CONTROL for the authoritative-name set.

        The seed datasets are placeholders by construction.  Marking one
        ``real_pipeline`` must NOT protect it — otherwise the guard would be
        "preserve everything", and the preservation tests above would be
        vacuous.
        """
        p = tmp_path / "detection_data.json"
        _write_json(p, _real_marked("should-be-replaced"))

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        payload = json.loads(p.read_text())
        assert payload.get("tracer") != "should-be-replaced"
        assert payload["data_origin"] == DATA_ORIGIN_SYNTHETIC

    def test_guard_survives_without_the_gitignored_marker(self, tmp_path):
        """Fresh-clone condition: no sentinel file anywhere.

        The old guard keyed solely on ``.real_data_marker``, which is matched
        by the repository's ``**/output/`` ignore rule and therefore absent
        after ``git clone``.  Provenance travels inside the tracked artifact,
        so the guard still holds.
        """
        marker = tmp_path / REAL_DATA_MARKER
        assert not marker.exists()

        p = tmp_path / "statistical_results.json"
        _write_json(p, _real_marked("clone-survivor"))
        original = p.read_text(encoding="utf-8")

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        assert not marker.exists(), "test lost its fresh-clone precondition"
        assert p.read_text(encoding="utf-8") == original

    def test_legacy_marker_still_overrides(self, tmp_path):
        """The out-of-band sentinel remains honoured for existing trees."""
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()
        (tmp_path / REAL_DATA_MARKER).write_text("mode=simulation", encoding="utf-8")

        snapshots = {
            name: (tmp_path / f"{name}.json").read_text(encoding="utf-8")
            for name in sorted(AUTHORITATIVE_RESULT_NAMES)
        }
        # A different seed would otherwise change every synthetic artifact.
        DataGenerator(seed=999, output_dir=str(tmp_path)).generate_all()

        for name, original in snapshots.items():
            assert (tmp_path / f"{name}.json").read_text(encoding="utf-8") == original

    def test_marker_absent_synthetic_files_do_refresh(self, tmp_path):
        """POSITIVE CONTROL for the marker test: without it, seeds change."""
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()
        snapshots = {
            name: (tmp_path / f"{name}.json").read_text(encoding="utf-8")
            for name in sorted(AUTHORITATIVE_RESULT_NAMES)
        }
        DataGenerator(seed=999, output_dir=str(tmp_path)).generate_all()

        changed = [
            name for name, original in snapshots.items()
            if (tmp_path / f"{name}.json").read_text(encoding="utf-8") != original
        ]
        assert changed, "no artifact changed — the marker test would be vacuous"

    def test_should_preserve_reports_the_decision(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        _write_json(tmp_path / "statistical_results.json", _real_marked("t"))
        assert gen.should_preserve("statistical_results") is True
        assert gen.should_preserve("detection_data") is False
        # Absent authoritative file: nothing to protect.
        assert gen.should_preserve("colony_results") is False


# ===========================================================================
# Provenance emission (PROV-3)
# ===========================================================================

class TestProvenanceEmission:
    """Every artifact generate_all writes carries the four provenance keys."""

    def test_every_generated_artifact_declares_provenance(self, tmp_path):
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        artifacts = sorted(
            p for p in tmp_path.glob("*.json")
            if not p.name.endswith(".provenance.json")
        )
        assert len(artifacts) == 11, f"unexpected artifact set: {artifacts}"

        for p in artifacts:
            prov = read_provenance(p)
            assert set(prov) == set(PROVENANCE_KEYS), f"{p.name}: {prov}"
            assert prov["data_origin"] == DATA_ORIGIN_SYNTHETIC, p.name
            assert prov["seed"] == 42, p.name
            assert prov["source_script"].endswith(".py"), p.name
            assert "DataGenerator" in prov["generated_by"], p.name

    def test_list_artifacts_use_sidecars(self, tmp_path):
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        for name in ("full_evaluation_results", "colony_results"):
            artifact = tmp_path / f"{name}.json"
            assert isinstance(json.loads(artifact.read_text()), list)
            assert provenance_sidecar_path(artifact).exists()

    def test_dict_generators_return_provenance_directly(self):
        """The methods themselves emit provenance, not only ``save``."""
        gen = DataGenerator(seed=42)
        for method_name in (
            "generate_ablation_results",
            "generate_sensitivity_results",
            "generate_cross_validation_results",
            "generate_statistical_results",
            "generate_multi_seed_results",
        ):
            payload = getattr(gen, method_name)()
            assert isinstance(payload, dict)
            for key in PROVENANCE_KEYS:
                assert key in payload, f"{method_name} missing {key}"
            assert payload["data_origin"] == DATA_ORIGIN_SYNTHETIC

    def test_save_without_provenance_is_byte_faithful(self, tmp_path):
        """``save`` must not inject anything when no provenance is supplied."""
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        payload = {"key": "value", "number": 42}
        path = gen.save(payload, "plain.json")
        assert json.loads(Path(path).read_text()) == payload
        assert not provenance_sidecar_path(Path(path)).exists()

    def test_save_does_not_relabel_declared_provenance(self, tmp_path):
        """A caller that declares real provenance keeps it."""
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        path = gen.save(
            {"data_origin": DATA_ORIGIN_REAL, "v": 1},
            "declared.json",
            provenance=gen.provenance(),
        )
        assert classify_provenance(path) == DATA_ORIGIN_REAL


# ===========================================================================
# Shipped artifacts
# ===========================================================================

_DATA_DIR = Path(__file__).resolve().parent.parent / "output" / "data"


class TestShippedArtifacts:
    """The checked-in results must not be DataGenerator placeholders."""

    @pytest.mark.parametrize("name", _REGRESSION_NAMES)
    def test_shipped_result_is_not_synthetic(self, name):
        path = _DATA_DIR / f"{name}.json"
        if not path.exists():
            pytest.skip(f"{name}.json not present in this checkout")
        # Shipped authoritative artifacts must be either measured pipeline
        # evidence (real_pipeline) or, for sensitivity, an explicitly-labelled
        # closed-form parametric model — never synthetic/schema placeholder,
        # and never overwritten by DataGenerator.  After P2-1, sensitivity is
        # honestly stamped `parametric_simulation` instead of a misleading
        # `real_pipeline`.
        origin = classify_provenance(path)
        assert origin in {DATA_ORIGIN_REAL, DATA_ORIGIN_PARAMETRIC}, (
            f"{name}.json classified as {origin!r} — it was probably "
            f"overwritten by DataGenerator"
        )

    @pytest.mark.parametrize("name", _REGRESSION_NAMES)
    def test_shipped_result_differs_from_generator_output(self, name, tmp_path):
        """The exact defect: on-disk file identical to synthetic constants."""
        path = _DATA_DIR / f"{name}.json"
        if not path.exists():
            pytest.skip(f"{name}.json not present in this checkout")

        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        gen.generate_all()
        synthetic = json.loads((tmp_path / f"{name}.json").read_text())
        shipped = json.loads(path.read_text())

        def _strip(payload):
            return {k: v for k, v in payload.items() if k not in PROVENANCE_KEYS}

        assert _strip(shipped) != _strip(synthetic), (
            f"{name}.json is byte-identical to DataGenerator output"
        )
