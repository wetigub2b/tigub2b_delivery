from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str = Field(..., description="Driver phone number with country code")
    code: str = Field(..., min_length=4, max_length=8, description="One-time verification code")


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
