"""OpenAI API client with circuit breaker and retry logic."""

import time
from collections.abc import AsyncGenerator
from typing import Any, Optional

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import CircuitBreakerError as CircuitBreakerException
from app.core.exceptions import EmbeddingError, ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAICircuitBreaker:
    """Circuit breaker for OpenAI API calls to prevent cascading failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"

    def can_execute(self) -> bool:
        """Check if the circuit allows execution."""
        if self._state == "CLOSED":
            return True

        if self._state == "OPEN":
            if (self._last_failure_time and
                time.time() - self._last_failure_time > self._recovery_timeout):
                self._state = "HALF_OPEN"
                return True
            return False

        return False

    def record_success(self) -> None:
        """Record a successful call."""
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            logger.warning(f"Circuit breaker OPEN for OpenAI API after {self._failure_count} failures")


_circuit_breaker = OpenAICircuitBreaker()


class OpenAIClient:
    """OpenAI API client wrapper with circuit breaker and retry logic."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)),
        reraise=True,
    )
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text with circuit breaker protection."""
        if not _circuit_breaker.can_execute():
            logger.warning("OpenAI circuit breaker is OPEN, skipping embedding generation")
            raise CircuitBreakerException("OpenAI API temporarily unavailable due to repeated failures")

        try:
            response = await self.client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            _circuit_breaker.record_success()
            return response.data[0].embedding
        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingError(
                message="Failed to generate embedding",
                details={"error": str(e)},
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)),
        reraise=True,
    )
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts with circuit breaker protection."""
        if not _circuit_breaker.can_execute():
            logger.warning("OpenAI circuit breaker is OPEN, skipping batch embedding generation")
            raise CircuitBreakerException("OpenAI API temporarily unavailable due to repeated failures")

        try:
            response = await self.client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=texts,
            )
            _circuit_breaker.record_success()
            return [item.embedding for item in response.data]
        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingError(
                message="Failed to generate batch embeddings",
                details={"error": str(e)},
            ) from e

    async def chat_completion_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = settings.OPENAI_MAX_TOKENS,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion with circuit breaker protection."""
        if not _circuit_breaker.can_execute():
            logger.warning("OpenAI circuit breaker is OPEN, skipping chat stream")
            raise CircuitBreakerException("OpenAI API temporarily unavailable due to repeated failures")

        try:
            stream = await self.client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            _circuit_breaker.record_success()

        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error(f"Failed to stream chat completion: {e}")
            raise ExternalServiceError(
                message="Failed to stream chat completion",
                details={"error": str(e)},
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = settings.OPENAI_MAX_TOKENS,
        json_mode: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Any:
        """
        Generate chat completion (non-streaming) with circuit breaker protection.
        Returns the string content if no tools are used, else returns the full message object.
        """
        if not _circuit_breaker.can_execute():
            logger.warning("OpenAI circuit breaker is OPEN, skipping chat completion")
            raise CircuitBreakerException("OpenAI API temporarily unavailable due to repeated failures")

        try:
            kwargs = {
                "model": settings.OPENAI_CHAT_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            _circuit_breaker.record_success()

            if hasattr(message, "tool_calls") and message.tool_calls:
                return message

            return message.content or ""
        except CircuitBreakerException:
            raise
        except Exception as e:
            _circuit_breaker.record_failure()
            logger.error(f"Failed to generate chat completion: {e}")
            raise ExternalServiceError(
                message="Failed to generate chat completion",
                details={"error": str(e)},
            ) from e
