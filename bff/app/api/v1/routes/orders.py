from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.schemas.order import OrderDetail, OrderSummary, ProofOfDelivery, UpdateShippingStatus
from app.services import order_service

router = APIRouter()


@router.get("/assigned", response_model=list[OrderSummary])
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


@router.get("/{order_sn}", response_model=OrderDetail)
async def get_order_detail(
    order_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> OrderDetail:
    detail = await order_service.fetch_order_detail(session, order_sn, current_user.user_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return detail


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


@router.post("/{order_sn}/proof", status_code=status.HTTP_202_ACCEPTED)
async def upload_proof_of_delivery(
    order_sn: str,
    payload: ProofOfDelivery,
    current_user=Depends(deps.get_current_user)
) -> dict:
    # TODO: integrate with object storage and persistence tables.
    return {
        "order_sn": order_sn,
        "status": "queued",
        "notes": payload.notes,
        "photo_url": payload.photo_url,
        "signature_url": payload.signature_url,
        "driver_id": current_user.user_id
    }
