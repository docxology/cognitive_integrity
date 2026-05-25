You are Claude Code in --print mode. Task: FORMAL / ADVERSARIAL / UTILS QUALITY PASS (Part 2).

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/

SCOPE:
A. src/formal/*.py (except __init__.py) — theorem_registry, latency_bound, stealth_impact, free_energy, trust_bounds, tla_spec, category_theory, spin_spec, nusmv_spec, byzantine_guarantees, spec_verifier, composition_proofs
B. src/colony/*.py (except __init__.py) — sybil_infiltration, benchmark, quorum_manipulation, emergent_misalignment, scorecard, recruitment_poisoning, belief_cascade
C. src/utils/*.py (except __init__.py) — config, types, timing, random_seed, logging_setup

ACTIONS per file:
1. Add `from __future__ import annotations` if missing
2. Ensure module docstring exists (explain the formal model or utility purpose)
3. Add type hints to all public functions (especially critical in types.py, config.py)
4. Fix bare `except:` → `except Exception:` or specific types
5. Extract any magic literals (default thresholds, timeouts, numeric tolerances) to constants
6. Check logger usage in utils/logging_setup.py — verify getLogger(__name__) pattern
7. In formal modules: ensure docstrings cite the formal property being implemented (e.g., "Implements Theorem 3.1 from Part 1")
8. In random_seed.py: verify deterministic seeding across numpy/random

RESTRICTIONS:
- No edits to architecture/, agents/, composition/, ablation/, attacks/ (already done)
- Keep changes purely mechanical; do not alter formal logic or algorithm semantics

OUTPUT: Same structured diffs per file. At the end:

=== FORMAL/COLONY/UTILS SUMMARY ===
Total-Scanned: <A+B+C counts>
Modified: <count>
Type-Hints-Added: <count>
Docstrings-Added: <count>
Constants: <list>
Formal-Doc-Enhancements: <which modules got theorem citations>
Remaining-Modules: <list modules NOT yet touched in Part 2: architectures/, agents/, composition/, ablation/>

Use --max-turns 20, --model haiku, budget $2.
