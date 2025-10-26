from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.schemas.order import OrderDetail, OrderSummary, ProofOfDelivery, ProofOfDeliveryResponse, UpdateShippingStatus
from app.services import order_service
from app.services import delivery_proof_service

router = APIRouter()


@router.get("/assigned", response_model=list[OrderSummary], response_model_by_alias=True)
async def list_assigned_orders(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> list[OrderSummary]:
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Include completed orders for TaskBoard to show all three tabs
    return await order_service.fetch_assigned_orders(session, driver.id, include_completed=True)


@router.get("/available", response_model=list[OrderSummary], response_model_by_alias=True)
async def list_available_orders(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> list[OrderSummary]:
    """
    List all unassigned orders available for pickup by any driver.
    Returns orders where driver_id is NULL.
    """
    return await order_service.fetch_orders(session, unassigned=True, limit=100)


@router.get("/{order_sn}", response_model=OrderDetail, response_model_by_alias=True)
async def get_order_detail(
    order_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> OrderDetail:
    detail = await order_service.fetch_order_detail(session, order_sn, current_user.user_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return detail


@router.post("/{order_sn}/pickup", status_code=status.HTTP_204_NO_CONTENT)
async def pickup_order(
    order_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Assign an unassigned order to the current driver.
    Sets driver_id and shipping_status to 0 (pending pickup).
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    picked_up = await order_service.pickup_order(session, order_sn, driver.id)
    if not picked_up:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order not found or already assigned to another driver"
        )


@router.post("/{order_sn}/status", status_code=status.HTTP_204_NO_CONTENT)
async def update_shipping_status(
    order_sn: str,
    payload: UpdateShippingStatus,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    updated = await order_service.update_order_shipping_status(
        session, order_sn, payload.shipping_status, current_user.user_id
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.post("/{order_sn}/proof", response_model=ProofOfDeliveryResponse, response_model_by_alias=True)
async def upload_proof_of_delivery(
    order_sn: str,
    payload: ProofOfDelivery,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> ProofOfDeliveryResponse:
    """
    Upload delivery proof photo and notes.
    Photo must be base64 encoded, max 4MB.
    After successful upload, order status is automatically updated to delivered (3).
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Upload photo and create delivery proof record
    proof = await delivery_proof_service.upload_delivery_proof(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id,
        photo_data=payload.photo,
        notes=payload.notes
    )

    # Update order status to delivered (3)
    await order_service.update_order_shipping_status(
        session=session,
        order_sn=order_sn,
        shipping_status=3,
        driver_id=driver.id
    )

    return ProofOfDeliveryResponse(
        status="uploaded",
        photo_url=proof.photo_url,
        order_sn=order_sn,
        uploaded_at=proof.created_at
    )
