from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with structured error information."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "INTERNAL_ERROR",
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, error_code="AUTH_ERROR")


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail, error_code="NOT_FOUND")


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail, error_code="CONFLICT")


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail, error_code="FORBIDDEN")


class ExternalServiceError(AppException):
    def __init__(
        self,
        detail: str = "External service unavailable",
        *,
        message: str | None = None,
        details: dict | None = None,
    ):
        msg = message or detail
        if details:
            msg = f"{msg}: {details}"
        super().__init__(status.HTTP_502_BAD_GATEWAY, msg, error_code="EXTERNAL_SERVICE_ERROR")


class EmbeddingError(AppException):
    def __init__(
        self,
        detail: str = "Embedding generation failed",
        *,
        message: str | None = None,
        details: dict | None = None,
    ):
        # Support both `detail=` (direct) and `message=`/`details=` (openai_client) call styles
        msg = message or detail
        if details:
            msg = f"{msg}: {details}"
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, msg, error_code="EMBEDDING_ERROR")


class APIError(AppException):
    def __init__(self, detail: str = "API request failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, error_code="API_ERROR")


class IndexingError(AppException):
    def __init__(self, detail: str = "Indexing process failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, error_code="INDEXING_ERROR")


class CircuitBreakerError(AppException):
    def __init__(self, detail: str = "Service circuit breaker open"):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, detail, error_code="CIRCUIT_BREAKER_OPEN")


class RateLimitError(AppException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, detail, error_code="RATE_LIMIT_EXCEEDED")


# ── FastAPI exception handlers ────────────────────────────────────────────────

def _add_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    """Inject CORS headers directly into error responses.

    Starlette's BaseHTTPMiddleware subclasses break the CORSMiddleware
    send_wrapper pipeline on error responses — the CORS headers are
    silently dropped.  This helper ensures they are always present.
    """
    from app.core.config import settings

    origin = request.headers.get("origin")
    if origin and origin in settings.CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers.setdefault("Vary", "Origin")
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Return structured error envelope with error_code and request_id."""
    request_id = getattr(request.state, "request_id", None) or "unknown"
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "request_id": request_id,
        },
    )
    return _add_cors_headers(request, response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return structured validation error envelope with request_id."""
    request_id = getattr(request.state, "request_id", None) or "unknown"
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "request_id": request_id,
            "errors": errors,
        },
    )
    return _add_cors_headers(request, response)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — ensures CORS headers are still applied.

    Without this, raw 500 responses from uncaught errors (e.g. database
    connection failures) bypass the structured response pipeline and may
    be returned without CORS headers, causing the browser to report a
    misleading CORS error instead of the real server error.
    """
    import logging

    logging.getLogger(__name__).exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    request_id = getattr(request.state, "request_id", None) or "unknown"
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "request_id": request_id,
        },
    )
    return _add_cors_headers(request, response)


