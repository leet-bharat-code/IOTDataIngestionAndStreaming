from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50, examples=["U1001"])
    name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=6)
    is_active: bool = True


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    password: str | None = Field(None, min_length=6)
    is_active: bool | None = None


class UserResponse(BaseModel):
    user_id: str
    name: str
    is_active: bool
