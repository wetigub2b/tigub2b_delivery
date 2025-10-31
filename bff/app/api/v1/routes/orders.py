from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.models.order import Order
from app.schemas.order import OrderDetail, OrderSummary, ProofOfDelivery, ProofOfDeliveryResponse, UpdateShippingStatus
from app.schemas.order_action import PickupRequest, PickupResponse
from app.services import order_service
from app.services import delivery_proof_service
from app.services import order_action_service
from app.services.file_upload_service import upload_base64_image

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


@router.post("/{order_sn}/pickup", response_model=PickupResponse, response_model_by_alias=True)
async def pickup_order(
    order_sn: str,
    payload: PickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Assign an unassigned order to the current driver with photo evidence.
    Sets shipping_status based on shipping_type:
    - Warehouse delivery (shipping_type=1): status → 2 (Driver Received)
    - Direct delivery (shipping_type=0): status → 4 (Warehouse Shipped/Direct Pickup)
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order to check shipping_type
    order_result = await session.execute(select(Order).where(Order.order_sn == order_sn))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Upload photo to tigu_uploaded_files
    file_id = await upload_base64_image(
        session=session,
        image_data=payload.photo,
        biz_type="order_action",
        biz_id=None  # Will be updated after action creation
    )

    # Pickup order with shipping_type-aware status
    picked_up = await order_service.pickup_order(session, order_sn, driver.id, order.shipping_type)
    if not picked_up:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order not found or already assigned to another driver"
        )

    # Determine new shipping_status based on shipping_type
    new_shipping_status = 2 if order.shipping_type == 1 else 4

    # Create order action record (action_type=1 for pickup)
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,  # Pending Receipt
        shipping_status=new_shipping_status,
        shipping_type=order.shipping_type,
        action_type=1,
        file_ids=[file_id],
        create_by=driver.name,
        remark=payload.notes
    )

    return PickupResponse(
        success=True,
        message="Order picked up successfully",
        order_sn=order_sn,
        shipping_status=new_shipping_status,
        action_id=action.id
    )


@router.post("/{order_sn}/arrive-warehouse", response_model=PickupResponse, response_model_by_alias=True)
async def arrive_warehouse(
    order_sn: str,
    payload: PickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Mark order as arrived at warehouse with photo evidence.
    Only for warehouse delivery (shipping_type=1).
    Transitions: status 2 → 3 (Arrived Warehouse)
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order to validate shipping_type
    order_result = await session.execute(select(Order).where(Order.order_sn == order_sn))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.shipping_type != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for warehouse delivery orders"
        )

    # Upload photo
    file_id = await upload_base64_image(
        session=session,
        image_data=payload.photo,
        biz_type="order_action",
        biz_id=None
    )

    # Update order status
    arrived = await order_service.arrive_warehouse(session, order_sn, driver.id)
    if not arrived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order not in correct state for warehouse arrival"
        )

    # Create order action record (action_type=2 for warehouse arrival)
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,
        shipping_status=3,
        shipping_type=order.shipping_type,
        action_type=2,
        file_ids=[file_id],
        create_by=driver.name,
        remark=payload.notes
    )

    return PickupResponse(
        success=True,
        message="Order arrived at warehouse",
        order_sn=order_sn,
        shipping_status=3,
        action_id=action.id
    )


@router.post("/{order_sn}/warehouse-ship", response_model=PickupResponse, response_model_by_alias=True)
async def warehouse_ship(
    order_sn: str,
    payload: PickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Mark order as shipped from warehouse with photo evidence.
    Only for warehouse delivery (shipping_type=1).
    Transitions: status 3 → 4 (Warehouse Shipped)
    Called by warehouse staff.
    """
    # Get order to validate shipping_type
    order_result = await session.execute(select(Order).where(Order.order_sn == order_sn))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.shipping_type != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for warehouse delivery orders"
        )

    # Upload photo
    file_id = await upload_base64_image(
        session=session,
        image_data=payload.photo,
        biz_type="order_action",
        biz_id=None
    )

    # Update order status
    shipped = await order_service.warehouse_ship(session, order_sn)
    if not shipped:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order not in correct state for warehouse shipping"
        )

    # Create order action record (action_type=3 for warehouse shipping)
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,
        shipping_status=4,
        shipping_type=order.shipping_type,
        action_type=3,
        file_ids=[file_id],
        create_by=current_user.phonenumber,
        remark=payload.notes
    )

    return PickupResponse(
        success=True,
        message="Order shipped from warehouse",
        order_sn=order_sn,
        shipping_status=4,
        action_id=action.id
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
    After successful upload, order status is automatically updated to delivered (5).
    Works for both warehouse and direct delivery paths.
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order for action record creation
    order_result = await session.execute(select(Order).where(Order.order_sn == order_sn))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Upload photo and create delivery proof record
    proof = await delivery_proof_service.upload_delivery_proof(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id,
        photo_data=payload.photo,
        notes=payload.notes
    )

    # Complete delivery (status 4 → 5)
    completed = await order_service.complete_delivery(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id
    )
    if not completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order not in correct state for delivery completion"
        )

    # Create order action record (action_type=4 for delivery completion)
    await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=3,  # Completed
        shipping_status=5,  # Delivered
        shipping_type=order.shipping_type,
        action_type=4,
        file_ids=[proof.id] if hasattr(proof, 'id') else None,
        create_by=driver.name,
        remark=payload.notes
    )

    return ProofOfDeliveryResponse(
        status="uploaded",
        photo_url=proof.photo_url,
        order_sn=order_sn,
        uploaded_at=proof.created_at
    )
