# Cognitive Security Tests - Quick Reference

Test suite for all CIF security modules.

## Test Files

| Test File | Module | Key Tests |
|-----------|--------|-----------|
| `test_trust.py` | trust.py | Config validation, delegation bounds, decay |
| `test_firewall.py` | firewall.py | Classification, pattern detection, semantic |
| `test_consensus.py` | consensus.py | Byzantine tolerance, quorum, weighted voting |
| `test_tripwire.py` | tripwire.py | Canary detection, alert severity, rotation |
| `test_provenance.py` | provenance.py | Taint propagation, ancestry, attribution |
| `test_detection.py` | detection.py | Drift detection, anomaly scoring |
| `test_invariants.py` | invariants.py | INV-1 through INV-5, runtime monitor |
| `test_sandbox.py` | sandbox.py | TTL expiry, promotion, corroboration |

## Quick Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific module
uv run pytest tests/test_trust.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run with output
uv run pytest tests/ -v -s
```

## Coverage Target

- **90%+ coverage required** for all src modules
- No algorithm mocks; semantic-backend boundary tests use an explicitly named
  controlled-vector double, not a production backend or semantic-quality proof
- All edge cases covered

## Test Patterns

All tests follow data computation pattern:
```python
def test_feature(self):
    """Description."""
    # Arrange - create real objects
    calc = TrustCalculus()

    # Act - perform computation
    result = calc.compute_trust(0.8, 0.9, 0.7)

    # Assert - verify with numerical comparison
    assert np.isclose(result, expected_value)
```

For the result/semantic contracts, run
`uv run pytest tests/test_visualization.py tests/test_firewall.py -q`.
Result-figure fixtures are test-only inputs: missing configurations/files and
malformed numeric evidence must raise without writing images. Complete inputs
must produce both formats and preserve visible non-measured labels.
Semantic tests cover explicit callable injection, paraphrase/benign score
plumbing, unavailable backends and invalid vectors; actual model quality must
be qualified with the application's pinned offline backend separately.
