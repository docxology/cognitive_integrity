# `src/agents/` — Agent Reference

Guidance for agents modifying the LLM-backed multiagent simulation package.

## Purpose

Provides real Ollama-integrated LLM agents and topology-aware orchestration used in Paper 2's **LLM-backed validation tier**. See [`README.md`](README.md) for API documentation and the [`../AGENTS.md`](../AGENTS.md) for package-wide rules.

## Rules

- **Real LLM inference only** — no mocking of Ollama responses. Tests that require Ollama must use `@pytest.mark.requires_ollama` and skip when unavailable.
- **Deterministic** — accept `seed` in all public entry points; record seed + model version in `SimulationResult`.
- **Topology-aware** — any new topology must have a matching adapter in `../architectures/` and a fixture in `tests/`.
- **Honest latency** — `AgentResponse.latency_ms` is the real wall-clock inference time; do not substitute placeholder values.

## When Editing

- Update [`README.md`](README.md) if you change public API.
- Update [`../README.md`](../README.md) manuscript-to-code anchor if a new module realizes a manuscript claim.
- Add tests in `tests/test_agents.py` that exercise the real Ollama path.

## Cross-Paper Reference

This package is cited by Paper 3 §3 and Paper 4 §2 (see [`../AGENTS.md`](../AGENTS.md) for the full cross-reference discipline).
