# Notification Module Documentation

## Overview

Local notification system for the Tigu B2B Delivery platform backed by **SQLite**
(`tigu_notification`). No Supabase — the BFF owns writes and reads; the driver app
polls the BFF.

**Features:**
- Driver notifications polled from BFF every 30s
- Order status updates and system alerts
- Admin broadcast functionality
- Bell icon with unread badge and dropdown

> Historical note: notifications were previously stored in Supabase (`notifications`
> table). They were migrated to `tigu_notification` in SQLite; Supabase is decommissioned.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Driver Mobile App                      │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ BFF Axios    │  │ Notification│  │ NotificationBell│  │
│  │ client       │──│ Store       │──│ Component       │  │
│  └──────┬───────┘  └─────────────┘  └────────────────┘  │
│         │ 30s polling                                    │
└─────────┼────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend + SQLite                    │
│  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ notification_    │  │ tigu_notification table     │  │
│  │ service.py       │──│                             │  │
│  └──────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

**Table: `tigu_notification`** (SQLite, created via SQLAlchemy `Base.metadata.create_all`)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK autoincrement | Primary key |
| driver_id | BIGINT | Driver ID |
| driver_phone | VARCHAR(20) | Driver phone (lookup key) |
| type | VARCHAR(50) | Notification type |
| title | VARCHAR(200) | Notification title |
| message | TEXT | Notification body |
| priority | VARCHAR(20) | low, normal, high, urgent |
| order_sn | VARCHAR(64) | Related order (optional) |
| action_url | VARCHAR(512) | Deep link URL (optional) |
| metadata | JSON | Additional data |
| is_read | BOOLEAN | Read status |
| read_at | DATETIME | Read timestamp |
| is_dismissed | BOOLEAN | Dismissed status |
| dismissed_at | DATETIME | Dismissed timestamp |
| created_at | DATETIME | Creation timestamp |

## Notification Types

| Type | Description | Priority |
|------|-------------|----------|
| `order_assigned` | New order assigned to driver | HIGH |
| `order_status_change` | Order status updated | NORMAL |
| `order_pickup_ready` | Order ready for pickup | HIGH |
| `order_urgent` | Urgent action required | URGENT |
| `system_alert` | System warnings | NORMAL |
| `system_announcement` | Admin announcements | LOW |

## API Endpoints

### Admin Endpoints (require admin authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/notifications/broadcast` | Broadcast to all/selected drivers |
| POST | `/api/notifications/driver/{id}` | Send to specific driver |
| POST | `/api/notifications/alert/{id}` | Send urgent alert to driver |

### Driver Endpoints (require driver authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/mine?limit=100&unread_only=false` | List own notifications |
| POST | `/api/notifications/mine/{id}/read` | Mark one as read |
| POST | `/api/notifications/mine/read-all` | Mark all as read |
| POST | `/api/notifications/mine/{id}/dismiss` | Dismiss one |
| POST | `/api/notifications/mine/clear` | Dismiss all |

### Request Examples

**Broadcast to all drivers:**
```json
POST /api/notifications/broadcast
{
  "title": "System Maintenance",
  "message": "System will be down for maintenance at 10 PM",
  "priority": "normal"
}
```

**Send to specific drivers:**
```json
POST /api/notifications/broadcast
{
  "title": "New Delivery Zone",
  "message": "You have been added to the downtown zone",
  "priority": "high",
  "driver_ids": [1, 2, 3]
}
```

**Send to single driver:**
```json
POST /api/notifications/driver/123
{
  "title": "Order Update",
  "message": "Your order has been reassigned",
  "priority": "normal",
  "order_sn": "ORD-12345"
}
```

## Frontend Integration

### NotificationBell Component

Add to your navigation/header:

```vue
<template>
  <header>
    <NotificationBell />
  </header>
</template>

<script setup>
import NotificationBell from '@/components/NotificationBell.vue';
</script>
```

### Using the Notification Store

```typescript
import { useNotificationStore } from '@/store/notifications';

const notificationStore = useNotificationStore();

// Access state
console.log(notificationStore.unreadCount);
console.log(notificationStore.notifications);

// Actions (ids are numbers — local DB keys)
await notificationStore.fetchNotifications();
await notificationStore.markAsRead(12);
await notificationStore.markAllAsRead();
await notificationStore.dismissNotification(12);
```

### Polling

The store polls `GET /notifications/mine` every 30s when logged in and raises a
browser notification for new high/urgent items. No realtime subscription.

## Backend Integration

### Creating Notifications Programmatically

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import notification_service
from app.services.notification_service import NotificationType, NotificationPriority

# Order assigned notification
await notification_service.create_order_assigned_notification(
    session,
    driver_id=123,
    driver_phone="1234567890",
    order_sn="ORD-12345",
    receiver_name="John Doe",
    receiver_address="123 Main St"
)

# Order status change
await notification_service.create_order_status_notification(
    session,
    driver_id=123,
    driver_phone="1234567890",
    order_sn="ORD-12345",
    old_status=1,
    new_status=2,
    status_label="In Transit"
)

# System announcement
await notification_service.create_system_announcement(
    session,
    driver_id=123,
    driver_phone="1234567890",
    title="Welcome!",
    message="Thank you for joining our platform"
)

# Broadcast to multiple drivers
await notification_service.broadcast_notification(
    session,
    driver_ids=[(1, "1111111111"), (2, "2222222222")],
    notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
    title="Holiday Schedule",
    message="Office closed on Dec 25"
)
```

## File Structure

```
tigub2b_delivery/
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   └── notifications.ts      # Notification types (local)
│   │   ├── store/
│   │   │   └── notifications.ts      # Pinia store (BFF polling)
│   │   ├── components/
│   │   │   └── NotificationBell.vue  # Bell UI component
│   │   └── locales/
│   │       └── en.json               # Translations (notifications section)
│
├── bff/
│   ├── app/
│   │   ├── models/
│   │   │   └── notification.py         # tigu_notification model
│   │   ├── services/
│   │   │   └── notification_service.py # SQLite business logic
│   │   ├── api/v1/routes/
│   │   │   └── notifications.py        # Admin + driver endpoints
│   │   └── core/
│   │       └── config.py               # DB settings
│
└── .env                                 # Environment variables (no Supabase)
```

## Environment Variables

No notification-specific variables. The BFF database URL covers storage:

```bash
DATABASE_URL=sqlite+aiosqlite:///./data/delivery.db
```

## Setup Instructions

### 1. Create tables + seed

```bash
cd bff
DATABASE_URL="sqlite+aiosqlite:///./data/delivery.db" ./.venv/bin/python init_sqlite.py
```

(`tigu_notification` is created via `Base.metadata.create_all`; no SQL migration needed.)

### 2. Install Dependencies

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd bff
pip install -r requirements.txt
```

### 3. Add NotificationBell to UI

Import and add `<NotificationBell />` to your navigation component.

## Security

- Driver endpoints resolve identity from the JWT (`get_current_user`) and scope all
  queries by that user's `phonenumber` — drivers only see their own notifications.
- Admin endpoints require `get_current_admin`.

## Troubleshooting

**Notifications not appearing:**
1. Verify BFF is running and `GET /api/notifications/mine` returns rows for the driver's phone
2. Verify `driver_phone` on the notification matches `sys_user.phonenumber`
3. Check browser console for API errors; ensure `delivery_token` is set

**Backend can't create notifications:**
1. Check `tigu_notification` table exists (`sqlite3 data/delivery.db ".tables"`)
2. Review backend logs for SQLAlchemy errors
