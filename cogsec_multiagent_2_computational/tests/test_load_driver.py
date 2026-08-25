"""Tests for the rate-controlled load driver.

The table this replaces derived a saturation point from cells nobody measured.
The risk in replacing it is the mirror image: a driver that reports saturation
because its own pacing is wrong, or that reports none because it never pushed
hard enough. These tests are mostly about the pacing being real and the
saturation verdict being the system's rather than the author's.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from evaluation.load_driver import LoadPoint, drive_at_rate, find_saturation, sweep_rates

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = REPO / "output" / "data" / "load_sweep.json"

MESSAGES = [f"message {i}" for i in range(40)]


def _point(target: float, achieved: float) -> LoadPoint:
    return LoadPoint(
        target_msg_per_s=target,
        achieved_msg_per_s=achieved,
        n_messages=10,
        detected=5,
        latency_ms_p50=1.0,
        latency_ms_p95=2.0,
        latency_ms_p99=3.0,
        cpu_seconds=0.1,
        wall_seconds=1.0,
    )


class TestThePacing:
    def test_a_slow_rate_is_actually_paced(self):
        """The driver must wait, or every rate is 'achieved' trivially.

        A pacer that does not sleep reports the loop's own speed at every
        target and never saturates, which looks like a system with no ceiling.
        """
        started = time.perf_counter()
        point = drive_at_rate(lambda _m: False, MESSAGES[:10], target_msg_per_s=50.0)
        elapsed = time.perf_counter() - started
        assert elapsed >= 0.9 * (9 / 50.0), "the driver did not pace"
        assert point.achieved_msg_per_s <= 60.0

    def test_a_rate_the_system_cannot_meet_is_reported_as_missed(self):
        """Handle slower than the interval must show achieved below target."""

        def slow(_message: str) -> bool:
            time.sleep(0.002)
            return False

        point = drive_at_rate(slow, MESSAGES[:20], target_msg_per_s=5000.0)
        assert not point.keeping_up
        assert point.achieved_msg_per_s < 5000.0

    def test_detection_is_counted_not_assumed(self):
        point = drive_at_rate(lambda m: m.endswith("1"), MESSAGES[:20], 500.0)
        assert point.detected == sum(1 for m in MESSAGES[:20] if m.endswith("1"))
        assert point.detection_rate == pytest.approx(point.detected / 20)

    def test_a_nonpositive_rate_raises(self):
        with pytest.raises(ValueError, match="positive"):
            drive_at_rate(lambda _m: False, MESSAGES, 0.0)

    def test_no_messages_raises(self):
        with pytest.raises(ValueError, match="no messages"):
            drive_at_rate(lambda _m: False, [], 100.0)

    def test_the_sweep_runs_lowest_rate_first(self):
        points = sweep_rates(lambda _m: False, MESSAGES[:5], [500.0, 100.0, 250.0])
        assert [p.target_msg_per_s for p in points] == [100.0, 250.0, 500.0]


class TestTheSaturationVerdict:
    def test_keeping_up_with_everything_reports_no_saturation(self):
        """Not a saturation point. The sweep did not reach one.

        Reporting a ceiling from a sweep that never saturated is how
        ~5000 msg/sec got published.
        """
        points = [_point(t, t) for t in (100.0, 500.0, 1000.0)]
        assert find_saturation(points) is None

    def test_the_highest_sustained_rate_is_the_saturation_point(self):
        points = [_point(100.0, 100.0), _point(500.0, 500.0), _point(1000.0, 700.0)]
        assert find_saturation(points) == 500.0

    def test_keeping_up_allows_five_percent_of_slack(self):
        assert _point(1000.0, 960.0).keeping_up
        assert not _point(1000.0, 900.0).keeping_up


class TestTheShippedSweep:
    @pytest.fixture(scope="class")
    def payload(self) -> dict:
        assert ARTIFACT.is_file(), "run scripts/run_load_sweep.py first"
        return json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_the_sweep_reached_saturation(self, payload):
        """Otherwise the table above it cannot name a ceiling."""
        assert payload["saturation_msg_per_s"] is not None, (
            "the sweep kept up with every rate tried, so it has no saturation "
            "point to report; raise the top of TARGET_RATES"
        )

    def test_detection_does_not_vary_with_arrival_rate(self, payload):
        """The retracted table claimed it fell from 0.94 to 0.89 under load.

        Nothing in this pipeline carries state between messages, so there is no
        mechanism by which arrival rate could change a verdict. If this ever
        fails, either a module has grown state or the driver is dropping
        messages, and both matter more than the number.
        """
        rates = {round(p["detection_rate"], 6) for p in payload["points"]}
        assert len(rates) == 1, (
            f"detection varies with arrival rate ({sorted(rates)}), which a "
            f"stateless pipeline cannot do"
        )

    def test_cpu_is_reported_as_a_ratio_not_a_percentage(self, payload):
        for point in payload["points"]:
            assert "cpu_utilisation" in point
            assert 0.0 <= point["cpu_utilisation"] <= 2.0
            assert "cpu_percent" not in point
