# `src/agents/` — LLM-Backed Multiagent Simulation

Real LLM-backed multiagent simulation used in Paper 2's **LLM-backed validation tier** (§5 Results). Provides Ollama-integrated agents organized in architecture-specific topologies (Claude Code, AutoGPT, CrewAI, LangGraph) that process attack payloads through genuine LLM inference — enabling the CIF defense modules in [`../core/`](../core/) to monitor actual agent interactions, not synthetic traces.

## Series Position

Part 2 of three in the *Cognitive Security for Multiagent Operators* series. The results produced by this package appear in:

- **Abstract** — "LLM-backed multiagent validation (N=10, Gemma 3 4B via Ollama) achieving 80–100% detection across Claude Code and CrewAI topologies"
- **§5 Results** — LLM-backed evaluation tier
- Cited by Part 3+4 §3 "Evidence" and §9 "Applications"

## Modules

| Module | Purpose | Key Exports |
| ------ | ------- | ----------- |
| `llm_agent.py` | Core `LLMAgent` class with Ollama integration (chat, streaming, retries) | `LLMAgent`, `OllamaConfig`, `AgentMessage`, `AgentResponse` |
| `multiagent_system.py` | Topology-aware agent orchestration across the four production architectures | `MultiAgentSystem`, `SimulationResult` |

## Quick Usage

```python
from src.agents import LLMAgent, OllamaConfig, MultiAgentSystem

# 1. Single LLM agent talking to local Ollama
config = OllamaConfig(model="gemma3:4b", host="http://localhost:11434")
agent = LLMAgent(role="researcher", config=config)
response = agent.respond(
    AgentMessage(sender="user", content="Summarize this report.")
)
print(response.content, response.latency_ms)

# 2. Full multiagent topology (e.g., CrewAI-style sequential pipeline)
system = MultiAgentSystem.from_topology(
    topology="crewai",
    n_agents=4,
    config=config,
)
result = system.process_attack(
    attack_payload="<adversarial prompt>",
    seed=42,
)
print(result.detected, result.defense_invocations)
```

## Prerequisites

- **Ollama** running locally (`ollama serve`)
- Model pulled: `ollama pull gemma3:4b`
- `src.core.*` defense modules importable (Firewall, Sandbox, Tripwire, Consensus, etc.)

The test fixture in `tests/conftest.py` auto-starts Ollama if missing and skips gracefully when unavailable — see the conditional-skip convention in [`../AGENTS.md`](../AGENTS.md).

## Topology Adapters

`MultiAgentSystem.from_topology(...)` dispatches to topology-specific orchestrators in [`../architectures/`](../architectures/):

| Topology | Architecture Module |
| -------- | ------------------- |
| `claude_code` | `src.architectures.claude_code` (hierarchical, 1 + n dynamic) |
| `autogpt` | `src.architectures.autogpt` (autonomous, 1 + plugins) |
| `crewai` | `src.architectures.crewai` (role-based, 3–10 fixed) |
| `langgraph` | `src.architectures.langgraph` (state machine) |

## No-Mocks Policy

This package uses **real Ollama inference**. Tests that require it are marked `@pytest.mark.requires_ollama` and skip when Ollama is unavailable — they do **not** mock the LLM response. See [`../AGENTS.md`](../AGENTS.md) for the full no-mocks policy.

## Manuscript Anchor

| Claim | Location |
| ----- | -------- |
| 80–100% detection across Claude Code and CrewAI | Abstract, §5 Results |
| N=10 per topology | §4 Experimental Setup |
| Gemma 3 4B via Ollama | §4 Experimental Setup |
