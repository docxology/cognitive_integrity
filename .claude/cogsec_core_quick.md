You are Claude Code in --print mode. Task: QUICK CODE QUALITY PASS on 8 core computational modules.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/core/

MODULES:
- detection.py
- firewall.py
- tripwire.py
- sandbox.py
- consensus.py
- trust.py
- provenance.py
- invariants.py

ACTIONS (apply to each file):
1. Add `from __future__ import annotations` if missing (top of file)
2. Add module-level docstring if missing or weak (explain purpose in 1 sentence)
3. Add type hints to all public functions that lack them
4. Strengthen docstrings: every function needs Args and Returns sections (Google style)
5. Replace bare `except:` with `except Exception:` (or specific if obvious like ValueError)
6. Extract any magic numbers/strings into module-level constants with clear names

RULES:
- Read file first, then propose minimal edits
- Only edit inside the TARGET directory
- Do NOT change function logic or signatures beyond adding types
- Keep diffs tiny — show hunks of ±10 lines max

OUTPUT FORMAT per file edited:

=== EDIT ===
File: projects/cognitive_integrity/cogsec_multiagent_2_computational/src/core/<module>.py
Type: [import-add|docstring|type-hints|error-handling|constant]
Change Summary: <one line>
Diff:
@@ -<line_start>,5 +<line_start>,6 @@
 <context lines>
+<added line>
-<removed line>

FINALLY, produce:

=== SUMMARY ===
Files-Scanned: 8
Files-Modified: <count>
Edits-by-Type: <dict>
Estimated-Test-Impact: <should coverage increase?>
Next-Steps: <which other modules get same treatment?>

Start. Use --max-turns 12. No subprocesses except pytest --collect-only if needed.
