from __future__ import annotations

from pydantic import BaseModel
from typing import Any


class IoTEvent(BaseModel):
    event: str = "NEW_DATA"
    user_id: str
    timestamp: float
    data: dict[str, Any]
