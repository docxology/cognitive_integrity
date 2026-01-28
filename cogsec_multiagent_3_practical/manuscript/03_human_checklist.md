\newpage

# Human-Actionable Checklist {#sec:human-checklist}

## Pre-Deployment Checklist

Before deploying a multiagent system in production, verify the following. Figure \ref{fig:checklist-flowchart} provides a visual overview of the deployment phases and their associated verification checkpoints.

![Deployment Readiness Checklist. The cognitive security deployment lifecycle consists of four phases: Pre-Deployment (threat model completion, CIF component selection, trust boundary definition), Integration (firewall configuration, sandbox policies, tripwire placement), Testing (red team assessment, penetration testing, failure mode analysis), and Operational (continuous monitoring, alerting, incident response). Each phase must be completed before advancing to the next.](figures/checklist_flowchart.pdf){#fig:checklist-flowchart width=95%}

### Architecture Review

- [ ] **Trust boundaries documented**: All points where trust is assumed vs. verified are explicitly mapped
- [ ] **Delegation limits configured**: Trust decay factor set (recommended: δ = 0.85-0.95)
- [ ] **Agent authentication implemented**: All agents have verifiable identity
- [ ] **Permission boundaries defined**: Each agent has explicit action restrictions

### Defense Configuration

- [ ] **Cognitive firewall enabled**: Input classification active for all external content
- [ ] **Belief sandboxing configured**: Unverified beliefs quarantined pending corroboration
- [ ] **Tripwires planted**: Canary beliefs placed to detect manipulation
- [ ] **Invariants defined**: Core security constraints specified and monitored

### Monitoring Setup

- [ ] **Drift detection active**: Belief distribution monitoring enabled
- [ ] **Alert thresholds configured**: Warning and critical levels set appropriately
- [ ] **Logging comprehensive**: All agent decisions and belief updates recorded
- [ ] **Dashboards available**: Real-time visibility into cognitive state

### Incident Response Prepared

- [ ] **Response procedures documented**: Steps for cognitive attack response defined
- [ ] **Quarantine capability ready**: Ability to isolate compromised agents
- [ ] **Rollback mechanism tested**: Can restore to known-good cognitive state
- [ ] **Escalation path clear**: Who to contact for cognitive security incidents

---

## Operational Checklist (Daily/Weekly)

### Daily Monitoring

- [ ] **Review drift alerts**: Check for unusual belief changes
- [ ] **Verify tripwire integrity**: Confirm canary beliefs unchanged
- [ ] **Check trust metrics**: Monitor for unexpected trust score changes
- [ ] **Review failed consensus**: Investigate any Byzantine fault indications

### Weekly Review

- [ ] **Analyze attack patterns**: Review blocked injection attempts
- [ ] **Audit delegation chains**: Check for unusual delegation patterns
- [ ] **Verify invariant compliance**: Confirm no invariant violations
- [ ] **Update threat intel**: Incorporate new attack techniques into defenses

---

## Incident Response Checklist

When a cognitive attack is suspected:

### Immediate Actions (First 15 Minutes)

- [ ] **Preserve evidence**: Capture current cognitive state before any changes
- [ ] **Assess scope**: Identify which agents and beliefs may be affected
- [ ] **Contain spread**: Isolate affected agents from propagating beliefs
- [ ] **Notify stakeholders**: Alert security team and relevant operators

### Investigation (First Hour)

- [ ] **Trace provenance**: Follow belief origins to identify injection point
- [ ] **Identify attack vector**: Determine how adversarial content entered
- [ ] **Assess impact**: Evaluate what decisions were influenced
- [ ] **Check for persistence**: Verify attack doesn't survive agent restart

### Recovery (Following Hours)

- [ ] **Restore clean state**: Reset affected beliefs to verified baseline
- [ ] **Strengthen defenses**: Update detection patterns based on attack
- [ ] **Verify integrity**: Confirm cognitive state passes all tripwires
- [ ] **Document incident**: Record details for future reference

### Post-Incident (Following Days)

- [ ] **Root cause analysis**: Complete investigation of attack chain
- [ ] **Defense improvements**: Implement countermeasures for attack type
- [ ] **Team debrief**: Share lessons learned with all operators
- [ ] **Update procedures**: Revise checklists based on incident learnings

Figure \ref{fig:timeline} provides an overview of these phases within the broader cognitive security lifecycle.

![Cognitive Security Lifecycle Phases. The deployment lifecycle consists of three major phases: Pre-Deployment (threat modeling, CIF selection, trust boundary definition, invariant specification), Operational (continuous monitoring, trust recalibration, anomaly detection, performance optimization), and Incident Response (quarantine compromised agents, belief state rollback, forensic analysis, recovery and hardening). The relative durations shown reflect typical enterprise deployments where operational monitoring dominates the lifecycle.](figures/timeline.pdf){#fig:timeline width=95%}

---

## Configuration Quick Reference

### Trust Calculus Parameters

| Parameter | Recommended Value | When to Adjust |
|-----------|------------------|----------------|
| Base weight (α) | 0.3 | Increase for stable architectures |
| Reputation weight (β) | 0.4 | Decrease for new deployments |
| Context weight (γ) | 0.3 | Increase for specialized tasks |
| Decay factor (δ) | 0.9 | Decrease for security-critical systems |

### Firewall Thresholds

| Threshold | Recommended Value | Risk Trade-off |
|-----------|------------------|----------------|
| Accept threshold | 0.3 | Lower = more strict, more false positives |
| Reject threshold | 0.7 | Higher = more permissive, more risk |
| Quarantine range | 0.3-0.7 | Narrower = faster decisions, less nuance |

### Tripwire Configuration

| Category | Recommended Count | Placement Strategy |
|----------|------------------|-------------------|
| Identity canaries | 3+ per agent | Core identity beliefs |
| Boundary canaries | 5+ per agent | Permission boundaries |
| Principal canaries | 2+ per agent | Trust relationships |
| Temporal canaries | 1 per agent | Session continuity |
