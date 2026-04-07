"""Tests for the user service layer against mock MongoDB."""

import pytest
import pytest_asyncio

from app.core.exceptions import DuplicateError, NotFoundError
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service


@pytest_asyncio.fixture
async def sample_user():
    payload = UserCreate(user_id="U9001", name="Test User", password="secret123")
    return await user_service.create_user(payload)


@pytest.mark.asyncio
class TestCreateUser:
    async def test_create_success(self, sample_user):
        assert sample_user.user_id == "U9001"
        assert sample_user.name == "Test User"
        assert sample_user.is_active is True

    async def test_duplicate_user(self, sample_user):
        with pytest.raises(DuplicateError, match="already exists"):
            await user_service.create_user(
                UserCreate(user_id="U9001", name="Dup", password="secret123")
            )


@pytest.mark.asyncio
class TestGetUser:
    async def test_found(self, sample_user):
        result = await user_service.get_user("U9001")
        assert result.user_id == "U9001"

    async def test_not_found(self):
        with pytest.raises(NotFoundError):
            await user_service.get_user("MISSING")


@pytest.mark.asyncio
class TestUpdateUser:
    async def test_update_name(self, sample_user):
        updated = await user_service.update_user("U9001", UserUpdate(name="New Name"))
        assert updated.name == "New Name"

    async def test_deactivate(self, sample_user):
        updated = await user_service.update_user("U9001", UserUpdate(is_active=False))
        assert updated.is_active is False

    async def test_update_not_found(self):
        with pytest.raises(NotFoundError):
            await user_service.update_user("MISSING", UserUpdate(name="X"))
