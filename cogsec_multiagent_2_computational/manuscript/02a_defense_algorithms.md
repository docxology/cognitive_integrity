\newpage

# Defense Algorithm Implementations {#sec:pseudocode}

This section summarizes the six core CIF defense algorithms and their correspondence to the formal definitions in Part 1. Complete pseudocode listings with implementation references are provided in Supplement S7 (\cref{sec:pseudocode-supplement}).

> **Reproducibility**: Algorithm implementations are in `src/core/`. Run `pytest tests/` to verify behavior (1,594 tests, 100% pass rate).

## Algorithm Overview

The CIF defense suite comprises six algorithms, each implementing a specific formal mechanism from Part 1:

1. **Cognitive Firewall Classification** (\cref{alg:firewall-impl}). Multi-stage detection pipeline implementing Part 1, Definition 5.3: three-stage filtering ($F_{sig} \to F_{sem} \to F_{anom}$) with combined threat scoring. Implemented in `src/core/firewall.py`.

2. **Belief Sandboxing** (\cref{alg:sandbox-impl}). Provisional belief management with $\kappa$-corroboration promotion, implementing Part 1, Definition 5.4 and Property 5.2. Beliefs are quarantined until they meet provenance, consistency, and corroboration criteria. Implemented in `src/core/sandbox.py`.

3. **Trust Update with Bounded Delegation** (\cref{alg:trust-impl}). Trust calculus with $\delta^d$ decay implementing Part 1, Theorem 4.2 (Trust Boundedness). Trust cannot be inflated through delegation chains. Integrates base trust, reputation tracking, and contextual modifiers. Implemented in `src/core/trust.py`.

4. **Cognitive Tripwire Monitoring** (\cref{alg:tripwire-impl}). Continuous monitoring of canary beliefs for unauthorized modifications, implementing Part 1, Section 5.3 (Definition 5.6). Severity is classified via a uniform 4-tier system (LOW, MEDIUM, HIGH, CRITICAL) based on drift magnitude. Implemented in `src/core/tripwire.py`.

5. **Byzantine Consensus Protocol** (\cref{alg:byzantine-impl}). Byzantine fault-tolerant consensus satisfying Part 1, Theorem 5.2, ensuring agreement when $f < n/3$ agents are Byzantine. Three-phase protocol: vote collection, echo verification, and supermajority decision. Implemented in `src/core/consensus.py`.

6. **Belief Drift Detection** (\cref{alg:drift-impl}). KL-divergence-based drift monitoring implementing Part 1, Definition 6.1. Combines distributional divergence with maximum belief delta for anomaly scoring. Implemented in `src/core/detection.py`.

## Configuration Parameters

All algorithms share a unified configuration system with 27 parameters organized into eight groups. Default values are calibrated for balanced precision--recall trade-offs. Full parameter documentation is in Supplement S5 (\cref{sec:framework-api}).
