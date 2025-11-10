"""
OrderAction API Routes

Endpoints for order workflow audit trail:
- Get action history for orders
- Get workflow timeline with photos
- Query specific actions
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.order_action import (
    OrderActionResponse,
    OrderActionWithFilesResponse,
    WorkflowTimelineItem,
    WorkflowTimelineResponse,
    get_action_type_label,
)
from app.services import order_action_service

router = APIRouter()


@router.get("/{order_sn}/actions", response_model=List[OrderActionResponse], response_model_by_alias=True)
async def get_order_actions(
    order_sn: str,
    action_type: int | None = None,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> List[OrderActionResponse]:
    """
    Get all actions for an order, ordered by create_time descending.

    Args:
        order_sn: Order serial number
        action_type: Optional filter by action type (0-11)
        current_user: Authenticated user
        session: Database session

    Returns:
        List of OrderAction records

    Raises:
        HTTPException 404: Order not found
    """
    # First get order to verify it exists
    from sqlalchemy import select
    from app.models.order import Order

    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found: {order_sn}"
        )

    # Get actions
    actions = await order_action_service.get_order_actions(
        session=session,
        order_id=order.id,
        action_type=action_type
    )

    # Build responses
    return [
        OrderActionResponse(
            id=action.id,
            order_id=action.order_id,
            order_status=action.order_status,
            shipping_status=action.shipping_status,
            shipping_type=action.shipping_type,
            action_type=action.action_type,
            action_type_label=get_action_type_label(action.action_type),
            logistics_voucher_file=action.logistics_voucher_file,
            create_by=action.create_by,
            remark=action.remark,
            create_time=action.create_time
        )
        for action in actions
    ]


@router.get("/{order_sn}/timeline", response_model=WorkflowTimelineResponse, response_model_by_alias=True)
async def get_workflow_timeline(
    order_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> WorkflowTimelineResponse:
    """
    Get complete workflow timeline for an order with file URLs.

    Returns action history with linked files for display in UI.

    Args:
        order_sn: Order serial number
        current_user: Authenticated user
        session: Database session

    Returns:
        WorkflowTimeline with ordered list of actions and photos

    Raises:
        HTTPException 404: Order not found
    """
    # First get order to verify it exists
    from sqlalchemy import select
    from app.models.order import Order

    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found: {order_sn}"
        )

    # Get timeline
    timeline_data = await order_action_service.get_workflow_timeline(
        session=session,
        order_id=order.id
    )

    # Build timeline items
    timeline_items = [
        WorkflowTimelineItem(
            action_id=item["action_id"],
            action_type=item["action_type"],
            action_type_label=get_action_type_label(item["action_type"]),
            create_time=item["create_time"],
            create_by=item["create_by"],
            remark=item["remark"],
            order_status=item["order_status"],
            shipping_status=item["shipping_status"],
            files=item["files"]
        )
        for item in timeline_data
    ]

    return WorkflowTimelineResponse(
        order_sn=order_sn,
        timeline=timeline_items
    )


@router.get("/{order_sn}/actions/latest", response_model=OrderActionResponse, response_model_by_alias=True)
async def get_latest_action(
    order_sn: str,
    action_type: int | None = None,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> OrderActionResponse:
    """
    Get most recent action for an order.

    Args:
        order_sn: Order serial number
        action_type: Optional filter by action type (0-11)
        current_user: Authenticated user
        session: Database session

    Returns:
        Most recent OrderAction

    Raises:
        HTTPException 404: Order not found or no actions found
    """
    # First get order to verify it exists
    from sqlalchemy import select
    from app.models.order import Order

    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found: {order_sn}"
        )

    # Get latest action
    action = await order_action_service.get_latest_action(
        session=session,
        order_id=order.id,
        action_type=action_type
    )

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No actions found for order: {order_sn}"
        )

    return OrderActionResponse(
        id=action.id,
        order_id=action.order_id,
        order_status=action.order_status,
        shipping_status=action.shipping_status,
        shipping_type=action.shipping_type,
        action_type=action.action_type,
        action_type_label=get_action_type_label(action.action_type),
        logistics_voucher_file=action.logistics_voucher_file,
        create_by=action.create_by,
        remark=action.remark,
        create_time=action.create_time
    )


@router.get("/actions/{action_id}", response_model=OrderActionWithFilesResponse, response_model_by_alias=True)
async def get_action_with_files(
    action_id: int,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> OrderActionWithFilesResponse:
    """
    Get action by ID with file URLs.

    Args:
        action_id: OrderAction ID
        current_user: Authenticated user
        session: Database session

    Returns:
        OrderAction with file URLs

    Raises:
        HTTPException 404: Action not found
    """
    # Get action
    action = await order_action_service.get_action_by_id(session, action_id)

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action not found: {action_id}"
        )

    # Get files
    files = await order_action_service.get_action_files(session, action_id)
    file_urls = [f.file_url for f in files]

    return OrderActionWithFilesResponse(
        id=action.id,
        order_id=action.order_id,
        order_status=action.order_status,
        shipping_status=action.shipping_status,
        shipping_type=action.shipping_type,
        action_type=action.action_type,
        action_type_label=get_action_type_label(action.action_type),
        logistics_voucher_file=action.logistics_voucher_file,
        create_by=action.create_by,
        remark=action.remark,
        create_time=action.create_time,
        file_urls=file_urls
    )
