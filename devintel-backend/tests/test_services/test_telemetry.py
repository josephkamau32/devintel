"""Tests for app.core.telemetry — OpenTelemetry tracing scaffolding and no-op fallback."""

from unittest.mock import MagicMock, patch

import pytest

import app.core.telemetry as telemetry
from app.core.telemetry import (
    _NoOpSpan,
    _NoOpTracer,
    get_tracer,
    init_telemetry,
    is_otel_enabled,
)


class TestTelemetryScaffolding:
    def test_is_otel_enabled_defaults_to_false(self, monkeypatch):
        monkeypatch.delenv("OTEL_ENABLED", raising=False)
        assert is_otel_enabled() is False

    @pytest.mark.parametrize("val", ["true", "1", "yes", "TRUE", "Yes"])
    def test_is_otel_enabled_truthy_values(self, monkeypatch, val):
        monkeypatch.setenv("OTEL_ENABLED", val)
        assert is_otel_enabled() is True

    @pytest.mark.parametrize("val", ["false", "0", "no", "anything_else"])
    def test_is_otel_enabled_falsy_values(self, monkeypatch, val):
        monkeypatch.setenv("OTEL_ENABLED", val)
        assert is_otel_enabled() is False

    def test_noop_tracer_and_span_context_manager(self):
        tracer = _NoOpTracer()
        span = tracer.start_as_current_span("operation_x", attributes={"foo": "bar"})
        assert isinstance(span, _NoOpSpan)

        # Ensure no-op span methods execute without error
        with span as s:
            s.set_attribute("repo.id", 123)
            s.set_status("OK")
            s.record_exception(RuntimeError("error"))

    def test_noop_tracer_start_span(self):
        tracer = _NoOpTracer()
        span = tracer.start_span("standalone_span")
        assert isinstance(span, _NoOpSpan)

    def test_get_tracer_returns_noop_tracer_when_disabled(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        tracer = get_tracer("my_module")
        assert isinstance(tracer, _NoOpTracer)

    def test_init_telemetry_disabled_marks_initialized(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        # Reset internal flag for clean test
        monkeypatch.setattr(telemetry, "_initialized", False)
        init_telemetry()
        assert telemetry._initialized is True
