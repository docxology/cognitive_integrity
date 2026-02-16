# Practical CogSec Source - Agent Reference

Practitioner implementations for the Cognitive Integrity Framework.

## Modules

| Module | Purpose |
|--------|---------|
| `agent_guidelines.py` | Agent configuration guidelines |
| `checklists.py` | Security deployment checklists |
| `deployment.py` | Deployment patterns |
| `pitfalls.py` | Common pitfalls and mitigations |
| `posture.py` | Security posture assessment |
| `risk_assessment.py` | Risk evaluation framework |
| `visualization.py` | Posture visualization |

## Usage

```python
from src import SecurityPosture, RiskAssessment

posture = SecurityPosture(config)
score = posture.evaluate()

risk = RiskAssessment()
matrix = risk.generate_matrix()
```
