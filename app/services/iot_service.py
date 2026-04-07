"""Single ingestion pipeline shared by REST and WebSocket producers.

Flow:
    1. Domain validation (pure business rules)
    2. User existence & active-status check
    3. Persist to MongoDB (idempotency via unique index)
    4. Publish event to messaging layer (NOT directly to WS)
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.domain.validators import validate_iot_data_point
from app.messaging.event_bus import publish_event
from app.repository import iot_repository, user_repository
from app.schemas.events import IoTEvent
from app.schemas.iot import IoTDataPoint, IoTDataResponse, IoTIngestResult

logger = get_logger("service.iot")


async def process_iot_data(data: IoTDataPoint) -> IoTIngestResult:
    """Unified pipeline -- called by both REST and WebSocket handlers."""

    validate_iot_data_point(
        metric_1=data.metric_1,
        metric_2=data.metric_2,
        timestamp=data.timestamp,
    )

    user = await user_repository.find_user_by_id(data.user_id)
    if user is None:
        raise NotFoundError("User", data.user_id)
    if not user.get("is_active", False):
        raise ValidationError(f"User '{data.user_id}' is not active")

    doc = {
        "user_id": data.user_id,
        "metric_1": data.metric_1,
        "metric_2": data.metric_2,
        "metric_3": data.metric_3,
        "timestamp": data.timestamp,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    await iot_repository.insert_iot_data(doc)

    event = IoTEvent(
        user_id=data.user_id,
        timestamp=data.timestamp,
        data={
            "metric_1": data.metric_1,
            "metric_2": data.metric_2,
            "metric_3": data.metric_3,
        },
    )
    await publish_event(event.model_dump())

    logger.info("IoT data processed: user=%s ts=%s", data.user_id, data.timestamp)
    return IoTIngestResult(user_id=data.user_id, timestamp=data.timestamp)


async def get_latest(user_id: str) -> IoTDataResponse:
    await _assert_user_exists(user_id)
    doc = await iot_repository.find_latest(user_id)
    if doc is None:
        raise NotFoundError("IoT data", user_id)
    return IoTDataResponse(**doc)


async def get_history(user_id: str, limit: int = 50) -> list[IoTDataResponse]:
    await _assert_user_exists(user_id)
    docs = await iot_repository.find_history(user_id, limit=limit)
    return [IoTDataResponse(**d) for d in docs]


async def _assert_user_exists(user_id: str) -> None:
    user = await user_repository.find_user_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
