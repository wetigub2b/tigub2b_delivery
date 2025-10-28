# Driver Delivery Workflow Guide
# 司机配送流程指南

---

## Table of Contents | 目录

- [English Version](#english-version)
  - [Overview](#overview)
  - [Phase 1: Pickup Available](#phase-1-pickup-available)
  - [Phase 2: Picked Up](#phase-2-picked-up)
  - [Phase 3: In Transit](#phase-3-in-transit)
  - [Phase 4: Complete](#phase-4-complete)
  - [Database Schema Reference](#database-schema-reference)
  - [API Endpoints Reference](#api-endpoints-reference)
- [中文版本](#中文版本)
  - [概述](#概述)
  - [阶段一：可接单](#阶段一可接单)
  - [阶段二：已接单](#阶段二已接单)
  - [阶段三：配送中](#阶段三配送中)
  - [阶段四：已完成](#阶段四已完成)
  - [数据库架构参考](#数据库架构参考)
  - [API接口参考](#api接口参考)

---

# English Version

## Overview

This document describes the complete delivery workflow from a driver's perspective, including all database operations that occur at each phase.

### Delivery Status Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DELIVERY LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────┘

    [Pickup Available]
           ↓
    Driver accepts order
           ↓
      [Picked Up]
           ↓
    Driver starts delivery
           ↓
      [In Transit]
           ↓
    Driver arrives & uploads proof
           ↓
       [Complete]
```

### Status Codes

| Status | shipping_status | order_status | Description |
|--------|----------------|--------------|-------------|
| Pickup Available | `NULL` | 1 | Unassigned order waiting for driver |
| Picked Up | `0` | 1 or 2 | Driver accepted, ready to deliver |
| In Transit | `1` or `2` | 2 | Order is being delivered |
| Complete | `3` | 3 | Delivery completed with proof |

---

## Phase 1: Pickup Available

### Driver Action
- Driver views list of available (unassigned) orders
- Driver selects an order to pickup
- Driver confirms acceptance of the order

### API Call
```http
GET /api/v1/orders/available
```

**Response Example:**
```json
{
  "items": [
    {
      "orderSn": "ORD-20250101-00001",
      "recipientName": "John Doe",
      "recipientPhone": "555-1234",
      "deliveryAddress": "123 Main St, District A",
      "shippingStatus": null,
      "itemCount": 3,
      "totalAmount": 199.99
    }
  ],
  "total": 15
}
```

### Database Query
```sql
SELECT o.*, w.name as warehouse_name
FROM tigu_order o
LEFT JOIN tigu_warehouse w ON o.warehouse_id = w.id
WHERE o.driver_id IS NULL
  AND o.shipping_status IS NULL
  AND o.order_status IN (1, 2)
ORDER BY o.create_time ASC;
```

### Table State

**Table:** `tigu_order`

| Column | Value | Note |
|--------|-------|------|
| `driver_id` | `NULL` | No driver assigned yet |
| `shipping_status` | `NULL` or `0` | Unassigned |
| `order_status` | `1` (Pending Shipment) | Payment completed, ready to ship |
| `shipping_time` | `NULL` | Not shipped yet |
| `finish_time` | `NULL` | Not completed |

### UI Display
- List of available orders with recipient details
- Distance from warehouse to delivery location
- Estimated delivery time
- Order value and item count
- "Accept Order" button for each order

---

## Phase 2: Picked Up

### Driver Action
- Driver clicks "Accept Order" or "Pickup" button
- System assigns the order to the driver
- Driver prepares to collect items from warehouse

### API Call
```http
POST /api/v1/orders/{order_sn}/pickup
```

**Request Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "message": "Order picked up successfully",
  "order": {
    "orderSn": "ORD-20250101-00001",
    "driverId": 5,
    "shippingStatus": 0
  }
}
```

### Database Operations

#### UPDATE Query
```sql
UPDATE tigu_order
SET driver_id = {authenticated_driver_id},
    shipping_status = 0,
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id IS NULL;  -- Ensure not already assigned
```

#### Affected Columns

**Table:** `tigu_order`

| Column | Before | After | Description |
|--------|--------|-------|-------------|
| `driver_id` | `NULL` | `5` | Driver ID from JWT token |
| `shipping_status` | `NULL` | `0` | Status: "Not Shipped" (pending pickup) |
| `update_time` | (old timestamp) | `2025-01-15 10:30:00` | Current timestamp |
| `order_status` | `1` | `1` or `2` | May update to "Pending Receipt" |

### Business Logic
1. Verify order exists and is unassigned (`driver_id IS NULL`)
2. Extract driver ID from JWT authentication token
3. Atomically update `driver_id` and `shipping_status`
4. Return updated order details to driver app
5. Remove order from "Available Orders" list
6. Add order to driver's "My Orders" list

### UI Update
- Order moves from "Available" tab to "Assigned" tab
- Order shows status: "Picked Up" or "Ready for Delivery"
- Driver can now start delivery

---

## Phase 3: In Transit

### Driver Action
- Driver collects items from warehouse
- Driver clicks "Start Delivery" button
- Driver navigates to delivery address
- System tracks delivery progress (optional GPS tracking)

### API Call
```http
POST /api/v1/orders/{order_sn}/status
Content-Type: application/json

{
  "shippingStatus": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order status updated successfully",
  "order": {
    "orderSn": "ORD-20250101-00001",
    "shippingStatus": 1
  }
}
```

### Database Operations

#### UPDATE Query
```sql
UPDATE tigu_order
SET shipping_status = 1,
    shipping_time = NOW(),
    order_status = 2,
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id = {authenticated_driver_id}
  AND shipping_status = 0;  -- Only allow transition from "Picked Up"
```

#### Affected Columns

**Table:** `tigu_order`

| Column | Before | After | Description |
|--------|--------|-------|-------------|
| `shipping_status` | `0` | `1` | Status: "Shipped" (in transit) |
| `shipping_time` | `NULL` | `2025-01-15 11:00:00` | Timestamp when delivery started |
| `order_status` | `1` or `2` | `2` | "Pending Receipt" |
| `update_time` | (previous) | `2025-01-15 11:00:00` | Current timestamp |

### Optional: Partial Delivery

For orders with multiple drop-off points:

```http
POST /api/v1/orders/{order_sn}/status
Content-Type: application/json

{
  "shippingStatus": 2
}
```

**Database Update:**
```sql
UPDATE tigu_order
SET shipping_status = 2,
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id = {authenticated_driver_id};
```

| shipping_status | Meaning |
|-----------------|---------|
| `1` | Fully in transit (single delivery point) |
| `2` | Partially shipped (multiple delivery points, some completed) |

### UI Update
- Order status shows "In Transit" or "Out for Delivery"
- Navigation/map shows route to delivery address
- Estimated arrival time displayed
- Option to call recipient
- Button to "Mark as Delivered" becomes available

---

## Phase 4: Complete

### Driver Action
- Driver arrives at delivery location
- Driver hands over items to recipient
- Driver takes photo of delivered items or signed receipt
- Driver adds optional delivery notes
- Driver submits delivery proof

### API Call
```http
POST /api/v1/orders/{order_sn}/proof
Content-Type: application/json

{
  "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "notes": "Delivered to recipient at front door"
}
```

**Request Body:**
- `photo`: Base64-encoded image (JPEG/PNG, max 4MB)
- `notes`: Optional text description (max 500 chars)

**Response:**
```json
{
  "success": true,
  "message": "Delivery proof uploaded successfully",
  "proof": {
    "id": 123,
    "orderSn": "ORD-20250101-00001",
    "photoUrl": "/deliveries/photos/ORD-20250101-00001_1705315200.jpeg",
    "notes": "Delivered to recipient at front door",
    "createdAt": "2025-01-15T11:30:00Z"
  }
}
```

### Database Operations

#### Step 1: Save Photo to Filesystem

**Operation:**
1. Decode base64 image data
2. Validate file size (≤ 4MB) and MIME type (JPEG/PNG)
3. Generate filename: `{order_sn}_{timestamp}.{extension}`
4. Save to: `/var/www/deliveries/photos/`
5. Generate URL path: `/deliveries/photos/{filename}`

**Example:**
```
File: /var/www/deliveries/photos/ORD-20250101-00001_1705315200.jpeg
URL:  https://api.wetigu.com/deliveries/photos/ORD-20250101-00001_1705315200.jpeg
```

#### Step 2: Insert Delivery Proof Record

```sql
INSERT INTO tigu_delivery_proof (
  order_id,
  order_sn,
  driver_id,
  photo_url,
  notes,
  file_size,
  mime_type,
  created_at,
  updated_at
) VALUES (
  {order_id},
  'ORD-20250101-00001',
  {driver_id},
  '/deliveries/photos/ORD-20250101-00001_1705315200.jpeg',
  'Delivered to recipient at front door',
  1245678,
  'image/jpeg',
  NOW(),
  NOW()
);
```

**Table:** `tigu_delivery_proof`

| Column | Value | Description |
|--------|-------|-------------|
| `id` | `123` | Auto-increment primary key |
| `order_id` | `5001` | Foreign key to tigu_order |
| `order_sn` | `ORD-20250101-00001` | Order serial number |
| `driver_id` | `5` | Foreign key to tigu_driver |
| `photo_url` | `/deliveries/photos/ORD-...jpeg` | Relative URL to photo |
| `notes` | `Delivered to recipient...` | Driver's notes |
| `file_size` | `1245678` | File size in bytes (1.2MB) |
| `mime_type` | `image/jpeg` | Image MIME type |
| `created_at` | `2025-01-15 11:30:00` | Creation timestamp |
| `updated_at` | `2025-01-15 11:30:00` | Update timestamp |

#### Step 3: Update Order Status to Delivered

```sql
UPDATE tigu_order
SET shipping_status = 3,
    order_status = 3,
    finish_time = NOW(),
    update_time = NOW()
WHERE order_sn = '{order_sn}'
  AND driver_id = {authenticated_driver_id}
  AND shipping_status IN (1, 2);  -- Only allow from In Transit
```

**Table:** `tigu_order`

| Column | Before | After | Description |
|--------|--------|-------|-------------|
| `shipping_status` | `1` or `2` | `3` | Status: "Delivered" |
| `order_status` | `2` | `3` | Status: "Completed" |
| `finish_time` | `NULL` | `2025-01-15 11:30:00` | Delivery completion time |
| `update_time` | (previous) | `2025-01-15 11:30:00` | Current timestamp |

#### Step 4: Update Driver Statistics (Optional)

```sql
UPDATE tigu_driver
SET total_deliveries = total_deliveries + 1,
    updated_at = NOW()
WHERE id = {driver_id};
```

**Table:** `tigu_driver`

| Column | Before | After | Description |
|--------|--------|-------|-------------|
| `total_deliveries` | `127` | `128` | Increment completed deliveries |
| `updated_at` | (previous) | `2025-01-15 11:30:00` | Current timestamp |

### Transaction Flow

The delivery proof upload is wrapped in a database transaction:

```python
async with session.begin():
    # 1. Verify order ownership and status
    order = await fetch_order(session, order_sn, driver_id)

    # 2. Save photo to filesystem
    photo_url = save_photo(image_bytes, order_sn, mime_type)

    # 3. Insert delivery_proof record
    proof = DeliveryProof(...)
    session.add(proof)

    # 4. Update order status to delivered
    order.shipping_status = 3
    order.order_status = 3
    order.finish_time = datetime.now()

    # 5. Update driver statistics
    driver.total_deliveries += 1

    await session.commit()
```

### UI Update
- Order moves to "Completed" tab
- Shows delivery timestamp and photo
- Displays "Delivered" badge with green checkmark
- Driver can view delivery details but cannot modify
- Completion confirmation message shown

### Validation Rules
- Only the assigned driver can upload proof
- Photo is required (cannot complete without photo)
- Order must be in "In Transit" status (shipping_status = 1 or 2)
- Photo must be JPEG or PNG format
- Photo size must be ≤ 4MB
- Base64 encoding must be valid

---

## Database Schema Reference

### Primary Tables

#### `tigu_order`
Main order table tracking delivery lifecycle.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Auto | Order ID |
| `order_sn` | VARCHAR(64) | UNIQUE | - | Order serial number |
| `user_id` | BIGINT UNSIGNED | INDEX | - | Customer ID |
| `shop_id` | BIGINT UNSIGNED | INDEX | - | Shop/Merchant ID |
| `driver_id` | BIGINT UNSIGNED | INDEX | NULL | Assigned driver (FK to tigu_driver) |
| `warehouse_id` | BIGINT | INDEX | - | Pickup location (FK to tigu_warehouse) |
| `shipping_status` | INT | INDEX | NULL | Delivery status (0-3) |
| `order_status` | INT | INDEX | - | Order lifecycle status (0-5) |
| `receiver_name` | VARCHAR(64) | - | - | Recipient name |
| `receiver_phone` | VARCHAR(32) | - | - | Recipient phone |
| `receiver_address` | VARCHAR(256) | - | - | Full delivery address |
| `receiver_province` | VARCHAR(50) | - | - | Province/State |
| `receiver_city` | VARCHAR(50) | - | - | City |
| `receiver_district` | VARCHAR(50) | - | - | District/County |
| `shipping_time` | DATETIME | - | NULL | When delivery started |
| `finish_time` | DATETIME | - | NULL | When delivery completed |
| `create_time` | DATETIME | - | NOW() | Order creation time |
| `update_time` | DATETIME | - | NOW() | Last update time |

**Indexes:**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_order_sn (order_sn)`
- `INDEX idx_driver_id (driver_id)`
- `INDEX idx_shipping_status (shipping_status)`
- `INDEX idx_user_id (user_id)`
- `INDEX idx_create_time (create_time)`

---

#### `tigu_delivery_proof`
Stores delivery proof photos and notes.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Auto | Proof record ID |
| `order_id` | BIGINT UNSIGNED | INDEX | - | FK to tigu_order (CASCADE) |
| `order_sn` | VARCHAR(64) | INDEX | - | Order serial number |
| `driver_id` | BIGINT UNSIGNED | INDEX | - | FK to tigu_driver (RESTRICT) |
| `photo_url` | VARCHAR(512) | - | - | URL path to photo |
| `notes` | TEXT | - | NULL | Delivery notes |
| `file_size` | INT UNSIGNED | - | - | Photo size in bytes |
| `mime_type` | VARCHAR(50) | - | - | Image MIME type |
| `created_at` | DATETIME | - | NOW() | Upload timestamp |
| `updated_at` | DATETIME | - | NOW() | Update timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `INDEX idx_order_sn (order_sn)`
- `INDEX idx_driver_id (driver_id)`
- `FOREIGN KEY (order_id) REFERENCES tigu_order(id) ON DELETE CASCADE`
- `FOREIGN KEY (driver_id) REFERENCES tigu_driver(id) ON DELETE RESTRICT`

---

#### `tigu_driver`
Driver master data.

| Column | Type | Index | Default | Description |
|--------|------|-------|---------|-------------|
| `id` | BIGINT UNSIGNED | PRIMARY | Auto | Driver ID |
| `name` | VARCHAR(100) | - | - | Driver name |
| `phone` | VARCHAR(20) | UNIQUE | - | Phone number (login) |
| `email` | VARCHAR(100) | - | NULL | Email address |
| `license_number` | VARCHAR(50) | - | NULL | Driver's license |
| `vehicle_type` | VARCHAR(50) | - | NULL | Vehicle type |
| `vehicle_plate` | VARCHAR(20) | - | NULL | License plate |
| `status` | TINYINT | INDEX | 1 | 1=Active, 0=Inactive |
| `rating` | DECIMAL(3,2) | - | 0.00 | Driver rating (0-5) |
| `total_deliveries` | INT | - | 0 | Completed deliveries |
| `created_at` | DATETIME | - | NOW() | Creation timestamp |
| `updated_at` | DATETIME | - | NOW() | Update timestamp |

**Indexes:**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_phone (phone)`
- `INDEX idx_status (status)`

---

### Relationship Diagram

```
┌─────────────────────┐
│  tigu_warehouse     │
│  (Pickup Location)  │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────────────────────────────────┐
│              tigu_order                          │
│  ┌──────────────────────────────────────────┐  │
│  │ - id (PK)                                 │  │
│  │ - order_sn (UNIQUE)                       │  │
│  │ - driver_id (FK) ───────┐                │  │
│  │ - warehouse_id (FK)      │                │  │
│  │ - shipping_status (0-3)  │                │  │
│  │ - order_status (0-5)     │                │  │
│  │ - receiver_* (address)   │                │  │
│  │ - shipping_time          │                │  │
│  │ - finish_time            │                │  │
│  └──────────────────────────┼────────────────┘  │
└───────────────────────────┬─┼───────────────────┘
                            │ │
                      ┌─────┘ └──────────┐
                      │ 1                │ N
                      │                  │
           ┌──────────▼───────┐   ┌─────▼──────────────┐
           │   tigu_driver    │   │ tigu_order_item    │
           │  ┌───────────┐   │   │ (Order Items)      │
           │  │ - id (PK) │   │   └────────────────────┘
           │  │ - phone   │◄──┼───┐
           │  │ - status  │   │   │ 1
           │  └───────────┘   │   │
           └──────────────────┘   │ N
                                  │
                    ┌─────────────▼──────────────┐
                    │  tigu_delivery_proof       │
                    │  ┌─────────────────────┐   │
                    │  │ - id (PK)           │   │
                    │  │ - order_id (FK)     │   │
                    │  │ - driver_id (FK)    │   │
                    │  │ - photo_url         │   │
                    │  │ - notes             │   │
                    │  └─────────────────────┘   │
                    └────────────────────────────┘
```

---

## API Endpoints Reference

### Driver Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/orders/available` | List unassigned orders | Required |
| `GET` | `/api/v1/orders/assigned` | List driver's assigned orders | Required |
| `GET` | `/api/v1/orders/{order_sn}` | Get order details | Required |
| `POST` | `/api/v1/orders/{order_sn}/pickup` | Accept/pickup order | Required |
| `POST` | `/api/v1/orders/{order_sn}/status` | Update shipping status | Required |
| `POST` | `/api/v1/orders/{order_sn}/proof` | Upload delivery proof | Required |
| `POST` | `/api/v1/routes/optimize` | Generate optimized route | Required |

### Authentication

All driver endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

JWT token contains:
- `phone`: Driver's phone number (unique identifier)
- `exp`: Token expiration timestamp

---

## Status Code Reference

### shipping_status (Delivery Status)

| Code | Label | Description | Next Action |
|------|-------|-------------|-------------|
| `NULL` | Unassigned | Order not assigned to driver | Driver pickup |
| `0` | Not Shipped | Driver accepted, preparing | Start delivery |
| `1` | Shipped | In transit to delivery location | Complete delivery |
| `2` | Partially Shipped | Partial delivery (multi-drop) | Complete remaining |
| `3` | Delivered | Delivery completed | None (final state) |

### order_status (Order Lifecycle)

| Code | Label | Description |
|------|-------|-------------|
| `0` | Pending Payment | Awaiting customer payment |
| `1` | Pending Shipment | Paid, ready for driver pickup |
| `2` | Pending Receipt | In transit, awaiting delivery |
| `3` | Completed | Order fulfilled |
| `4` | Cancelled | Order cancelled |
| `5` | After-Sales | After-sales service requested |

### driver.status (Driver Status)

| Code | Label | Description |
|------|-------|-------------|
| `0` | Inactive | Driver account disabled |
| `1` | Active | Driver available for assignments |

---

## Error Handling

### Common Error Scenarios

#### 1. Order Already Assigned
```json
{
  "error": "ORDER_ALREADY_ASSIGNED",
  "message": "This order has already been assigned to another driver"
}
```

**Cause:** Another driver picked up the order first
**Resolution:** Refresh available orders list

---

#### 2. Invalid Order Status Transition
```json
{
  "error": "INVALID_STATUS_TRANSITION",
  "message": "Cannot update status from 3 to 1"
}
```

**Cause:** Attempting to change completed order back to in-transit
**Resolution:** Status transitions must follow valid sequence

---

#### 3. Photo Upload Failed
```json
{
  "error": "FILE_TOO_LARGE",
  "message": "Photo size exceeds 4MB limit"
}
```

**Cause:** Image file too large
**Resolution:** Compress image before upload

---

#### 4. Unauthorized Access
```json
{
  "error": "UNAUTHORIZED",
  "message": "This order is not assigned to you"
}
```

**Cause:** Driver trying to update another driver's order
**Resolution:** Only access your assigned orders

---

## Best Practices

### For Drivers
1. **Always take clear photos** - Ensure delivery proof is visible and well-lit
2. **Add detailed notes** - Mention specific delivery location (e.g., "Left at front door")
3. **Update status promptly** - Mark status changes immediately for accurate tracking
4. **Verify recipient** - Confirm identity before handing over items
5. **Check items** - Verify item count matches order before leaving warehouse

### For Administrators
1. **Monitor unassigned orders** - Ensure orders don't remain unassigned for long periods
2. **Track driver performance** - Review completion rates and delivery times
3. **Validate delivery proofs** - Spot-check photos for quality and authenticity
4. **Handle exceptions** - Process after-sales requests promptly
5. **Optimize routes** - Use route planning to minimize delivery times

---

## Appendix: Database Migrations

### Migration Files

| File | Purpose |
|------|---------|
| `001_create_driver_table.sql` | Create tigu_driver table |
| `002_add_driver_id_to_orders.sql` | Add driver_id FK to tigu_order |
| `005_create_delivery_proof_table.sql` | Create tigu_delivery_proof table |

### Sample Migration: Add driver_id to orders

```sql
-- Migration: 002_add_driver_id_to_orders.sql
ALTER TABLE tigu_order
ADD COLUMN driver_id BIGINT UNSIGNED NULL
AFTER shop_id;

ALTER TABLE tigu_order
ADD INDEX idx_driver_id (driver_id);

ALTER TABLE tigu_order
ADD CONSTRAINT fk_order_driver
FOREIGN KEY (driver_id)
REFERENCES tigu_driver(id)
ON DELETE RESTRICT;
```

---

# 中文版本

## 概述

本文档从司机角度描述完整的配送工作流程，包括每个阶段发生的所有数据库操作。

### 配送状态流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        配送生命周期                                │
└─────────────────────────────────────────────────────────────────┘

      [可接单]
         ↓
    司机接受订单
         ↓
      [已接单]
         ↓
    司机开始配送
         ↓
      [配送中]
         ↓
    司机送达并上传凭证
         ↓
      [已完成]
```

### 状态代码

| 状态 | shipping_status | order_status | 说明 |
|------|----------------|--------------|------|
| 可接单 | `NULL` | 1 | 未分配订单，等待司机接单 |
| 已接单 | `0` | 1 或 2 | 司机已接受，准备配送 |
| 配送中 | `1` 或 `2` | 2 | 订单正在配送中 |
| 已完成 | `3` | 3 | 配送已完成并上传凭证 |

---

## 阶段一：可接单

### 司机操作
- 司机查看可用（未分配）订单列表
- 司机选择一个订单进行接单
- 司机确认接受该订单

### API 调用
```http
GET /api/v1/orders/available
```

**响应示例：**
```json
{
  "items": [
    {
      "orderSn": "ORD-20250101-00001",
      "recipientName": "张三",
      "recipientPhone": "138-0000-1234",
      "deliveryAddress": "北京市朝阳区建国路123号",
      "shippingStatus": null,
      "itemCount": 3,
      "totalAmount": 199.99
    }
  ],
  "total": 15
}
```

### 数据库查询
```sql
SELECT o.*, w.name as warehouse_name
FROM tigu_order o
LEFT JOIN tigu_warehouse w ON o.warehouse_id = w.id
WHERE o.driver_id IS NULL
  AND o.shipping_status IS NULL
  AND o.order_status IN (1, 2)
ORDER BY o.create_time ASC;
```

### 表状态

**表名：** `tigu_order`

| 字段 | 值 | 说明 |
|------|-----|------|
| `driver_id` | `NULL` | 尚未分配司机 |
| `shipping_status` | `NULL` 或 `0` | 未分配 |
| `order_status` | `1`（待发货） | 已支付，等待发货 |
| `shipping_time` | `NULL` | 尚未发货 |
| `finish_time` | `NULL` | 尚未完成 |

### 界面显示
- 显示可接订单列表及收件人详情
- 显示从仓库到配送地点的距离
- 显示预计配送时间
- 显示订单金额和商品数量
- 每个订单有"接单"按钮

---

## 阶段二：已接单

### 司机操作
- 司机点击"接单"或"取货"按钮
- 系统将订单分配给该司机
- 司机准备从仓库取货

### API 调用
```http
POST /api/v1/orders/{order_sn}/pickup
```

**请求头：**
```
Authorization: Bearer {jwt_token}
```

**响应：**
```json
{
  "success": true,
  "message": "订单接单成功",
  "order": {
    "orderSn": "ORD-20250101-00001",
    "driverId": 5,
    "shippingStatus": 0
  }
}
```

### 数据库操作

#### 更新语句
```sql
UPDATE tigu_order
SET driver_id = {已认证的司机ID},
    shipping_status = 0,
    update_time = NOW()
WHERE order_sn = '{订单编号}'
  AND driver_id IS NULL;  -- 确保尚未被分配
```

#### 受影响的字段

**表名：** `tigu_order`

| 字段 | 更新前 | 更新后 | 说明 |
|------|--------|--------|------|
| `driver_id` | `NULL` | `5` | 从JWT令牌获取的司机ID |
| `shipping_status` | `NULL` | `0` | 状态："未发货"（待取货） |
| `update_time` | （旧时间戳） | `2025-01-15 10:30:00` | 当前时间戳 |
| `order_status` | `1` | `1` 或 `2` | 可能更新为"待收货" |

### 业务逻辑
1. 验证订单存在且未被分配（`driver_id IS NULL`）
2. 从JWT认证令牌中提取司机ID
3. 原子性更新 `driver_id` 和 `shipping_status`
4. 向司机应用返回更新后的订单详情
5. 从"可接订单"列表中移除该订单
6. 将订单添加到司机的"我的订单"列表

### 界面更新
- 订单从"可接"标签移至"已接"标签
- 订单显示状态："已接单"或"准备配送"
- 司机现在可以开始配送

---

## 阶段三：配送中

### 司机操作
- 司机从仓库取货
- 司机点击"开始配送"按钮
- 司机导航至配送地址
- 系统追踪配送进度（可选GPS追踪）

### API 调用
```http
POST /api/v1/orders/{order_sn}/status
Content-Type: application/json

{
  "shippingStatus": 1
}
```

**响应：**
```json
{
  "success": true,
  "message": "订单状态更新成功",
  "order": {
    "orderSn": "ORD-20250101-00001",
    "shippingStatus": 1
  }
}
```

### 数据库操作

#### 更新语句
```sql
UPDATE tigu_order
SET shipping_status = 1,
    shipping_time = NOW(),
    order_status = 2,
    update_time = NOW()
WHERE order_sn = '{订单编号}'
  AND driver_id = {已认证的司机ID}
  AND shipping_status = 0;  -- 仅允许从"已接单"状态转换
```

#### 受影响的字段

**表名：** `tigu_order`

| 字段 | 更新前 | 更新后 | 说明 |
|------|--------|--------|------|
| `shipping_status` | `0` | `1` | 状态："已发货"（配送中） |
| `shipping_time` | `NULL` | `2025-01-15 11:00:00` | 配送开始时间戳 |
| `order_status` | `1` 或 `2` | `2` | "待收货" |
| `update_time` | （之前的值） | `2025-01-15 11:00:00` | 当前时间戳 |

### 可选：部分配送

对于有多个配送点的订单：

```http
POST /api/v1/orders/{order_sn}/status
Content-Type: application/json

{
  "shippingStatus": 2
}
```

**数据库更新：**
```sql
UPDATE tigu_order
SET shipping_status = 2,
    update_time = NOW()
WHERE order_sn = '{订单编号}'
  AND driver_id = {已认证的司机ID};
```

| shipping_status | 含义 |
|-----------------|------|
| `1` | 完全配送中（单个配送点） |
| `2` | 部分已配送（多个配送点，部分已完成） |

### 界面更新
- 订单状态显示"配送中"或"运送中"
- 导航/地图显示到配送地址的路线
- 显示预计到达时间
- 提供联系收件人的选项
- "标记为已送达"按钮变为可用

---

## 阶段四：已完成

### 司机操作
- 司机到达配送地点
- 司机将商品交给收件人
- 司机拍摄已送达商品或签收单的照片
- 司机添加可选的配送备注
- 司机提交配送凭证

### API 调用
```http
POST /api/v1/orders/{order_sn}/proof
Content-Type: application/json

{
  "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "notes": "已送达收件人门口"
}
```

**请求体：**
- `photo`：Base64编码的图片（JPEG/PNG，最大4MB）
- `notes`：可选的文字描述（最多500字符）

**响应：**
```json
{
  "success": true,
  "message": "配送凭证上传成功",
  "proof": {
    "id": 123,
    "orderSn": "ORD-20250101-00001",
    "photoUrl": "/deliveries/photos/ORD-20250101-00001_1705315200.jpeg",
    "notes": "已送达收件人门口",
    "createdAt": "2025-01-15T11:30:00Z"
  }
}
```

### 数据库操作

#### 步骤1：保存照片到文件系统

**操作：**
1. 解码base64图片数据
2. 验证文件大小（≤ 4MB）和MIME类型（JPEG/PNG）
3. 生成文件名：`{订单编号}_{时间戳}.{扩展名}`
4. 保存到：`/var/www/deliveries/photos/`
5. 生成URL路径：`/deliveries/photos/{文件名}`

**示例：**
```
文件：/var/www/deliveries/photos/ORD-20250101-00001_1705315200.jpeg
URL： https://api.wetigu.com/deliveries/photos/ORD-20250101-00001_1705315200.jpeg
```

#### 步骤2：插入配送凭证记录

```sql
INSERT INTO tigu_delivery_proof (
  order_id,
  order_sn,
  driver_id,
  photo_url,
  notes,
  file_size,
  mime_type,
  created_at,
  updated_at
) VALUES (
  {订单ID},
  'ORD-20250101-00001',
  {司机ID},
  '/deliveries/photos/ORD-20250101-00001_1705315200.jpeg',
  '已送达收件人门口',
  1245678,
  'image/jpeg',
  NOW(),
  NOW()
);
```

**表名：** `tigu_delivery_proof`

| 字段 | 值 | 说明 |
|------|-----|------|
| `id` | `123` | 自增主键 |
| `order_id` | `5001` | 外键关联 tigu_order |
| `order_sn` | `ORD-20250101-00001` | 订单编号 |
| `driver_id` | `5` | 外键关联 tigu_driver |
| `photo_url` | `/deliveries/photos/ORD-...jpeg` | 照片相对URL |
| `notes` | `已送达收件人...` | 司机备注 |
| `file_size` | `1245678` | 文件大小（字节）：1.2MB |
| `mime_type` | `image/jpeg` | 图片MIME类型 |
| `created_at` | `2025-01-15 11:30:00` | 创建时间戳 |
| `updated_at` | `2025-01-15 11:30:00` | 更新时间戳 |

#### 步骤3：更新订单状态为已送达

```sql
UPDATE tigu_order
SET shipping_status = 3,
    order_status = 3,
    finish_time = NOW(),
    update_time = NOW()
WHERE order_sn = '{订单编号}'
  AND driver_id = {已认证的司机ID}
  AND shipping_status IN (1, 2);  -- 仅允许从配送中状态转换
```

**表名：** `tigu_order`

| 字段 | 更新前 | 更新后 | 说明 |
|------|--------|--------|------|
| `shipping_status` | `1` 或 `2` | `3` | 状态："已送达" |
| `order_status` | `2` | `3` | 状态："已完成" |
| `finish_time` | `NULL` | `2025-01-15 11:30:00` | 配送完成时间 |
| `update_time` | （之前的值） | `2025-01-15 11:30:00` | 当前时间戳 |

#### 步骤4：更新司机统计数据（可选）

```sql
UPDATE tigu_driver
SET total_deliveries = total_deliveries + 1,
    updated_at = NOW()
WHERE id = {司机ID};
```

**表名：** `tigu_driver`

| 字段 | 更新前 | 更新后 | 说明 |
|------|--------|--------|------|
| `total_deliveries` | `127` | `128` | 增加已完成配送数量 |
| `updated_at` | （之前的值） | `2025-01-15 11:30:00` | 当前时间戳 |

### 事务流程

配送凭证上传被包装在数据库事务中：

```python
async with session.begin():
    # 1. 验证订单归属和状态
    order = await fetch_order(session, order_sn, driver_id)

    # 2. 保存照片到文件系统
    photo_url = save_photo(image_bytes, order_sn, mime_type)

    # 3. 插入 delivery_proof 记录
    proof = DeliveryProof(...)
    session.add(proof)

    # 4. 更新订单状态为已送达
    order.shipping_status = 3
    order.order_status = 3
    order.finish_time = datetime.now()

    # 5. 更新司机统计数据
    driver.total_deliveries += 1

    await session.commit()
```

### 界面更新
- 订单移至"已完成"标签
- 显示配送时间戳和照片
- 显示带绿色对勾的"已送达"徽章
- 司机可以查看配送详情但不能修改
- 显示完成确认消息

### 验证规则
- 只有被分配的司机可以上传凭证
- 照片为必填项（无照片不能完成）
- 订单必须处于"配送中"状态（shipping_status = 1 或 2）
- 照片必须为JPEG或PNG格式
- 照片大小必须 ≤ 4MB
- Base64编码必须有效

---

## 数据库架构参考

### 主要表

#### `tigu_order`
主订单表，追踪配送生命周期。

| 字段 | 类型 | 索引 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | BIGINT UNSIGNED | 主键 | 自增 | 订单ID |
| `order_sn` | VARCHAR(64) | 唯一 | - | 订单编号 |
| `user_id` | BIGINT UNSIGNED | 索引 | - | 客户ID |
| `shop_id` | BIGINT UNSIGNED | 索引 | - | 商家ID |
| `driver_id` | BIGINT UNSIGNED | 索引 | NULL | 分配的司机（外键至 tigu_driver） |
| `warehouse_id` | BIGINT | 索引 | - | 取货地点（外键至 tigu_warehouse） |
| `shipping_status` | INT | 索引 | NULL | 配送状态（0-3） |
| `order_status` | INT | 索引 | - | 订单生命周期状态（0-5） |
| `receiver_name` | VARCHAR(64) | - | - | 收件人姓名 |
| `receiver_phone` | VARCHAR(32) | - | - | 收件人电话 |
| `receiver_address` | VARCHAR(256) | - | - | 完整配送地址 |
| `receiver_province` | VARCHAR(50) | - | - | 省/州 |
| `receiver_city` | VARCHAR(50) | - | - | 城市 |
| `receiver_district` | VARCHAR(50) | - | - | 区/县 |
| `shipping_time` | DATETIME | - | NULL | 配送开始时间 |
| `finish_time` | DATETIME | - | NULL | 配送完成时间 |
| `create_time` | DATETIME | - | NOW() | 订单创建时间 |
| `update_time` | DATETIME | - | NOW() | 最后更新时间 |

**索引：**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_order_sn (order_sn)`
- `INDEX idx_driver_id (driver_id)`
- `INDEX idx_shipping_status (shipping_status)`
- `INDEX idx_user_id (user_id)`
- `INDEX idx_create_time (create_time)`

---

#### `tigu_delivery_proof`
存储配送凭证照片和备注。

| 字段 | 类型 | 索引 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | BIGINT UNSIGNED | 主键 | 自增 | 凭证记录ID |
| `order_id` | BIGINT UNSIGNED | 索引 | - | 外键至 tigu_order（级联删除） |
| `order_sn` | VARCHAR(64) | 索引 | - | 订单编号 |
| `driver_id` | BIGINT UNSIGNED | 索引 | - | 外键至 tigu_driver（限制删除） |
| `photo_url` | VARCHAR(512) | - | - | 照片URL路径 |
| `notes` | TEXT | - | NULL | 配送备注 |
| `file_size` | INT UNSIGNED | - | - | 照片大小（字节） |
| `mime_type` | VARCHAR(50) | - | - | 图片MIME类型 |
| `created_at` | DATETIME | - | NOW() | 上传时间戳 |
| `updated_at` | DATETIME | - | NOW() | 更新时间戳 |

**索引：**
- `PRIMARY KEY (id)`
- `INDEX idx_order_sn (order_sn)`
- `INDEX idx_driver_id (driver_id)`
- `FOREIGN KEY (order_id) REFERENCES tigu_order(id) ON DELETE CASCADE`
- `FOREIGN KEY (driver_id) REFERENCES tigu_driver(id) ON DELETE RESTRICT`

---

#### `tigu_driver`
司机主数据表。

| 字段 | 类型 | 索引 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | BIGINT UNSIGNED | 主键 | 自增 | 司机ID |
| `name` | VARCHAR(100) | - | - | 司机姓名 |
| `phone` | VARCHAR(20) | 唯一 | - | 手机号（用于登录） |
| `email` | VARCHAR(100) | - | NULL | 电子邮箱 |
| `license_number` | VARCHAR(50) | - | NULL | 驾驶证号 |
| `vehicle_type` | VARCHAR(50) | - | NULL | 车辆类型 |
| `vehicle_plate` | VARCHAR(20) | - | NULL | 车牌号 |
| `status` | TINYINT | 索引 | 1 | 1=激活，0=停用 |
| `rating` | DECIMAL(3,2) | - | 0.00 | 司机评分（0-5） |
| `total_deliveries` | INT | - | 0 | 已完成配送数量 |
| `created_at` | DATETIME | - | NOW() | 创建时间戳 |
| `updated_at` | DATETIME | - | NOW() | 更新时间戳 |

**索引：**
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_phone (phone)`
- `INDEX idx_status (status)`

---

### 关系图

```
┌─────────────────────┐
│  tigu_warehouse     │
│   （仓库/取货点）      │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────────────────────────────────┐
│              tigu_order（订单）                    │
│  ┌──────────────────────────────────────────┐  │
│  │ - id (主键)                               │  │
│  │ - order_sn (唯一)                         │  │
│  │ - driver_id (外键) ───────┐              │  │
│  │ - warehouse_id (外键)      │              │  │
│  │ - shipping_status (0-3)   │              │  │
│  │ - order_status (0-5)      │              │  │
│  │ - receiver_* (地址信息)    │              │  │
│  │ - shipping_time           │              │  │
│  │ - finish_time             │              │  │
│  └──────────────────────────┼──────────────┘  │
└───────────────────────────┬─┼─────────────────┘
                            │ │
                      ┌─────┘ └──────────┐
                      │ 1                │ N
                      │                  │
           ┌──────────▼───────┐   ┌─────▼──────────────┐
           │   tigu_driver    │   │ tigu_order_item    │
           │   （司机）         │   │  （订单项目）        │
           │  ┌───────────┐   │   └────────────────────┘
           │  │ - id (PK) │   │
           │  │ - phone   │◄──┼───┐
           │  │ - status  │   │   │ 1
           │  └───────────┘   │   │
           └──────────────────┘   │ N
                                  │
                    ┌─────────────▼──────────────┐
                    │  tigu_delivery_proof       │
                    │   （配送凭证）               │
                    │  ┌─────────────────────┐   │
                    │  │ - id (主键)          │   │
                    │  │ - order_id (外键)    │   │
                    │  │ - driver_id (外键)   │   │
                    │  │ - photo_url (照片)   │   │
                    │  │ - notes (备注)       │   │
                    │  └─────────────────────┘   │
                    └────────────────────────────┘
```

---

## API接口参考

### 司机端点

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/orders/available` | 列出未分配订单 | 必需 |
| `GET` | `/api/v1/orders/assigned` | 列出司机已分配订单 | 必需 |
| `GET` | `/api/v1/orders/{order_sn}` | 获取订单详情 | 必需 |
| `POST` | `/api/v1/orders/{order_sn}/pickup` | 接受/接单 | 必需 |
| `POST` | `/api/v1/orders/{order_sn}/status` | 更新配送状态 | 必需 |
| `POST` | `/api/v1/orders/{order_sn}/proof` | 上传配送凭证 | 必需 |
| `POST` | `/api/v1/routes/optimize` | 生成优化路线 | 必需 |

### 认证

所有司机端点需要JWT认证：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

JWT令牌包含：
- `phone`：司机手机号（唯一标识符）
- `exp`：令牌过期时间戳

---

## 状态代码参考

### shipping_status（配送状态）

| 代码 | 标签 | 说明 | 下一步操作 |
|------|------|------|-----------|
| `NULL` | 未分配 | 订单未分配给司机 | 司机接单 |
| `0` | 未发货 | 司机已接受，准备中 | 开始配送 |
| `1` | 已发货 | 正在前往配送地点 | 完成配送 |
| `2` | 部分已发货 | 部分配送（多点配送） | 完成剩余配送 |
| `3` | 已送达 | 配送已完成 | 无（最终状态） |

### order_status（订单生命周期）

| 代码 | 标签 | 说明 |
|------|------|------|
| `0` | 待付款 | 等待客户付款 |
| `1` | 待发货 | 已付款，等待司机取货 |
| `2` | 待收货 | 配送中，等待送达 |
| `3` | 已完成 | 订单已完成 |
| `4` | 已取消 | 订单已取消 |
| `5` | 售后中 | 已请求售后服务 |

### driver.status（司机状态）

| 代码 | 标签 | 说明 |
|------|------|------|
| `0` | 停用 | 司机账户已禁用 |
| `1` | 激活 | 司机可接单 |

---

## 错误处理

### 常见错误场景

#### 1. 订单已被分配
```json
{
  "error": "ORDER_ALREADY_ASSIGNED",
  "message": "此订单已被其他司机接单"
}
```

**原因：** 另一位司机先接了该订单
**解决方案：** 刷新可接订单列表

---

#### 2. 无效的状态转换
```json
{
  "error": "INVALID_STATUS_TRANSITION",
  "message": "无法将状态从 3 更新为 1"
}
```

**原因：** 尝试将已完成订单改回配送中
**解决方案：** 状态转换必须遵循有效顺序

---

#### 3. 照片上传失败
```json
{
  "error": "FILE_TOO_LARGE",
  "message": "照片大小超过4MB限制"
}
```

**原因：** 图片文件过大
**解决方案：** 上传前压缩图片

---

#### 4. 未授权访问
```json
{
  "error": "UNAUTHORIZED",
  "message": "此订单未分配给您"
}
```

**原因：** 司机尝试更新其他司机的订单
**解决方案：** 只能访问您自己的订单

---

## 最佳实践

### 司机
1. **始终拍摄清晰照片** - 确保配送凭证清晰可见且光线充足
2. **添加详细备注** - 注明具体配送位置（例如："放在前门"）
3. **及时更新状态** - 立即标记状态变化以准确追踪
4. **验证收件人** - 交付物品前确认身份
5. **检查物品** - 离开仓库前验证物品数量与订单一致

### 管理员
1. **监控未分配订单** - 确保订单不会长时间未分配
2. **追踪司机表现** - 审查完成率和配送时间
3. **验证配送凭证** - 抽查照片质量和真实性
4. **处理异常** - 及时处理售后请求
5. **优化路线** - 使用路线规划最小化配送时间

---

## 附录：数据库迁移

### 迁移文件

| 文件 | 用途 |
|------|------|
| `001_create_driver_table.sql` | 创建 tigu_driver 表 |
| `002_add_driver_id_to_orders.sql` | 向 tigu_order 添加 driver_id 外键 |
| `005_create_delivery_proof_table.sql` | 创建 tigu_delivery_proof 表 |

### 示例迁移：向订单添加 driver_id

```sql
-- 迁移: 002_add_driver_id_to_orders.sql
ALTER TABLE tigu_order
ADD COLUMN driver_id BIGINT UNSIGNED NULL
AFTER shop_id;

ALTER TABLE tigu_order
ADD INDEX idx_driver_id (driver_id);

ALTER TABLE tigu_order
ADD CONSTRAINT fk_order_driver
FOREIGN KEY (driver_id)
REFERENCES tigu_driver(id)
ON DELETE RESTRICT;
```

---

## 文档版本

- **版本：** 1.0
- **最后更新：** 2025-01-15
- **作者：** 技术团队
- **系统：** Tigub2b 配送管理系统

---

**备注：** 本文档基于 `/home/mli/tigub2b/tigub2b_delivery/` 代码库的全面分析生成。
