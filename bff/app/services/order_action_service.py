"""
Service for managing order action audit trail and file linking.
Handles workflow step logging with photo evidence.
"""
from __future__ import annotations

from datetime import datetime
from time import time_ns
from typing import Optional

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderAction, UploadedFile


def generate_snowflake_id() -> int:
    """
    Generate a simple snowflake-like ID using nanosecond timestamp.

    In production, use a proper distributed ID generator.
    For now, using millisecond timestamp as a simple unique ID.
    """
    return int(time_ns() / 1000000)


async def create_order_action(
    session: AsyncSession,
    order_id: int,
    order_status: int,
    shipping_status: int,
    shipping_type: int,
    action_type: int,
    file_ids: list[int] | None = None,
    create_by: str = "system",
    remark: str | None = None
) -> OrderAction:
    """
    Create order action record with optional file linking.

    Args:
        session: Database session
        order_id: Order ID
        order_status: Current order_status
        shipping_status: Current shipping_status
        shipping_type: 0=User, 1=Warehouse
        action_type: Action type code (0-10)
        file_ids: List of uploaded file IDs to link
        create_by: Creator identifier
        remark: Optional remarks

    Returns:
        Created OrderAction instance
    """
    # Generate snowflake ID
    action_id = generate_snowflake_id()

    # Prepare logistics_voucher_file (comma-separated file IDs)
    voucher_file = ",".join(str(fid) for fid in file_ids) if file_ids else None

    # Insert action record
    stmt = insert(OrderAction).values(
        id=action_id,
        order_id=order_id,
        order_status=order_status,
        shipping_status=shipping_status,
        shipping_type=shipping_type,
        action_type=action_type,
        logistics_voucher_file=voucher_file,
        create_by=create_by,
        create_time=datetime.now(),
        remark=remark
    )
    await session.execute(stmt)

    # Link files to action via biz_id
    if file_ids:
        for file_id in file_ids:
            update_stmt = (
                update(UploadedFile)
                .where(UploadedFile.id == file_id)
                .values(biz_id=action_id, biz_type="order_action")
            )
            await session.execute(update_stmt)

    await session.commit()

    # Fetch and return created action
    result = await session.execute(
        select(OrderAction).where(OrderAction.id == action_id)
    )
    return result.scalar_one()


async def get_order_actions(
    session: AsyncSession,
    order_id: int
) -> list[OrderAction]:
    """
    Get all action records for an order, ordered by creation time.

    Args:
        session: Database session
        order_id: Order ID

    Returns:
        List of OrderAction records
    """
    stmt = (
        select(OrderAction)
        .where(OrderAction.order_id == order_id)
        .order_by(OrderAction.create_time.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_action_files(
    session: AsyncSession,
    action_id: int
) -> list[UploadedFile]:
    """
    Get all files linked to an action.

    Args:
        session: Database session
        action_id: OrderAction ID

    Returns:
        List of UploadedFile records
    """
    stmt = (
        select(UploadedFile)
        .where(UploadedFile.biz_id == action_id)
        .where(UploadedFile.biz_type == "order_action")
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_latest_action(
    session: AsyncSession,
    order_id: int
) -> Optional[OrderAction]:
    """
    Get the most recent action for an order.

    Args:
        session: Database session
        order_id: Order ID

    Returns:
        Most recent OrderAction or None
    """
    stmt = (
        select(OrderAction)
        .where(OrderAction.order_id == order_id)
        .order_by(OrderAction.create_time.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()
