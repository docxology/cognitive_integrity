\newpage

# Adversarial Training Evaluation {#sec:adversarial-training}

> **Cross-paper reading guide.**
> The $\Omega$ ladder used in this paper is the technique ladder of
> \cref{sec:omega-mapping}, not Part 1's access-based adversary classes; the two
> do not correspond by index. Deployment implications of adversarial training
> cycles are discussed in the merged Part 3+4 \cite{friedman2026cogsec3}: its
> Deployment Guide (§5) and its Per-Role Security Hardening section (§4b).
>
> **Status.** Values are generated deterministically by
> `scripts/run_adversarial_training.py --seed 42` →
> `output/data/adversarial_training_results.json` and pinned by
> `tests/test_redteam.py` (AT-round and manuscript-consistency tests). The round
> detection rates are a **closed-form design model** — simulated by
> `AdversarialTrainer` from a baseline plus per-round gap attributions rather
> than a pipeline-in-the-loop measurement. Firewall-measured evasion results are
> reported separately in §05h.
>
> **Scope of the AT results.** The per-round $\Delta$DR profile (baseline 0.447,
> round-5 +0.2323), the Key Findings below, the Convergence/Nash projection, and
> the Ω-level 100% implications are **by construction of this closed-form design
> model** — they encode an assumed learning curve, not a measured re-run of the
> defense pipeline. In `measurement_mode='real'`, hardening compares a
> before/after corpus measurement; because the refined thresholds are not yet
> coupled to the firewall's decision function, real mode currently measures no
> improvement ($\Delta \approx 0$). The 0.447 baseline and +0.2323 round-5 gain
> are therefore the scenario assumptions of the design model, not an observed
> hardening result.

## Overview {#sec:adv-overview}

Adversarial training (AT) is the process of iteratively exposing defense mechanisms
to generated attacks, retuning detection thresholds and trust parameters based on
observed failure modes, and re-evaluating the hardened configuration. Unlike static
benchmark evaluation, AT closes the loop between attack generation and defense
refinement, providing an empirical lower bound on the detection rate achievable after
a fixed number of red-teaming rounds.

This section reports results from $K = 5$ rounds of adversarial training applied to
the Claude Code architecture's CIF pipeline. Each round generates $M = 100$ novel
attacks adapted to the previous round's defense configuration, evaluates detection
rates, and updates the pipeline parameters to address observed gaps.

## Adversarial Training Protocol {#sec:at-protocol}

### Round Structure

Each training round $k \in \{1, \ldots, K\}$ proceeds as follows:

1. **Attack generation**: Generate $M = 100$ attacks using the current red-team
   generator `src/redteam/generator.py`, conditioned on the defense configuration
   $\theta^{(k-1)}$ to maximize evasion probability.

2. **Evaluation**: Run the CIF pipeline on all generated attacks; record detection
   rate $\hat{p}^{(k)}$, false negative pattern $\mathcal{F}^{(k)}$, and
   per-component miss rates $\{m_c^{(k)}\}_{c \in \mathcal{C}}$.

3. **Gap attribution**: Decompose $\mathcal{F}^{(k)}$ into component-specific failure
   modes using the ablation attribution method (§\ref{sec:extended-ablation}).

4. **Threshold refinement**: Update detection thresholds
   $\theta^{(k)} = \theta^{(k-1)} + \alpha \cdot \nabla_\theta \hat{p}^{(k)}$
   where $\alpha = 0.05$ is the refinement learning rate.

5. **Re-evaluation**: Evaluate the updated configuration $\theta^{(k)}$ on the
   original 950-attack corpus to confirm that targeted improvements do not regress
   general detection.

### Attack Adaptation Strategy

The red-team generator adapts attacks along three axes per round:

- **Semantic variation**: Paraphrasing injection payloads to evade lexical signatures.
- **Structural mutation**: Modifying the attack's structural features (nesting depth,
  indirect routing) to evade pattern-based detectors.
- **Trust vector targeting**: Identifying the highest-trust path to the target and
  routing attacks through it, exploiting gaps in delegation-chain verification.

The adaptation is implemented in `src/redteam/generator.py::AdversarialGenerator`
and uses the $\Omega_3$–$\Omega_5$ adversary capability levels from
Part 1 \cite{friedman2026cogsec1} Definition 4.

## Results {#sec:at-results}

Table: Adversarial training round-by-round detection rates (Claude Code, seed 42). {#tab:at-rounds}

| Round | Attack Set | Base DR | AT-Hardened DR | $\Delta$ from baseline |
| :---: | :--- | :---: | :---: | :---: |
| 0 (baseline) | Original 950 | 44.7% | --- | --- |
| 1 | AT-Round-1 ($M=100$) | 30.9% | 52.0% | +7.3 pp |
| 2 | AT-Round-2 ($M=100$) | 36.3% | 57.6% | +12.9 pp |
| 3 | AT-Round-3 ($M=100$) | 49.4% | 62.6% | +17.9 pp |
| 4 | AT-Round-4 ($M=100$) | 65.1% | 65.5% | +20.8 pp |
| 5 | AT-Round-5 ($M=100$) | 76.0% | 67.9% | +23.2 pp |

*AT-Hardened DR = detection rate of hardened configuration on the original 950-attack corpus
after each round of threshold refinement. Base DR = detection rate of the current
configuration on newly-generated round-specific attacks. $\Delta$ = improvement over
pre-AT baseline (44.7%).*

### Key Findings

*The four findings below are properties of the closed-form design model (see
Status), not pipeline-in-the-loop measurements.*

1. **Iterative improvement**: Each round yields monotonically increasing hardened DR,
   from 52.0% (Round 1) to 67.9% (Round 5), a cumulative improvement of +23.2 pp over
   the pre-AT baseline.

2. **Later attack sets are easier for the unhardened baseline, not harder**: Base DR
   --- the unhardened configuration's detection rate on each round's fresh attack
   set --- rises from 30.9% to 76.0%. A *rising* base detection rate means the
   generator's later attacks are more, not less, detectable by an untouched
   detector. The generator drifts toward patterns the baseline already recognises
   rather than toward genuinely novel evasions, which is a property of the
   generator, not evidence that the adversary is gaining ground.

3. **No significant regression**: Re-evaluation on the original 950-attack corpus
   after each refinement round shows monotonically improving detection rates,
   confirming that targeted improvements generalize rather than overfit.

4. **Residual evasion after five rounds**: on the original 950-attack corpus the
   Round-5 hardened configuration reaches 67.9% detection, leaving 32.1% evasion.
   (The 76.0% figure in the same row is the *Base DR* column --- the unhardened
   baseline against the Round-5 attack set --- and is not a property of the
   hardened configuration.)

## Convergence Analysis {#sec:at-convergence}

The adversarial training dynamics can be modeled as a two-player zero-sum game
between the defender (maximizing DR) and the red team (maximizing evasion):

$$\theta^* = \arg\max_\theta \min_{\mathcal{A}} \mathrm{DR}(\theta, \mathcal{A})$$
\label{eq:at-nash-objective}
The Nash equilibrium of this game defines the highest detection rate achievable
against an adaptive adversary with knowledge of $\theta$. The empirical AT
sequence's per-round gain sequence $(7.3, 5.6, 5.0, 2.9, 2.4)$ pp is approximately
linear rather than geometrically decaying, and the projected
Nash equilibrium of 100.0\% DR (full detection against any adaptive adversary at
this corpus size) is a property of the assumed per-round gains of the design
model — it is a projection, not a measured result. Larger corpora and stochastic
evaluation would produce intermediate Nash values.

The gap between the Nash projection (100.0\%) and the parametric
ceiling (96--100\%) reflects the deterministic evaluation on a fixed attack
corpus. The adapter-maturity gap $G_{\text{adapter}}$ identified in
§\ref{sec:architecture-gap-analysis} separates the parametric design ceiling
from current empirical pipeline performance.

## Implications for the $\Omega_1$–$\Omega_5$ Adversary Taxonomy {#sec:at-omega-implications}

Per-$\Omega$ detection rates are deliberately **not** reported here. The only
per-level numbers the codebase can produce come from
`RedTeamEvaluator.omega_level_dr()`, which scales one hardened detection rate by a
fixed per-level constant; they are a property of those constants, not a measurement
of per-class performance. An earlier revision tabulated them, and this section
retains its label only so that cross-references from the rest of the series resolve.
Establishing measured per-$\Omega$ rates requires a runtime `omega_level`
annotation on `AttackSample`, which the corpus generator does not currently emit
(\cref{sec:omega-mapping}); that is the prerequisite for this analysis, and it is
recorded as future work rather than reported as a result.
