"""
Notification API routes for admin broadcast and management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.models.user import User
from app.services import notification_service
from app.services.notification_service import NotificationPriority, NotificationType

router = APIRouter()


class BroadcastRequest(BaseModel):
    """Request model for broadcasting notifications."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    priority: str = Field(default="normal")
    driver_ids: list[int] | None = Field(
        default=None,
        description="If None, broadcasts to all active drivers"
    )


class NotificationResponse(BaseModel):
    """Response model for notification operations."""
    success: bool
    count: int
    message: str


class SingleNotificationRequest(BaseModel):
    """Request model for sending notification to a single driver."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    priority: str = Field(default="normal")
    notification_type: str = Field(default="system_announcement")
    order_sn: str | None = None
    action_url: str | None = None


@router.post("/broadcast", response_model=NotificationResponse)
async def broadcast_notification(
    payload: BroadcastRequest,
    current_user: Annotated[User, Depends(deps.get_current_admin)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)]
) -> NotificationResponse:
    """
    Broadcast a notification to drivers (admin only).

    If driver_ids is provided, sends to those specific drivers.
    Otherwise, sends to all active drivers.
    """
    # Get target drivers
    if payload.driver_ids:
        stmt = select(Driver.id, Driver.phone).where(
            Driver.id.in_(payload.driver_ids),
            Driver.status == 1
        )
    else:
        stmt = select(Driver.id, Driver.phone).where(Driver.status == 1)

    result = await session.execute(stmt)
    drivers = [(row.id, row.phone) for row in result.all()]

    if not drivers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active drivers found"
        )

    # Convert priority string to enum
    try:
        priority = NotificationPriority(payload.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL

    # Broadcast notification
    count = await notification_service.broadcast_notification(
        session,
        driver_ids=drivers,
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=payload.title,
        message=payload.message,
        priority=priority
    )

    return NotificationResponse(
        success=count > 0,
        count=count,
        message=f"Notification sent to {count} drivers"
    )


@router.post("/driver/{driver_id}", response_model=NotificationResponse)
async def send_driver_notification(
    driver_id: int,
    payload: SingleNotificationRequest,
    current_user: Annotated[User, Depends(deps.get_current_admin)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)]
) -> NotificationResponse:
    """Send notification to a specific driver (admin only)."""
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Convert priority and type strings to enums
    try:
        priority = NotificationPriority(payload.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL

    try:
        notification_type = NotificationType(payload.notification_type)
    except ValueError:
        notification_type = NotificationType.SYSTEM_ANNOUNCEMENT

    notification = await notification_service.create_notification(
        session,
        driver_id=driver.id,
        driver_phone=driver.phone,
        notification_type=notification_type,
        title=payload.title,
        message=payload.message,
        priority=priority,
        order_sn=payload.order_sn,
        action_url=payload.action_url
    )

    return NotificationResponse(
        success=notification is not None,
        count=1 if notification else 0,
        message="Notification sent" if notification else "Failed to send notification"
    )


@router.post("/alert/{driver_id}", response_model=NotificationResponse)
async def send_urgent_alert(
    driver_id: int,
    payload: SingleNotificationRequest,
    current_user: Annotated[User, Depends(deps.get_current_admin)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)]
) -> NotificationResponse:
    """Send urgent alert to a specific driver (admin only)."""
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    notification = await notification_service.create_urgent_notification(
        session,
        driver_id=driver.id,
        driver_phone=driver.phone,
        title=payload.title,
        message=payload.message,
        order_sn=payload.order_sn
    )

    return NotificationResponse(
        success=notification is not None,
        count=1 if notification else 0,
        message="Urgent alert sent" if notification else "Failed to send alert"
    )


def _driver_phone(user: User) -> str:
    if not user.phonenumber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user has no phone number",
        )
    return user.phonenumber


@router.get("/mine")
async def list_mine(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)],
    limit: int = 100,
    unread_only: bool = False,
) -> dict:
    items = await notification_service.list_driver_notifications(
        session, _driver_phone(current_user), limit=min(limit, 200), unread_only=unread_only
    )
    return {"notifications": items, "total": len(items)}


@router.post("/mine/{notification_id}/read")
async def mark_mine_read(
    notification_id: int,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)],
) -> dict:
    ok = await notification_service.mark_read(session, notification_id, _driver_phone(current_user))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"success": True}


@router.post("/mine/read-all")
async def mark_mine_all_read(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)],
) -> dict:
    count = await notification_service.mark_all_read(session, _driver_phone(current_user))
    return {"success": True, "count": count}


@router.post("/mine/{notification_id}/dismiss")
async def dismiss_mine(
    notification_id: int,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)],
) -> dict:
    ok = await notification_service.dismiss(session, notification_id, _driver_phone(current_user))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"success": True}


@router.post("/mine/clear")
async def clear_mine(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(deps.get_db_session)],
) -> dict:
    count = await notification_service.clear_all(session, _driver_phone(current_user))
    return {"success": True, "count": count}
