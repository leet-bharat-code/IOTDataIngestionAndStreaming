"""MongoDB connection lifecycle managed as an application-level singleton.

``init_db`` is called once at startup; ``close_db`` at shutdown.
Other modules obtain a database handle via ``get_database()``.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("db")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _db = _client[settings.mongodb_db_name]

    await _client.admin.command("ping")
    await _ensure_indexes()
    logger.info("MongoDB connected: db=%s", settings.mongodb_db_name)


async def _ensure_indexes() -> None:
    assert _db is not None

    # Serves both uniqueness enforcement AND the (user_id, timestamp DESC)
    # query pattern used by find_latest / find_history.
    await _db.iot_data.create_index(
        [("user_id", ASCENDING), ("timestamp", DESCENDING)],
        unique=True,
        name="uq_user_ts",
    )
    await _db.users.create_index(
        "user_id", unique=True, name="uq_user_id",
    )


async def close_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _db
