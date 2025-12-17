from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
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
    from datetime import datetime

    phone = _normalize_phone(payload.phone)
    result = await session.execute(select(User).where(User.phonenumber == phone))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Driver not found")

    # TODO: integrate with OTP verification provider.
    if payload.code != "123456":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")

    # Update login date
    user.login_date = datetime.now()
    await session.commit()

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


@router.post("/register-driver")
async def register_driver(
    payload: dict,
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Self-registration endpoint for new drivers - creates inactive account pending admin approval"""
    from datetime import datetime
    from decimal import Decimal
    from app.models.driver import Driver
    
    # Validate required fields
    if not payload.get("name") or not payload.get("phone") or not payload.get("password") or not payload.get("license_number"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name, phone, password, and driver license number are required"
        )
    
    phone = _normalize_phone(payload["phone"])
    
    # Check if phone already exists in tigu_driver
    existing_driver = await session.execute(
        select(Driver).where(Driver.phone == phone)
    )
    if existing_driver.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Check if phone already exists in sys_user
    existing_user = await session.execute(
        select(User).where(User.phonenumber == phone)
    )
    if existing_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Generate username from phone
    username = f"driver_{phone}"
    
    # Check if username exists
    existing_username = await session.execute(
        select(User).where(User.user_name == username)
    )
    if existing_username.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password
    hashed_password = get_password_hash(payload["password"])
    
    # Generate new user_id
    max_user_id_result = await session.execute(select(func.max(User.user_id)))
    max_user_id = max_user_id_result.scalar()
    new_user_id = (max_user_id or 0) + 1
    
    # Create sys_user record (INACTIVE by default - status "1")
    new_user = User(
        user_id=new_user_id,
        user_name=username,
        nick_name=payload["name"],
        phonenumber=phone,
        email=payload.get("email"),
        password=hashed_password,
        status="1",  # 1 = INACTIVE - requires admin approval
        del_flag="0",
        user_type="00",
        create_time=datetime.now(),
        update_time=datetime.now(),
        remark="Self-registered driver - pending admin approval"
    )
    
    session.add(new_user)
    await session.flush()
    
    # Create tigu_driver record (INACTIVE by default - status 0)
    new_driver = Driver(
        name=payload["name"],
        phone=phone,
        email=payload.get("email"),
        license_number=payload.get("license_number"),
        vehicle_type=payload.get("vehicle_type"),
        vehicle_plate=payload.get("vehicle_plate"),
        vehicle_model=payload.get("vehicle_model"),
        notes="Self-registered - pending admin approval",
        status=0,  # 0 = INACTIVE in tigu_driver
        rating=Decimal("5.00"),
        total_deliveries=0
    )
    
    session.add(new_driver)
    await session.commit()
    
    return {
        "message": "Registration successful. Your account is pending admin approval.",
        "phone": phone,
        "name": payload["name"]
    }
