\newpage

# Methodology: Implementation Details {#sec:methodology}

This section describes how the formal CIF mechanisms from Part 1 are realized as executable defense algorithms. The implementation follows three design principles: (1) **fidelity to formal specification**---each algorithm directly implements a Part 1 definition or theorem, with explicit cross-references; (2) **composability**---mechanisms operate independently and compose through well-defined interfaces, matching the defense composition algebra; and (3) **configurability**---all thresholds, weights, and operational parameters are externalized to enable deployment-specific tuning (\cref{sec:config-params}).

> **Cross-Reference Note**: All algorithms implement formal definitions from Part 1. We cite specific theorems using "(Part 1, Theorem X.Y)" notation to enable traceability from implementation to theoretical foundations.

The implementation comprises six core algorithms (\cref{sec:pseudocode}), 27 configuration parameters organized into eight parameter groups (\cref{sec:config-params}), and 13 packages comprising eight core defense modules totaling approximately 21,000 lines of Python with 1,557 passing tests at 100\% pass rate. The complete source is available at DOI: 10.5281/zenodo.18364128.

**Defense Algorithms** (\cref{sec:pseudocode}): Six pseudocode implementations---Cognitive Firewall (three-stage classification), Belief Sandboxing (provisional isolation with $\kappa$-corroboration promotion), Trust Update (bounded delegation with $\delta^d$ decay), Tripwire Monitoring (canary belief surveillance), Byzantine Consensus (three-phase agreement), and Drift Detection (KL divergence anomaly scoring).

**Configuration Parameters** (\cref{sec:config-params}): Eight parameter tables covering core framework, trust calculus, firewall, sandbox, tripwire, drift detection, consensus, and invariant parameters, plus three deployment profiles (low latency, high throughput, Byzantine-heavy).

**Framework API Reference** (\cref{sec:framework-api}): Eight module API specifications (Trust, Firewall, Consensus, Detection, Provenance, Sandbox, Tripwire, Invariants).

**Deployment Guide** (\cref{sec:deployment}): Production checklist, configuration guidance, post-deployment verification, and integration examples (Python and YAML).
