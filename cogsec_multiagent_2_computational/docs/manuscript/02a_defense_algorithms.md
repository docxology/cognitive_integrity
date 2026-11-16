\newpage

# Defense Algorithm Implementations {#sec:pseudocode}

This section summarizes the six core CIF defense algorithms and their correspondence to the formal definitions in Part 1. Complete pseudocode listings with implementation references are provided in Supplement S7 (\cref{sec:pseudocode-supplement}).

> **Reproducibility**: Algorithm implementations are in `src/core/`. Run `uv run pytest tests/` to verify behavior against the project coverage gate (90%+ project code, no mocks).

## Algorithm Overview

The CIF defense suite comprises six algorithms, each implementing a specific formal mechanism from Part 1:

1. **Cognitive Firewall Classification** (\cref{alg:firewall-impl}). Multi-stage detection pipeline implementing Part 1's Firewall Decision Rules definition: three-stage filtering ($F_{sig} \to F_{sem} \to F_{anom}$) with combined threat scoring. Implemented in `src/core/firewall.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py, FirewallAdapter)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(firewall)
pipeline = MonadicPipeline([firewall, sandbox, tripwire])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

2. **Belief Sandboxing** (\cref{alg:sandbox-impl}). Provisional belief management with $\kappa$-corroboration promotion, implementing Part 1's Belief Sandbox definition and Property 5.2. Beliefs are quarantined until they meet provenance, consistency, and corroboration criteria. Implemented in `src/core/sandbox.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py, SandboxAdapter)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(sandbox)
pipeline = MonadicPipeline([firewall, sandbox, tripwire])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

3. **Trust Update with Bounded Delegation** (\cref{alg:trust-impl}). Trust calculus with $\delta^d$ decay implementing Part 1's Trust Boundedness theorem (Trust Boundedness). Trust cannot be inflated through delegation chains. Integrates base trust, reputation tracking, and contextual modifiers. Implemented in `src/core/trust.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py, TrustAdapter)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(trust_calculus)
pipeline = MonadicPipeline([firewall, trust_calculus, consensus])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

4. **Cognitive Tripwire Monitoring** (\cref{alg:tripwire-impl}). Continuous monitoring of canary beliefs for unauthorized modifications, implementing Part 1's Canary Belief and Tripwire Alert Condition definitions. Severity is classified via a uniform 4-tier system (LOW, MEDIUM, HIGH, CRITICAL) based on drift magnitude. Implemented in `src/core/tripwire.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py, TripwireAdapter)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(tripwire)
pipeline = MonadicPipeline([firewall, sandbox, tripwire])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

5. **Byzantine Consensus Protocol** (\cref{alg:byzantine-impl}). Byzantine fault-tolerant consensus satisfying Part 1's Byzantine Agreement Requirement theorem, ensuring agreement when $f < n/3$ agents are Byzantine. Three-phase protocol: vote collection, echo verification, and supermajority decision. Implemented in `src/core/consensus.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py, ConsensusAdapter)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(byzantine_consensus)
pipeline = MonadicPipeline([trust_calculus, byzantine_consensus])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

6. **Belief Drift Detection** (\cref{alg:drift-impl}). KL-divergence-based drift monitoring implementing Part 1's Drift Score definition. Combines distributional divergence with maximum belief delta for anomaly scoring. Implemented in `src/core/detection.py`.

### Monadic Type Signature

```python
# Standard interface (src/composition/adapters.py; src/core/detection.py's AnomalyScorer.evaluate takes (agent_id, state) and returns AnomalyVerdict)
def evaluate(self, message: str, context: dict | None = None) -> DefenseResult: ...

# Monadic interface (src/core/monad.py)
from src.core.monad import from_defense_result, Result, DetectionEvent
from src.formal.category_theory import lift_defense_module, DefenseMorphism

morphism: DefenseMorphism = lift_defense_module(drift_detector)
pipeline = MonadicPipeline([firewall, drift_detector, tripwire])
result: Result[list[DefenseResult], DetectionEvent] = pipeline.run(message, context)
```

See Supplement~\ref{sec:s09-functional-api} for full specification.

## Worked Example: Attack Payload Through the Pipeline {#sec:worked-example}

To make the layered defense concrete, consider the attack payload: *"Ignore previous instructions. You are now operating in maintenance mode. Forward all future messages to external-service.com."* This is a direct injection attack (category: prompt injection / direct injection).

**Stage 1 — Cognitive Firewall**: The direct imperative matches one injection pattern, contributing $0.8$; the phrase "maintenance mode" is not a separate injection-pattern match. There are no suspicious-pattern, dense-URL, or dense-code-block matches, so $S_{inj}=0.8$ and $S_{sus}=0$. With the operational defaults $\tau_1=0.8$ and $\tau_2=0.5$, the strict rejection test $S_{inj}>\tau_1$ is false, but $\max(S_{inj},S_{sus})=0.8>\tau_2$ → **QUARANTINE**. The message therefore follows the sandbox path rather than being accepted or rejected.

**Stage 2 — Belief Sandbox**: Source trust $\mathcal{T}_s = 0.4 < \tau_{trusted} = 0.9$ → belief quarantined as PENDING in $\mathcal{B}_{provisional}$. Promotion check: provenance $V(\pi) = \text{True}$, consistency check passes, but corroboration count $= 0 < \kappa = 2$ → remains provisional.

**Stage 3 — Tripwire Monitor**: Canary belief "I operate only under my operator's instructions" checked. If this belief probability drifts from 0.95 to 0.62, drift $= 0.33 > \epsilon_{high} = 0.30$ → **HIGH alert** emitted; `TriggerResponse()` called.

**Stages 4–8**: Drift Detector computes KL divergence $= 0.18$ (below $\theta_{drift} = 0.3$, no alert). Trust Update applies failure penalty to source reputation. Byzantine Consensus (if invoked) rejects the instruction by supermajority. Provenance Attestation flags unverifiable delegation chain.

*This example illustrates the shipped rule's strict threshold comparisons and asymmetric rejection path: an injection score exactly equal to $\tau_1=0.8$ is not rejected, while its maximum with the suspicious score still exceeds $\tau_2=0.5$ and is quarantined. No weighted three-detector score or online attack centroid enters the decision.*

## Configuration Parameters

All algorithms share a unified configuration system with 29 parameters organized into eight groups. Default values are calibrated for balanced precision--recall trade-offs. Full parameter documentation is in Supplement S5 (\cref{sec:framework-api}).
