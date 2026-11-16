# Changelog

All three papers in *Cognitive Security for Multiagent Operators* are versioned
together, because they share one measurement layer: Part 2 produces the
artifacts, and Parts 1 and 3 cite them. A change to a measurement can move a
number in any of the three, so a version that applied to one paper alone would
be a version of nothing.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project uses [semantic versioning](https://semver.org/spec/v2.0.0.html),
where a major version marks a change to a published number.

## Unreleased

### Corrected

- Implemented the fail-closed figure, explicit semantic backend, complete LLM matrix,
  fresh CI inventory, runtime-guide and TOML-parser source contracts (CI-001–CI-007).
  The CI matrix targets Python 3.11 and exact primary 3.15.2, with Ruff's floor
  aligned to Python 3.11 and mypy resolving the canonical `src.*` package.
- Part 1 now requires an explicit encoder and provides pinned, strictly offline
  `sentence-transformers==6.3.0` with MiniLM revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Actual trained-vector and consumer
  regressions passed offline. This is not deployment-efficacy qualification:
  both illustrative attack inputs still receive ACCEPT at unchanged defaults.
  Model directories and acquisition manifests remain operator-trusted inputs.
- LLM retries preserve prior diagnostic bytes in attempt archives; incomplete
  matrices and setup failures cannot publish success or overwrite prior final
  evidence. Result figures reject missing or malformed required inputs and
  visibly distinguish illustrative/model panels from measured inputs.
- Reconciled solo-firewall capability, score-sweep versus deployed-verdict
  operating points, and the Detection module's Sybil exception against retained
  artifacts. The fresh inventory records 5,279 collected tests across the series,
  including 3,667 in Part 2; collection totals are not pass counts.
- Independently requalified the two changed render-input fingerprints after a
  native fresh render reproduced all 26 historical PNG/PDF files byte-for-byte.
  Historical scientific inputs, artifact identities, renderer history and strict
  validation remain unchanged; the original input snapshot is retained in history.

- Reconciled Part 2's integrated and legacy attack-corpus descriptions against
  the shipped generator and retained experiment artifacts. The current corpus
  chapter reports five primary families, fifteen subcategories, 1,475 uniquely
  identified samples and 961 distinct payloads at seed 42; the historical
  architecture simulation retains its 950 × 4 denominator.
- Corrected difficulty and technique-level Ω summaries, distinguished the
  100-attack multi-seed samples from full-corpus measurements, and removed
  unsupported bounds on field performance. Released PDFs and deposits remain
  historical artifacts; these are corrections to current source.
- Extended corpus-summary regression checks and repaired their relocated
  manuscript paths.
- Repaired the relocated manuscript figure link and code-anchor links, and
  included the five missing PDF/PNG plots generated from existing measured
  artifacts. Existing publication figure files and deposited PDFs are preserved.

### Corrected (deep review, second pass)

- **Withdrew the executed-model-checking claim across all three papers.** Part 1's
  introduction listed "Model-checked safety properties" as a contribution and its
  formal-verification chapter pointed readers to an "executable run in Part 2 §S04"
  and "empirical verification results", while Part 2's conclusion and Part 3's
  applications introduction repeated "model-checked safety invariants". No model
  checker was ever run in this series. All three now describe formally specified
  invariants plus the model-checking *configurations*, and the tables read
  "specifications in Part 2 §S04, no run".
- **Regenerated the missing formal-verdict artifact** `output/formal/verification_summary.json`
  via `scripts/verify_formal_specs.py` (NuSMV=SKIP, SPIN=SKIP, TLA+=SKIP,
  `verified: false`). Three manuscript citations pointed at a file no run had
  produced.
- **Corrected the multi-seed arm's description and stability verdict.** The prose
  claimed each seed scored "the first 100 entries ... all of which are
  direct-injection items"; the artifact records a stratified 100-attack sample
  across all five families. The summary table claimed "Stability (CV < 0.05):
  Achieved" while `multi_seed_results.json` records `stable: false` (per-category
  CVs 0.094 and 0.085 exceed the threshold). The stale "range of 0.37--0.56" and
  "±10 percentage points" became the measured 0.82--0.90 (8 points), and an
  editorial note about the correction itself was removed from the caption.
- **Corrected the ablation TPR in Part 2's conclusion** from "~12%" to the measured
  "~89.0%", and the power-summary table's stale estimated rates (multi-seed
  0.45 → 0.863, ablation 0.12 → 0.89) with `N*` recomputed through
  `power_analysis_beta_binomial` (380 → 185, 165 → 150). The "12%--100%"
  evaluation-mode range is now the measured 74.3%--100%.
- **Withdrew an unbacked Bayes-factor comparison** ("parametric 92/100 vs multi-seed
  45/100"): neither count exists in any artifact, and the two arms are not measured
  on the same corpus or denominator.
- **Corrected five mathematical defects in Part 1.** The correlated-composition
  formula had the covariance sign inverted (now `-\sum Cov`, with a second-order
  caveat for >2 detectors); the redundancy-resilience theorem asserted a false
  `min(a,b) = a·b` identity and an "if and only if" the proof does not establish
  (now `min` and "only if"); the OODA latency property claimed 141 ms sufficed for
  any ε ∈ (0,0.1) (now the derived 136 ms stack with the ε-dependent cycle
  requirement); the belief-sandbox remark defined an effective attack by `ΔF > κ`
  while displaying `ΔF ≤ κ` (now rejection on `>` and effectiveness on `≤`); and
  the KL–AUC "coupling" claimed a universal lower bound that does not exist (now
  the correct optimal-detector identity plus the Pinsker *upper* bound, with the
  table column relabelled "AUC ceiling").
- **Downgraded the defense-composition algebra from "bounded distributive lattice"
  to a meet-semilattice with identity.** On the shared accept predicate both
  operators are conjunction, so absorption fails and no lattice exists. The
  stealth-impact "tight bound" π/2 is now stated as the constant of the reciprocal
  definitions (product = 1), not a geometric theorem; the curvature claim that
  supported it is corrected (radius-2 sphere, curvature 1/4, independent of
  concentration). The path-trust base case is reconciled with its own definition
  (decay factor included), and the AUC confidence-interval formula now uses the
  correct DeLong normalization $1/(n(n-1))$ with the placement values defined.
- **Fixed the gates that missed these.** `check_conclusion_numbers.py` matched only
  decimal percentages, so the integer "12%" escaped; it now also handles integers
  while excluding confidence levels ("95% CI/HDI") and forward-looking targets.
  `check_series_integrity.py --only artifact-provenance` only saw `output/data/`
  paths, so the dangling `output/formal/...` citation passed; a second pass now
  resolves backtick-quoted `output/**` paths across all three parts.
- **Narrowed `.gitignore`.** `**/output/` silently dropped every newly generated
  artifact from `git add` while the gates derive every published number from that
  tree. Only regenerable bulk (`.checkpoints/`, `output/web/`,
  `figure-portability/`, LaTeX byproducts) is ignored now.
- **Refreshed the reviewed figure snapshot.** `figure_publication_snapshot.json`
  still carried the pre-`2e26473` hashes of `pyproject.toml` and `uv.lock`, so the
  three historical-fidelity tests failed against the committed dependency floor.
- **Corrected a false CI comment.** The "Test inventory is current" step claimed a
  commit adding tests without refreshing the inventory "fails here"; it only checks
  that the tracked JSON parses and sums correctly. The step is renamed and the
  limitation is stated.

### Corrected (deep review, third pass)

- **Removed an invalid probabilistic-independence proof and narrowed detection
  claims.** Part 1 no longer infers independent firewall and sandbox failure events
  from disjoint feature sets; independence is an explicit architectural assumption
  with a union-bound relaxation. The KL–AUC passage now distinguishes ranking AUC,
  total variation and equal-prior Bayes error, and the CUSUM discussion identifies
  which ARL approximation is a heuristic rather than a calibrated guarantee.
- **Regenerated the measured evidence and synchronized all three manuscripts.** The
  live 100-attack ablation records Invariants ΔTPR −0.670, Tripwire ΔTPR −0.010 and
  a 75.3% dominant share; the measured CIF ROC AUC is 0.902. The separate detector
  AUCs are 0.917 (Invariants), 0.918 (equal-weight ensemble), 0.384 (Firewall) and
  0.373 (drift). The trust adapter fires on no corpus item at the shipped 0.5
  threshold, so its zero Shapley value is reported as a capability limitation rather
  than hidden as masking or described as a measured detection success.
- **Repaired implementation and boundary defects found by the review.** These include
  scalar-Bernoulli KL drift in Part 1, fail-closed empty practical checklists and
  posture assessment, LLM-fallback results being reported as successful LLM runs,
  Youden optimization missing observed score cutpoints, strict Hasse covers between
  equal-rate nodes and dropped tied immediate successors, TLA+ configuration
  validation taking precedence over tool
  discovery, and empty latency means returning 0 instead of NaN. Package-migration
  fallout in LLM test adapters, provenance shims and logging was corrected at the
  canonical `src.*` boundary.
- **Strengthened the evidence gates instead of suppressing their findings.** The
  claim registry and series ledger now bind the current prose, including the
  integrated red-team corpus, distinct ablation/capability denominators and explicit
  arithmetic gap statements. The truncation gate recognizes Python comments inside
  `lstlisting`; missing bibliography citations and the dangling FEP label were
  restored. Figures, tables, the full 256-coalition taxonomy, the module-capability
  matrix and the reviewed render snapshot were regenerated from current code and
  artifacts, and the collected series inventory is now 5,175 tests.

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
