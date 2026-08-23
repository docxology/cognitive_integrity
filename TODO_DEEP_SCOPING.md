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


## Sweep backlog (2026-08-23)

A 12-agent sweep with adversarial verification of every finding returned 153
confirmed defects across the three papers: 72 HIGH, 62 MED, 19 LOW. 73 are
mechanically fixable; the rest need an author judgement about what the paper
should claim. Closed items are struck from this list as they land.

### HIGH (66 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| p1-conclusion-theorem-6-2 | `09_conclusion.md:72` | `_combined_manuscript.aux` from the committed build resolves thm:stealth-impact to **4.15**. Theorem **6.2** is `thm:cascade-fpr` (Cascade FPR Reduction), an unrelated result. The open quest | agent |
| part1-proof-status-index-numbers-wrong | `S01_proofs.md:13` | Seven of the ten parenthetical numbers disagree with the numbers the renderer actually assigns. From cogsec_multiagent_1_theory/output/pdf/_combined_manuscript.aux: thm:trust-bounded = 4.3 ( | agent |
| p1-s01-theorem-numbers-wrong | `S01_proofs.md:13` | Every hand-typed number in the Proof Status index (and the matching section headings at S01:111, 229, 327, 431, 531, 614, 712) disagrees with the numbers the renderer actually assigns. Read  | agent |
| p1-theta-absent-from-notation-supplement | `S03_notation.md:82` | $\theta$ does not appear anywhere in S03_notation.md's 189 lines, yet Part 1 uses it 15 times in four unrelated senses: (1) $\theta_{\text{drift}}$, the KL drift threshold --- 04_formal_fram | agent |
| 02a-evaluate-not-on-core-classes | `02a_defense_algorithms.md:19` | None of the six core classes has an `evaluate` method. I checked with `hasattr`: `CognitiveFirewall` False, `SandboxManager` False, `TrustCalculus` False, `CognitiveTripwire` False, `Byzanti | agent |
| tripwire-severity-thresholds-wrong | `02b_configuration_parameters.md:67` | `src/core/tripwire.py:13-15` sets `_DRIFT_CRITICAL = 0.5`, `_DRIFT_HIGH = 0.3`, `_DRIFT_MEDIUM = 0.2` — all three published values are wrong. I confirmed behaviourally by constructing `Tripw | agent |
| p2-roc-caption-stale-vs-rewritten-generator | `04_experimental_setup.md:118` | Every particular is false against the current generator and artifact. I read src/visualization/figures/roc_curves.py: it now draws TWO panels (left = detector comparison across cif_full_pipe | agent |
| p2-multiseed-corpus-and-architecture | `05_results.md:11` | Contradicted by the shipped artifact and by two other passages in the same paper. `output/data/multi_seed_results.json` records `seed_metrics[i].n_attacks = 100` for all 30 seeds, a single c | agent |
| p2-gap-table-parametric-claude-code | `05_results.md:59` | This row gives Claude Code a parametric DR of 80%. The row directly above it in the same table gives Claude Code a parametric DR of 100%, and tab:parametric-vs-llm forty lines later (05_resu | agent |
| scalability-beta2-does-not-exceed-beta1 | `05d_ablation_and_scalability.md:100` | 4.6 is smaller than 5.6; the sentence asserts the opposite of its own two numbers. Confirmed against the artifact: output/data/scalability_results.json -> latency_regression_median coefficie | agent |
| p2-05e-posterior-median-not-derivable | `05e_bayesian_uncertainty.md:41` | The stated HDI pins the posterior to Beta(46,56) exactly. I recomputed with the module the section names as its source (`.venv/bin/python`, `sys.path.insert(0,'src')`, `from statistics.bayes | agent |
| p2-05e-code-listing-raises-typeerror | `05e_bayesian_uncertainty.md:53` | I ran the listing verbatim with the project venv from the project root: `TypeError: bayes_factor_two_proportions() got an unexpected keyword argument 'prior'`. The real signature at src/stat | agent |
| p2-ablation-share-82-vs-70 | `06_discussion.md:96` | Two other passages state the same quantity as 70%, and the artifact agrees with them, not with 82%. From `output/data/ablation_results.json` the component_removal deltas are 0.05102, 0.02040 | agent |
| p2-top3-59-percent | `06_discussion.md:19` | 59% is not derivable from `output/data/ablation_results.json` under any reading. Top-3 removal deltas (0.05102 + 0.020408 + 0.010204 = 0.081633) are 80.0% of the summed harmful delta (0.1020 | agent |
| p2-s07-legend-contradicts-own-table | `S07_algorithm_pseudocode.md:24` | Read the whole file. This legend covers the complexity table at lines 15-23. Row 19 of that table is `\| 3. Trust Update \| Part 1's Trust Boundedness theorem \| $O(1)$ direct; $O(d)$ transi | agent |
| sidecar-hash-key-mismatch | `run_full_evaluation.py:183` | `src/data/generate.py:82` defines `SIDECAR_HASH_KEY = "artifact_sha256"` and `_sidecar_provenance()` (generate.py:152-176) reads `payload.get(SIDECAR_HASH_KEY)`. Because the writer emits `sh | agent |
| injector-n10-stamps-pipeline-arm | `injector.py:1006` | Ran inject_all(dry_run=True, strict=False) with an InjectionReport: it reports `04_experimental_setup.md llm_total_n 3` -- the pattern fires on THREE sites, not one. Two are LLM sites (04:44 | agent |
| p2-taxonomy-corpus-derivation-is-dead-code | `comprehensive_taxonomy.py:25` | The try block always raises and the hardcoded fallback always wins. I ran it in the part-2 venv: `AttackCorpus.generate(seed=42)` returns an object whose public API is by_category/by_difficu | agent |
| payoff-bullets-attributed-to-wrong-artifact | `03_simulation_review.md:52` | None of these three numbers appears in the payoff matrix. I ran `cogsec_multiagent_2_computational/.venv/bin/python -c "from src.analysis.game_theory import compute_cif_payoff_matrix; ..."`; | agent |
| emergent-misalignment-not-highest-fpr | `03_simulation_review.md:50` | Read cogsec_multiagent_2_computational/output/data/colony_results.json and printed every scenario's 30-seed means: recruitment_poisoning det 0.8071 / fpr 0.0672; sybil_infiltration 1.0000 /  | agent |
| p3-hdi-two-values | `03_simulation_review.md:95` | Part 3's own conclusion gives a different 95% HDI for the identical quantity: 08_conclusion.md:25 -- "a mean detection rate of 44.8\% [95\% HDI: 35.5\%, 54.7\%]". The conclusion's interval i | agent |
| parametric-ceiling-87 | `06b_case_studies.md:75` | The parametric ceiling is a gated ledger quantity: series_ledger.py derives parametric_ceiling_low=96.0 and parametric_ceiling_high=100.0 from full_evaluation_results.json, and Part 3 states | agent |
| cyber-attack-pattern-table | `09e_cyber_security.md:73` | The same file's body (line 25) says "This constitutes a **Context Boundary Violation** attack pattern ... The diagonal elements themselves are untouched, which is what distinguishes this fro | agent |
| drone-casualties-misattribution | `09f_drone_wars.md:20` | The 70--80% figure in the public record (IISS, Western-official estimates, UN HRMMU) is for **drones** generally — overwhelmingly manually piloted FPV — not AI-directed systems. The paper's  | agent |
| fig-caption-pattern-totals | `10_cross_domain_discussion.md:5` | The §10.1 table 14 lines below reads **Total \| 5 \| 1 \| 4**, and src/applications/domain_coverage.py's ATTACK_PATTERNS column sums are [5,1,4] — pinned by tests/test_applications.py::test_ | agent |
| p3-domain-coverage-figure-stale-and-caption-disagrees-with-table | `10_cross_domain_discussion.md:5` | Three artifacts disagree. (1) Source: I ran the part-3 venv against src/applications/domain_coverage.py — ATTACK_PATTERNS column sums are FR Polarity Inversion 5, Constraint Relaxation 1, Co | agent |
| novel-patterns-three-vs-four | `10b_applications_conclusion.md:13` | 09_applications_intro.md:67 states "**C4:** Four novel defense pattern extensions: verification channel separation (biowarfare), active perturbation probing (trade wars), physics-informed in | agent |
| placeholder-doi-king | `references.bib:1284` | All-zeros placeholder DOI; `https://doi.org/10.1080/01402390.2024.0000000` returns "Error: DOI Not Found". It is the only citation for the verifiable world-claim at 09f_drone_wars.md:20 ("Th | agent |
| stale-domain-coverage-figure | `domain_coverage.png:1` | Re-rendering with `.venv/bin/python -c "from src.applications.domain_coverage import render_domain_coverage_figures; render_domain_coverage_figures(Path('/tmp/claude/regen'))"` produces "Con | agent |
| ungated-ablation-deltas | `series_ledger.py:675` | check_series_integrity.py:176 does `if quantity.pattern is None: continue`, so these three are skipped outright. All three ARE stated in prose, and one of the sites is in Part 1, which claim | agent |
| ungated-top-synergy | `series_ledger.py:699` | The value +0.031 is restated in seven prose sites across two papers, one of them outside claim_registry's reach: cogsec_multiagent_1_theory/manuscript/10_limitations.md:172 "two pairs tied f | agent |
| ungated-colony-emergent-fpr | `series_ledger.py:729` | Derives 25.4839 (-> 25.5%). Four prose sites state it, and the ledger checks none. Part 3: cogsec_multiagent_3_practical/manuscript/03_simulation_review.md:50 "**emergent misalignment achiev | agent |
| ungated-at-final-hardened-dr | `series_ledger.py:779` | Part 1 quotes it twice and nothing checks Part 1: cogsec_multiagent_1_theory/manuscript/06_detection_methods.md:615 "raising hardened detection from 52.0\% at Round 1 to 67.9\% at Round 5 in | agent |
| owasp-complete-coverage | `01_abstract.md:3` | "Complete coverage" of a ten-item standard is a 10/10 quantified claim with no supporting artifact anywhere in the series. I grepped all of Part 1 for OWASP/ASI: `grep -rn "OWASP" cogsec_mul | **author** |
| p1-abstract-owasp-complete-coverage | `01_abstract.md:3` | `grep -rn -i owasp cogsec_multiagent_1_theory/manuscript/*.md` returns only this abstract sentence, three passing mentions in 02_introduction.md (61, 191, 195), and two bibliography lines. P | **author** |
| p1-associativity-claim-inverted | `02_introduction.md:244` | 04_formal_framework.md:342-358 states and proves the opposite: `\begin{theorem}[Delegation Associativity]` ... "this operation is not associative in general", with equation `T_1 \otimes (T_2 | **author** |
| omega-detection-matrix | `06_detection_methods.md:421` | No such matrix exists, and the same file says so 414 lines earlier. Line 7 of this very file states: "Part 2 reports no measured per-$\Omega$-class detection rates: the corpus carries a desi | **author** |
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
| nash-optimal-headline-rests-on-a-value-the-same-paragraph-retracts | `03_simulation_review.md:50` | The paragraph disowns 56.1\% and then leans on a Nash result that is computed from exactly that number. output/data/colony_results_single_seed.json gives emergent_misalignment detection_rate | **author** |
| overall-detection-94-percent | `03_simulation_review.md:87` | Computed directly from the committed artifact cogsec_multiagent_2_computational/output/data/full_evaluation_results.json (16 rows, n_attacks-weighted): overall = 0.995; per architecture Clau | **author** |
| p3-94-percent-headline | `03_simulation_review.md:87` | Eight lines below, the same file's "A Note on Three Numbers" box enumerates the three detection rates a reader should encounter -- 96--100%, 44.8%, ~12.2% -- and 94% is not among them. The s | **author** |
| part3-cif-composer-html-does-not-exist | `05_deployment_guide.md:136` | `ls cogsec_multiagent_2_computational/output/web/ \| grep -v '^manuscript__'` returns only `favicon.ico` — the directory holds nothing but the rendered manuscript HTML and a favicon. `find . | **author** |
| p3-pitfall-figure-plots-a-different-eight-than-the-section | `06_common_pitfalls.md:5` | The figure plots a different set of pitfalls from the section it illustrates, and names a category that does not exist. I read src/visualization.py:639-712 (`get_pitfalls_data`), whose own d | **author** |
| case-study-3-tau2-tuning-sign | `06b_case_studies.md:73` | Part 2's quarantine-threshold sensitivity table (S08_parametric_analysis.md:201-211) gives the opposite sign for FPR: $\tau_2=0.5$ → TPR 0.94, FPR 0.06; $\tau_2=0.55$ → TPR 0.94, FPR 0.07. P | **author** |
| sec105-enumerates-three-of-four | `10_cross_domain_discussion.md:91` | §10.5 announces four and then enumerates only Verification Channel Separation (Biowarfare), Active Perturbation Probing (Trade Wars) and Physics-Informed Invariants (Infrastructure). The fou | **author** |
| asb-19-7-defense-success | `10_cross_domain_discussion.md:62` | Fetched the cited source (arXiv:2410.02644, Agent Security Bench, both /abs and /html/v3). The number 19.7 does not appear anywhere in the paper, and the paper never uses the metric "defense | **author** |
| placeholder-doi-vespignani | `references.bib:1238` | The DOI is an all-zeros placeholder and does not resolve: `curl -H 'Accept: application/vnd.citationstyles.csl+json' https://doi.org/10.1038/s41467-024-00000-0` returns "Error: DOI Not Found | **author** |
| wrong-doi-agrisecurity | `references.bib:1332` | The DOI resolves, but to a completely different paper. Crossref content negotiation on 10.1016/j.compag.2024.109200 returns title "Using singular spectrum analysis and empirical mode decompo | **author** |

### MED (60 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| mypy-advisory-blocker-gone | `ci.yml:87` | The named blocker no longer exists and its stated rationale is incoherent. Ran the exact CI command from cogsec_multiagent_2_computational: `.venv/bin/mypy src` -> `Success: no issues found  | agent |
| compat-py310-blocker-gone | `ci.yml:271` | I re-verified the full 3.10 matrix and it is green in all three parts, so the stated precondition for promotion is now met. Built three isolated 3.10 envs with the CI install command (`uv sy | agent |
| latency-empirical-observation | `S01_proofs.md:793` | There is no empirical observation. The inputs it corroborates are labelled as non-measurements twelve lines above, at S01_proofs.md:781-782: "With the same illustrative parameters used in th | agent |
| 02b-lambda-default-wrong | `02b_configuration_parameters.md:82` | $\lambda$ is the `lambda_weight` argument of `DriftDetector.is_anomalous` (`src/core/detection.py:184`), whose default is **0.5**, not 0.3: `def is_anomalous(self, current, window: int = 10, | agent |
| p2-bayes-denominators | `05_results.md:62` | Neither count matches the computation the paper actually reports. 05e_bayesian_uncertainty.md:50 shows the code: `bayes_factor_two_proportions(n1=100, k1=45, n2=100, k2=92)` -- the empirical | agent |
| s05-pattern-counts-wrong | `S05_framework_api.md:46` | I counted them from the shipped class: `len(PatternDetector.INJECTION_PATTERNS)` is **13** and `len(PatternDetector.SUSPICIOUS_PATTERNS)` is **7** (`src/core/firewall.py:54-78`). The "15" ap | agent |
| s05-sandbox-module-descriptions | `S05_framework_api.md:110` | `src/core/sandbox.py:17` defines `class BeliefPartition(Enum)` with exactly two members, `VERIFIED = "verified"` and `PROVISIONAL = "provisional"`. It is a tag, not a container, holds no bel | agent |
| p2-trust-decay-caption-omits-schematic-panel-b | `S08_parametric_analysis.md:215` | The caption describes only Panel A of a two-panel figure; Panel B is fabricated data and the caption never says so. src/visualization/figures/trust_decay.py:33 creates `plt.subplots(1, 2, .. | agent |
| s09-detectionevent-field-names | `S09_functional_api.md:25` | `src/core/monad.py:53-66` defines `DetectionEvent` with exactly three fields: `module_name: str`, `score: float`, `details: Dict[str, Any]`. There is no `context` and no `timestamp`, so `eve | agent |
| injector-labels-no-claim-inspects | `injector.py:843` | I dumped every (document,label,count) from a dry-run InjectionReport and every claim_registry claim grouped by file, then diffed. These labels are written into the manuscript but no claim re | agent |
| p2-f5b-test-bayesian-src-prefix-double-loads-package | `test_bayesian.py:27` | This is the leftover half of the reverted refactor. It is the ONLY statistics import in the repo that uses the `src.` prefix; the other 33 occurrences (8 test files, 4 scripts/run_*.py, 3 sr | agent |
| shipped-provenance-gate-covers-2-of-7 | `test_data_provenance.py:55` | This is the gate that should have caught the finding above, and it cannot: `AUTHORITATIVE_RESULT_NAMES` (src/data/generate.py:88-96) holds seven names, `_REGRESSION_NAMES` holds two. The onl | agent |
| profile-b-tau1-mismatch | `05_deployment_guide.md:32` | Part 2's named table gives $\tau_1$ (reject) = 0.7 and $\tau_2$ (quarantine) = 0.5 (S08_parametric_analysis.md:275-276, restated at :311 "Optimal parameters: $\tau_1 = 0.7$ (reject), $\tau_2 | agent |
| ibm-breach-cost-uncited | `05c_cost_benefit.md:44` | This is a world-claim about an external figure with no `\cite{}` anywhere in the file (`grep -n 'IBM' 05c_cost_benefit.md` returns only this line; references.bib has no IBM Cost of a Data Br | agent |
| p3-pitfall4-hardest-attack | `06_common_pitfalls.md:70` | Part 3's own Finding 6, at 03_simulation_review.md:50, says the opposite: "emergent misalignment achieves the lowest detection rate (74.3\%) at the highest false positive rate (25.5\%) **of  | agent |
| asb-84-3-is-highest-not-average | `09_applications_intro.md:22` | The ASB abstract (arXiv:2410.02644v3, fetched) reads verbatim: "...with the **highest** average attack success rate of 84.30%, but limited effectiveness shown in current defenses". 84.30% is | agent |
| wittmann-wrong-doi | `references.bib:1303` | `https://doi.org/10.1126/science.adq7592` returns "Error: DOI Not Found". The real paper (which the 09h_biowarfare.md:38 prose describes accurately) is Wittmann, Alexanian et al., "Strengthe | agent |
| no-notation-gate-in-series-integrity | `check_series_integrity.py:656` | Ran `grep -rn notation --include=*.py` across all three parts and scripts/ --- the only hits are an unrelated comment in cogsec_multiagent_1_theory/tests/test_proof_status.py:31 and a filena | agent |
| ungated-at-rounds | `series_ledger.py:795` | Stated in four prose sites and covered by no claim (the four 05g claims are baseline_dr, final_hardened_dr, round1_hardened, total_delta -- none is a round count). Part 2: 05g_adversarial_tr | agent |
| ungated-at-total-delta | `series_ledger.py:787` | cogsec_multiagent_1_theory/manuscript/08_discussion.md:16 hand-types it: "$+23.2$ pp over the pre-AT baseline" -- Part 1, so claim_registry cannot see it. In Part 2, 05g.total_delta covers o | agent |
| ungated-scalability-max-agents | `series_ledger.py:755` | It has prose sites and no claim covers any of them (the 05d claim set is 05d.corpus_size, 05d.full_pipeline_tpr, 05d.ms_mean, 05d.intro_detection_delta and the tpr/delta/synergy table rows - | agent |
| abstract-five-defenses-membership | `01_abstract.md:5` | The count is right and the membership is wrong. The body's five are enumerated as headings in cogsec_multiagent_1_theory/manuscript/05_defense_mechanisms.md: "Canonical Defense 1: Cognitive  | **author** |
| rag-53-percent-owasp | `02_introduction.md:195` | An adoption statistic sourced to a vulnerability taxonomy. The cited entry (references.bib:377-383) is "OWASP Top 10 for LLM Applications 2025", a security standard listing risk categories;  | **author** |
| tau-f-undefined-value | `04_formal_framework.md:704` | $\tau_f$ occurs exactly once in the whole Part 1 manuscript (`grep -rn "tau_f" manuscript/*.md` returns this line only) and is absent from the notation table, which lists only $\tau_1$ (reje | **author** |
| risk-profile-detection-column | `05_defense_mechanisms.md:554` | Four stated detection rates with no derivation and no disclaimer. `grep -rn "99\.5"` across all three manuscript trees returns exactly one hit — this line; the value appears in no artifact,  | **author** |
| auc-misattributed-to-part2 | `06_detection_methods.md:419` | These are Part 1's own figure values, not Part 2's. I ran Part 1's ROC generator math directly (`.venv/bin/python` over `src/visualization/roc_curves.py`, which builds tpr = 1-(1-fpr)**k wit | **author** |
| pipeline-stage-tpr-column | `06_detection_methods.md:571` | Same class as tab:risk-profiles and in the same undisclaimed state, but worse because these numbers are load-bearing: thm:pipeline-tpr (line 592) composes them and \cref{thm:pipeline-tpr} is | **author** |
| pipeline-cost-15pct | `06_detection_methods.md:584` | The figure does not follow from the theorem's own equation with the paper's own pipeline. eq:pipeline-cost is $\mathbb{E}[\text{cost}] = \sum_i c_i \prod_{j<i} \rho_j$, and tab:pipeline-stag | **author** |
| p1-rho-table-entry-never-used | `S03_notation.md:62` | Grepped `\rho` across every Part 1 manuscript file. Every occurrence is one of four meanings, and none is a penalty factor: (a) precision weight of an agent's channel --- 04_formal_framework | **author** |
| p1-mathcal-M-two-rows-no-disambiguation | `S03_notation.md:44` | Line 154 of the same file reads `\| $\mathcal{M}$ \| Set of marker types \| \cref{def:stigmergic-operator} \|`. The identical unsubscripted symbol gets two rows in two tables of one referenc | **author** |
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

### LOW (19 open)

| ID | Site | Defect | Who |
|----|------|--------|-----|
| ruff-format-blocker-counts-stale | `ci.yml:67` | The blocker is real — this step cannot be promoted — but all three hand-typed counts have drifted, in both directions, which is the exact hand-typed-number-drift class this series' doctrine  | agent |
| header-omits-fourth-advisory | `ci.yml:9` | The header enumerates three advisory items, but the file has four `continue-on-error: true` occurrences — `grep -n continue-on-error .github/workflows/ci.yml` returns lines 69 (ruff format), | agent |
| p1-mathcal-K-undocumented | `03_threat_model.md:46` | $\mathcal{K}$ is a component of the adversary-class tuples at 03_threat_model.md:44 ($\mathcal{K}_{\text{public}}$), :54 ($\mathcal{K}_{\text{system}}$), :69/71 ($\mathcal{K}_{\text{domain}} | agent |
| p1-cusum-symbols-undocumented | `05_defense_mechanisms.md:674` | The CUSUM change-detection subsection (05_defense_mechanisms.md:672-696) introduces three symbols --- $g_t$ (cumulative statistic, line 672), $\nu$ (allowance / reference value, lines 672, 6 | agent |
| p1-capital-lambda-undocumented | `06_detection_methods.md:439` | $\Lambda$ is used here and at 06_detection_methods.md:444 and has no row in S03_notation.md. It is visually close to the two documented lowercase $\lambda$ entries (S03 lines 95 and 159), wh | agent |
| p1-sigma-table-entry-conflicts-with-ooda-use | `S03_notation.md:152` | This is the only row for $\Sigma$, but 04_formal_framework.md:798 defines the OODA automaton as `\text{OODA}_i = (Q, q_0, \Sigma, \delta_{\text{OODA}})` and line 800 states '$\Sigma = \mathc | agent |
| p1-mathcal-E-edge-set-undocumented | `S03_notation.md:151` | Only row for $\mathcal{E}$. But 03_threat_model.md:139 defines adversary class $\Omega_4 = \langle \mathcal{E}_{\text{ctrl}}, f_{\text{man}}, \mathcal{K}_{\text{protocol}}, \mathcal{C}_{\tex | agent |
| p1-lambda-third-meaning-undocumented | `S03_notation.md:95` | S03 already carries two $\lambda$ rows --- line 95 here and line 159 ('Temporal decay constant (colonial trust)'), matching 06_detection_methods.md:18/31 and S02_eusocial_cogsec.md:94/96/474 | agent |
| 02a-parameter-count-wrong | `02a_defense_algorithms.md:145` | Counting the rows of the eight tables in 02b_configuration_parameters.md gives 29, not 27: core 5 (lines 15-19), trust 6 (27-32), firewall 5 (42-46), sandbox 2 (58-59), tripwire 5 (67-71), d | agent |
| redteamevaluator-wrong-class-name | `05g_adversarial_training.md:157` | There is no `RedTeamEvaluator` class anywhere in the repository. `grep -n "^class " src/redteam/__init__.py` lists `ATConfig`, `ATRoundResult`, `AdversarialTrainer`, `NashEquilibriumEstimato | agent |
| p2-f5b-analysis-runner-absolute-self-import | `analysis_runner.py:253` | analysis_runner.py is a submodule of the statistics package but imports its own siblings by absolute top-level name. Every other module in the package uses relative form (src/statistics/__in | agent |
| ledger-crossval-comment-is-false | `series_ledger.py:742` | A manuscript does write it: `grep -rn --include='*.md' -E "[0-9]+-fold"` returns cogsec_multiagent_2_computational/manuscript/05_results.md:153 "\| Bag-of-words LR (trained, 5-fold CV) \| 1. | agent |
| ungated-at-baseline-dr | `series_ledger.py:771` | It has prose sites, so it is gateable now. 05g_adversarial_training.md:92 "\| 0 (baseline) \| Original 950 \| 44.7% \|" and 05g:102 "pre-AT baseline (44.7%)." and the Status block at 05g:26  | agent |
| ungated-redteam-attacks-generated | `series_ledger.py:763` | It has prose sites: 05h_redteam_evaluation.md:15 "`scripts/run_redteam.py --seed 42` -> `output/data/redteam_evaluation_results.json`\n($M=950$)" and 05h:59 "Table: Mutation operator evaluat | agent |
| p1-orphan-generated-figures | `03_detection_results_figure.py:1` | Nothing in Part 1's manuscript uses either. I enumerated every image inclusion in cogsec_multiagent_1_theory/manuscript/*.md (twelve `![...](figures/*.pdf)` plus five `\includegraphics{figur | **author** |
| 02b-invariant-interval-outside-own-range | `02b_configuration_parameters.md:100` | The only invariant check-interval setting in the code is `FrameworkConfig.invariant_check_interval` (`src/utils/config.py:55`), whose default is **1.0** second — not 60s, and outside the pub | **author** |
| part2-s01-theorem-1-nonexistent | `S01_notation_reference.md:50` | There is no "Theorem 1" in either paper's numbering. Part 1 numbers theorems per section (`\newtheorem{theorem}{Theorem}[section]` in preamble.md), so every Part 1 theorem is of the form N.M | **author** |
| firewall-only-60-70 | `03_simulation_review.md:22` | Computed the firewall-only column means from Part 2's S08 per-architecture tables: Claude Code 0.707, AutoGPT 0.700, CrewAI 0.728, LangGraph 0.763 — i.e. 70--76%, not 60--70%. Individual cel | **author** |
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
