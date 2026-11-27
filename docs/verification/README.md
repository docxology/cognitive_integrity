# Local trust-calculus verification

The checked-in theory module evaluates bounded confidence scores. This local
example exercises its weighted score, delegation along a fixed numerical path,
and input validation. The fixture uses only numeric values and emits a JSON
receipt and figure under `output/`.

Use Python 3.11 or later with NumPy, Matplotlib, and pytest installed. The
commands below work from a source checkout with the theory module and its
trust tests materialized.

```bash
export PYTHONPATH="$PWD/cogsec_multiagent_1_theory/src"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest --noconftest --import-mode=importlib cogsec_multiagent_1_theory/tests/test_trust.py
python docs/verification/replay_trust.py
```

The fixture requires the weighted score, path scores, and invalid-input
controls documented in the [assurance note](../manuscript/README.md).
Its receipt is `output/data/trust_fixture.json`. A failure stops artifact
generation and calls for inspection of the source and stated invariant.

For PDF and HTML, use the isolated [pinned Template workflow](../manuscript/README.md#render-the-note).
