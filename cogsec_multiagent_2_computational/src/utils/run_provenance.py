"""Run-provenance capture for generated data artifacts.

A reader who downloads ``output/data/*.json`` cannot otherwise tell which
revision of the code, which interpreter, or which numeric stack produced the
numbers — BLAS-threaded floating-point ordering alone perturbs the third
decimal of a detection rate, so an environment difference is indistinguishable
from a genuine irreproducibility.  This module captures that environment.

It is deliberately *narrow*: it records facts, never opinions, and it never
invents one.  Every field that cannot be established degrades to
:data:`PROVENANCE_UNKNOWN` (or, for the package map, to ``"unknown"`` for the
individual package).  In particular a commit SHA is emitted only when ``git``
actually returns a 40-hex object name for ``HEAD``; there is no fallback to a
tag, a branch name, or an environment variable that could be mistaken for a
real revision.

Determinism
-----------
Wall-clock time is the only nondeterministic field.  ``include_timestamp=False``
sets ``timestamp_utc`` to ``None`` and leaves every other field intact, so the
whole block becomes byte-stable within one checkout and environment.  This
matters because :class:`data.generate.DataGenerator` is byte-deterministic for
a fixed seed, and several callers rely on that.

Unknown-safety of ``git_dirty``
-------------------------------
``git_dirty`` is ``True``/``False`` when git answered and the string
``"unknown"`` when it did not.  ``"unknown"`` is deliberately *truthy* so that
``if prov["git_dirty"]:`` reads an unestablished state as "assume dirty"
rather than silently as "clean".
"""

from __future__ import annotations

import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

#: Value recorded for any fact that could not be established.
PROVENANCE_UNKNOWN = "unknown"

#: Packages whose resolved versions are recorded with every artifact.  These
#: are the three that move published numbers: numpy/scipy drive the arithmetic,
#: matplotlib drives the figures.
TRACKED_PACKAGES: tuple[str, ...] = ("numpy", "scipy", "matplotlib")

#: Keys present in every :func:`run_provenance` block.
RUN_PROVENANCE_KEYS: tuple[str, ...] = (
    "source_script",
    "seed",
    "git_commit",
    "git_dirty",
    "python_version",
    "python_implementation",
    "platform",
    "packages",
    "timestamp_utc",
)

#: Repository root used when the caller does not name one: the project
#: directory two levels above ``src/utils/``.
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Hard ceiling on any git invocation so a wedged git can never hang a run.
_GIT_TIMEOUT_S = 15.0

_SHA_LENGTH = 40
_HEX_DIGITS = frozenset("0123456789abcdef")


def _git(args: Sequence[str], repo_root: Path) -> Optional[str]:
    """Run ``git *args`` in *repo_root*, returning stdout or ``None``.

    ``None`` means "git could not answer": the binary is absent, the directory
    is not a checkout, the command failed, or it timed out.  No exception
    escapes, and nothing is invented in place of an answer.

    Parameters
    ----------
    args : sequence of str
        Arguments after the ``git`` executable.  Never passed through a shell.
    repo_root : Path
        Working directory for the invocation.

    Returns
    -------
    str or None
    """
    try:
        # Fixed argv, shell=False: nothing here is interpolated into a shell.
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _looks_like_sha(value: str) -> bool:
    """Return ``True`` only for a full 40-character lowercase hex object name."""
    return len(value) == _SHA_LENGTH and set(value) <= _HEX_DIGITS


def git_commit(repo_root: Union[str, Path, None] = None) -> str:
    """Return the ``HEAD`` commit SHA, or :data:`PROVENANCE_UNKNOWN`.

    A value is returned only when git prints something that is actually a
    40-hex object name.  Anything else — no git, no checkout, a fresh repo with
    no commits, a truncated or symbolic answer — yields ``"unknown"``.

    Parameters
    ----------
    repo_root : str or Path, optional
        Directory to resolve ``HEAD`` in.  Defaults to :data:`DEFAULT_REPO_ROOT`.

    Returns
    -------
    str
    """
    root = Path(repo_root) if repo_root is not None else DEFAULT_REPO_ROOT
    out = _git(["rev-parse", "HEAD"], root)
    if out is None:
        return PROVENANCE_UNKNOWN
    sha = out.strip().lower()
    return sha if _looks_like_sha(sha) else PROVENANCE_UNKNOWN


def git_dirty(repo_root: Union[str, Path, None] = None) -> Union[bool, str]:
    """Return whether the working tree has uncommitted or untracked changes.

    Parameters
    ----------
    repo_root : str or Path, optional
        Directory to inspect.  Defaults to :data:`DEFAULT_REPO_ROOT`.

    Returns
    -------
    bool or str
        ``True``/``False`` when git answered; :data:`PROVENANCE_UNKNOWN`
        (truthy, so it is read conservatively) when it did not.
    """
    root = Path(repo_root) if repo_root is not None else DEFAULT_REPO_ROOT
    out = _git(["status", "--porcelain"], root)
    if out is None:
        return PROVENANCE_UNKNOWN
    return bool(out.strip())


def package_versions(
    names: Sequence[str] = TRACKED_PACKAGES,
) -> Dict[str, str]:
    """Return resolved distribution versions for *names*.

    Parameters
    ----------
    names : sequence of str, optional
        Distribution names.  Defaults to :data:`TRACKED_PACKAGES`.

    Returns
    -------
    dict
        Name → version string, or :data:`PROVENANCE_UNKNOWN` when the
        distribution is not installed in the running environment.
    """
    resolved: Dict[str, str] = {}
    for name in names:
        try:
            resolved[name] = version(name)
        except PackageNotFoundError:
            resolved[name] = PROVENANCE_UNKNOWN
    return resolved


def utc_timestamp() -> str:
    """Return the current UTC time as a second-resolution ISO-8601 string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_provenance(
    source_script: str,
    seed: Optional[int] = None,
    *,
    repo_root: Union[str, Path, None] = None,
    include_timestamp: bool = True,
    packages: Sequence[str] = TRACKED_PACKAGES,
) -> Dict[str, Any]:
    """Capture the environment that produced an artifact.

    Parameters
    ----------
    source_script : str
        Repository-relative path of the producing script, e.g.
        ``"scripts/generate_all_data.py"``.
    seed : int, optional
        Master seed the producer was run with.  ``None`` when the producer is
        not seeded.
    repo_root : str or Path, optional
        Checkout to read git facts from.  Defaults to :data:`DEFAULT_REPO_ROOT`.
    include_timestamp : bool, default True
        When ``False``, ``timestamp_utc`` is ``None`` and the block becomes
        byte-stable for a fixed checkout and environment.
    packages : sequence of str, optional
        Distributions to record.  Defaults to :data:`TRACKED_PACKAGES`.

    Returns
    -------
    dict
        Exactly the keys in :data:`RUN_PROVENANCE_KEYS`.
    """
    root = Path(repo_root) if repo_root is not None else DEFAULT_REPO_ROOT
    return {
        "source_script": source_script,
        "seed": seed,
        "git_commit": git_commit(root),
        "git_dirty": git_dirty(root),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": package_versions(packages),
        "timestamp_utc": utc_timestamp() if include_timestamp else None,
    }


def format_run_provenance(block: Dict[str, Any]) -> str:
    """Render a provenance block as a short human-readable summary.

    Parameters
    ----------
    block : dict
        A :func:`run_provenance` result.

    Returns
    -------
    str
    """
    commit = str(block.get("git_commit", PROVENANCE_UNKNOWN))
    short = commit[:12] if _looks_like_sha(commit) else commit
    dirty = block.get("git_dirty", PROVENANCE_UNKNOWN)
    dirty_txt = "dirty" if dirty is True else ("clean" if dirty is False else "dirty?")
    pkgs = block.get("packages", {})
    pkg_txt = ", ".join(f"{k}={v}" for k, v in sorted(pkgs.items())) if pkgs else "none"
    return (
        f"git {short} ({dirty_txt}) | "
        f"python {block.get('python_version', PROVENANCE_UNKNOWN)} | "
        f"{block.get('platform', PROVENANCE_UNKNOWN)} | "
        f"{pkg_txt} | "
        f"seed={block.get('seed')} | "
        f"utc={block.get('timestamp_utc')}"
    )
