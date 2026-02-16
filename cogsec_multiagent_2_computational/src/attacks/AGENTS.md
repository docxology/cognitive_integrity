# Attack Corpus - Agent Reference

950-attack corpus with generators for security evaluation.

## Modules

### corpus.py

Central attack corpus management.

**Key Classes:**

- `AttackCorpus` - Main corpus with filtering and sampling
- `Attack` - Single attack with metadata
- `AttackCategory` - Enum of attack types

### templates.py

Attack template system for generating variants.

**Key Classes:**

- `AttackTemplate` - Parameterized attack pattern
- `TemplateEngine` - Variable substitution engine

### validation.py

Attack validation and effectiveness scoring.

**Key Classes:**

- `AttackValidator` - Validates attack structure
- `EffectivenessScorer` - Measures attack success

### generators/

Subdirectory with category-specific generators.

## Attack Categories

| Category | Count | Description |
|----------|-------|-------------|
| Prompt Injection | 500 | Direct, indirect, nested |
| Trust Exploitation | 200 | Impersonation, delegation abuse |
| Belief Manipulation | 150 | Fabrication, progressive drift |
| Coordination | 100 | Sybil, consensus poisoning |

## Usage

```python
from src.attacks import AttackCorpus

corpus = AttackCorpus.load_default()
injection_attacks = corpus.filter(category="prompt_injection")
sample = corpus.sample(n=50, seed=42)
```
