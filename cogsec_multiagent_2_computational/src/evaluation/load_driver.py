"""Drive the pipeline at a target arrival rate and record what happens.

Part 2's supplement reported detection rate, latency and CPU usage at five
message rates and derived a saturation point of ~5000 messages/sec from them.
Nothing had ever driven the pipeline at a controlled rate: there was no pacer,
no CPU sampler and no notion of arrival at all, so all fifteen cells and the
conclusion were typed. The table was retracted; this is the thing that makes it
answerable.

What a rate means here
----------------------
Messages are released on a schedule rather than as fast as the loop can run.
Each message has a due time; if the pipeline is keeping up, the driver waits
for it, and if it is not, the message goes late and the *achieved* rate falls
below the target. Saturation is where those two diverge, which is a property of
the system rather than a threshold someone picked.

CPU is sampled with :func:`resource.getrusage`, so it is process CPU-seconds
consumed over the run rather than an instantaneous percentage. A percentage
would need a sampling interval and a core count to be meaningful, and both
would have to be recorded beside it; utilisation as a ratio of CPU time to wall
time says the same thing without the ambiguity.

Single process, single thread. The framework offers no concurrency, so
reporting a rate as though it scaled across cores would be a claim about code
that does not exist.
"""

from __future__ import annotations

import resource
import time
from dataclasses import dataclass
from typing import Callable, Sequence

__all__ = ["LoadPoint", "drive_at_rate", "sweep_rates", "find_saturation"]


@dataclass(frozen=True)
class LoadPoint:
    """One target rate and what the system did with it."""

    target_msg_per_s: float
    achieved_msg_per_s: float
    n_messages: int
    detected: int
    latency_ms_p50: float
    latency_ms_p95: float
    latency_ms_p99: float
    cpu_seconds: float
    wall_seconds: float

    @property
    def detection_rate(self) -> float:
        return self.detected / self.n_messages if self.n_messages else 0.0

    @property
    def cpu_utilisation(self) -> float:
        """Process CPU-seconds per wall-second. Above 1.0 needs threads."""
        return self.cpu_seconds / self.wall_seconds if self.wall_seconds > 0 else 0.0

    @property
    def keeping_up(self) -> bool:
        """Within 5% of the target. Below that the queue is growing."""
        return self.achieved_msg_per_s >= 0.95 * self.target_msg_per_s


def _percentile(ordered: Sequence[float], q: float) -> float:
    if not ordered:
        return 0.0
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def drive_at_rate(
    handle: Callable[[str], bool],
    messages: Sequence[str],
    target_msg_per_s: float,
) -> LoadPoint:
    """Feed *messages* to *handle* on a schedule and measure the result.

    ``handle`` returns whether the message was flagged, so the detection rate
    under load is measured rather than assumed constant -- the retracted table
    claimed detection fell as rate rose, which is the sort of claim that needs
    a measurement precisely because it is plausible.
    """
    if target_msg_per_s <= 0:
        raise ValueError(f"target rate must be positive, got {target_msg_per_s}")
    if not messages:
        raise ValueError("no messages to drive")

    interval = 1.0 / target_msg_per_s
    latencies: list[float] = []
    detected = 0

    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    started = time.perf_counter()
    for index, message in enumerate(messages):
        due = started + index * interval
        now = time.perf_counter()
        if now < due:
            time.sleep(due - now)
        t0 = time.perf_counter()
        if handle(message):
            detected += 1
        latencies.append((time.perf_counter() - t0) * 1000.0)
    wall = time.perf_counter() - started
    cpu_after = resource.getrusage(resource.RUSAGE_SELF)

    cpu = (cpu_after.ru_utime - cpu_before.ru_utime) + (
        cpu_after.ru_stime - cpu_before.ru_stime
    )
    ordered = sorted(latencies)
    middle = len(ordered) // 2
    return LoadPoint(
        target_msg_per_s=target_msg_per_s,
        achieved_msg_per_s=len(messages) / wall if wall > 0 else 0.0,
        n_messages=len(messages),
        detected=detected,
        latency_ms_p50=(
            ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
        ),
        latency_ms_p95=_percentile(ordered, 0.95),
        latency_ms_p99=_percentile(ordered, 0.99),
        cpu_seconds=cpu,
        wall_seconds=wall,
    )


def sweep_rates(
    handle: Callable[[str], bool],
    messages: Sequence[str],
    targets: Sequence[float],
) -> list[LoadPoint]:
    """Drive at each target rate in turn, lowest first."""
    return [drive_at_rate(handle, messages, target) for target in sorted(targets)]


def find_saturation(points: Sequence[LoadPoint]) -> float | None:
    """The highest target rate the system still kept up with.

    ``None`` when it kept up with every rate tried, which means the sweep did
    not reach saturation rather than that there is none. Reporting a saturation
    point from a sweep that never saturated is how ~5000 msg/sec got published.
    """
    kept = [p.target_msg_per_s for p in points if p.keeping_up]
    if not kept or len(kept) == len(points):
        return None
    return max(kept)
