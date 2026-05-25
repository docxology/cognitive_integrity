You are Claude Code operating in --print mode. Task: perform a RAPID CODE QUALITY SWEEP on the computational validation part of the Cognitive Integrity project.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET PROJECT: projects/cognitive_integrity/cogsec_multiagent_2_computational/

SCOPE (limited, high-impact):
1. Type hints: add to any src/ module missing them on public functions
2. Docstrings: ensure every public function has at least a one-line description plus Args/Returns
3. Bare excepts: replace `except:` with `except Exception:` (or specific types if obvious)
4. Magic numbers: extract literals > 1000 or cryptic formulas into named constants
5. Test collection: run pytest --collect-only to verify all tests are discovered
6. Coverage config: read pyproject.toml, confirm fail_under = 90
7. Security: scan for "password|api_key|secret|token" hardcoded strings in src/

RULES:
- Only modify files in the TARGET PROJECT (cogsec_multiagent_2_computational)
- Use Read to inspect files before editing
- Edits must be minimal and precise
- For each edit, output a structured diff:

=== EDIT ===
File: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/<module>.py
Type: <type-hints|docstring|error-handling|constant>
Change Summary: <one line>
Diff:
@@ -<old_line>,X +<new_line>,X @@
 <context>
-<removed>
+<added>

At the end, emit:

=== REPORT ===
Files-Scanned: <count>
Files-Modified: <count>
Edits-by-Category: {…}
Tests-Discovered: <count from pytest --collect-only>
Coverage-Required: 90 (from pyproject.toml)
Security-Flags: <list any red flags>
Outstanding-Issues: <what needs human attention>

GO. Use --max-turns 20.
