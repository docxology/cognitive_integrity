#!/usr/bin/env python3
"""What the pipeline costs, measured against a control that does not run it.

Four tables in this series report a defended-versus-undefended comparison:
an "Undefended Success Rate" column footnoted as *measured without any CIF
defense mechanisms active*, baseline-versus-CIF latency at p50/p95/p99, three
integrity-preservation ratios, and a cover panel reading ``Latency: +23%``.
None of them could ever have been computed, because **no undefended arm exists
anywhere in this project**. Every measurement runs the pipeline; nothing ran
the same corpus with the pipeline disabled.

This is that arm, for the half of it that is answerable here.

What it measures
----------------
Two passes over the same messages in the same process: a control that does the
framing work and no evaluation, and the full eight-module pipeline. The
difference is the cost of the defense, in milliseconds and in bytes, with the
distribution reported rather than the mean alone -- these are wall-clock
timings and a mean is what one scheduling hiccup moves.

Why there is no percentage
--------------------------
A percentage overhead needs a baseline workload to be a percentage *of*, and
this project models no agent: the control's per-message cost is the loop, not a
turn of work. Dividing by it produces a large number that means nothing, which
is where ``+23%`` and the ``45ms → 52ms`` row came from.

There is a real denominator, and it is measured: ``llm_demo_results.json``
records mean turn latencies of about 8.1 s and 10.0 s for the two architectures
that ran against a live model. Against a turn of that length the pipeline's
cost is reported here as a fraction, which is the only defensible version of
the claim those tables were reaching for.

    python3 scripts/run_overhead_control.py
    python3 scripts/run_overhead_control.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Callable, Sequence

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import create_full_pipeline  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "overhead_control.json"
LLM_ARTIFACT = REPO / "output" / "data" / "llm_demo_results.json"

#: Discarded before timing so import-time and first-call costs -- regex
#: compilation, lazy module construction -- do not land in the distribution.
WARMUP = 50


def _percentiles(samples: Sequence[float]) -> dict[str, float]:
    ordered = sorted(samples)
    n = len(ordered)

    def at(q: float) -> float:
        return ordered[min(n - 1, int(q * n))]

    middle = n // 2
    return {
        # Computed here rather than with the stdlib `statistics` module, which
        # this project shadows: `src/statistics/` is on the path under pytest,
        # so `import statistics` resolves to the package and `statistics.median`
        # raises AttributeError. The shadowing is a wider hazard than this file
        # and is worth knowing about; the arithmetic is two lines.
        "p50": (
            ordered[middle] if n % 2 else (ordered[middle - 1] + ordered[middle]) / 2
        ),
        "p95": at(0.95),
        "p99": at(0.99),
        "mean": sum(ordered) / n,
        "min": ordered[0],
        "max": ordered[-1],
        "n": n,
    }


def _measure(label: str, handle: Callable[[str], object], messages: Sequence[str]) -> dict:
    """Time one arm over *messages*, plus its peak allocation and throughput."""
    for message in messages[:WARMUP]:
        handle(message)

    tracemalloc.start()
    latencies: list[float] = []
    started = time.perf_counter()
    for message in messages:
        t0 = time.perf_counter()
        handle(message)
        latencies.append((time.perf_counter() - t0) * 1000.0)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "arm": label,
        "latency_ms": _percentiles(latencies),
        "throughput_msg_per_s": len(messages) / elapsed if elapsed > 0 else 0.0,
        "peak_traced_bytes": peak,
        "wall_clock_s": elapsed,
    }


def _llm_turn_seconds() -> dict[str, float]:
    """Measured agent turn latencies, the only honest denominator available."""
    if not LLM_ARTIFACT.is_file():
        return {}
    payload = json.loads(LLM_ARTIFACT.read_text(encoding="utf-8"))
    architectures = payload.get("phase2_architectures") or {}
    return {
        name: row["avg_latency_ms"] / 1000.0
        for name, row in architectures.items()
        if isinstance(row, dict) and row.get("avg_latency_ms")
    }


def build(seed: int = 42) -> dict[str, object]:
    attacks = [s.payload for s in AttackCorpus.generate(seed=seed)]
    benign = [b.text for b in BenignCorpus.generate()]
    messages = attacks + benign
    if len(messages) <= WARMUP:
        raise RuntimeError(
            f"only {len(messages)} messages, which is not more than the "
            f"{WARMUP}-message warmup; the timing would be all warmup"
        )

    pipeline = create_full_pipeline()

    # The control does what the defended arm does apart from the defense: it
    # touches the message so the loop is not optimised into nothing, and
    # returns. Anything less would time an empty loop; anything more would
    # smuggle work into the baseline and shrink the measured overhead.
    def control(message: str) -> object:
        return len(message)

    def defended(message: str) -> object:
        return pipeline.evaluate(message)

    control_arm = _measure("control", control, messages)
    defended_arm = _measure("full_pipeline", defended, messages)

    added_ms = defended_arm["latency_ms"]["p50"] - control_arm["latency_ms"]["p50"]
    added_bytes = defended_arm["peak_traced_bytes"] - control_arm["peak_traced_bytes"]

    turns = _llm_turn_seconds()
    against_turn = {
        name: (added_ms / 1000.0) / seconds
        for name, seconds in turns.items()
        if seconds > 0
    }

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_overhead_control.py",
        "seed": seed,
        "n_messages": len(messages),
        "n_attacks": len(attacks),
        "n_benign": len(benign),
        "warmup": WARMUP,
        "arms": {"control": control_arm, "full_pipeline": defended_arm},
        "added": {
            "median_latency_ms": added_ms,
            "peak_traced_bytes": added_bytes,
            "throughput_ratio": (
                defended_arm["throughput_msg_per_s"] / control_arm["throughput_msg_per_s"]
                if control_arm["throughput_msg_per_s"] > 0
                else None
            ),
        },
        "as_fraction_of_measured_agent_turn": against_turn,
        "note": (
            "No percentage overhead is reported against the control. The control "
            "is the loop, not a unit of agent work, so a ratio against it is a "
            "number without a referent -- which is what the retired '+23%' and "
            "'45ms -> 52ms' rows were. as_fraction_of_measured_agent_turn "
            "divides the added median latency by the measured mean turn time "
            "from llm_demo_results.json, which is a denominator that exists."
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
        # Timings are not reproducible to the digit; the shape and the sample
        # size are, and a stale run is one taken over a different corpus.
        if stored.get("n_messages") != fresh["n_messages"]:
            print("overhead control is stale: the corpus size has changed")
            return 1
        print("overhead control: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    for name, arm in fresh["arms"].items():
        lat = arm["latency_ms"]
        print(
            f"  {name:14s} p50 {lat['p50']:.4f} ms  p95 {lat['p95']:.4f}  "
            f"p99 {lat['p99']:.4f}  {arm['throughput_msg_per_s']:>10,.0f} msg/s  "
            f"peak {arm['peak_traced_bytes'] / 1024:,.0f} KiB"
        )
    added = fresh["added"]
    print(
        f"  added: {added['median_latency_ms']:.4f} ms/message, "
        f"{added['peak_traced_bytes'] / 1024:,.0f} KiB peak"
    )
    for name, fraction in fresh["as_fraction_of_measured_agent_turn"].items():
        print(f"    against a measured {name} turn: {fraction:.6%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
