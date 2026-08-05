"""Typed contracts for the AI orchestration layer.

All AI interactions flow through these models — they serve as the contract
between feature services and the underlying provider implementations.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AIProvider(str, Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    LOCAL = "local"


class AIOperation(str, Enum):
    """Type of AI operation."""

    CHAT_COMPLETION = "chat_completion"
    CHAT_STREAM = "chat_stream"
    EMBEDDING = "embedding"
    EMBEDDING_BATCH = "embedding_batch"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AIMessage(BaseModel):
    """A single message in a conversation."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    name: Optional[str] = None


class CompletionRequest(BaseModel):
    """Request for a chat completion (streaming or non-streaming)."""

    messages: list[AIMessage]
    model: Optional[str] = None  # None = use provider default
    temperature: float = 0.7
    max_tokens: int = 1000
    json_mode: bool = False
    tools: Optional[list[dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    stream: bool = False

    # Metadata for logging / metrics — not sent to the provider
    agent: Optional[str] = None
    operation_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    repo_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


class EmbeddingRequest(BaseModel):
    """Request for embedding generation."""

    texts: list[str]
    model: Optional[str] = None  # None = use provider default

    # Metadata
    agent: Optional[str] = None
    operation_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    repo_id: Optional[UUID] = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TokenUsage(BaseModel):
    """Token usage breakdown."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    """Response from a chat completion."""

    content: str = ""
    tool_calls: Optional[list[dict[str, Any]]] = None
    raw_message: Optional[Any] = None  # Provider-specific message object

    # Metadata
    provider: AIProvider = AIProvider.OPENAI
    model: str = ""
    operation_id: str = ""
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    cost_estimate_usd: float = 0.0
    cached: bool = False


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""

    embeddings: list[list[float]]

    # Metadata
    provider: AIProvider = AIProvider.OPENAI
    model: str = ""
    operation_id: str = ""
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    cost_estimate_usd: float = 0.0


# ---------------------------------------------------------------------------
# Cost estimation (approximate per-1K-token rates, USD)
# ---------------------------------------------------------------------------

_COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "text-embedding-3-small": {"prompt": 0.00002, "completion": 0.0},
    "text-embedding-3-large": {"prompt": 0.00013, "completion": 0.0},
}


def estimate_cost(model: str, usage: TokenUsage) -> float:
    """Estimate cost in USD for a given model and token usage."""
    rates = _COST_PER_1K_TOKENS.get(model, {"prompt": 0.0, "completion": 0.0})
    prompt_cost = (usage.prompt_tokens / 1000) * rates["prompt"]
    completion_cost = (usage.completion_tokens / 1000) * rates["completion"]
    return round(prompt_cost + completion_cost, 6)
