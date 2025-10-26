from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, UploadedFile, Warehouse
from app.schemas.order import OrderDetail, OrderItem as OrderItemSchema, OrderSummary, WarehouseSnapshot

SHIPPING_STATUS_LABELS = {
    0: "Not Shipped",
    1: "Shipped",
    2: "Partially Shipped",
    3: "Delivered"
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
    return OrderDetail(
        **base.model_dump(),
        logistics_order_number=order.logistics_order_number,
        shipping_time=order.shipping_time,
        finish_time=order.finish_time
    )


async def fetch_assigned_orders(session: AsyncSession, driver_id: int, include_completed: bool = False) -> List[OrderSummary]:
    """
    Fetch assigned orders for a driver.

    Args:
        session: Database session
        driver_id: ID of the driver
        include_completed: If True, includes completed orders (shipping_status=3).
                          If False, only active orders (0,1,2) for route planning.
    """
    if include_completed:
        status_filter = [0, 1, 2, 3]  # All statuses for TaskBoard
    else:
        status_filter = [0, 1, 2]  # Only active orders for RoutePlanner

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
    driver_id: int
) -> bool:
    """
    Assign an unassigned order to a driver and set shipping_status to 0 (pending pickup).

    Args:
        session: Database session
        order_sn: Order serial number
        driver_id: ID of the driver picking up the order

    Returns:
        bool: True if order was successfully assigned, False if not found or already assigned
    """
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.driver_id.is_(None))  # Only pickup unassigned orders
        .values(driver_id=driver_id, shipping_status=0)
    )
    result = await session.execute(stmt)
    await session.commit()
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
