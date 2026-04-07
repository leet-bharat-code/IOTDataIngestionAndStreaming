from fastapi import APIRouter

from app.core.dependencies import CurrentUserId
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(body: UserCreate) -> UserResponse:
    return await user_service.create_user(body)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    _caller: CurrentUserId = ...,
) -> UserResponse:
    return await user_service.update_user(user_id, body)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _caller: CurrentUserId = ...,
) -> UserResponse:
    return await user_service.get_user(user_id)
