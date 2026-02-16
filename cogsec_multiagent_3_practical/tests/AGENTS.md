# Practical CogSec Tests - Agent Reference

Test suite for practical CIF implementations.

## Test Modules

| Module | Coverage |
|--------|----------|
| `test_agent_guidelines.py` | Agent configuration |
| `test_checklists.py` | Deployment checklists |
| `test_deployment.py` | Deployment patterns |
| `test_pitfalls.py` | Pitfall detection |
| `test_posture.py` | Posture assessment |
| `test_practical.py` | Integration tests |
| `test_risk_assessment.py` | Risk evaluation |
| `test_visualization.py` | Visualization output |

## Running Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src --cov-report=term-missing
```
