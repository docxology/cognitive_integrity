\newpage

# Supplementary: Deployment Guide and Integration {#sec:deployment}

This supplementary material provides deployment considerations and integration examples for production CIF deployment. It complements --- and does not replace --- the dedicated practitioner's guidance in unified Part 3+4 (DOI: 10.5281/zenodo.18364130), which presents full deployment guides (Section 5), incident-response playbooks, monitoring strategies, cost--benefit analysis, and operator risk frameworks. For domain-calibrated deployment parameters across ten critical operational sectors (from millisecond-scale drone swarms to year-scale diplomatic agents), see its Sections 9--10.

## Production Deployment Checklist {#sec:production-checklist}

Before deploying CIF in production environments, verify completion of all items:

Table: Production deployment checklist. {#tab:deploy-checklist}

| Checkpoint | Verification | Method |
| --- | --- | --- |
| Signing keys generated | Key files exist | `ls *.pem` |
| TLS certificates valid | Chain verified | `openssl verify` |
| Secrets management configured | Service healthy | Vault health check |
| Firewall thresholds tuned | Config valid | $\tau_1 > \tau_2$ |
| Canary beliefs defined | Count sufficient | $\geq 3$ per agent |
| Consensus configured | Requirement met | $n \geq 3f + 1$ |
| Detection rate validated | Rate acceptable | $\geq 90\%$ on sample |
| Latency within budget | Overhead measured | $\leq 25\%$ overhead |
| Alerting configured | Test passed | Test alert received |

## Pre-Deployment {#sec:pre-deploy}

**Framework installation**:
\begin{itemize}
\item Install Python 3.10+ with pip
\item Install core dependencies: numpy $\geq$ 1.24, scipy $\geq$ 1.10, scikit-learn $\geq$ 1.2
\item Optional: torch $\geq$ 2.0 for semantic embeddings
\item Test GPU availability if using embeddings
\end{itemize}

**Security preparation**:
\begin{itemize}
\item Generate signing key pairs for each agent
\item Configure TLS certificates for inter-agent communication
\item Set up secrets management (e.g., HashiCorp Vault)
\item Configure firewall rules for inter-agent communication
\end{itemize}

### Configuration {#sec:config-checklist}

**Core framework**:
\begin{itemize}
\item Set trust decay factor $\delta$ based on security requirements (\cref{tab:core-params})
\item Configure belief thresholds $\tau_{accept}$, $\tau_{trusted}$
\item Define corroboration count $\kappa$ based on agent pool size
\item Set trust weights $\alpha, \beta, \gamma$ (must sum to 1)
\end{itemize}

**Firewall configuration**:
\begin{itemize}
\item Load injection pattern database
\item Initialize semantic embedding model
\item Configure threshold values $\tau_1$, $\tau_2$ (\cref{tab:firewall-params})
\item Set score weights $w_1, w_2, w_3$
\end{itemize}

**Tripwire setup**:
\begin{itemize}
\item Define canary beliefs for each agent (canary belief definition (Part 1, Definition 7))
\item Set expected probability values
\item Configure drift thresholds (\cref{tab:tripwire-params})
\item Set monitoring intervals
\end{itemize}

**Consensus configuration**:
\begin{itemize}
\item Verify $n \geq 3f + 1$ for expected Byzantine count (Byzantine termination theorem (Part 1, Theorem 5))
\item Set round timeout based on network latency
\item Configure quorum thresholds (\cref{tab:consensus-params})
\end{itemize}

### Post-Deployment Verification {#sec:post-deploy}

**Functional testing**:
\begin{itemize}
\item Send test messages through firewall (expect ACCEPT)
\item Send known attack patterns (expect REJECT/QUARANTINE)
\item Verify tripwire alerts on artificial drift
\item Test consensus with simulated Byzantine agent
\end{itemize}

**Performance validation**:
\begin{itemize}
\item Measure baseline latency
\item Verify overhead within 23\% target (latency overhead theorem (Part 1, Theorem 6))
\item Confirm throughput meets requirements
\item Monitor memory usage over 24h
\end{itemize}

**Security verification**:
\begin{itemize}
\item Run attack corpus subset (sample 100 attacks)
\item Verify detection rate $\geq 90\%$
\item Confirm false positive rate $\leq 10\%$
\item Test escalation paths to human review
\end{itemize}

## Integration Examples {#sec:integration-examples}

### Python Integration {#sec:python-integration}

```python
# Internal module paths
from src.core.firewall import CognitiveFirewall, FirewallConfig
from src.core.sandbox import SandboxManager, SandboxConfig, PromotionCriteria
from src.core.trust import TrustCalculus, TrustConfig

# Initialize components
firewall = CognitiveFirewall(
    config=FirewallConfig(
        tau_1=0.7,   # Hard-reject threshold; scores above this → REJECT
        tau_2=0.5,   # Quarantine threshold; scores in (tau_2, tau_1] → QUARANTINE
    )
)

sandbox = SandboxManager(
    config=SandboxConfig(
        default_ttl_seconds=3600.0,
        max_provisional_beliefs=1000,
    ),
    promotion_criteria=PromotionCriteria(
        min_corroborations=2,
    ),
)

trust_calc = TrustCalculus(
    config=TrustConfig(
        alpha=0.3, beta=0.5, gamma=0.2,
        decay=0.8,
    )
)

# Process incoming message
def process_message(msg, source):
    # Firewall check
    decision = firewall.classify(msg)
    if decision == "REJECT":
        return None

    # Get trust score
    trust = trust_calc.compute_trust(
        base=0.5, reputation=0.7, context=0.6
    )

    # Extract beliefs
    beliefs = extract_beliefs(msg)
    for belief in beliefs:
        if decision == "QUARANTINE" or trust < 0.9:
            sandbox.add_provisional(belief, source, trust)
        else:
            verified_beliefs.add(belief)

    return beliefs
```

### Operational Monitoring {#sec:operational-monitoring}

The following operational metrics emerged as informative during our experimental evaluation and are included here as a reference for production monitoring:

Table: Key operational metrics for CIF monitoring. {#tab:operational-metrics}

| Metric | Threshold | Action | Frequency |
| --- | --- | --- | --- |
| Detection rate (rolling 1h) | $< 0.85$ | Investigate corpus shift | Continuous |
| False positive rate (rolling 1h) | $> 0.15$ | Review threshold calibration | Continuous |
| Firewall latency (p99) | $> 500$ms | Scale or optimize patterns | Every 5 min |
| Trust score distribution entropy | $< 0.5$ (bimodal) | Investigate faction formation | Every 15 min |
| Tripwire alert rate | $> 3\times$ baseline | Escalate to human review | Continuous |
| Consensus round count | $> R_{max}/2$ avg | Check for Byzantine agents | Per consensus |

These thresholds were calibrated against our experimental corpus and may require adjustment based on a given deployment's false-positive tolerance and threat model (see Part 3 for deployment-specific guidance).

### YAML Configuration {#sec:yaml-config}

```yaml
cif:
  version: "1.0"

  trust:
    alpha: 0.3
    beta: 0.5
    gamma: 0.2
    delta: 0.8
    learning_rate: 0.1

  firewall:
    enabled: true
    tau_1: 0.7        # Hard reject; inputs above this score are rejected outright
    tau_2: 0.5        # Quarantine; inputs in (tau_2, tau_1] are sandboxed
    weights:
      injection: 0.4
      semantic: 0.3
      anomaly: 0.3

  sandbox:
    enabled: true
    ttl_default: 3600
    k_corroboration: 2
    max_provisional: 1000

  tripwires:
    enabled: true
    epsilon_critical: 0.30   # Drift above this → CRITICAL alert
    epsilon_high: 0.20       # Drift in (epsilon_high, epsilon_critical] → HIGH
    epsilon_medium: 0.08     # Drift in (epsilon_medium, epsilon_high] → MEDIUM
    check_interval: 30
    canaries:
      - id: "identity"
        belief: "I am Agent-1"
        expected: 1.0
      - id: "principal"
        belief: "My principal is Alice"
        expected: 1.0

  consensus:
    enabled: true
    round_timeout: 5000
    max_rounds: 10

  monitoring:
    prometheus_port: 9090
    log_level: "INFO"
    alert_webhook: "https://alerts.example.com/cif"
```
