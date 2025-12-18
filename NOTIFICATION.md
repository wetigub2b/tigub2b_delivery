# Notification Module Documentation

## Overview

Real-time notification system for the Tigu B2B Delivery platform using **Supabase** for storage and real-time delivery.

**Features:**
- Real-time in-app notifications via Supabase Realtime
- Order status updates and system alerts
- Admin broadcast functionality
- Bell icon with unread badge and dropdown

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Driver Mobile App                      │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ Supabase     │  │ Notification│  │ NotificationBell│  │
│  │ JS Client    │──│ Store       │──│ Component       │  │
│  └──────┬───────┘  └─────────────┘  └────────────────┘  │
│         │ Realtime Subscription                          │
└─────────┼────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                 SUPABASE (PostgreSQL)                    │
│  ┌─────────────────────────────────────────────────────┐│
│  │  notifications table + RLS + Realtime enabled       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
          ▲
          │ Insert notifications
┌─────────┴───────────────────────────────────────────────┐
│                 FastAPI Backend                          │
│  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ notification_    │──│ Order Service triggers      │  │
│  │ service.py       │  │ (status changes, assigns)   │  │
│  └──────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

**Table: `notifications`** (Supabase PostgreSQL)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| driver_id | BIGINT | Driver ID from MySQL |
| driver_phone | VARCHAR(20) | Driver phone for RLS |
| type | VARCHAR(50) | Notification type |
| title | TEXT | Notification title |
| message | TEXT | Notification body |
| priority | VARCHAR(20) | low, normal, high, urgent |
| order_sn | VARCHAR(50) | Related order (optional) |
| action_url | TEXT | Deep link URL (optional) |
| metadata | JSONB | Additional data |
| is_read | BOOLEAN | Read status |
| read_at | TIMESTAMPTZ | Read timestamp |
| is_dismissed | BOOLEAN | Dismissed status |
| created_at | TIMESTAMPTZ | Creation timestamp |

**SQL Migration:** `migrations/supabase_notifications.sql`

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

// Actions
await notificationStore.fetchNotifications();
await notificationStore.markAsRead('notification-id');
await notificationStore.markAllAsRead();
await notificationStore.dismissNotification('notification-id');
```

### Realtime Subscription

The store automatically subscribes to realtime updates when a user is logged in. New notifications appear instantly without page refresh.

## Backend Integration

### Creating Notifications Programmatically

```python
from app.services import notification_service
from app.services.notification_service import NotificationType, NotificationPriority

# Order assigned notification
await notification_service.create_order_assigned_notification(
    driver_id=123,
    driver_phone="1234567890",
    order_sn="ORD-12345",
    receiver_name="John Doe",
    receiver_address="123 Main St"
)

# Order status change
await notification_service.create_order_status_notification(
    driver_id=123,
    driver_phone="1234567890",
    order_sn="ORD-12345",
    old_status=1,
    new_status=2,
    status_label="In Transit"
)

# System announcement
await notification_service.create_system_announcement(
    driver_id=123,
    driver_phone="1234567890",
    title="Welcome!",
    message="Thank you for joining our platform"
)

# Broadcast to multiple drivers
await notification_service.broadcast_notification(
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
│   │   │   └── supabase.ts           # Supabase client config
│   │   ├── store/
│   │   │   └── notifications.ts      # Pinia notification store
│   │   ├── components/
│   │   │   └── NotificationBell.vue  # Bell UI component
│   │   └── locales/
│   │       └── en.json               # Translations (notifications section)
│   └── package.json                  # @supabase/supabase-js dependency
│
├── bff/
│   ├── app/
│   │   ├── services/
│   │   │   └── notification_service.py  # Notification business logic
│   │   ├── api/v1/routes/
│   │   │   └── notifications.py         # Admin API endpoints
│   │   └── core/
│   │       └── config.py                # Supabase settings
│   └── requirements.txt                 # supabase dependency
│
├── migrations/
│   └── supabase_notifications.sql       # Database schema
│
└── .env                                 # Environment variables
```

## Environment Variables

```bash
# Frontend (Vite)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Backend (Python)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Setup Instructions

### 1. Supabase Table Setup

Run the SQL migration in Supabase Dashboard → SQL Editor:

```sql
-- See migrations/supabase_notifications.sql for full schema
```

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

### 3. Configure Environment

Add Supabase credentials to `.env`:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Get from Supabase Dashboard → Settings → API

### 4. Add NotificationBell to UI

Import and add `<NotificationBell />` to your navigation component.

## Security

- **Row Level Security (RLS):** Drivers can only view/update their own notifications
- **Service Role Key:** Backend uses service role key to bypass RLS for creating notifications
- **JWT Claims:** RLS policies match `driver_phone` from JWT claims

## Troubleshooting

**Notifications not appearing:**
1. Check Supabase Realtime is enabled on the notifications table
2. Verify `driver_phone` matches between JWT and notification record
3. Check browser console for WebSocket connection errors

**Backend can't create notifications:**
1. Verify `SUPABASE_SERVICE_ROLE_KEY` is set correctly
2. Check Supabase project URL matches
3. Review backend logs for Supabase client errors

**RLS blocking queries:**
1. Ensure JWT contains `phonenumber` or `phone` claim
2. Verify RLS policies are correctly configured
3. Test queries in Supabase SQL Editor with RLS enabled
