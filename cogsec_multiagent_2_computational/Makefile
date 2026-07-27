.PHONY: all check-real-data data synthetic-data figures tables verify tests \
        evaluate lint format-check clean

# `comm`, `mktemp` and `trap` in the `clean` recipe need a POSIX-ish shell with
# predictable behaviour; pin it rather than inheriting whatever /bin/sh is.
SHELL := /bin/bash

# ---------------------------------------------------------------------------
# Toolchain
# ---------------------------------------------------------------------------
# The documented install is `uv sync`, which creates .venv but does NOT put it
# on PATH.  Bare `python`, `pytest` and `ruff` therefore do not resolve from a
# clean shell and every target that used them failed before it started.  Route
# through `uv run`, which resolves the project environment explicitly.
#
# Each variable stays overridable so a caller that already has an activated
# environment can substitute it, e.g.:
#     make tests PYTEST=.venv/bin/pytest
UV      ?= uv
PYTHON  ?= $(UV) run python
PYTEST  ?= $(UV) run pytest
RUFF    ?= $(UV) run ruff
GIT     ?= git
SCRIPTS  = scripts

# ---------------------------------------------------------------------------
# Real vs. synthetic data
# ---------------------------------------------------------------------------
# These five files are the *empirically measured* pipeline evidence the
# manuscript's headline numbers are computed from.  They are git-tracked.  The
# synthetic generator in src/data/generate.py writes files with the same names
# and a wildly different distribution (mean detection ~0.97 vs. the real
# ~0.45), so regenerating figures and tables on top of it silently flips
# published verdicts.  Nothing in the default build is allowed to overwrite
# them: `make all` reads them, and only the explicitly-named `synthetic-data`
# target produces placeholder data, into a separate directory.
REAL_DATA_DIR      ?= output/data
SYNTHETIC_DATA_DIR ?= output/data_synthetic

REAL_DATA_FILES = \
	$(REAL_DATA_DIR)/full_evaluation_results.json \
	$(REAL_DATA_DIR)/ablation_results.json \
	$(REAL_DATA_DIR)/colony_results.json \
	$(REAL_DATA_DIR)/cross_validation_results.json \
	$(REAL_DATA_DIR)/multi_seed_results.json

# ---------------------------------------------------------------------------
# Default: verify the tracked evidence, then rebuild everything derived from it
# ---------------------------------------------------------------------------
# Sub-makes rather than prerequisites so the ordering holds under `make -j`.
all:
	$(MAKE) check-real-data
	$(MAKE) verify
	$(MAKE) tests
	$(MAKE) figures
	$(MAKE) tables

# Fail loudly if the real evidence is absent or has been replaced by synthetic
# placeholder data.  This is the guard that makes `all` safe to run.
check-real-data:
	@missing=""; \
	for f in $(REAL_DATA_FILES); do \
	  if [ ! -f "$$f" ]; then missing="$$missing$$(printf '\n  %s' "$$f")"; fi; \
	done; \
	if [ -n "$$missing" ]; then \
	  { echo "ERROR: real-pipeline evidence is missing:$$missing"; \
	    echo ""; \
	    echo "These files are git-tracked publication evidence.  Restore them from"; \
	    echo "git, or regenerate them with the real experiment scripts listed in"; \
	    echo "REPRODUCE.md under 'Synthetic vs. Real Data'."; \
	    echo "Do NOT use 'make synthetic-data' -- it produces placeholder numbers."; \
	  } >&2; \
	  exit 1; \
	fi
	@$(PYTHON) -c 'import json, sys; docs = [(p, json.load(open(p))) for p in sys.argv[1:]]; declared = {p: d["data_origin"] for p, d in docs if isinstance(d, dict) and "data_origin" in d}; bad = sorted(p for p, o in declared.items() if o != "real_pipeline"); sys.exit("ERROR: these files are not real-pipeline evidence: " + ", ".join(bad)) if bad else None; sys.exit("ERROR: none of the required files declare data_origin, so the provenance check would be vacuous; expected at least 2 of: " + ", ".join(sys.argv[1:])) if len(declared) < 2 else None; print("check-real-data: " + str(len(docs)) + " files present, " + str(len(declared)) + " declare data_origin=real_pipeline")' $(REAL_DATA_FILES)

# Removed on purpose: `make data` used to overwrite the tracked real-pipeline
# evidence with synthetic placeholders, and `all` depended on it.
data:
	@{ echo "ERROR: 'make data' has been removed because it overwrote the tracked"; \
	   echo "real-pipeline evidence in output/data/ with synthetic placeholders."; \
	   echo ""; \
	   echo "  make synthetic-data   schema-compliant PLACEHOLDER data ->"; \
	   echo "                        $(SYNTHETIC_DATA_DIR)/ (never output/data/)"; \
	   echo "  make all              verify + tests + figures + tables from the"; \
	   echo "                        real data already in output/data/"; \
	   echo ""; \
	   echo "For empirically measured data see REPRODUCE.md, 'Synthetic vs. Real Data'."; \
	 } >&2; exit 1

# Schema-compliant PLACEHOLDER data.  Written to its own directory so it can
# never be mistaken for, or overwrite, the measured results.
synthetic-data:
	@echo "Writing SYNTHETIC placeholder data to $(SYNTHETIC_DATA_DIR)/"
	@echo "(placeholder distributions -- not empirically measured; see REPRODUCE.md)"
	$(PYTHON) $(SCRIPTS)/generate_all_data.py --output $(SYNTHETIC_DATA_DIR)

# Generate all 8 manuscript figures from whatever is in output/data/.
figures:
	$(PYTHON) $(SCRIPTS)/generate_all_figures.py

# Generate LaTeX tables from whatever is in output/data/.
tables:
	$(PYTHON) $(SCRIPTS)/generate_all_tables.py

# Verify manuscript integrity
verify:
	$(PYTHON) $(SCRIPTS)/verify_manuscript.py --root manuscript

# Run full test suite
tests:
	$(PYTEST) tests/ -v

# Run evaluation experiments
evaluate:
	$(PYTHON) -m src evaluate --seed 42

# Lint Python sources
lint:
	$(RUFF) check src/ scripts/ tests/

# Formatting check.  Advisory: the tree is not `ruff format`-clean yet, so this
# is deliberately not part of `all` or `lint`.
format-check:
	$(RUFF) format --check src/ scripts/ tests/

# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------
# `rm -rf output/` deleted 43 git-tracked publication artifacts and no target
# restored them.  Only untracked, regenerable files are removable here; git is
# the authority on which those are.  Run with DRY_RUN=1 to list without
# deleting.
clean:
	@set -euo pipefail; \
	if ! $(GIT) rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
	  echo "clean: not inside a git work tree; refusing to guess which artifacts are tracked" >&2; \
	  exit 1; \
	fi; \
	verb="removed"; if [ -n "$${DRY_RUN:-}" ]; then verb="would remove"; fi; \
	tracked=$$(mktemp); present=$$(mktemp); \
	trap 'rm -f "$$tracked" "$$present"' EXIT; \
	$(GIT) ls-files -- output | LC_ALL=C sort > "$$tracked"; \
	{ find output -type f 2>/dev/null || true; } | LC_ALL=C sort > "$$present"; \
	n=0; \
	while IFS= read -r f; do \
	  [ -n "$$f" ] || continue; \
	  if [ -n "$${DRY_RUN:-}" ]; then echo "would remove $$f"; else rm -f "$$f"; fi; \
	  n=$$((n + 1)); \
	done < <(comm -23 "$$present" "$$tracked"); \
	echo "clean: $$verb $$n untracked file(s) under output/"; \
	echo "clean: kept $$(wc -l < "$$tracked" | tr -d ' ') tracked file(s) under output/"; \
	if [ -n "$$($(GIT) ls-files -- manuscript_verification.log)" ]; then \
	  echo "clean: manuscript_verification.log is git-tracked; leaving it in place"; \
	elif [ -n "$${DRY_RUN:-}" ]; then \
	  echo "would remove manuscript_verification.log"; \
	else \
	  rm -f manuscript_verification.log; \
	fi
	@if [ -z "$${DRY_RUN:-}" ]; then \
	  find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true; \
	  find . -name "*.pyc" -delete 2>/dev/null || true; \
	  rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov; \
	else \
	  echo "would remove: __pycache__ dirs, *.pyc, .pytest_cache, .ruff_cache, .mypy_cache, htmlcov"; \
	fi
