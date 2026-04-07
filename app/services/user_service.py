from __future__ import annotations

from app.core.exceptions import DuplicateError, NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_password
from app.repository import user_repository
from app.schemas.user import UserCreate, UserResponse, UserUpdate

logger = get_logger("service.user")


def _to_response(doc: dict) -> UserResponse:
    return UserResponse(
        user_id=doc["user_id"], name=doc["name"], is_active=doc["is_active"],
    )


async def create_user(payload: UserCreate) -> UserResponse:
    existing = await user_repository.find_user_by_id(payload.user_id)
    if existing:
        raise DuplicateError(f"User '{payload.user_id}' already exists")

    doc = {
        "user_id": payload.user_id,
        "name": payload.name,
        "password_hash": hash_password(payload.password),
        "is_active": payload.is_active,
    }
    await user_repository.insert_user(doc)
    logger.info("User created: %s", payload.user_id)
    return _to_response(doc)


async def update_user(user_id: str, payload: UserUpdate) -> UserResponse:
    existing = await user_repository.find_user_by_id(user_id)
    if not existing:
        raise NotFoundError("User", user_id)

    fields: dict[str, object] = {}
    if payload.name is not None:
        fields["name"] = payload.name
    if payload.password is not None:
        fields["password_hash"] = hash_password(payload.password)
    if payload.is_active is not None:
        fields["is_active"] = payload.is_active

    if fields:
        await user_repository.update_user(user_id, fields)

    updated = await user_repository.find_user_by_id(user_id)
    if updated is None:
        raise NotFoundError("User", user_id)
    return _to_response(updated)


async def get_user(user_id: str) -> UserResponse:
    user = await user_repository.find_user_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return _to_response(user)
