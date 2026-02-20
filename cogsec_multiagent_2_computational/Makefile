.PHONY: all data figures tables verify tests evaluate lint clean

PYTHON ?= python
PYTEST ?= pytest
SCRIPTS = scripts

# Default: full reproducible pipeline
all: data figures tables verify

# Generate seed datasets for schema validation
data:
	$(PYTHON) $(SCRIPTS)/generate_all_data.py

# Generate all 8 manuscript figures (depends on data)
figures: data
	$(PYTHON) $(SCRIPTS)/generate_all_figures.py

# Generate LaTeX tables from results
tables: data
	$(PYTHON) $(SCRIPTS)/generate_all_tables.py

# Verify manuscript integrity
verify:
	$(PYTHON) $(SCRIPTS)/verify_manuscript.py --root manuscript

# Run full test suite
tests:
	$(PYTEST) tests/ -v

# Run evaluation experiments (depends on data)
evaluate: data
	$(PYTHON) -m src evaluate --seed 42

# Lint Python sources
lint:
	ruff check src/ scripts/ tests/

# Clean generated artifacts
clean:
	rm -rf output/
	rm -rf manuscript_verification.log
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
