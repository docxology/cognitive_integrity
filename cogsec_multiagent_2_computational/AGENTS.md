# Cognitive Integrity Framework: Computational Validation - Agent Reference

**Location:** `projects/cognitive_integrity/cogsec_multiagent_2_computational/`. Active nested project under the program `cognitive_integrity/`; use qualified name `cognitive_integrity/cogsec_multiagent_2_computational` for pipeline and PDF scripts.

## Overview

Part 2 of the **Cognitive Security for Multiagent Operators** series. Computational validation of CIF through implementation, benchmarking, and statistical analysis. Claims-to-code mapping: `docs/claims_traceability.md`; reproduction: `docs/framework_validation.md`.

## Key Features & Capabilities

### Defense Mechanism Implementations

- **Cognitive Firewall**: Pattern-based and semantic injection detection
- **Belief Sandbox**: Provisional belief management with TTL
- **Trust Calculus**: Bounded delegation with decay
- **Byzantine Consensus**: Fault-tolerant multi-agent agreement
- **Tripwire Detection**: Canary belief monitoring
- **Provenance Tracking**: Information flow with taint labels
- **Behavioral Invariants**: Runtime security constraint checking

### Attack Corpus (950 attacks)

- **Prompt Injection** (500): Direct, indirect, nested variants
- **Trust Exploitation** (200): Identity impersonation, delegation abuse
- **Belief Manipulation** (150): Evidence fabrication, progressive drift
- **Coordination Attacks** (100): Sybil, consensus poisoning, quorum manipulation

### Target Architectures (6 systems)

- Claude Code (hierarchical)
- AutoGPT (autonomous + plugins)
- CrewAI (role-based)
- LangGraph (graph-based)
- MetaGPT (SOP-driven)
- Camel (debate)

## Directory Structure

```text
cogsec_multiagent_2_computational/
├── src/                        # Source code
│   ├── core/                   # Defense mechanism implementations
│   │   ├── firewall.py         # Cognitive firewall (multi-stage classifier)
│   │   ├── sandbox.py          # Belief sandboxing (TTL, promotion)
│   │   ├── trust.py            # Trust calculus (bounded delegation + decay)
│   │   ├── consensus.py        # Byzantine consensus (n ≥ 3f+1)
│   │   ├── tripwire.py         # Canary belief monitoring
│   │   ├── provenance.py       # Information flow / taint tracking
│   │   ├── detection.py        # Drift & anomaly detection
│   │   ├── invariants.py       # Behavioral invariant checking
│   │   ├── batch_detection.py  # Batch message analysis
│   │   └── online_detection.py # Streaming anomaly detection
│   ├── architectures/          # Target architecture adapters
│   │   ├── base.py             # Abstract base class
│   │   ├── claude_code.py      # Hierarchical (Claude Code)
│   │   ├── autogpt.py          # Autonomous + plugins (AutoGPT)
│   │   ├── crewai.py           # Role-based (CrewAI)
│   │   ├── langgraph.py        # Graph-based (LangGraph)
│   │   ├── metagpt.py          # SOP-driven (MetaGPT)
│   │   └── camel.py            # Debate (Camel)
│   ├── attacks/                # Attack corpus generation
│   │   ├── corpus.py           # AttackCorpus.generate()
│   │   ├── templates.py        # Attack prompt templates
│   │   ├── validation.py       # Attack validity checks
│   │   └── generators/         # Per-category generators
│   ├── evaluation/             # Experiment orchestration & metrics
│   ├── composition/            # Defense composition algebra
│   ├── colony/                 # Colony benchmarks
│   ├── statistics/             # Statistical analysis suite
│   ├── formal/                 # Formal verification (theorem registry)
│   ├── agents/                 # Simulated agent framework
│   ├── ablation/               # Ablation study module
│   ├── visualization/          # Figure generation
│   ├── manuscript/             # Manuscript verifier & LaTeX converter
│   ├── utils/                  # Shared types & helpers
│   └── data/                   # Data loaders
├── scripts/                    # Entry-point scripts (17)
│   ├── run_full_evaluation.py  # Full CIF pipeline (6 archs × 950 attacks)
│   ├── run_statistical_analysis.py  # Hypothesis tests & effect sizes
│   ├── run_ablation.py         # Component ablation study
│   ├── run_colony_benchmarks.py     # Colony-level benchmarks
│   ├── run_sensitivity_analysis.py  # Parameter sensitivity sweeps
│   ├── run_multi_seed.py       # Multi-seed stability analysis
│   ├── run_cross_validation.py # K-fold cross-validation
│   ├── run_formal_validation.py     # Formal theorem verification
│   ├── run_llm_demo.py         # Live LLM integration demo
│   ├── run_publication_suite.py     # Full publication-quality analysis
│   ├── verify_formal_specs.py  # SMV/PML/TLA+ spec generation
│   ├── verify_manuscript.py    # Manuscript consistency checks
│   ├── generate_all_figures.py # All manuscript figures → output/figures/
│   ├── generate_all_tables.py  # All manuscript tables
│   ├── generate_all_data.py    # All experimental data → output/data/
│   ├── convert_latex_tables.py # LaTeX → Markdown table conversion
│   └── z_inject_manuscript_values.py # Auto-inject values into manuscript
├── tests/                      # 36 test_*.py modules + conftest; 90%+ coverage (see glob in repo)
├── manuscript/                 # Paper content (28 files)
└── output/                     # Generated figures and data
    ├── figures/                # *.pdf figures
    └── data/                   # *.json results
```

## Testing

```bash
# Run all tests with 90%+ coverage requirement
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific module tests
uv run pytest tests/test_trust.py -v
uv run pytest tests/test_firewall.py -v

# Run formal validation (7 theorems)
uv run python scripts/run_formal_validation.py --seed 42

# Run analysis scripts
uv run python scripts/run_full_evaluation.py --seed 42
uv run python scripts/run_statistical_analysis.py --seed 42
uv run python scripts/run_ablation.py --seed 42
uv run python scripts/run_colony_benchmarks.py --seed 42
uv run python scripts/run_sensitivity_analysis.py --seed 42
uv run python scripts/run_multi_seed.py --seed 42
uv run python scripts/run_cross_validation.py --seed 42

# Generate outputs
uv run python scripts/generate_all_data.py --seed 42
uv run python scripts/generate_all_figures.py
uv run python scripts/generate_all_tables.py

# Verification
uv run python scripts/verify_formal_specs.py
uv run python scripts/verify_manuscript.py
uv run python scripts/convert_latex_tables.py

# LLM demo (requires Ollama)
uv run python scripts/run_llm_demo.py --provider ollama --model gemma3:4b
```

## Notation Reference

All notation follows the canonical definitions in:

- `../cogsec_multiagent_1_theory/manuscript/S03_notation.md`

Key symbols used in this paper:

- $\mathcal{T}_{i \to j}$: Trust from agent $i$ to agent $j$
- $\delta$: Trust decay factor
- $q$: Quorum threshold
- $f$: Maximum Byzantine agents

## Module Dependencies

```text
core/firewall.py ──> core/detection.py (anomaly scoring)
core/consensus.py ──> (standalone)
core/trust.py ──> (standalone, uses numpy)
core/tripwire.py ──> (standalone, uses numpy)
core/provenance.py ──> (standalone)
core/invariants.py ──> (standalone)
core/sandbox.py ──> (standalone)
core/detection.py ──> (standalone, uses numpy)
composition/adapters.py ──> core/* (wraps all defense modules)
composition/pipeline.py ──> utils/types (DefenseResult)
evaluation/runner.py ──> core/*, attacks/*, architectures/*
```

## Security Considerations

- All modules implement defense-in-depth principles
- Trust scores are always bounded [0, 1]
- Delegation cannot amplify trust
- Byzantine consensus requires n >= 3f + 1
- No mock methods - all tests use real computations
