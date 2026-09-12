"""Gemini provider implementation.

Wraps the Google GenAI SDK conforming to the BaseAIProvider interface
so the orchestrator can route requests through it.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any, Optional

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
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._default_chat_model = settings.GEMINI_CHAT_MODEL
        self._default_embedding_model = settings.GEMINI_EMBEDDING_MODEL

    @property
    def provider_name(self) -> str:
        return "gemini"

    # -- Completion --------------------------------------------------------

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Non-streaming chat completion."""
        model = request.model or self._default_chat_model
        start = time.perf_counter()

        try:
            # Build contents from messages
            # Gemini uses "model" role instead of "assistant"
            contents = []
            system_instruction = None

            for m in request.messages:
                if m.role == "system":
                    system_instruction = m.content
                else:
                    role = "model" if m.role == "assistant" else "user"
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part(text=m.content)],
                    ))

            config = types.GenerateContentConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                system_instruction=system_instruction,
            )

            if request.json_mode:
                config.response_mime_type = "application/json"

            response = await self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

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

        except Exception as e:
            logger.error("Gemini completion failed: %s", e)
            from app.core.exceptions import ExternalServiceError
            raise ExternalServiceError(
                message="Failed to generate chat completion via Gemini",
                details={"error": str(e)},
            ) from e

    # -- Streaming ---------------------------------------------------------

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """Streaming chat completion — yields content tokens."""
        model = request.model or self._default_chat_model

        try:
            contents = []
            system_instruction = None

            for m in request.messages:
                if m.role == "system":
                    system_instruction = m.content
                else:
                    role = "model" if m.role == "assistant" else "user"
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part(text=m.content)],
                    ))

            config = types.GenerateContentConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                system_instruction=system_instruction,
            )

            async for chunk in self._client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error("Gemini stream failed: %s", e)
            from app.core.exceptions import ExternalServiceError
            raise ExternalServiceError(
                message="Failed to stream chat completion via Gemini",
                details={"error": str(e)},
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
                    contents=texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                    ),
                )
                return [emb.values for emb in response.embeddings]
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

    # -- Health check ------------------------------------------------------

    async def health_check(self) -> bool:
        """Quick check that Gemini responds."""
        try:
            # List models to verify the API key works
            models = self._client.models.list()
            return len(list(models)) > 0
        except Exception:
            return False
