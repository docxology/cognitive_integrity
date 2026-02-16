# Source Package - Agent Reference

Top-level source package for the Cognitive Integrity Framework (CIF) computational validation.

## Package Structure

| Package | Purpose |
|---------|---------|
| `core/` | Core defense algorithms (trust, firewall, consensus, etc.) |
| `ablation/` | Component removal and synergy studies |
| `architectures/` | Production multiagent architecture adapters |
| `attacks/` | 950-attack corpus with generators |
| `colony/` | Colony-level CogSec benchmarks |
| `composition/` | Defense composition algebra |
| `data/` | Data generation and result loading |
| `evaluation/` | Experiment runner, metrics, benchmarks |
| `formal/` | Theorem validation and model checker specs |
| `statistics/` | Hypothesis testing, effect sizes, CI |
| `utils/` | Configuration, logging, timing, types |
| `visualization/` | Publication-quality figures and tables |

## Import Conventions

```python
# Core modules re-exported at src level
from src import TrustCalculus, CognitiveFirewall, ByzantineConsensus

# Or import from subpackages directly
from src.core.trust import TrustMatrix
from src.attacks.corpus import AttackCorpus
from src.evaluation.runner import ExperimentRunner
```

## Design Principles

1. **Modular Architecture** - Each subpackage is self-contained
2. **Thin Orchestrator** - Scripts coordinate, modules compute
3. **No Mocks** - All tests use real computations
4. **Deterministic** - Fixed seeds for reproducibility
