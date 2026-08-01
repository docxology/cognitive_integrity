# `src/redteam/` — Agent Reference

Guidance for agents modifying the adversarial training and red-team evaluation package.

## Purpose

Adversarial evaluation layer over the core CIF defenses: Ω₁–Ω₅ conditioned
attack generation, iterative adversarial training (AT), and real-firewall
mutation-operator evasion measurement. See [`README.md`](README.md) for the API
map and manuscript anchors (§05g / §05h).

## Modules

### `generator.py`

`AdversarialGenerator` emits attacks conditioned on a defense configuration and
an `OmegaLevel`. `AttackMutator` applies 12 mutation operators to an attack
(public `mutate_payload(str, op)` entry used by the corpus sweep).

- Evasion score is a **design heuristic** based on Ω level, mutation bonus, and
  threshold penalty — it is *not* a firewall-measured rate. Keep that distinction
  explicit in any prose that cites it.
- `attack_id` is a SHA-256 digest; generation is deterministic at a fixed seed.

### `evasion.py`

The only part of this package that measures the *real* firewall:

- `flagged_payloads` de-duplicates the scanned corpus, so the denominator counts
  distinct payloads, not repeated template copies.
- `run_evasion_sweep` reports each operator's successes/attempts with a Wilson
  interval and raises `VacuousSweepError` below `DEFAULT_MIN_DENOMINATOR` (50).
  A uniformly-zero result is a legitimate finding — never "fix" it, but report it
  with its denominator and interval.
- `mutate` is `(payload, operator) -> payload`; `is_flagged` returns True for
  anything the firewall does not `ACCEPT`.

### `__init__.py` / `convergence.py`

`AdversarialTrainer` and the convergence estimators in `convergence.py` model
AT dynamics. Their threshold updates and gap attributions are **simulated**
round math keyed to `BASELINE_DR` and `ROUND_GAP_ATTRIBUTION`, not a trained
model — do not present them as empirically fitted ML.

## Rules

- **Deterministic** — all entry points accept `seed` (default 42).
- **Real measurement where claimed** — only the `evasion.py` sweep against
  `core.firewall.CognitiveFirewall` is a firewall-measured result. The generator
  self-score and the AT simulation must be labelled as such in any manuscript or
  doc prose.
- **No mocks** — test against the real `AttackCorpus` and `CognitiveFirewall`.
- **Manuscript anchored** — non-trivial exports carry docstring refs to Paper 2
  §05g / §05h.
- **Pinned to data** — after any change to the corpus, firewall, or operators,
  re-run `scripts/run_redteam.py --seed 42`, re-derive the `manuscript/05h*`
  mutation table, and confirm `tests/test_redteam.py` (which binds the two) is
  green.

## When Editing

- Update [`README.md`](README.md) for any API change.
- Update [`../README.md`](../README.md) subpackage map and
  [`../../docs/claims_traceability.md`](../../docs/claims_traceability.md) if you
  add a claim-backing function.
- Add tests in `tests/test_redteam.py` / `tests/test_redteam_convergence.py`.
- Regenerate the artifact with `scripts/run_redteam.py --seed 42`.

## Cross-Paper Reference

The merged Part 3+4 paper (`friedman2026cogsec3`) §4.2 practitioner red-team
checklists and §5.3.2 incident-response integration consume the evasion findings
produced here.