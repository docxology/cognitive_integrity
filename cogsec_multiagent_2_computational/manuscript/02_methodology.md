\newpage

# Methodology: Implementation Details {#sec:methodology}

This section describes how the formal CIF mechanisms from Part 1 are realized as executable defense algorithms. The implementation follows three design principles: (1) **fidelity to formal specification**---each algorithm directly implements a Part 1 definition or theorem, with explicit cross-references; (2) **composability**---mechanisms operate independently and compose through well-defined interfaces, matching the defense composition algebra; and (3) **configurability**---all thresholds, weights, and operational parameters are externalized to enable deployment-specific tuning (\cref{sec:config-params}).

> **Cross-Reference Note**: All algorithms implement formal definitions from Part 1. We cite specific theorems using "(Part 1, Theorem X.Y)" notation to enable traceability from implementation to theoretical foundations.

The implementation comprises six core algorithms (\cref{sec:pseudocode}), 27 configuration parameters organized into eight parameter groups (\cref{sec:config-params}), and 13 packages comprising eight core defense modules. The code is tested under the project coverage gate; regenerate current counts from the test runner rather than hand-authoring them. The complete source is available at DOI: 10.5281/zenodo.18364128.

## Processing Pipeline Architecture {#sec:pipeline-architecture}

The CIF defense suite processes each inter-agent message through a layered pipeline. Modules 1–5 operate **in series** for each message; modules 6–8 operate **in parallel** on separate communication events (trust updates on interaction completion, consensus on multi-agent decisions, provenance on message receipt).

**Table: CIF processing pipeline — module order, inputs, outputs, and attack targets.** {#tab:pipeline-architecture}

| Stage | Module | Primary Input | Output | Attack Target |
| --- | --- | --- | --- | --- |
| 1. Input filter | Cognitive Firewall | Raw inter-agent message | ACCEPT / QUARANTINE / REJECT + score | Prompt injection (all subcategories) |
| 2. Isolation | Belief Sandbox | Quarantined message + source trust | PENDING / SUCCESS / CONFLICT | Unverified content propagation |
| 3. Behavioral | Tripwire Monitor | Agent belief state snapshot | Alert set (severity: LOW–CRITICAL) | Belief manipulation, canary modification |
| 4. Statistical | Drift Detector | Sliding window of belief history | KL divergence score + drift alerts | Progressive drift, gradual manipulation |
| 5. Structural | Anomaly Scorer | Per-message feature vector | Deviation score | Statistical outliers, novel attack patterns |
| 6. Delegation | Trust Calculus | Agent interaction outcome | Updated trust score $[0,1]$ | Trust exploitation, delegation abuse |
| 7. Coordination | Byzantine Consensus | Multi-agent vote set | ACCEPT / REJECT / UNDECIDED | Coordination attacks, quorum manipulation |
| 8. Attribution | Provenance Attestation | Message + delegation chain | VERIFIED / UNVERIFIED origin | Identity impersonation, source fabrication |

**Evaluation Modes**: The defense suite is evaluated in two complementary modes (§\ref{sec:eval-methodology}): (1) *pipeline-driven*, where real attack text flows through the implemented modules and the pipeline's own verdict is used; (2) *parametric simulation*, where detection is computed from calibrated base rates modulated by architecture-specific multipliers. When a real pipeline is passed to `ExperimentRunner`, Mode 1 is used; when no pipeline is provided, Mode 2 is used. Primary empirical analyses in Sections \ref{sec:extended-results}–\ref{sec:extended-ablation} use Mode 1; the parametric ceiling analysis (§\ref{sec:parametric-analysis}) uses Mode 2.

**Defense Algorithms** (\cref{sec:pseudocode}): Six pseudocode implementations---Cognitive Firewall (three-stage classification), Belief Sandboxing (provisional isolation with $\kappa$-corroboration promotion), Trust Update (bounded delegation with $\delta^d$ decay), Tripwire Monitoring (canary belief surveillance), Byzantine Consensus (three-phase agreement), and Drift Detection (KL divergence anomaly scoring).

**Configuration Parameters** (\cref{sec:config-params}): Eight parameter tables covering core framework, trust calculus, firewall, sandbox, tripwire, drift detection, consensus, and invariant parameters, plus three deployment profiles (low latency, high throughput, Byzantine-heavy).

**Framework API Reference** (\cref{sec:framework-api}): Eight module API specifications (Trust, Firewall, Consensus, Detection, Provenance, Sandbox, Tripwire, Invariants).

**Deployment Guide** (\cref{sec:deployment}): Production checklist, configuration guidance, post-deployment verification, and integration examples (Python and YAML).
