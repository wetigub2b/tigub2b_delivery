# Driver Delivery Workflow Guide
# 司机配送流程指南

---

## Table of Contents | 目录

- [English Version](#english-version)
  - [Overview](#overview)
  - [Delivery Type Routing](#delivery-type-routing)
  - [Warehouse Delivery Path](#warehouse-delivery-path)
  - [Direct-to-User Delivery Path](#direct-to-user-delivery-path)
  - [Database Schema Reference](#database-schema-reference)
  - [API Endpoints Reference](#api-endpoints-reference)
- [中文版本](#中文版本)
  - [概述](#概述-1)
  - [配送类型路由](#配送类型路由)
  - [仓库配送路径](#仓库配送路径)
  - [直送用户路径](#直送用户路径)
  - [数据库架构参考](#数据库架构参考-1)
  - [API接口参考](#api接口参考-1)

---

# English Version

## Overview

This document describes the complete delivery workflow from a driver's perspective, including all database operations that occur at each phase. The system supports **two delivery paths** determined by `shipping_type`:

- **Warehouse Delivery** (`shipping_type = 1`): Merchant → Driver → Warehouse → Final Delivery
- **Direct-to-User Delivery** (`shipping_type = 0`): Merchant → Driver → User

### Key Features

- **Audit Trail**: Every workflow step is logged in `tigu_order_action` table
- **Photo Evidence**: All transitions require photo upload to `tigu_uploaded_files`
- **Dual Workflow**: Warehouse vs. direct-to-user delivery paths
- **Snowflake IDs**: Distributed unique ID generation for action records

---

## Delivery Type Routing

The `shipping_type` field in `tigu_order` determines which workflow path the driver follows:

```
┌─────────────────────────────────────────────────────────────────┐
│                     DELIVERY ROUTING                             │
└─────────────────────────────────────────────────────────────────┘

            [Order Ready - Merchant Prepared Goods]
                            ↓
                   ┌────────┴────────┐
                   │  shipping_type?  │
                   └────────┬────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
         = 1                              = 0
     (Warehouse)                        (Direct)
            │                               │
            ↓                               ↓
┌───────────────────────┐      ┌───────────────────────┐
│  Warehouse Path       │      │  Direct Path          │
│                       │      │                       │
│  1. Driver Pickup     │      │  1. Driver Pickup     │
│  2. Arrive Warehouse  │      │  2. Complete Delivery │
│  3. Warehouse Ship    │      │                       │
│  4. Complete Delivery │      │                       │
└───────────────────────┘      └───────────────────────┘
```

### Status Code Mapping

| shipping_status | Label | Warehouse Path | Direct-to-User Path |
|-----------------|-------|----------------|---------------------|
| `NULL` | Unassigned | ✓ Available for pickup | ✓ Available for pickup |
| `2` | Driver Received | ✓ Driver picked up goods | ❌ N/A |
| `3` | Arrived at Warehouse | ✓ Delivered to warehouse | ❌ N/A |
| `4` | Warehouse Shipped | ✓ Warehouse ships to end user | ✓ Driver picked up goods |
| `5` | Delivered | ✓ Final delivery complete | ✓ Delivery complete |

---

## Warehouse Delivery Path

**Flow**: `shipping_type = 1` (Merchant → Driver → Warehouse → End User)

```
[Goods Ready] → [Driver Pickup] → [Arrive Warehouse] → [Warehouse Ships] → [Delivered]
   status=1        status=2           status=3            status=4          status=5
  action=0        action=1           action=2            action=3          action=4
```

---

### Phase 1: Goods Ready (Merchant Prepares Order)

**Trigger**: Backend merchant clicks "Goods Prepared" button

#### Database State

**Table**: `tigu_order`

| Column | Value | Note |
|--------|-------|------|
| `driver_id` | `NULL` | No driver assigned |
| `shipping_status` | `NULL` | Awaiting driver assignment |
| `shipping_type` | `1` | Warehouse delivery |
| `order_status` | `1` | Pending Shipment |
| `shipping_time` | `NULL` | Not yet shipped |
| `driver_receive_time` | `NULL` | Not yet picked up |

#### Business Logic
- Merchant marks inventory as ready for pickup
- Order becomes visible in driver's "Available Orders" list
- System filters orders by `shipping_type` to show appropriate workflow

---

### Phase 2: Driver Pickup (司机收货)

**Driver Action**: Driver collects goods from merchant/warehouse and confirms receipt

#### API Call
```http
POST /api/v1/orders/{order_sn}/pickup
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Picked up 5 boxes from merchant warehouse"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Order picked up successfully",
  "order": {
    "orderSn": "1973427465779625985",
    "shippingStatus": 2,
    "orderStatus": 2,
    "actionId": "1973438237720702978"
  }
}
```

#### Database Operations

**Step 1**: Insert photo to `tigu_uploaded_files`

```sql
-- Generate Snowflake ID for file
INSERT INTO tigu_uploaded_files (
  id,
  file_name,
  file_url,
  file_size,
  file_type,
  biz_id,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),  -- File ID
  'pickup_1973427465779625985_1705315200.jpeg',
  '/uploads/delivery/pickup_1973427465779625985_1705315200.jpeg',
  1245678,
  'image/jpeg',
  NULL,  -- Will be updated after action insert
  NOW()
);
```

**Step 2**: Update order status

```sql
UPDATE tigu_order
SET order_status = 2,
    shipping_status = 2,
    shipping_time = NOW(),
    driver_receive_time = NOW(),
    driver_id = {authenticated_driver_id},
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND driver_id IS NULL;  -- Prevent double-assignment
```

**Step 3**: Insert action record

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),  -- Action ID: 1973438237720702978
  {order_id},
  2,
  2,
  1,  -- Warehouse delivery
  1,  -- Action: Driver Pickup
  '{file_id}',  -- Comma-separated file IDs if multiple
  NOW()
);
```

**Step 4**: Link file to action via `biz_id`

```sql
UPDATE tigu_uploaded_files
SET biz_id = 1973438237720702978  -- Action ID
WHERE id = {file_id};
```

#### Affected Tables

**`tigu_order`**:

| Column | Before | After |
|--------|--------|-------|
| `driver_id` | `NULL` | `5` |
| `order_status` | `1` | `2` |
| `shipping_status` | `NULL` | `2` |
| `shipping_time` | `NULL` | `2025-01-15 10:30:00` |
| `driver_receive_time` | `NULL` | `2025-01-15 10:30:00` |

**`tigu_order_action`**: New record created
**`tigu_uploaded_files`**: New record(s) created and linked

#### Validation Rules
- Photo is **required** (cannot proceed without evidence)
- Order must not already be assigned to another driver
- Photo must be JPEG/PNG, max 4MB
- `shipping_type` must be 1 (warehouse delivery)

---

### Phase 3: Arrive at Warehouse (到达仓库)

**Driver Action**: Driver arrives at destination warehouse and uploads proof of delivery

#### API Call
```http
POST /api/v1/orders/{order_sn}/arrive-warehouse
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Delivered to Warehouse A, Section 3"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Arrival confirmed",
  "order": {
    "orderSn": "1973427465779625985",
    "shippingStatus": 3,
    "actionId": "1973445123456789012"
  }
}
```

#### Database Operations

**Step 1**: Insert photo to `tigu_uploaded_files` (same as Phase 2)

**Step 2**: Update order status

```sql
UPDATE tigu_order
SET shipping_status = 3,
    arrive_warehouse_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND driver_id = {authenticated_driver_id}
  AND shipping_status = 2;  -- Must be from "Driver Received"
```

**Step 3**: Insert action record

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {order_id},
  2,  -- order_status remains 2
  3,  -- shipping_status updated to 3
  1,
  2,  -- Action: Arrive Warehouse
  '{file_id}',
  NOW()
);
```

**Step 4**: Link file to action

```sql
UPDATE tigu_uploaded_files
SET biz_id = {action_id}
WHERE id = {file_id};
```

#### Affected Tables

**`tigu_order`**:

| Column | Before | After |
|--------|--------|-------|
| `shipping_status` | `2` | `3` |
| `arrive_warehouse_time` | `NULL` | `2025-01-15 12:00:00` |

---

### Phase 4: Warehouse Ships (仓库发货)

**Warehouse Action**: Warehouse staff confirms shipment to end user

#### API Call
```http
POST /api/v1/orders/{order_sn}/warehouse-ship
Content-Type: multipart/form-data
Authorization: Bearer {warehouse_staff_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Shipped via courier ABC-12345"
}
```

#### Database Operations

**Step 1**: Insert photo (same process)

**Step 2**: Update order

```sql
UPDATE tigu_order
SET shipping_status = 4,
    warehouse_shipping_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND shipping_status = 3;
```

**Step 3**: Insert action

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {order_id},
  2,
  4,
  1,
  3,  -- Action: Warehouse Ships
  '{file_id}',
  NOW()
);
```

#### Affected Tables

**`tigu_order`**:

| Column | Before | After |
|--------|--------|-------|
| `shipping_status` | `3` | `4` |
| `warehouse_shipping_time` | `NULL` | `2025-01-15 14:00:00` |

---

### Phase 5: Delivery Complete (完成)

**Final Delivery**: Goods delivered to end user

#### API Call
```http
POST /api/v1/orders/{order_sn}/complete
Content-Type: multipart/form-data
Authorization: Bearer {delivery_staff_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Delivered to recipient, signature obtained"
}
```

#### Database Operations

**Step 1**: Insert photo

**Step 2**: Update order

```sql
UPDATE tigu_order
SET shipping_status = 5,
    order_status = 3,  -- Completed
    finish_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND shipping_status = 4;
```

**Step 3**: Insert action

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {order_id},
  3,  -- Completed
  5,  -- Delivered
  1,
  4,  -- Action: Complete
  '{file_id}',
  NOW()
);
```

#### Affected Tables

**`tigu_order`**:

| Column | Before | After |
|--------|--------|-------|
| `shipping_status` | `4` | `5` |
| `order_status` | `2` | `3` |
| `finish_time` | `NULL` | `2025-01-15 16:00:00` |

---

## Direct-to-User Delivery Path

**Flow**: `shipping_type = 0` (Merchant → Driver → End User)

```
[Goods Ready] → [Driver Pickup] → [Delivered]
   status=1        status=4        status=5
  action=0        action=1        action=4
```

---

### Phase 1: Goods Ready

Same as warehouse path - merchant prepares goods.

---

### Phase 2: Driver Pickup (司机收货)

**Driver Action**: Driver picks up goods from merchant

#### API Call
```http
POST /api/v1/orders/{order_sn}/pickup
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Picked up from merchant store"
}
```

#### Database Operations

**Key Difference**: `shipping_status` is set to **4** (not 2) for direct delivery

**Step 1**: Insert photo to `tigu_uploaded_files`

**Step 2**: Update order

```sql
UPDATE tigu_order
SET order_status = 2,
    shipping_status = 4,  -- Direct to status 4
    shipping_time = NOW(),
    driver_receive_time = NOW(),
    driver_id = {authenticated_driver_id},
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id IS NULL;
```

**Step 3**: Insert action

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {order_id},
  2,
  4,  -- shipping_status = 4
  0,  -- shipping_type = 0 (Direct)
  1,  -- Action: Driver Pickup
  '{file_id}',
  NOW()
);
```

**Step 4**: Link file

```sql
UPDATE tigu_uploaded_files
SET biz_id = {action_id}
WHERE id = {file_id};
```

---

### Phase 3: Complete Delivery (完成)

**Driver Action**: Driver delivers directly to end user

#### API Call
```http
POST /api/v1/orders/{order_sn}/complete
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**Request Body**:
```json
{
  "photo": "base64_encoded_image_data",
  "notes": "Delivered to customer at doorstep"
}
```

#### Database Operations

**Step 1**: Insert photo

**Step 2**: Update order

```sql
UPDATE tigu_order
SET shipping_status = 5,
    order_status = 3,
    finish_time = NOW(),
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id = {authenticated_driver_id}
  AND shipping_status = 4;  -- Must be from status 4
```

**Step 3**: Insert action

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {order_id},
  3,
  5,
  0,  -- Direct delivery
  4,  -- Action: Complete
  '{file_id}',
  NOW()
);
```

---

## Database Schema Reference

### Primary Tables

#### `tigu_order`

Main order table with delivery tracking.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Auto | Order ID |
| `order_sn` | VARCHAR(64) | UNIQUE | - | Order serial number |
| `user_id` | BIGINT UNSIGNED | INDEX | - | Customer ID |
| `shop_id` | BIGINT UNSIGNED | INDEX | - | Merchant ID |
| `driver_id` | BIGINT UNSIGNED | INDEX | NULL | Assigned driver |
| `warehouse_id` | BIGINT | INDEX | - | Pickup warehouse |
| `shipping_type` | **TINYINT** | **INDEX** | - | **0=User, 1=Warehouse** |
| `shipping_status` | INT | INDEX | NULL | Delivery status (2,3,4,5) |
| `order_status` | INT | INDEX | - | Order lifecycle (0-5) |
| `receiver_name` | VARCHAR(64) | - | - | Recipient name |
| `receiver_phone` | VARCHAR(32) | - | - | Recipient phone |
| `receiver_address` | VARCHAR(256) | - | - | Delivery address |
| `shipping_time` | DATETIME | - | NULL | **When driver receives goods** |
| `driver_receive_time` | **DATETIME** | - | **NULL** | **Driver pickup timestamp** |
| `arrive_warehouse_time` | **DATETIME** | - | **NULL** | **Warehouse arrival time** |
| `warehouse_shipping_time` | **DATETIME** | - | **NULL** | **Warehouse ship time** |
| `finish_time` | DATETIME | - | NULL | Final delivery time |
| `create_time` | DATETIME | - | NOW() | Order creation |
| `update_time` | DATETIME | - | NOW() | Last update |

**New Indexes**:
- `INDEX idx_shipping_type (shipping_type)`
- `INDEX idx_shipping_status_type (shipping_status, shipping_type)`

---

#### `tigu_order_action`

**NEW TABLE**: Workflow audit trail for every status change.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Snowflake | Action ID (Snowflake) |
| `order_id` | BIGINT UNSIGNED | INDEX | - | FK to tigu_order |
| `order_status` | INT | INDEX | - | order_status at this step |
| `shipping_status` | INT | INDEX | - | shipping_status at this step |
| `shipping_type` | TINYINT | INDEX | - | 0=User, 1=Warehouse |
| `action_type` | **TINYINT** | **INDEX** | - | **Action type code (0-10)** |
| `logistics_voucher_file` | **VARCHAR(512)** | - | **NULL** | **Comma-separated file IDs** |
| `created_at` | DATETIME | - | NOW() | Action timestamp |
| `updated_at` | DATETIME | - | NOW() | Update timestamp |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX idx_order_id (order_id)`
- `INDEX idx_action_type (action_type)`
- `FOREIGN KEY (order_id) REFERENCES tigu_order(id) ON DELETE CASCADE`

**action_type Codes**:

| Code | Label | Description |
|------|-------|-------------|
| `0` | Goods Prepared | Merchant marks inventory ready |
| `1` | Driver Pickup | Driver receives goods |
| `2` | Arrive Warehouse | Driver delivers to warehouse |
| `3` | Warehouse Ships | Warehouse ships to end user |
| `4` | Complete | Final delivery to recipient |
| `5` | Refund Requested | User requests refund |
| `6` | Return Approved | Merchant approves return |
| `7` | Return Denied | Merchant denies return |
| `8` | Refund Approved | Merchant approves refund |
| `9` | Refund Denied | Merchant denies refund |
| `10` | Return Evidence | User uploads return proof |

---

#### `tigu_uploaded_files`

File storage with business entity linking.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Snowflake | File ID (Snowflake) |
| `file_name` | VARCHAR(255) | - | - | Original filename |
| `file_url` | VARCHAR(512) | - | - | Storage path/URL |
| `file_size` | INT UNSIGNED | - | - | File size in bytes |
| `file_type` | VARCHAR(50) | - | - | MIME type |
| `biz_id` | **BIGINT UNSIGNED** | **INDEX** | **NULL** | **Links to tigu_order_action.id** |
| `created_at` | DATETIME | - | NOW() | Upload timestamp |
| `updated_at` | DATETIME | - | NOW() | Update timestamp |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX idx_biz_id (biz_id)` - Links files to action records

**File Linking Logic**:
1. Upload file → Get `file_id`
2. Create action → Get `action_id`
3. Update file: `SET biz_id = action_id WHERE id = file_id`

---

#### `tigu_driver`

Driver master data.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Auto | Driver ID |
| `name` | VARCHAR(100) | - | - | Driver name |
| `phone` | VARCHAR(20) | UNIQUE | - | Phone (login) |
| `email` | VARCHAR(100) | - | NULL | Email |
| `license_number` | VARCHAR(50) | - | NULL | Driver's license |
| `vehicle_type` | VARCHAR(50) | - | NULL | Vehicle type |
| `vehicle_plate` | VARCHAR(20) | - | NULL | License plate |
| `status` | TINYINT | INDEX | 1 | 1=Active, 0=Inactive |
| `rating` | DECIMAL(3,2) | - | 0.00 | Rating (0-5) |
| `total_deliveries` | INT | - | 0 | Completed count |
| `created_at` | DATETIME | - | NOW() | Creation time |
| `updated_at` | DATETIME | - | NOW() | Update time |

---

### Relationship Diagram

```
┌─────────────────────┐
│  tigu_warehouse     │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────────────────────────────────┐
│              tigu_order                          │
│  ┌──────────────────────────────────────────┐  │
│  │ - id (PK)                                 │  │
│  │ - order_sn (UNIQUE)                       │  │
│  │ - driver_id (FK)                         │  │
│  │ - shipping_type (0=User, 1=Warehouse)    │  │
│  │ - shipping_status (2,3,4,5)              │  │
│  │ - driver_receive_time                    │  │
│  │ - arrive_warehouse_time                  │  │
│  │ - warehouse_shipping_time                │  │
│  └──────────────────────────┬───────────────┘  │
└───────────────────────────┬─┼──────────────────┘
                            │ │
                      ┌─────┘ └──────────┐
                      │ 1                │ N
                      │                  │
           ┌──────────▼───────┐   ┌─────▼──────────────────┐
           │   tigu_driver    │   │ tigu_order_action      │
           └──────────────────┘   │  ┌──────────────────┐  │
                                  │  │ - id (PK)        │  │
                                  │  │ - order_id (FK)  │──┼──┐
                                  │  │ - action_type    │  │  │ 1
                                  │  │ - logistics_...  │  │  │
                                  │  └────────┬─────────┘  │  │
                                  └───────────┼────────────┘  │
                                              │               │ N
                                              │               │
                                              │  ┌────────────▼─────────────┐
                                              │  │  tigu_uploaded_files     │
                                              │  │  ┌────────────────────┐  │
                                              │  │  │ - id (PK)          │  │
                                              │  │  │ - file_url         │  │
                                              └──┼──│ - biz_id (FK)      │  │
                                                 │  └────────────────────┘  │
                                                 └──────────────────────────┘
```

---

## API Endpoints Reference

### Driver Endpoints

| Method | Endpoint | Description | Auth | Workflow |
|--------|----------|-------------|------|----------|
| `GET` | `/api/v1/orders/available` | List unassigned orders | Required | Both |
| `GET` | `/api/v1/orders/assigned` | Driver's orders | Required | Both |
| `GET` | `/api/v1/orders/{order_sn}` | Order details | Required | Both |
| `POST` | `/api/v1/orders/{order_sn}/pickup` | Driver pickup | Required | Both |
| `POST` | `/api/v1/orders/{order_sn}/arrive-warehouse` | **Arrive warehouse** | **Required** | **Warehouse only** |
| `POST` | `/api/v1/orders/{order_sn}/warehouse-ship` | **Warehouse ships** | **Required** | **Warehouse only** |
| `POST` | `/api/v1/orders/{order_sn}/complete` | Complete delivery | Required | Both |

---

### Authentication

All endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

JWT payload:
```json
{
  "phone": "13800138000",
  "driver_id": 5,
  "exp": 1705392000
}
```

---

## Status Code Reference

### shipping_status (Delivery Status)

| Code | Label | Warehouse Path | Direct Path | Description |
|------|-------|----------------|-------------|-------------|
| `NULL` | Unassigned | ✓ | ✓ | Order not assigned |
| `2` | Driver Received | ✓ | ❌ | Driver picked up (warehouse) |
| `3` | Arrived Warehouse | ✓ | ❌ | Delivered to warehouse |
| `4` | Warehouse Shipped | ✓ | ✓ | Shipped (warehouse) OR Picked up (direct) |
| `5` | Delivered | ✓ | ✓ | Final delivery complete |

### shipping_type (Delivery Type)

| Code | Label | Description |
|------|-------|-------------|
| `0` | Direct to User | Driver delivers directly to end user |
| `1` | Via Warehouse | Driver delivers to warehouse first |

### order_status (Order Lifecycle)

| Code | Label | Description |
|------|-------|-------------|
| `0` | Pending Payment | Awaiting payment |
| `1` | Pending Shipment | Paid, ready for pickup |
| `2` | Pending Receipt | In transit |
| `3` | Completed | Order fulfilled |
| `4` | Cancelled | Order cancelled |
| `5` | After-Sales | Return/refund in progress |

---

## Error Handling

### Common Errors

#### 1. Invalid shipping_type Transition

```json
{
  "error": "INVALID_SHIPPING_TYPE",
  "message": "Cannot call arrive-warehouse for direct-to-user delivery (shipping_type=0)"
}
```

#### 2. Missing Photo Evidence

```json
{
  "error": "PHOTO_REQUIRED",
  "message": "Photo upload is mandatory for this action"
}
```

#### 3. Invalid Status Transition

```json
{
  "error": "INVALID_STATUS_TRANSITION",
  "message": "Cannot transition from shipping_status=5 to shipping_status=3"
}
```

#### 4. File Upload Failed

```json
{
  "error": "FILE_UPLOAD_FAILED",
  "message": "Failed to save file to tigu_uploaded_files table"
}
```

---

## Best Practices

### For Drivers

1. **Always upload clear photos** - Required for audit trail
2. **Check shipping_type** - Determines which workflow to follow
3. **Follow status sequence** - Cannot skip workflow steps
4. **Add detailed notes** - Helps with issue resolution
5. **Verify recipient identity** - Before final delivery

### For Administrators

1. **Monitor action logs** - `tigu_order_action` provides complete audit trail
2. **Validate photo evidence** - Check `tigu_uploaded_files` linked via `biz_id`
3. **Track warehouse vs. direct** - Analyze performance by `shipping_type`
4. **Review incomplete workflows** - Identify orders stuck at intermediate states
5. **Enforce photo requirements** - Cannot proceed without evidence

---

## Appendix: Transaction Examples

### Complete Warehouse Delivery Transaction

```sql
START TRANSACTION;

-- 1. Upload photo
INSERT INTO tigu_uploaded_files (id, file_name, file_url, file_size, file_type, biz_id, created_at)
VALUES (SNOWFLAKE_NEXT_ID(), 'pickup.jpg', '/uploads/pickup.jpg', 123456, 'image/jpeg', NULL, NOW());

SET @file_id = LAST_INSERT_ID();

-- 2. Update order
UPDATE tigu_order
SET shipping_status = 2,
    order_status = 2,
    shipping_time = NOW(),
    driver_receive_time = NOW(),
    driver_id = 5
WHERE order_sn = '1973427465779625985' AND driver_id IS NULL;

-- 3. Insert action
INSERT INTO tigu_order_action (id, order_id, order_status, shipping_status, shipping_type, action_type, logistics_voucher_file, created_at)
VALUES (SNOWFLAKE_NEXT_ID(), 5001, 2, 2, 1, 1, @file_id, NOW());

SET @action_id = LAST_INSERT_ID();

-- 4. Link file to action
UPDATE tigu_uploaded_files SET biz_id = @action_id WHERE id = @file_id;

COMMIT;
```

---

# 中文版本

## 概述

本文档从司机角度描述完整的配送工作流程，包括每个阶段的所有数据库操作。系统支持由 `shipping_type` 决定的**两种配送路径**:

- **仓库配送** (`shipping_type = 1`): 商家 → 司机 → 仓库 → 最终配送
- **直送用户** (`shipping_type = 0`): 商家 → 司机 → 用户

### 关键特性

- **审计追踪**: 每个工作流步骤都记录在 `tigu_order_action` 表中
- **照片凭证**: 所有转换都需要上传照片到 `tigu_uploaded_files`
- **双路径工作流**: 仓库配送 vs. 直送用户
- **雪花ID**: 分布式唯一ID生成，用于操作记录

---

## 配送类型路由

`tigu_order` 表中的 `shipping_type` 字段决定司机遵循的工作流路径:

```
┌─────────────────────────────────────────────────────────────────┐
│                       配送路由                                     │
└─────────────────────────────────────────────────────────────────┘

            [订单就绪 - 商家已备货]
                            ↓
                   ┌────────┴────────┐
                   │  shipping_type?  │
                   └────────┬────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
         = 1                              = 0
       (仓库)                            (直送)
            │                               │
            ↓                               ↓
┌───────────────────────┐      ┌───────────────────────┐
│  仓库路径              │      │  直送路径              │
│                       │      │                       │
│  1. 司机收货           │      │  1. 司机收货          │
│  2. 到达仓库           │      │  2. 完成配送          │
│  3. 仓库发货           │      │                       │
│  4. 完成配送           │      │                       │
└───────────────────────┘      └───────────────────────┘
```

### 状态代码映射

| shipping_status | 标签 | 仓库路径 | 直送用户路径 |
|-----------------|------|---------|------------|
| `NULL` | 未分配 | ✓ 可接单 | ✓ 可接单 |
| `2` | 司机已收货 | ✓ 司机取货 | ❌ 不适用 |
| `3` | 到达仓库 | ✓ 送达仓库 | ❌ 不适用 |
| `4` | 仓库已发货 | ✓ 仓库发货给终端用户 | ✓ 司机取货 |
| `5` | 已送达 | ✓ 最终配送完成 | ✓ 配送完成 |

---

## 仓库配送路径

**流程**: `shipping_type = 1` (商家 → 司机 → 仓库 → 终端用户)

```
[备货完成] → [司机收货] → [到达仓库] → [仓库发货] → [已送达]
   状态=1      状态=2       状态=3        状态=4      状态=5
  操作=0      操作=1       操作=2        操作=3      操作=4
```

---

### 阶段一: 备货完成 (商家准备订单)

**触发**: 后端商家点击"备货完成"按钮

#### 数据库状态

**表**: `tigu_order`

| 字段 | 值 | 说明 |
|------|-----|------|
| `driver_id` | `NULL` | 未分配司机 |
| `shipping_status` | `NULL` | 等待司机分配 |
| `shipping_type` | `1` | 仓库配送 |
| `order_status` | `1` | 待发货 |
| `shipping_time` | `NULL` | 尚未发货 |
| `driver_receive_time` | `NULL` | 尚未取货 |

---

### 阶段二: 司机收货

**司机操作**: 司机从商家/仓库取货并确认收货

#### API 调用
```http
POST /api/v1/orders/{order_sn}/pickup
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**请求体**:
```json
{
  "photo": "base64编码的图片数据",
  "notes": "从商家仓库取货5箱"
}
```

**响应**:
```json
{
  "success": true,
  "message": "订单接单成功",
  "order": {
    "orderSn": "1973427465779625985",
    "shippingStatus": 2,
    "orderStatus": 2,
    "actionId": "1973438237720702978"
  }
}
```

#### 数据库操作

**步骤1**: 插入照片到 `tigu_uploaded_files`

```sql
INSERT INTO tigu_uploaded_files (
  id,
  file_name,
  file_url,
  file_size,
  file_type,
  biz_id,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  'pickup_1973427465779625985_1705315200.jpeg',
  '/uploads/delivery/pickup_1973427465779625985_1705315200.jpeg',
  1245678,
  'image/jpeg',
  NULL,
  NOW()
);
```

**步骤2**: 更新订单状态

```sql
UPDATE tigu_order
SET order_status = 2,
    shipping_status = 2,
    shipping_time = NOW(),
    driver_receive_time = NOW(),
    driver_id = {已认证的司机ID},
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND driver_id IS NULL;
```

**步骤3**: 插入操作记录

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {订单ID},
  2,
  2,
  1,
  1,  -- 操作: 司机收货
  '{文件ID}',
  NOW()
);
```

**步骤4**: 通过 `biz_id` 关联文件到操作

```sql
UPDATE tigu_uploaded_files
SET biz_id = 1973438237720702978
WHERE id = {文件ID};
```

---

### 阶段三: 到达仓库

**司机操作**: 司机到达目标仓库并上传送达凭证

#### API 调用
```http
POST /api/v1/orders/{order_sn}/arrive-warehouse
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**请求体**:
```json
{
  "photo": "base64编码的图片数据",
  "notes": "送达仓库A，3号区"
}
```

#### 数据库操作

**步骤1**: 插入照片 (同阶段二)

**步骤2**: 更新订单状态

```sql
UPDATE tigu_order
SET shipping_status = 3,
    arrive_warehouse_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND driver_id = {已认证的司机ID}
  AND shipping_status = 2;
```

**步骤3**: 插入操作记录

```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {订单ID},
  2,
  3,
  1,
  2,  -- 操作: 到达仓库
  '{文件ID}',
  NOW()
);
```

---

### 阶段四: 仓库发货

**仓库操作**: 仓库工作人员确认发货给终端用户

#### 数据库操作

**更新订单**:
```sql
UPDATE tigu_order
SET shipping_status = 4,
    warehouse_shipping_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND shipping_status = 3;
```

**插入操作**:
```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {订单ID},
  2,
  4,
  1,
  3,  -- 操作: 仓库发货
  '{文件ID}',
  NOW()
);
```

---

### 阶段五: 完成配送

**最终配送**: 商品送达终端用户

#### 数据库操作

**更新订单**:
```sql
UPDATE tigu_order
SET shipping_status = 5,
    order_status = 3,
    finish_time = NOW(),
    update_time = NOW()
WHERE order_sn = '1973427465779625985'
  AND shipping_status = 4;
```

**插入操作**:
```sql
INSERT INTO tigu_order_action (
  id,
  order_id,
  order_status,
  shipping_status,
  shipping_type,
  action_type,
  logistics_voucher_file,
  created_at
) VALUES (
  SNOWFLAKE_NEXT_ID(),
  {订单ID},
  3,
  5,
  1,
  4,  -- 操作: 完成
  '{文件ID}',
  NOW()
);
```

---

## 直送用户路径

**流程**: `shipping_type = 0` (商家 → 司机 → 终端用户)

```
[备货完成] → [司机收货] → [已送达]
   状态=1      状态=4      状态=5
  操作=0      操作=1      操作=4
```

### 阶段一: 备货完成

与仓库路径相同

### 阶段二: 司机收货

**关键区别**: `shipping_status` 设置为 **4** (而非2)

```sql
UPDATE tigu_order
SET order_status = 2,
    shipping_status = 4,  -- 直接到状态4
    shipping_time = NOW(),
    driver_receive_time = NOW(),
    driver_id = {已认证的司机ID}
WHERE order_sn = '{订单编号}'
  AND driver_id IS NULL;
```

### 阶段三: 完成配送

司机直接送达终端用户

```sql
UPDATE tigu_order
SET shipping_status = 5,
    order_status = 3,
    finish_time = NOW()
WHERE order_sn = '{订单编号}'
  AND shipping_status = 4;
```

---

## 数据库架构参考

### 主要表

#### `tigu_order`

订单主表，包含配送追踪。

**新增字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `shipping_type` | **TINYINT** | **0=用户，1=仓库** |
| `driver_receive_time` | **DATETIME** | **司机取货时间** |
| `arrive_warehouse_time` | **DATETIME** | **到达仓库时间** |
| `warehouse_shipping_time` | **DATETIME** | **仓库发货时间** |

---

#### `tigu_order_action`

**新表**: 工作流审计追踪表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT UNSIGNED | 操作ID (雪花ID) |
| `order_id` | BIGINT UNSIGNED | 外键至 tigu_order |
| `order_status` | INT | 此步骤的 order_status |
| `shipping_status` | INT | 此步骤的 shipping_status |
| `shipping_type` | TINYINT | 0=用户，1=仓库 |
| `action_type` | **TINYINT** | **操作类型代码 (0-10)** |
| `logistics_voucher_file` | **VARCHAR(512)** | **逗号分隔的文件ID** |
| `created_at` | DATETIME | 操作时间戳 |

**action_type 代码**:

| 代码 | 标签 | 说明 |
|------|------|------|
| `0` | 备货 | 商家标记库存就绪 |
| `1` | 司机收货 | 司机收取货物 |
| `2` | 到达仓库 | 司机送达仓库 |
| `3` | 仓库发货 | 仓库发货给终端用户 |
| `4` | 完成 | 最终送达收件人 |
| `5` | 申请退款 | 用户申请退款 |
| `6` | 允许退货 | 商家允许退货 |
| `7` | 拒绝退货 | 商家拒绝退货 |
| `8` | 同意退款 | 商家同意退款 |
| `9` | 拒绝退款 | 商家拒绝退款 |
| `10` | 退货凭证 | 用户上传退货证明 |

---

#### `tigu_uploaded_files`

文件存储表，通过业务实体关联

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT UNSIGNED | 文件ID (雪花ID) |
| `file_name` | VARCHAR(255) | 原始文件名 |
| `file_url` | VARCHAR(512) | 存储路径/URL |
| `file_size` | INT UNSIGNED | 文件大小(字节) |
| `file_type` | VARCHAR(50) | MIME类型 |
| `biz_id` | **BIGINT UNSIGNED** | **关联到 tigu_order_action.id** |
| `created_at` | DATETIME | 上传时间戳 |

**文件关联逻辑**:
1. 上传文件 → 获取 `file_id`
2. 创建操作 → 获取 `action_id`
3. 更新文件: `SET biz_id = action_id WHERE id = file_id`

---

## API接口参考

### 司机端点

| 方法 | 端点 | 说明 | 认证 | 工作流 |
|------|------|------|------|--------|
| `GET` | `/api/v1/orders/available` | 列出未分配订单 | 必需 | 两者 |
| `GET` | `/api/v1/orders/assigned` | 司机的订单 | 必需 | 两者 |
| `POST` | `/api/v1/orders/{order_sn}/pickup` | 司机取货 | 必需 | 两者 |
| `POST` | `/api/v1/orders/{order_sn}/arrive-warehouse` | **到达仓库** | **必需** | **仅仓库** |
| `POST` | `/api/v1/orders/{order_sn}/warehouse-ship` | **仓库发货** | **必需** | **仅仓库** |
| `POST` | `/api/v1/orders/{order_sn}/complete` | 完成配送 | 必需 | 两者 |

---

## 最佳实践

### 司机

1. **始终上传清晰照片** - 审计追踪必需
2. **检查 shipping_type** - 决定遵循哪个工作流
3. **遵循状态顺序** - 不能跳过工作流步骤
4. **添加详细备注** - 帮助问题解决
5. **验证收件人身份** - 最终配送前

### 管理员

1. **监控操作日志** - `tigu_order_action` 提供完整审计追踪
2. **验证照片凭证** - 检查通过 `biz_id` 关联的 `tigu_uploaded_files`
3. **追踪仓库 vs. 直送** - 按 `shipping_type` 分析性能
4. **审查未完成工作流** - 识别卡在中间状态的订单
5. **强制照片要求** - 无凭证无法继续

---

## 文档版本

- **版本**: 2.0
- **最后更新**: 2025-01-15
- **作者**: 技术团队
- **系统**: Tigub2b 配送管理系统
- **更新说明**: 根据实际后端实现更新，包含 shipping_type、tigu_order_action、tigu_uploaded_files 集成

---

**备注**: 本文档准确反映 `/home/mli/tigub2b/tigub2b_delivery/` 代码库的实际后端实现，基于 `system_integration.docx` 的规范。
