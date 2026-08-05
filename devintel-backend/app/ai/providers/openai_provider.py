"""OpenAI provider implementation.

Wraps the existing OpenAI client with circuit breaker and retry logic,
now conforming to the BaseAIProvider interface so the orchestrator
can route requests through it.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any, Optional

import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.models import (
    AIProvider,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    TokenUsage,
    estimate_cost,
)
from app.ai.providers.base import BaseAIProvider
from app.core.config import settings
from app.core.exceptions import (
    CircuitBreakerError as CircuitBreakerException,
    EmbeddingError,
    ExternalServiceError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Circuit breaker (reused from the legacy OpenAI client)
# ---------------------------------------------------------------------------


class _CircuitBreaker:
    """Circuit breaker to prevent cascading failures to OpenAI."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"

    def can_execute(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if (
                self._last_failure_time
                and time.time() - self._last_failure_time > self._recovery_timeout
            ):
                self._state = "HALF_OPEN"
                return True
            return False
        return False

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            logger.warning(
                "Circuit breaker OPEN after %d failures",
                self._failure_count,
            )


_circuit_breaker = _CircuitBreaker()

_RETRYABLE = (
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.RateLimitError,
)


# ---------------------------------------------------------------------------
# Provider implementation
# ---------------------------------------------------------------------------


class OpenAIProvider(BaseAIProvider):
    """Concrete OpenAI provider with circuit breaker and retry logic."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._default_chat_model = settings.OPENAI_CHAT_MODEL
        self._default_embedding_model = settings.OPENAI_EMBEDDING_MODEL

    @property
    def provider_name(self) -> str:
        return "openai"

    # -- Completion --------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(_RETRYABLE),
        reraise=True,
    )
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Non-streaming chat completion."""
        if not _circuit_breaker.can_execute():
            raise CircuitBreakerException(
                "OpenAI API temporarily unavailable due to repeated failures"
            )

        model = request.model or self._default_chat_model
        start = time.perf_counter()

        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [m.model_dump(exclude_none=True) for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if request.json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if request.tools:
                kwargs["tools"] = request.tools
            if request.tool_choice:
                kwargs["tool_choice"] = request.tool_choice

            response = await self._client.chat.completions.create(**kwargs)
            _circuit_breaker.record_success()

            message = response.choices[0].message
            latency_ms = (time.perf_counter() - start) * 1000

            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            # Determine content vs tool_calls
            tool_calls = None
            content = message.content or ""
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            return CompletionResponse(
                content=content,
                tool_calls=tool_calls,
                raw_message=message,
                provider=AIProvider.OPENAI,
                model=model,
                operation_id=request.operation_id,
                token_usage=usage,
                latency_ms=latency_ms,
                cost_estimate_usd=estimate_cost(model, usage),
            )

        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error("OpenAI completion failed: %s", e)
            raise ExternalServiceError(
                message="Failed to generate chat completion",
                details={"error": str(e)},
            ) from e

    # -- Streaming ---------------------------------------------------------

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """Streaming chat completion — yields content tokens."""
        if not _circuit_breaker.can_execute():
            raise CircuitBreakerException(
                "OpenAI API temporarily unavailable due to repeated failures"
            )

        model = request.model or self._default_chat_model

        try:
            stream_resp = await self._client.chat.completions.create(
                model=model,
                messages=[m.model_dump(exclude_none=True) for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )

            async for chunk in stream_resp:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            _circuit_breaker.record_success()

        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error("OpenAI stream failed: %s", e)
            raise ExternalServiceError(
                message="Failed to stream chat completion",
                details={"error": str(e)},
            ) from e

    # -- Embeddings --------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(_RETRYABLE),
        reraise=True,
    )
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for a batch of texts."""
        if not _circuit_breaker.can_execute():
            raise CircuitBreakerException(
                "OpenAI API temporarily unavailable due to repeated failures"
            )

        model = request.model or self._default_embedding_model
        start = time.perf_counter()

        try:
            response = await self._client.embeddings.create(
                model=model,
                input=request.texts,
            )
            _circuit_breaker.record_success()

            latency_ms = (time.perf_counter() - start) * 1000
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            return EmbeddingResponse(
                embeddings=[item.embedding for item in response.data],
                provider=AIProvider.OPENAI,
                model=model,
                operation_id=request.operation_id,
                token_usage=usage,
                latency_ms=latency_ms,
                cost_estimate_usd=estimate_cost(model, usage),
            )

        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error("OpenAI embedding failed: %s", e)
            raise EmbeddingError(
                message="Failed to generate embeddings",
                details={"error": str(e)},
            ) from e

    # -- Health check ------------------------------------------------------

    async def health_check(self) -> bool:
        """Quick check that OpenAI responds."""
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
