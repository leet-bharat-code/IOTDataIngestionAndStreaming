from __future__ import annotations

from typing import Any

from pymongo.errors import DuplicateKeyError

from app.core.exceptions import DuplicateError
from app.core.logging import get_logger
from app.repository.database import get_database

logger = get_logger("repo.iot")

_PROJECTION = {"_id": 0}


async def insert_iot_data(doc: dict[str, Any]) -> None:
    db = get_database()
    try:
        await db.iot_data.insert_one(doc)
    except DuplicateKeyError as exc:
        raise DuplicateError(
            f"Data point already exists for user_id={doc.get('user_id')} "
            f"timestamp={doc.get('timestamp')}"
        ) from exc
    logger.info("IoT data stored: user=%s ts=%s", doc.get("user_id"), doc.get("timestamp"))


async def find_latest(user_id: str) -> dict[str, Any] | None:
    db = get_database()
    return await db.iot_data.find_one(
        {"user_id": user_id},
        _PROJECTION,
        sort=[("timestamp", -1)],
    )


async def find_history(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    db = get_database()
    cursor = (
        db.iot_data.find({"user_id": user_id}, _PROJECTION)
        .sort("timestamp", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
