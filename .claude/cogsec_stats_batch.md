You are Claude Code in --print mode. Task: CONTINUED CODE QUALITY PASS on Part 2 computational modules.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET PROJECT: projects/cognitive_integrity/cogsec_multiagent_2_computational/

PREVIOUS WORK: Core 8 modules (detection, firewall, tripwire, sandbox, consensus, trust, provenance, invariants) already have:
- `from __future__ import annotations`
- Module docstrings
- Callable type hints fixed
- Constants extracted where obvious

NOW APPLY SAME STANDARDS to these subdirectories:
A. src/statistics/*.py (except __init__.py) — hypothesis, confidence, effect_size, stability, anova, regression, nonparametric, analysis_runner, assumptions, cross_validation, sensitivity, bayesian
B. src/evaluation/*.py (except __init__.py) — metrics, runner, precision_recall, benchmark, llm_evaluator, roc, scalability
C. src/data/*.py (except __init__.py) — generate, loaders, result_loaders, schema
D. src/attacks/*.py (except __init__.py and attacks/generators/* because those are many) — corpus, validation, templates (if simple); also attacks/generators/injection.py, belief_manipulation.py, coordination.py, trust_exploitation.py (the simpler generator modules)

CRITERIA per file:
1. Add `from __future__ import annotations` if missing (at top after docstring)
2. Ensure module-level docstring exists (1-2 sentences)
3. Add type hints to all public functions lacking them (use proper typing: Optional, List, Dict, Tuple, Callable, etc.)
4. Replace bare `except:` or `except Exception as e: pass` patterns with either specific exception types or at minimum `except Exception:` with a comment or logging
5. Extract magic numbers > 1000 or unclear thresholds into module-level constants (e.g., `_DEFAULT_TIMEOUT = 60`)
6. Add `logger = logging.getLogger(__name__)` if file uses logging but doesn't have logger

RESTRICTIONS:
- Do NOT modify attacks/generators/__init__.py or any complex generator files beyond the 4 listed — those are large; they will get a separate pass
- Do NOT modify visualization/ modules yet (separate pass for matplotlib issues)
- Do NOT modify formal/, colony/, architectures/, agents/, composition/, ablation/ yet
- Only Read/Edit/Write within the specified subdirs
- Keep diffs minimal; edit only what's necessary

OUTPUT:
For each file edited, emit exactly one block:

=== EDIT ===
File: <absolute path>
Type: <import-add|docstring|type-hints|error-handling|constant>
Diff:
@@ -<line_start>,5 +<line_start>,6 @@
 <context>
+<added>
-<removed>

At the end:

=== SUMMARY ===
Modules-Scanned: <A, B, C, D counts>
Modules-Modified: <count>
TopMissingDocstrings: <list any files that had none>
TopTypeGaps: <function names where types were added>
Constants-Added: <list>
Next-Batch: <what remains: visualization, formal, colony, architectures, agents, composition, ablation>

Use --max-turns 18 to complete this batch.
