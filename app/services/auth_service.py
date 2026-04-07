from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import verify_password, create_access_token
from app.repository import user_repository
from app.core.logging import get_logger

logger = get_logger("service.auth")


async def authenticate(user_id: str, password: str) -> str:
    user = await user_repository.find_user_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    if not user.get("is_active", False):
        raise AuthenticationError("Account is deactivated")
    if not verify_password(password, user["password_hash"]):
        raise AuthenticationError("Invalid credentials")

    token = create_access_token(subject=user_id)
    logger.info("Token issued for user=%s", user_id)
    return token
