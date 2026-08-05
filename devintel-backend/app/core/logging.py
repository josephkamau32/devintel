"""Structured logging configuration with contextvars-based request context.

Every log entry automatically includes request_id, user_id, and repo_id
when they are set on the current async context (by middleware).

Usage::

    from app.core.logging import get_logger, log_context

    logger = get_logger(__name__)

    # In middleware or route handler:
    log_context.set(request_id="abc-123", user_id="user-456")

    # Later, any logger call automatically includes the context:
    logger.info("Processing request")
    # → {"timestamp": "...", "level": "INFO", "request_id": "abc-123", ...}
"""

import contextvars
import logging
import sys
from datetime import UTC
from typing import Any, Optional

from app.core.config import settings


# ---------------------------------------------------------------------------
# Context variables for structured logging
# ---------------------------------------------------------------------------

class _LogContext:
    """Thread/task-local log context using contextvars.

    Values set here are automatically included in every JSON log entry
    for the current async task (request scope).
    """

    _request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "request_id", default=None
    )
    _user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "user_id", default=None
    )
    _repo_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "repo_id", default=None
    )
    _agent: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "agent", default=None
    )

    def set(
        self,
        *,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        repo_id: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> None:
        """Set context values for the current async task."""
        if request_id is not None:
            self._request_id.set(request_id)
        if user_id is not None:
            self._user_id.set(user_id)
        if repo_id is not None:
            self._repo_id.set(repo_id)
        if agent is not None:
            self._agent.set(agent)

    def clear(self) -> None:
        """Reset all context values."""
        self._request_id.set(None)
        self._user_id.set(None)
        self._repo_id.set(None)
        self._agent.set(None)

    def as_dict(self) -> dict[str, str]:
        """Return all non-None context values as a dict."""
        ctx: dict[str, str] = {}
        for key, var in [
            ("request_id", self._request_id),
            ("user_id", self._user_id),
            ("repo_id", self._repo_id),
            ("agent", self._agent),
        ]:
            val = var.get()
            if val is not None:
                ctx[key] = val
        return ctx


log_context = _LogContext()


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """JSON log formatter with automatic context injection."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime

        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject contextvars (request_id, user_id, repo_id, agent)
        log_data.update(log_context.as_dict())

        # Legacy support: also check for attrs set directly on the record
        if hasattr(record, "request_id") and "request_id" not in log_data:
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id") and "user_id" not in log_data:
            log_data["user_id"] = record.user_id

        # Include extra fields passed via logger.info("msg", extra={...})
        for key in ("repo_id", "agent", "operation", "latency_ms", "tokens", "cost_usd"):
            val = getattr(record, key, None)
            if val is not None and key not in log_data:
                log_data[key] = val

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Configure application logging."""
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Set formatter based on configuration
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
