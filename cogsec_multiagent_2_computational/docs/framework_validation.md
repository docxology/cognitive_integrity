# Framework Validation & Reproducibility

This document details how the Cognitive Integrity Framework (CIF) was empirically validated, including the target architectures, experimental parameters, and reproducibility instructions. It serves as a guide for reproducing the results presented in Part 2 of the manuscript.

## Target Architectures

The framework was tested against six distinct multiagent architectural patterns to ensure generalizability. Adapters for these architectures are located in `src/architectures/`.

1. **Hierarchical (Orchestrator-Worker)**: Modeled on Enterprise RAG systems.
    - *Implementation*: `src/architectures/hierarchical.py`
2. **Peer-to-Peer (Swarm)**: Modeled on Decentralized Autonomous Organizations (DAOs).
    - *Implementation*: `src/architectures/p2p.py`
3. **Role-Based (Team)**: Modeled on CrewAI / ChatDev.
    - *Implementation*: `src/architectures/role_based.py`
4. **State Machine (Cyclic)**: Modeled on LangGraph.
    - *Implementation*: `src/architectures/state_machine.py`
5. **Pipeline (Linear)**: Modeled on Standard ETL/Processing chains.
    - *Implementation*: `src/architectures/pipeline.py`
6. **Hybrid (Complex)**: A composite of hierarchical and p2p elements.
    - *Implementation*: `src/architectures/hybrid.py`

## Attack Corpus

The evaluation used a comprehensive corpus of 950 cognitive attacks, generated to cover the theoretical threat model. Categories include:

- **Prompt Injection**: Direct LLM input manipulation.
- **Trust Exploitation**: Social engineering of agent trust scores.
- **Belief Manipulation**: Planting false axioms or data.
- **Coordination Subversion**: Disrupting consensus/voting.

Corpus generation logic: `src/attacks/corpus_generator.py`

## Reproducing the Experiments

All experiments are deterministic (seed=42).

### 1. Run Full Evaluation

This script runs the entire experimental suite across all architectures and attack types.

```bash
python projects/cognitive_integrity/cogsec_multiagent_2_computational/scripts/run_full_evaluation.py
```

**Output**: `output/data/full_evaluation_results.json`

### 2. Run Ablation Studies

This script tests the contribution of individual components (removing Firewall, Trust, etc. one by one).

```bash
python projects/cognitive_integrity/cogsec_multiagent_2_computational/scripts/run_ablation.py
```

**Output**: `output/data/ablation_results.json`

### 3. Run Scalability Analysis

This script measures performance overhead (latency/memory) as agent count increases.

```bash
python projects/cognitive_integrity/cogsec_multiagent_2_computational/scripts/run_scalability.py
```

**Output**: `output/data/scalability_results.json`

### 4. Generate Figures

Once data is generated, run this to produce the plots used in the manuscript.

```bash
python projects/cognitive_integrity/cogsec_multiagent_2_computational/scripts/generate_all_figures.py
```

**Output**: `output/figures/*.png`

## Validation Results Check

You can compare your generated results with the canonical results in the repo:

- `output/data/canonical_results.json` vs `output/data/full_evaluation_results.json`

## Requirements

- Python 3.10+
- `numpy`, `scipy`, `matplotlib` (see `pyproject.toml`)
