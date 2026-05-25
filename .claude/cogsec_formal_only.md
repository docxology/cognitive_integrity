You are Claude Code in --print mode. Task: FORMAL MODULES QUALITY PASS — Part 2 computational project.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/formal/

FILES (13 modules):
theorem_registry.py, latency_bound.py, stealth_impact.py, free_energy.py, trust_bounds.py,
tla_spec.py, category_theory.py, spin_spec.py, nusmv_spec.py, byzantine_guarantees.py,
spec_verifier.py, composition_proofs.py, __init__.py

ACTIONS PER FILE:
1. Add `from __future__ import annotations` if absent (top after docstring)
2. Add/strengthen module docstring: explain which formal method (TLA+, Spin, NuSMV, category theory) and which Part 1 theorem/definition it implements
3. Add type hints to all public functions; use proper types from typing (Callable, Literal, TypedDict where appropriate)
4. Replace any bare `except:` with `except Exception:` (these formal modules rarely have try/except but check)
5. Extract magic numbers (tolerance epsilon=1e-6, timeout seconds, bound values) to ALL_CAPS module constants with comments
6. If a module loads spec files from disk, validate path handling (use pathlib.Path)

RULES:
- Do NOT modify algorithmic logic; only typing, documentation, constants
- Keep changes minimal; skip modules that already fully comply

OUTPUT exactly:

=== EDIT ===
File: <path>
Type: <import-add|docstring|type-hints|constant|error-handling>
Diff:
@@ -<start>,5 +<start>,6 @@
 <context>
+<added>
-<removed>

At end:

=== FORMAL SUMMARY ===
Scanned: 13 (list which had no edits)
Modified: <count>
Types-Added: <count>
Docs-Enhanced: <count>
Constants: <list names>
Next: colony/, utils/, architectures/, agents/, composition/, ablation/

Use --max-turns 15, --model haiku, budget $1.5.
