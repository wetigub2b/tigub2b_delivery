"""
Notification service backed by local DB (tigu_notification).
Replaces the former Supabase implementation.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationType(str, Enum):
    ORDER_ASSIGNED = "order_assigned"
    ORDER_STATUS_CHANGE = "order_status_change"
    ORDER_PICKUP_READY = "order_pickup_ready"
    ORDER_URGENT = "order_urgent"
    SYSTEM_ALERT = "system_alert"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


def to_dict(n: Notification) -> dict:
    return {
        "id": n.id,
        "driver_id": n.driver_id,
        "driver_phone": n.driver_phone,
        "type": n.type,
        "title": n.title,
        "message": n.message,
        "priority": n.priority,
        "order_sn": n.order_sn,
        "action_url": n.action_url,
        "metadata": n.extra_metadata or {},
        "is_read": n.is_read,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "is_dismissed": n.is_dismissed,
        "dismissed_at": n.dismissed_at.isoformat() if n.dismissed_at else None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


async def create_notification(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    order_sn: str | None = None,
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict | None:
    n = Notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        type=notification_type.value,
        title=title,
        message=message,
        priority=priority.value,
        order_sn=order_sn,
        action_url=action_url,
        extra_metadata=metadata or {},
    )
    session.add(n)
    await session.commit()
    await session.refresh(n)
    return to_dict(n)


async def create_order_assigned_notification(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    receiver_name: str,
    receiver_address: str,
) -> dict | None:
    return await create_notification(
        session,
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_ASSIGNED,
        title="New Order Assigned",
        message=f"Deliver to {receiver_name} at {receiver_address}",
        priority=NotificationPriority.HIGH,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={"receiver_name": receiver_name, "receiver_address": receiver_address},
    )


async def create_order_status_notification(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    old_status: int,
    new_status: int,
    status_label: str,
) -> dict | None:
    return await create_notification(
        session,
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_STATUS_CHANGE,
        title="Order Status Updated",
        message=f"Order {order_sn}: {status_label}",
        priority=NotificationPriority.NORMAL,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={"old_status": old_status, "new_status": new_status},
    )


async def create_pickup_ready_notification(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    pickup_location: str,
) -> dict | None:
    return await create_notification(
        session,
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_PICKUP_READY,
        title="Order Ready for Pickup",
        message=f"Pick up order {order_sn} at {pickup_location}",
        priority=NotificationPriority.HIGH,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={"pickup_location": pickup_location},
    )


async def create_urgent_notification(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    title: str,
    message: str,
    order_sn: str | None = None,
) -> dict | None:
    return await create_notification(
        session,
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_URGENT,
        title=title,
        message=message,
        priority=NotificationPriority.URGENT,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}" if order_sn else None,
    )


async def create_system_announcement(
    session: AsyncSession,
    driver_id: int,
    driver_phone: str,
    title: str,
    message: str,
) -> dict | None:
    return await create_notification(
        session,
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=title,
        message=message,
        priority=NotificationPriority.LOW,
    )


async def broadcast_notification(
    session: AsyncSession,
    driver_ids: list[tuple[int, str]],
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    metadata: dict[str, Any] | None = None,
) -> int:
    rows = [
        Notification(
            driver_id=driver_id,
            driver_phone=driver_phone,
            type=notification_type.value,
            title=title,
            message=message,
            priority=priority.value,
            extra_metadata=metadata or {},
        )
        for driver_id, driver_phone in driver_ids
    ]
    session.add_all(rows)
    await session.commit()
    return len(rows)


async def list_driver_notifications(
    session: AsyncSession,
    driver_phone: str,
    limit: int = 100,
    unread_only: bool = False,
) -> list[dict]:
    stmt = (
        select(Notification)
        .where(Notification.driver_phone == driver_phone, Notification.is_dismissed == False)  # noqa: E712
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    result = await session.execute(stmt)
    return [to_dict(n) for n in result.scalars().all()]


async def mark_read(session: AsyncSession, notification_id: int, driver_phone: str) -> bool:
    stmt = select(Notification).where(
        Notification.id == notification_id, Notification.driver_phone == driver_phone
    )
    n = (await session.execute(stmt)).scalar_one_or_none()
    if not n:
        return False
    n.is_read = True
    n.read_at = datetime.now()
    await session.commit()
    return True


async def mark_all_read(session: AsyncSession, driver_phone: str) -> int:
    stmt = select(Notification).where(
        Notification.driver_phone == driver_phone, Notification.is_read == False  # noqa: E712
    )
    rows = (await session.execute(stmt)).scalars().all()
    now = datetime.now()
    for n in rows:
        n.is_read = True
        n.read_at = now
    await session.commit()
    return len(rows)


async def dismiss(session: AsyncSession, notification_id: int, driver_phone: str) -> bool:
    stmt = select(Notification).where(
        Notification.id == notification_id, Notification.driver_phone == driver_phone
    )
    n = (await session.execute(stmt)).scalar_one_or_none()
    if not n:
        return False
    n.is_dismissed = True
    n.dismissed_at = datetime.now()
    await session.commit()
    return True


async def clear_all(session: AsyncSession, driver_phone: str) -> int:
    stmt = select(Notification).where(
        Notification.driver_phone == driver_phone, Notification.is_dismissed == False  # noqa: E712
    )
    rows = (await session.execute(stmt)).scalars().all()
    now = datetime.now()
    for n in rows:
        n.is_dismissed = True
        n.dismissed_at = now
    await session.commit()
    return len(rows)
