\newpage

# Red-Team Evaluation Framework {#sec:redteam-evaluation}

> **Cross-paper reading guide.**
> Red-team methodology builds on the adversary capability taxonomy in
> Part 1 \cite{friedman2026cogsec1} §3.2–3.4. Practical deployment of red-team
> infrastructure is discussed in the merged Part 3+4 \cite{friedman2026cogsec3} §4.2
> (practitioner red-team checklists) and §5.3.2 (incident-response integration).
>
> **Status.** Values below are generated deterministically by
> `scripts/run_redteam.py --seed 42` → `output/data/redteam_evaluation_results.json`
> ($M=950$). The mutation-operator table is re-derived from that data file by
> `tests/test_redteam.py` (evasion-sweep and manuscript-consistency tests), so
> the manuscript cannot drift from the committed measurements.

## Red-Team Architecture {#sec:redteam-arch}

The CIF red-team evaluation framework (`src/redteam/`) provides a structured
infrastructure for:

1. **Attack generation**: Automated generation of novel attacks across the full
   $\Omega_1$–$\Omega_5$ capability spectrum.
2. **Evasion probing**: Targeted probing of specific defense components to identify
   parameter-space blind spots.
3. **Mutation testing**: Systematic mutation of known detected attacks to identify
   detection boundary conditions.
4. **Campaign orchestration**: Multi-stage attack campaigns spanning multiple
   agent interactions to detect coordinated $\Omega_5$ scenarios.

### Module Structure

```
src/redteam/
├── __init__.py          # AdversarialTrainer, ATConfig, NashEquilibriumEstimator
├── generator.py         # AdversarialGenerator: conditioned attack generation; AttackMutator
├── convergence.py       # Round-attribution and adversarial-rate-of-change tracking
└── evasion.py           # Mutation-operator evasion sweep vs. the real CognitiveFirewall
```

*As-built listing. The manuscript v1.0 draft referenced `mutator.py`, `campaign.py`,
`evasion_probe.py`, `scorer.py`, and `report.py` as planned modules; of these,
`campaign.py`, `evasion_probe.py`, `scorer.py`, and `report.py` are not yet
implemented. Mutation testing is driven by `generator.py`'s `AttackMutator`
class, which performs all 12 mutation types inline; the mutation-operator escape
sweep below is driven by `evasion.py`, which runs those operators against the
real `CognitiveFirewall` and reports each rate with a Wilson confidence interval
and a minimum-denominator anti-vacuity guard.*

## Mutation Testing Results {#sec:mutation-results}

Mutation testing applies 12 mutation operators to each detected attack,
generating variants that test the boundary of the detection decision surface.
A mutation is "successful" (from the adversary's perspective) if it converts a
detected attack to an undetected one while preserving the attack's semantic intent.

Table: Mutation operator evaluation (real pipeline, seed 42, $M=950$). {#tab:mutation-operators}

| Mutation Operator | Attempts | Successful Evasions | Evasion Rate | 95\% CI |
| :--- | ---: | ---: | :---: | :---: |
| Semantic paraphrase | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Nested wrapping | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Indirect routing | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Authority prefix | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Gradual insertion | 66 | 3 | 4.5\% | [1.6, 12.5\%] |
| Chain delegation | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Belief anchoring | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Multi-hop routing | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Canary avoidance | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Confidence spoofing | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Byzantine mimicry | 66 | 0 | 0.0\% | [0.0, 5.5\%] |
| Quorum flooding | 66 | 0 | 0.0\% | [0.0, 5.5\%] |

### Detection Boundary Analysis

The mutation results reveal that on the 66 distinct payloads the firewall flags
in the 950-sample corpus (871 distinct payloads, seed 42), 11 of the 12 mutation
operators produce zero evasions against the real CIF pipeline. The exception is
**gradual insertion**, which evaded detection in 3 of 66 cases (4.5\%; 95\%
Wilson CI $[1.6\%, 12.5\%]$) by splitting the `ignore previous instructions`
trigger phrase so the firewall's lexical pattern no longer matches. Of the 792
total mutation attempts (66 $\times$ 12 operators), 789 were detected. For the
eleven zero-success operators, the 95\% Wilson upper bounds indicate the true
evasion rate is below 5.5\% with 95\% confidence.

**Interpretation**: The near-zero-evasion result reflects the current pipeline's effectiveness against this template-generated attack corpus at seed 42. It does not imply that the pipeline is impervious to mutation attacks. The 66-flagged-payload denominator may not contain the specific attack patterns that each mutation operator targets; the single successful operator, gradual insertion, works by a *lexical* mechanism (splitting the trigger phrase) rather than by semantic reformulation. Furthermore, the mutation operators may produce variants that no longer preserve the original attack's semantic intent (the preservation check in the mutator is lexical, not semantic), so successful (semantics-preserving) evasions may be genuinely rare on this corpus.

### Known Limitations

The current red-team evaluation has important scope limitations:

1. **Corpus size**: The evasion denominator is 66 distinct flagged payloads drawn from the 950-sample corpus (871 distinct payloads), limiting statistical power (e.g., the gradual-insertion 4.5\% rate has a 95\% CI spanning 1.6–12.5\%).
2. **Deterministic evaluation**: All evaluations use seed 42; results may differ with other seeds.
3. **Template-generated attacks**: The attack corpus is 100\% synthetic template expansion; mutation effectiveness may differ on real-world attacks.
4. **Lexical preservation check**: The semantic-equivalence check in the mutator is lexical, not semantic; some "preserved" mutations may have altered meaning, and some "broken" mutations may have preserved it.

Future work should expand the evaluation corpus, implement semantic preservation checking, and test against real-world attack corpora.

## $\Omega$-Level Coverage {#sec:redteam-omega}

The red-team harness generates $M=190$ attacks per $\Omega$ level (950 total,
seed 42) using `AdversarialGenerator` with $\Omega$-conditioned templates. The
table reports, per level, how many attacks were generated, how many *distinct*
payloads the generator emitted (its template set is small), and the generator's
mean self-estimated evasion score — a design-level heuristic, **not** a
firewall-measured evasion rate. Firewall-measured evasion is reported separately
in the mutation sweep above, whose denominator is the 66 corpus payloads the
firewall flags.

Table: Red-team generator summary by adversary capability level (seed 42). {#tab:redteam-omega}

| Adversary Level | Attacks Generated | Distinct Payloads | Mean Self-Estimated Evasion |
| :--- | ---: | ---: | :---: |
| $\Omega_1$ (passive) | 190 | 2 | 0.6% |
| $\Omega_2$ (injection) | 190 | 3 | 24.6% |
| $\Omega_3$ (impersonation) | 190 | 3 | 32.6% |
| $\Omega_4$ (belief manipulation) | 190 | 3 | 36.6% |
| $\Omega_5$ (coordinated) | 190 | 5 | 44.6% |

*The monotonic increase in the generator's self-estimated evasion score with $\Omega$
level is expected: higher-capability adversaries receive higher base evasion scores
by construction and emit more structurally diverse payloads (distinct-payload counts
2→5). These are generative heuristics, not firewall-measured evasion. The
firewall-measured proxy is the mutation sweep above: 66 of the corpus's 871 distinct
payloads (7.6\%) are flagged, and 11 of 12 mutation operators achieve zero real
evasions against the firewall. The $\Omega_5$ design-level score of 44.6\% reflects
that coordinated multi-step attacks are treated as the most capable adversary class,
but this corpus does not independently measure their real-world evasion under the
firewall.*
