"""Gemini provider implementation.

Wraps the Google GenAI SDK conforming to the BaseAIProvider interface
so the orchestrator can route requests through it.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any, cast

from google import genai
from google.genai import types

from app.ai.models import (
    AIProvider,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    TokenUsage,
)
from app.ai.providers.base import BaseAIProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseAIProvider):
    """Concrete Gemini provider using the google-genai SDK."""

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY or "dummy_gemini_api_key"
        self._client = genai.Client(api_key=api_key)
        self._default_chat_model = settings.GEMINI_CHAT_MODEL
        self._fallback_chat_model = getattr(settings, "GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")
        self._default_embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self._first_token_timeout = getattr(settings, "GEMINI_FIRST_TOKEN_TIMEOUT", 8.0)

    @property
    def provider_name(self) -> str:
        return "gemini"

    # -- Internal Helpers --------------------------------------------------

    def _build_config(self, request: CompletionRequest) -> types.GenerateContentConfig:
        """Build GenerateContentConfig with thinking level and SDK retry options."""
        system_instruction = None
        for m in request.messages:
            if m.role == "system":
                system_instruction = m.content

        # Configure google-genai SDK internal tenacity retries for transient HTTP errors.
        # Short exponential backoff with jitter keeps worst-case connection retry under ~15s.
        retry_options = types.HttpRetryOptions(
            attempts=3,
            initial_delay=1.0,
            max_delay=6.0,
            exp_base=2.0,
            jitter=0.5,
            http_status_codes=[429, 500, 502, 503, 504],
        )
        http_options = types.HttpOptions(retry_options=retry_options)

        # Set low/minimal thinking level for chat answers to prevent extended thinking pauses
        thinking_config = types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.MINIMAL,
        )

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            system_instruction=system_instruction,
            http_options=http_options,
            thinking_config=thinking_config,
        )

        if request.json_mode:
            config.response_mime_type = "application/json"

        return config

    def _build_contents(self, request: CompletionRequest) -> list[types.Content]:
        """Build contents from messages for Gemini API."""
        contents = []
        for m in request.messages:
            if m.role != "system":
                role = "model" if m.role == "assistant" else "user"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=m.content)],
                ))
        return contents

    def _is_transient_error(self, e: Exception) -> bool:
        """Check if an error is transient, 404 (model retired), or a timeout eligible for retry/fallback."""
        if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
            return True
        err_code = getattr(e, "code", None) or getattr(e, "status_code", None)
        if err_code in (404, 408, 429, 500, 502, 503, 504):
            return True
        err_str = str(e).lower()
        return any(
            k in err_str
            for k in (
                "404",
                "not found",
                "not_found",
                "503",
                "429",
                "high demand",
                "overloaded",
                "quota",
                "resource_exhausted",
                "timeout",
                "temporarily unavailable",
                "unavailable",
            )
        )

    # -- Completion --------------------------------------------------------

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Non-streaming chat completion with automatic fallback."""
        model = request.model or self._default_chat_model
        fallback_model = self._fallback_chat_model if self._fallback_chat_model != model else None
        contents = self._build_contents(request)
        config = self._build_config(request)
        start = time.perf_counter()

        try:
            response = await self._client.aio.models.generate_content(
                model=model,
                contents=cast(Any, contents),
                config=config,
            )
        except Exception as e:
            if fallback_model and self._is_transient_error(e):
                logger.warning(
                    "Gemini complete on primary model %s failed (%s). Falling back to %s.",
                    model, e, fallback_model,
                )
                try:
                    model = fallback_model
                    response = await self._client.aio.models.generate_content(
                        model=model,
                        contents=cast(Any, contents),
                        config=config,
                    )
                except Exception as fb_err:
                    logger.error("Gemini completion fallback failed: %s", fb_err)
                    from app.core.exceptions import ExternalServiceError
                    raise ExternalServiceError(
                        message="Failed to generate chat completion via Gemini fallback",
                        details={"error": str(fb_err), "model": fallback_model},
                    ) from fb_err
            else:
                logger.error("Gemini completion failed: %s", e)
                from app.core.exceptions import ExternalServiceError
                raise ExternalServiceError(
                    message="Failed to generate chat completion via Gemini",
                    details={"error": str(e), "model": model},
                ) from e

        latency_ms = (time.perf_counter() - start) * 1000

        usage = TokenUsage(
            prompt_tokens=response.usage_metadata.prompt_token_count or 0 if response.usage_metadata else 0,
            completion_tokens=response.usage_metadata.candidates_token_count or 0 if response.usage_metadata else 0,
            total_tokens=response.usage_metadata.total_token_count or 0 if response.usage_metadata else 0,
        )

        content = response.text or ""

        return CompletionResponse(
            content=content,
            provider=AIProvider.GEMINI,
            model=model,
            operation_id=request.operation_id,
            token_usage=usage,
            latency_ms=latency_ms,
            cost_estimate_usd=0.0,
        )

    # -- Streaming ---------------------------------------------------------

    async def _stream_with_first_token_timeout(
        self,
        model: str,
        contents: list[types.Content],
        request: CompletionRequest,
    ) -> AsyncGenerator[str, None]:
        """Stream chunks, enforcing first_token_timeout on the very first token."""
        config = self._build_config(request)
        stream_response = await self._client.aio.models.generate_content_stream(
            model=model,
            contents=cast(Any, contents),
            config=config,
        )

        stream_iter = stream_response.__aiter__()
        try:
            first_chunk = await asyncio.wait_for(
                stream_iter.__anext__(),
                timeout=self._first_token_timeout,
            )
        except StopAsyncIteration:
            return

        if first_chunk.text:
            yield first_chunk.text

        async for chunk in stream_iter:
            if chunk.text:
                yield chunk.text

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """Streaming chat completion — yields content tokens with transient retry and fallback.

        Only retries or switches to fallback if NO tokens have been yielded yet,
        ensuring response text is never duplicated.
        """
        primary_model = request.model or self._default_chat_model
        fallback_model = self._fallback_chat_model if self._fallback_chat_model != primary_model else None
        contents = self._build_contents(request)
        tokens_yielded = 0

        # Attempt primary model
        try:
            async for token in self._stream_with_first_token_timeout(primary_model, contents, request):
                tokens_yielded += 1
                yield token
            return
        except Exception as e:
            if tokens_yielded > 0 or not fallback_model or not self._is_transient_error(e):
                logger.error("Gemini stream failed on model=%s (tokens_yielded=%d): %s", primary_model, tokens_yielded, e)
                from app.core.exceptions import ExternalServiceError
                raise ExternalServiceError(
                    message="Failed to stream chat completion via Gemini",
                    details={"error": str(e), "model": primary_model},
                ) from e

            logger.warning(
                "Gemini stream on primary model %s failed before first token (%s). Falling back to %s.",
                primary_model, e, fallback_model,
            )

        # Attempt fallback model
        try:
            async for token in self._stream_with_first_token_timeout(fallback_model, contents, request):
                tokens_yielded += 1
                yield token
        except Exception as e:
            logger.error("Gemini stream failed on fallback model=%s: %s", fallback_model, e)
            from app.core.exceptions import ExternalServiceError
            raise ExternalServiceError(
                message="Failed to stream chat completion via Gemini fallback",
                details={"error": str(e), "model": fallback_model},
            ) from e

    # -- Embeddings --------------------------------------------------------

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for a batch of texts."""
        model = request.model or self._default_embedding_model
        start = time.perf_counter()

        try:
            embeddings = await self._embed_with_retry(model, request.texts)

            latency_ms = (time.perf_counter() - start) * 1000

            return EmbeddingResponse(
                embeddings=embeddings,
                provider=AIProvider.GEMINI,
                model=model,
                operation_id=request.operation_id,
                token_usage=TokenUsage(prompt_tokens=0, total_tokens=0),
                latency_ms=latency_ms,
                cost_estimate_usd=0.0,
            )

        except Exception as e:
            logger.error("Gemini embedding failed: %s", e)
            from app.core.exceptions import EmbeddingError
            raise EmbeddingError(
                message="Failed to generate embeddings via Gemini",
                details={"error": str(e)},
            ) from e

    async def _embed_with_retry(
        self, model: str, texts: list[str], max_retries: int = 5
    ) -> list[list[float]]:
        """Embed texts with retry + exponential backoff for rate limits."""
        import asyncio

        from google.genai.errors import ClientError

        for attempt in range(max_retries):
            try:
                response = await self._client.aio.models.embed_content(
                    model=model,
                    contents=cast(Any, texts),
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                    ),
                )
                if response.embeddings:
                    return [list(emb.values) for emb in response.embeddings if emb.values is not None]
                return []
            except ClientError as e:
                # google-genai ClientError uses e.code (int), not e.status.
                # e.status is always None in this SDK version.
                err_code = getattr(e, "code", None) or getattr(e, "status", None)
                is_rate_limit = err_code == 429 or "429" in str(e) or "quota" in str(e).lower()
                if is_rate_limit and attempt < max_retries - 1:
                    wait = min(2 ** (attempt + 2), 120)  # 4s, 8s, 16s, 32s, 120s
                    logger.warning(
                        "Gemini rate limited (attempt %d/%d), waiting %ds...",
                        attempt + 1, max_retries, wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        return []

    # -- Health check ------------------------------------------------------

    async def health_check(self) -> bool:
        """Quick check that Gemini responds."""
        try:
            # List models to verify the API key works
            models = self._client.models.list()
            return len(list(models)) > 0
        except Exception:
            return False
