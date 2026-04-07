from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error envelope returned by every failing endpoint."""

    error: str
    message: str
    details: Any = None
