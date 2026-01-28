\newpage

# Deployment Considerations {#sec:deployment}

## Risk Profile Assessment

Before configuring cognitive security mechanisms, assess your deployment risk profile:

### Low Risk Profile
**Characteristics**:
- Internal-only deployment
- Non-sensitive data handling
- Human-in-the-loop for all significant actions
- Limited inter-agent communication

**Recommended Configuration**:
- Firewall: Standard thresholds (accept: 0.3, reject: 0.7)
- Trust decay: Moderate (δ = 0.95)
- Consensus: Simple majority for coordination
- Monitoring: Daily review sufficient

### Medium Risk Profile
**Characteristics**:
- Customer-facing but limited autonomy
- Some sensitive data handling
- Periodic human oversight
- Moderate delegation chains

**Recommended Configuration**:
- Firewall: Tighter thresholds (accept: 0.25, reject: 0.65)
- Trust decay: Stricter (δ = 0.9)
- Consensus: 2/3 majority with identity verification
- Monitoring: Real-time alerts for critical events

### High Risk Profile
**Characteristics**:
- Autonomous actions with significant impact
- Sensitive/regulated data handling
- Extended periods without human oversight
- Complex delegation hierarchies

**Recommended Configuration**:
- Firewall: Strict thresholds (accept: 0.2, reject: 0.6)
- Trust decay: Aggressive (δ = 0.85)
- Consensus: Byzantine-tolerant (n ≥ 3f + 1)
- Monitoring: Continuous with immediate alerting

### Understanding Trust Decay

The trust decay parameter δ governs how quickly trust attenuates through delegation chains. Figure \ref{fig:trust-decay} compares the three recommended configurations across delegation depths.

![Trust Decay Comparison: Effect of δ Parameter. These curves demonstrate how effective trust diminishes with delegation depth under different decay configurations. Conservative settings (δ=0.9) allow deeper delegation chains while aggressive settings (δ=0.7) rapidly attenuate trust, limiting attack propagation. The formula $T_{effective} = T_{initial} \times \delta^d$ governs this relationship, where $d$ is delegation depth. Red dashed lines mark the practical trust threshold (10%) below which delegated authority becomes negligible.](figures/trust_decay.pdf){#fig:trust-decay width=95%}

With δ = 0.85 (high-risk recommendation), trust drops to 52% after 4 hops and below 10% after 14 hops, providing strong containment of trust laundering attacks while permitting reasonable delegation depths.

---

## Architecture-Specific Guidance

### Hierarchical Architectures (Claude Code, AutoGPT)

**Characteristics**: Central orchestrator delegates to specialized workers

**Key Risks**:
- Orchestrator compromise cascades to all workers
- Worker escalation can influence orchestrator
- Single point of failure

**Mitigations**:
- Strong orchestrator protection (strictest thresholds)
- Bounded upward influence from workers
- Orchestrator tripwires for identity canaries
- Consider multi-orchestrator redundancy for critical deployments

### Peer-to-Peer Architectures (Camel)

**Characteristics**: Equal-authority agents with lateral communication

**Key Risks**:
- Lateral movement attacks (compromise spreads horizontally)
- Sybil attacks (injected fake agents)
- Consensus manipulation

**Mitigations**:
- Byzantine consensus for all multi-agent decisions
- Strong agent authentication
- Network topology monitoring
- Reputation systems with slow trust building

### Role-Based Architectures (CrewAI)

**Characteristics**: Agents have defined roles with boundaries

**Key Risks**:
- Role impersonation
- Boundary violation
- Role privilege escalation

**Mitigations**:
- Role-based permission boundaries
- Challenge-response for role verification
- Cross-role action validation
- Audit trails for role-based actions

### State Machine Architectures (LangGraph)

**Characteristics**: Explicit state transitions govern behavior

**Key Risks**:
- State corruption
- Invalid transition injection
- State history manipulation

**Mitigations**:
- State integrity verification (hashing)
- Transition validation against allowed graph
- History immutability enforcement
- Rollback capability to known-good states

---

## Scaling Considerations

### Agent Count Scaling

| Agents | Concerns | Recommendations |
|--------|----------|-----------------|
| 2-10 | Individual agent security dominates | Standard CIF deployment |
| 10-100 | Coordination attacks become viable | Byzantine consensus required |
| 100-1000 | Emergent behavior security | Collective monitoring, quorum scaling |
| 1000+ | Colonial cognitive security | Stigmergic defense patterns (see Part 1 Appendix) |

### Latency Budget

CIF introduces overhead. Plan accordingly:

| Component | Typical Latency | When to Optimize |
|-----------|-----------------|------------------|
| Firewall | 5-10ms | Batch classification for bulk inputs |
| Trust computation | 1-2ms | Cache trust scores for stable relationships |
| Sandbox lookup | <1ms | Rarely a bottleneck |
| Tripwire check | 1-5ms | Sample rather than check all beliefs |
| Consensus | 50-200ms | Reserve for critical decisions only |

---

## Integration Patterns

### Pattern 1: Wrapper Integration
Wrap existing agent framework with CIF layer:
- Input: Firewall classification before agent processing
- Inter-agent: Trust verification on message passing
- Output: Invariant checking before action execution

### Pattern 2: Native Integration
Embed CIF into agent architecture:
- Agent maintains own belief sandbox
- Trust calculus integrated with delegation logic
- Tripwires planted during agent initialization

### Pattern 3: Sidecar Integration
Run CIF as separate monitoring service:
- Asynchronous belief drift detection
- Centralized trust matrix management
- Aggregated alert dashboard
