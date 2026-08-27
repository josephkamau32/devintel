"""Tests for rate limiting in-memory fallback (F-11 security fix)."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.types import ASGIApp

from app.core.config import settings
from app.main import app
from app.middleware.rate_limit import (
    ENDPOINT_RATE_LIMITS,
    _check_in_memory_rate_limit,
    _in_memory_store,
    reset_in_memory_rate_limit_store,
)


@pytest.fixture(autouse=True)
def clean_rate_limit_store():
    """Ensure in-memory store is clean before and after each test."""
    reset_in_memory_rate_limit_store()
    yield
    reset_in_memory_rate_limit_store()


@pytest.mark.asyncio
async def test_in_memory_fallback_triggers_429_when_redis_none():
    """When Redis is unavailable (returns None), in-memory rate limiting must enforce limits."""
    # Test on a specific endpoint limit, e.g. /api/v1/auth (limit = 30)
    auth_limit = ENDPOINT_RATE_LIMITS["/api/v1/auth"]

    with patch("app.core.redis_pool.RedisPool.get_client", new_callable=AsyncMock) as mock_get_client:
        mock_get_client.return_value = None

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            # Send requests up to limit
            for i in range(auth_limit):
                res = await ac.get("/api/v1/auth/me")
                # Even if auth fails with 401, rate limiter should allow up to auth_limit requests
                assert res.status_code != 429, f"Request {i+1} unexpectedly rate limited"
                assert "X-RateLimit-Limit" in res.headers

            # Next request MUST trigger 429
            res = await ac.get("/api/v1/auth/me")
            assert res.status_code == 429
            body = res.json()
            assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
            assert "detail" in body
            assert res.headers.get("Retry-After") == "60"


@pytest.mark.asyncio
async def test_in_memory_fallback_triggers_429_when_redis_raises():
    """When Redis errors out with an exception, in-memory rate limiter must kick in."""
    limit = ENDPOINT_RATE_LIMITS["/api/v1/health-score"]  # limit = 10

    with patch("app.core.redis_pool.RedisPool.get_client", new_callable=AsyncMock) as mock_get_client:
        mock_get_client.side_effect = ConnectionError("Redis connection refused")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            for i in range(limit):
                res = await ac.get("/api/v1/health-score")
                assert res.status_code != 429, f"Request {i+1} unexpectedly rate limited"

            # Limit exceeded
            res = await ac.get("/api/v1/health-score")
            assert res.status_code == 429
            assert res.json()["error_code"] == "RATE_LIMIT_EXCEEDED"


def test_in_memory_sliding_window_pruning():
    """Verify timestamps older than 60s are pruned from the in-memory window."""
    window_key = "ratelimit:test_client:test_group"
    limit = 5
    now = time.time()

    # Seed with 5 timestamps from 70 seconds ago (expired)
    _in_memory_store[window_key] = [now - 70 for _ in range(limit)]

    # Calling check should prune old entries and allow new request
    resp = _check_in_memory_rate_limit(
        window_key=window_key,
        rate_limit=limit,
        client_key="test_client",
        path="/api/v1/test",
    )
    assert resp is None
    assert len(_in_memory_store[window_key]) == 1  # 5 old pruned + 1 new added


def test_in_memory_sliding_window_exceeded():
    """Verify active timestamps within 60s trigger 429."""
    window_key = "ratelimit:test_client:test_group"
    limit = 3
    now = time.time()

    # Seed with 3 recent timestamps within window
    _in_memory_store[window_key] = [now - 10, now - 5, now - 1]

    resp = _check_in_memory_rate_limit(
        window_key=window_key,
        rate_limit=limit,
        client_key="test_client",
        path="/api/v1/test",
    )
    assert resp is not None
    assert resp.status_code == 429
