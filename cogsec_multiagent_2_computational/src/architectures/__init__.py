"""Multi-agent architecture adapters for the Cognitive Security Framework.

Provides abstract base classes and concrete adapters for four production
multi-agent frameworks: Claude Code, AutoGPT, CrewAI, and LangGraph.
"""

from __future__ import annotations

from .autogpt import AutoGPTAdapter
from .base import ArchitectureAdapter, ArchitectureProfile
from .claude_code import ClaudeCodeAdapter
from .crewai import CrewAIAdapter
from .langgraph import LangGraphAdapter

__all__ = [
    # Base
    "ArchitectureAdapter",
    "ArchitectureProfile",
    # Adapters
    "AutoGPTAdapter",
    "ClaudeCodeAdapter",
    "CrewAIAdapter",
    "LangGraphAdapter",
]
