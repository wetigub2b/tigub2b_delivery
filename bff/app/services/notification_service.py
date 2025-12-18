"""
Notification service for creating and broadcasting notifications via Supabase.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from supabase import create_client, Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Supabase client singleton
_supabase_client: Client | None = None


def get_supabase() -> Client | None:
    """Get or create Supabase client singleton."""
    global _supabase_client

    if _supabase_client is None:
        if settings.supabase_url and settings.supabase_service_role_key:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
        else:
            logger.warning("Supabase not configured. Notifications will be disabled.")

    return _supabase_client


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


async def create_notification(
    driver_id: int,
    driver_phone: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    order_sn: str | None = None,
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None
) -> dict | None:
    """
    Create a new notification for a driver.

    Args:
        driver_id: Driver's ID from MySQL database
        driver_phone: Driver's phone number (used for RLS matching)
        notification_type: Type of notification
        title: Notification title
        message: Notification message body
        priority: Priority level (low, normal, high, urgent)
        order_sn: Related order serial number (optional)
        action_url: Deep link URL for notification click (optional)
        metadata: Additional JSON metadata (optional)

    Returns:
        Created notification dict or None if failed
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Cannot create notification: Supabase not configured")
        return None

    notification_data = {
        "driver_id": driver_id,
        "driver_phone": driver_phone,
        "type": notification_type.value,
        "title": title,
        "message": message,
        "priority": priority.value,
        "order_sn": order_sn,
        "action_url": action_url,
        "metadata": metadata or {},
    }

    try:
        result = supabase.table("notifications").insert(notification_data).execute()

        if result.data:
            logger.info(
                f"Created notification for driver {driver_id}: {notification_type.value}"
            )
            return result.data[0]

        return None

    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return None


async def create_order_assigned_notification(
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    receiver_name: str,
    receiver_address: str
) -> dict | None:
    """Create notification when a new order is assigned to driver."""
    return await create_notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_ASSIGNED,
        title="New Order Assigned",
        message=f"Deliver to {receiver_name} at {receiver_address}",
        priority=NotificationPriority.HIGH,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={
            "receiver_name": receiver_name,
            "receiver_address": receiver_address
        }
    )


async def create_order_status_notification(
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    old_status: int,
    new_status: int,
    status_label: str
) -> dict | None:
    """Create notification when order status changes."""
    return await create_notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_STATUS_CHANGE,
        title="Order Status Updated",
        message=f"Order {order_sn}: {status_label}",
        priority=NotificationPriority.NORMAL,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={
            "old_status": old_status,
            "new_status": new_status
        }
    )


async def create_pickup_ready_notification(
    driver_id: int,
    driver_phone: str,
    order_sn: str,
    pickup_location: str
) -> dict | None:
    """Create notification when order is ready for pickup."""
    return await create_notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_PICKUP_READY,
        title="Order Ready for Pickup",
        message=f"Pick up order {order_sn} at {pickup_location}",
        priority=NotificationPriority.HIGH,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}",
        metadata={
            "pickup_location": pickup_location
        }
    )


async def create_urgent_notification(
    driver_id: int,
    driver_phone: str,
    title: str,
    message: str,
    order_sn: str | None = None
) -> dict | None:
    """Create urgent notification requiring immediate attention."""
    return await create_notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.ORDER_URGENT,
        title=title,
        message=message,
        priority=NotificationPriority.URGENT,
        order_sn=order_sn,
        action_url=f"/order/{order_sn}" if order_sn else None
    )


async def create_system_announcement(
    driver_id: int,
    driver_phone: str,
    title: str,
    message: str
) -> dict | None:
    """Create system-wide announcement notification."""
    return await create_notification(
        driver_id=driver_id,
        driver_phone=driver_phone,
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=title,
        message=message,
        priority=NotificationPriority.LOW
    )


async def broadcast_notification(
    driver_ids: list[tuple[int, str]],
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    metadata: dict[str, Any] | None = None
) -> int:
    """
    Broadcast notification to multiple drivers.

    Args:
        driver_ids: List of (driver_id, driver_phone) tuples
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        priority: Priority level
        metadata: Additional metadata

    Returns:
        Number of successfully created notifications
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Cannot broadcast: Supabase not configured")
        return 0

    notifications = [
        {
            "driver_id": driver_id,
            "driver_phone": driver_phone,
            "type": notification_type.value,
            "title": title,
            "message": message,
            "priority": priority.value,
            "metadata": metadata or {}
        }
        for driver_id, driver_phone in driver_ids
    ]

    try:
        result = supabase.table("notifications").insert(notifications).execute()
        count = len(result.data) if result.data else 0
        logger.info(f"Broadcast notification to {count} drivers")
        return count

    except Exception as e:
        logger.error(f"Failed to broadcast notification: {e}")
        return 0
