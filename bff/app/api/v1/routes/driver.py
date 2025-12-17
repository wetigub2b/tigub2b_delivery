from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.driver import Driver
from app.models.user import User
from app.schemas.driver import DriverProfileResponse, DriverProfileUpdateRequest

router = APIRouter()


@router.get("/profile", response_model=DriverProfileResponse)
async def get_driver_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> DriverProfileResponse:
    """Get the current driver's profile information"""
    # Find driver by phone number (links sys_user to tigu_driver)
    result = await session.execute(
        select(Driver).where(Driver.phone == current_user.phonenumber)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )

    return DriverProfileResponse(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        email=driver.email,
        license_number=driver.license_number,
        vehicle_type=driver.vehicle_type,
        vehicle_plate=driver.vehicle_plate,
        vehicle_model=driver.vehicle_model,
        status=driver.status,
        rating=driver.rating,
        total_deliveries=driver.total_deliveries,
        created_at=driver.created_at
    )


@router.put("/profile", response_model=DriverProfileResponse)
async def update_driver_profile(
    payload: DriverProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> DriverProfileResponse:
    """Update the current driver's profile information"""
    # Find driver by phone number
    result = await session.execute(
        select(Driver).where(Driver.phone == current_user.phonenumber)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )

    # Update fields if provided
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            setattr(driver, field, value)

    # Also update name in sys_user if changed
    if payload.name is not None:
        current_user.nick_name = payload.name

    # Also update email in sys_user if changed
    if payload.email is not None:
        current_user.email = payload.email

    await session.commit()
    await session.refresh(driver)

    return DriverProfileResponse(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        email=driver.email,
        license_number=driver.license_number,
        vehicle_type=driver.vehicle_type,
        vehicle_plate=driver.vehicle_plate,
        vehicle_model=driver.vehicle_model,
        status=driver.status,
        rating=driver.rating,
        total_deliveries=driver.total_deliveries,
        created_at=driver.created_at
    )
