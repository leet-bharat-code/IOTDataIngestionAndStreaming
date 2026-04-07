"""In-process event bus that decouples the service layer from delivery mechanisms.

The service layer calls ``publish_event`` without knowing *who* is listening.
Handlers (e.g. the WebSocket broadcaster) register via ``subscribe``.

This is the seam where Redis pub/sub or Kafka can be plugged in later
without touching any business logic.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.core.logging import get_logger

logger = get_logger("messaging")

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]

_subscribers: list[EventHandler] = []


def subscribe(handler: EventHandler) -> None:
    _subscribers.append(handler)
    logger.info("Event subscriber registered: %s", handler.__qualname__)


async def publish_event(event: dict[str, Any]) -> None:
    logger.debug("Publishing event: %s", event.get("event"))
    tasks = [handler(event) for handler in _subscribers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                "Event handler %s raised: %s",
                _subscribers[idx].__qualname__,
                result,
            )


def clear_subscribers() -> None:
    """For test teardown."""
    _subscribers.clear()
