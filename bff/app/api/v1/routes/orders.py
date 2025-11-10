from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.schemas.order import (
    ArriveWarehouseRequest,
    CompleteDeliveryRequest,
    OrderDetail,
    WarehouseReceiveRequest,
    WarehouseShipRequest,
)
from app.services import order_service

router = APIRouter()


@router.get("/{order_sn}", response_model=OrderDetail, response_model_by_alias=True)
async def get_order_detail(
    order_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> OrderDetail:
    """
    Get order details by serial number.

    Used by OrderDetail view for displaying order information.
    """
    detail = await order_service.fetch_order_detail(session, order_sn, current_user.user_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return detail


# New 4-Workflow Transition Endpoints

@router.post("/{order_sn}/arrive-warehouse", status_code=status.HTTP_204_NO_CONTENT)
async def arrive_warehouse(
    order_sn: str,
    payload: ArriveWarehouseRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Driver arrives at warehouse (action_type=2).

    Workflow: Merchant→Driver→Warehouse→User (Workflows 1 & 3)

    This function:
    1. Updates order shipping_status to 3 (司机送达仓库)
    2. Sets arrive_warehouse_time timestamp
    3. Creates OrderAction record with photo evidence

    Args:
        order_sn: Order serial number
        payload: Arrival request with photo IDs
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Driver not found or order not found
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    arrived = await order_service.arrive_warehouse(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id,
        photo_ids=payload.photo_ids
    )

    if not arrived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )


@router.post("/{order_sn}/warehouse-receive", status_code=status.HTTP_204_NO_CONTENT)
async def warehouse_receive(
    order_sn: str,
    payload: WarehouseReceiveRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Warehouse receives goods from driver (action_type=3).

    Workflow: Merchant→Driver→Warehouse→User (Workflows 1 & 3)

    This function:
    1. Updates order shipping_status to 4 (仓库已收货)
    2. Creates OrderAction record

    Args:
        order_sn: Order serial number
        payload: Warehouse receive request
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Order not found
    """
    received = await order_service.warehouse_receive(
        session=session,
        order_sn=order_sn,
        warehouse_staff_id=payload.warehouse_staff_id,
        photo_ids=payload.photo_ids
    )

    if not received:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )


@router.post("/{order_sn}/warehouse-ship", status_code=status.HTTP_204_NO_CONTENT)
async def warehouse_ship(
    order_sn: str,
    payload: WarehouseShipRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Warehouse ships goods to end user (action_type=4).

    Workflow: Merchant→Warehouse→User (Workflow 1 only)

    This function:
    1. Updates order shipping_status to 5 (司机配送用户)
    2. Sets warehouse_shipping_time timestamp
    3. Creates OrderAction record

    Args:
        order_sn: Order serial number
        payload: Warehouse ship request
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Order not found
    """
    shipped = await order_service.warehouse_ship(
        session=session,
        order_sn=order_sn,
        warehouse_staff_id=payload.warehouse_staff_id,
        photo_ids=payload.photo_ids
    )

    if not shipped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )


@router.post("/{order_sn}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_delivery(
    order_sn: str,
    payload: CompleteDeliveryRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Complete delivery to end user (action_type=5).

    Works for all 4 workflows - final delivery step.

    This function:
    1. Updates order shipping_status to 6 (已送达)
    2. Sets finish_time timestamp
    3. Creates OrderAction record with delivery proof

    Args:
        order_sn: Order serial number
        payload: Complete delivery request with proof photos
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Driver not found or order not found
    """
    # Look up driver by phone number to get driver_id (for driver deliveries)
    # Or use current user ID for merchant deliveries
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()

    # Use driver ID if driver exists, otherwise use current user ID
    completer_id = driver.id if driver else current_user.user_id

    completed = await order_service.complete_delivery(
        session=session,
        order_sn=order_sn,
        completer_id=completer_id,
        photo_ids=payload.photo_ids
    )

    if not completed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
