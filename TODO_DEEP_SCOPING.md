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

## Executive Summary - measured 2026-08-16 (Round 9)

| Paper | Tests | Manuscript verifier | Notes |
|-------|-------|---------------------|-------|
| 1 | 437 passed / 0 skipped | PASS (7/7) | |
| 2 | 3369 passed / 3 skipped | claim registry 163/163 MATCH | |
| 3 | 935 passed / 0 skipped | PASS (8/8) | |
| series | 33 passed (`tests/test_series_integrity.py`) | gate PASS | new in Round 10 |

Measured 2026-08-22. The series row is the new program-level gate; it had no predecessor,
which is the finding that organises this round.

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
| P2AI-06..08 | The injector writes 15 labels no registry claim inspects, and 05e's Bayesian numbers have no artifact to pin against. |
| N9, N10 | Symbol overloading across the three papers. |
| BIB-11 | 169 bibliography entries are defined and never cited (Part 1 47, Part 2 49, Part 3 73). Not a defect a reader can see --- pandoc emits only cited works, and there is no `nocite` --- but it is where both fabricated `supplychain2025` entries hid, so the bibliography check now reports the count as an advisory. Pruning is an author call. |
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


## Round 12 scope (2026-08-24) — three workstreams, scoped not yet executed

This section scopes the three items left open after the invariants rewrite. Nothing
here is executed yet; each workstream states its blast radius, its method, the
decision it needs, and the condition under which it is finished.

### W1 — Corpus migration: make the integrated 1,475-item corpus the only corpus

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

### W2 — Backlog re-verification: the list has drifted from the repository

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

### W3 — Bibliography: 153 defined-and-never-cited entries

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
