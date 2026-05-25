You are performing a SYSTEMATIC CODE QUALITY & ARCHITECTURE AUDIT on cognitive_integrity. This is a four-part research program on Cognitive Security for Multiagent Operators.

WORKING DIRECTORY: /Users/4d/Documents/GitHub/template/projects/cognitive_integrity/
PROVIDED CONTEXT: The project structure has been discovered — you have full read access.

YOUR MISSION — Scan ALL FOUR PARTS and produce:

1. ARCHITECTURAL HEALTH CHECK
   - For each part, verify pyproject.toml has correct coverage threshold (fail_under = 90)
   - Check that no src/ module imports from another part's src/ (enforce isolation)
   - Verify each part's src/__init__.py is either empty or re-exports cleanly
   - Check for circular imports within each part's src/ tree
   - Validate that scripts/ (if present) are thin orchestrators calling src/

2. CODE QUALITY INVENTORY
   - For every .py file in src/ across all 4 parts, note:
     * Missing type hints on public functions (annotate with proper types)
     * Missing or inadequate docstrings (Google/NumPy style required)
     * Bare `except:` clauses that need specific exception types
     * Magic numbers that should be module-level constants
     * Missing logger = logging.getLogger(__name__)
   - Prioritize: core modules (trust, firewall, detection, provenance, invariants) first

3. TEST SUITE DIAGNOSTIC
   - Run pytest --collect-only on each part to count tests
   - Read pyproject.toml coverage config — is 90% enforced?
   - Scan conftest.py fixtures for state leakage (module-level fixtures, caching)
   - Look for any unittest.mock usage — should be nearly zero (data-only rule)
   - Note any skip/xfail markers and reasons

4. MANUSCRIPT INTEGRITY (Parts 1–3)
   - List manuscript/ directory contents
   - Read manuscript/config.yaml — verify sections array matches files
   - Scan all .md files for stale narrative markers (TODO, FIXME, XXX, UPDATE_ME)
   - Check preamble.md for LaTeX packages and figure setup
   - Count figures referenced vs. defined in src/visualization

5. VISUALIZATION PIPELINE CHECK (Parts 1 & 2)
   - Identify all matplotlib usage — check for plt.close() to avoid memory leaks
   - Look for hardcoded figure sizes that need adjustment for publication
   - Verify colormaps — no jet, use viridis/plasma/cividis
   - Check for `plt.show()` calls — must be removed or gated behind __main__ guard

6. QUICK-WINS REFACTORING (implement immediately)
   - Add missing `from __future__ import annotations` to every src/ module that lacks it
   - Add top-level module docstrings to any src/*.py without them
   - Extract any magic numbers > 3 digits or unclear formulas into named constants
   - Fix all `except:` to `except Exception:` at minimum, or specific types
   - Add `if __name__ == "__main__":` guards around demonstration code

7. SECURITY SCAN (automated)
   - Search src/ for "password", "api_key", "token", "secret" literals
   - Flag any eval(), exec(), pickle.loads() without sandboxing
   - Check path construction — ensure no user input directly in open() without validation

DELIVERABLE FORMAT:

For EVERY MODIFICATION you make, emit:

=== MODIFIED FILE ===
Path: /absolute/path/to/file.py
Change-Type: [type-hints | docstring | constant-extraction | error-handling | import-fix | security]
Lines-Affected: N
Reason: <one-sentence why>
Before-Snippet:
  <up to 10 lines showing what changed>
After-Snippet:
  <up to 10 lines showing result>

For ARCHITECTURAL FINDINGS (no code change), emit:

=== ARCHITECTURE NOTE ===
Part: <cogsec_multiagent_X_…>
Severity: [CRITICAL|HIGH|MEDIUM|LOW]
Topic: <import-isolation|coverage-config|thin-orchestrator|circular-dependency|etc.>
Location: <specific file or directory>
Issue: <concise description>
Fix: <recommended action, ideally with exact command or code change>

At the end, emit:

=== SUMMARY REPORT ===
Parts-Scanned: 1,2,3,4
Files-Reviewed: <total>
Files-Modified: <count> (breakdown by change-type)
Critical-Issues-Fixed: <count>
Test-Impact: <did we improve testability? which tests now pass?>
Manuscript-Impact: <which manuscript sections now validate?>
Performance-Notes: <any hot paths identified?>
Remaining-Work: <what needs deeper investigation or human review?>

Start with Part 2 (largest, 1700+ tests), then scan Parts 1, 3, 4 in order. Use --max-turns 30 to stay within budget. Do NOT launch long-running subprocesses — just static analysis with Read tool and targeted edits. If a test fails to collect or a file cannot be parsed, note it and move on.

Begin now.
