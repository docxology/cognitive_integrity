# Changelog

All three papers in *Cognitive Security for Multiagent Operators* are versioned
together, because they share one measurement layer: Part 2 produces the
artifacts, and Parts 1 and 3 cite them. A change to a measurement can move a
number in any of the three, so a version that applied to one paper alone would
be a version of nothing.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project uses [semantic versioning](https://semver.org/spec/v2.0.0.html),
where a major version marks a change to a published number.

## [2.0.0] — 2026-08-26

Part 1 second edition; Parts 2 and 3 first publication.

### Added

- **An undefended control arm** (`scripts/run_overhead_control.py`). Four tables
  reported a defended-versus-undefended comparison and no such arm existed. The
  defense costs +0.610 ms at the median and +32 KiB peak, which is 0.0075% of a
  measured agent turn.
- **A rate-controlled load driver** (`src/evaluation/load_driver.py`). Saturation
  at 2,000 messages/sec; detection is flat at 0.930 across every rate, because
  nothing in the pipeline carries state between messages.
- **False-positive mitigations as implementations** rather than a table
  (`src/composition/mitigations.py`). Two strategies take the false-positive rate
  from 0.183 to zero for 1.7 points of true positives.
- **A firewall threshold sweep** (`src/evaluation/threshold_sweep.py`), which
  finds τ₂ flat from 0.25 to 0.75.
- **Two stratification dimensions on the corpus**, `omega_level` and `target`,
  so results can be grouped by what an attack aims at.
- **A per-module capability matrix**, separating what a defense detects from what
  it adds to a pipeline that already contains the others.
- **Five figures** for the five new measurements, and a shared loader
  (`src/visualization/artifact.py`) that fails closed and prints each figure's
  artifact and origin on the page.
- **The public API the supplements document**: `src/core/base.py` and
  `src/cogsec/`, with a gate that executes every import written in any manuscript.

### Changed

- Every number in the series is measured on the integrated 1,475-item attack
  corpus. The previous 950-item corpus reaches five of the eight defense modules.
- The consensus module is rewritten around five named consensus invariants and
  detects 81.1% of byzantine manipulation at a zero false-positive rate, having
  previously detected nothing anywhere.
- The multi-seed arm draws a stratified sample across every attack family rather
  than a prefix of the corpus.
- The bibliography is closed: every entry is cited, and the check gates on it.

### Removed

- Claims no experiment in this project could produce: an inter-annotator
  agreement statistic for a generated corpus, integrity-preservation ratios with
  no integrity metric behind them, per-architecture overhead profiles for an
  architecture-agnostic pipeline, and a message-volume saturation point measured
  by nothing.

[2.0.0]: https://github.com/docxology/cognitive_integrity/releases/tag/v2.0.0
