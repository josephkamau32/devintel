"""Regression tests for RateLimitMiddleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient, ASGITransport
from starlette import status

from app.core.exceptions import unhandled_exception_handler
from app.middleware.rate_limit import RateLimitMiddleware, reset_in_memory_rate_limit_store


@pytest.fixture(autouse=True)
def clean_rate_limit_store():
    reset_in_memory_rate_limit_store()
    yield
    reset_in_memory_rate_limit_store()


@pytest.mark.asyncio
async def test_rate_limit_middleware_does_not_double_call_next_on_downstream_exception():
    """
    REGRESSION TEST (Bug B):
    Ensure downstream exceptions (e.g., database constraint violations) are NOT
    swallowed or misidentified as Redis errors by RateLimitMiddleware, and do NOT
    cause call_next to be executed a second time on an already-consumed request body.
    """
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, default_limit=10)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    call_count = 0

    @app.post("/api/v1/repos/test-fail")
    async def failing_endpoint(request: Request):
        nonlocal call_count
        call_count += 1
        # Read body to simulate normal endpoint behavior
        body = await request.json()
        assert body.get("repo_name") == "test-repo"
        # Simulate downstream failure (such as NotNullViolationError or business logic error)
        raise RuntimeError("Simulated downstream database constraint violation")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repos/test-fail",
            json={"repo_name": "test-repo"},
        )

    # Downstream handler must be called EXACTLY ONCE
    assert call_count == 1, f"Expected endpoint to be called once, but was called {call_count} times!"

    # Response should be a structured 500 error from unhandled_exception_handler, not a hang or 429
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["error_code"] == "INTERNAL_ERROR"
    assert data["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_successful_requests():
    """Verify normal requests pass through with rate limit headers."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, default_limit=10)

    @app.get("/api/v1/repos/test-ok")
    async def ok_endpoint():
        return {"status": "ok"}

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/repos/test-ok")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
    assert "X-RateLimit-Limit" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_middleware_falls_back_to_in_memory_on_redis_error(monkeypatch):
    """Verify Redis connection errors gracefully fall back to in-memory rate limiting."""
    app = FastAPI()
    # default_limit is used for endpoints not in ENDPOINT_RATE_LIMITS
    app.add_middleware(RateLimitMiddleware, default_limit=2)

    @app.get("/api/v1/other/test-fallback")
    async def endpoint():
        return {"ok": True}

    from app.core.redis_pool import RedisPool

    async def broken_get_client():
        raise ConnectionError("Redis connection refused")

    monkeypatch.setattr(RedisPool, "get_client", broken_get_client)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First 2 requests succeed under in-memory limit
        r1 = await client.get("/api/v1/other/test-fallback")
        assert r1.status_code == status.HTTP_200_OK

        r2 = await client.get("/api/v1/other/test-fallback")
        assert r2.status_code == status.HTTP_200_OK

        # 3rd request should hit in-memory limit
        r3 = await client.get("/api/v1/other/test-fallback")
        assert r3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert r3.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
