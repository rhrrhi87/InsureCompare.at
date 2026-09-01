"""Domain-level exceptions translated to HTTP responses by the API layer.

File: backend/app/core/exceptions.py
"""
from fastapi import HTTPException, status


class DomainError(Exception):
    """Base class for domain-level errors raised by services."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Bad request"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


class UnauthorisedError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required"


class ForbiddenError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Operation not permitted"


class ValidationError(DomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed"


class UploadTooLargeError(DomainError):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    detail = "Uploaded file exceeds maximum allowed size"


class UnsupportedMediaError(DomainError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    detail = "Unsupported media type"


def domain_to_http(error: DomainError) -> HTTPException:
    """Translate a domain error into an HTTPException for FastAPI."""
    return HTTPException(status_code=error.status_code, detail=error.detail)
