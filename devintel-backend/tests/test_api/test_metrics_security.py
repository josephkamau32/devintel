"""Tests for /metrics endpoint authentication and route template cardinality (F-18 security fix)."""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_metrics_unauthenticated_returns_404(monkeypatch):
    """Unauthenticated requests to /metrics must fail closed with 404."""
    monkeypatch.setattr(settings, "METRICS_API_KEY", "super-secret-metrics-key")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/metrics")
        assert res.status_code == 404
        assert res.json()["detail"] == "Not Found"


@pytest.mark.asyncio
async def test_metrics_invalid_key_returns_404(monkeypatch):
    """Requests with an incorrect key must return 404 (not 401/403 to avoid probers)."""
    monkeypatch.setattr(settings, "METRICS_API_KEY", "super-secret-metrics-key")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/metrics", headers={"X-Metrics-Key": "wrong-key"})
        assert res.status_code == 404
        assert res.json()["detail"] == "Not Found"


@pytest.mark.asyncio
async def test_metrics_unset_key_fails_closed(monkeypatch):
    """When METRICS_API_KEY is empty/unset, /metrics must return 404 for all requests."""
    monkeypatch.setattr(settings, "METRICS_API_KEY", "")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/metrics", headers={"X-Metrics-Key": "some-key"})
        assert res.status_code == 404
        assert res.json()["detail"] == "Not Found"


@pytest.mark.asyncio
async def test_metrics_valid_x_metrics_key_header_returns_200(monkeypatch):
    """Valid X-Metrics-Key header successfully authenticates and returns Prometheus output."""
    monkeypatch.setattr(settings, "METRICS_API_KEY", "super-secret-metrics-key")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/metrics", headers={"X-Metrics-Key": "super-secret-metrics-key"})
        assert res.status_code == 200
        assert "text/plain" in res.headers.get("content-type", "")
        # Standard Prometheus metrics or custom counters present
        assert ("http_requests_total" in res.text or "process_cpu_seconds_total" in res.text)


@pytest.mark.asyncio
async def test_metrics_valid_bearer_token_returns_200(monkeypatch):
    """Valid Authorization Bearer token (used by Prometheus scraper) successfully authenticates."""
    monkeypatch.setattr(settings, "METRICS_API_KEY", "super-secret-metrics-key")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/metrics", headers={"Authorization": "Bearer super-secret-metrics-key"})
        assert res.status_code == 200
        assert "text/plain" in res.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_metrics_route_template_cardinality_elimination(monkeypatch):
    """Parameterized routes must record the route template label, eliminating UUID cardinality explosion."""
    metrics_key = "test-metrics-key-123"
    monkeypatch.setattr(settings, "METRICS_API_KEY", metrics_key)

    id_1 = str(uuid.uuid4())
    id_2 = str(uuid.uuid4())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Hit parameterized route with two distinct UUIDs
        await ac.get(f"/api/v1/repos/{id_1}/search?q=test")
        await ac.get(f"/api/v1/repos/{id_2}/search?q=test")

        # Scrape metrics
        res = await ac.get("/metrics", headers={"X-Metrics-Key": metrics_key})
        assert res.status_code == 200
        metrics_body = res.text

        # Verify template is present
        assert 'endpoint="/api/v1/repos/{repository_id}/search"' in metrics_body

        # Verify neither raw UUID is leaked as an endpoint label
        assert f'endpoint="/api/v1/repos/{id_1}/search"' not in metrics_body
        assert f'endpoint="/api/v1/repos/{id_2}/search"' not in metrics_body
        assert id_1 not in metrics_body
        assert id_2 not in metrics_body


@pytest.mark.asyncio
async def test_metrics_in_progress_gauge_balance_under_concurrent_and_sequential_requests():
    """Verify http_requests_in_progress gauge increments and decrements with matching label symmetry.

    After sending several sequential and concurrent requests to a parameterized route with different UUIDs,
    the in-progress gauge for that template endpoint must return to exactly its initial value (0).
    """
    import asyncio
    from app.middleware.metrics import http_requests_in_progress

    template = "/api/v1/repos/{repository_id}/search"
    method = "GET"

    # Capture baseline gauge value for this route label
    initial_val = http_requests_in_progress.labels(method=method, endpoint=template)._value.get()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Sequential requests with different UUIDs
        for _ in range(5):
            uid = str(uuid.uuid4())
            await ac.get(f"/api/v1/repos/{uid}/search?q=test")

        # Concurrent requests with different UUIDs
        tasks = [
            ac.get(f"/api/v1/repos/{str(uuid.uuid4())}/search?q=test")
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)

    # Verify gauge nets back to initial value (0)
    final_val = http_requests_in_progress.labels(method=method, endpoint=template)._value.get()
    assert final_val == initial_val == 0.0, f"Gauge balance leaked: initial={initial_val}, final={final_val}"

