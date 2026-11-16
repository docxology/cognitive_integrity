# `src/redteam/` — Adversarial Training and Red-Team Evaluation

Adversarial evaluation layer over the core CIF defenses: conditioned attack
generation across the Ω₁–Ω₅ adversary capability spectrum, iterative
adversarial training with threshold refinement, and a mutation-operator escape
sweep scored against the real `CognitiveFirewall`. This subpackage realizes the
§05g (adversarial training) and §05h (red-team evaluation) empirical claims of
the manuscript.

## Series Position

Part 2 of three in the *Cognitive Security for Multiagent Operators* series.
The adversary capability taxonomy this package implements is defined formally in
Part 1 §3.2–3.4; the practitioner red-team checklists that consume these results
live in the merged Part 3+4 §4.2.

## Modules

| Module | Purpose | Key Exports |
| ------ | ------- | ----------- |
| `__init__.py` | Adversarial training framework — iterative AT rounds, threshold refinement, convergence projection, plus the modular real-measurement building blocks | `AdversarialTrainer`, `ATConfig`, `ATRoundResult`, `NashEquilibriumEstimator`, `measure_detection_rate`, `refine_thresholds`, `evaluate_adaptive_attacks` |
| `generator.py` | Conditioned attack generation and mutation | `AdversarialGenerator`, `GeneratedAttack`, `AttackMutator`, `OmegaLevel` |
| `convergence.py` | Round-attribution and adversarial-rate-of-change tracking | `convergence_round_estimate`, `geometric_convergence_projection`, `natural_gradient_at_step` |
| `evasion.py` | Mutation-operator evasion sweep against the real firewall, with Wilson intervals and an anti-vacuity minimum-denominator guard | `run_evasion_sweep`, `flagged_payloads`, `OperatorEvasion`, `VacuousSweepError` |

## Real vs. Model Measurement

`AdversarialTrainer` runs in one of two modes (`ATConfig.measurement_mode`,
default `"model"`):

- **`model`** (default) reproduces the published §05g round-by-round AT table.
  Round detection rates are closed-form simulation constants (see the §05g
  "Status" note) — deterministic and reproducible, but not a pipeline
  measurement.
- **`real`** measures round detection rates against a **real** detector — the
  injected `detector` callable, or the real `CognitiveFirewall` on the real
  1475-sample `AttackCorpus`. It uses the modular, pure building blocks above
  (`measure_detection_rate`, `refine_thresholds`, `evaluate_adaptive_attacks`),
  so every number is a measured fraction, not a constant. Run it via
  `scripts/run_adversarial_training.py --measurement-mode real`.

> **Honest real-mode finding.** Against the standalone `CognitiveFirewall`,
> real-mode AT measures a corpus detection rate of ≈8% and shows **no
> measurable hardening** from threshold refinement (`delta_dr ≈ 0`), because the
> `config_thresholds` the trainer refines do not gate the firewall's
> `classify()`. Real-mode is thus a faithful *measurement* of the current
> detector; demonstrating real hardening would require wiring threshold
> refinement into an adjustable detector (e.g. the composed pipeline), which is
> future work. §05h reports the firewall-measured *evasion* results; §05g
> reports the design-model AT trajectory.

## Quick Usage

```python
# 1. Generate attacks across the adversary capability spectrum
from src.redteam.generator import AdversarialGenerator, OmegaLevel
gen = AdversarialGenerator(
    config_thresholds={"drift_threshold": 0.3, "anomaly_threshold": 0.5},
    omega_level=OmegaLevel.OMEGA_5_COORDINATED,
    seed=42,
)
attacks = gen.generate_batch(190)
avg_evasion = sum(a.heuristic_evasion_score for a in attacks) / len(attacks)

# 2. Run iterative adversarial training
from src.redteam import AdversarialTrainer, ATConfig, NashEquilibriumEstimator
trainer = AdversarialTrainer(ATConfig(n_rounds=5, seed=42))
trainer.run()
summary = trainer.summary()                 # baseline → hardened DR, delta per round
cumulative = [r.delta_dr for r in trainer.rounds]
increments = [cumulative[0]] + [
    cumulative[i] - cumulative[i - 1] for i in range(1, len(cumulative))
]
proj = NashEquilibriumEstimator(increments).projected_equilibrium_dr(
    trainer._baseline_dr
)

# 3. Measure mutation-operator evasion against the real firewall
from src.redteam.evasion import flagged_payloads, run_evasion_sweep
from src.redteam.generator import AttackMutator
from src.core.firewall import CognitiveFirewall, Classification
from src.attacks.corpus import AttackCorpus

firewall = CognitiveFirewall()
corpus = AttackCorpus.generate(seed=42)
denom = flagged_payloads(
    [s.payload for s in corpus],
    lambda p: firewall.classify(p) != Classification.ACCEPT,
)
sweep = run_evasion_sweep(
    denom,
    AttackMutator.MUTATION_OPERATORS,
    AttackMutator(seed=42).mutate_payload,
    lambda p: firewall.classify(p) != Classification.ACCEPT,
)
print(sweep["gradual_insertion"])  # 8/76, 10.5%, Wilson CI [5.4%, 19.4%]
```

## Manuscript Anchor

| Claim (§05h) | Implementation |
| ----- | -------------- |
| Attack generation across Ω₁–Ω₅ | `generator.AdversarialGenerator` |
| Mutation testing (12 operators) | `generator.AttackMutator` |
| Mutation-operator evasion rates vs. the real firewall | `evasion.run_evasion_sweep` / `evasion.flagged_payloads` |
| Adversarial training rounds and hardening (§05g) | `AdversarialTrainer` |
| Nash-equilibrium DR projection (§05g) | `NashEquilibriumEstimator` |

## Dependencies

- `numpy >= 1.22` (RNG, gradient/geometric arithmetic)
- `attacks.corpus` (the real 1475-sample `AttackCorpus` sweep denominator)
- `core.firewall` (`CognitiveFirewall` classification in the evasion sweep)

## Testing

Tests in `tests/test_redteam.py` (generator/trainer/estimator/convergence/evasion)
and `tests/test_redteam_convergence.py` verify:

- Higher-capability adversaries achieve higher mean self-estimated evasion scores.
- AT improves hardened detection rate monotonically and reproduces §05g deltas.
- The evasion sweep de-duplicates its denominator, refuses vacuous denominators,
  and its manuscript table cannot drift from the live measurement.

All tests use real numerical computation against the real firewall and corpus —
see [`../AGENTS.md`](../AGENTS.md) for the no-mocks policy. Reproduce the data
artifact with `scripts/run_redteam.py --seed 42`.