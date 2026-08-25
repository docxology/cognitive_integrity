"""The public API the supplements document.

S03 documents ``from cogsec.benchmarks import ColonyBenchmark`` and
``from cogsec.testing import CIFTestSuite``, and carried a note conceding that
neither import worked: "the import path shown above reflects the proposed
public API". A note saying a code block does not run is more honest than
silence and still leaves the reader with a code block that does not run.

This package is that API, implemented rather than proposed. It is a facade:
every entry point delegates to the internal modules under ``src/`` and adds no
behaviour of its own. Two names for one thing is a cost, and the reason to pay
it here is that the internal layout is organised for the framework's own
development while the documented surface is organised for someone reproducing
the paper, and those are genuinely different audiences.

Where the internal signature and the documented one disagreed, the documented
one won, because it is the one in print.
"""

from __future__ import annotations

__all__ = ["benchmarks", "testing"]
