"""Tests for AI streaming reliability, retry, fallback model, and cancellation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.errors import ClientError

from app.ai.models import AIMessage, CompletionRequest
from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.core.config import settings


class MockChunk:
    def __init__(self, text: str):
        self.text = text


class MockProvider(BaseAIProvider):
    @property
    def provider_name(self) -> str:
        return "mock_provider"

    async def complete(self, request):
        pass

    async def stream(self, request):
        yield "token1"
        yield "token2"

    async def embed(self, request):
        pass


@pytest.mark.asyncio
async def test_orchestrator_stream_cancellation_no_unbound_local_error():
    """Client disconnect (CancelledError / GeneratorExit) must not raise UnboundLocalError

    and must record status='cancelled'.
    """
    orchestrator = AIOrchestrator(provider=MockProvider())

    with patch("app.ai.orchestrator.record_ai_request") as mock_record:
        gen = orchestrator.stream(messages=[AIMessage(role="user", content="hello")])
        first_token = await gen.__anext__()
        assert first_token == "token1"

        # Client closes generator early (e.g. HTTP client disconnect)
        await gen.aclose()

        # Verify record_ai_request recorded 'cancelled' and did not crash with UnboundLocalError
        assert mock_record.called
        assert mock_record.call_args.kwargs["status"] == "cancelled"


@pytest.mark.asyncio
async def test_gemini_stream_503_then_success_no_duplicate_tokens():
    """503 on first attempt followed by success yields tokens without duplication."""
    provider = GeminiProvider()
    provider._default_chat_model = "gemini-3.6-flash"
    provider._fallback_chat_model = "gemini-3-flash-preview"

    attempts = 0

    async def fake_generate_content_stream(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            # First attempt fails with 503
            raise ClientError(503, {"error": {"code": 503, "message": "The model is overloaded."}})

        # Second attempt succeeds
        async def response_stream():
            yield MockChunk("Hello ")
            yield MockChunk("world")

        return response_stream()

    provider._client = MagicMock()
    provider._client.aio.models.generate_content_stream = AsyncMock(side_effect=fake_generate_content_stream)

    request = CompletionRequest(
        messages=[AIMessage(role="user", content="test question")],
    )

    tokens = []
    async for token in provider.stream(request):
        tokens.append(token)

    assert tokens == ["Hello ", "world"]
    assert "".join(tokens) == "Hello world"
    assert attempts == 2


@pytest.mark.asyncio
async def test_gemini_stream_repeated_503_uses_fallback_model():
    """Repeated 503 on primary model falls back to GEMINI_FALLBACK_MODEL."""
    provider = GeminiProvider()
    provider._default_chat_model = "gemini-3.6-flash"
    provider._fallback_chat_model = "gemini-3-flash-preview"

    models_called = []

    async def fake_generate_content_stream(*args, **kwargs):
        model = kwargs.get("model")
        models_called.append(model)
        if model == "gemini-3.6-flash":
            raise ClientError(503, {"error": {"code": 503, "message": "High demand, unavailable"}})
        elif model == "gemini-3-flash-preview":
            async def response_stream():
                yield MockChunk("Answer from ")
                yield MockChunk("fallback model")
            return response_stream()
        raise ValueError(f"Unexpected model {model}")

    provider._client = MagicMock()
    provider._client.aio.models.generate_content_stream = AsyncMock(side_effect=fake_generate_content_stream)

    request = CompletionRequest(
        messages=[AIMessage(role="user", content="What is devintel-core?")],
    )

    tokens = []
    async for token in provider.stream(request):
        tokens.append(token)

    assert "".join(tokens) == "Answer from fallback model"
    assert models_called == ["gemini-3.6-flash", "gemini-3-flash-preview"]


@pytest.mark.asyncio
async def test_gemini_stream_first_token_timeout_uses_fallback():
    """If primary model sends no first token within timeout, switch to fallback model."""
    provider = GeminiProvider()
    provider._default_chat_model = "gemini-3.6-flash"
    provider._fallback_chat_model = "gemini-3-flash-preview"
    provider._first_token_timeout = 0.05  # Fast timeout for test

    models_called = []

    async def fake_generate_content_stream(*args, **kwargs):
        model = kwargs.get("model")
        models_called.append(model)
        if model == "gemini-3.6-flash":
            async def slow_stream():
                # Sleep longer than the 0.05s timeout before yielding first token
                await asyncio.sleep(0.3)
                yield MockChunk("Late token")
            return slow_stream()
        elif model == "gemini-3-flash-preview":
            async def fast_stream():
                yield MockChunk("Fast ")
                yield MockChunk("fallback")
            return fast_stream()
        raise ValueError(f"Unexpected model {model}")

    provider._client = MagicMock()
    provider._client.aio.models.generate_content_stream = AsyncMock(side_effect=fake_generate_content_stream)

    request = CompletionRequest(
        messages=[AIMessage(role="user", content="Question")],
    )

    tokens = []
    async for token in provider.stream(request):
        tokens.append(token)

    assert "".join(tokens) == "Fast fallback"
    assert models_called == ["gemini-3.6-flash", "gemini-3-flash-preview"]


@pytest.mark.asyncio
async def test_gemini_stream_no_fallback_after_tokens_yielded():
    """If primary model yields tokens and THEN encounters an error, do NOT switch to fallback."""
    provider = GeminiProvider()
    provider._default_chat_model = "gemini-3.6-flash"
    provider._fallback_chat_model = "gemini-3-flash-preview"

    models_called = []

    async def fake_generate_content_stream(*args, **kwargs):
        model = kwargs.get("model")
        models_called.append(model)
        if model == "gemini-3.6-flash":
            async def stream_with_mid_failure():
                yield MockChunk("Partial content...")
                # Transient error mid-stream
                raise ClientError(503, {"error": {"code": 503, "message": "Service dropped mid-stream"}})
            return stream_with_mid_failure()
        elif model == "gemini-3-flash-preview":
            async def fallback_stream():
                yield MockChunk("Should not be called")
            return fallback_stream()

    provider._client = MagicMock()
    provider._client.aio.models.generate_content_stream = AsyncMock(side_effect=fake_generate_content_stream)

    request = CompletionRequest(
        messages=[AIMessage(role="user", content="Question")],
    )

    tokens = []
    from app.core.exceptions import ExternalServiceError
    with pytest.raises(ExternalServiceError):
        async for token in provider.stream(request):
            tokens.append(token)

    # First token was received
    assert tokens == ["Partial content..."]
    # Fallback model was NOT called because tokens were already yielded
    assert models_called == ["gemini-3.6-flash"]


@pytest.mark.asyncio
async def test_gemini_fallback_model_configured_to_gemini_3_1_flash_lite():
    """Verify GeminiProvider default fallback matches settings.GEMINI_FALLBACK_MODEL (gemini-3.1-flash-lite)."""
    provider = GeminiProvider()
    assert provider._fallback_chat_model == "gemini-3.1-flash-lite"
    assert settings.GEMINI_FALLBACK_MODEL == "gemini-3.1-flash-lite"

    models_called = []

    async def fake_stream(*args, **kwargs):
        model = kwargs.get("model")
        models_called.append(model)
        if model == provider._default_chat_model:
            raise ClientError(503, {"error": {"code": 503, "message": "High demand, unavailable"}})
        elif model == "gemini-3.1-flash-lite":
            async def resp():
                yield MockChunk("Response from gemini-3.1-flash-lite")
            return resp()
        raise ValueError(f"Unexpected model {model}")

    provider._client = MagicMock()
    provider._client.aio.models.generate_content_stream = AsyncMock(side_effect=fake_stream)

    request = CompletionRequest(
        messages=[AIMessage(role="user", content="Explain RAG pipeline")],
    )

    tokens = []
    async for token in provider.stream(request):
        tokens.append(token)

    assert "".join(tokens) == "Response from gemini-3.1-flash-lite"
    assert models_called == [provider._default_chat_model, "gemini-3.1-flash-lite"]
