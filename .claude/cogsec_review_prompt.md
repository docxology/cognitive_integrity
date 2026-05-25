You are performing a DEEP CODE REVIEW and SYSTEMATIC IMPROVEMENT pass on the cognitive_integrity multi-part research project. This is a multi-paper series on Cognitive Security for Multiagent Operators.

TARGET: /Users/4d/Documents/GitHub/template/projects/cognitive_integrity/

PARTS (4 independent projects sharing a program directory):
1. cogsec_multiagent_1_theory — formal foundations (20 visualization modules, 8 core modules, manuscript with 9 sections)
2. cogsec_multiagent_2_computational — empirical validation (1700+ tests, stats, formal proofs, attack corpus, ablation, evaluation)
3. cogsec_multiagent_3_practical — deployment guides (industrial translation)
4. cogsec_multiagent_4_applications — cross-domain applications (WIP)

REVIEW & IMPROVEMENT MANDATE:

PHASE A — ARCHITECTURAL AUDIT
  - Verify project isolation compliance: no cross-project imports between parts
  - Check each pyproject.toml for correct dependencies, coverage thresholds, pytest config
  - Validate thin-orchestrator pattern: scripts/ only import from src/ and infrastructure/
  - Scan for circular dependencies within each src/ tree
  - Review package structure: __init__.py exports, module cohesion

PHASE B — CODE QUALITY (apply universally)
  - Add type hints to all public functions lacking them (runtime checkable)
  - Strengthen docstrings: every public module, class, function needs Google/NumPy style with Args/Returns/Raises
  - Replace bare `except:` with specific exception types
  - Identify and extract magic numbers/strings to constants with clear names
  - Check for consistent logging usage (import logging; logger = logging.getLogger(__name__))
  - Ensure deterministic random seeds (utils/random_seed.py usage)
  - Validate error handling: no silent failures, all errors surface with context

PHASE C — TEST SUITE HEALTH
  - Each test file: verify 90%+ coverage actually met (read pytest.ini options, compare against current coverage reports if any)
  - Check for test isolation (no shared state between tests)
  - Ensure fixtures in conftest.py don't leak state
  - Verify test naming follows test_*.py pattern and functions test_*
  - Look for TODOs/FIXMEs in tests indicating known gaps
  - Check for mocks — any use of unittest.mock should be justified (infrastructure rule: zero mocks for data)

PHASE D — MANUSCRIPT & RENDERING INTEGRITY (Parts 1–3 have manuscripts)
  - Verify all manuscript sections exist per config.yaml
  - Check cross-references: figures, equations, sections use stable labels (not hardcoded numbers)
  - Validate references.bib: all citations defined, no broken keys
  - Ensure figures/table generation scripts in src/visualization or src/manuscript connect to manuscript
  - Check for stale narrative: superseded claims, outdated citations, deprecated terminology

PHASE E — VISUALIZATION & FIGURE PIPELINE (Parts 1 & 2)
  - All matplotlib figures: check for headless-safe configuration (Agg backend)
  - Verify fonts, DPI, and size settings meet publication standards
  - Ensure each figure function returns fig, ax or saves to correct output path
  - Validate color palettes are colorblind-friendly and print-safe
  - Check for memory leaks in figure generation (plt.close() usage)

PHASE F — DATA & STATISTICS (Part 2)
  - Statistical tests: verify assumptions checked before application
  - Confidence intervals reported with effect sizes
  - Multiple testing corrections applied (Bonferroni, FDR)
  - Data loaders validate schema and handle missing/corrupt data
  - Attack corpus integrity: no PII, synthetically generated, license-compatible

PHASE G — FORMAL METHODS (Part 2)
  - Formal specs: TLA+, NuSMV, Spin — ensure spec files exist and are syntactically valid
  - Theorem registry: all formal claims mapped to proofs/verdicts
  - Category theory abstractions: verify monoid/group laws actually hold in code

PHASE H — SECURITY & SAFETY
  - No hardcoded credentials or API keys
  - Input validation on all public entry points (functions that accept external data)
  - Check for unsafe deserialization (pickle, eval, exec)
  - Path traversal protection if filesystem access is parameterized
  - Dependency scan for known vulnerabilities (outdated versions in pyproject.toml)

PHASE I — PERFORMANCE & SCALABILITY
  - Identify O(n²) or worse algorithms in hot paths (trust network propagation, detection loops)
  - Vectorization opportunities: replace Python loops with numpy operations
  - Parallelization potential: concurrent.executor or multiprocessing usage
  - Memory usage patterns: large arrays copied unnecessarily?
  - Caching strategies: @functools.lru_cache on expensive pure functions

PHASE J — DOCUMENTATION HOLES
  - README.md in each part describes installation, usage, reproduction steps?
  - AGENTS.md present in each part? If not, create minimal one with project overview, key commands, file layout
  - SKILL.md presence? (Optional but recommended for agent routing)
  - In-code documentation: module-level docstrings explaining purpose and containing examples?
  - Any undocumented public APIs?

ACTIONABLE OUTPUT FORMAT:

For EACH file you modify, output:
1. FILE: <absolute path>
   CHANGE: <category: type-hints | docstring | error-handling | refactor | constant-extraction | import-reorder>
   REASON: <concise why>
   FIRST_10_LINES: <show first 10 lines of changed file snippet>
   <OPTIONAL: full diff or relevant code block showing before/after>

For ARCHITECTURAL issues, output:
ISSUE: <category> — <location>
SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW]
RECOMMENDATION: <specific actionable steps>
CITATION: <file path and line numbers if applicable>

Create a summary report at the end with:
- Total files reviewed
- Files modified (by category)
- Critical issues found and fixed
- Test improvements implemented
- Documentation gaps filled
- Performance wins achieved
- Any remaining known limitations

START scanning from the most complex part (cogsec_multiagent_2_computational) and work through all 4 parts systematically. Prioritize fixes that unblock testing and manuscript rendering.

You have full Read access across all files. Use --max-turns 40 to ensure thoroughness. Estimate: 1700+ tests in Part 2 alone plus manuscript generation — take the turns you need.
