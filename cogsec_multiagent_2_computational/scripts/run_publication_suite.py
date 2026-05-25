#!/usr/bin/env python3
"""Run full-scale publication experiments.

This script automates the execution of the two major evaluation modes required
for the manuscript:
1. Parametric Simulation: replicates of the 950-sample corpus.
2. LLM-Empirical Evaluation: sample_size × 4 categories × 4 architectures.

Configuration is read from experiment_config.toml (single source of truth).
Pass --publication to use publication-scale parameters instead of iteration defaults.

It is discovered and executed automatically by the analysis pipeline.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def load_config(project_root: Path, publication: bool = False) -> dict:
    """Load experiment_config.toml and return resolved parameters."""
    config_path = project_root / "experiment_config.toml"
    if config_path.exists() and tomllib is not None:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
        if publication:
            section = raw.get("publication", {})
        else:
            section = raw.get("llm", {})
        return {
            "sample_size": section.get("sample_size", 5),
            "replicates": raw.get("publication" if publication else "simulation", {}).get("replicates", 1),
            "model": raw.get("llm", {}).get("model", "gemma3:4b"),
            "seed": raw.get("simulation", {}).get("seed", 42),
        }
    # Fallback defaults if no config file
    return {"sample_size": 5, "replicates": 1, "model": "gemma3:4b", "seed": 42}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CIF experiments (reads experiment_config.toml)")
    parser.add_argument("--publication", action="store_true",
                        help="Use publication-scale parameters (replicates=11, sample_size=10)")
    parser.add_argument("--sample-size", type=int, default=None,
                        help="Override sample_size from config")
    parser.add_argument("--replicates", type=int, default=None,
                        help="Override replicates from config")
    parser.add_argument("--run-llm", action="store_true",
                        help="Run live Ollama LLM evaluation (also enabled by COGSEC_RUN_LLM_ANALYSIS=1)")
    args = parser.parse_args()

    # Resolve paths
    current_script = Path(__file__).resolve()
    project_root = current_script.parent.parent
    scripts_dir = current_script.parent
    runner_script = scripts_dir / "run_full_evaluation.py"

    # Load config
    cfg = load_config(project_root, publication=args.publication)
    sample_size = args.sample_size if args.sample_size is not None else cfg["sample_size"]
    replicates = args.replicates if args.replicates is not None else cfg["replicates"]
    model = cfg["model"]
    seed = str(cfg["seed"])

    mode_label = "PUBLICATION" if args.publication else "ITERATION"
    print("=" * 70)
    print(f"     RUNNING {mode_label} EXPERIMENTS")
    print(f"     sample_size={sample_size}  replicates={replicates}  model={model}")
    print("=" * 70)
    
    # 1. Parametric Simulation
    print(f"\n[Part 1/2] Parametric Simulation: {replicates} replicate(s)")
    cmd_sim = [
        sys.executable, str(runner_script),
        "--mode", "simulation",
        "--replicates", str(replicates),
        "--seed", seed,
        "--output", "output/data_publication/simulation"
    ]
    print(f"Command: {' '.join(cmd_sim)}")
    try:
        subprocess.run(cmd_sim, cwd=str(project_root), check=True)
        print(">> Parametric simulation complete.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Parametric simulation failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    # 2. LLM Evaluation (opt-in; live Ollama calls are too slow for default renders)
    total_calls = sample_size * 4 * 4  # 4 categories × 4 architectures
    print(f"\n[Part 2/2] LLM-Empirical Evaluation: N=~{total_calls} (sample-size={sample_size})")
    cmd_llm = [
        sys.executable, str(runner_script),
        "--mode", "llm",
        "--sample-size", str(sample_size), 
        "--model", model,
        "--seed", seed,
        "--output", "output/data_publication/llm"
    ]
    print(f"Command: {' '.join(cmd_llm)}")

    if not args.run_llm and os.environ.get("COGSEC_RUN_LLM_ANALYSIS") != "1":
        print("WARNING: LLM evaluation skipped. Set COGSEC_RUN_LLM_ANALYSIS=1 or pass --run-llm to run real Ollama evaluation.")
        print("WARNING: Parametric simulation complete; LLM publication data remains opt-in.")
        sys.exit(0)

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
            print("WARNING: Ollama not available — LLM evaluation skipped. Parametric results are still valid.")
            sys.exit(0)
            
    except subprocess.CalledProcessError as e:
        print(f"ERROR: LLM evaluation failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"ERROR: Unexpected error in LLM evaluation: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("ALL EXPERIMENTS COMPLETED SUCCESSFULLY")
    print("="*70)

if __name__ == "__main__":
    main()

