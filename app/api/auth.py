from fastapi import APIRouter

from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    token = await auth_service.authenticate(body.user_id, body.password)
    return TokenResponse(access_token=token)
