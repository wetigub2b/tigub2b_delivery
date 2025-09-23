from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, validate_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services.cache import get_refresh_token, store_refresh_token

router = APIRouter()


def _normalize_phone(phone: str) -> str:
    return phone.replace(" ", "")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    phone = _normalize_phone(payload.phone)
    result = await session.execute(select(User).where(User.phonenumber == phone))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Driver not found")

    # TODO: integrate with OTP verification provider.
    if payload.code != "123456":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")

    access_token = create_access_token(str(user.user_id))
    refresh_token = create_refresh_token(str(user.user_id))

    settings = get_settings()
    await store_refresh_token(user.user_id, refresh_token, settings.refresh_token_expire_minutes * 60)

    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest) -> TokenResponse:
    subject = validate_token(payload.refresh_token, scope="refresh")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    expected = await get_refresh_token(int(subject))
    if expected != payload.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)
    settings = get_settings()
    await store_refresh_token(int(subject), refresh_token, settings.refresh_token_expire_minutes * 60)
    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)
