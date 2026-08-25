# Cognitive Integrity Program - Per-Paper TODO Deep Scoping

**Date:** 2026-07-06 (original) / **Last reviewed:** 2026-08-23
**Owner:** Daniel Ari Friedman
**Status:** Every gate in this repository used to be scoped to a single part, which made
cross-paper drift structurally invisible. A program-level gate now exists
(`scripts/check_series_integrity.py`, wired into CI) with six gating checks ---
shared-quantities, bibliography, truncation, math-hygiene, artifact-provenance and
cross-paper-pointers --- and a matching write path (`scripts/inject_series_values.py`)
that rewrites every shared number from its artifact. Both read one ledger
(`scripts/series_ledger.py`), because two mechanisms with separate ideas of where a
number lives is the defect class the whole apparatus exists to catch. Each check was
written because a real defect had already passed through the space it now covers, and
each is mutation-tested, because a gate that cannot fail is worse than no gate.
**Auditor:** seven-lens review with adversarial verification of every finding; 113 of 114
findings survived verification, 44 at HIGH
**Scope:** All three papers in `cognitive_integrity/` (Part 1 theory, Part 2 computational, Part 3+4 practical)
**Status legend:** `DONE` verified at HEAD | `OPEN` tracked forward | `PARTIAL` partially addressed | `[A]` author decision | `[H]` agent-scoped work | `[H+A]` both

---

## Executive Summary - measured 2026-08-25 (Round 12)

| Paper | Tests | Manuscript verifier | Notes |
|-------|-------|---------------------|-------|
| 1 | 442 passed / 0 skipped | PASS | |
| 2 | 3422 passed / 3 skipped | claim registry 171/171, zero unreconciled | |
| 3 | 935 passed / 0 skipped | PASS | |
| series | 69 passed (`tests/test_series_integrity.py`) | gate PASS (6/6) | |

Every number in all three papers is now measured on the integrated 1,475-item attack
corpus. The claim registry has a write path (`scripts/sync_claims.py`), so its
`KNOWN_UNRECONCILED` set is empty rather than 28 entries deep, and the bibliography check
gates rather than counts.

---

## Completed / Closed

### Round 10 (2026-08-22) — cross-paper pass

The organising finding: **every gate was per-part.** Each paper ran its own tests and its
own `verify_manuscript.py`, and Part 2 ran its claim registry over its own manuscript only.
No gate compared the three papers to each other, so a quantity could be published as two
different numbers in two papers that cite each other and stay green for nine rounds.

| ID | Sev | Issue | Status |
|----|-----|-------|--------|
| R10-BIB-FAB | HIGH | Seven bibliography entries carried arXiv IDs belonging to unrelated papers (astronomy, nuclear theory, general relativity, federated learning). Verified individually against arxiv.org. | DONE — repaired to the real source where one exists (EchoLeak → CVE-2025-32711 advisory; TopicAttack → arXiv:2507.13686; PromptPwnd → Trail of Bits argument-injection disclosure; Prompt Infection → arXiv:2410.07283; Zero-Trust → NIST SP 800-207), deleted where none does |
| R10-BIB-AUTH | HIGH | Fourteen entries for real papers carried invented author lists; three propagated into Part 2's related-work prose as wrong attributions. | DONE — all corrected against the primary record |
| R10-BIB-DUP | MED | Four duplicate works under two bibkeys (P1 carlini, P2 goodfellow, P3 owasp, P3 cpwbft/zheng); `friston2022free` resolved to two different papers in P2 vs P3. | DONE — duplicates removed, key collision split |
| R10-CEIL | HIGH | The parametric ceiling was published as 94--100% in 26 places and 96--100% in the rest. The artifact's minimum cell is 0.96 and `tests/test_manuscript_claims.py` already asserted ≥0.96. | DONE — 96--100% everywhere; derived gap 49--88 → 51--88 |
| R10-ARCH | HIGH | Part 1's Discussion claimed six architectures and named peer-to-peer; Part 2 evaluates four. | DONE |
| R10-MEAN | HIGH | Part 1 carried 44.7% [43.4, 46.2] for Part 2's multi-seed mean of 44.8% [43.2, 46.4]. | DONE |
| R10-OMEGA | HIGH | Ω₁–Ω₅ names two different ladders: Part 1's access-based classes and Part 2's technique ladder (`redteam/generator.py::OmegaLevel`), with Part 2 attributing its own ladder to "Part 1 Definition 4". They do not correspond by index. | PARTIAL — false attribution removed and the two ladders disambiguated in Part 2 §3; figure caption restored to Part 1's classes (the figure code was already correct). **Author decision below.** |
| R10-05G | HIGH | Part 2 §5g ended mid-sentence on a dangling heading; the per-Ω table it once held was deleted as a design model, and Part 1 still cited its numbers (97%…49%). | DONE — section closed honestly, Part 1's citation of the retracted numbers removed |
| R10-EMERG | HIGH | Part 3 headlined 56.1% / 46.6% FPR for emergent misalignment, which Part 2 retracts in three places (real: 74.3% / 25.5%). Part 3 also narrowed Part 2's 95% HDI from [35.5, 54.7] to [41.3, 48.3]. | DONE |
| R10-SEMI | HIGH | Part 1's supplement proved a "closed semiring" its own body says is not constructed; the type-closure proof used an outcome outside its stated codomain and the distributivity gloss was wrong. | DONE — restated as the bounded distributive lattice the proof establishes |
| R10-CT | HIGH | S04 labelled CT.1/CT.2/CT.3 as left identity / right identity / associativity, contradicting the same file's intro and the CT.1–CT.3 defined in §01c/§02c. | DONE |
| R10-PTR | MED | 73 hardcoded cross-paper pointers ("Part 1, Theorem 3.2a", "Paper 1, Def. 5.5"). Part 3's 22 numbered definition pointers each named a different definition than their sentence, and 5.5 was used for two defenses. Part 2's audited as mostly correct. | PARTIAL — Part 3's converted to named references; "Theorem 3.2a" (names nothing in Part 1) repointed; Part 2's 44 remain, gated advisory |
| R10-TESTS | MED | Test counts hardcoded in Part 3's abstract and introduction (3,308) and in Part 2's `SKILL.md` (3338). | DONE — 3,369. Still hand-maintained; see backlog |


### Round 9 (2026-08-16) — this pass
| ID | Sev | Issue | Status |
|----|-----|-------|--------|
| R9-BFT-N | MED | `ByzantineConsensus` accepted n<=0 because default f=(n-1)//3 is negative and n>=3f+1 still held | DONE — both cores reject n<1 and f<0 |
| R9-P1-Q | MED | Part 1 `QuorumVerification` lacked the Part 2 n_agents/f guards (P2-39 sibling) | DONE — same guards + tests |
| R9-TM | MED | `TrustMatrix(n_agents=0)` built an empty array | DONE — both cores reject n<1 |
| R9-DEL | MED | `delegate_trust` / `compute_path_trust` accepted NaN, out-of-range edges, and negative depth | DONE — unit-interval + depth>=0 (d=0 is identity, used by decay figures) |
| R9-P3-TBL | MIN | Part 3 README series table dropped its own row after the Documentation heading | DONE — row restored in the table |
| P2-F11 | MED | stability writer labeled one pipeline as Claude Code | DONE earlier (Round 7b): `per_architecture={}` with explicit comment |

### Round 8 (2026-08-16)
R8-P1-M3, R8-P3-R7, R8-P3-DUP, R8-P3-NP, R8-P3-FLT, R8-P2-CV, R8-TRUST, R8-CI. See prior commit b218a19.

### Prior rounds
Paper 1 P1-1..P1-22, H7, Round 6/7 math/pandoc/labels.
Paper 2 P2-1..P2-4/6..20/22..38, P2-F1..F4/F5a/F6/F8..F16, LOW-3, L2, P2-39, Round 7b.
Paper 3 P3-1..P3-3, P3-M1..M5, P3-m6..m11.
Program: CITATION.cff schema-valid.

---

## Round 11 (2026-08-23) — triple-check, auto-injection, gate mutation testing

A second seven-lens review, this one adversarially re-verifying Round 10's own fixes and
mutation-testing the gates it added. 89 of 96 findings survived verification, 34 at HIGH.
Most of what it found in the gates was self-inflicted, which is the point of running it.

**Auto-injection now exists for the whole series.** `scripts/series_ledger.py` derives 32
variables from the artifacts (nothing stored), `scripts/inject_series_values.py` writes them
back, and `scripts/collect_test_inventory.py` derives the test count that had gone stale
three times. Gated prose sites went from 95 to 175. Two variables derive structurally rather
than from a field: the domain count from Part 3's section files, and the ablation denominator
from the measurement resolution.

**Gates that could not fail, all fixed:** `parametric_ceiling_high` captured a literal 100;
`truncation` read only a file's last line; the proof-status test-of-the-test never invoked
the audit; the proof-detection window reached into the *next* theorem's proof; seven cited
artifacts were untracked so the gate was red on any clean clone; the provenance check
accepted an empty sidecar and missed bare-filename citations.

### Still open

| ID | What is left |
|----|--------------|
| S08 six-way tables | Resolved by disclosure, not measurement. Regenerating them needs a real six-way run; retiring them means dropping to the artifact's four categories. Author call. |
| P2AI-06..08 | PARTIAL. The registry now has a write path and zero unreconciled claims, but the injector still writes 15 labels no registry claim inspects, and 05e's Bayesian numbers still have no artifact to pin against. |
| N9, N10 | Symbol overloading across the three papers. |
| ~~BIB-11~~ | CLOSED in Round 12. Pruned to the cited set (349 entries to 207, uncited 153 to 4, the survivors named in a README or an audit note), and the advisory is now a gating check. |
| H1--H3, H5 | The author-math backlog, carried forward. |

### Closed since

- **R11-02** --- S06's integration example is rewritten against the shipped API and is
  now executed as a test (`test_manuscript_code_examples.py`), so it cannot drift from
  the code again without failing the suite.
- **R11-03 / R11-04** --- `FirewallConfig.injection_threshold` has been 0.8 since the
  fork with Part 1; five sites across Parts 2 and 3 published 0.7 as the implementation
  default, including S05's API reference and a deployment-guide YAML block that
  contradicted the Python block in the same supplement. The three thresholds are now
  ledger variables read out of the dataclass with `ast`, and the prose says "operational
  default" wherever it states the shipped value --- which is what separates it from
  S08's parametric optimum and Part 3's per-profile tuning, three different quantities
  that had been sharing one symbol.
- **R11-05** --- The bibliography gate's unreachable title branch is replaced by a
  bibkey-collision pass, which found the real defect underneath: one bibkey resolving to
  two different works, four times over. The divergent DOIs were those collisions and
  went with them; DOIs now agree across all three bibliographies.
- **figures F01** --- Both panels of `fig:detection-performance` plotted series nobody
  measured: Panel A labelled per-architecture means as per-mechanism ablations over a
  hardcoded FPR list, and Panel B's "Firewall Only" was the Full CIF value times 0.80,
  making the gap it asked the reader to notice exactly 20% by construction. Both now
  read their artifacts. The true numbers are a better result: series composition
  predicts 12.6% against a measured 12.2%.
- **P2AI-09** --- Partially. `ablation_full_tpr` and the new
  `ablation_series_prediction` are now gated at the figure caption they govern.
- **Cross-paper pointers** --- Part 2 cited Part 1 forty-three times by
  renderer-assigned number and twelve pointed at a different result than the citing
  sentence described, including one citation ("arms-race bounds in Part 1, Section 4")
  to a bound Part 1 does not contain. All forty-three are resolved to named results; the
  check is now gating rather than advisory and passes at zero.


## Round 12 (2026-08-24) — three workstreams, all closed

All three shipped. The scope below is kept as written, because the gap between what
each workstream was expected to do and what it actually found is the most useful thing
in this file. W1 was scoped as a migration and turned into a diagnosis: the corpus was
never the reason three modules measured zero. W2 was scoped as 145 fixes and turned out
to be 62 fixes already applied. W3 was the only one that went as planned.

**Outcome, per workstream:**

| | Scoped as | What it actually was |
|---|---|---|
| **W1** | flip a default, regenerate artifacts, rewrite prose | the docstring's causal claim was false too: extending the corpus by 525 payloads written for the three zero-Shapley modules moved none of them. Separating contribution from capability (`run_module_capability_matrix.py`) showed two were masked and one detected nothing anywhere; rewriting it took consensus from 0.0% to 81.1% at zero FPR. No module has a Shapley value of zero now. |
| **W2** | re-verify, then fix 145 rows | 62 were already closed and none superseded, so the list overstated the debt by 43%. Nine more fixed; 74 struck. |
| **W3** | prune, or add `nocite`, or leave it | pruned: 349 entries to 207, uncited 153 to 4, and the advisory promoted to a gating check that is mutation-tested. |

**Three defects the migration surfaced that nothing had been looking for:** the
multi-seed arm took `corpus[:100]` from a corpus that emits its injections first, so a
direct-injection rate had been published as an overall one and widening the corpus moved
it by zero digits; `run_full_evaluation.py` wrote its provenance hash under a key the
reader does not read, so a parametric artifact classified as unverifiable for as long as
its sidecar existed; and `inject_series_values` rewrote by first-occurrence rather than by
matched span, turning "Assumption 4" into "Assumption 10" while making the gap phrase it
was maintaining correct. All three are fixed, and each now has a test that fails without
the fix.

### DONE — W1 — Corpus migration: make the integrated 1,475-item corpus the only corpus

**The finding that makes this urgent.** `src/attacks/corpus.py:242` reads
`def generate(cls, seed: int = 42, *, extended: bool = False)`, and its own docstring
three lines below reads *"``extended=True`` is the integrated corpus and the default"*
and *"every number this series reports is now measured against one that can [reach all
eight modules]"*. Both sentences are false at HEAD. The signature default is `False`,
and of the twelve call sites outside the tests, exactly **two** pass `extended=True`.
Every published number in the series is measured on the 950-item corpus that reaches
five of the eight defense modules — the corpus whose coverage gap is the reason three
adapters carry a Shapley value of exactly zero. A source docstring asserting a
measurement property the code does not have is the same defect class as a manuscript
asserting one, and it is currently the only place in the repository where a false
claim about provenance is stated in the first person.

**Call sites, exhaustively.** Ten production sites take the 950 corpus:

| Site | Feeds | Downstream |
|------|-------|------------|
| `src/ablation/runner.py:222` | `ablation_results.json` | the 0.959 TPR, the Shapley table, S08 |
| `src/evaluation/baselines.py:225` | `baseline_comparison.json` | the 98-item subsample, §05 |
| `src/statistics/stability.py:396` | `multi_seed_results.json` | the 44.8% [43.2, 46.4] mean, cited in Part 1 |
| `src/redteam/__init__.py:305` | `redteam_evaluation_results.json` | §05g, the Ω ladder |
| `src/visualization/figures/comprehensive_taxonomy.py:23` | taxonomy figure | 12-category roll-up |
| `src/visualization/tables/corpus_tables.py:61` | corpus tables | the published category counts |
| `src/__main__.py:43` | CLI demo | none |
| `scripts/run_full_evaluation.py:88` | `full_evaluation_results.json` | §05 headline rates |
| `scripts/run_cross_validation.py:48` | `cross_validation_results.json` | the fold table |
| `scripts/run_redteam.py:118` | red-team artifact | §05g |

Two sites already migrated: `scripts/run_taxonomy_evaluation.py:328` (behind `--extended`)
and `scripts/run_combination_rule_study.py:87` (hardcoded `extended=True`).

**Blast radius.** 26 manuscript files mention 950; 2 lines mention 1,475. Migrating
re-derives essentially every measured number in Part 2 and every number Parts 1 and 3
cite from it. The ledger and `inject_series_values.py` handle the propagation, but the
*prose around* the numbers — "twelve categories", "950 published items", the
corpus-construction narrative in `03_attack_corpus.md` — is not injected and must be
rewritten by hand. The three category names added by the extension
(`provenance_laundering`, `sandbox_escape`, `byzantine_manipulation`) need a
construction account in the manuscript, not just a count.

**Method.** Flip the signature default to `extended: bool = True`, delete the keyword
from the two sites that pass it, and let the test suite enumerate what breaks — the
category-count and corpus-size assertions are the specification, so their failures are
the migration checklist rather than noise. Regenerate all ten artifacts, run the ledger
write path, then hand-rewrite `03_attack_corpus.md` and the two supplements that narrate
corpus construction. Keep `extended=False` reachable and tested, because the published
950-item results must stay reproducible for the comparison.

**Decision needed.** Whether the papers report the 1,475 corpus as *the* corpus with the
950 results retained as a prior-version comparison, or report both side by side as a
coverage study. The first is cleaner and is what the docstring already claims; the
second is more informative about what corpus coverage does to a Shapley table, and the
taxonomy harness can already produce both.

**Done when** no production call site passes `extended`, the docstring's claim is true,
every artifact carries a corpus digest of the 1,475-item corpus, and no manuscript
sentence describes a twelve-category corpus.

### DONE — W2 — Backlog re-verification: the list has drifted from the repository

**The finding.** The sweep backlog below lists 145 open rows (66 HIGH, 60 MED, 19 LOW)
as measured on 2026-08-23. Triaging each row's site against `git diff 0fa0a09..HEAD`:
**122 of the 145 sit on files that have changed since the sweep**, and only 23 sit on
files untouched — 20 of those 23 being author decisions rather than agent work. Four MED
rows spot-checked at HEAD were all already fixed: `02b-lambda-default-wrong` (02b now
publishes $\lambda = 0.5$, matching `detection.py`), `tripwire-severity-thresholds-wrong`
(02b now publishes 0.50/0.30/0.20, matching `tripwire.py:13-15`),
`s05-pattern-counts-wrong` (S05 now says 13 and 7, matching `len(PatternDetector.*)`),
and `s05-sandbox-module-descriptions` (S05 now describes `BeliefPartition` as the
two-member tag it is).

So the backlog is not a work list, it is a stale snapshot, and reading a count off it
overstates the debt by an unknown margin. That is the same failure the series gate
exists to prevent, one level up: a record of the repository that the repository has
moved past.

**Method.** Re-verify all 145 rows against HEAD before doing any of the work they
describe, because a fix applied to an already-fixed row is how prose gets corrupted.
Each row carries a file, a line and a concrete assertion, so each is checkable in one or
two commands. Partition the outcome three ways: closed (strike the row and say which
commit closed it), still open (keep, with a re-measured line number), or superseded (the
claim no longer parses against the current text — the most dangerous class, because it
looks like "still open" from the outside).

**Cost.** 145 checks, of which roughly 60 are single-grep. The 122 changed-site rows are
the ones that need reading; the 23 untouched-site rows can be carried forward as-is.

**Done when** every row is marked closed, open-with-current-line, or superseded, and the
HIGH/MED/LOW counts in the section header are derived from the table rather than typed.

### DONE — W3 — Bibliography: 153 defined-and-never-cited entries

**Current measurement** from the series gate's advisory: Part 1 39, Part 2 44, Part 3 70,
down from 169 at Round 11 without anyone pruning — the drop is citations added, not
entries removed. Pandoc emits only cited works and there is no `nocite`, so no reader
ever sees these. They are invisible, which is precisely why both fabricated
`supplychain2025` entries survived there for nine rounds.

**Three options, and they are genuinely different.** (a) Prune to the cited set and set
the gate to fail on any uncited entry, which makes the bibliography a closed
1:1 artifact and makes a future fabrication impossible to hide. (b) Keep them as a
curated reading list and add `nocite` so they render, which turns 153 invisible entries
into a visible bibliography section a reader can use — but then every one of them needs
the same verification the cited entries got. (c) Keep the status quo, an advisory count
that nobody acts on.

**Recommendation: (a).** The entries were never verified to the standard the cited ones
were, and the argument for keeping an unverified entry that no reader can see is only
that deleting it might lose something — which git already handles.

**Done when** the per-part uncited count is zero and the bibliography check's advisory
is promoted to a gating failure, or (b) is chosen and every newly-rendered entry has been
verified against its primary record.

### Standing author decisions, unchanged

`S08` six-way tables (regenerate from `run_taxonomy_evaluation.py` or retire to the
artifact's four categories); `N9`/`N10` symbol overloading across the three papers;
`P2AI-06..08` (15 injected labels no registry claim inspects, and 05e's Bayesian numbers
with no artifact to pin against); `H1--H3`, `H5`, the author-math backlog.

---

## Round 14 scope (2026-08-25) — the hardcoded sweep

An 80-agent sweep with adversarial verification of every candidate looked for
values a reader would take as measured: data literals in figure and table
generators, prose tables no artifact produces, and artifacts under
`output/data` whose contents were typed rather than measured. Layout,
documented configuration defaults, and anything the claim registry or the
ledger already binds were excluded by construction, and every finding had to
survive a refutation pass that defaulted to refusing it.

**51 of 74 candidates confirmed**, classified by what it would take to make
each one real:

| Class | Count | Meaning |
|---|---|---|
| `measurable_now` | 27 | an existing corpus and existing modules can compute it |
| `needs_new_harness` | 16 | a real experiment is required that does not exist yet |
| `not_empirical` | 7 | a design constant or an illustration; only the label is wrong |
| `unmeasurable` | 1 | no experiment in this project could produce it |

The sharpest single finding is on the cover. `cif_comprehensive.py` draws a
box headed **KEY METRICS** in Figure 1, which is also the cover image, reading
`Detection: 94%`, `FPR: 6%`, `Latency: +23%`, `Integrity: +127%`. All four were
string literals. 94 and 6 sum to 100, which is what a pair invented together
looks like, and a sibling module in the same package had already diagnosed 0.94
in its own comment as "a stale headline the series has since corrected" and
labelled its own panel schematic. The same headline survived on the cover,
unlabelled, for the life of the project.

### Closed in this round

- The cover panel now reads `defense_overlap.json`, `scalability_results.json`
  and `colony_results.json`. Detection and FPR come from the same measurement
  over the same two corpora, which is the property 94/6 never had. The two
  claims that were not measurable at all are gone rather than rephrased:
  nothing here measures the pipeline against a no-pipeline baseline, so the
  panel reports absolute latency instead of an overhead ratio, and
  `Integrity: +127%` had no referent anywhere in the repository.
- The defense-composition table's sixteen literal cells, replaced by
  `scripts/run_defense_overlap.py`.
- The scalability figure and table, which read a generator placeholder while
  the real timings sat beside them unread.
- Panel B of the detection figure, and the four `*_data.json` placeholders.

### Round 14 progress (2026-08-25)

**21 of 51 confirmed findings closed, 30 still open.** All 7 `not_empirical`
relabels, the 1 `unmeasurable` retraction, and 13 of the 27 `measurable_now`.
The counts are matched by file and line against the sweep's own records rather
than tallied by hand, because 7 + 1 + 13 is exactly the arithmetic this round
keeps finding people get wrong.

The `unmeasurable` one was the worst thing in the series. Part 2 stated that ground
truth labels "were assigned by two independent annotators (Cohen's $\kappa = 0.84$)
with disagreements resolved by a third reviewer". No such annotation was performed and
no $\kappa$ could exist for a corpus whose every label is emitted by a generator. The
paragraph now says that, and carries the retraction in the open.

Three findings turned out to be one defect wearing three faces: the taxonomy figure's
twelve typed subcategory counts (six wrong), the artifact's `FAMILY_OF` mapping three
categories to themselves and silently making a six-way roll-up nine-way, and the
figure's four-colour palette crashing on the fifth family. All three came from the same
habit of hand-maintaining a map the corpus already defines.

The sharpest correction is `tab:baseline-comparison`, which carries the paper's central
self-criticism. Every cell had drifted, and the caption's argument -- CIF beaten by a
factor of 7.7, the keyword regex detecting three times as many attacks -- was computed
off a stale 0.122 row and had become false in the other direction. A self-criticism
built on stale numbers is not humility; it is a different error with a more sympathetic
surface.

### Still open (30)

| Class | Count |
|---|---|
| `measurable_now` | 14 |
| `needs_new_harness` | 16 |

#### measurable_now

| Site | Claim |
|---|---|
| `01c_theoretical_connections.md:164` | "Periodic defender retraining (every 5 cycles, +3% recovery per retraining event) stabilizes the long-run equilibrium at ~0.52---a 4-percentage-point  |
| `03_attack_corpus.md:96` | tab:difficulty-dist, captioned "actual generator output, seed 42", reports Hard 535 / 56.3%, Medium 335 / 35.3%, Easy 80 / 8.4%. |
| `04_experimental_setup.md:42` | "The EnhancedCognitiveFirewall module detects the majority of attacks on first evaluation (short-circuiting the series chain), with mean latency of 0. |
| `04_experimental_setup.md:55` | "…the multi-seed pipeline analysis (30 seeds, mean DR ~86%) and real ablation studies (full pipeline TPR ~12%) establish empirical baselines"; 06_disc |
| `05_results.md:58` | tab: architecture-gap table's Total Gap column reads "~55 pp" on a row whose own Parametric DR is 100% and Empirical DR is 86.3%. |
| `05b_statistical_significance.md:101` | tab: power table reports, per comparison, an effect-size label, a Required n, an Available n and an achieved statistical Power — multi-seed vs 0: 5/30 |
| `05d_ablation_and_scalability.md:84` | Footnote to the scalability table: "95% CIs computed via bootstrap resampling (B = 1,000 iterations) over 10 independent runs per agent count. Detecti |
| `05e_bayesian_uncertainty.md:33` | tab:bayesian-posteriors restates "each major detection claim" as a Beta posterior with explicit k, n and 95% HDI: multi-seed pipeline k=45/n=100 → Bet |
| `05e_bayesian_uncertainty.md:71` | tab:power-analysis gives each evaluation mode's "Est. True Rate" and the sample size n* required for a ±5 pp HDI: multi-seed pipeline 0.45 → n*=380, A |
| `05f_architecture_gap_analysis.md:45` | tab:module-maturity's Evidence column gives a measured per-module marginal contribution for all eight modules — Detection −0.051, Trust Calculus −0.02 |
| `S02_detection_algorithms.md:55` | tab:auc-ci, captioned "Empirical AUC with 95% confidence intervals", reports Drift Score 0.87 [0.84, 0.90] and Ensemble 0.94 [0.92, 0.96]. |
| `S11_adversarial_training_theory.md:77` | Corollary S11.1: "For the empirical AT results in §sec:at-convergence, the observed geometric decay ratio of ≈0.65 implies 1 − αL ≈ 0.65, so αL ≈ 0.35 |
| `fp_mitigation.py:28` | _default_waterfall_data returns a nine-point false-positive-rate series — 0.150, 0.095, 0.070, 0.052, 0.040, 0.032, 0.026, 0.022, 0.018 — plotted as a |
| `03_simulation_review.md:106` | A table headed "Tripwire Configuration Data", introduced by "The simulations utilized the following tripwire densities to achieve the reported results |

#### needs_new_harness

| Site | Claim |
|---|---|
| `04_formal_framework.md:762` | Table tab:cif-ad-matrix, "CIF-AD coupling matrix: coverage of each defense mechanism across AD cycle phases", is twenty-five two-decimal coverage valu |
| `05_defense_mechanisms.md:458` | Table tab:defense-stack, captioned "Recommended defense stack with latency and detection rates", assigns each of six layers a latency (10ms, 5ms, 1ms, |
| `06_detection_methods.md:511` | Table tab:it-detectability, captioned "Information-theoretic detectability by attack class", presents four numeric columns for each of the five Omega  |
| `comprehensive_taxonomy.py:87` | Five per-adversary-class detection rates are typed into the `classes` list (0.85, 0.78, 0.71, 0.65, 0.45 at lines 87, 101, 115, 129, 143) and rendered |
| `03_attack_corpus.md:42` | tab:injection-subcats gives a per-subcategory "Undefended Success Rate" (78%, 65%, 82%) and "CIF Success" (3%, 5%, 7%), with the footnote "Undefended  |
| `03_attack_corpus.md:113` | tab:target-dist reports the corpus's distribution over attack targets — Belief state 280, Action execution 250, Trust relationships 220, Temporal stat |
| `05d_ablation_and_scalability.md:136` | tab:volume-scaling reports detection rate, latency and CPU usage at five message rates (500→0.94/52ms/34%, 1000→0.94/68ms/56%, 2000→0.93/112ms/78%, 50 |
| `S02_detection_algorithms.md:159` | tab:fp-root-causes attributes false positives to five root causes with frequencies that sum to 100% — benign novelty 35%, threshold drift 25%, feature |
| `S02_detection_algorithms.md:192` | tab:fp-mitigation-results reports the measured effectiveness of six FP-mitigation strategies — Confirmation Cascade −60% FPR / −5% TPR, Temporal Smoot |
| `S08_parametric_analysis.md:38` | tab:parametric-claude-code-perf and its AutoGPT twin (line 69) report baseline-vs-CIF latency at p50/p95/p99 (45ms→52ms, 112→138, 287→361; 89→108, 234 |
| `S08_parametric_analysis.md:48` | tab:parametric-claude-code-integrity reports "integrity preservation" for three scenarios — single attack 0.72→0.99 (+38%), sustained attack 1h 0.31→0 |
| `cif_comprehensive.py:281` | The same sidebar states "Integrity: +127%", reading as a measured 2.27x improvement in belief/system integrity attributable to the framework. |
| `comprehensive_taxonomy.py:96` | Fig. 2, the shipped attack-taxonomy figure, draws a filled progress bar and a "Detection: 85%" / "78%" / "71%" / "65%" / "45%" label under each of the |
| `02_theory_review.md:47` | "Part 2's data consistently validated this: High-impact attacks were detected 98% of the time, while low-impact attacks were detected only 74% of the  |
| `02_theory_review.md:87` | "The $\Omega_5$ miss rate (44%) reflects FEP's fundamental challenge" — a specific per-adversary-class miss rate presented as a measured property of C |
| `06b_case_studies.md:73` | "Tuning $\tau_2$ ... from $0.5 \to 0.55$ ... Post-tuning: FPR drops to 3% (300 false positives/day); TPR for this attack type drops from 72% to 68%" — |


---

## Round 13 scope (2026-08-25) — what is left, and why most of it is not an author decision

75 rows remain open: 31 HIGH, 41 MED, 2 LOW as the tables below count them. **Sixty-nine
are labelled `author`.** Read at face value that says the mechanical work is finished and
the rest is judgement. It is not what it says.

Every one of those labels was assigned by a reviewer answering a narrower question: *can
an agent fix this from the row alone?* A row saying "this table's numbers have no
artifact" is unfixable from the row, because the fix is either a measurement that does
not exist yet or a retraction, and neither is in the row. But that is a statement about
missing instrumentation, not about the nature of the defect. Round 12 is the proof: W2's
four hand-checked `author` rows were all already fixed, and the invariants and consensus
rewrites — the two largest changes in the project's history — were both `author` rows
until something measured the thing they were arguing about.

So the organising question for this round is not "which of these do I fix" but **"which
of these can be made checkable, so the gate names the sentence and the author only
decides what it should say"**. Grouped that way, the 75 rows are eight problems, not
seventy-five.

### G1 — Numbers presented as measured, with no artifact behind them (20 rows)

The largest group and the most serious, because it is the exact defect class the entire
apparatus exists to catch, surviving inside the papers the apparatus guards.
`defense_composition.py:147` hardcodes sixteen of twenty cells and computes the Full CIF
row from the four hardcoded inputs. `06_discussion.md:41` carries an architecture-insights
table whose topology dimension appears in no shipped artifact at all. `06_discussion.md:58`
presents 0.89 and 0.72 as measured firewall performance; both are cells of a *parametric*
table, and the 0.72 is the sandbox's cell, not the firewall's. The 98/74 impact-stratified
split is cited in three places across two papers and Part 2 reports no impact-stratified
results of any kind.

**What makes this tractable:** the claim registry already binds 171 numbers to the
computation that produces them, and `sync_claims.py` now writes them back. What it cannot
do is notice a number that is bound to *nothing*. The gate to build is the complement of
the one that exists: sweep every numeric literal in the prose, subtract the ones a claim
or ledger variable owns, and require the remainder to be either inside an explicitly
non-empirical context or listed with a reason. Round 11 built exactly this shape for
citations — `_cited_keys` minus the bibliography — and Round 12 turned that count into a
gate. This is the same move applied to numbers, and it is the highest-value item left in
the project.

Roughly a third of these will resolve to "measure it" (the harness usually exists), a
third to "relabel it parametric", and a third to "retract it". The gate does not decide
which; it makes the choice unavoidable and enumerable.

### G2 — The documented API is not the shipped API (16 rows)

S07's Algorithm 1 describes an embedding stage and an anomaly stage that
`CognitiveFirewall.classify()` does not have; `ProvenanceTracker` appears in no source
file; S09 documents `src.core.base`, which does not import. A reader following these
supplements gets `ModuleNotFoundError`, which is the least forgivable failure mode a
methods paper has.

**Already measured, this round:** of the 18 import statements appearing in manuscript
prose across the three parts, **6 do not resolve** — `src.core.base` (twice),
`cogsec.benchmarks`, `cogsec.testing`, a bare `path`, and `src.utils.config.CIFConfig`,
which imports but has no such attribute. That check took four lines and is worth having
permanently.

**The gate:** extend `test_manuscript_code_examples.py`, which already executes S06's
integration example, to every import path, every documented type and every documented
call signature in the supplements. Signatures are checkable with `inspect.signature`
against the named class, which is what would have caught
`add_provisional(belief, ttl_seconds=None)` being documented with a trust argument it
has never had. Once it runs, each remaining row names a specific symbol and the decision
is binary: implement it or delete the paragraph.

### G3 — One symbol, several meanings (5 rows)

`ρ` carries five meanings in Part 2 and has zero rows in its notation table. `η` has two
undocumented senses in Part 1, `d` is both a defense index and a distance. This is N9/N10,
carried since Round 11, and one of the five remaining `agent` rows is a request for the
gate that would close it.

**The gate:** for each part, extract every distinct `$\symbol$` from the prose, compare
against the notation supplement's table, and fail on a symbol used but not documented —
plus the harder direction, a symbol documented once but used in two definitions, which
Round 12 fixed for `\mathcal{M}` by hand and which nothing prevents recurring. Cheap to
build, mechanically decidable, and it closes a family that has survived three rounds of
being noticed.

### G4 — Part 3 restates Part 1 and Part 2, and the restatement drifts (13 rows)

CT.3 is renamed and restated; the stealth-impact theorem becomes a different claim; a BFT
result is restated as an iff that the original does not assert; an associativity claim is
inverted; a τ₂ mechanism runs backwards. The cross-paper pointer gate built in Round 10
checks that a pointer *resolves*. Nothing checks that what the pointer says the source
says is what the source says.

**This is the group with the least mechanical leverage and it should be honest about
that.** A faithfulness check between a theorem statement and its restatement is not a
regex. What *is* tractable: require every restatement to quote the source's own sentence
rather than paraphrase it, and gate on the quoted text matching the source verbatim.
That converts a semantic problem into a string comparison at the cost of some prose
elegance, and it is the only version of this that a gate can hold.

### G5 — Figures and tables that disagree with their own captions (7 rows)

A taxonomy caption describing a different figure, a pitfall figure plotting a different
eight items than its section lists, generated LaTeX tables never `\input` anywhere, and
orphan generated figures nothing references. The figure registry already exists;
extending it to assert that every generated artifact is referenced exactly once, and that
caption-stated counts match the figure's own data, covers most of this. Round 12's
domain-coverage row was closed exactly this way.

### G6 — Bibliography facts the gate cannot see (4 rows)

A misattributed Copilot RCE disclosure, a placeholder DOI, dead source URLs, uncited MCP
benchmarks. The Round 12 prune closed the *structural* half of the bibliography problem —
nothing is defined-and-unreachable now — but a correctly-formatted entry with the wrong
authors is invisible to any local check. These need network verification against the
primary record, one entry at a time, and that is the honest cost.

### G7 — Coverage claimed as complete that is not (5 rows)

"Complete OWASP coverage" in two abstracts, an ASI mapping that contradicts itself, a
section enumerating three of four. Small, self-contained, and each resolvable by counting
what is actually mapped and writing that number instead of the word "complete". Worth
doing early because it is cheap and it is the kind of claim a hostile reader checks first.

### G8 — Instrumentation gaps (6 rows, and the five remaining `agent` rows live here)

Ablation deltas that no gate covers; the injector writing 15 labels no registry claim
inspects; two provenance schemas where there should be one; a Python 3.10 blocker in CI
that no longer exists; ledger variables with genuinely no prose site, which means a
committed artifact nothing reads. These are the rows that make the other groups
checkable, which is the argument for doing them first.

### Recommended order

**G8 then G2 then G1** is the sequence with the most leverage, and the reason is that
each one makes the next one cheaper. G8 is the instrumentation. G2 is the smallest gate
with a defect already measured behind it — six broken imports, findable in four lines of
Python — so it is the cheapest proof that the approach converts `author` rows into
enumerable ones. G1 is the largest and the most important, and it is worth entering with
a working example of the pattern rather than inventing it there.

**G7 and G5 are cheap and can go in parallel with any of it.** G3 is a clean, bounded
gate whenever there is an appetite for it. **G4 and G6 are the genuine author decisions
in this list** — a faithfulness judgement and a set of facts that need the primary record
— and they are the only two groups where "author" means what it says.

### What Round 12 changed about how this file should be read

Do not act on a row without re-verifying it. Of 145 rows carried into Round 12, 62 were
already fixed, and editing prose that is already correct is how both write-path
corruptions repaired in that round were introduced. The re-verification is cheap — each
row carries a file, a line and a checkable assertion — and it is the difference between
a work list and a snapshot of a repository that has moved on.

---

## Sweep backlog (2026-08-23, re-verified 2026-08-24)

A 12-agent sweep with adversarial verification of every finding returned 153
confirmed defects across the three papers: 72 HIGH, 62 MED, 19 LOW. Closed items
are struck from this list as they land.

**Re-verified 2026-08-24 before any of it was worked on.** Every one of the 145
then-open rows was checked against HEAD by a 16-agent read-only pass, each row
required to return the command output that decided it, with a second
adjudication pass over any row a verifier could not evaluate. The result: **62
already closed, 83 still open, none superseded.** Nine more were fixed in the
same round, so 74 rows are struck here.

That ratio is the finding. The list had drifted far enough that reading a count
off it overstated the debt by 43%, and four MED rows spot-checked by hand before
the sweep began were all already fixed. A backlog nobody re-verifies is a
snapshot of a repository that has moved, and acting on one of its stale rows
means editing prose that is already correct --- which is how the two write-path
corruptions repaired this round were introduced in the first place. Re-verify
before fixing; a fix applied to a fixed row is worse than no fix.

### HIGH (31 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| p3-domain-coverage-figure-stale-and-caption-disagrees-with-table | `10_cross_domain_discussion.md:5` | Three artifacts disagree. (1) Source: I ran the part-3 venv against src/applications/domain_coverage.py — ATTACK_PATTERNS column sums are FR Polarity Inversion 5, Constraint Relaxation 1, Co | agent |
| ungated-ablation-deltas | `series_ledger.py:675` | check_series_integrity.py:176 does `if quantity.pattern is None: continue`, so these three are skipped outright. All three ARE stated in prose, and one of the sites is in Part 1, which claim | agent |
| owasp-complete-coverage | `01_abstract.md:3` | "Complete coverage" of a ten-item standard is a 10/10 quantified claim with no supporting artifact anywhere in the series. I grepped all of Part 1 for OWASP/ASI: `grep -rn "OWASP" cogsec_mul | **author** |
| p1-abstract-owasp-complete-coverage | `01_abstract.md:3` | `grep -rn -i owasp cogsec_multiagent_1_theory/manuscript/*.md` returns only this abstract sentence, three passing mentions in 02_introduction.md (61, 191, 195), and two bibliography lines. P | **author** |
| p1-associativity-claim-inverted | `02_introduction.md:244` | 04_formal_framework.md:342-358 states and proves the opposite: `\begin{theorem}[Delegation Associativity]` ... "this operation is not associative in general", with equation `T_1 \otimes (T_2 | **author** |
| fp-mitigation-80pct | `06_detection_methods.md:423` | Part 2's only false-positive-mitigation table is cogsec_multiagent_2_computational/manuscript/S02_detection_algorithms.md:187-199 (tab:fp-mitigation-results). It gives the three named strate | **author** |
| p1-provably-undetectable-vs-deferred | `08_discussion.md:60` | S01_proofs.md:31 lists `thm:stealth-impact` under "**Asserted without proof (deferred).** ... they are assertions whose proofs are deferred to future work." 04_formal_framework.md:627 says s | **author** |
| p1-fr-bound-proof-redefines-stealth | `S01_proofs.md:1052` | The proof of thm:fr-bound-restated contradicts its own theorem statement and its own lemma. (a) The theorem at S01:993 defines `\mathcal{S}_{\mathrm{FR}} = 1/d_{\mathrm{FR}}`, which the firs | **author** |
| p2-asi-mapping-self-contradiction | `01b_related_work.md:35` | 07_conclusion.md:57 in the same paper gives an incompatible mapping: "CIF addresses ASI01--ASI03, ASI06, and ASI08; the remaining risks (ASI04 data poisoning, ASI05 resource manipulation, ** | **author** |
| worked-example-reject-is-actually-quarantine | `02a_defense_algorithms.md:131` | I ran the paper's own payload through the shipped code. `PatternDetector().score_injection(payload)` returns **0.8**, not 0.72 (matched injection patterns carry weight 0.8 each in `firewall. | **author** |
| p2-taxonomy-caption-describes-a-different-figure | `03_attack_corpus.md:20` | None of the visual-encoding claims is implemented, and 82% appears nowhere. I read comprehensive_taxonomy.py and then read the committed output/figures/comprehensive_taxonomy.png. The figure | **author** |
| p2-corpus-provenance-red-team | `03c_attack_ethics.md:26` | tab:generation-stats attributes 280 of the 950 attacks (29.5%) to human manual crafting, LLM-assisted mutation, and adversarial optimization. That is flatly contradicted by the last line of  | **author** |
| p2-peer-to-peer-results-not-evaluated | `06_discussion.md:46` | Part 2 evaluates exactly four architectures -- Claude Code, AutoGPT, CrewAI, LangGraph -- and none is peer-to-peer. I checked every file in `output/data/`: the string `peer` does not appear  | **author** |
| s07-embedding-and-anomaly-stage-fabricated | `S07_algorithm_pseudocode.md:65` | None of it exists. `grep -rni "sentence.transformer\|MiniLM" --include='*.py' --include='*.toml' --include='*.lock' .` over the whole repo returns zero hits — sentence-transformers is not a  | **author** |
| s07-provenance-tracker-does-not-exist | `S07_algorithm_pseudocode.md:116` | `grep -rn "ProvenanceTracker" src/ tests/` returns zero matches. `src/core/provenance.py` defines only `TaintLabel`, `ProvenanceRecord`, `ProvenanceChain`, `ProvenanceGraph`, `CausalAttribut | **author** |
| firewall-algorithm-1-vs-classify | `S07_algorithm_pseudocode.md:63` | I read `src/core/firewall.py:171-200`. `CognitiveFirewall.classify()` never calls a semantic or anomaly detector and computes no weighted sum: it compares `score_injection(m)` alone to `inje | **author** |
| p3-06-direction | `S08_parametric_analysis.md:208` | These are the same quantity, not different ones -- same parameter (tau_2), same move (0.5 -> 0.55), and Part 3 even anchors on Part 2's own tau_2=0.5 FPR of 6% (06b_case_studies.md:71, '6% F | **author** |
| s08-sensitivity-provenance | `S08_parametric_analysis.md:184` | The named artifact cannot produce those tables, so the reproducibility claim is false for the numbers it is asserted over. I loaded output/data/sensitivity_results.json and enumerated it: it | **author** |
| s09-types-do-not-exist | `S09_functional_api.md:16` | `python -c "from src.core.base import DefenseResult, CognitiveState"` fails with `ModuleNotFoundError: No module named 'src.core.base'` — `ls src/core/` shows no `base.py`. `grep -rn "class  | **author** |
| s09-empty-pipeline-raises | `S09_functional_api.md:34` | I ran it: `MonadicPipeline([])` raises `ValueError: MonadicPipeline requires at least one module`. The guard is `src/core/monad.py:227-229` — `if not modules: raise ValueError(...)` — so the | **author** |
| p2-defense-composition-hardcoded-98pct | `defense_composition.py:147` | Sixteen of the twenty cells are hardcoded strings; only the Full CIF row is computed, and it is computed from the four hardcoded inputs. I ran `compute_series_detection_rate([0.58,0.60,0.68, | **author** |
| omega5-miss-rate-44 | `02_theory_review.md:87` | The only 44.6% in the series is the $\Omega_5$ row of Part 2's red-team generator summary (output/data/redteam_evaluation_results.json: OMEGA_5_COORDINATED.mean_heuristic_evasion_score = 0.4 | **author** |
| impact-stratified-98-74 | `02_theory_review.md:47` | Part 2 reports no impact-stratified detection results. `grep -rni "high-impact\|low-impact\|impact level"` over cogsec_multiagent_2_computational/manuscript returns only prose about the theo | **author** |
| part3-98-74-impact-detection-not-in-part2 | `02_theory_review.md:47` | Part 2 reports no impact-stratified detection rates. `grep -rniE "high[- ]impact\|low[- ]impact" cogsec_multiagent_2_computational/manuscript/*.md` returns exactly one hit (04_experimental_s | **author** |
| p3-94-percent-headline | `03_simulation_review.md:87` | Eight lines below, the same file's "A Note on Three Numbers" box enumerates the three detection rates a reader should encounter -- 96--100%, 44.8%, ~12.2% -- and 94% is not among them. The s | **author** |
| part3-cif-composer-html-does-not-exist | `05_deployment_guide.md:136` | `ls cogsec_multiagent_2_computational/output/web/ \| grep -v '^manuscript__'` returns only `favicon.ico` — the directory holds nothing but the rendered manuscript HTML and a favicon. `find . | **author** |
| p3-pitfall-figure-plots-a-different-eight-than-the-section | `06_common_pitfalls.md:5` | The figure plots a different set of pitfalls from the section it illustrates, and names a category that does not exist. I read src/visualization.py:639-712 (`get_pitfalls_data`), whose own d | **author** |
| case-study-3-tau2-tuning-sign | `06b_case_studies.md:73` | Part 2's quarantine-threshold sensitivity table (S08_parametric_analysis.md:201-211) gives the opposite sign for FPR: $\tau_2=0.5$ → TPR 0.94, FPR 0.06; $\tau_2=0.55$ → TPR 0.94, FPR 0.07. P | **author** |
| sec105-enumerates-three-of-four | `10_cross_domain_discussion.md:91` | §10.5 announces four and then enumerates only Verification Channel Separation (Biowarfare), Active Perturbation Probing (Trade Wars) and Physics-Informed Invariants (Infrastructure). The fou | **author** |
| asb-19-7-defense-success | `10_cross_domain_discussion.md:62` | Fetched the cited source (arXiv:2410.02644, Agent Security Bench, both /abs and /html/v3). The number 19.7 does not appear anywhere in the paper, and the paper never uses the metric "defense | **author** |
| placeholder-doi-vespignani | `references.bib:1238` | The DOI is an all-zeros placeholder and does not resolve: `curl -H 'Accept: application/vnd.citationstyles.csl+json' https://doi.org/10.1038/s41467-024-00000-0` returns "Error: DOI Not Found | **author** |

### MED (41 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| compat-py310-blocker-gone | `ci.yml:271` | I re-verified the full 3.10 matrix and it is green in all three parts, so the stated precondition for promotion is now met. Built three isolated 3.10 envs with the CI install command (`uv sy | agent |
| injector-labels-no-claim-inspects | `injector.py:843` | I dumped every (document,label,count) from a dry-run InjectionReport and every claim_registry claim grouped by file, then diffed. These labels are written into the manuscript but no claim re | agent |
| no-notation-gate-in-series-integrity | `check_series_integrity.py:656` | Ran `grep -rn notation --include=*.py` across all three parts and scripts/ --- the only hits are an unrelated comment in cogsec_multiagent_1_theory/tests/test_proof_status.py:31 and a filena | agent |
| abstract-five-defenses-membership | `01_abstract.md:5` | The count is right and the membership is wrong. The body's five are enumerated as headings in cogsec_multiagent_1_theory/manuscript/05_defense_mechanisms.md: "Canonical Defense 1: Cognitive  | **author** |
| rag-53-percent-owasp | `02_introduction.md:195` | An adoption statistic sourced to a vulnerability taxonomy. The cited entry (references.bib:377-383) is "OWASP Top 10 for LLM Applications 2025", a security standard listing risk categories;  | **author** |
| tau-f-undefined-value | `04_formal_framework.md:704` | $\tau_f$ occurs exactly once in the whole Part 1 manuscript (`grep -rn "tau_f" manuscript/*.md` returns this line only) and is absent from the notation table, which lists only $\tau_1$ (reje | **author** |
| risk-profile-detection-column | `05_defense_mechanisms.md:554` | Four stated detection rates with no derivation and no disclaimer. `grep -rn "99\.5"` across all three manuscript trees returns exactly one hit — this line; the value appears in no artifact,  | **author** |
| auc-misattributed-to-part2 | `06_detection_methods.md:419` | These are Part 1's own figure values, not Part 2's. I ran Part 1's ROC generator math directly (`.venv/bin/python` over `src/visualization/roc_curves.py`, which builds tpr = 1-(1-fpr)**k wit | **author** |
| pipeline-stage-tpr-column | `06_detection_methods.md:571` | Same class as tab:risk-profiles and in the same undisclaimed state, but worse because these numbers are load-bearing: thm:pipeline-tpr (line 592) composes them and \cref{thm:pipeline-tpr} is | **author** |
| pipeline-cost-15pct | `06_detection_methods.md:584` | The figure does not follow from the theorem's own equation with the paper's own pipeline. eq:pipeline-cost is $\mathbb{E}[\text{cost}] = \sum_i c_i \prod_{j<i} \rho_j$, and tab:pipeline-stag | **author** |
| p1-rho-table-entry-never-used | `S03_notation.md:62` | Grepped `\rho` across every Part 1 manuscript file. Every occurrence is one of four meanings, and none is a penalty factor: (a) precision weight of an agent's channel --- 04_formal_framework | **author** |
| p1-eta-two-undocumented-senses | `S03_notation.md:60` | With line 61 ($\eta$ = learning rate) these are the only two $\eta$ rows. Two further senses are used and undocumented, and one of them directly conflicts with this row's subscript conventio | **author** |
| p1-d-defense-index-and-distance | `S03_notation.md:57` | The same $d$ overload the backlog reports for Part 2 also exists in Part 1, with only the delegation-depth sense documented. Two others are in use: (a) DEFENSE INDEX --- 04_formal_framework. | **author** |
| p2-abstract-validated-vs-baseline-comparison | `00_abstract.md:23` | The paper's own baseline comparison (05_results.md, tab:baseline-comparison) reports that the full 8-module CIF pipeline ranks **4 of 5** detectors by Youden's J on the identical corpus: bag | **author** |
| 02b-rmax-does-not-exist | `02b_configuration_parameters.md:91` | `grep -rn "max_rounds\|R_max\|rounds" src/core/consensus.py` returns zero matches. `ConsensusConfig` (line 39) has exactly three fields — `acceptance_threshold=0.7`, `rejection_threshold=0.3 | **author** |
| 02b-kappa-three-different-values | `02b_configuration_parameters.md:17` | The shipped default is 1, not 2: `src/core/sandbox.py:160` sets `min_corroborations: int = 1`, with an inline comment explaining the deliberate change from 0 to 1 (P2-36). A third value is h | **author** |
| p2-attack-surface-caption-encodings-not-implemented | `03_attack_corpus.md:119` | Neither encoding exists and two of the five named nodes are not on the figure. I read src/visualization/figures/attack_surface.py: it imports no corpus and loads no data, every arrow is a fi | **author** |
| part2-03b-delta-to-the-zero | `03b_attack_examples.md:114` | $\delta^0 = 1$ for any $\delta$, so the stated identity is false; the same verbatim block sets "T_rep = 0.3 -> 0.85" so no consistent $\delta$ makes $\delta^0 = 0.8$. Part 1's Trust Boundedn | **author** |
| in-sample-claim-contradicted-by-baseline-table | `04_experimental_setup.md:30` | 05_results.md:147 says the opposite about a rate the paper reports: "The trained comparator (bag-of-words logistic regression) is\nscored strictly out of fold." and 05_results.md:153 tabulat | **author** |
| scalability-summary-says-linear | `05d_ablation_and_scalability.md:144` | Contradicted twice by the same file, ~30 lines earlier. 05d:115 "Memory growth is **quadratic**, not linear, across the measured range: $\gamma_2$ is significant ($p < 0.0001$, CI excluding  | **author** |
| p2-firewall-89-72-presented-as-measured | `06_discussion.md:58` | Both numbers are cells of tab:parametric-claude-code-detection (S08_parametric_analysis.md:27) -- 0.89 is that table's Firewall/direct-injection cell and 0.72 is its *Sandbox* cell for the s | **author** |
| p2-architecture-insights-table-numbers-have-no-artifact | `06_discussion.md:41` | No shipped artifact carries a topology dimension at all. I scanned every file in output/data/*.json for the strings hierarchical / peer_to_peer / peer-to-peer / role_based / role-based / sta | **author** |
| p2-rho-five-meanings-zero-rows | `S01_notation_reference.md:75` | $\rho$ has no row in Part 2's table, and the deferral above does not rescue it: Part 1's S03 documents $\rho$ only as a penalty factor (line 62) and a stigmergic signal reliability (line 158 | **author** |
| byzantine-three-phase-protocol-not-implemented | `S05_framework_api.md:66` | `grep -ni "echo\|signature\|sign(\|broadcast\|phase" src/core/consensus.py` returns **zero matches** in the entire file. `ByzantineConsensus` (line 47) has exactly two operations: `submit_vo | **author** |
| s07-sandbox-algorithm-vs-code | `S07_algorithm_pseudocode.md:114` | I read `src/core/sandbox.py:221-298`. `add_provisional(belief, ttl_seconds=None)` has no trust argument and no $\tau_{trusted}$ branch — every belief goes to the provisional partition uncond | **author** |
| s08-tau2-mechanism-backwards | `S08_parametric_analysis.md:211` | The stated mechanism is backwards independently of whether the table numbers are right. The firewall's three-way split (src/core/firewall.py:191-201) is REJECT for score > tau_1, QUARANTINE  | **author** |
| s11-missing-verification-script | `S11_adversarial_training_theory.md:19` | `scripts/verify_at_convergence.py` does not exist. I enumerated every `src/`, `scripts/`, `tests/` and `output/` path referenced across all three manuscripts and checked each against the fil | **author** |
| p2-generated-latex-tables-never-included | `generate_all_tables.py:37` | None of the ten is included in the manuscript. `grep -rn "tables/" manuscript/*.md` returns nothing, and grepping the ten filenames plus `\input{tables` across manuscript/, config.yaml, prea | **author** |
| part3-firewall-three-verification-layers | `02_theory_review.md:33` | Part 1 defines no such function. cogsec_multiagent_1_theory/manuscript/05_defense_mechanisms.md:139 def:firewall is $\mathcal{F}: \mathcal{M} \to \{\textsc{accept}, \textsc{quarantine}, \tex | **author** |
| part3-stealth-impact-restated-as-different-claim | `02_theory_review.md:45` | Two problems. (a) The quoted statement is not Part 1's theorem. Part 1's thm:stealth-impact (04_formal_framework.md:596, rendered 4.15) states $\mathcal{I}\cdot\mathcal{S}\le C_{\text{channe | **author** |
| part3-ct3-renamed-and-restated | `02_theory_review.md:100` | Part 2's CT.3 is a different theorem with a different name and content: cogsec_multiagent_2_computational/manuscript/02c_composability_algebra.md:34 declares `\begin{theorem}[Monadic Detecti | **author** |
| p3-theory-review-98-74 | `02_theory_review.md:47` | Part 2 has no high-impact/low-impact stratification. The 74% is the emergent-misalignment *colony scenario* rate (74.3%, `colony_results.json`), which Part 3's own Finding 6 (03_simulation_r | **author** |
| part3-06b-trust-bound-085-unsupported | `06b_case_studies.md:22` | No Part 1 result yields this bound. Trust Boundedness (thm:trust-bounded, rendered 4.3) gives $\mathcal{T}^{del}_{i\to k}\le\delta^d$; No Trust Amplification (thm:no-trust-amp 4.8 / thm:trus | **author** |
| arms-race-does-not-maintain-positive-value | `07_future_directions.md:55` | I ran `arms_race_simulation(0.56)` (the static Nash value, the starting point Part 2 uses) with the module's documented defaults -- attacker_adapt_rate 0.02/round, defender_adapt_rate 0.03 e | **author** |
| p3-maturity-stage-outcomes-decrease | `08_conclusion.md:62` | The maturity roadmap's expected outcomes decrease monotonically as the stages advance: Stage 2 (Balanced) promises 96--100%, Stage 3 (High Assurance) promises 95--98%, Stage 4 (Adapter Matur | **author** |
| mcp-benchmarks-uncited | `10_cross_domain_discussion.md:157` | An empirical world-claim ("benchmarks show high attack success rates") with no `\cite{}`. Every other limitation in §10.9 that makes an empirical claim carries a citation (limitation 1 cites | **author** |
| part3-bft-iff-tight-overclaim | `10_cross_domain_discussion.md:107` | Two mismatches with Part 1. (a) Part 1's "quorum formula" is $q = \lceil (n+f+1)/2 \rceil$ (def:quorum, 05_defense_mechanisms.md:353-359); $n \ge 3f+1$ is a separate result, Byzantine Agreem | **author** |
| copilot-rce-attribution | `references.bib:1399` | The URL 404s (host https://www.pillar.security/ returns 200, so this is an absent path, not a network failure). CVE-2025-53773 was disclosed by Johann Rehberger (embracethered.com, "GitHub C | **author** |
| dead-source-urls | `references.bib:1391` | All four return 404 while their hosts return 200 (adversa.ai, neuraltrust.ai, fao.org all 200 at root; doi.org returns "Error: DOI Not Found" for the Computers & Security DOI) — so these are | **author** |
| part3-config-reference-contradicts-series | `config_reference.py:76` | The manuscript says no such thing. `grep -rn "Reputation weight\|Base weight\|Context weight\|Decay factor\|Accept threshold\|Reject threshold" cogsec_multiagent_3_practical/manuscript/` ret | **author** |
| two-provenance-schemas | `check_series_integrity.py:730` | The series gate and Part 2 enforce two different, silently divergent provenance schemas, and that divergence is the structural reason the sidecar-hash-key defect stayed green. Part 2's `src/ | **author** |

### LOW (2 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| p1-orphan-generated-figures | `03_detection_results_figure.py:1` | Nothing in Part 1's manuscript uses either. I enumerated every image inclusion in cogsec_multiagent_1_theory/manuscript/*.md (twelve `![...](figures/*.pdf)` plus five `\includegraphics{figur | **author** |
| ledger-vars-with-genuinely-no-prose-site | `series_ledger.py:747` | These three genuinely have no prose site, so pattern=None is correct for them today -- but that is worth recording, because it means cross_validation_results.json is a committed artifact who | **author** |

## Open backlog (by severity)

### Author decisions surfaced by Round 10

- **R10-OMEGA — one symbol, two ladders.** Part 1's Ω₁–Ω₅ are *access* classes
  (external / peripheral / agent-level / coordination / systemic). Part 2's are *technique*
  classes (passive / injection / impersonation / belief / coordinated), encoded in
  `src/redteam/generator.py::OmegaLevel`. They cannot be renumbered into each other: this
  corpus's "Ω₂ (injection)" spans Part 1's Ω₁ and Ω₂, because direct injection arrives
  through user input and indirect injection through fetched tool content. Round 10 removed
  the false attribution and stated the divergence in Part 2 §3. **Decide:** (a) rename
  Part 2's enum and regenerate the affected artifacts so one Ω ladder serves the series, or
  (b) keep two ladders and give the second its own symbol.
- **R10-S08 — S08's tables are not the artifact.** RESOLVED BY DISCLOSURE, not regeneration.
  S08's methodology note claimed "All data generated by `run_full_evaluation.py` →
  `full_evaluation_results.json`", which was false: the artifact carries four corpus
  categories across four architectures, while S08's per-architecture tables use a six-way
  attack taxonomy the corpus does not have, and none of their cells appears in the artifact.
  The note now states which tables are artifact-derived (the aggregate rows the claim
  registry pins) and which are calibrated response-surface illustrations, and the
  per-architecture summary and the 92% direct-injection figure in §05e are labelled at the
  point of use. **Still open for the author:** whether to regenerate the six-way tables from
  a real six-way run, or retire them in favour of the artifact's four categories. Disclosure
  removes the misreading; it does not add the missing measurement.
- **R10-PTR — Part 2's 44 numbered cross-paper pointers.** Audited as mostly resolving
  correctly, so they were left in place rather than churned. Converting them to named
  references is what promotes `cross-paper-pointers` from advisory to gating.
- **R10-TESTS — the test count is still hand-typed** in Part 3's abstract and introduction.
  It has now drifted three times. Emitting it into a Part 2 artifact and hydrating a
  `{{TOKEN}}` at render time is the fix that holds.

### Round 10 findings still open

113 findings survived adversarial verification. All HIGH findings and the great majority of
MED are closed across the seven Round-10 commits; what remains is listed below, and every
remaining item is either an author decision or a judgement call about what a paper should
claim rather than a mechanical correction.

| ID | What is left |
|----|--------------|
| N9, N10 | Symbol overloading: `d` carries three unrelated meanings in Part 2 (delegation depth, distance, dimension) and only one is documented; Part 1's supplement lists $\lambda$, $\rho$ and $M$ with two meanings each while the body carries four for $\rho$. Disambiguating means choosing new symbols, which is an author call. |
| crossref-MISSED-28 | Part 3's game-theoretic payoff bullets quote numbers that match no Part 2 table. Either re-derive them from `src/analysis/game_theory.py` or drop the bullets. |
| P3-06 | Case Study 3's threshold-tuning result runs opposite to Part 2's measured direction. Resolving it needs the case study re-run, not a text edit. |
| BIB-11 | Roughly half of every bibliography is uncited. Gating this would fail with ~150 violations on day one, so it is recorded rather than enforced; the honest fix is a pruning pass. |
| H1--H3, H5 | The standing author-math backlog (defense independence, closed-semiring axioms, the Fisher-Rao bound, KL-AUC direction). Round 10 made the *claims* honest --- each is now recorded as asserted rather than proved --- but the proofs remain open. |

### Major — Scoped (deferred)
- **H2 (Part 2) — Real-mode AT is a structural no-op.** Refined thresholds are never threaded into the real detector. **Acceptance:** defensible mapping onto detector parameters + held-out delta>0 + regression test. Author architecture decision.

### Part 1 — theory soundness (author decision)
- **H1** defense-independence re-derivation. **H2** closed-semiring axioms. **H3** Fisher-Rao I*S <= pi/2. **H5** KL-AUC bound direction.
- **M1/M2/M4-M7/M9-M11, HIGH-2** Claim vs Proof.
- **Claim-vs-Proof catalog** — 7 theorems without proof (aggregation, trust-monotonic, cross-modality-bound, threshold-selection, fpr-composition, cascade-fpr, pipeline-tpr) + 6 corollaries.

### Medium
- **P2-5 (PARTIAL)** — committed full_evaluation_results.json still provenance-bare; writer is honest. Author tie-break / regen decision.
- **P2-F5b** — full `from statistics.*` import refactor. Previously half-done and reverted. Do not half-fix.

### Minor
- **CI py3.10** still `continue-on-error`. Promote after a runner-verified 3.10 matrix.
- **Part 2/3 DOIs** reserved-not-public until first release.
- **Part 1 title variants** — author decision.

---

## Checked this round
- Full suites: 437 / 3367+3skip / 934; coverage 97.72 / 96.95 / 99.94.
- d=0 kept as identity so trust-decay figures stay valid.
- Author-math and H2 AT threading untouched.
