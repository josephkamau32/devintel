"""OpenTelemetry instrumentation — traces, metrics, and spans.

Runs alongside Prometheus (which handles `/metrics` scraping) to add
distributed tracing with context propagation across services.

Configuration via environment variables:
- ``OTEL_ENABLED=true`` — enable telemetry (default: false)
- ``OTEL_EXPORTER_OTLP_ENDPOINT`` — OTLP collector endpoint
- ``OTEL_SERVICE_NAME`` — service name (default: devintel-backend)

Usage::

    from app.core.telemetry import init_telemetry, get_tracer

    # In lifespan:
    init_telemetry(app)

    # In code:
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("repo.id", repo_id)
        result = await do_work()
"""

from __future__ import annotations

import os
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

_initialized = False


def is_otel_enabled() -> bool:
    """Check if OpenTelemetry is enabled via environment."""
    return os.environ.get("OTEL_ENABLED", "false").lower() in ("true", "1", "yes")


def init_telemetry(app=None) -> None:
    """Initialize OpenTelemetry instrumentation.

    Args:
        app: FastAPI application instance (for auto-instrumentation).
    """
    global _initialized

    if _initialized:
        return

    if not is_otel_enabled():
        logger.info("OpenTelemetry disabled (set OTEL_ENABLED=true to enable)")
        _initialized = True
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.environ.get("OTEL_SERVICE_NAME", "devintel-backend")

        resource = Resource(attributes={
            SERVICE_NAME: service_name,
        })

        provider = TracerProvider(resource=resource)

        # OTLP exporter (works with Jaeger, Tempo, etc.)
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)

        # Auto-instrument FastAPI
        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI auto-instrumented with OpenTelemetry")
            except ImportError:
                logger.debug("opentelemetry-instrumentation-fastapi not installed")

        # Auto-instrument SQLAlchemy
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument()
            logger.info("SQLAlchemy auto-instrumented with OpenTelemetry")
        except ImportError:
            logger.debug("opentelemetry-instrumentation-sqlalchemy not installed")

        # Auto-instrument httpx
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            logger.info("httpx auto-instrumented with OpenTelemetry")
        except ImportError:
            logger.debug("opentelemetry-instrumentation-httpx not installed")

        _initialized = True
        logger.info(
            "OpenTelemetry initialized: service=%s endpoint=%s",
            service_name, endpoint,
        )

    except ImportError:
        logger.warning(
            "OpenTelemetry SDK not installed. Install with: "
            "pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
        )
        _initialized = True
    except Exception as e:
        logger.error("Failed to initialize OpenTelemetry: %s", e)
        _initialized = True


def get_tracer(name: str):
    """Get an OpenTelemetry tracer.

    Returns a no-op tracer if OTel is not enabled, so callers
    don't need to check.
    """
    if not is_otel_enabled():
        # Return a no-op tracer
        return _NoOpTracer()

    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpSpan:
    """No-op span for when OTel is disabled."""

    def set_attribute(self, key, value):
        pass

    def set_status(self, status):
        pass

    def record_exception(self, exception):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoOpTracer:
    """No-op tracer for when OTel is disabled."""

    def start_as_current_span(self, name, **kwargs):
        return _NoOpSpan()

    def start_span(self, name, **kwargs):
        return _NoOpSpan()
