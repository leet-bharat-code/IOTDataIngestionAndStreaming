"""Bridges the event bus to the WebSocket connection manager.

Registered as an event-bus subscriber at startup so that every
``NEW_DATA`` event is pushed to relevant WebSocket subscribers.
"""

from __future__ import annotations

from typing import Any

from app.websocket.manager import manager
from app.core.logging import get_logger

logger = get_logger("ws.broadcaster")


async def handle_iot_event(event: dict[str, Any]) -> None:
    if event.get("event") != "NEW_DATA":
        return

    user_id = event.get("user_id", "")
    await manager.broadcast_to_user(user_id, event)
    logger.debug("Broadcast NEW_DATA to subscribers of user=%s", user_id)
