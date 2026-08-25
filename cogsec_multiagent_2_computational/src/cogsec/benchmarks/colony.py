"""``python -m cogsec.benchmarks.colony --config colony_configs.yaml``.

S03's quickstart names this entry point. It did not exist, so the quickstart's
last line failed with ``No module named cogsec``. It exists now and does what
the surrounding text says it does: read a config file describing one or more
scenarios, run each, and print the Colony Cognitive Security score.

The config is a mapping of scenario name to the same config dict
:class:`~cogsec.benchmarks.ColonyBenchmark` takes::

    recruitment_poisoning:
      n_agents: 100
      adversary_class: omega_2
      duration_steps: 300
    sybil_infiltration:
      n_agents: 50

YAML is read with :mod:`yaml` when it is installed and JSON otherwise, so a
``.json`` config works in an environment without PyYAML rather than failing on
an import the paper never mentions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from cogsec.benchmarks import SCENARIOS, ColonyBenchmark


def load_config(path: Path) -> Dict[str, Any]:
    """Read a scenario config from YAML or JSON.

    Raises rather than defaulting to an empty config: running every scenario
    at built-in defaults when the caller asked for a specific file is the kind
    of helpfulness that produces a result attributed to the wrong experiment.
    """
    if not path.is_file():
        raise FileNotFoundError(f"config file {path} does not exist")
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - depends on the env
            raise ImportError(
                f"{path} is YAML but PyYAML is not installed; install it or "
                f"supply the same content as JSON"
            ) from exc
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{path} does not describe any scenario")
    unknown = sorted(set(payload) - set(SCENARIOS))
    if unknown:
        raise KeyError(f"unknown scenario(s) {unknown}; known scenarios are {list(SCENARIOS)}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="run each scenario across this many consecutive seeds; a single "
        "run of a stochastic simulation is one draw and should not be published",
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    print(f"{'scenario':26s} {'DR':>7s} {'FPR':>7s} {'resil':>7s} {'CCS':>7s}")
    for name, scenario_config in config.items():
        benchmark = ColonyBenchmark(name, scenario_config)
        runs = (
            [benchmark.run()]
            if args.repeats == 1
            else benchmark.run_repeated(args.repeats)
        )
        mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
        print(
            f"{name:26s} "
            f"{mean([r.detection_rate for r in runs]):7.3f} "
            f"{mean([r.false_positive_rate for r in runs]):7.3f} "
            f"{mean([r.resilience_score for r in runs]):7.3f} "
            f"{mean([benchmark.compute_ccs(result=r) for r in runs]):7.3f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
