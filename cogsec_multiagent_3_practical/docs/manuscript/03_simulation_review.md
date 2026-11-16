# The Evidence: What We Proved in Part 2 {#sec:paper2-review}

![Effective trust vs.\ delegation depth at decay factors $\delta = \{0.9, 0.85, 0.7\}$, with 50\% and 10\% thresholds marking delegation bounds.](figures/trust_decay.png){#fig:trust-decay width=75%}

Part 1 supplies the formal apparatus. Part 2 supplies the empirical evaluation: tested CIF modules, a **950-attack** corpus, and an architecture-aware simulation over four headline topologies (Claude Code, AutoGPT, CrewAI, LangGraph), with broader adapter coverage documented in Part 2.

Here is what the data says.

## The Experimental Setup

We tested four common multi-agent architectures found in production:

* **Claude Code** (Hierarchical)
* **AutoGPT** (Autonomous Loop)
* **CrewAI** (Role-Based Team)
* **LangGraph** (State Machine)

The test corpus included direct prompt injection, poisoned RAG contexts, deep trust exploitation, and multi-turn social engineering.

## Finding 1: Defense Layering vs. Individual Efficacy

**The Data**: In the parametric evaluation the full CIF stack achieved a **96--100% parametric detection ceiling**, with direct injection detected at 99--100% across architectures. The separate real-pipeline evaluation had a lower multi-seed mean of 86.3%.
**The Implication**: The parametric model rewards layering, but the real pipeline does not spread the work evenly across layers, and the 100-attack ablation corpus says so plainly. The Invariants module alone detects 85% of that corpus against the full stack's 89.0%, a four-percentage-point margin over the best singleton; no other module detects more than 10% on its own (the next best, Consensus, reaches 6%). Removing Invariants costs 67 percentage points of true-positive rate, removing the Tripwire costs one, and removing Consensus, Detection, Firewall, Provenance, Sandbox or Trust Calculus costs nothing this corpus can measure. That is a statement about *marginal* contribution, not about capability: a module whose detections are all also caught by Invariants scores zero here while detecting plenty on its own. Layering may still buy coverage against attacks this corpus does not contain, but the older claim that removing any single layer opens a measurable gap is not what the ablation shows.

On the separate 1,475-item capability corpus, the Invariants checker detects 83.3\% on its own. That solo capability result is not the 85\% ablation-only TPR and must not be substituted for it.

## Finding 2: State Machine Determinism

**The Data**: In the historical parametric full evaluation (950 simulated attacks per architecture), **LangGraph detected 950/950 (100%)**, tied with Claude Code and CrewAI; AutoGPT detected 931/950 (98.0%). No architecture was uniquely best.
**The Mechanism**: In a state machine, valid transitions are explicitly defined. Attempts to move from an `Analyze` state to an `Execute` state without passing through `Verify` were caught immediately.
**The Implication**: Explicit state definitions provide a "security for free" effect, where the architecture itself enforces behavioral invariants that are difficult to bypass.

## Finding 3: Hierarchical Vulnerability

**The Data**: **Claude Code** and **AutoGPT** styles were strong against external attacks but vulnerable to **Systemic ($\Omega_5$)** compromise.
**The Mechanism**: When the "Boss" agent was tricked, it ordered "Worker" agents to execute malicious actions, and they complied.
**The Implication**: Hierarchical systems exhibit a Single Point of Failure at the root. Security in these topologies requires worker-level tripwires that can reject orders even from authenticated superiors.

## Finding 4: Roles as Security Boundaries

**The Data**: **CrewAI** performed exceptionally well against privilege escalation.
**The Mechanism**: "Roles" acted as effective containers for capabilities. A "Researcher" agent lacked the tools to write code, rendering code-execution attacks against it inert.
**The Implication**: Strict role definitions function as effective security boundaries, limiting the blast radius of a compromised agent.

## Finding 5: The Stealth-Impact Tradeoff

**The Data**: Part 2's corpus has no impact label, so it provides no impact-stratified detection result. The stealth--impact tradeoff is a theoretical prediction, not an experimental finding of this evaluation.
**The Implication**: Whether catastrophic takeover attempts generate more detectable noise than low-impact nudges remains untested here. Operators should not claim an empirical advantage against either class without a corpus that records impact and reports detection by impact stratum.

## Finding 6: Emergent Misalignment Is the Hardest Scenario to Detect

The colony benchmark reveals a striking pattern: **emergent misalignment achieves the lowest detection rate (74.3\%) of any evaluated scenario**, at a false positive rate of 25.5\%. It is not the noisiest scenario: belief cascade detects every attack but at a higher false positive cost (37.4\%). (These are Part 2's 30-seed benchmark means; an earlier single-seed figure of 56.1\% is not the publication estimate.) Part 2's game-theoretic analysis does not explain why, and it is worth being exact about that. Its payoff matrix is a design model: thirty-five of its thirty-six cells have no measurement behind them, and the one that does is this scenario. On the published 74.3\% the equilibrium moves to coordination with game value 0.61; it named emergent misalignment only while the matrix still carried the retracted single-seed 56.1\%. What survives is the measurement itself: of the five scenarios the colony benchmark actually runs, emergent misalignment is the hardest to detect, and by a clear margin.

Part 2's parametric evaluation and colony benchmark show that:
- Full CIF achieves 99--100\% detection against direct injection ($\Omega_1$) and 96--100\% against impersonation, the corpus category standing for trust exploitation ($\Omega_4$)
- Against emergent misalignment (distributed sub-threshold drift with no explicit adversaries), detection falls to 74.3\%
- A rational adversary, knowing CIF is deployed, is pushed away from direct injection. Where exactly it
  is pushed *to* is a design-model question rather than a measured one: on the published numbers Part 2's
  payoff matrix puts the equilibrium at coordination, not emergent misalignment

This is not a failure of CIF—it is a consequence of its success. When explicit attacks are reliably detected, adversaries are forced toward the subtlest and most distributed manipulation strategies. The 74.3\% detection rate on emergent misalignment represents the current frontier of defensive capability, not a gap in the framework's design.

**Operator implication**: Deploy colony-scale entropy monitoring and schedule periodic manual behavioral audits (weekly for high-stakes deployments). The $\Omega_5$ playbook (\cref{sec:incident-response}) provides the response protocol when drift accumulates despite in-context detection.

## Finding 7: The Implementation Gap Is a Feature, Not a Bug

The arithmetic gaps between the parametric ceiling (96--100\%) and the real pipeline compare unlike measurements; they do not identify adapter maturity or any other cause. The **narrow** gap is $96.0-86.3=9.7$ percentage points, from the parametric floor to the architecture-agnostic 30-seed pipeline mean (100 stratified attacks plus 120 benign messages per seed, no adapter). The **wide** gap is $100.0-89.0=11.0$ percentage points, from the parametric top to the full pipeline's rate on the separate 100-attack ablation corpus, where almost all detection comes from the Invariants module and removing any other module except the Tripwire costs nothing the corpus can measure. These are not endpoints of one deployment estimate. Use the 30-seed result for conservative planning and retain each corpus's mode and denominator. Part~2 introduces a 5-level CMMI-style adapter maturity scale:

| Level | Name | Marginal TPR | Description |
| :--- | :--- | :--- | :--- |
| 1 | Stub | $\sim$0\% | Hardcoded scores; no domain logic |
| 2 | Heuristic | 1--5\% | Pattern matching; uncalibrated thresholds |
| 3 | Statistical | 5--15\% | Calibrated thresholds; regression features |
| 4 | Adaptive | 15--30\% | Online learning; per-architecture tuning |
| 5 | Verified | 30\%+ | Formal guarantees; cross-architecture validated |

The rubric column is each adapter's *marginal* contribution to true-positive rate,
not a whole-pipeline detection rate: a Level-5 adapter is one that adds 30 or more
percentage points when introduced, not one that reaches 30\% detection on its own.

The 86.3\% multi-seed mean comes from one architecture-agnostic pipeline with no adapter, so it neither measures a Claude Code adapter nor establishes a maturity level. Part 2's roadmap describes what advancing each adapter toward Level 5 would require, without quoting a projected point gain for any of them. The parametric ceiling (96--100\%) is a design target from simulation, not a measured result for a deployed adapter.

**Operator implication**: If a deployment introduces architecture-specific adapters, assess each adapter against its own threat model and corpus rather than assigning a level from the architecture-agnostic multi-seed result. Whether adapter work closes the parametric-to-pipeline gap requires future measurement; the current artifacts do not establish that outcome.

---

## A Note on the Numbers

The detection rates in Part 2 are derived from a calibrated parametric simulation, modeled on the architecture's topology. They represent the *structural* security of the design.

* **96--100% Parametric Ceiling** means: "In the calibrated parametric simulation ($N=3{,}800$ design-level instances), the full CIF defense stack detects 96--100% of attack vectors, with per-architecture rates ranging from 98--100%."
* It does **not** mean: "We have a magic Python script that catches 96--100% of all evil AI thoughts."

We proved the *architecture* works. The implementation fidelity is the variable for the builder.

> **A Note on Three Numbers**: Throughout this guide you will encounter three detection rates that may seem contradictory. They are not — they measure different things:
>
> - **96--100\%** (parametric simulation, $N=3{,}800$): CIF's **design-level detection ceiling** — what the defense architecture achieves when adapters are fully mature (Level 5) and conditions match the calibrated model. This is the target, not the current reality.
> - **86.3\%** [95\% CI: 85.5\%, 87.1\%] (architecture-agnostic multi-seed pipeline, 30 seeds of 100 stratified attacks plus 120 benign messages, no adapter): The **current empirical baseline** for this pipeline, with measured FPR 18.5\% over the benign arms. It is not an architecture-specific or adapter-tuning estimate.
> - **89.0\%** (100-attack ablation corpus, all categories including hardest): full-pipeline true-positive rate on a corpus built to include difficult attacks, almost all of it contributed by the Invariants module, which scores demand structure rather than topic nouns. Read it as an upper bound rather than a floor: the corpus is template-generated, a detector keyed on demand structure is being asked to recognise generated demands, and the 0\% false-positive rate reported beside it comes from the fifty easy benign strings hard-coded in Part 2's ablation runner, not from the adversarially hard `BenignCorpus` behind the multi-seed figure above.
>
> All three numbers are correct, and they are not interchangeable. Use 86.3\% for realistic planning, since it is measured on the adversarially hard benign corpus and carries its 18.5\% false-positive rate with it; read 89.0\% as an upper bound, because its corpus is template-generated and the 0\% false-positive rate beside it comes from fifty easy benign strings; and treat 96\% as the floor of the achievable ceiling with mature adapters rather than as anything measured today.

### Tripwire Configuration Data

The tripwire densities below are what Part 2's pipeline installs, not a target
density. One `TripwireAdapter` is constructed per pipeline rather than per agent,
and its constructor
(`cogsec_multiagent_2_computational/src/composition/adapters.py`) adds exactly
three canaries; `get_canary_count()` on the resulting adapter returns
`{'identity': 1, 'boundary': 1, 'principal': 1, 'temporal': 0, 'general': 0}`.
`add_temporal_canary` is defined in `src/core/tripwire.py` but never called, so
no temporal canary is installed anywhere.

| Category | Count Used in Sim | Placement Strategy |
|----------|-------------------|-------------------|
| Identity canaries | 1 per pipeline | Core identity beliefs |
| Boundary canaries | 1 per pipeline | Permission boundaries |
| Principal canaries | 1 per pipeline | Trust relationships |
| Temporal canaries | 0 (never installed) | Session continuity (unused) |
