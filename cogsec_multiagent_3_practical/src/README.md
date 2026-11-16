# Practical CogSec Source

Practitioner implementations for the Cognitive Integrity Framework.

## Modules

| Module | Purpose |
|--------|---------|
| `agent_guidelines.py` | Independent-confidence drift and coordination monitoring |
| `checklists/` | Deployment, operational, and incident-response checklists |
| `deployment.py` | Illustrative deployment profiles and trust-decay analysis |
| `pitfalls.py` | Pitfall catalog and assessment |
| `posture.py` | Five-pillar posture and maturity assessment |
| `risk_assessment.py` | Attack-surface mapping and threat modeling |
| `verification.py` | Pandoc/LaTeX verification with module-owned log handlers |
| `visualization.py` | Operator-posture, risk, and catalog-backed pitfall figures |

The distribution exports one package, `src`, and its descendants. Use package-qualified imports:

```python
from src import ChecklistItem, OperatorPostureAssessment, PostureLevel
from src.deployment import DeploymentConfigurator, RiskProfile

assessment = OperatorPostureAssessment(PostureLevel.STANDARD)
assessment.add_check(ChecklistItem("trust", "configuration", "Trust boundaries documented"))
profile = DeploymentConfigurator().get_config(RiskProfile.MEDIUM)
```

Configuration values are illustrative starting points, not measured field-performance guarantees.
