from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, UploadedFile, Warehouse
from app.models.delivery_proof import DeliveryProof
from app.models.prepare_goods import PrepareGoods
from app.schemas.order import DeliveryProofInfo, OrderDetail, OrderItem as OrderItemSchema, OrderSummary, WarehouseSnapshot
from app.services import order_action_service
from app.services.order_action_service import ActionType

# Updated shipping status labels to match 4-workflow system
SHIPPING_STATUS_LABELS = {
    0: "待备货",           # Pending Prepare (before PrepareGoods created)
    1: "已备货",           # Prepared (merchant uploaded photo)
    2: "司机收货中",        # Driver Pickup (driver uploaded photo)
    3: "司机送达仓库",      # Driver Delivered to Warehouse
    4: "仓库已收货",        # Warehouse Received
    5: "司机配送用户",      # Driver Delivering to User
    6: "已送达",           # Delivered to User
    7: "完成"              # Complete
}

ORDER_STATUS_LABELS = {
    0: "Pending Payment",
    1: "Pending Shipment",
    2: "Pending Receipt",
    3: "Completed",
    4: "Cancelled",
    5: "After-Sales"
}


def _resolve_text(value: str | dict | None) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return value.get("en-US") or value.get("zh-CN") or json.dumps(value)
    return str(value)


async def _build_item(session: AsyncSession, item: OrderItem) -> OrderItemSchema:
    # Fetch main SKU image from uploaded files
    sku_image = None
    stmt = (
        select(UploadedFile.file_url)
        .where(UploadedFile.biz_type == 'product_sku')
        .where(UploadedFile.biz_id == item.sku_id)
        .where(UploadedFile.is_main == 1)
        .limit(1)
    )
    result = await session.execute(stmt)
    file_url = result.scalar_one_or_none()

    if file_url:
        # Prepend base URL if the path is relative
        if file_url.startswith('/'):
            sku_image = f"https://api.wetigu.com{file_url}"
        else:
            sku_image = file_url

    return OrderItemSchema(
        sku_id=item.sku_id,
        sku_code=item.sku_code,
        product_name=_resolve_text(item.product_name),
        quantity=item.quantity,
        sku_image=sku_image
    )


def _build_pickup_location(warehouse: Warehouse | None) -> WarehouseSnapshot | None:
    if not warehouse:
        return None
    address = f"{warehouse.line1}, {warehouse.city}, {warehouse.province} {warehouse.postal_code}"
    return WarehouseSnapshot(
        id=warehouse.id,
        name=warehouse.name,
        address=address,
        latitude=float(warehouse.latitude) if warehouse.latitude is not None else None,
        longitude=float(warehouse.longitude) if warehouse.longitude is not None else None
    )


def _build_delivery_proof(proof: DeliveryProof | None) -> DeliveryProofInfo | None:
    if not proof:
        return None
    return DeliveryProofInfo(
        photo_url=proof.photo_url,
        notes=proof.notes,
        created_at=proof.created_at
    )


async def _serialize(session: AsyncSession, order: Order) -> OrderSummary:
    pickup = _build_pickup_location(order.warehouse)
    items = [await _build_item(session, item) for item in order.items]
    return OrderSummary(
        order_sn=order.order_sn,
        shipping_status=order.shipping_status,
        order_status=order.order_status,
        driver_id=order.driver_id,
        driver_name=order.driver.name if order.driver else None,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        receiver_address=order.receiver_address,
        receiver_city=order.receiver_city,
        receiver_province=order.receiver_province,
        receiver_postal_code=order.receiver_postal_code,
        shipping_status_label=SHIPPING_STATUS_LABELS.get(order.shipping_status, "Unknown"),
        order_status_label=ORDER_STATUS_LABELS.get(order.order_status, "Unknown"),
        create_time=order.create_time,
        pickup_location=pickup,
        items=items
    )


async def _serialize_detail(session: AsyncSession, order: Order) -> OrderDetail:
    base = await _serialize(session, order)
    proof = _build_delivery_proof(order.delivery_proof)

    # Get delivery_type from PrepareGoods (single source of truth)
    delivery_type = await _get_order_delivery_type(session, order.id)

    return OrderDetail(
        **base.model_dump(),
        logistics_order_number=order.logistics_order_number,
        shipping_time=order.shipping_time,
        finish_time=order.finish_time,
        delivery_proof=proof,
        delivery_type=delivery_type,
        driver_receive_time=order.driver_receive_time,
        arrive_warehouse_time=order.arrive_warehouse_time,
        warehouse_shipping_time=order.warehouse_shipping_time
    )


async def _get_order_delivery_type(session: AsyncSession, order_id: int) -> int | None:
    """
    Get delivery_type for an order from PrepareGoods (single source of truth).

    Args:
        session: Database session
        order_id: Order ID

    Returns:
        0 = Merchant self-delivery
        1 = Third-party driver delivery
        None = Order not yet in any PrepareGoods package
    """
    stmt = (
        select(PrepareGoods.delivery_type)
        .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def fetch_assigned_orders(session: AsyncSession, driver_id: int, include_completed: bool = False) -> List[OrderSummary]:
    """
    Fetch assigned orders for a driver.

    Args:
        session: Database session
        driver_id: ID of the driver
        include_completed: If True, includes completed orders (shipping_status=3).
                          If False, only in-transit orders (1,2) for route planning.
    """
    if include_completed:
        status_filter = [0, 1, 2, 3]  # All statuses for TaskBoard
    else:
        status_filter = [1, 2]  # Only in-transit orders for RoutePlanner (exclude pending pickup)

    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.warehouse), selectinload(Order.driver))
        .where(Order.driver_id == driver_id)
        .where(Order.shipping_status.in_(status_filter))
        .order_by(Order.create_time.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return [await _serialize(session, order) for order in orders]


async def fetch_order_detail(session: AsyncSession, order_sn: str, driver_id: int) -> OrderDetail | None:
    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.warehouse), selectinload(Order.driver))
        .where(Order.order_sn == order_sn)
    )
    result = await session.execute(stmt)
    order = result.scalars().unique().first()
    if not order:
        return None
    return await _serialize_detail(session, order)


async def update_order_shipping_status(
    session: AsyncSession,
    order_sn: str,
    shipping_status: int,
    driver_id: int
) -> bool:
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .values(shipping_status=shipping_status)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def pickup_order(
    session: AsyncSession,
    order_sn: str,
    driver_id: int,
    photo_ids: List[int]
) -> bool:
    """
    Driver picks up goods from merchant (action_type=1).

    This function:
    1. Verifies order is in PrepareGoods package
    2. Updates order shipping_status to 2 (司机收货中)
    3. Sets driver_receive_time timestamp
    4. Creates OrderAction record with photo evidence

    Args:
        session: Database session
        order_sn: Order serial number
        driver_id: ID of the driver picking up the order
        photo_ids: IDs of uploaded pickup photos

    Returns:
        bool: True if pickup successful, False if order not found

    Raises:
        ValueError: If order not in PrepareGoods package (no delivery_type)
    """
    # Get order
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    # Verify order is in PrepareGoods package
    delivery_type = await _get_order_delivery_type(session, order.id)
    if delivery_type is None:
        raise ValueError(f"Order {order_sn} not in any PrepareGoods package. Cannot pickup.")

    # Update order status and timestamp
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .values(
            driver_id=driver_id,
            shipping_status=2,  # 司机收货中
            driver_receive_time=datetime.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()

    # Create OrderAction record
    await order_action_service.record_driver_pickup(
        session=session,
        order_id=order.id,
        driver_id=driver_id,
        photo_ids=photo_ids
    )

    return result.rowcount > 0


async def fetch_orders(
    session: AsyncSession,
    status: Optional[int] = None,
    driver_id: Optional[int] = None,
    unassigned: bool = False,
    search: Optional[str] = None,
    limit: int = 100
) -> List[OrderSummary]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.warehouse), selectinload(Order.driver))
        .order_by(Order.create_time.desc())
        .limit(limit)
    )

    if status is not None:
        stmt = stmt.where(Order.shipping_status == status)

    if driver_id is not None:
        stmt = stmt.where(Order.driver_id == driver_id)

    if unassigned:
        stmt = stmt.where(Order.driver_id.is_(None))

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Order.order_sn.ilike(pattern),
                Order.receiver_name.ilike(pattern),
                Order.receiver_phone.ilike(pattern)
            )
        )

    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return [await _serialize(session, order) for order in orders]


# New workflow functions for 4-workflow delivery system

async def arrive_warehouse(
    session: AsyncSession,
    order_sn: str,
    driver_id: int,
    photo_ids: List[int]
) -> bool:
    """
    Driver arrives at warehouse (action_type=2).

    Workflow: 商家→司机→仓库→用户 (Workflow 2 & 4)

    This function:
    1. Updates order shipping_status to 3 (司机送达仓库)
    2. Sets arrive_warehouse_time timestamp
    3. Creates OrderAction record with photo evidence

    Args:
        session: Database session
        order_sn: Order serial number
        driver_id: ID of the driver
        photo_ids: IDs of uploaded arrival photos

    Returns:
        bool: True if update successful, False if order not found
    """
    # Get order
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    # Update order status and timestamp
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.driver_id == driver_id)  # Verify driver owns this order
        .values(
            shipping_status=3,  # 司机送达仓库
            arrive_warehouse_time=datetime.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()

    # Create OrderAction record
    await order_action_service.record_driver_arrive_warehouse(
        session=session,
        order_id=order.id,
        driver_id=driver_id,
        photo_ids=photo_ids
    )

    return result.rowcount > 0


async def warehouse_receive(
    session: AsyncSession,
    order_sn: str,
    warehouse_staff_id: int,
    photo_ids: List[int] | None = None
) -> bool:
    """
    Warehouse receives goods from driver (action_type=3).

    Workflow: 商家→司机→仓库→用户 (Workflow 2 & 4)

    This function:
    1. Updates order shipping_status to 4 (仓库已收货)
    2. Creates OrderAction record

    Args:
        session: Database session
        order_sn: Order serial number
        warehouse_staff_id: ID of warehouse staff
        photo_ids: Optional IDs of uploaded receipt photos

    Returns:
        bool: True if update successful, False if order not found
    """
    # Get order
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    # Update order status
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .values(shipping_status=4)  # 仓库已收货
    )
    result = await session.execute(stmt)
    await session.commit()

    # Create OrderAction record
    await order_action_service.record_warehouse_receive(
        session=session,
        order_id=order.id,
        warehouse_staff_id=warehouse_staff_id,
        photo_ids=photo_ids
    )

    return result.rowcount > 0


async def warehouse_ship(
    session: AsyncSession,
    order_sn: str,
    warehouse_staff_id: int,
    photo_ids: List[int] | None = None
) -> bool:
    """
    Warehouse ships goods to end user (action_type=4).

    Workflow: 商家→司机→仓库→用户 (Workflow 2 only)

    This function:
    1. Updates order shipping_status to 5 (司机配送用户)
    2. Sets warehouse_shipping_time timestamp
    3. Creates OrderAction record

    Args:
        session: Database session
        order_sn: Order serial number
        warehouse_staff_id: ID of warehouse staff
        photo_ids: Optional IDs of uploaded shipping photos

    Returns:
        bool: True if update successful, False if order not found
    """
    # Get order
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    # Update order status and timestamp
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .values(
            shipping_status=5,  # 司机配送用户
            warehouse_shipping_time=datetime.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()

    # Create OrderAction record
    await order_action_service.record_warehouse_ship(
        session=session,
        order_id=order.id,
        warehouse_staff_id=warehouse_staff_id,
        photo_ids=photo_ids
    )

    return result.rowcount > 0


async def complete_delivery(
    session: AsyncSession,
    order_sn: str,
    completer_id: int,
    photo_ids: List[int]
) -> bool:
    """
    Complete delivery to end user (action_type=5).

    Works for all 4 workflows - final delivery step.

    This function:
    1. Updates order shipping_status to 6 (已送达)
    2. Sets finish_time timestamp
    3. Creates OrderAction record with delivery proof

    Args:
        session: Database session
        order_sn: Order serial number
        completer_id: ID of person completing delivery (driver or merchant)
        photo_ids: IDs of uploaded delivery proof photos

    Returns:
        bool: True if update successful, False if order not found
    """
    # Get order
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    # Update order status and timestamp
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .values(
            shipping_status=6,  # 已送达
            finish_time=datetime.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()

    # Create OrderAction record
    await order_action_service.record_delivery_complete(
        session=session,
        order_id=order.id,
        completer_id=completer_id,
        photo_ids=photo_ids
    )

    return result.rowcount > 0
