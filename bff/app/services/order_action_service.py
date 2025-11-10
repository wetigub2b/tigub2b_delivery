"""
OrderAction Service

Handles order workflow audit trail including:
- Creating action records for status transitions
- Linking photo evidence files to actions
- Querying action history
- Managing workflow state validation

This service works with the file linking pattern:
1. Upload file → Get file_id from UploadedFile
2. Create OrderAction → Get action_id
3. Link file: UPDATE UploadedFile SET biz_id=action_id, biz_type='order_action'
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, UploadedFile
from app.models.order_action import OrderAction
from app.utils import generate_snowflake_id


# Action Type Constants
class ActionType:
    """Order action type codes"""
    GOODS_PREPARED = 0      # 备货 (Merchant prepared goods)
    DRIVER_PICKUP = 1       # 司机收货 (Driver picked up)
    DRIVER_TO_WAREHOUSE = 2 # 司机送达仓库 (Driver arrived at warehouse)
    WAREHOUSE_RECEIVE = 3   # 仓库收货 (Warehouse received)
    WAREHOUSE_SHIP = 4      # 仓库发货 (Warehouse shipped)
    DELIVERY_COMPLETE = 5   # 完成 (Delivery completed)
    REFUND_REQUEST = 6      # 退款申请 (Refund requested)
    REFUND_APPROVED = 7     # 退款同意 (Refund approved)
    REFUND_REJECTED = 8     # 退款拒绝 (Refund rejected)
    RETURN_GOODS = 9        # 退货 (Goods returned)
    REFUND_COMPLETE = 10    # 退款完成 (Refund completed)
    ORDER_CANCELLED = 11    # 订单取消 (Order cancelled)


async def create_order_action(
    session: AsyncSession,
    order_id: int,
    action_type: int,
    create_by: int,
    file_ids: List[int] | None = None,
    remark: str | None = None
) -> OrderAction:
    """
    Create order action record for workflow transition.

    This function:
    1. Fetches current order state
    2. Creates OrderAction record with status snapshots
    3. Links photo evidence files if provided
    4. Commits transaction

    Args:
        session: Database session
        order_id: Order ID
        action_type: Action type code (see ActionType constants)
        create_by: Creator identifier (driver_id, merchant_id, etc.)
        file_ids: Optional list of UploadedFile IDs for photo evidence
        remark: Optional notes/comments

    Returns:
        Created OrderAction instance

    Raises:
        ValueError: If order not found

    Example:
        # Driver uploads pickup photo and creates action
        file_id = 12345  # From file upload
        action = await create_order_action(
            session=session,
            order_id=order.id,
            action_type=ActionType.DRIVER_PICKUP,
            create_by=driver_id,
            file_ids=[file_id],
            remark="Picked up at merchant location"
        )
    """
    # Fetch order to get current state
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise ValueError(f"Order not found: {order_id}")

    # Create action record with state snapshot
    action = OrderAction(
        id=generate_snowflake_id(),
        order_id=order_id,
        order_status=order.order_status,
        shipping_status=order.shipping_status,
        shipping_type=order.shipping_type,
        action_type=action_type,
        logistics_voucher_file=",".join(str(fid) for fid in file_ids) if file_ids else None,
        create_by=create_by,
        remark=remark,
        create_time=datetime.now()
    )

    session.add(action)
    await session.flush()  # Get action.id

    # Link files to this action if provided
    if file_ids:
        await link_files_to_action(session, action.id, file_ids)

    await session.commit()

    return action


async def link_files_to_action(
    session: AsyncSession,
    action_id: int,
    file_ids: List[int]
) -> int:
    """
    Link uploaded files to an OrderAction record.

    Updates UploadedFile records to link them to the action:
    - Sets biz_id = action_id
    - Sets biz_type = 'order_action'

    Args:
        session: Database session
        action_id: OrderAction ID
        file_ids: List of UploadedFile IDs to link

    Returns:
        Number of files linked

    Example:
        # Upload files first, then link after action created
        file_ids = [123, 124, 125]  # From upload
        await link_files_to_action(session, action.id, file_ids)
    """
    if not file_ids:
        return 0

    stmt = (
        update(UploadedFile)
        .where(UploadedFile.id.in_(file_ids))
        .values(
            biz_id=action_id,
            biz_type="order_action"
        )
    )

    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount


async def get_order_actions(
    session: AsyncSession,
    order_id: int,
    action_type: int | None = None
) -> List[OrderAction]:
    """
    Get all actions for an order, ordered by create_time descending.

    Args:
        session: Database session
        order_id: Order ID
        action_type: Optional filter by action type

    Returns:
        List of OrderAction instances
    """
    stmt = (
        select(OrderAction)
        .where(OrderAction.order_id == order_id)
        .order_by(OrderAction.create_time.desc())
    )

    if action_type is not None:
        stmt = stmt.where(OrderAction.action_type == action_type)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_latest_action(
    session: AsyncSession,
    order_id: int,
    action_type: int | None = None
) -> OrderAction | None:
    """
    Get most recent action for an order.

    Args:
        session: Database session
        order_id: Order ID
        action_type: Optional filter by action type

    Returns:
        Most recent OrderAction or None if no actions found
    """
    stmt = (
        select(OrderAction)
        .where(OrderAction.order_id == order_id)
        .order_by(OrderAction.create_time.desc())
        .limit(1)
    )

    if action_type is not None:
        stmt = stmt.where(OrderAction.action_type == action_type)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_action_files(
    session: AsyncSession,
    action_id: int
) -> List[UploadedFile]:
    """
    Get all files linked to an action.

    Args:
        session: Database session
        action_id: OrderAction ID

    Returns:
        List of UploadedFile instances linked to this action
    """
    stmt = (
        select(UploadedFile)
        .where(UploadedFile.biz_type == "order_action")
        .where(UploadedFile.biz_id == action_id)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_action_by_id(
    session: AsyncSession,
    action_id: int
) -> OrderAction | None:
    """
    Get action by ID.

    Args:
        session: Database session
        action_id: OrderAction ID

    Returns:
        OrderAction instance or None if not found
    """
    stmt = select(OrderAction).where(OrderAction.id == action_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# Helper functions for specific workflow actions

async def record_goods_prepared(
    session: AsyncSession,
    order_id: int,
    merchant_id: int,
    photo_ids: List[int]
) -> OrderAction:
    """
    Record that merchant has prepared goods (action_type=0).

    Args:
        session: Database session
        order_id: Order ID
        merchant_id: Merchant ID
        photo_ids: IDs of uploaded preparation photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.GOODS_PREPARED,
        create_by=merchant_id,
        file_ids=photo_ids,
        remark="Goods prepared by merchant"
    )


async def record_driver_pickup(
    session: AsyncSession,
    order_id: int,
    driver_id: int,
    photo_ids: List[int]
) -> OrderAction:
    """
    Record that driver has picked up goods (action_type=1).

    Args:
        session: Database session
        order_id: Order ID
        driver_id: Driver ID
        photo_ids: IDs of uploaded pickup photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.DRIVER_PICKUP,
        create_by=driver_id,
        file_ids=photo_ids,
        remark="Driver picked up goods"
    )


async def record_driver_arrive_warehouse(
    session: AsyncSession,
    order_id: int,
    driver_id: int,
    photo_ids: List[int]
) -> OrderAction:
    """
    Record that driver arrived at warehouse (action_type=2).

    Args:
        session: Database session
        order_id: Order ID
        driver_id: Driver ID
        photo_ids: IDs of uploaded arrival photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.DRIVER_TO_WAREHOUSE,
        create_by=driver_id,
        file_ids=photo_ids,
        remark="Driver arrived at warehouse"
    )


async def record_warehouse_receive(
    session: AsyncSession,
    order_id: int,
    warehouse_staff_id: int,
    photo_ids: List[int] | None = None
) -> OrderAction:
    """
    Record that warehouse received goods (action_type=3).

    Args:
        session: Database session
        order_id: Order ID
        warehouse_staff_id: Warehouse staff ID
        photo_ids: Optional IDs of uploaded receipt photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.WAREHOUSE_RECEIVE,
        create_by=warehouse_staff_id,
        file_ids=photo_ids,
        remark="Warehouse received goods"
    )


async def record_warehouse_ship(
    session: AsyncSession,
    order_id: int,
    warehouse_staff_id: int,
    photo_ids: List[int] | None = None
) -> OrderAction:
    """
    Record that warehouse shipped goods to user (action_type=4).

    Args:
        session: Database session
        order_id: Order ID
        warehouse_staff_id: Warehouse staff ID
        photo_ids: Optional IDs of uploaded shipping photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.WAREHOUSE_SHIP,
        create_by=warehouse_staff_id,
        file_ids=photo_ids,
        remark="Warehouse shipped to user"
    )


async def record_delivery_complete(
    session: AsyncSession,
    order_id: int,
    completer_id: int,
    photo_ids: List[int]
) -> OrderAction:
    """
    Record that delivery is complete (action_type=5).

    Args:
        session: Database session
        order_id: Order ID
        completer_id: ID of person completing delivery (driver or merchant)
        photo_ids: IDs of uploaded delivery photos

    Returns:
        Created OrderAction
    """
    return await create_order_action(
        session=session,
        order_id=order_id,
        action_type=ActionType.DELIVERY_COMPLETE,
        create_by=completer_id,
        file_ids=photo_ids,
        remark="Delivery completed"
    )


async def get_workflow_timeline(
    session: AsyncSession,
    order_id: int
) -> List[dict]:
    """
    Get complete workflow timeline for an order with file URLs.

    Returns action history with linked files for display.

    Args:
        session: Database session
        order_id: Order ID

    Returns:
        List of dicts containing action details and file URLs

    Example:
        timeline = await get_workflow_timeline(session, order_id)
        # [
        #   {
        #     "action_type": 0,
        #     "create_time": "2025-11-09 10:00:00",
        #     "create_by": 123,
        #     "remark": "Goods prepared",
        #     "files": ["https://cdn.../photo1.jpg", "https://cdn.../photo2.jpg"]
        #   },
        #   ...
        # ]
    """
    # Get all actions for order
    actions = await get_order_actions(session, order_id)

    timeline = []
    for action in actions:
        # Get files for this action
        files = await get_action_files(session, action.id)

        timeline.append({
            "action_id": action.id,
            "action_type": action.action_type,
            "create_time": action.create_time.isoformat() if action.create_time else None,
            "create_by": action.create_by,
            "remark": action.remark,
            "order_status": action.order_status,
            "shipping_status": action.shipping_status,
            "files": [f.file_url for f in files]
        })

    return timeline
