# Red-Team Evaluation and Adversarial Training

**Red-team evaluation** probes CIF defenses by generating adversarial attacks and
measuring how often they evade detection. **Adversarial training (AT)** iterates
attack generation → detection measurement → threshold refinement. This guide
covers both, implemented in `src/redteam/` and driven by `scripts/run_redteam.py`
and `scripts/run_adversarial_training.py`.

## Quick start

```bash
# Firewall-measured mutation-operator evasion sweep (real pipeline, seed 42)
uv run python scripts/run_redteam.py --seed 42
#   -> output/data/redteam_evaluation_results.json  (data_origin: real_pipeline)

# Adversarial training round table (closed-form design model, matches §05g)
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42
#   -> output/data/adversarial_training_results.json

# Adversarial training measured against the real firewall + corpus (real mode)
uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42 \
    --measurement-mode real
```

## What the red-team sweep measures

`src/redteam/evasion.py` scores the **real `CognitiveFirewall`** over the real
950-sample `AttackCorpus`. For each of the 12 mutation operators it reports how
many distinct flagged payloads the operator converts into accepted ones, with a
Wilson confidence interval and a minimum-denominator anti-vacuity guard:

```python
from redteam.evasion import flagged_payloads, run_evasion_sweep
from redteam.generator import AttackMutator
from core.firewall import CognitiveFirewall, Classification
from attacks.corpus import AttackCorpus

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
print(sweep["gradual_insertion"])  # 3/66, 4.5%, Wilson CI [1.6%, 12.5%]
```

The denominator is **de-duplicated** (distinct flagged payloads), so repeated
template copies cannot inflate the sample size. A uniformly-zero result is a
legitimate finding; it is reported with its denominator and interval.

## Real vs. model adversarial training

`AdversarialTrainer` runs in two modes (`ATConfig.measurement_mode`):

| Mode | What it measures | Provenance |
| ---- | ---------------- | ---------- |
| `model` (default) | Closed-form round detection rates — reproduces the §05g table | `source_script` + `seed` (deliberately **no** `data_origin`) |
| `real` | Round detection rates against the real `CognitiveFirewall` and `AttackCorpus` | `data_origin: real_pipeline` + `detector` |

Real mode uses the modular, deterministic building blocks in `src/redteam/`
(`measure_detection_rate`, `refine_thresholds`, `evaluate_adaptive_attacks`).
**Honest real-mode result:** against the standalone firewall it measures a
corpus detection rate of ≈8% and shows no measurable hardening from threshold
refinement, because the trainer's `config_thresholds` do not gate the firewall's
`classify()`. Demonstrating real hardening requires wiring refinement into an
adjustable detector (e.g. the composed pipeline) — future work.

## Manuscript binding

- §05h (`manuscript/05h_redteam_evaluation.md`) reports the firewall-measured
  mutation sweep. `tests/test_redteam.py` parses its table and compares it to the
  live sweep, so the manuscript cannot drift from the data.
- §05g (`manuscript/05g_adversarial_training.md`) reports the design-model AT
  trajectory; `tests/test_redteam.py` also binds its round table to the trainer.

## Notes

- Every value is deterministic at a fixed seed; re-running at the same seed
  reproduces the artifact byte-for-byte.
- No mocks anywhere — tests score the real firewall and corpus.
- See [`../claims_traceability.md`](../claims_traceability.md) and
  [`src/redteam/`](../../src/redteam/README.md) for the module map.