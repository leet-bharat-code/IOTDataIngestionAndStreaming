from __future__ import annotations

from fastapi import Depends, Header
from typing import Annotated

from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError


async def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ")
    payload = decode_access_token(token)
    return payload["sub"]


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
