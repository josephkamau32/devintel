"""Prometheus metrics middleware for monitoring."""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database Metrics
db_connections_total = Gauge(
    "db_connections_total",
    "Total database connections in pool",
)

db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
)

# Application Metrics
embedding_operations_total = Counter(
    "embedding_operations_total",
    "Total embedding operations",
    ["operation"],  # create, search, delete
)

github_api_calls_total = Counter(
    "github_api_calls_total",
    "Total GitHub API calls",
    ["endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for each request."""
        method = request.method
        path = request.url.path
        
        # Skip metrics endpoint itself
        if path == "/metrics":
            return await call_next(request)
        
        # Increment in-progress gauge
        http_requests_in_progress.labels(method=method, endpoint=path).inc()
        
        # Time the request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status_code,
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path,
            ).observe(duration)
            
            http_requests_in_progress.labels(method=method, endpoint=path).dec()
        
        return response


def track_cache_hit():
    """Increment cache hit counter."""
    cache_hits_total.inc()


def track_cache_miss():
    """Increment cache miss counter."""
    cache_misses_total.inc()


def track_embedding_operation(operation: str):
    """Track embedding operations."""
    embedding_operations_total.labels(operation=operation).inc()


def track_github_api_call(endpoint: str):
    """Track GitHub API calls."""
    github_api_calls_total.labels(endpoint=endpoint).inc()


def update_db_pool_metrics(total: int, active: int):
    """Update database connection pool metrics."""
    db_connections_total.set(total)
    db_connections_active.set(active)
