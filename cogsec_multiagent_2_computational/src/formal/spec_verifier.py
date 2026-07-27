"""Formal specification generation and verification.

Wraps NuSMV, SPIN, and TLA+ spec generators with optional tool verification.

Fail-closed contract
--------------------
A verification verdict is only ever ``PASS`` when the external checker was
actually executed *and* emitted positive evidence that every property holds.
Every other situation is reported as a distinct, non-passing state:

``SKIP``
    The checker is not installed (``shutil.which`` found nothing).
``ERROR``
    The checker is installed but could not be executed, timed out, crashed, or
    exited non-zero without emitting a property verdict.
``INCONCLUSIVE``
    The checker ran cleanly but its output does not establish the properties
    (unrecognised output, or an invocation that only translates the model
    rather than model-checking it).
``FAIL``
    The checker ran and reported at least one violated property.

This replaces an earlier negative-form check (``"error" not in output.lower()``)
under which a missing/broken binary, a silent stub on ``PATH``, or a NuSMV run
with mixed ``is true`` / ``is false`` verdicts all reported ``PASS``.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

from formal.nusmv_spec import generate_nusmv_spec
from formal.spin_spec import generate_promela_spec
from formal.tla_spec import generate_tla_spec

logger = logging.getLogger(__name__)

#: Wall-clock budget for a single model-checker invocation, in seconds.
DEFAULT_TIMEOUT_S = 300


class VerificationStatus(Enum):
    """Explicit outcome of one model-checker invocation.

    ``PASSED`` requires positive evidence from a checker that actually ran.
    The absence of an error message is never sufficient.
    """

    PASSED = "PASS"
    FAILED = "FAIL"
    SKIPPED = "SKIP"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class VerificationResult:
    """Structured verdict for a single tool/spec pair.

    Attributes:
        tool: Human-readable checker name (``"NuSMV"``, ``"SPIN"``, ``"TLA+"``).
        status: One of :class:`VerificationStatus`.
        detail: Free-text explanation (never used to derive ``status``).
    """

    tool: str
    status: VerificationStatus
    detail: str = ""

    @property
    def passed(self) -> bool:
        """True only for a genuine, evidence-backed pass."""
        return self.status is VerificationStatus.PASSED

    def __str__(self) -> str:
        if not self.detail:
            return self.status.value
        return f"{self.status.value}: {self.detail}"


@dataclass(frozen=True)
class CommandOutcome:
    """Result of attempting to run an external command.

    ``executed`` distinguishes "the process ran and produced a return code"
    from "the process could not be started / timed out".  Callers must branch
    on ``executed`` before interpreting ``stdout``/``stderr``; the previous
    implementation folded launch failures into a plain output string, which a
    negative-form substring test then read as success.
    """

    executed: bool
    returncode: Optional[int]
    stdout: str
    stderr: str
    error: str = ""

    @property
    def combined(self) -> str:
        """stdout and stderr concatenated, for text scanning."""
        return f"{self.stdout}\n{self.stderr}"


def check_tool(name: str) -> Optional[str]:
    """Check if a command-line tool is available in PATH.

    Returns the tool path or None.
    """
    return shutil.which(name)


def run_command(
    cmd: Sequence[str], cwd: Path, timeout: float = DEFAULT_TIMEOUT_S
) -> CommandOutcome:
    """Run a command and return a structured :class:`CommandOutcome`.

    Never raises for a failing or unlaunchable command.  A non-zero exit is
    reported via ``returncode`` with ``executed=True``; a failure to launch
    (missing binary, unusable ``cwd``, exec-format error, timeout) is reported
    with ``executed=False`` and a populated ``error``.

    Args:
        cmd: Argument vector.
        cwd: Working directory for the child process.
        timeout: Wall-clock limit in seconds.

    Returns:
        CommandOutcome describing what happened.
    """
    printable = " ".join(str(part) for part in cmd)
    try:
        completed = subprocess.run(  # noqa: S603 - argv list, no shell
            list(cmd),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out after %ss: %s", timeout, printable)
        return CommandOutcome(
            executed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"{printable} timed out after {timeout}s",
        )
    except OSError as exc:
        logger.warning("Command could not be executed: %s (%s)", printable, exc)
        return CommandOutcome(
            executed=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"{printable} could not be executed: {exc}",
        )
    return CommandOutcome(
        executed=True,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _launch_failure(tool: str, outcome: CommandOutcome) -> VerificationResult:
    """Uniform ERROR result for a checker that could not be run."""
    return VerificationResult(
        tool=tool,
        status=VerificationStatus.ERROR,
        detail=f"{tool} present but not runnable: {outcome.error}",
    )


# NuSMV prints one line per specification, e.g.
#   -- specification AG !compromised  is true
_NUSMV_VERDICT_RE = re.compile(
    r"--\s*specification\s+(?P<spec>.*?)\s+is\s+(?P<verdict>true|false)",
    re.IGNORECASE,
)

# SPIN reports parse/translation problems on stdout or stderr.
_SPIN_PROBLEM_RE = re.compile(
    r"(syntax error|spin:\s*error|redeclaration|undeclared|saw '|error:)",
    re.IGNORECASE,
)

_TLC_SUCCESS = "Model checking completed. No error"
_TLC_PROBLEM_RE = re.compile(
    r"(Invariant\s+\S+\s+is violated|is violated|Error:|Temporal properties were violated)",
    re.IGNORECASE,
)


def verify_nusmv(spec_path: Path) -> VerificationResult:
    """Verify a NuSMV spec, requiring an explicit per-specification verdict.

    PASS requires that NuSMV exited 0, emitted at least one
    ``-- specification ... is true`` line, and emitted no ``is false`` line.
    A run whose output mixes ``is true`` and ``is false`` is a FAIL, not a PASS.
    """
    tool = check_tool("NuSMV")
    if not tool:
        return VerificationResult(
            "NuSMV", VerificationStatus.SKIPPED, "NuSMV not found in PATH"
        )

    outcome = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if not outcome.executed:
        return _launch_failure("NuSMV", outcome)

    verdicts = _NUSMV_VERDICT_RE.findall(outcome.combined)
    falsified = [spec for spec, verdict in verdicts if verdict.lower() == "false"]
    if falsified:
        return VerificationResult(
            "NuSMV",
            VerificationStatus.FAILED,
            f"{len(falsified)}/{len(verdicts)} specifications false: "
            f"{'; '.join(falsified)[:400]}",
        )
    if not verdicts:
        return VerificationResult(
            "NuSMV",
            VerificationStatus.INCONCLUSIVE,
            "NuSMV produced no '-- specification ... is true/false' verdict "
            f"(exit {outcome.returncode}): {outcome.combined.strip()[:400]}",
        )
    if outcome.returncode != 0:
        return VerificationResult(
            "NuSMV",
            VerificationStatus.ERROR,
            f"NuSMV exited {outcome.returncode} despite emitting verdicts: "
            f"{outcome.combined.strip()[:400]}",
        )
    return VerificationResult(
        "NuSMV",
        VerificationStatus.PASSED,
        f"{len(verdicts)} specifications verified true",
    )


def verify_spin(spec_path: Path) -> VerificationResult:
    """Translate a Promela spec with ``spin -a`` and report an honest verdict.

    ``spin -a`` *generates* the ``pan`` verifier source; it does not run a
    model check.  A clean translation therefore cannot establish the temporal
    properties, so the best available verdict is INCONCLUSIVE.  Reporting PASS
    here (as the previous ``"error" not in output`` test did) credits the model
    with a verification that never ran.
    """
    tool = check_tool("spin")
    if not tool:
        return VerificationResult(
            "SPIN", VerificationStatus.SKIPPED, "SPIN not found in PATH"
        )

    outcome = run_command([tool, "-a", str(spec_path.name)], cwd=spec_path.parent)
    if not outcome.executed:
        return _launch_failure("SPIN", outcome)

    text = outcome.combined
    if outcome.returncode != 0 or _SPIN_PROBLEM_RE.search(text):
        return VerificationResult(
            "SPIN",
            VerificationStatus.FAILED,
            f"spin -a rejected the model (exit {outcome.returncode}): "
            f"{text.strip()[:400]}",
        )

    verifier_source = spec_path.parent / "pan.c"
    if not verifier_source.exists():
        return VerificationResult(
            "SPIN",
            VerificationStatus.ERROR,
            "spin -a exited 0 but produced no verifier source (pan.c); "
            "the binary on PATH does not behave like SPIN",
        )

    return VerificationResult(
        "SPIN",
        VerificationStatus.INCONCLUSIVE,
        "model translated to pan.c; 'spin -a' does not model-check — compile "
        "and run pan to obtain a temporal-property verdict",
    )


def verify_tla(spec_path: Path) -> VerificationResult:
    """Verify a TLA+ spec with TLC, requiring TLC's explicit success banner."""
    tool = check_tool("tlc")
    if not tool:
        return VerificationResult(
            "TLA+", VerificationStatus.SKIPPED, "TLC (TLA+ checker) not found in PATH"
        )

    outcome = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if not outcome.executed:
        return _launch_failure("TLA+", outcome)

    text = outcome.combined
    if _TLC_SUCCESS in text and outcome.returncode == 0:
        return VerificationResult(
            "TLA+", VerificationStatus.PASSED, "TLC completed with no errors"
        )
    if _TLC_PROBLEM_RE.search(text):
        return VerificationResult(
            "TLA+",
            VerificationStatus.FAILED,
            f"TLC reported a violation (exit {outcome.returncode}): "
            f"{text.strip()[:400]}",
        )
    if outcome.returncode != 0:
        return VerificationResult(
            "TLA+",
            VerificationStatus.ERROR,
            f"TLC exited {outcome.returncode} without a recognised verdict: "
            f"{text.strip()[:400]}",
        )
    return VerificationResult(
        "TLA+",
        VerificationStatus.INCONCLUSIVE,
        f"TLC produced no recognised verdict: {text.strip()[:400]}",
    )


def generate_and_verify_all(
    output_dir: Path,
    *,
    n_agents: int = 5,
    max_byzantine: int = 1,
) -> dict[str, VerificationResult]:
    """Generate all formal specs and verify with available tools.

    Parameters
    ----------
    output_dir : Path
        Directory to write spec files.
    n_agents : int
        Number of agents for the spec.
    max_byzantine : int
        Maximum number of Byzantine agents.

    Returns
    -------
    dict
        Mapping of spec name → :class:`VerificationResult`.  Use
        ``str(result)`` for the legacy ``"PASS"`` / ``"SKIP: ..."`` rendering
        and ``result.passed`` for a boolean that is true only for an
        evidence-backed pass.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, VerificationResult] = {}

    # NuSMV
    nusmv_content = generate_nusmv_spec(n_agents=n_agents, max_byzantine=max_byzantine)
    nusmv_path = output_dir / "cif_model.smv"
    nusmv_path.write_text(nusmv_content)
    results["NuSMV"] = verify_nusmv(nusmv_path)

    # SPIN
    spin_content = generate_promela_spec(n_agents=n_agents, max_byzantine=max_byzantine)
    spin_path = output_dir / "cif_model.pml"
    spin_path.write_text(spin_content)
    results["SPIN"] = verify_spin(spin_path)

    # TLA+
    tla_content = generate_tla_spec(n_agents=n_agents, max_byzantine=max_byzantine)
    tla_path = output_dir / "CognitiveIntegrityFramework.tla"
    tla_path.write_text(tla_content)
    results["TLA+"] = verify_tla(tla_path)

    return results
