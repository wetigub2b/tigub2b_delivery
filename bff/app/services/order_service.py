from __future__ import annotations

import json
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, Warehouse
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


def _build_item(item: OrderItem) -> OrderItemSchema:
    return OrderItemSchema(
        sku_id=item.sku_id,
        sku_code=item.sku_code,
        product_name=_resolve_text(item.product_name),
        quantity=item.quantity
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


def _serialize(order: Order) -> OrderSummary:
    pickup = _build_pickup_location(order.warehouse)
    items = [_build_item(item) for item in order.items]
    return OrderSummary(
        order_sn=order.order_sn,
        shipping_status=order.shipping_status,
        order_status=order.order_status,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        receiver_address=order.receiver_address,
        receiver_city=order.receiver_city,
        receiver_province=order.receiver_province,
        receiver_postal_code=order.receiver_postal_code,
        shipping_status_label=SHIPPING_STATUS_LABELS.get(order.shipping_status, "Unknown"),
        order_status_label=ORDER_STATUS_LABELS.get(order.order_status, "Unknown"),
        pickup_location=pickup,
        items=items
    )


def _serialize_detail(order: Order) -> OrderDetail:
    base = _serialize(order)
    return OrderDetail(
        **base.model_dump(),
        logistics_order_number=order.logistics_order_number,
        shipping_time=order.shipping_time,
        finish_time=order.finish_time
    )


async def fetch_assigned_orders(session: AsyncSession, driver_id: int) -> List[OrderSummary]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.warehouse))
        .where(Order.shipping_status.in_([0, 1, 2]))
        .order_by(Order.create_time.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return [_serialize(order) for order in orders]


async def fetch_order_detail(session: AsyncSession, order_sn: str, driver_id: int) -> OrderDetail | None:
    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.warehouse))
        .where(Order.order_sn == order_sn)
    )
    result = await session.execute(stmt)
    order = result.scalars().unique().first()
    if not order:
        return None
    return _serialize_detail(order)


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
