You are Claude Code in --print mode. Task: COMPLETE REMAINING PART 2 MODULES QUALITY PASS.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/

ALREADY DONE: core/, statistics/, evaluation/, data/, attacks/generators (selected), visualization/figures, visualization/tables, manuscript/

REMAINING MODULES TO PROCESS:
Category | Directories
---------|------------
Formal   | formal/ (theorem_registry, latency_bound, stealth_impact, free_energy, trust_bounds, tla_spec, category_theory, spin_spec, nusmv_spec, byzantine_guarantees, spec_verifier, composition_proofs)
Colony   | colony/ (sybil_infiltration, benchmark, quorum_manipulation, emergent_misalignment, scorecard, recruitment_poisoning, belief_cascade)
Utils    | utils/ (config, types, timing, random_seed, logging_setup)
Arch     | architectures/ (crewai, autogpt, langgraph, base, claude_code)
Agents   | agents/ (llm_agent, multiagent_system)
Compose  | composition/ (algebra, factory, pipeline, fusion, adapters)
Ablation | ablation/ (runner, component_removal, synergy, minimal_config)

ACTIONS for EVERY FILE in these dirs (except __init__.py):
1. Add `from __future__ import annotations` if absent (after docstring)
2. Ensure module docstring exists (1–2 sentences, explains purpose and Part 1 connection)
3. Add type hints to all public functions missing them (proper typing imports)
4. Replace bare `except:` with `except Exception:` or specific types
5. Extract magic numbers > 1000 or cryptic formulas into ALL_CAPS constants with comments
6. For logging usage: ensure `logger = logging.getLogger(__name__)` pattern
7. For utils/types.py: review TypedDict definitions, ensure completeness

RESTRICTIONS:
- Do NOT change algorithmic logic; only typing, docs, constants
- Keep diffs minimal
- If a file already clearly has all these, skip after noting "already compliant"

PROGRESS REPORTING:
Every ~5 files processed, emit:
  Progress: <dir>/<module>.py — <changes count>

FINAL REPORT:
=== PART2 REMAINING SUMMARY ===
Modules-Scanned: <total>
Modified: <count>
By-Category: {formal: X, colony: Y, utils: Z, arch: A, agents: B, compose: C, ablation: D}
Type-Hints-Added: <count>
Docstrings-Added/Enhanced: <count>
Constants-Extracted: <list (name: value)>
Files-Already-Perfect: <list>
Next-Priority: <any remaining critical gaps?>

Start with formal/ (most mathematically critical), then colony, utils, arch, agents, composition, ablation in that order.

Use --max-turns 40, --model haiku, budget $3.0. Go.
