# Implementation Plan: Updated Workflow Integration

**Date**: 2025-01-15
**Based On**: DRIVER_WORKFLOW_GUIDE_UPDATED.md
**Database**: tigu_b2b (DO NOT ALTER BASE TABLES - they already exist)

---

## Executive Summary

The database already contains all required tables and fields for the updated workflow:
- ✅ `tigu_order_action` table exists
- ✅ `tigu_order` has `driver_receive_time`, `arrive_warehouse_time`, `warehouse_shipping_time` fields
- ✅ `tigu_uploaded_files` has `biz_id` linking capability
- ✅ `tigu_order` has `shipping_type` field

**What's Missing**: Backend (BFF) and Frontend code to utilize these existing database structures.

---

## Database Status (NO CHANGES NEEDED)

### ✅ Existing Tables Verified

#### `tigu_order`
```sql
-- Already has ALL required fields:
- shipping_type (int) ✓
- shipping_status (int) ✓
- driver_receive_time (datetime) ✓
- arrive_warehouse_time (datetime) ✓
- warehouse_shipping_time (datetime) ✓
```

#### `tigu_order_action`
```sql
-- Already exists with correct structure:
- id (bigint unsigned, PK) ✓
- order_id (bigint) ✓
- order_status (int) ✓
- shipping_status (int) ✓
- shipping_type (int) ✓
- action_type (int) ✓ -- 0-10 codes
- logistics_voucher_file (varchar 2000) ✓ -- Comma-separated file IDs
- create_time, update_time, create_by, update_by, remark ✓
```

#### `tigu_uploaded_files`
```sql
-- Already has linking capability:
- id (bigint unsigned, PK) ✓
- file_url (varchar 500) ✓
- biz_type (varchar 200, nullable) ✓
- biz_id (bigint unsigned, nullable) ✓ -- Links to tigu_order_action.id
- is_main (int, default 0) ✓
```

---

## Required Changes

## Phase 1: Backend (BFF) - SQLAlchemy Models

### 1.1 Update `bff/app/models/order.py`

**File**: `/home/mli/tigub2b/tigub2b_delivery/bff/app/models/order.py`

#### Add Missing Fields to `Order` Model (Lines 28-58)

```python
class Order(Base):
    __tablename__ = "tigu_order"

    # ... existing fields ...

    # ADD these timestamp fields:
    driver_receive_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    arrive_warehouse_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    warehouse_shipping_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    # ... rest of model ...
```

**Location**: After line 50 (`finish_time`), before line 51 (`create_time`)

#### Add New `OrderAction` Model (After `Warehouse` class, ~line 94)

```python
class OrderAction(Base):
    __tablename__ = "tigu_order_action"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("tigu_order.id"), index=True)
    order_status: Mapped[int] = mapped_column(Integer, default=0)
    shipping_status: Mapped[int] = mapped_column(Integer)
    shipping_type: Mapped[int] = mapped_column(Integer, default=0)
    action_type: Mapped[int] = mapped_column(Integer)  # 0-10 codes
    logistics_voucher_file: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    create_by: Mapped[str] = mapped_column(String(64), default="")
    create_time: Mapped[datetime] = mapped_column(DateTime())
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    # Relationship to order
    order: Mapped[Order] = relationship("Order", backref="actions")
```

**Validation**: No database migration needed - table already exists.

---

### 1.2 Update `UploadedFile` Model

The model already exists at line 18-25. **Verify it has all fields**:

```python
class UploadedFile(Base):
    __tablename__ = "tigu_uploaded_files"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    file_url: Mapped[str] = mapped_column(String(500))
    biz_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    biz_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)  # ✓ Already exists
    is_main: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
```

**Status**: ✅ Already complete - no changes needed.

---

## Phase 2: Backend (BFF) - Schemas

### 2.1 Create `bff/app/schemas/order_action.py` (NEW FILE)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class OrderActionBase(BaseModel):
    """Base schema for order action"""
    model_config = ConfigDict(populate_by_name=True)

    order_id: int = Field(alias='orderId')
    order_status: int = Field(alias='orderStatus')
    shipping_status: int = Field(alias='shippingStatus')
    shipping_type: int = Field(alias='shippingType')
    action_type: int = Field(alias='actionType')
    logistics_voucher_file: Optional[str] = Field(default=None, alias='logisticsVoucherFile')


class OrderActionCreate(OrderActionBase):
    """Schema for creating order action"""
    pass


class OrderActionResponse(OrderActionBase):
    """Schema for order action response"""
    id: int
    create_time: datetime = Field(alias='createTime')


class PickupRequest(BaseModel):
    """Schema for pickup with photo upload"""
    model_config = ConfigDict(populate_by_name=True)

    photo: str = Field(..., description="Base64 encoded image")
    notes: Optional[str] = Field(default=None, max_length=1000)


class PickupResponse(BaseModel):
    """Schema for pickup response"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    order_sn: str = Field(alias='orderSn')
    shipping_status: int = Field(alias='shippingStatus')
    action_id: int = Field(alias='actionId')
```

**Location**: New file at `bff/app/schemas/order_action.py`

---

### 2.2 Update `bff/app/schemas/order.py`

**Add new fields to `OrderDetail` schema** (Line 56-60):

```python
class OrderDetail(OrderSummary):
    logistics_order_number: Optional[str] = Field(alias='logisticsOrderNumber')
    shipping_time: Optional[datetime] = Field(alias='shippingTime')
    finish_time: Optional[datetime] = Field(alias='finishTime')

    # ADD these new timestamp fields:
    driver_receive_time: Optional[datetime] = Field(default=None, alias='driverReceiveTime')
    arrive_warehouse_time: Optional[datetime] = Field(default=None, alias='arriveWarehouseTime')
    warehouse_shipping_time: Optional[datetime] = Field(default=None, alias='warehouseShippingTime')

    delivery_proof: Optional[DeliveryProofInfo] = Field(default=None, alias='deliveryProof')
```

**Add `shipping_type` to `OrderSummary`** (Line 35-53):

```python
class OrderSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_sn: str = Field(alias='orderSn')
    shipping_status: int = Field(alias='shippingStatus')
    shipping_type: int = Field(alias='shippingType')  # ADD THIS
    order_status: int = Field(alias='orderStatus')
    # ... rest of fields ...
```

---

## Phase 3: Backend (BFF) - Services

### 3.1 Create `bff/app/services/order_action_service.py` (NEW FILE)

```python
"""
Service for managing order action audit trail and file linking.
Handles workflow step logging with photo evidence.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderAction, UploadedFile


async def create_order_action(
    session: AsyncSession,
    order_id: int,
    order_status: int,
    shipping_status: int,
    shipping_type: int,
    action_type: int,
    file_ids: list[int] | None = None,
    create_by: str = "system"
) -> OrderAction:
    """
    Create order action record with optional file linking.

    Args:
        session: Database session
        order_id: Order ID
        order_status: Current order_status
        shipping_status: Current shipping_status
        shipping_type: 0=User, 1=Warehouse
        action_type: Action type code (0-10)
        file_ids: List of uploaded file IDs to link
        create_by: Creator identifier

    Returns:
        Created OrderAction instance
    """
    # Generate snowflake ID (simplified - use actual snowflake generator in production)
    from time import time_ns
    action_id = int(time_ns() / 1000000)  # Millisecond timestamp as simple ID

    # Prepare logistics_voucher_file (comma-separated file IDs)
    voucher_file = ",".join(str(fid) for fid in file_ids) if file_ids else None

    # Insert action record
    stmt = insert(OrderAction).values(
        id=action_id,
        order_id=order_id,
        order_status=order_status,
        shipping_status=shipping_status,
        shipping_type=shipping_type,
        action_type=action_type,
        logistics_voucher_file=voucher_file,
        create_by=create_by,
        create_time=datetime.now()
    )
    await session.execute(stmt)

    # Link files to action via biz_id
    if file_ids:
        for file_id in file_ids:
            await session.execute(
                UploadedFile.__table__.update()
                .where(UploadedFile.id == file_id)
                .values(biz_id=action_id, biz_type="order_action")
            )

    await session.commit()

    # Fetch and return created action
    result = await session.execute(
        select(OrderAction).where(OrderAction.id == action_id)
    )
    return result.scalar_one()


async def get_order_actions(
    session: AsyncSession,
    order_id: int
) -> list[OrderAction]:
    """Get all action records for an order"""
    stmt = (
        select(OrderAction)
        .where(OrderAction.order_id == order_id)
        .order_by(OrderAction.create_time.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_action_files(
    session: AsyncSession,
    action_id: int
) -> list[UploadedFile]:
    """Get all files linked to an action"""
    stmt = (
        select(UploadedFile)
        .where(UploadedFile.biz_id == action_id)
        .where(UploadedFile.biz_type == "order_action")
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

**Location**: New file at `bff/app/services/order_action_service.py`

---

### 3.2 Update `bff/app/services/order_service.py`

**Update status labels** (Lines 14-28):

```python
SHIPPING_STATUS_LABELS = {
    0: "Not Shipped",
    1: "Shipped",
    2: "Driver Received",        # NEW
    3: "Arrived Warehouse",      # NEW
    4: "Warehouse Shipped",      # UPDATED
    5: "Delivered"               # NEW
}
```

**Update `pickup_order` function** (Lines 183-208):

```python
async def pickup_order(
    session: AsyncSession,
    order_sn: str,
    driver_id: int,
    shipping_type: int  # ADD THIS PARAMETER
) -> bool:
    """
    Assign order to driver with shipping_type-aware status setting.

    For warehouse delivery (shipping_type=1): sets shipping_status=2
    For direct delivery (shipping_type=0): sets shipping_status=4
    """
    # Determine shipping_status based on shipping_type
    new_shipping_status = 2 if shipping_type == 1 else 4

    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.driver_id.is_(None))
        .values(
            driver_id=driver_id,
            order_status=2,  # Pending Receipt
            shipping_status=new_shipping_status,
            shipping_time=func.now(),
            driver_receive_time=func.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0
```

**Add new service functions** (After `pickup_order`, ~line 208):

```python
async def arrive_warehouse(
    session: AsyncSession,
    order_sn: str,
    driver_id: int
) -> bool:
    """
    Mark order as arrived at warehouse (shipping_status=3).
    Only for warehouse delivery (shipping_type=1).
    """
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.driver_id == driver_id)
        .where(Order.shipping_status == 2)  # Must be from "Driver Received"
        .where(Order.shipping_type == 1)    # Only warehouse delivery
        .values(
            shipping_status=3,
            arrive_warehouse_time=func.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def warehouse_ship(
    session: AsyncSession,
    order_sn: str
) -> bool:
    """
    Mark order as shipped from warehouse (shipping_status=4).
    Called by warehouse staff.
    """
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.shipping_status == 3)  # Must be from "Arrived Warehouse"
        .where(Order.shipping_type == 1)
        .values(
            shipping_status=4,
            warehouse_shipping_time=func.now()
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def complete_delivery(
    session: AsyncSession,
    order_sn: str,
    driver_id: int | None = None
) -> bool:
    """
    Mark order as delivered (shipping_status=5, order_status=3).
    Works for both delivery types.
    """
    stmt = (
        update(Order)
        .where(Order.order_sn == order_sn)
        .where(Order.shipping_status == 4)  # Must be from status 4
        .values(
            shipping_status=5,
            order_status=3,  # Completed
            finish_time=func.now()
        )
    )

    if driver_id:
        stmt = stmt.where(Order.driver_id == driver_id)

    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0
```

**Import `func` at top of file**:
```python
from sqlalchemy import or_, select, update, func  # Add func
```

---

### 3.3 Update `bff/app/services/delivery_proof_service.py`

**Modify `upload_delivery_proof` to use `tigu_uploaded_files`** and create action record.

Current implementation saves to `tigu_delivery_proof` table. We need to ALSO:
1. Save to `tigu_uploaded_files`
2. Create `OrderAction` record
3. Link file to action via `biz_id`

This will be a significant refactor - document this separately.

---

## Phase 4: Backend (BFF) - API Routes

### 4.1 Update `bff/app/api/v1/routes/orders.py`

**Modify imports** (Line 1-10):

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.models.order import Order
from app.schemas.order import OrderDetail, OrderSummary, ProofOfDelivery, ProofOfDeliveryResponse, UpdateShippingStatus
from app.schemas.order_action import PickupRequest, PickupResponse  # NEW
from app.services import order_service, delivery_proof_service, order_action_service  # Add order_action_service
```

**Modify `/pickup` endpoint** (Lines 53-75):

```python
@router.post("/{order_sn}/pickup", response_model=PickupResponse)
async def pickup_order(
    order_sn: str,
    payload: PickupRequest,  # NEW - now requires photo
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Driver picks up order from merchant.
    Sets shipping_status based on shipping_type:
    - shipping_type=1 (warehouse): status=2
    - shipping_type=0 (direct): status=4

    Requires photo evidence and creates order_action record.
    """
    # Get driver
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order to check shipping_type
    result = await session.execute(
        select(Order).where(Order.order_sn == order_sn)
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # 1. Upload photo to tigu_uploaded_files
    file_id = await delivery_proof_service.upload_photo(
        session=session,
        photo_data=payload.photo,
        order_sn=order_sn
    )

    # 2. Update order status
    picked_up = await order_service.pickup_order(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id,
        shipping_type=order.shipping_type
    )
    if not picked_up:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order already assigned"
        )

    # 3. Create order_action record
    new_status = 2 if order.shipping_type == 1 else 4
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,
        shipping_status=new_status,
        shipping_type=order.shipping_type,
        action_type=1,  # Driver Pickup
        file_ids=[file_id],
        create_by=f"driver_{driver.id}"
    )

    return PickupResponse(
        success=True,
        message="Order picked up successfully",
        order_sn=order_sn,
        shipping_status=new_status,
        action_id=action.id
    )
```

**Add new endpoint `/arrive-warehouse`** (After `/pickup`):

```python
@router.post("/{order_sn}/arrive-warehouse", response_model=PickupResponse)
async def arrive_warehouse(
    order_sn: str,
    payload: PickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Driver arrives at warehouse with goods.
    Only for warehouse delivery (shipping_type=1).
    Sets shipping_status=3.
    """
    # Get driver
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order
    result = await session.execute(
        select(Order).where(Order.order_sn == order_sn).where(Order.driver_id == driver.id)
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.shipping_type != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="arrive-warehouse only for warehouse delivery (shipping_type=1)"
        )

    # 1. Upload photo
    file_id = await delivery_proof_service.upload_photo(
        session=session,
        photo_data=payload.photo,
        order_sn=order_sn
    )

    # 2. Update order
    arrived = await order_service.arrive_warehouse(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id
    )
    if not arrived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid status transition"
        )

    # 3. Create action
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,
        shipping_status=3,
        shipping_type=1,
        action_type=2,  # Arrive Warehouse
        file_ids=[file_id],
        create_by=f"driver_{driver.id}"
    )

    return PickupResponse(
        success=True,
        message="Arrival at warehouse confirmed",
        order_sn=order_sn,
        shipping_status=3,
        action_id=action.id
    )
```

**Add new endpoint `/warehouse-ship`** (After `/arrive-warehouse`):

```python
@router.post("/{order_sn}/warehouse-ship", response_model=PickupResponse)
async def warehouse_ship(
    order_sn: str,
    payload: PickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PickupResponse:
    """
    Warehouse staff confirms shipment to end user.
    Only for warehouse delivery (shipping_type=1).
    Sets shipping_status=4.
    """
    # Get order
    result = await session.execute(
        select(Order).where(Order.order_sn == order_sn)
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.shipping_type != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="warehouse-ship only for warehouse delivery (shipping_type=1)"
        )

    # 1. Upload photo
    file_id = await delivery_proof_service.upload_photo(
        session=session,
        photo_data=payload.photo,
        order_sn=order_sn
    )

    # 2. Update order
    shipped = await order_service.warehouse_ship(
        session=session,
        order_sn=order_sn
    )
    if not shipped:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid status transition"
        )

    # 3. Create action
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=2,
        shipping_status=4,
        shipping_type=1,
        action_type=3,  # Warehouse Ships
        file_ids=[file_id],
        create_by=f"warehouse_staff_{current_user.user_id}"
    )

    return PickupResponse(
        success=True,
        message="Order shipped from warehouse",
        order_sn=order_sn,
        shipping_status=4,
        action_id=action.id
    )
```

**Modify `/proof` endpoint** (Lines 91-132):

Update to use new `complete_delivery` function and set shipping_status=5 (not 3):

```python
@router.post("/{order_sn}/proof", response_model=ProofOfDeliveryResponse, response_model_by_alias=True)
async def upload_proof_of_delivery(
    order_sn: str,
    payload: ProofOfDelivery,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> ProofOfDeliveryResponse:
    """
    Upload final delivery proof.
    Sets shipping_status=5, order_status=3 (Completed).
    """
    # Get driver
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get order
    result = await session.execute(
        select(Order).where(Order.order_sn == order_sn).where(Order.driver_id == driver.id)
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # 1. Upload photo
    file_id = await delivery_proof_service.upload_photo(
        session=session,
        photo_data=payload.photo,
        order_sn=order_sn
    )

    # 2. Update order to delivered
    completed = await order_service.complete_delivery(
        session=session,
        order_sn=order_sn,
        driver_id=driver.id
    )
    if not completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid status transition"
        )

    # 3. Create action
    action = await order_action_service.create_order_action(
        session=session,
        order_id=order.id,
        order_status=3,
        shipping_status=5,
        shipping_type=order.shipping_type,
        action_type=4,  # Complete
        file_ids=[file_id],
        create_by=f"driver_{driver.id}"
    )

    return ProofOfDeliveryResponse(
        status="uploaded",
        photo_url=f"https://api.wetigu.com/uploads/{order_sn}_{file_id}.jpg",  # Adjust based on actual storage
        order_sn=order_sn,
        uploaded_at=action.create_time
    )
```

---

## Phase 5: Frontend Changes

### 5.1 Update Types/Interfaces

**File**: `frontend/src/types/order.ts` (or create if doesn't exist)

```typescript
export interface Order {
  orderSn: string
  shippingStatus: number
  shippingType: number  // NEW: 0=User, 1=Warehouse
  orderStatus: number
  driverId?: number
  driverName?: string
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  receiverCity?: string
  receiverProvince?: string
  receiverPostalCode?: string
  shippingStatusLabel: string
  orderStatusLabel: string
  createTime: string

  // NEW timestamp fields:
  driverReceiveTime?: string
  arriveWarehouseTime?: string
  warehouseShippingTime?: string
  shippingTime?: string
  finishTime?: string

  pickupLocation?: {
    id: number
    name: string
    address: string
    latitude?: number
    longitude?: number
  }
  items: OrderItem[]
}

export interface OrderAction {
  id: number
  orderId: number
  orderStatus: number
  shippingStatus: number
  shippingType: number
  actionType: number
  logisticsVoucherFile?: string
  createTime: string
}
```

---

### 5.2 Update Store

**File**: `frontend/src/store/orders.ts`

Add new actions for warehouse workflow:

```typescript
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useOrderStore = defineStore('orders', {
  state: () => ({
    availableOrders: [] as Order[],
    assignedOrders: [] as Order[],
    currentOrder: null as Order | null
  }),

  actions: {
    // ... existing actions ...

    // NEW: Driver pickup with photo
    async pickupOrder(orderSn: string, photo: string, notes?: string) {
      const response = await api.post(`/orders/${orderSn}/pickup`, {
        photo,
        notes
      })
      return response.data
    },

    // NEW: Arrive at warehouse
    async arriveWarehouse(orderSn: string, photo: string, notes?: string) {
      const response = await api.post(`/orders/${orderSn}/arrive-warehouse`, {
        photo,
        notes
      })
      return response.data
    },

    // NEW: Warehouse ships
    async warehouseShip(orderSn: string, photo: string, notes?: string) {
      const response = await api.post(`/orders/${orderSn}/warehouse-ship`, {
        photo,
        notes
      })
      return response.data
    },

    // Existing complete delivery
    async completeDelivery(orderSn: string, photo: string, notes?: string) {
      const response = await api.post(`/orders/${orderSn}/proof`, {
        photo,
        notes
      })
      return response.data
    }
  }
})
```

---

### 5.3 Update Components

#### `OrderCard.vue` - Show shipping_type badge

Add visual indicator for delivery type:

```vue
<template>
  <div class="order-card">
    <!-- Existing content -->

    <!-- NEW: Delivery type badge -->
    <div class="delivery-type-badge" :class="deliveryTypeClass">
      {{ deliveryTypeLabel }}
    </div>

    <!-- Status timeline for warehouse delivery -->
    <div v-if="order.shippingType === 1" class="warehouse-timeline">
      <div class="timeline-step" :class="{ completed: order.driverReceiveTime }">
        ✓ Driver Pickup
      </div>
      <div class="timeline-step" :class="{ completed: order.arriveWarehouseTime }">
        {{ order.arriveWarehouseTime ? '✓' : '○' }} Arrive Warehouse
      </div>
      <div class="timeline-step" :class="{ completed: order.warehouseShippingTime }">
        {{ order.warehouseShippingTime ? '✓' : '○' }} Warehouse Ships
      </div>
      <div class="timeline-step" :class="{ completed: order.finishTime }">
        {{ order.finishTime ? '✓' : '○' }} Delivered
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  order: Order
}>()

const deliveryTypeLabel = computed(() => {
  return props.order.shippingType === 1 ? 'Via Warehouse' : 'Direct to User'
})

const deliveryTypeClass = computed(() => {
  return props.order.shippingType === 1 ? 'warehouse' : 'direct'
})
</script>
```

#### `OrderDetail.vue` - Add action buttons based on shipping_type

```vue
<template>
  <div class="order-detail">
    <!-- Existing content -->

    <!-- Action buttons based on workflow -->
    <div class="actions">
      <!-- Warehouse Delivery Path -->
      <template v-if="order.shippingType === 1">
        <button
          v-if="order.shippingStatus === 2"
          @click="showArriveWarehouseModal = true"
          class="btn-primary"
        >
          Arrive at Warehouse
        </button>

        <button
          v-if="order.shippingStatus === 3"
          @click="showWarehouseShipModal = true"
          class="btn-primary"
        >
          Warehouse Ship
        </button>

        <button
          v-if="order.shippingStatus === 4"
          @click="showCompleteModal = true"
          class="btn-success"
        >
          Complete Delivery
        </button>
      </template>

      <!-- Direct Delivery Path -->
      <template v-else-if="order.shippingType === 0">
        <button
          v-if="order.shippingStatus === 4"
          @click="showCompleteModal = true"
          class="btn-success"
        >
          Complete Delivery
        </button>
      </template>
    </div>

    <!-- Photo upload modals -->
    <PhotoUploadModal
      v-if="showArriveWarehouseModal"
      title="Arrive at Warehouse"
      @submit="handleArriveWarehouse"
      @cancel="showArriveWarehouseModal = false"
    />

    <PhotoUploadModal
      v-if="showWarehouseShipModal"
      title="Warehouse Ships"
      @submit="handleWarehouseShip"
      @cancel="showWarehouseShipModal = false"
    />

    <PhotoUploadModal
      v-if="showCompleteModal"
      title="Complete Delivery"
      @submit="handleComplete"
      @cancel="showCompleteModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useOrderStore } from '@/store/orders'

const orderStore = useOrderStore()
const showArriveWarehouseModal = ref(false)
const showWarehouseShipModal = ref(false)
const showCompleteModal = ref(false)

async function handleArriveWarehouse(photo: string, notes: string) {
  await orderStore.arriveWarehouse(props.order.orderSn, photo, notes)
  showArriveWarehouseModal.value = false
  // Refresh order
}

async function handleWarehouseShip(photo: string, notes: string) {
  await orderStore.warehouseShip(props.order.orderSn, photo, notes)
  showWarehouseShipModal.value = false
  // Refresh order
}

async function handleComplete(photo: string, notes: string) {
  await orderStore.completeDelivery(props.order.orderSn, photo, notes)
  showCompleteModal.value = false
  // Refresh order
}
</script>
```

#### Create `PhotoUploadModal.vue` (NEW COMPONENT)

Reusable modal for photo upload across all workflow steps:

```vue
<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <h2>{{ title }}</h2>

      <div class="photo-upload">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          @change="handlePhotoSelect"
          ref="photoInput"
        />

        <div v-if="photoPreview" class="photo-preview">
          <img :src="photoPreview" alt="Preview" />
        </div>

        <button v-else @click="$refs.photoInput.click()" class="btn-camera">
          📷 Take Photo
        </button>
      </div>

      <div class="notes-input">
        <label>Notes (optional)</label>
        <textarea
          v-model="notes"
          placeholder="Add delivery notes..."
          maxlength="1000"
        />
      </div>

      <div class="modal-actions">
        <button @click="$emit('cancel')" class="btn-secondary">
          Cancel
        </button>
        <button
          @click="handleSubmit"
          :disabled="!photoBase64"
          class="btn-primary"
        >
          Submit
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  title: string
}>()

const emit = defineEmits<{
  submit: [photo: string, notes: string]
  cancel: []
}>()

const photoBase64 = ref('')
const photoPreview = ref('')
const notes = ref('')

function handlePhotoSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    photoBase64.value = e.target?.result as string
    photoPreview.value = photoBase64.value
  }
  reader.readAsDataURL(file)
}

function handleSubmit() {
  if (!photoBase64.value) return
  emit('submit', photoBase64.value, notes.value)
}
</script>
```

---

## Phase 6: Testing Plan

### 6.1 Database Validation

```bash
# Verify tables exist
sudo mysql -e "USE tigu_b2b; SHOW TABLES LIKE 'tigu_order%';"

# Verify tigu_order fields
sudo mysql -e "USE tigu_b2b; DESCRIBE tigu_order;" | grep -E "(shipping_type|driver_receive|arrive_warehouse|warehouse_shipping)"

# Verify tigu_order_action structure
sudo mysql -e "USE tigu_b2b; DESCRIBE tigu_order_action;"

# Verify tigu_uploaded_files has biz_id
sudo mysql -e "USE tigu_b2b; DESCRIBE tigu_uploaded_files;" | grep biz_id
```

### 6.2 Backend Unit Tests

Create `bff/tests/test_order_action.py`:

```python
import pytest
from app.services import order_action_service

@pytest.mark.asyncio
async def test_create_order_action(db_session, test_order):
    """Test order action creation with file linking"""
    action = await order_action_service.create_order_action(
        session=db_session,
        order_id=test_order.id,
        order_status=2,
        shipping_status=2,
        shipping_type=1,
        action_type=1,
        file_ids=[12345],
        create_by="driver_5"
    )

    assert action.action_type == 1
    assert action.logistics_voucher_file == "12345"
    assert action.shipping_type == 1
```

### 6.3 API Integration Tests

```python
@pytest.mark.asyncio
async def test_pickup_warehouse_delivery(client, auth_headers, test_order):
    """Test pickup for warehouse delivery sets status=2"""
    response = await client.post(
        f"/api/v1/orders/{test_order.order_sn}/pickup",
        json={"photo": "data:image/jpeg;base64,fake", "notes": "Test"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["shippingStatus"] == 2  # Warehouse delivery
    assert "actionId" in data


@pytest.mark.asyncio
async def test_pickup_direct_delivery(client, auth_headers, test_order_direct):
    """Test pickup for direct delivery sets status=4"""
    response = await client.post(
        f"/api/v1/orders/{test_order_direct.order_sn}/pickup",
        json={"photo": "data:image/jpeg;base64,fake", "notes": "Test"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["shippingStatus"] == 4  # Direct delivery
```

### 6.4 Frontend E2E Tests (Cypress)

```typescript
describe('Warehouse Delivery Workflow', () => {
  it('should complete full warehouse delivery flow', () => {
    cy.login('driver')

    // 1. Pickup
    cy.visit('/orders/available')
    cy.contains('Warehouse Delivery').click()
    cy.get('[data-testid="pickup-btn"]').click()
    cy.uploadPhoto('pickup.jpg')
    cy.get('[data-testid="submit-btn"]').click()

    // 2. Arrive Warehouse
    cy.visit('/orders/assigned')
    cy.get('[data-testid="order-card"]').first().click()
    cy.get('[data-testid="arrive-warehouse-btn"]').click()
    cy.uploadPhoto('arrive.jpg')
    cy.get('[data-testid="submit-btn"]').click()

    // 3. Warehouse Ships (admin action - skip in driver test)

    // 4. Complete
    cy.get('[data-testid="complete-btn"]').click()
    cy.uploadPhoto('complete.jpg')
    cy.get('[data-testid="submit-btn"]').click()

    cy.contains('Delivery completed').should('be.visible')
  })
})
```

---

## Phase 7: Deployment Checklist

### Pre-Deployment

- [ ] Database schema verified (no migrations needed)
- [ ] All BFF unit tests pass
- [ ] All API integration tests pass
- [ ] Frontend E2E tests pass
- [ ] Code review completed
- [ ] Documentation updated

### Deployment Steps

1. **Backend (BFF)**
   ```bash
   cd /home/mli/tigub2b/tigub2b_delivery
   ./deploy_backend.sh
   ```

2. **Frontend**
   ```bash
   cd /home/mli/tigub2b/tigub2b_delivery
   ./deploy_frontend.sh
   ```

3. **Verify Deployment**
   ```bash
   # Check BFF health
   curl https://api.wetigu.com/health

   # Check frontend
   curl https://delivery.wetigu.com
   ```

### Post-Deployment Validation

- [ ] Test warehouse delivery workflow end-to-end
- [ ] Test direct delivery workflow end-to-end
- [ ] Verify order_action records created correctly
- [ ] Verify files linked via biz_id
- [ ] Monitor logs for errors
- [ ] Check database for orphaned records

---

## Summary of Changes

### Database (NO CHANGES - Already Exists)
- ✅ All tables and fields exist
- ✅ No migrations required

### Backend (BFF)
- **Models** (1 file modified, 1 new model):
  - `order.py`: Add 3 timestamp fields, add `OrderAction` model
- **Schemas** (1 file new, 1 modified):
  - NEW: `order_action.py`
  - MODIFIED: `order.py` - add timestamp fields
- **Services** (1 file new, 2 modified):
  - NEW: `order_action_service.py`
  - MODIFIED: `order_service.py` - add 4 new functions
  - MODIFIED: `delivery_proof_service.py` - integrate with uploaded_files
- **Routes** (1 file modified):
  - `orders.py`: Modify `/pickup`, add `/arrive-warehouse`, `/warehouse-ship`, modify `/proof`

### Frontend
- **Types** (1 file new/modified):
  - `types/order.ts`: Add new fields
- **Store** (1 file modified):
  - `store/orders.ts`: Add 3 new actions
- **Components** (1 new, 2 modified):
  - NEW: `PhotoUploadModal.vue`
  - MODIFIED: `OrderCard.vue` - show delivery type
  - MODIFIED: `OrderDetail.vue` - workflow-specific buttons

### Total File Count
- **Backend**: 7 files (1 new, 6 modified)
- **Frontend**: 4 files (1 new, 3 modified)
- **Tests**: 3 files (all new)

---

## Risk Assessment

### Low Risk
- ✅ Database already has all required structure
- ✅ Backward compatible (old orders still work)
- ✅ Photo upload already exists

### Medium Risk
- ⚠️ Status code changes require frontend updates
- ⚠️ New workflow requires driver training

### Mitigation
- Feature flag for new workflow (optional)
- Gradual rollout by warehouse
- Driver training materials
- Admin dashboard monitoring

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize implementation phases**
3. **Set up feature branch**: `feature/updated-workflow`
4. **Begin Phase 1**: Backend models
5. **Incremental testing** after each phase
6. **Staging deployment** before production

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Created By**: Claude Code Assistant
**Review Required**: Backend Lead, Frontend Lead, QA Lead
