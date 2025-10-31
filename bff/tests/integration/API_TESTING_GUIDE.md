# API Integration Testing Guide

Manual testing guide for the dual workflow API endpoints.

## Prerequisites

1. Backend server running: `uvicorn app.main:app --reload`
2. Valid authentication token
3. Test orders in database with different `shipping_type` values

## Authentication

Get access token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "1234567890", "code": "123456"}'
```

Save the `accessToken` for subsequent requests.

## Test Scenarios

### Scenario 1: Warehouse Delivery Workflow (shipping_type=1)

#### Step 1: Pickup Order
**Expected**: `shippingStatus` → 2 (Driver Received)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/pickup \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Picked up from warehouse"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Order picked up successfully",
  "orderSn": "TOD123",
  "shippingStatus": 2,
  "actionId": 1234567890
}
```

#### Step 2: Arrive at Warehouse
**Expected**: `shippingStatus` 2 → 3 (Arrived Warehouse)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/arrive-warehouse \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Arrived at main warehouse"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Order arrived at warehouse",
  "orderSn": "TOD123",
  "shippingStatus": 3,
  "actionId": 1234567891
}
```

#### Step 3: Warehouse Ships
**Expected**: `shippingStatus` 3 → 4 (Warehouse Shipped)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/warehouse-ship \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Shipped from warehouse to customer"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Order shipped from warehouse",
  "orderSn": "TOD123",
  "shippingStatus": 4,
  "actionId": 1234567892
}
```

#### Step 4: Complete Delivery
**Expected**: `shippingStatus` 4 → 5 (Delivered), `orderStatus` → 3 (Completed)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/proof \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Delivered to customer"
  }'
```

**Expected Response**:
```json
{
  "status": "uploaded",
  "photoUrl": "https://api.wetigu.com/uploads/proof_123.jpg",
  "orderSn": "TOD123",
  "uploadedAt": "2024-10-31T10:30:00Z"
}
```

---

### Scenario 2: Direct Delivery Workflow (shipping_type=0)

#### Step 1: Pickup Order
**Expected**: `shippingStatus` → 4 (Warehouse Shipped/Direct Pickup)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/pickup \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Picked up directly for delivery"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Order picked up successfully",
  "orderSn": "TOD456",
  "shippingStatus": 4,
  "actionId": 1234567893
}
```

#### Step 2: Complete Delivery
**Expected**: `shippingStatus` 4 → 5 (Delivered)

```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/proof \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "notes": "Delivered directly to customer"
  }'
```

---

## Error Cases to Test

### 1. Wrong Order State
```bash
# Try to arrive at warehouse when status is not 2
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/arrive-warehouse \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{"photo": "data:image/jpeg;base64,...", "notes": "Test"}'
```

**Expected**: `409 Conflict` - "Order not in correct state for warehouse arrival"

### 2. Direct Delivery Attempting Warehouse Steps
```bash
# Try warehouse-ship on direct delivery order (shipping_type=0)
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/warehouse-ship \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{"photo": "data:image/jpeg;base64,...", "notes": "Test"}'
```

**Expected**: `400 Bad Request` - "This endpoint is only for warehouse delivery orders"

### 3. Missing Photo
```bash
curl -X POST http://localhost:8000/api/v1/orders/{orderSn}/pickup \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Test without photo"}'
```

**Expected**: `422 Unprocessable Entity` - Validation error for missing `photo` field

### 4. Invalid Order
```bash
curl -X POST http://localhost:8000/api/v1/orders/INVALID_SN/pickup \
  -H "Authorization: Bearer {accessToken}" \
  -H "Content-Type: application/json" \
  -d '{"photo": "data:image/jpeg;base64,...", "notes": "Test"}'
```

**Expected**: `404 Not Found` - "Order not found"

---

## Database Validation Queries

After each step, verify database state:

```sql
-- Check order status
SELECT order_sn, shipping_status, order_status, shipping_type,
       driver_receive_time, arrive_warehouse_time,
       warehouse_shipping_time, finish_time
FROM tigu_order WHERE order_sn = 'TOD123';

-- Check action audit trail
SELECT id, action_type, shipping_status, shipping_type,
       logistics_voucher_file, create_time, remark
FROM tigu_order_action WHERE order_id = {order_id}
ORDER BY create_time ASC;

-- Check uploaded files
SELECT id, file_url, biz_id, biz_type
FROM tigu_uploaded_files
WHERE biz_type = 'order_action' AND biz_id IN (
  SELECT id FROM tigu_order_action WHERE order_id = {order_id}
);
```

---

## Success Criteria

✅ **Warehouse Workflow**:
- Pickup sets status to 2
- Arrive warehouse sets status to 3
- Warehouse ship sets status to 4
- Complete delivery sets status to 5

✅ **Direct Workflow**:
- Pickup sets status to 4
- Complete delivery sets status to 5

✅ **Audit Trail**:
- Each step creates an order_action record
- Photos are uploaded and linked via biz_id
- Timestamps are recorded correctly

✅ **Error Handling**:
- Invalid state transitions return 409
- Wrong delivery type returns 400
- Missing data returns 422
- Invalid orders return 404

---

## Automated Test Script (Optional)

Save as `test_workflow_api.sh`:

```bash
#!/bin/bash

# Configuration
API_URL="http://localhost:8000/api/v1"
PHONE="1234567890"
CODE="123456"

# Login
echo "Logging in..."
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"$PHONE\",\"code\":\"$CODE\"}" \
  | jq -r '.accessToken')

echo "Token: $TOKEN"

# Test warehouse workflow
ORDER_SN="TOD123"
PHOTO="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD"

echo "Testing warehouse workflow for $ORDER_SN..."

# Step 1: Pickup
curl -s -X POST "$API_URL/orders/$ORDER_SN/pickup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test pickup\"}" \
  | jq '.'

# Step 2: Arrive warehouse
curl -s -X POST "$API_URL/orders/$ORDER_SN/arrive-warehouse" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test arrive\"}" \
  | jq '.'

# Step 3: Warehouse ship
curl -s -X POST "$API_URL/orders/$ORDER_SN/warehouse-ship" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test ship\"}" \
  | jq '.'

# Step 4: Complete
curl -s -X POST "$API_URL/orders/$ORDER_SN/proof" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test complete\"}" \
  | jq '.'

echo "Workflow test complete!"
```

Run with: `chmod +x test_workflow_api.sh && ./test_workflow_api.sh`
