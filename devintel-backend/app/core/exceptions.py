from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class ExternalServiceError(AppException):
    def __init__(self, detail: str = "External service unavailable"):
        super().__init__(status.HTTP_502_BAD_GATEWAY, detail)


class EmbeddingError(AppException):
    def __init__(self, detail: str = "Embedding generation failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class APIError(AppException):
    def __init__(self, detail: str = "API request failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class IndexingError(AppException):
    def __init__(self, detail: str = "Indexing process failed"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class CircuitBreakerError(AppException):
    def __init__(self, detail: str = "Service circuit breaker open"):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, detail)


# ── FastAPI exception handlers ────────────────────────────────────────────────
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )
