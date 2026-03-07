"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class DevIntelException(Exception):
    """Base exception for DevIntel application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize exception."""
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(DevIntelException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(DevIntelException):
    """User not authorized."""

    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=403, details=details)


class NotFoundError(DevIntelException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=404, details=details)


class ValidationError(DevIntelException):
    """Validation failed."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=422, details=details)


class RateLimitError(DevIntelException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=429, details=details)


class ExternalServiceError(DevIntelException):
    """External service error."""

    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=502, details=details)


class IndexingError(DevIntelException):
    """Repository indexing error."""

    def __init__(self, message: str = "Indexing failed", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=500, details=details)


class EmbeddingError(DevIntelException):
    """Embedding generation error."""

    def __init__(self, message: str = "Embedding generation failed", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=500, details=details)


class APIError(DevIntelException):
    """Generic API error."""

    def __init__(self, message: str = "API error", status_code: int = 500, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        super().__init__(message, status_code=status_code, details=details)
