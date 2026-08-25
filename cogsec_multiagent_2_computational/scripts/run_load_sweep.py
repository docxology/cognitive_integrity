#!/usr/bin/env python3
"""Drive the pipeline at controlled arrival rates and find where it saturates.

Restores the measurement that ``tab:volume-scaling`` claimed. That table gave
detection rate, latency and CPU at five message rates and derived a saturation
point of ~5000 messages/sec; nothing had driven the pipeline at a rate, so all
fifteen cells were typed and the table was retracted.

The sweep runs the same corpus at each target rate in
:data:`TARGET_RATES`, releasing messages on a schedule rather than as fast as
the loop allows. Saturation is where the achieved rate stops tracking the
target, which the system decides rather than the author.

    python3 scripts/run_load_sweep.py
    python3 scripts/run_load_sweep.py --check
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import create_full_pipeline  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402
from evaluation.load_driver import find_saturation, sweep_rates  # noqa: E402

OUTPUT = REPO / "output" / "data" / "load_sweep.json"

#: Rates to try, spanning either side of the measured single-threaded ceiling
#: of roughly 1,800 messages/sec recorded in overhead_control.json.
TARGET_RATES = (100.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)

#: Messages per run. Small enough that six rates finish in seconds, large
#: enough that a p99 means something.
SAMPLE = 400


def build(seed: int = 42) -> dict[str, object]:
    attacks = [s.payload for s in AttackCorpus.generate(seed=seed)]
    benign = [b.text for b in BenignCorpus.generate()]
    messages = (attacks + benign)[:SAMPLE]
    pipeline = create_full_pipeline()

    def handle(message: str) -> bool:
        return bool(pipeline.evaluate(message).detected)

    points = sweep_rates(handle, messages, TARGET_RATES)
    saturation = find_saturation(points)

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_load_sweep.py",
        "seed": seed,
        "n_messages_per_run": len(messages),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "concurrency": "single process, single thread",
        "points": [
            {
                "target_msg_per_s": p.target_msg_per_s,
                "achieved_msg_per_s": p.achieved_msg_per_s,
                "keeping_up": p.keeping_up,
                "detection_rate": p.detection_rate,
                "latency_ms_p50": p.latency_ms_p50,
                "latency_ms_p95": p.latency_ms_p95,
                "latency_ms_p99": p.latency_ms_p99,
                "cpu_utilisation": p.cpu_utilisation,
                "cpu_seconds": p.cpu_seconds,
                "wall_seconds": p.wall_seconds,
            }
            for p in points
        ],
        "saturation_msg_per_s": saturation,
        "note": (
            "saturation_msg_per_s is null when the sweep kept up with every "
            "rate tried, which means it did not reach saturation rather than "
            "that there is none. CPU is reported as process CPU-seconds per "
            "wall-second rather than a percentage, because a percentage needs "
            "a sampling interval and a core count recorded beside it."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    fresh = build(args.seed)
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing {OUTPUT.relative_to(REPO)}", file=sys.stderr)
            return 1
        stored = json.loads(OUTPUT.read_text(encoding="utf-8"))
        stored_rates = [p["target_msg_per_s"] for p in stored.get("points", [])]
        if stored_rates != [p["target_msg_per_s"] for p in fresh["points"]]:
            print("load sweep is stale: the rate grid has changed")
            return 1
        print("load sweep: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    header = (
        f"  {'target':>8s} {'achieved':>10s} {'DR':>6s} "
        f"{'p50':>8s} {'p99':>8s} {'CPU':>6s}  keeping up"
    )
    print(header)
    for row in fresh["points"]:
        print(
            f"  {row['target_msg_per_s']:8.0f} {row['achieved_msg_per_s']:10.0f} "
            f"{row['detection_rate']:6.3f} {row['latency_ms_p50']:8.3f} "
            f"{row['latency_ms_p99']:8.3f} {row['cpu_utilisation']:6.2f}  "
            f"{'yes' if row['keeping_up'] else 'NO'}"
        )
    sat = fresh["saturation_msg_per_s"]
    print(
        f"  saturation: {sat:,.0f} msg/s"
        if sat
        else "  saturation: not reached at any rate tried"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
