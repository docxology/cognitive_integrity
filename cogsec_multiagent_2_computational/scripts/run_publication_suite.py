#!/usr/bin/env python3
"""Run full-scale publication experiments.

This script automates the execution of the two major evaluation modes required
for the manuscript:
1. Parametric Simulation (N=10,450): 11 replicates of the 950-sample corpus.
2. LLM-Empirical Evaluation (N=~160): 10 samples × 4 categories × 4 architectures.

It is discovered and executed automatically by the analysis pipeline.
"""

import sys
import subprocess
from pathlib import Path

def main() -> None:
    # Resolve paths
    current_script = Path(__file__).resolve()
    project_root = current_script.parent.parent
    scripts_dir = current_script.parent
    runner_script = scripts_dir / "run_full_evaluation.py"
    
    print("=" * 70)
    print("     RUNNING PUBLICATION-SCALE EXPERIMENTS")
    print("=" * 70)
    
    # 1. Parametric Simulation (N = 950 * 11 = 10,450)
    print("\n[Part 1/2] Parametric Simulation: 10,000+ Replicates")
    cmd_sim = [
        sys.executable, str(runner_script),
        "--mode", "simulation",
        "--replicates", "11",
        "--seed", "42",
        "--output", "output/data_publication/simulation"
    ]
    print(f"Command: {' '.join(cmd_sim)}")
    try:
        subprocess.run(cmd_sim, cwd=str(project_root), check=True)
        print(">> Parametric simulation complete.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Parametric simulation failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    # 2. LLM Evaluation (N = 10 per category * 4 categories * 4 architectures = 160 total)
    # Note: Requires Ollama to be running
    print("\n[Part 2/2] LLM-Empirical Evaluation: N=~160 (sample-size=10)")
    cmd_llm = [
        sys.executable, str(runner_script),
        "--mode", "llm",
        "--sample-size", "10", 
        "--model", "gemma3:4b",
        "--seed", "42",
        "--output", "output/data_publication/llm"
    ]
    print(f"Command: {' '.join(cmd_llm)}")
    try:
        # Check if Ollama is likely available (simple check)
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        
        if result == 0:
            subprocess.run(cmd_llm, cwd=str(project_root), check=True)
            print(">> LLM evaluation complete.")
        else:
            print("WARNING: Ollama not detected on port 11434. Skipping LLM evaluation.")
            # We don't fail the build if Ollama is missing, just skip (optional but safer for CI)
            # However, user requested "ensure it runs", so maybe we should fail?
            # Let's fail if it's missing to be strict as requested.
            print("ERROR: Ollama is required for publication experiments.")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"ERROR: LLM evaluation failed with exit code {e.returncode}")
        # We don't exit immediately, let's allow the script to finish providing context
        # But we should exit with error code at the end
        sys.exit(e.returncode)
    except Exception as e:
        print(f"ERROR: Unexpected error in LLM evaluation: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("ALL PUBLICATION EXPERIMENTS COMPLETED SUCCESSFULLY")
    print("="*70)

if __name__ == "__main__":
    main()
