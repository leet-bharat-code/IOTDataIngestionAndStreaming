"""WebSocket connection manager.

Maintains a mapping of ``user_id -> set[WebSocket]`` so that subscriber
connections can receive fan-out pushes for a specific user's data.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger("ws.manager")


class ConnectionManager:
    def __init__(self) -> None:
        self._subscriptions: dict[str, set[WebSocket]] = {}

    async def add_subscription(self, user_id: str, ws: WebSocket) -> None:
        self._subscriptions.setdefault(user_id, set()).add(ws)
        logger.info("Subscriber added for user=%s (total=%d)", user_id, len(self._subscriptions[user_id]))

    async def remove_subscription(self, user_id: str, ws: WebSocket) -> None:
        subs = self._subscriptions.get(user_id)
        if subs:
            subs.discard(ws)
            if not subs:
                del self._subscriptions[user_id]
        logger.info("Subscriber removed for user=%s", user_id)

    async def broadcast_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        subs = self._subscriptions.get(user_id)
        if not subs:
            return

        message = json.dumps(payload)
        stale: list[WebSocket] = []

        async def _safe_send(ws: WebSocket) -> None:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        await asyncio.gather(*[_safe_send(ws) for ws in subs])

        for ws in stale:
            subs.discard(ws)
            logger.warning("Stale subscriber removed for user=%s", user_id)

    @property
    def active_subscriptions(self) -> dict[str, int]:
        return {uid: len(conns) for uid, conns in self._subscriptions.items()}


manager = ConnectionManager()
