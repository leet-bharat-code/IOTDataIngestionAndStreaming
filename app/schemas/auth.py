from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["U1001"])
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
