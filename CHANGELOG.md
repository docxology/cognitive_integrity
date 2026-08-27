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
- **A gate over the conclusions** (`scripts/check_conclusion_numbers.py`). The
  ledger gates shared quantities and Part 2's registry binds its prose, but
  neither reaches a conclusion that restates a measurement in its own words, so
  six stale numbers survived every check. The gate reports an incomplete
  reference set as its own failure rather than as unbacked numbers in the paper.

### Changed

- Every number in the series is measured on the integrated 1,475-item attack
  corpus. The previous 950-item corpus reaches five of the eight defense modules.
- The consensus module is rewritten around five named consensus invariants and
  detects 81.1% of byzantine manipulation at a zero false-positive rate, having
  previously detected nothing anywhere.
- The multi-seed arm draws a stratified sample across every attack family rather
  than a prefix of the corpus.
- The bibliography is closed: every entry is cited, and the check gates on it.
- Part 3's cover figure was a stacked bar chart of a one-hot matrix, so every
  bar stood at exactly 1 and the quantitative axis carried nothing; the legend
  covered the per-pattern totals. It is now the categorical assignment it always
  was, and the generator refuses to draw a matrix that is not one-hot.
- Part 1's cover image was declared outside the `paper:` block the renderer
  reads, so the paper shipped with no cover figure at all.
- Three descriptions that restated measurements in prose no gate reads: two
  cover alt texts (one naming a retired 94% detection rate, one giving pattern
  counts of 3 and 2 where the matrix holds 4 and 1) and the detection-performance
  caption, which still described a placeholder artifact deleted two versions ago.

### Removed

- **A methodology section describing research that did not happen.** Part 2's
  corpus section reported eight security researchers over a four-week red-team
  exercise, human review of every generated attack, an inter-rater reliability
  of Cohen's kappa = 0.84, a sophistication-versus-success correlation, a
  detection-rate-by-attack-age table, a 90-day coordinated disclosure with four
  framework vendors and their patch versions, an IRB determination, and a tiered
  access process requiring an NDA. Its conclusion thanked the eight researchers
  and the anonymous reviewers, and its ethics statement repeated the IRB and
  disclosure claims. The corpus is one seeded call to five generator modules,
  the paper had never been submitted anywhere, and the corpus described as
  restricted is a pure function of a published seed. The section now describes
  the generator, the three mechanical guards that stand in for review, and why
  a restricted tier would be incoherent for a corpus anyone can regenerate.
  `scripts/check_unhappened_claims.py` gates the vocabulary of human process
  across all 85 manuscript files, with every legitimate use registered against a
  reason and fifteen tests driving the shipped sentences back through it.

- **Legacy narration, everywhere it had accumulated.** Part 1's framework figure
  still drew the invented quartet -- `Detection: 94%`, `FPR: 6%`,
  `Latency: +23%`, `Integrity: +127%` -- on a paper that measures nothing and
  has no artifact for a gate to check them against; the panel is gone and the
  figure says where the numbers live instead. Part 3 quoted 94% twice more, once
  as CrewAI "performing best" on trust exploitation where three architectures
  tie at 100%. Part 2's gap-closure roadmap projected marginal gains totalling
  +41 points against a baseline that had moved, and now states measured
  per-module capability with no projection at all. Sixteen code comments and
  docstrings narrated past defects in the first person; each is restated as
  present-tense rationale for the design it guards. Thirteen dated audit and
  round-numbered process documents are removed, along with every link to them.
  Three bibliography entries survived only because a deleted audit log named
  them, and now carry real citations.

- **A figure runner for Parts 1 and 3.** Neither had a
  `scripts/generate_all_figures.py`, so a caller that invoked one failed with a
  file-not-found and left every PNG stale. Both now have one that runs each
  numbered script, reports every failure rather than the first, and exits
  non-zero.

- **What a six-lens adversarial audit found on the eve of deposition.** Twenty-four
  confirmed defects, of which nine were blockers: a Bayesian supplement whose entire
  table rested on a detection count of 45/100 that exists in no seed of the artifact
  (the seeds run 82--90); a 72% semantic-reformulation rate from an experiment that
  was never run, paired with an 89% firewall figure the capability matrix contradicts
  at 31%; a +35--41 point adapter roadmap quoted in three places after the section
  that produced it had withdrawn it; model-checking verdicts reported as verified
  while `verification_summary.json` records all three checkers absent and
  `verified: false`; a five-step operator workflow for an interactive web application
  that does not exist in the repository; a normative "complete working example" that
  crashes with `AttributeError` because it composes two mechanisms the pipeline
  cannot call; and a firewall pseudocode documenting a three-stage weighted rule with
  a 384-dimensional sentence embedding and an IsolationForest stage against an
  implementation that is two detectors combined by `max`.

- Claims no experiment in this project could produce: an inter-annotator
  agreement statistic for a generated corpus, integrity-preservation ratios with
  no integrity metric behind them, per-architecture overhead profiles for an
  architecture-agnostic pipeline, and a message-volume saturation point measured
  by nothing.

[2.0.0]: https://github.com/docxology/cognitive_integrity/releases/tag/v2.0.0


## Unreleased-integration

- 2026-08-27 — Part 2 (cogsec_multiagent_2_computational): corrected the abstract's
  ablation claims (ΔTPR −0.000/0% → −0.650/73%, now matching
  `output/data/ablation_results.json` and Section 05d); the claim registry's two
  corresponding abstract claims now derive from the dominant ablation component
  instead of a hard-coded module name, so 171/171 claims still verify. Colony
  benchmark docs now record the actual 30-seed regeneration command. No shared
  quantity values changed; the series gates are unchanged in verdict.
