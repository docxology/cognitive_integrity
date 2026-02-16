# Deployment Profiles: Evaluated Configurations from Part 2 {#sec:deployment}

In Part 2, we evaluated specific configurations of the Cognitive Integrity Framework to understand how different tuning parameters affected security and performance outcomes. The following profiles are derived directly from the **Parameter Sensitivity Analysis** (Part 2, Section 5.3) and **Architecture-Specific Results** (Part 2, Section 5.1).

## Profile A: The "Internal Tool" Baseline (Low Latency)

This profile corresponds to the "High Usability" configuration tested in the sensitivity analysis ($\delta=0.95$). It is designed for low-risk, human-in-the-loop environments.

**Configuration Parameters**:

* **Trust Decay ($\delta$)**: `0.95`. Maintained >50% trust retention even after 13 delegation hops.
* **Firewall Sensitivity**: Relaxed ($\tau=0.9$).
* **Consensus**: Simple Majority.

**Observed Performance** (Sensitivity Table 5.2):

* **Latency Overhead**: Minimal (~15% baseline).
* **Detection Rate**: **87%** (vs 94% optimal).
* **Trade-off**: The high trust decay allows for fluid, deep delegation chains but increases vulnerability to subtle trust laundering ($\Omega_4$).

## Profile B: The "Customer Facing" Baseline (Balanced)

This profile corresponds to the **Empirically Optimal Configuration** identified in Part 2 (Table 5.6), which balances security guarantees with operational overhead.

**Configuration Parameters**:

* **Trust Decay ($\delta$)**: `0.80`. At this setting, trust degrades to <50% after 3 hops, strictly bounding the "radius of effective delegation."
* **Firewall Sensitivity**: Balanced ($\tau=0.5$).
* **Consensus**: Variable (Architecture Dependent).

**Observed Performance** (Sensitivity Table 5.2):

* **Latency Overhead**: Reduced detection latency (~8.5s for drift detection).
* **Detection Rate**: **94%**.
* **Resilience**: Maximizes the F1 score, providing the best empirically observed trade-off between False Positives (0.06) and True Positives.

## Profile C: The "Autonomous Operator" Baseline (High Assurance)

This profile corresponds to the "Byzantine-Heavy" configuration tested in Part 2 (Table 2.8). It is required for high-stakes, unsupervised environments.

**Configuration Parameters**:

* **Trust Decay ($\delta$)**: `0.60`. Aggressive decay. Trust halves every 1.3 hops, enforcing a strictly flat command structure.
* **Firewall Sensitivity**: Strict ($\tau=0.4$).
* **Consensus**: Byzantine Fault Tolerance ($n \ge 3f+1$).

**Observed Performance** (Sensitivity Table 5.3):

* **Latency Overhead**: Significant (+35-48% depending on corroboration count).
* **Detection Rate**: **95%** (general) to **98%** (LangGraph-specific).
* **Resilience**: Specifically tunes parameters to resist coordination attacks ($\Omega_4$), accepting higher latency for a near-zero semantic drift rate.

---

## Architecture-Specific Observations

Beyond the parameter profiles, Part 2's architecture adapters revealed specific interactions between the defense framework and the underlying agent topology.

### LangGraph (State Machines)

**Observation**: LangGraph architectures achieved the highest overall detection rates (98%) in our tests (Part 2, Table 5.6).
**Mechanism**: The explicit definition of state transitions allowed for rigorous **Invariant Checking**. Invalid state transitions were detected deterministically by the framework.

### CrewAI (Role-Based)

**Observation**: CrewAI architectures performed best against "Trust Exploitation" attacks (94% detection) (Part 2, Table 5.4).
**Mechanism**: The framework's role definitions acted as implicit **Identity Tripwires**. When an agent attempted to act outside its defined role, the behavior was flagged as a role violation.

---

## Minimal Viable Implementation

We also evaluated a "Minimal Viable Implementation" (MVI) to determine the baseline efficacy of the framework's core components.

**The Setup**:

1. **Trust Decay**: $\delta = 0.80$ (The optimal balance point).
2. **Cognitive Firewall**: Ingress only.
3. **Tripwires**: One per agent.

**Result**: Even this minimal setup shifted the success rate against low-effort attacks from 100% (Baseline) to <5%, providing a critical first line of defense.
