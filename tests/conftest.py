"""Shared test fixtures.

Uses mongomock-motor to provide an in-memory MongoDB for repository-level
tests, and patches the database module so service tests hit the mock.
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

from app.core.config import get_settings


@pytest_asyncio.fixture(autouse=True)
async def mock_db(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Replace the real Motor client with mongomock-motor for every test."""
    client = AsyncMongoMockClient()
    db = client[get_settings().mongodb_db_name]

    import app.repository.database as db_mod
    monkeypatch.setattr(db_mod, "_client", client)
    monkeypatch.setattr(db_mod, "_db", db)

    yield

    await client.drop_database(get_settings().mongodb_db_name)
