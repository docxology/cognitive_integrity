"""LLM-backed multiagent simulation for CIF evaluation.

Provides real LLM agents organized in architecture-specific topologies
(Claude Code, AutoGPT, CrewAI, LangGraph) that process
attack payloads through genuine LLM inference, enabling CIF defense
modules to monitor actual agent interactions.

Modules:
    llm_agent: Core LLMAgent class with Ollama integration
    multiagent_system: Topology-aware agent orchestration
"""

from .llm_agent import AgentMessage, AgentResponse, LLMAgent, OllamaConfig
from .multiagent_system import MultiAgentSystem, SimulationResult

__all__ = [
    "AgentMessage",
    "AgentResponse",
    "LLMAgent",
    "MultiAgentSystem",
    "OllamaConfig",
    "SimulationResult",
]
