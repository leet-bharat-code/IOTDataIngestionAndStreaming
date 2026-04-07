from __future__ import annotations

from typing import Any

from app.repository.database import get_database
from app.core.logging import get_logger

logger = get_logger("repo.user")


async def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    db = get_database()
    return await db.users.find_one({"user_id": user_id}, {"_id": 0})


async def insert_user(doc: dict[str, Any]) -> None:
    db = get_database()
    await db.users.insert_one(doc)
    logger.info("User inserted: %s", doc.get("user_id"))


async def update_user(user_id: str, fields: dict[str, Any]) -> bool:
    db = get_database()
    result = await db.users.update_one({"user_id": user_id}, {"$set": fields})
    updated = result.modified_count > 0
    if updated:
        logger.info("User updated: %s fields=%s", user_id, list(fields.keys()))
    return updated
