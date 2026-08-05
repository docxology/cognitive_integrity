"""LLM-backed agent for multiagent simulation.

Each ``LLMAgent`` wraps a local Ollama model instance and maintains its
own conversation context.  Agents are given architecture-specific system
prompts that define their role, trust boundaries, and communication
constraints within the multiagent topology.

The agent communicates via ``AgentMessage`` objects that carry metadata
(sender, receiver, timestamp) alongside content, enabling CIF defense
modules to monitor inter-agent interactions.

Usage::

    agent = LLMAgent(
        agent_id="researcher_0",
        role="researcher",
        system_prompt="You are a researcher agent in a CrewAI crew...",
    )
    response = agent.process_message(
        AgentMessage(sender="coordinator", content="Analyze this input...")
    )
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM backend.

    Attributes:
        base_url: Ollama server URL.
        model: Model name to use for inference.
        temperature: Sampling temperature (0.0 = deterministic).
        max_tokens: Maximum response length in tokens.
        timeout: HTTP request timeout in seconds.
        seed: Random seed for reproducible outputs.
    """

    base_url: str = "http://localhost:11434"
    model: str = "gemma3:4b"
    temperature: float = 0.7
    max_tokens: int = 256
    timeout: float = 120.0
    seed: Optional[int] = 42


# ---------------------------------------------------------------------------
# Data classes for agent communication
# ---------------------------------------------------------------------------

@dataclass
class AgentMessage:
    """A message passed between agents or from the environment.

    Attributes:
        sender: ID of the sending agent (or "environment" / "user").
        content: Text content of the message.
        receiver: ID of the intended recipient (None = broadcast).
        metadata: Additional context (attack category, step number, etc.).
        timestamp: Wall-clock time when the message was created.
    """

    sender: str
    content: str
    receiver: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResponse:
    """Response from an LLM agent.

    Attributes:
        agent_id: ID of the responding agent.
        role: Role of the responding agent.
        content: Generated text response.
        raw_content: Raw LLM output before any post-processing.
        latency_ms: Time taken for LLM inference in milliseconds.
        model: Model used for generation.
        input_message: The message that triggered this response.
    """

    agent_id: str
    role: str
    content: str
    raw_content: str
    latency_ms: float
    model: str
    input_message: Optional[AgentMessage] = None


# ---------------------------------------------------------------------------
# LLM Agent
# ---------------------------------------------------------------------------

class LLMAgent:
    """An LLM-backed agent in a multiagent system.

    Each agent has a unique identity, role, and system prompt that defines
    its behavior within the architecture topology.  Messages are processed
    through a real Ollama LLM call, and conversation history is maintained
    for multi-turn interactions within a simulation step.

    Args:
        agent_id: Unique identifier for this agent.
        role: Role label (e.g., "researcher", "orchestrator", "reviewer").
        system_prompt: Architecture- and role-specific system prompt.
        config: Ollama configuration. Uses defaults if not provided.
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        system_prompt: str,
        config: Optional[OllamaConfig] = None,
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.config = config or OllamaConfig()
        self._history: List[Dict[str, str]] = []
        self._total_calls = 0
        self._total_latency_ms = 0.0

        # Initialize history with system prompt
        self._history.append({"role": "system", "content": self.system_prompt})

        logger.info(
            "LLMAgent initialized: id=%s role=%s model=%s",
            self.agent_id, self.role, self.config.model,
        )

    def process_message(self, message: AgentMessage) -> AgentResponse:
        """Process an incoming message through the LLM.

        Sends the message content to Ollama with the agent's conversation
        history and returns the generated response.

        Args:
            message: Incoming message to process.

        Returns:
            AgentResponse with the LLM's generated text and metadata.

        Raises:
            ConnectionError: If Ollama is not reachable.
            RuntimeError: If the LLM returns an error.
        """
        # Format the user message with sender context
        user_content = self._format_incoming(message)
        self._history.append({"role": "user", "content": user_content})

        # Call Ollama
        start_time = time.time()
        raw_response = self._call_ollama()
        latency_ms = (time.time() - start_time) * 1000

        # Track metrics
        self._total_calls += 1
        self._total_latency_ms += latency_ms

        # Store in history
        self._history.append({"role": "assistant", "content": raw_response})

        logger.debug(
            "Agent %s responded in %.1fms (%d tokens)",
            self.agent_id, latency_ms, len(raw_response.split()),
        )

        return AgentResponse(
            agent_id=self.agent_id,
            role=self.role,
            content=raw_response,
            raw_content=raw_response,
            latency_ms=latency_ms,
            model=self.config.model,
            input_message=message,
        )

    def reset_context(self) -> None:
        """Clear conversation history, keeping only the system prompt."""
        self._history = [{"role": "system", "content": self.system_prompt}]

    @property
    def call_count(self) -> int:
        """Total number of LLM calls made by this agent."""
        return self._total_calls

    @property
    def avg_latency_ms(self) -> float:
        """Average latency per call in milliseconds."""
        if self._total_calls == 0:
            return 0.0
        return self._total_latency_ms / self._total_calls

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_incoming(self, message: AgentMessage) -> str:
        """Format an incoming message for the LLM prompt."""
        parts = []
        if message.sender and message.sender != "environment":
            parts.append(f"[Message from {message.sender}]")
        parts.append(message.content)
        return "\n".join(parts)

    def _call_ollama(self) -> str:
        """Make a synchronous call to the Ollama chat API.

        Returns:
            The content of the assistant's response.

        Raises:
            ConnectionError: If Ollama is not reachable.
            RuntimeError: If the response is empty or contains an error.
        """
        url = f"{self.config.base_url}/api/chat"

        payload = {
            "model": self.config.model,
            "messages": self._history,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        if self.config.seed is not None:
            payload["options"]["seed"] = self.config.seed  # type: ignore[index]

        try:
            response = requests.post(
                url, json=payload, timeout=self.config.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                raise RuntimeError(
                    f"Ollama error for agent {self.agent_id}: {data['error']}"
                )

            content = data.get("message", {}).get("content", "")
            if not content:
                logger.warning(
                    "Empty response from Ollama for agent %s", self.agent_id,
                )
                return "(no response)"

            # Strip thinking tags (qwen-style)
            import re
            content = re.sub(
                r"<think[^>]*>[\s\S]*?[\n\s]+response", "", content,
                flags=re.IGNORECASE | re.DOTALL,
            ).strip()

            return content

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot reach Ollama at {self.config.base_url} "
                f"for agent {self.agent_id}: {e}"
            ) from e
        except requests.exceptions.Timeout:
            raise ConnectionError(
                f"Ollama request timed out after {self.config.timeout}s "
                f"for agent {self.agent_id}"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama HTTP error for agent {self.agent_id}: {e}"
            ) from e

    def __repr__(self) -> str:
        return (
            f"LLMAgent(id={self.agent_id!r}, role={self.role!r}, "
            f"model={self.config.model!r}, calls={self._total_calls})"
        )
