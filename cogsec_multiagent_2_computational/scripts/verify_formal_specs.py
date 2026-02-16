#!/usr/bin/env python3
"""
Formal Specification Verification Script.

This script generates the formal specifications (NuSMV, SPIN, TLA+) for the
Cognitive Integrity Framework and attempts to run the model checkers if available.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path (insert at front to take priority over system src package)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.formal.nusmv_spec import generate_nusmv_spec
from src.formal.spin_spec import generate_promela_spec
from src.formal.tla_spec import generate_tla_spec

OUTPUT_DIR = Path("output/formal")


def check_tool(name: str) -> Optional[str]:
    """Check if a tool is available in PATH."""
    return shutil.which(name)


def run_command(cmd: List[str], cwd: Path) -> str:
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running {' '.join(cmd)}: {e.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"


def verify_nusmv(spec_path: Path) -> None:
    """Verify NuSMV spec."""
    tool = check_tool("NuSMV")
    if not tool:
        print("  [SKIP] NuSMV not found in PATH.")
        return

    print("  [RUN] Running NuSMV...")
    output = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if "is true" in output:
        print("  [PASS] Specification validated successfully.")
    else:
        print("  [FAIL] Verification output:\n" + output[:500] + "...")


def verify_spin(spec_path: Path) -> None:
    """Verify SPIN spec."""
    tool = check_tool("spin")
    if not tool:
        print("  [SKIP] SPIN not found in PATH.")
        return

    print("  [RUN] Running SPIN syntax check...")
    output = run_command([tool, "-a", str(spec_path.name)], cwd=spec_path.parent)
    if "error" not in output.lower():
        print("  [PASS] Syntax check passed.")
    else:
        print("  [FAIL] Syntax check failed:\n" + output[:500])


def verify_tla(spec_path: Path) -> None:
    """Verify TLA+ spec."""
    # Java-based tools are harder to detect, check for tlc or tla2tools usage pattern
    # Assuming 'tlc' alias or script exists
    tool = check_tool("tlc")
    if not tool:
        print("  [SKIP] TLC (TLA+ checker) not found in PATH.")
        return

    print("  [RUN] Running TLC...")
    output = run_command([tool, str(spec_path.name)], cwd=spec_path.parent)
    if "Model checking completed. No error" in output:
        print("  [PASS] Model checking passed.")
    else:
        print("  [FAIL] Verification output:\n" + output[:500])


def main():
    """Main execution."""
    print("Cognitive Integrity Framework - Formal Verification")
    print("===================================================")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

    # 1. Generate NuSMV
    print("\n1. Generating NuSMV Specification...")
    nusmv_content = generate_nusmv_spec(n_agents=5, max_byzantine=1)
    nusmv_path = OUTPUT_DIR / "cif_model.smv"
    nusmv_path.write_text(nusmv_content)
    print(f"  [OK] Written to {nusmv_path.name}")
    verify_nusmv(nusmv_path)

    # 2. Generate SPIN (Promela)
    print("\n2. Generating SPIN (Promela) Specification...")
    spin_content = generate_promela_spec(n_agents=5, max_byzantine=1)
    spin_path = OUTPUT_DIR / "cif_model.pml"
    spin_path.write_text(spin_content)
    print(f"  [OK] Written to {spin_path.name}")
    verify_spin(spin_path)

    # 3. Generate TLA+
    print("\n3. Generating TLA+ Specification...")
    tla_content = generate_tla_spec(n_agents=5, max_byzantine=1)
    tla_path = OUTPUT_DIR / "CognitiveIntegrityFramework.tla"
    tla_path.write_text(tla_content)
    print(f"  [OK] Written to {tla_path.name}")
    verify_tla(tla_path)

    print("\n---------------------------------------------------")
    print("Verification Artifact Generation Complete.")


if __name__ == "__main__":
    main()
