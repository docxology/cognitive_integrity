# Architecture Adapters - Agent Reference

Adapters for 4 production multiagent architectures.

## Modules

### base.py

Abstract base class for architecture adapters.

**Key Classes:**

- `ArchitectureAdapter` - Base adapter interface
- `AgentNode` - Represents agent in topology
- `CommunicationChannel` - Inter-agent communication

### claude_code.py

Adapter for Claude Code (hierarchical orchestrator).

### autogpt.py

Adapter for AutoGPT (autonomous + plugins).

### crewai.py

Adapter for CrewAI (role-based teams).

### langgraph.py

Adapter for LangGraph (graph-based workflows).

### metagpt.py

Adapter for MetaGPT (SOP-driven).

### camel.py

Adapter for CAMEL (debate-based).

## Usage

```python
from src.architectures import ClaudeCodeAdapter, AutoGPTAdapter

adapter = ClaudeCodeAdapter()
topology = adapter.build_topology(n_agents=5)
attack_surface = adapter.get_attack_surface()
```

## Architecture Properties

| Architecture | Topology | Trust Model | Attack Surface |
|--------------|----------|-------------|----------------|
| Claude Code | Hierarchical | Principal-based | Orchestrator |
| AutoGPT | Star | Plugin-based | Plugins |
| CrewAI | Role graph | Role-based | Handoffs |
| LangGraph | DAG | Edge-based | Nodes |
| MetaGPT | Sequential | SOP-based | Interfaces |
| CAMEL | Debate pair | Symmetric | Messages |
