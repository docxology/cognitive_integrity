# `src/` — Agent Reference (Paper 2)

Source-package guidance for agents modifying the Cognitive Integrity Framework (CIF) computational validation codebase (Paper 2 of the three-part series).

## Series Position

This codebase is the **authoritative CIF implementation** — Papers 1, 3, and 4 of the *Cognitive Security for Multiagent Operators* series all cite this package. Do not break the manuscript-to-code anchor.

- Part 1 (`friedman2026cogsec1`) defines the apparatus; this `src/` implements it.
- Part 3 (`friedman2026cogsec3`) is the practitioner's guide; its §3 "Evidence" chapter cites **this package's headline metrics**.
- Part 3+4 (`friedman2026cogsec3`) applies CIF to ten domains; its sections 9–10 methodology validation-anchors to **this package's benchmarks**.

**Do not** mischaracterize Paper 3 as "biological" or "eusocial" — that content is in Paper 1's S02 supplementary. Paper 3 = practitioner's qualitative review.

## Package Structure

See [`README.md`](README.md) for the full subpackage map. Every subpackage has its own `README.md` + `AGENTS.md`.

## Import Conventions

```python
# Top-level re-exports (preferred for brevity)
from src import TrustCalculus, CognitiveFirewall, ByzantineConsensus

# Subpackage imports (preferred for specialized APIs)
from src.core.trust import TrustMatrixWithDecay
from src.attacks.corpus import AttackCorpus
from src.evaluation.runner import ExperimentRunner
from src.composition import DefensePipeline
```

`src/__init__.py` inserts the package directory into `sys.path` so that legacy absolute imports (e.g. `from utils.timing import stopwatch`) continue to resolve. Do not remove this shim without a repo-wide refactor.

## Design Principles (enforced)

1. **Modular** — every subpackage is self-contained with its own docs.
2. **Thin Orchestrator** — `scripts/` only orchestrate; computation lives here.
3. **No Mocks** — tests use real numerical data. `MagicMock`, `mocker.patch`, `unittest.mock` are prohibited anywhere in the project. `pytest-httpserver` handles HTTP; real temp files handle I/O.
4. **Deterministic** — default `seed=42`; reproducibility is a first-class contract.
5. **Typed** — public APIs have complete type hints; `mypy --strict` clean.
6. **Cited** — non-trivial functions carry a manuscript anchor in the docstring.

## Docstring Convention (Paper-Anchored)

When implementing a function that realizes a manuscript claim, include a **manuscript anchor** in the docstring so that future agents can trace code → paper and paper → code.

```python
def compute_series_detection_rate(rates: Sequence[float]) -> float:
    """Series composition of detection rates (Paper 1, Theorem 3.1).

    Given independent detection rates r_1, ..., r_n for orthogonal defenses in
    series, the combined detection rate is::

        1 - prod(1 - r_i)

    This realizes the multiplicative composition theorem from Paper 1 \\cite{friedman2026cogsec1}
    §5 (Defense Composition Algebra). Empirical validation of the bound appears
    in Paper 2 §5.6 (this manuscript).

    Args:
        rates: Per-mechanism detection rates in [0, 1].

    Returns:
        Series-composed detection rate in [0, 1].
    """
    from math import prod
    return 1 - prod(1 - r for r in rates)
```

## No-Mocks Policy (Absolute)

Using any of `MagicMock`, `mock.patch`, `unittest.mock`, `mocker.patch`, `monkeypatch` against project internals is a project-wide violation. Enforcement is by policy + convention (tests construct real objects; several test modules state the no-MagicMock contract in their docstrings). Note: there is **no** `infrastructure/validation/no_mock_enforcer.py` in this repo — that file lives in the parent template's infrastructure and is not wired here, so the no-mocks discipline is maintained in-repo by the stated contract, not by a local CI gate (P2-26).

Approved alternatives:

| Scenario | Use Instead |
| -------- | ----------- |
| HTTP testing | `pytest-httpserver` (real local server) |
| File I/O | `tmp_path` fixture + real files |
| CLI testing | `subprocess.run` against real scripts |
| LLM testing | Real Ollama instance (conftest auto-starts) |
| PDF generation | `reportlab` producing real PDFs |
| Time | Inject real `datetime` / `time.monotonic` fixtures |

## Coverage Requirements

- **Project code (src/)**: 90% minimum, target 95%+.
- **Infrastructure code (elsewhere in repo)**: 60% minimum.

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

## Cross-Paper Reference Discipline

When a code change affects a manuscript claim:

1. Identify which manuscript sections (in this paper or siblings) cite the affected metric.
2. Update **all** affected cross-references, not just this paper's.
3. Run `scripts/verify_manuscript.py` — it checks citation, label, and figure integrity.

Sibling-paper sections that cite this codebase's metrics:

| Sibling | Section | What They Cite |
| ------- | ------- | -------------- |
| Paper 1 | §8 Discussion | Ablation deltas from `src.ablation` |
| Paper 1 | §9 Conclusion | Headline detection rate |
| Part 3+4 | §3 Evidence | 96–100% parametric ceiling, 3,369 passing tests |
| Part 3+4 | §5 Deployment | Per-component configuration guidance |
| Part 3+4 | §5b Incident Response | Adversary class detection rates |
| Part 3+4 | §2 Methodology | 96–100% ceiling as validation anchor |
| Part 3+4 | §4 Discussion | Defense composition algebra empirical backing |

## Adding a New Module

1. Create `src/<sub>/<module>.py` with complete type hints + anchored docstring.
2. Re-export key symbols in `src/<sub>/__init__.py` and, if public, in `src/__init__.py`.
3. Add `src/<sub>/README.md` + `src/<sub>/AGENTS.md` if the subpackage is new.
4. Add tests in `tests/test_<module>.py` using real data (no mocks).
5. Update this AGENTS.md's anchor table if the new module realizes a manuscript claim.
6. Run `uv run pytest`, `uv run mypy`, and `uv run python scripts/verify_manuscript.py` before committing.

## Forbidden in `src/`

- `print` (use `logging` — `get_logger(__name__)`)
- `sys.exit` (raise exceptions; `scripts/` decide how to exit)
- Hard-coded absolute paths
- Writes to arbitrary filesystem locations (accept `Path` via caller)
- Stateful module-level globals (use dataclasses / config objects)

## Contact / Reviews

When in doubt: check [`README.md`](README.md) for conventions, or defer to the manuscript-anchor table above to identify which section the code implements.
