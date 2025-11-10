# Delivery System Refactoring Plan

**Project**: Tigub2b Delivery Management System
**Date Created**: 2025-11-09
**Based On**: delivery-process-zh.md, IMPLEMENTATION_PLAN.md, Current Codebase Analysis
**Author**: System Architect
**Status**: Draft for Review

---

## Executive Summary

This document outlines a comprehensive refactoring plan to align the current delivery system implementation with the complete business requirements documented in `delivery-process-zh.md`. The refactoring addresses critical gaps between the documented workflows and current implementation.

### Key Findings

1. **Documentation Discrepancy**: Two different workflow interpretations exist
   - `delivery-process-zh.md`: 4 workflows based on delivery_type + shipping_type combination
   - `DRIVER_WORKFLOW_GUIDE_UPDATED.md`: 2 workflows based on shipping_type only

2. **Missing Database Models**: Critical tables not yet modeled
   - `tigu_prepare_goods` (备货表)
   - `tigu_prepare_goods_item` (备货明细表)
   - `tigu_order_action` (订单操作记录表)

3. **Incomplete Order Model**: Missing fields for complete workflow tracking
   - Timestamp fields for workflow stages
   - Prepare goods relationship
   - Action history relationship

4. **Business Process Gap**: Current implementation focuses only on driver delivery workflow, missing:
   - Merchant preparation workflow
   - Warehouse receiving workflow
   - Complete audit trail with file linking

---

## Problem Analysis

### Current State

#### Backend (BFF Layer)
- **Location**: `/home/mli/tigub2b/tigub2b_delivery/bff/`
- **Framework**: FastAPI + SQLAlchemy (async)
- **Database**: MySQL (tigu_b2b)

**Existing Models**:
```
✓ Order (tigu_order)
✓ OrderItem (tigu_order_item)
✓ Warehouse (tigu_warehouse)
✓ Driver (tigu_driver)
✓ DeliveryProof (tigu_delivery_proof)
✓ UploadedFile (tigu_uploaded_files)
✓ User (tigu_user)
✓ DriverPerformance (tigu_driver_performance)
```

**Missing Models**:
```
✗ PrepareGoods (tigu_prepare_goods)
✗ PrepareGoodsItem (tigu_prepare_goods_item)
✗ OrderAction (tigu_order_action)
```

#### Frontend
- **Location**: `/home/mli/tigub2b/tigub2b_delivery/frontend/`
- **Framework**: Vue 3 + TypeScript + Capacitor
- **State**: Pinia stores

**Current Views**:
- Driver task board
- Route planner
- Order details
- Admin dashboard

**Missing UI**:
- Merchant prepare goods workflow
- Warehouse receiving workflow
- Complete status timeline visualization
- Action audit trail display

### Target State

Complete implementation of all 4 delivery workflows as documented in `delivery-process-zh.md`:

1. **Merchant Self-Delivery → Warehouse** (delivery_type=0, shipping_type=0)
2. **Merchant Self-Delivery → User** (delivery_type=0, shipping_type=1)
3. **Third-Party Delivery → Warehouse** (delivery_type=1, shipping_type=0)
4. **Third-Party Delivery → User** (delivery_type=1, shipping_type=1)

---

## Refactoring Strategy

### Approach: Incremental Enhancement

We'll use a **phased rollout approach** to minimize risk while delivering value incrementally:

- **Phase 1**: Database models and core infrastructure (Backend)
- **Phase 2**: Service layer refactoring (Backend)
- **Phase 3**: API endpoint updates (Backend)
- **Phase 4**: Frontend workflow implementation
- **Phase 5**: Integration testing and validation
- **Phase 6**: Deployment and migration

### Design Principles

1. **Backward Compatibility**: Existing orders must continue to function
2. **Data Integrity**: All workflow transitions require photo evidence
3. **Audit Trail**: Complete history in tigu_order_action table
4. **Workflow Flexibility**: Support all 4 delivery types
5. **Status Consistency**: Clear state machine for each workflow
6. **Separation of Concerns**: Prepare goods vs. delivery tracking

---

## Detailed Phase Plan

## Phase 1: Database Models & Infrastructure (Week 1)

**Goal**: Create missing database models and update existing ones

### 1.1 Create PrepareGoods Model

**File**: `bff/app/models/prepare_goods.py` (NEW)

```python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class PrepareGoods(Base):
    """
    备货表 (tigu_prepare_goods)
    Tracks prepared packages for driver delivery
    """
    __tablename__ = "tigu_prepare_goods"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    prepare_sn: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="备货单号")

    # Linked orders (one prepare package can contain multiple orders)
    order_ids: Mapped[str] = mapped_column(Text, comment="订单ID列表(逗号分隔)")

    # Delivery configuration
    delivery_type: Mapped[int] = mapped_column(Integer, default=0, comment="配送方式: 0=商家自配, 1=第三方配送")
    shipping_type: Mapped[int] = mapped_column(Integer, default=0, comment="发货类型: 0=发仓库, 1=发用户")

    # Status tracking
    prepare_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="备货状态: NULL=待备货, 0=已备货, 1=司机收货中, 2=司机送达仓库, 3=仓库已收货, 4=司机配送用户, 5=已送达, 6=完成"
    )

    # Merchant info
    shop_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), index=True, comment="商家ID")

    # Warehouse (if applicable)
    warehouse_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_warehouse.id"),
        nullable=True,
        comment="目标仓库ID"
    )

    # Driver (if third-party delivery)
    driver_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_driver.id"),
        nullable=True,
        comment="司机ID"
    )

    # Timestamps
    create_time: Mapped[datetime] = mapped_column(DateTime(), comment="创建时间")
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True, comment="更新时间")

    # Relationships
    items: Mapped[list[PrepareGoodsItem]] = relationship("PrepareGoodsItem", back_populates="prepare_goods", lazy="selectin")
    warehouse: Mapped[Warehouse | None] = relationship("Warehouse", lazy="joined")
    driver: Mapped[Driver | None] = relationship("Driver", lazy="joined")


class PrepareGoodsItem(Base):
    """
    备货明细表 (tigu_prepare_goods_item)
    Items in prepared packages for detailed display
    """
    __tablename__ = "tigu_prepare_goods_item"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    prepare_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_prepare_goods.id"),
        index=True,
        comment="备货单ID"
    )
    order_item_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_order_item.id"),
        comment="订单明细ID"
    )

    # Item details (denormalized for performance)
    product_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    sku_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    quantity: Mapped[int] = mapped_column(Integer, comment="数量")

    # Timestamps
    create_time: Mapped[datetime] = mapped_column(DateTime())

    # Relationships
    prepare_goods: Mapped[PrepareGoods] = relationship("PrepareGoods", back_populates="items")
    order_item: Mapped[OrderItem] = relationship("OrderItem", lazy="joined")
```

**Database Validation**:
```sql
-- Verify tables exist
SHOW TABLES LIKE 'tigu_prepare_goods%';

-- Verify structure
DESCRIBE tigu_prepare_goods;
DESCRIBE tigu_prepare_goods_item;
```

---

### 1.2 Create OrderAction Model

**File**: `bff/app/models/order_action.py` (NEW)

```python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class OrderAction(Base):
    """
    订单操作记录表 (tigu_order_action)

    Complete audit trail for all order workflow transitions.
    Each status change creates a new action record with photo evidence.

    Action Type Codes:
    - 0: 备货 (Goods Prepared)
    - 1: 司机收货 (Driver Pickup)
    - 2: 司机送达仓库 (Driver Arrives Warehouse)
    - 3: 仓库收货 (Warehouse Receives)
    - 4: 仓库发货 (Warehouse Ships)
    - 5: 完成 (Delivery Complete)
    - 6: 用户申请退款 (Refund Requested)
    - 7: 商家允许退货 (Return Approved)
    - 8: 商家不允许退货 (Return Denied)
    - 9: 商家同意退款 (Refund Approved)
    - 10: 商家拒绝退款 (Refund Denied)
    - 11: 用户退货凭证 (Return Evidence)
    - 12: 司机送达仓库 (Driver Delivers to Warehouse) - alternative to action 2
    """
    __tablename__ = "tigu_order_action"

    # Snowflake ID for distributed system
    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, comment="雪花算法ID")

    # Order reference
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_order.id"),
        index=True,
        comment="订单ID"
    )

    # Status snapshot at time of action
    order_status: Mapped[int] = mapped_column(Integer, comment="订单状态快照")
    shipping_status: Mapped[int] = mapped_column(Integer, comment="配送状态快照")

    # Action details
    action_type: Mapped[int] = mapped_column(Integer, index=True, comment="操作类型(0-12)")

    # File evidence (comma-separated file IDs from tigu_uploaded_files)
    logistics_voucher_file: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="物流凭证文件ID列表(逗号分隔)"
    )

    # Audit fields
    create_by: Mapped[str] = mapped_column(String(64), comment="创建人(操作人)")
    create_time: Mapped[datetime] = mapped_column(DateTime(), comment="创建时间")
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="更新人")
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True, comment="更新时间")
    remark: Mapped[str | None] = mapped_column(String(5000), nullable=True, comment="备注")

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="actions", lazy="joined")
```

**Database Validation**:
```sql
-- Verify table structure
DESCRIBE tigu_order_action;

-- Check indexes
SHOW INDEX FROM tigu_order_action;
```

---

### 1.3 Update Order Model

**File**: `bff/app/models/order.py` (MODIFY)

**Add missing fields** (around line 48-52):

```python
class Order(Base):
    __tablename__ = "tigu_order"

    # ... existing fields ...

    # ADD: Delivery configuration
    delivery_type: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="配送方式: 0=商家自配, 1=第三方配送"
    )

    # MODIFY: Ensure shipping_type exists (may already be there)
    shipping_type: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="发货类型: 0=发仓库, 1=发用户"
    )

    # ADD: Workflow timestamp fields
    driver_receive_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="司机收货时间"
    )
    arrive_warehouse_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="到达仓库时间"
    )
    warehouse_shipping_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="仓库发货时间"
    )

    # ... existing fields ...

    # ADD: New relationships
    actions: Mapped[list[OrderAction]] = relationship(
        "OrderAction",
        back_populates="order",
        lazy="selectin",
        order_by="OrderAction.create_time.desc()"
    )
```

---

### 1.4 Update UploadedFile Model

**File**: `bff/app/models/order.py` (MODIFY)

Ensure UploadedFile has `biz_type` and `biz_id` for linking to OrderAction:

```python
class UploadedFile(Base):
    __tablename__ = "tigu_uploaded_files"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    file_url: Mapped[str] = mapped_column(String(500))

    # Business entity linking
    biz_type: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="业务类型: order_action, product_sku, etc."
    )
    biz_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
        index=True,  # ADD INDEX
        comment="业务ID(关联tigu_order_action.id等)"
    )

    is_main: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
```

---

### 1.5 Import Updates

**File**: `bff/app/models/__init__.py` (MODIFY)

Add new models to imports:

```python
from app.models.order import Order, OrderItem, Warehouse, UploadedFile
from app.models.order_action import OrderAction  # NEW
from app.models.prepare_goods import PrepareGoods, PrepareGoodsItem  # NEW
from app.models.driver import Driver
from app.models.delivery_proof import DeliveryProof
from app.models.user import User
from app.models.driver_performance import DriverPerformance

__all__ = [
    "Order",
    "OrderItem",
    "Warehouse",
    "UploadedFile",
    "OrderAction",  # NEW
    "PrepareGoods",  # NEW
    "PrepareGoodsItem",  # NEW
    "Driver",
    "DeliveryProof",
    "User",
    "DriverPerformance",
]
```

---

## Phase 2: Service Layer Refactoring (Week 2)

**Goal**: Create service layer for new models and refactor existing services

### 2.1 Create PrepareGoodsService

**File**: `bff/app/services/prepare_goods_service.py` (NEW)

```python
"""
Service for managing merchant prepare goods workflow.
Handles package preparation and status updates.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.prepare_goods import PrepareGoods, PrepareGoodsItem
from app.models.order import Order


async def create_prepare_package(
    session: AsyncSession,
    order_ids: List[int],
    shop_id: int,
    delivery_type: int,
    shipping_type: int,
    warehouse_id: int | None = None
) -> PrepareGoods:
    """
    Merchant creates prepare goods package for one or more orders.

    Args:
        session: Database session
        order_ids: List of order IDs to include in package
        shop_id: Merchant shop ID
        delivery_type: 0=Merchant self-delivery, 1=Third-party driver
        shipping_type: 0=To warehouse, 1=To user
        warehouse_id: Target warehouse (if shipping_type=0)

    Returns:
        Created PrepareGoods instance
    """
    # Generate prepare SN (simplified - use actual business logic)
    from time import time_ns
    prepare_sn = f"PREP{int(time_ns() / 1000000)}"

    # Create prepare goods record
    prepare_goods = PrepareGoods(
        prepare_sn=prepare_sn,
        order_ids=",".join(str(oid) for oid in order_ids),
        delivery_type=delivery_type,
        shipping_type=shipping_type,
        prepare_status=None,  # NULL = pending prepare
        shop_id=shop_id,
        warehouse_id=warehouse_id,
        create_time=datetime.now()
    )

    session.add(prepare_goods)
    await session.flush()

    # Fetch order items and create prepare_goods_item records
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id.in_(order_ids))
    )
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()

    for order in orders:
        for item in order.items:
            prepare_item = PrepareGoodsItem(
                prepare_id=prepare_goods.id,
                order_item_id=item.id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                quantity=item.quantity,
                create_time=datetime.now()
            )
            session.add(prepare_item)

    await session.commit()
    await session.refresh(prepare_goods)

    return prepare_goods


async def update_prepare_status(
    session: AsyncSession,
    prepare_sn: str,
    new_status: int
) -> bool:
    """
    Update prepare goods status.

    Status values:
    - NULL: 待备货 (Pending prepare)
    - 0: 已备货 (Prepared - merchant photo uploaded)
    - 1: 司机收货中 (Driver pickup - driver photo)
    - 2: 司机送达仓库 (Driver delivered to warehouse - driver photo)
    - 3: 仓库已收货 (Warehouse received - warehouse photo)
    - 4: 司机配送用户 (Driver delivering to user - driver photo)
    - 5: 已送达 (Delivered to user - driver photo)
    - 6: 完成 (Complete)
    """
    stmt = (
        update(PrepareGoods)
        .where(PrepareGoods.prepare_sn == prepare_sn)
        .values(prepare_status=new_status, update_time=datetime.now())
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def get_prepare_package(
    session: AsyncSession,
    prepare_sn: str
) -> PrepareGoods | None:
    """Get prepare package by SN with all items"""
    stmt = (
        select(PrepareGoods)
        .options(
            selectinload(PrepareGoods.items).selectinload(PrepareGoodsItem.order_item),
            selectinload(PrepareGoods.warehouse),
            selectinload(PrepareGoods.driver)
        )
        .where(PrepareGoods.prepare_sn == prepare_sn)
    )
    result = await session.execute(stmt)
    return result.scalars().first()
```

---

### 2.2 Create OrderActionService

**File**: `bff/app/services/order_action_service.py` (NEW)

Already outlined in IMPLEMENTATION_PLAN.md (Phase 3.1), implement as specified with enhancements:

```python
"""
Service for managing order action audit trail.
Creates action records for each workflow transition with photo evidence.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_action import OrderAction
from app.models.order import UploadedFile


async def create_order_action(
    session: AsyncSession,
    order_id: int,
    order_status: int,
    shipping_status: int,
    action_type: int,
    file_ids: List[int] | None = None,
    create_by: str = "system",
    remark: str | None = None
) -> OrderAction:
    """
    Create order action record with file linking.

    Args:
        session: Database session
        order_id: Order ID
        order_status: Current order_status snapshot
        shipping_status: Current shipping_status snapshot
        action_type: Action type code (0-12)
        file_ids: List of uploaded file IDs for evidence
        create_by: Creator identifier (driver_id, merchant_id, etc.)
        remark: Additional notes

    Returns:
        Created OrderAction instance
    """
    # Generate snowflake ID (simplified)
    from time import time_ns
    action_id = int(time_ns() / 1000000)

    # Prepare logistics_voucher_file (comma-separated)
    voucher_file = ",".join(str(fid) for fid in file_ids) if file_ids else None

    # Create action record
    stmt = insert(OrderAction).values(
        id=action_id,
        order_id=order_id,
        order_status=order_status,
        shipping_status=shipping_status,
        action_type=action_type,
        logistics_voucher_file=voucher_file,
        create_by=create_by,
        create_time=datetime.now(),
        remark=remark
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

    # Fetch and return
    result = await session.execute(
        select(OrderAction).where(OrderAction.id == action_id)
    )
    return result.scalar_one()


async def get_order_actions(
    session: AsyncSession,
    order_id: int
) -> List[OrderAction]:
    """Get complete action history for an order"""
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
) -> List[UploadedFile]:
    """Get all photo evidence files for an action"""
    stmt = (
        select(UploadedFile)
        .where(UploadedFile.biz_id == action_id)
        .where(UploadedFile.biz_type == "order_action")
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

---

### 2.3 Update OrderService

**File**: `bff/app/services/order_service.py` (MODIFY)

Add new workflow functions as outlined in IMPLEMENTATION_PLAN.md Phase 3.2:

1. Update shipping status labels
2. Update `pickup_order` to consider delivery_type + shipping_type
3. Add `arrive_warehouse` function
4. Add `warehouse_ship` function
5. Add `complete_delivery` function

---

## Phase 3: API Endpoints (Week 3)

**Goal**: Create and update API endpoints for all workflows

### 3.1 Create Prepare Goods Endpoints (Merchant Admin)

**File**: `bff/app/api/v1/routes/prepare_goods.py` (NEW)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.prepare_goods import (
    PrepareGoodsCreate,
    PrepareGoodsResponse,
    PrepareGoodsStatusUpdate
)
from app.services import prepare_goods_service

router = APIRouter()


@router.post("/", response_model=PrepareGoodsResponse)
async def create_prepare_package(
    payload: PrepareGoodsCreate,
    current_user=Depends(deps.get_current_merchant_user),  # Merchant auth
    session: AsyncSession = Depends(deps.get_db_session)
) -> PrepareGoodsResponse:
    """
    Merchant creates prepare goods package for delivery.
    Combines multiple orders into one package with delivery configuration.
    """
    package = await prepare_goods_service.create_prepare_package(
        session=session,
        order_ids=payload.order_ids,
        shop_id=current_user.shop_id,
        delivery_type=payload.delivery_type,
        shipping_type=payload.shipping_type,
        warehouse_id=payload.warehouse_id
    )
    return PrepareGoodsResponse.from_orm(package)


@router.post("/{prepare_sn}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_prepare(
    prepare_sn: str,
    payload: PhotoUpload,  # Base64 photo + notes
    current_user=Depends(deps.get_current_merchant_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Merchant marks prepare goods as complete with photo evidence.
    Sets prepare_status = 0 (已备货)
    """
    # Upload photo
    # Update prepare status
    # Create order_action record
    pass


@router.get("/{prepare_sn}", response_model=PrepareGoodsResponse)
async def get_prepare_package(
    prepare_sn: str,
    current_user=Depends(deps.get_current_merchant_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PrepareGoodsResponse:
    """Get prepare package details"""
    package = await prepare_goods_service.get_prepare_package(session, prepare_sn)
    if not package:
        raise HTTPException(status_code=404, detail="Prepare package not found")
    return PrepareGoodsResponse.from_orm(package)
```

---

### 3.2 Update Order Endpoints

**File**: `bff/app/api/v1/routes/orders.py` (MODIFY)

Implement all endpoint updates as outlined in IMPLEMENTATION_PLAN.md Phase 4.1:

1. Modify `/pickup` endpoint
2. Add `/arrive-warehouse` endpoint
3. Add `/warehouse-ship` endpoint
4. Modify `/proof` endpoint

---

## Phase 4: Frontend Implementation (Week 4-5)

**Goal**: Implement UI for all 4 workflows

### 4.1 Merchant Admin Prepare Goods UI

**New Views**:
- `PrepareGoodsCreate.vue` - Create prepare package
- `PrepareGoodsList.vue` - List merchant's prepare packages
- `PrepareGoodsDetail.vue` - Package detail with action timeline

**Components**:
- `DeliveryTypeSelector.vue` - Choose delivery_type + shipping_type
- `OrderSelector.vue` - Multi-select orders for packaging
- `PreparePhotoUpload.vue` - Upload preparation photo

---

### 4.2 Driver Workflow Enhancement

**Update Existing Views**:
- `AvailableOrders.vue` - Filter by delivery_type
- `TaskBoard.vue` - Show workflow path based on shipping_type
- `OrderDetail.vue` - Dynamic action buttons based on prepare_status

**Add Workflow Path Visualization**:
```vue
<template>
  <div class="workflow-timeline">
    <!-- Workflow 1: Merchant → Warehouse -->
    <template v-if="deliveryType === 0 && shippingType === 0">
      <WorkflowStep :completed="prepareStatus >= 0" icon="📦">
        Merchant Prepared
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 3" icon="🏭">
        Delivered to Warehouse
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 4" icon="🚚">
        Warehouse Shipped
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 6" icon="✅">
        Delivered to User
      </WorkflowStep>
    </template>

    <!-- Workflow 2: Merchant → User -->
    <template v-else-if="deliveryType === 0 && shippingType === 1">
      <WorkflowStep :completed="prepareStatus >= 0" icon="📦">
        Merchant Prepared
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 5" icon="🚚">
        Shipped to User
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 6" icon="✅">
        Delivered
      </WorkflowStep>
    </template>

    <!-- Workflow 3: Driver → Warehouse -->
    <template v-else-if="deliveryType === 1 && shippingType === 0">
      <WorkflowStep :completed="prepareStatus >= 0" icon="📦">
        Goods Ready
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 1" icon="🚗">
        Driver Pickup
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 2" icon="🏭">
        Arrive Warehouse
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 3" icon="✓">
        Warehouse Received
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 4" icon="🚚">
        Warehouse Ships
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 6" icon="✅">
        Delivered
      </WorkflowStep>
    </template>

    <!-- Workflow 4: Driver → User -->
    <template v-else-if="deliveryType === 1 && shippingType === 1">
      <WorkflowStep :completed="prepareStatus >= 0" icon="📦">
        Goods Ready
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 1" icon="🚗">
        Driver Pickup
      </WorkflowStep>
      <WorkflowStep :completed="prepareStatus >= 5" icon="✅">
        Delivered to User
      </WorkflowStep>
    </template>
  </div>
</template>
```

---

### 4.3 Warehouse Admin UI

**New Views**:
- `WarehouseReceiving.vue` - Receive goods from merchants/drivers
- `WarehouseShipping.vue` - Ship goods to end users
- `WarehouseInventory.vue` - Track received packages

---

### 4.4 Admin Audit Trail

**New Components**:
- `OrderActionTimeline.vue` - Visual timeline of all actions
- `ActionPhotoGallery.vue` - Display all photo evidence
- `WorkflowAnalytics.vue` - Analytics by delivery_type + shipping_type

---

## Phase 5: Integration Testing (Week 6)

### 5.1 Unit Tests

**Backend Tests**:
```
tests/unit/
├── test_prepare_goods_service.py
├── test_order_action_service.py
├── test_order_service_refactored.py
└── test_workflow_state_machine.py
```

**Test Coverage Goals**:
- PrepareGoods CRUD: 90%+
- OrderAction creation and linking: 95%+
- Workflow state transitions: 100%
- File linking logic: 100%

---

### 5.2 Integration Tests

**API Tests**:
```
tests/integration/
├── test_workflow_1_merchant_warehouse.py
├── test_workflow_2_merchant_user.py
├── test_workflow_3_driver_warehouse.py
└── test_workflow_4_driver_user.py
```

**Test Scenarios**:
1. Complete Workflow 1 (merchant self → warehouse → user)
2. Complete Workflow 2 (merchant self → user)
3. Complete Workflow 3 (driver → warehouse → user)
4. Complete Workflow 4 (driver → user)
5. Invalid state transitions
6. Missing photo evidence
7. Concurrent driver assignment

---

### 5.3 E2E Tests

**Cypress Tests**:
```javascript
describe('4 Delivery Workflows', () => {
  it('Workflow 1: Merchant self-delivery to warehouse', () => {
    // Merchant creates prepare package
    // Merchant uploads completion photo
    // Warehouse receives goods
    // Warehouse ships to user
    // Verify complete action trail
  })

  it('Workflow 2: Merchant self-delivery to user', () => {
    // Merchant prepares and ships directly
    // Verify simplified workflow
  })

  it('Workflow 3: Driver delivery to warehouse', () => {
    // Driver picks up
    // Driver delivers to warehouse
    // Warehouse receives and ships
    // Final delivery
  })

  it('Workflow 4: Driver delivery to user', () => {
    // Driver picks up and delivers directly
    // Verify shortest workflow path
  })
})
```

---

## Phase 6: Deployment & Migration (Week 7)

### 6.1 Database Migration

**Strategy**: Zero-downtime migration using shadow tables

```sql
-- Step 1: Verify all tables exist
SHOW TABLES LIKE 'tigu_%';

-- Step 2: Add new indexes
ALTER TABLE tigu_order ADD INDEX idx_delivery_shipping_type (delivery_type, shipping_type);
ALTER TABLE tigu_uploaded_files ADD INDEX idx_biz_id (biz_id);

-- Step 3: Backfill delivery_type for existing orders (optional)
UPDATE tigu_order
SET delivery_type = 1  -- Assume third-party delivery for existing orders
WHERE delivery_type IS NULL;

-- Step 4: Create initial prepare_goods records for active orders (optional)
-- This is optional depending on business requirements
```

---

### 6.2 Feature Flags

Implement progressive rollout:

```python
# config.py
FEATURE_FLAGS = {
    "PREPARE_GOODS_ENABLED": True,
    "MERCHANT_SELF_DELIVERY_ENABLED": True,
    "WAREHOUSE_WORKFLOW_ENABLED": True,
    "AUDIT_TRAIL_ENABLED": True
}
```

Frontend:
```typescript
// featureFlags.ts
export const FEATURES = {
  prepareGoods: import.meta.env.VITE_FEATURE_PREPARE_GOODS === 'true',
  merchantWorkflow: import.meta.env.VITE_FEATURE_MERCHANT_WORKFLOW === 'true'
}
```

---

### 6.3 Deployment Checklist

**Pre-Deployment**:
- [ ] All unit tests pass (90%+ coverage)
- [ ] All integration tests pass
- [ ] E2E tests pass for all 4 workflows
- [ ] Database indexes created
- [ ] Feature flags configured
- [ ] Rollback plan documented
- [ ] Monitoring dashboards created

**Deployment Steps**:
1. Deploy backend (BFF) with feature flags OFF
2. Verify health checks
3. Enable PREPARE_GOODS_ENABLED flag
4. Monitor for errors (24 hours)
5. Deploy frontend
6. Enable remaining feature flags gradually
7. Full system validation

**Post-Deployment**:
- [ ] Monitor error rates
- [ ] Check database performance
- [ ] Validate photo uploads working
- [ ] Verify all 4 workflows functional
- [ ] User acceptance testing

---

## Implementation Timeline

### Week 1: Phase 1 - Database Models
- Day 1-2: Create PrepareGoods models
- Day 3: Create OrderAction model
- Day 4: Update Order model
- Day 5: Unit tests for models

### Week 2: Phase 2 - Service Layer
- Day 1-2: PrepareGoodsService
- Day 3: OrderActionService
- Day 4-5: Update OrderService

### Week 3: Phase 3 - API Endpoints
- Day 1-2: Prepare goods endpoints
- Day 3-4: Update order endpoints
- Day 5: API integration tests

### Week 4-5: Phase 4 - Frontend
- Week 4: Merchant admin UI
- Week 5: Driver workflow + Warehouse UI

### Week 6: Phase 5 - Testing
- Day 1-3: Complete all unit tests
- Day 4-5: E2E testing all workflows

### Week 7: Phase 6 - Deployment
- Day 1-2: Database migration
- Day 3: Backend deployment
- Day 4: Frontend deployment
- Day 5: Validation and monitoring

---

## Risk Assessment

### High Risk Items

1. **Database Schema Discrepancy**
   - **Risk**: tigu_prepare_goods table may not exist as documented
   - **Mitigation**: Validate database schema before Phase 1
   - **Fallback**: Create migration scripts

2. **Workflow Complexity**
   - **Risk**: 4 different workflows increases testing surface
   - **Mitigation**: State machine validation, comprehensive tests
   - **Fallback**: Feature flags for gradual rollout

3. **Photo Upload at Scale**
   - **Risk**: Large photo files may cause performance issues
   - **Mitigation**: Image compression, CDN integration
   - **Fallback**: Queue-based async upload

### Medium Risk Items

1. **Backward Compatibility**
   - **Risk**: Existing orders may break with new fields
   - **Mitigation**: Nullable fields, default values
   - **Fallback**: Shadow deployment

2. **State Machine Transitions**
   - **Risk**: Invalid state transitions could corrupt data
   - **Mitigation**: Database constraints, validation layer
   - **Fallback**: Action log for rollback

---

## Success Metrics

### Technical Metrics
- **Test Coverage**: ≥90% for new code
- **API Response Time**: <200ms for order operations
- **Photo Upload Success Rate**: ≥99%
- **Database Query Performance**: <50ms for order queries

### Business Metrics
- **Workflow Completion Rate**: ≥95% for all 4 workflows
- **Photo Evidence Compliance**: 100% (all transitions have photos)
- **Audit Trail Completeness**: 100% (no missing action records)
- **User Adoption**: 80% of merchants use prepare goods feature within 1 month

---

## Appendix A: Status Code Reference

### prepare_status (备货状态)

| Code | Label | Description |
|------|-------|-------------|
| `NULL` | 待备货 | Pending prepare (merchant not yet finished) |
| `0` | 已备货 | Prepared (merchant uploaded photo) |
| `1` | 司机收货中 | Driver pickup (driver uploaded photo) |
| `2` | 司机送达仓库 | Driver delivered to warehouse (driver photo) |
| `3` | 仓库已收货 | Warehouse received (warehouse photo) |
| `4` | 司机配送用户 | Driver delivering to user (for workflow 4) |
| `5` | 已送达 | Delivered to user (final photo) |
| `6` | 订单完成 | Order complete |

### action_type (操作类型)

| Code | Label | Workflow | Actor |
|------|-------|----------|-------|
| `0` | 备货 | All | Merchant |
| `1` | 司机收货 | 3, 4 | Driver |
| `2` | 司机送达仓库 | 3 | Driver |
| `3` | 仓库收货 | 1, 3 | Warehouse |
| `4` | 仓库发货 | 1, 3 | Warehouse |
| `5` | 完成 | All | Driver/Merchant |
| `6` | 用户申请退款 | All | User |
| `7` | 商家允许退货 | All | Merchant |
| `8` | 商家不允许退货 | All | Merchant |
| `9` | 商家同意退款 | All | Merchant |
| `10` | 商家拒绝退款 | All | Merchant |
| `11` | 用户退货凭证 | All | User |

---

## Appendix B: Workflow State Machines

### Workflow 1: Merchant Self → Warehouse → User

```
prepare_status transitions:
NULL → 0 (merchant prepare photo)
     → 3 (warehouse receive photo)
     → 4 (warehouse ship photo)
     → 5 (delivery photo)
     → 6 (complete)

Required actions:
- action_type 0 (merchant prepare)
- action_type 3 (warehouse receive)
- action_type 4 (warehouse ship)
- action_type 5 (complete delivery)
```

### Workflow 2: Merchant Self → User

```
prepare_status transitions:
NULL → 0 (merchant prepare photo)
     → 5 (merchant delivery photo)
     → 6 (complete)

Required actions:
- action_type 0 (merchant prepare)
- action_type 5 (complete delivery)
```

### Workflow 3: Driver → Warehouse → User

```
prepare_status transitions:
NULL → 0 (merchant prepare)
     → 1 (driver pickup photo)
     → 2 (driver warehouse delivery photo)
     → 3 (warehouse receive photo)
     → 4 (warehouse ship photo)
     → 5 (final delivery photo)
     → 6 (complete)

Required actions:
- action_type 0 (merchant prepare)
- action_type 1 (driver pickup)
- action_type 2 (driver to warehouse)
- action_type 3 (warehouse receive)
- action_type 4 (warehouse ship)
- action_type 5 (complete)
```

### Workflow 4: Driver → User

```
prepare_status transitions:
NULL → 0 (merchant prepare)
     → 1 (driver pickup photo)
     → 5 (driver delivery photo)
     → 6 (complete)

Required actions:
- action_type 0 (merchant prepare)
- action_type 1 (driver pickup)
- action_type 5 (complete)
```

---

## Appendix C: File Linking Pattern

**Complete Photo Upload Flow**:

```python
# 1. Upload photo to storage and create file record
file_record = UploadedFile(
    id=SNOWFLAKE_ID,
    file_url="/uploads/photo.jpg",
    file_size=123456,
    file_type="image/jpeg",
    biz_id=None,  # Not yet linked
    biz_type=None
)
session.add(file_record)
await session.flush()  # Get file_id

# 2. Update order/prepare_goods status
await update_order_status(...)

# 3. Create order_action record
action = await create_order_action(
    order_id=order.id,
    action_type=1,
    file_ids=[file_record.id],
    ...
)

# 4. Link file to action via biz_id
await session.execute(
    UploadedFile.__table__.update()
    .where(UploadedFile.id == file_record.id)
    .values(biz_id=action.id, biz_type="order_action")
)

await session.commit()
```

**Query Pattern**:

```python
# Get all photos for an order
actions = await get_order_actions(session, order_id)
for action in actions:
    files = await get_action_files(session, action.id)
    # Display photos in timeline
```

---

## Conclusion

This refactoring plan provides a comprehensive, phased approach to implementing the complete delivery workflow system as documented in `delivery-process-zh.md`. By following this plan, we will:

1. ✅ Support all 4 delivery workflows
2. ✅ Maintain complete audit trail with photo evidence
3. ✅ Ensure backward compatibility with existing orders
4. ✅ Implement proper state machine validation
5. ✅ Provide rich UI for all user roles (merchant, driver, warehouse, admin)
6. ✅ Enable comprehensive analytics and reporting

**Next Steps**:
1. Review this plan with technical leads
2. Validate database schema against production
3. Get approval for 7-week timeline
4. Begin Phase 1 implementation

**Document Version**: 1.0
**Review Required**: Backend Lead, Frontend Lead, Product Owner, QA Lead
