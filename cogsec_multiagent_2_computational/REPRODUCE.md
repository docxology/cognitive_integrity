# Reproducibility Guide

## System Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
# Clone repository
git clone https://github.com/docxology/cognitive_integrity.git
cd cognitive_integrity/cogsec_multiagent_2_computational

# Install dependencies
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

## Full Pipeline

```bash
make all
```

This runs: `data -> figures -> tables -> verify`

## Individual Targets

| Command | Description |
|---------|-------------|
| `make data` | Generate synthetic evaluation data |
| `make figures` | Generate all 8 manuscript figures |
| `make tables` | Generate LaTeX tables |
| `make verify` | Verify manuscript integrity |
| `make tests` | Run full test suite |
| `make evaluate` | Run evaluation experiments |
| `make lint` | Lint Python sources |
| `make clean` | Remove generated artifacts |

## Expected Outputs

- `output/figures/` -- 8 PDF + PNG figure pairs
- `output/tables/` -- LaTeX table files
- `output/data/` -- Generated evaluation data (JSON)

## Runtime Notes

- Figure generation uses a headless matplotlib backend (`Agg`)
- Tests use deterministic seeds for reproducibility
- The full pipeline (`make all`) requires no GPU
