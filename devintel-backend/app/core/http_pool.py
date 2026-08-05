"""Shared httpx client pool — reuse connections across the application.

Creating a new ``httpx.AsyncClient`` per request is expensive (TLS
handshake, connection setup). This module provides a shared, long-lived
client with connection pooling and sensible defaults.

Usage::

    from app.core.http_pool import get_http_client

    async with get_http_client() as client:
        response = await client.get("https://api.github.com/...")

    # Or for manual lifecycle management:
    client = get_http_client()
    response = await client.get(...)
    # client is closed in lifespan shutdown
"""

from __future__ import annotations

from typing import Optional

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Optional[httpx.AsyncClient] = None

# Connection pool limits
_POOL_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=30,
)

_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=30.0,
    write=10.0,
    pool=10.0,
)


def get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx.AsyncClient singleton.

    The client is lazily initialized on first call and reused for all
    subsequent requests. Connection pooling is handled automatically.
    """
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            limits=_POOL_LIMITS,
            timeout=_TIMEOUT,
            follow_redirects=True,
            http2=True,
            headers={
                "User-Agent": "DevIntel/1.0",
            },
        )
        logger.info("HTTP client pool initialized")
    return _client


async def close_http_client() -> None:
    """Close the shared HTTP client. Call from lifespan shutdown."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
        logger.info("HTTP client pool closed")
