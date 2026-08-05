"""Central AI Orchestrator — single entry point for all AI operations.

Every service that needs AI capabilities goes through this class instead
of instantiating provider clients directly.  The orchestrator handles:

- Provider routing (OpenAI now, extensible to others)
- Metrics collection (tokens, latency, cost)
- Circuit breaker delegation (via provider)
- Caching (optional, for embedding lookups)
- Structured logging
- Consistent error handling
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Optional

from app.ai.metrics import record_ai_request
from app.ai.models import (
    AIMessage,
    AIProvider as AIProviderEnum,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIOrchestrator:
    """Central orchestrator for all AI operations.

    Usage::

        orchestrator = get_orchestrator()
        response = await orchestrator.complete(
            messages=[AIMessage(role="user", content="Hello")],
            agent="chat",
        )
        print(response.content, response.token_usage, response.latency_ms)
    """

    def __init__(self, provider: Optional[BaseAIProvider] = None) -> None:
        self._provider = provider or OpenAIProvider()

    @property
    def provider(self) -> BaseAIProvider:
        return self._provider

    # ------------------------------------------------------------------
    # Chat completion (non-streaming)
    # ------------------------------------------------------------------

    async def complete(
        self,
        messages: list[AIMessage] | list[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[object] = None,
        agent: Optional[str] = None,
        repo_id=None,
        user_id=None,
    ) -> CompletionResponse:
        """Execute a chat completion through the provider.

        Accepts either ``AIMessage`` objects or plain dicts for convenience.
        """
        normalized = _normalize_messages(messages)

        # Apply feature flag model override if configured
        effective_model = model
        if agent and not model:
            from app.core.feature_flags import flags
            override = flags.get_model_override(agent)
            if override:
                effective_model = override
                logger.debug("Model override for agent=%s: %s", agent, override)

        request = CompletionRequest(
            messages=normalized,
            model=effective_model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            tools=tools,
            tool_choice=tool_choice,
            agent=agent,
            repo_id=repo_id,
            user_id=user_id,
        )

        start = time.perf_counter()
        status = "success"
        try:
            response = await self._provider.complete(request)
        except Exception:
            status = "error"
            raise
        finally:
            elapsed = time.perf_counter() - start
            # Record metrics even on failure (with 0 tokens)
            record_ai_request(
                provider=self._provider.provider_name,
                model=model or "default",
                agent=agent or "unknown",
                operation="chat_completion",
                status=status,
                latency_s=elapsed,
                prompt_tokens=response.token_usage.prompt_tokens if status == "success" else 0,
                completion_tokens=response.token_usage.completion_tokens if status == "success" else 0,
                cost_usd=response.cost_estimate_usd if status == "success" else 0.0,
            )

        logger.info(
            "AI completion: model=%s tokens=%d latency=%.0fms cost=$%.4f agent=%s",
            response.model,
            response.token_usage.total_tokens,
            response.latency_ms,
            response.cost_estimate_usd,
            agent or "unknown",
        )

        # Run zero-cost quality evaluation
        try:
            from app.ai.evaluation.evaluator import get_evaluator
            evaluation = get_evaluator().evaluate(
                prompt_messages=[{"role": m.role, "content": m.content} for m in normalized],
                response_content=response.content,
                agent=agent or "unknown",
                model=response.model,
                latency_ms=response.latency_ms,
                prompt_tokens=response.token_usage.prompt_tokens,
                completion_tokens=response.token_usage.completion_tokens,
                cost_usd=response.cost_estimate_usd,
                user_id=str(user_id) if user_id else None,
                repo_id=str(repo_id) if repo_id else None,
                expected_format="json" if json_mode else "text",
            )
            response.metadata["evaluation_score"] = evaluation.overall_score
        except Exception as e:
            logger.debug("Evaluation failed (non-critical): %s", e)

        return response

    # ------------------------------------------------------------------
    # Chat completion (streaming)
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[AIMessage] | list[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        agent: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion, yielding tokens as they arrive."""
        normalized = _normalize_messages(messages)

        request = CompletionRequest(
            messages=normalized,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            agent=agent,
        )

        start = time.perf_counter()
        try:
            async for token in self._provider.stream(request):
                yield token
            status = "success"
        except Exception:
            status = "error"
            raise
        finally:
            elapsed = time.perf_counter() - start
            record_ai_request(
                provider=self._provider.provider_name,
                model=model or "default",
                agent=agent or "unknown",
                operation="chat_stream",
                status=status,
                latency_s=elapsed,
                prompt_tokens=0,  # Not available in streaming mode
                completion_tokens=0,
                cost_usd=0.0,
            )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    async def embed(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> list[float]:
        """Generate a single embedding vector."""
        response = await self.embed_batch([text], model=model, agent=agent)
        return response.embeddings[0]

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> EmbeddingResponse:
        """Generate embeddings for a batch of texts."""
        request = EmbeddingRequest(
            texts=texts,
            model=model,
            agent=agent,
        )

        start = time.perf_counter()
        status = "success"
        try:
            response = await self._provider.embed(request)
        except Exception:
            status = "error"
            raise
        finally:
            elapsed = time.perf_counter() - start
            record_ai_request(
                provider=self._provider.provider_name,
                model=model or "default",
                agent=agent or "embedding",
                operation="embedding",
                status=status,
                latency_s=elapsed,
                prompt_tokens=response.token_usage.prompt_tokens if status == "success" else 0,
                completion_tokens=0,
                cost_usd=response.cost_estimate_usd if status == "success" else 0.0,
            )

        return response


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """Return the global AIOrchestrator singleton.

    Lazily initialized on first call so import-time side effects are avoided.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_messages(messages: list) -> list[AIMessage]:
    """Accept either AIMessage objects or plain dicts.

    Also sanitizes message content to redact secrets before sending
    to the AI provider.
    """
    from app.ai.safety import sanitize_for_llm

    normalized = []
    for m in messages:
        if isinstance(m, AIMessage):
            normalized.append(AIMessage(
                role=m.role,
                content=sanitize_for_llm(m.content),
                name=m.name,
            ))
        elif isinstance(m, dict):
            sanitized = {**m, "content": sanitize_for_llm(m.get("content", ""))}
            normalized.append(AIMessage(**sanitized))
        else:
            raise TypeError(f"Expected AIMessage or dict, got {type(m)}")
    return normalized
