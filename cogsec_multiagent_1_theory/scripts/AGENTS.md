# Cognitive Security Scripts - Agent Reference

Analysis and figure generation scripts for the Cognitive Integrity Framework manuscript.

## Script Categories

### Figure Generation (01-05, 07-18)
Generate publication-quality visualizations for manuscript inclusion.

**Pattern:**
```python
#!/usr/bin/env python3
"""Figure script following thin orchestrator pattern."""
from pathlib import Path
import matplotlib.pyplot as plt
from src.module import ClassName  # Import from src

def main():
    output_dir = Path("output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use src methods for computation
    results = compute_from_src()

    # Script handles visualization only
    fig, ax = plt.subplots()
    # ... visualization code ...

    output_path = output_dir / "figure_name.png"
    fig.savefig(output_path)
    print(str(output_path))  # For manifest collection

if __name__ == "__main__":
    main()
```

### Data Generation (06)
`06_generate_data.py` - Generates all experimental datasets:
- Trust decay simulations
- Detection performance metrics
- Attack scenario data
- Consensus convergence data

### Validation (verify)
`verify_manuscript.py` - Validates manuscript integrity:
- Cross-reference checking
- Figure registration verification
- Citation validation

## Script Details

### 01_attack_surface_figure.py
Visualizes the attack surface taxonomy:
- External adversary (prompt injection)
- Peer adversary (malicious agent)
- Tool adversary (compromised tool)
- Environmental adversary (data poisoning)
- Systemic adversary (infrastructure)

### 02_trust_decay_figure.py
Plots trust decay across delegation depths:
- Single-hop vs multi-hop decay
- Different decay rates (0.7, 0.8, 0.9)
- Bounded trust guarantees

### 03_detection_results_figure.py
Shows detection performance:
- ROC curves for different detectors
- Precision-recall tradeoffs
- F1 score comparisons

### 04_cif_architecture_figure.py
System architecture diagram:
- Input processing flow
- Defense layer composition
- Belief state management

### 05_threat_taxonomy_figure.py
Threat classification visualization:
- Attack vectors
- Defense mappings
- Risk levels

### 06_generate_data.py
**Primary data generation script:**
```python
# Outputs:
# - output/data/trust_decay.csv
# - output/data/detection_results.csv
# - output/data/consensus_convergence.csv
# - output/data/attack_scenarios.json
```

### 07_roc_curves_figure.py
ROC curve analysis:
- Firewall detection
- Anomaly scoring
- Semantic similarity

### 08_scalability_figure.py
Scalability analysis:
- Agent count vs latency
- Memory usage scaling
- Consensus convergence time

### 09_attack_timeline_figure.py
Attack progression visualization:
- Detection timeline
- Alert propagation
- Response actions

### 10_defense_composition_figure.py
Defense stack visualization:
- Layer-by-layer protection
- Cumulative effectiveness

### 11_trust_network_figure.py
Trust relationship graph:
- Agent-to-agent trust
- Delegation paths
- Trust clusters

### 12_belief_sandbox_figure.py
Sandbox state visualization:
- Verified vs provisional counts
- TTL distribution
- Promotion rates

### 13_ablation_study_figure.py
Component contribution analysis:
- Detection accuracy by feature
- Trust component weights
- Consensus performance

### 14_detection_performance_figure.py
Multi-detector comparison:
- Pattern detector
- Semantic detector
- Anomaly scorer

### 15_fp_mitigation_figure.py
False positive analysis:
- Quarantine effectiveness
- Human review impact
- Threshold tuning

### 16_comprehensive_taxonomy_figure.py
Full attack taxonomy:
- All five adversary classes
- Attack techniques
- Defense mappings

### 17_cif_comprehensive_figure.py
Complete framework diagram:
- All components
- Data flows
- Integration points

### 18_trust_calculus_figure.py
Mathematical visualization:
- Trust formula
- Decay curves
- Delegation bounds

### 19_cif_ad_coupling_figure.py
CIF-AD coupling matrix visualization:
- Action-Delegation phase mapping
- Attack surface coverage across OODA phases
- Defense portfolio optimization

### 20_ooda_phase_figure.py
OODA phase diagram:
- Observe-Orient-Decide-Act cycle
- CIF defense integration at each phase
- Attack vector mapping to OODA transitions

### verify_manuscript.py
Manuscript validation:
- Figure cross-references
- Equation numbering
- Citation completeness

## Dependencies

All scripts import from:
- `src/` modules for computation
- `matplotlib` for visualization
- `numpy` for numerical operations
- `pathlib` for file operations

## Output Structure

```
output/
├── figures/
│   ├── attack_surface.png
│   ├── trust_decay.png
│   ├── detection_results.png
│   └── ...
├── data/
│   ├── trust_decay.csv
│   ├── detection_results.csv
│   └── ...
└── reports/
    └── validation_report.json
```

## Thin Orchestrator Pattern

**Required:**
- All computation via `src/` imports
- Scripts handle only I/O and visualization
- Print output paths for manifest collection
- Use fixed seeds for reproducibility

**Forbidden:**
- Business logic in scripts
- Algorithm implementation
- Direct numerical computation (use src methods)
