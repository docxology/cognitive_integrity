"""Multi-agent architecture adapters for the Cognitive Security Framework.

Provides abstract base classes and concrete adapters for six production
multi-agent frameworks: Claude Code, AutoGPT, CrewAI, LangGraph,
MetaGPT, and CAMEL.
"""

from .autogpt import AutoGPTAdapter
from .base import ArchitectureAdapter, ArchitectureProfile
from .camel import CamelAdapter
from .claude_code import ClaudeCodeAdapter
from .crewai import CrewAIAdapter
from .langgraph import LangGraphAdapter
from .metagpt import MetaGPTAdapter

__all__ = [
    # Base
    "ArchitectureAdapter",
    "ArchitectureProfile",
    # Adapters
    "AutoGPTAdapter",
    "CamelAdapter",
    "ClaudeCodeAdapter",
    "CrewAIAdapter",
    "LangGraphAdapter",
    "MetaGPTAdapter",
]
