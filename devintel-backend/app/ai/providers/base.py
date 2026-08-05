"""Abstract base for AI providers.

Every concrete provider (OpenAI, Anthropic, etc.) must implement this
protocol so the orchestrator can swap providers without touching callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Optional

from app.ai.models import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class BaseAIProvider(ABC):
    """Abstract interface for AI providers.

    Concrete implementations handle authentication, retries, and
    provider-specific API translation.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g. 'openai')."""
        ...

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate a chat completion (non-streaming).

        Args:
            request: Typed completion request with messages and parameters.

        Returns:
            Typed response with content, token usage, and metadata.
        """
        ...

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """Stream a chat completion token-by-token.

        Args:
            request: Typed completion request.

        Yields:
            Content tokens as they arrive from the provider.
        """
        ...

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for one or more texts.

        Args:
            request: Typed embedding request with texts.

        Returns:
            Typed response with embedding vectors and metadata.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the provider is reachable. Default: True."""
        return True
