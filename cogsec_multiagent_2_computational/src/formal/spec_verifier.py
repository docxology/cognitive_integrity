"""Formal specification generation and verification.

Wraps NuSMV, SPIN, and TLA+ spec generators with optional tool verification.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from formal.nusmv_spec import generate_nusmv_spec
from formal.spin_spec import generate_promela_spec
from formal.tla_spec import generate_tla_spec

logger = logging.getLogger(__name__)


def check_tool(name: str) -> Optional[str]:
    """Check if a command-line tool is available in PATH.

    Returns the tool path or None.
    """
    return shutil.which(name)


def run_command(cmd: list[str], cwd: Path) -> str:
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running {' '.join(cmd)}: {e.stderr}"
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"Execution failed: {e!s}"


def verify_nusmv(spec_path: Path) -> str:
    """Verify NuSMV spec if tool is available. Returns status string."""
    tool = check_tool("NuSMV")
    if not tool:
        return "SKIP: NuSMV not found in PATH"
    output = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if "is true" in output:
        return "PASS"
    return f"FAIL: {output[:500]}"


def verify_spin(spec_path: Path) -> str:
    """Verify SPIN spec if tool is available. Returns status string."""
    tool = check_tool("spin")
    if not tool:
        return "SKIP: SPIN not found in PATH"
    output = run_command([tool, "-a", str(spec_path.name)], cwd=spec_path.parent)
    if "error" not in output.lower():
        return "PASS"
    return f"FAIL: {output[:500]}"


def verify_tla(spec_path: Path) -> str:
    """Verify TLA+ spec if TLC is available. Returns status string."""
    tool = check_tool("tlc")
    if not tool:
        return "SKIP: TLC (TLA+ checker) not found in PATH"
    output = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if "Model checking completed. No error" in output:
        return "PASS"
    return f"FAIL: {output[:500]}"


def generate_and_verify_all(
    output_dir: Path,
    *,
    n_agents: int = 5,
    max_byzantine: int = 1,
) -> dict[str, str]:
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
        Mapping of spec name → verification status string.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

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
