"""Tests for the authentication service layer."""

import pytest
import pytest_asyncio

from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import decode_access_token
from app.schemas.user import UserCreate, UserUpdate
from app.services import auth_service, user_service


@pytest_asyncio.fixture
async def registered_user():
    await user_service.create_user(
        UserCreate(user_id="U8001", name="Auth Tester", password="correct-horse")
    )


@pytest.mark.asyncio
class TestAuthenticate:
    async def test_success_returns_valid_jwt(self, registered_user):
        token = await auth_service.authenticate("U8001", "correct-horse")
        payload = decode_access_token(token)
        assert payload["sub"] == "U8001"

    async def test_wrong_password(self, registered_user):
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await auth_service.authenticate("U8001", "wrong-password")

    async def test_nonexistent_user(self):
        with pytest.raises(NotFoundError):
            await auth_service.authenticate("GHOST", "any")

    async def test_inactive_user_rejected(self, registered_user):
        await user_service.update_user("U8001", UserUpdate(is_active=False))
        with pytest.raises(AuthenticationError, match="deactivated"):
            await auth_service.authenticate("U8001", "correct-horse")
