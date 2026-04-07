from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error carrying a machine-readable code, human message,
    HTTP status, and optional structured details."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(code="AUTHENTICATION_ERROR", message=message, status_code=401)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(code="AUTHORIZATION_ERROR", message=message, status_code=403)


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} '{identifier}' not found",
            status_code=404,
        )


class DuplicateError(AppError):
    def __init__(self, message: str = "Duplicate entry") -> None:
        super().__init__(code="DUPLICATE", message=message, status_code=409)


class ValidationError(AppError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            code="VALIDATION_ERROR", message=message, status_code=422, details=details,
        )
