You are Claude Code in --print mode. Task: VISUALIZATION & MANUSCRIPT PIPELINE QUALITY PASS.

WORKDIR: /Users/4d/Documents/GitHub/template
TARGET: projects/cognitive_integrity/cogsec_multiagent_2_computational/

SCOPE:
A. src/visualization/figures/*.py (all figure generation modules)
B. src/visualization/tables/*.py (all table generation modules)
C. src/manuscript/*.py (injector.py, verifier.py, latex_converter.py)

ACTIONS per file:
1. Matplotlib safety: ensure Agg backend is set or no `plt.show()` calls remain
2. Memory management: check each figure function calls `plt.close(fig)` or uses context manager
3. Color palette: flag use of 'jet' colormap; recommend 'viridis' or 'cividis'
4. Font/DPI: verify explicit rcParams or savefig(..., dpi=300) for publication
5. API consistency: see if functions return (fig, ax) or save to path — unify if inconsistent
6. Docstrings: add Google style if missing, explain return values and output location
7. Constants: extract hardcoded figure sizes (e.g., (12, 8)) into named module constants
8. Type hints: verify Callable types where functions are passed as arguments

For manuscript modules:
- Check that injector.py reads manuscript variables correctly
- Verify verifier.py checks required sections exist
- Ensure latex_converter.py handles math environments safely

OUTPUT per edited file: structured diff as before.

Also scan for any `import seaborn as sns` and verify sns.set_style("whitegrid") or similar consistent styling.

At end, report:

=== VIZ SUMMARY ===
Modules-Scanned: <count>
Edits-Made: <count>
Colormap-Issues: <count> (jet → viridis replacements)
Memory-Leaks-Fixed: <count> (missing plt.close())
API-Changes: <list files with return signature improvements>
Manuscript-Tools: <status of injector/verifier>

Use --max-turns 20, --model haiku, budget $2.
