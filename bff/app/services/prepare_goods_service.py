"""
PrepareGoods Service

Handles merchant preparation workflow including:
- Creating prepare goods packages
- Updating prepare status
- Querying prepare goods information
- Managing the relationship between orders and prepare packages

This service owns the delivery_type configuration (single source of truth).
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.prepare_goods import PrepareGoods, PrepareGoodsItem


async def create_prepare_package(
    session: AsyncSession,
    order_ids: List[int],
    shop_id: int,
    delivery_type: int,
    shipping_type: int,
    warehouse_id: int | None = None
) -> PrepareGoods:
    """
    Merchant creates prepare goods package for one or more orders.

    This sets delivery_type as the SINGLE SOURCE OF TRUTH for delivery configuration.
    All other services should read delivery_type from the PrepareGoods table.

    Args:
        session: Database session
        order_ids: List of order IDs to include in package
        shop_id: Merchant shop ID
        delivery_type: 0=Merchant self-delivery, 1=Third-party driver
        shipping_type: 0=To warehouse, 1=To user
        warehouse_id: Target warehouse (required if shipping_type=0)

    Returns:
        Created PrepareGoods instance with items loaded

    Raises:
        ValueError: If warehouse_id missing when shipping_type=0
        ValueError: If no orders found for given order_ids

    Workflow:
        1. Validate inputs
        2. Generate prepare_sn
        3. Create PrepareGoods record (sets delivery_type)
        4. Fetch order items
        5. Create PrepareGoodsItem records
        6. Commit transaction
    """
    # Validation
    if shipping_type == 0 and warehouse_id is None:
        raise ValueError("warehouse_id required when shipping_type=0 (to warehouse)")

    if not order_ids:
        raise ValueError("order_ids cannot be empty")

    # Generate prepare serial number
    # Format: PREP + timestamp (milliseconds)
    from time import time_ns
    prepare_sn = f"PREP{int(time_ns() / 1000000)}"

    # Create prepare goods record
    prepare_goods = PrepareGoods(
        prepare_sn=prepare_sn,
        order_ids=",".join(str(oid) for oid in order_ids),
        delivery_type=delivery_type,  # SINGLE SOURCE OF TRUTH
        shipping_type=shipping_type,
        prepare_status=None,  # NULL = pending prepare
        shop_id=shop_id,
        warehouse_id=warehouse_id,
        create_time=datetime.now()
    )

    session.add(prepare_goods)
    await session.flush()  # Get prepare_goods.id

    # Fetch order items for all orders
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id.in_(order_ids))
        .where(Order.shop_id == shop_id)  # Security: only merchant's orders
    )
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()

    if not orders:
        raise ValueError(f"No orders found for shop_id={shop_id} with order_ids={order_ids}")

    # Create prepare goods items from order items
    for order in orders:
        for item in order.items:
            prepare_item = PrepareGoodsItem(
                prepare_id=prepare_goods.id,
                order_item_id=item.id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                quantity=item.quantity,
                create_time=datetime.now()
            )
            session.add(prepare_item)

    await session.commit()

    # Refresh to get relationships loaded
    await session.refresh(prepare_goods)

    return prepare_goods


async def update_prepare_status(
    session: AsyncSession,
    prepare_sn: str,
    new_status: int
) -> bool:
    """
    Update prepare goods status.

    Status Flow:
    - NULL: 待备货 (Pending prepare)
    - 0: 已备货 (Prepared - merchant uploaded photo)
    - 1: 司机收货中 (Driver pickup - driver uploaded photo)
    - 2: 司机送达仓库 (Driver delivered to warehouse)
    - 3: 仓库已收货 (Warehouse received)
    - 4: 司机配送用户 (Driver delivering to user)
    - 5: 已送达 (Delivered to user)
    - 6: 完成 (Complete)

    Args:
        session: Database session
        prepare_sn: Prepare goods serial number
        new_status: New status value (0-6 or None)

    Returns:
        True if update successful, False if prepare_sn not found
    """
    stmt = (
        update(PrepareGoods)
        .where(PrepareGoods.prepare_sn == prepare_sn)
        .values(prepare_status=new_status, update_time=datetime.now())
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def get_prepare_package(
    session: AsyncSession,
    prepare_sn: str
) -> PrepareGoods | None:
    """
    Get prepare package by serial number with all items loaded.

    Args:
        session: Database session
        prepare_sn: Prepare goods serial number

    Returns:
        PrepareGoods instance with items, warehouse, driver relationships loaded
        None if not found
    """
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.items).selectinload(PrepareGoodsItem.order_item),
            selectinload(PrepareGoods.warehouse),
            selectinload(PrepareGoods.driver)
        )
        .where(PrepareGoods.prepare_sn == prepare_sn)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_prepare_package_by_order_id(
    session: AsyncSession,
    order_id: int
) -> PrepareGoods | None:
    """
    Get prepare package that contains a specific order.

    This is the primary method to get delivery_type for an order
    (single source of truth pattern).

    Args:
        session: Database session
        order_id: Order ID to search for

    Returns:
        PrepareGoods instance if order is in a package
        None if order not yet prepared

    Note:
        Uses LIKE query on order_ids CSV field.
        For better performance, consider adding fulltext index on order_ids.
    """
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.warehouse),
            selectinload(PrepareGoods.driver)
        )
        .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_shop_prepare_packages(
    session: AsyncSession,
    shop_id: int,
    status: int | None = None,
    limit: int = 50
) -> List[PrepareGoods]:
    """
    Get prepare packages for a merchant shop.

    Args:
        session: Database session
        shop_id: Merchant shop ID
        status: Filter by prepare_status (None = all statuses)
        limit: Maximum number of records to return

    Returns:
        List of PrepareGoods instances
    """
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.items),
            selectinload(PrepareGoods.warehouse),
            selectinload(PrepareGoods.driver)
        )
        .where(PrepareGoods.shop_id == shop_id)
        .order_by(PrepareGoods.create_time.desc())
        .limit(limit)
    )

    if status is not None:
        stmt = stmt.where(PrepareGoods.prepare_status == status)

    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def assign_driver_to_prepare(
    session: AsyncSession,
    prepare_sn: str,
    driver_id: int
) -> bool:
    """
    Assign a driver to a prepare goods package (for third-party delivery).

    Only applicable when delivery_type=1 (third-party delivery).

    Args:
        session: Database session
        prepare_sn: Prepare goods serial number
        driver_id: Driver ID to assign

    Returns:
        True if assignment successful, False if prepare_sn not found

    Note:
        Does not validate if delivery_type=1. Caller should check.
    """
    stmt = (
        update(PrepareGoods)
        .where(PrepareGoods.prepare_sn == prepare_sn)
        .values(driver_id=driver_id, update_time=datetime.now())
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def get_driver_assigned_packages(
    session: AsyncSession,
    driver_id: int,
    limit: int = 50
) -> List[PrepareGoods]:
    """
    Get prepare packages assigned to a driver.

    Only returns packages with delivery_type=1 (third-party delivery).

    Args:
        session: Database session
        driver_id: Driver ID
        limit: Maximum number of records

    Returns:
        List of PrepareGoods instances assigned to driver
    """
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.items),
            selectinload(PrepareGoods.warehouse)
        )
        .where(PrepareGoods.driver_id == driver_id)
        .where(PrepareGoods.delivery_type == 1)  # Third-party only
        .order_by(PrepareGoods.create_time.desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def get_available_packages(
    session: AsyncSession,
    limit: int = 50
) -> List[PrepareGoods]:
    """
    Get available packages that are ready for driver pickup.

    Returns packages that are:
    - prepare_status = 0 (prepared, ready for pickup)
    - driver_id IS NULL (not assigned to any driver yet)
    - delivery_type = 1 (third-party driver delivery)

    Args:
        session: Database session
        limit: Maximum number of records

    Returns:
        List of PrepareGoods instances available for pickup
    """
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.items),
            selectinload(PrepareGoods.warehouse)
        )
        .where(PrepareGoods.driver_id.is_(None))  # Not assigned
        .where(PrepareGoods.prepare_status == 0)  # Prepared
        .where(PrepareGoods.delivery_type == 1)  # Third-party only
        .order_by(PrepareGoods.create_time.desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def get_order_delivery_type(
    session: AsyncSession,
    order_id: int
) -> int | None:
    """
    Get delivery_type for an order from PrepareGoods (single source of truth).

    This is a convenience function for getting just the delivery_type
    without loading the full PrepareGoods object.

    Args:
        session: Database session
        order_id: Order ID

    Returns:
        0 = Merchant self-delivery
        1 = Third-party driver delivery
        None = Order not yet in any PrepareGoods package

    Usage:
        delivery_type = await get_order_delivery_type(session, order_id)
        if delivery_type == 1:
            # Third-party delivery workflow
        elif delivery_type == 0:
            # Merchant self-delivery workflow
        else:
            # Order not yet prepared
    """
    stmt = (
        select(PrepareGoods.delivery_type)
        .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
