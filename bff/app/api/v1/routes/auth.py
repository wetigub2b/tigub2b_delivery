from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash, validate_token, verify_password
from app.models.user import User
from app.schemas.admin import AdminLoginRequest
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

    access_token = create_access_token(str(user.user_id), user.effective_role)
    refresh_token = create_refresh_token(str(user.user_id), user.effective_role)

    settings = get_settings()
    await store_refresh_token(user.user_id, refresh_token, settings.refresh_token_expire_minutes * 60)

    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(payload: AdminLoginRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    result = await session.execute(select(User).where(User.user_name == payload.username))
    user = result.scalars().first()
    if not user or not user.is_active or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    # Update login date if column exists
    try:
        from datetime import datetime
        if hasattr(user, 'login_date'):
            user.login_date = datetime.now()
            await session.commit()
    except Exception:
        # Ignore if login_date column doesn't exist
        pass

    access_token = create_access_token(str(user.user_id), user.effective_role)
    refresh_token = create_refresh_token(str(user.user_id), user.effective_role)

    settings = get_settings()
    await store_refresh_token(user.user_id, refresh_token, settings.refresh_token_expire_minutes * 60)

    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    subject = validate_token(payload.refresh_token, scope="refresh")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    expected = await get_refresh_token(int(subject))
    if expected != payload.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Get user to include role in new tokens
    result = await session.execute(select(User).where(User.user_id == int(subject)))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(subject, user.role)
    refresh_token = create_refresh_token(subject, user.role)
    settings = get_settings()
    await store_refresh_token(int(subject), refresh_token, settings.refresh_token_expire_minutes * 60)
    return TokenResponse(accessToken=access_token, refreshToken=refresh_token)
