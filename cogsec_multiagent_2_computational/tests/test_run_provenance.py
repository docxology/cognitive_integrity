"""Run-provenance capture: honesty, graceful degradation, and determinism.

The defect this file guards against is a data artifact that cannot be traced
to the code and environment that produced it, and — worse — one that *claims*
a provenance it does not have.  Two properties therefore need positive
controls, because both could be satisfied by a constant:

* ``git_dirty`` must actually track the tree.  A helper hardcoded to ``False``
  would pass any single-state assertion, so :class:`TestGitDirtyFlag` builds a
  real throwaway repository, commits, asserts ``False``, then mutates the tree
  and asserts ``True``.  Neither half passes on its own under a constant.
* ``git_commit`` must degrade to ``"unknown"`` outside a checkout rather than
  crash or invent a SHA.  A helper hardcoded to ``"unknown"`` would pass that,
  so :class:`TestGitCommit` pairs it with an assertion that inside a real
  repository the helper returns the *exact* SHA ``git rev-parse HEAD`` prints.

The ambient tree cannot be used for either control: it is usually clean and
always a checkout, so both assertions would be one-sided.  Every git fact here
comes from a repository created under ``tmp_path`` by real ``git`` commands.

No mocks.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Sequence

import pytest

from data.generate import (
    DATA_ORIGIN_REAL,
    PROVENANCE_KEYS,
    DataGenerator,
    provenance_sidecar_path,
    read_provenance,
)
from utils.run_provenance import (
    DEFAULT_REPO_ROOT,
    PROVENANCE_UNKNOWN,
    RUN_PROVENANCE_KEYS,
    TRACKED_PACKAGES,
    format_run_provenance,
    git_commit,
    git_dirty,
    package_versions,
    run_provenance,
    utc_timestamp,
)

_HEX = set("0123456789abcdef")


# ---------------------------------------------------------------------------
# Real-git helpers (no mocks: these shell out to the actual git binary)
# ---------------------------------------------------------------------------

def _git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def _git_available() -> bool:
    try:
        subprocess.run(
            ["git", "--version"], capture_output=True, timeout=30, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return True


requires_git = pytest.mark.skipif(
    not _git_available(), reason="git binary not available",
)


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """A real git repository with exactly one commit and a clean tree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "--quiet"], repo)
    _git(["config", "user.email", "test@example.invalid"], repo)
    _git(["config", "user.name", "Provenance Test"], repo)
    _git(["config", "commit.gpgsign", "false"], repo)
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(["add", "tracked.txt"], repo)
    _git(["commit", "--quiet", "-m", "initial"], repo)
    return repo


@pytest.fixture
def outside_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory that git must treat as outside any checkout.

    ``GIT_CEILING_DIRECTORIES`` stops git ascending past *tmp_path*, so the
    result does not depend on whether the machine's temp directory happens to
    sit inside somebody's repository.
    """
    work = tmp_path / "not_a_repo"
    work.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    return work


# ===========================================================================
# git_commit
# ===========================================================================

@requires_git
class TestGitCommit:
    """The SHA must be real when there is one and absent when there is not."""

    def test_returns_the_exact_head_sha_in_a_real_repo(self, temp_repo):
        """POSITIVE CONTROL for the degradation test below.

        If the helper simply returned ``"unknown"`` it would satisfy
        :meth:`test_unknown_outside_a_checkout` while recording nothing.  This
        pins the value to what git itself prints.
        """
        expected = _git(["rev-parse", "HEAD"], temp_repo).stdout.strip()
        assert len(expected) == 40

        assert git_commit(temp_repo) == expected

    def test_unknown_outside_a_checkout(self, outside_repo):
        """Outside a checkout: ``"unknown"``, not a crash and not a guess."""
        assert git_commit(outside_repo) == PROVENANCE_UNKNOWN

    def test_unknown_in_a_repo_with_no_commits(self, tmp_path):
        """``git init`` with no commit has no HEAD — that is not a SHA."""
        repo = tmp_path / "empty"
        repo.mkdir()
        _git(["init", "--quiet"], repo)
        assert git_commit(repo) == PROVENANCE_UNKNOWN

    def test_unknown_for_a_nonexistent_directory(self, tmp_path):
        """A missing cwd raises inside subprocess; the helper must absorb it."""
        assert git_commit(tmp_path / "does" / "not" / "exist") == PROVENANCE_UNKNOWN

    def test_value_is_never_a_partial_or_symbolic_name(self, temp_repo):
        sha = git_commit(temp_repo)
        assert set(sha) <= _HEX
        assert sha not in {"HEAD", "main", "master", ""}


# ===========================================================================
# git_dirty  (the mandated positive control)
# ===========================================================================

@requires_git
class TestGitDirtyFlag:
    """The dirty flag must track the tree, in both directions."""

    def test_clean_tree_reports_false(self, temp_repo):
        """Half one of the pair: a freshly committed tree is clean."""
        assert _git(["status", "--porcelain"], temp_repo).stdout.strip() == ""
        assert git_dirty(temp_repo) is False

    def test_modified_tracked_file_reports_true(self, temp_repo):
        """POSITIVE CONTROL: the flag flips to True when the tree is dirtied.

        The ambient repository was clean when this suite was written, so an
        assertion against it would have been satisfied by a hardcoded
        ``False``.  The condition is constructed here instead.
        """
        assert git_dirty(temp_repo) is False  # precondition

        (temp_repo / "tracked.txt").write_text("v2 — modified\n", encoding="utf-8")

        assert _git(["status", "--porcelain"], temp_repo).stdout.strip() != ""
        assert git_dirty(temp_repo) is True

    def test_untracked_file_also_reports_true(self, temp_repo):
        assert git_dirty(temp_repo) is False
        (temp_repo / "brand_new.txt").write_text("hello\n", encoding="utf-8")
        assert git_dirty(temp_repo) is True

    def test_staged_change_reports_true(self, temp_repo):
        (temp_repo / "tracked.txt").write_text("v3\n", encoding="utf-8")
        _git(["add", "tracked.txt"], temp_repo)
        assert git_dirty(temp_repo) is True

    def test_returns_to_false_after_committing(self, temp_repo):
        """The flag is not sticky: it follows the tree back to clean."""
        (temp_repo / "tracked.txt").write_text("v4\n", encoding="utf-8")
        assert git_dirty(temp_repo) is True
        _git(["add", "tracked.txt"], temp_repo)
        _git(["commit", "--quiet", "-m", "second"], temp_repo)
        assert git_dirty(temp_repo) is False

    def test_unknown_outside_a_checkout_is_truthy(self, outside_repo):
        """Unestablished state must not read as "clean" to a boolean test."""
        value = git_dirty(outside_repo)
        assert value == PROVENANCE_UNKNOWN
        assert value is not False
        assert bool(value) is True

    def test_unknown_for_a_nonexistent_directory(self, tmp_path):
        assert git_dirty(tmp_path / "nope") == PROVENANCE_UNKNOWN


# ===========================================================================
# package_versions
# ===========================================================================

class TestPackageVersions:
    """Versions come from the installed distributions, never from a literal."""

    def test_tracked_packages_resolve(self):
        versions = package_versions()
        assert set(versions) == set(TRACKED_PACKAGES)
        for name, ver in versions.items():
            assert ver != PROVENANCE_UNKNOWN, f"{name} should be installed"

    def test_recorded_numpy_version_matches_the_imported_module(self):
        """Binds the record to the actual runtime, not to a stored string."""
        import numpy

        assert package_versions(["numpy"])["numpy"] == numpy.__version__

    def test_absent_distribution_is_unknown_not_a_crash(self):
        name = "cogsec-definitely-not-installed-xyz"
        assert package_versions([name]) == {name: PROVENANCE_UNKNOWN}

    def test_empty_selection_is_empty(self):
        assert package_versions([]) == {}


# ===========================================================================
# run_provenance block
# ===========================================================================

class TestRunProvenanceBlock:
    """Shape, honesty, and the deterministic mode."""

    def test_has_exactly_the_documented_keys(self):
        block = run_provenance("scripts/generate_all_data.py", 42)
        assert set(block) == set(RUN_PROVENANCE_KEYS)

    def test_records_source_script_and_seed(self):
        block = run_provenance("scripts/run_ablation.py", 7)
        assert block["source_script"] == "scripts/run_ablation.py"
        assert block["seed"] == 7

    def test_seed_may_be_absent(self):
        block = run_provenance("scripts/x.py", None)
        assert block["seed"] is None

    def test_environment_fields_are_populated(self):
        block = run_provenance("scripts/x.py", 42)
        assert block["python_version"].count(".") >= 2
        assert block["python_implementation"]
        assert block["platform"]
        assert set(block["packages"]) == set(TRACKED_PACKAGES)

    def test_python_version_matches_the_running_interpreter(self):
        import sys

        block = run_provenance("scripts/x.py", 42)
        major, minor = sys.version_info[:2]
        assert block["python_version"].startswith(f"{major}.{minor}.")

    @requires_git
    def test_git_fields_come_from_the_named_repo_root(self, temp_repo):
        block = run_provenance("scripts/x.py", 1, repo_root=temp_repo)
        assert block["git_commit"] == _git(["rev-parse", "HEAD"], temp_repo).stdout.strip()
        assert block["git_dirty"] is False

    @requires_git
    def test_dirty_flag_propagates_into_the_block(self, temp_repo):
        """POSITIVE CONTROL: the block reflects a dirtied tree, not a constant."""
        clean = run_provenance("scripts/x.py", 1, repo_root=temp_repo)
        (temp_repo / "tracked.txt").write_text("dirtied\n", encoding="utf-8")
        dirty = run_provenance("scripts/x.py", 1, repo_root=temp_repo)

        assert clean["git_dirty"] is False
        assert dirty["git_dirty"] is True

    def test_outside_a_checkout_the_block_is_unknown_not_missing(self, outside_repo):
        block = run_provenance("scripts/x.py", 42, repo_root=outside_repo)
        assert set(block) == set(RUN_PROVENANCE_KEYS)
        assert block["git_commit"] == PROVENANCE_UNKNOWN
        assert block["git_dirty"] == PROVENANCE_UNKNOWN
        # Everything that does not need git is still recorded.
        assert block["platform"]
        assert block["python_version"]

    def test_timestamp_present_by_default(self):
        block = run_provenance("scripts/x.py", 42)
        assert isinstance(block["timestamp_utc"], str)
        assert block["timestamp_utc"].endswith("+00:00")

    def test_no_timestamp_mode_nulls_only_the_clock(self, outside_repo):
        """Deterministic mode drops wall-clock and nothing else."""
        with_ts = run_provenance(
            "scripts/x.py", 42, repo_root=outside_repo, include_timestamp=True,
        )
        without_ts = run_provenance(
            "scripts/x.py", 42, repo_root=outside_repo, include_timestamp=False,
        )
        assert without_ts["timestamp_utc"] is None
        assert with_ts["timestamp_utc"] is not None
        assert {k: v for k, v in with_ts.items() if k != "timestamp_utc"} == {
            k: v for k, v in without_ts.items() if k != "timestamp_utc"
        }

    @requires_git
    def test_no_timestamp_mode_is_byte_stable(self, temp_repo):
        first = run_provenance(
            "s.py", 42, repo_root=temp_repo, include_timestamp=False,
        )
        second = run_provenance(
            "s.py", 42, repo_root=temp_repo, include_timestamp=False,
        )
        # Asserted explicitly: two runs inside the same wall-clock second would
        # otherwise satisfy the equality below even if the flag were ignored.
        assert first["timestamp_utc"] is None
        assert second["timestamp_utc"] is None
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)

    def test_block_is_json_serialisable(self):
        block = run_provenance("scripts/x.py", 42)
        assert json.loads(json.dumps(block)) == block

    def test_default_repo_root_is_the_project_directory(self):
        assert (DEFAULT_REPO_ROOT / "src" / "utils" / "run_provenance.py").is_file()

    def test_utc_timestamp_is_second_resolution_iso8601(self):
        stamp = utc_timestamp()
        assert stamp.endswith("+00:00")
        assert "." not in stamp  # microseconds stripped


class TestFormatRunProvenance:
    """The human-readable summary must not overstate what was captured."""

    def test_renders_a_real_block(self):
        text = format_run_provenance(run_provenance("scripts/x.py", 42))
        assert "python " in text
        assert "numpy=" in text
        assert "seed=42" in text

    def test_unknown_commit_is_shown_as_unknown(self, outside_repo):
        text = format_run_provenance(
            run_provenance("scripts/x.py", 42, repo_root=outside_repo),
        )
        assert PROVENANCE_UNKNOWN in text
        assert "dirty?" in text

    @requires_git
    def test_clean_and_dirty_render_differently(self, temp_repo):
        clean = format_run_provenance(run_provenance("s.py", 1, repo_root=temp_repo))
        (temp_repo / "tracked.txt").write_text("x\n", encoding="utf-8")
        dirty = format_run_provenance(run_provenance("s.py", 1, repo_root=temp_repo))
        assert "(clean)" in clean
        assert "(dirty)" in dirty

    def test_empty_block_does_not_crash(self):
        text = format_run_provenance({})
        assert PROVENANCE_UNKNOWN in text
        assert "none" in text


# ===========================================================================
# DataGenerator integration
# ===========================================================================

def _artifacts(directory: Path) -> List[Path]:
    return sorted(
        p for p in directory.glob("*.json") if not p.name.endswith(".provenance.json")
    )


class TestDataGeneratorStamping:
    """Every artifact generate_all writes must carry the environment record."""

    def test_every_artifact_records_run_provenance(self, tmp_path):
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        artifacts = _artifacts(tmp_path)
        assert artifacts, "no artifacts written — this test would be vacuous"

        for path in artifacts:
            prov = read_provenance(path)
            block = prov.get("run_provenance")
            assert isinstance(block, dict), f"{path.name} has no run_provenance"
            assert set(block) == set(RUN_PROVENANCE_KEYS), path.name
            assert block["seed"] == 42, path.name
            assert block["source_script"].endswith(".py"), path.name
            assert block["packages"]["numpy"] != PROVENANCE_UNKNOWN, path.name

    def test_run_provenance_is_part_of_the_provenance_key_set(self):
        """Keeping it inside PROVENANCE_KEYS is what stops the shipped-vs-
        synthetic comparison in test_data_provenance.py from going vacuous."""
        assert "run_provenance" in PROVENANCE_KEYS

    def test_list_artifacts_carry_it_in_the_sidecar(self, tmp_path):
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        for name in ("full_evaluation_results", "colony_results"):
            artifact = tmp_path / f"{name}.json"
            assert isinstance(json.loads(artifact.read_text()), list)
            sidecar = json.loads(provenance_sidecar_path(artifact).read_text())
            assert set(sidecar["run_provenance"]) == set(RUN_PROVENANCE_KEYS)

    def test_all_artifacts_of_one_run_share_one_block(self, tmp_path):
        """One run, one environment record — not eleven different clocks."""
        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        blocks = {
            json.dumps(read_provenance(p)["run_provenance"], sort_keys=True)
            for p in _artifacts(tmp_path)
        }
        assert len(blocks) == 1, f"{len(blocks)} distinct provenance blocks"

    def test_generator_block_matches_the_helper_contract(self, tmp_path):
        gen = DataGenerator(seed=99, output_dir=str(tmp_path))
        block = gen.run_provenance()
        assert set(block) == set(RUN_PROVENANCE_KEYS)
        assert block["seed"] == 99
        assert block["source_script"] == "scripts/generate_all_data.py"
        # Cached: the same object is reused for every artifact.
        assert gen.run_provenance() is block


class TestDataGeneratorDeterminism:
    """The deterministic mode must actually restore byte-for-byte equality."""

    def _run(self, directory: Path, *, include_timestamp: bool) -> None:
        DataGenerator(
            seed=42,
            output_dir=str(directory),
            include_timestamp=include_timestamp,
        ).generate_all()

    def test_no_timestamp_mode_is_byte_identical_across_runs(self, tmp_path):
        a, b = tmp_path / "a", tmp_path / "b"
        self._run(a, include_timestamp=False)
        self._run(b, include_timestamp=False)

        # Asserted before the byte comparison: two runs landing in the same
        # wall-clock second would otherwise satisfy it even if
        # include_timestamp were ignored entirely.
        artifacts = _artifacts(a)
        assert artifacts, "no artifacts written — this test would be vacuous"
        for path in artifacts:
            clock = read_provenance(path)["run_provenance"]["timestamp_utc"]
            assert clock is None, f"{path.name} still records a clock: {clock!r}"

        # Every file, artifacts and provenance sidecars alike.
        names = [p.name for p in sorted(a.glob("*.json"))]
        assert len(names) > len(artifacts), "sidecars missing from the comparison"
        for name in names:
            assert (a / name).read_bytes() == (b / name).read_bytes(), name

    def test_default_mode_actually_writes_a_clock(self, tmp_path):
        """POSITIVE CONTROL for the determinism test.

        If ``include_timestamp`` were ignored, both modes would emit the same
        bytes and the test above would prove nothing about the flag.  Default
        output must in fact carry a clock, and deterministic output must not.
        """
        stamped, plain = tmp_path / "stamped", tmp_path / "plain"
        self._run(stamped, include_timestamp=True)
        self._run(plain, include_timestamp=False)

        stamped_artifacts = _artifacts(stamped)
        assert stamped_artifacts, "no artifacts written — this test would be vacuous"

        for path in stamped_artifacts:
            clock = read_provenance(path)["run_provenance"]["timestamp_utc"]
            assert isinstance(clock, str) and clock, path.name
            assert read_provenance(plain / path.name)[
                "run_provenance"
            ]["timestamp_utc"] is None, path.name

    def test_timestamped_runs_agree_once_the_clock_is_removed(self, tmp_path):
        """Wall-clock is the *only* nondeterministic field."""
        a, b = tmp_path / "ts_a", tmp_path / "ts_b"
        self._run(a, include_timestamp=True)
        self._run(b, include_timestamp=True)

        artifacts = _artifacts(a)
        assert artifacts, "no artifacts written — this test would be vacuous"
        for path in artifacts:
            assert _without_clock(path) == _without_clock(b / path.name), path.name


def _without_clock(path: Path) -> object:
    """Load an artifact (plus sidecar) with every timestamp removed."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("run_provenance"), dict):
        payload["run_provenance"] = {
            k: v for k, v in payload["run_provenance"].items() if k != "timestamp_utc"
        }
    sidecar_path = provenance_sidecar_path(path)
    sidecar: Optional[object] = None
    if sidecar_path.is_file():
        raw = json.loads(sidecar_path.read_text(encoding="utf-8"))
        raw.pop("artifact_sha256", None)
        if isinstance(raw.get("run_provenance"), dict):
            raw["run_provenance"] = {
                k: v for k, v in raw["run_provenance"].items() if k != "timestamp_utc"
            }
        sidecar = raw
    return (payload, sidecar)


class TestRealArtifactsAreNotTouched:
    """Stamping must not reach into measured evidence."""

    def test_real_marked_artifact_keeps_its_numbers_and_gains_nothing(self, tmp_path):
        real = {
            "data_origin": DATA_ORIGIN_REAL,
            "source_script": "scripts/run_statistical_analysis.py",
            "generated_by": "scripts/run_statistical_analysis.py --seed 42",
            "seed": 42,
            "cohens_d_cif_vs_baseline": 3.14159,
        }
        path = tmp_path / "statistical_results.json"
        path.write_text(json.dumps(real, indent=2), encoding="utf-8")
        before = path.read_bytes()

        DataGenerator(seed=42, output_dir=str(tmp_path)).generate_all()

        assert path.read_bytes() == before
        payload = json.loads(path.read_text())
        assert payload["cohens_d_cif_vs_baseline"] == 3.14159
        assert "run_provenance" not in payload
