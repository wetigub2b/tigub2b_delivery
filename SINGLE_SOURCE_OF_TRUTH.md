# Single Source of Truth Pattern

**Date**: 2025-11-09
**Decision**: Use `tigu_prepare_goods.delivery_type` as the single source of truth
**Rationale**: Avoid data duplication and inconsistency

---

## Problem Statement

The original design had `delivery_type` in both tables:
- ❌ `tigu_order.delivery_type` (proposed)
- ✅ `tigu_prepare_goods.delivery_type` (already exists in DB)

**Issue**: Two sources of truth → Data synchronization problems → Bugs

---

## Solution: Single Source of Truth

### ✅ Canonical Location

**`tigu_prepare_goods.delivery_type`** is the **ONLY** source of truth for delivery configuration.

```python
# tigu_prepare_goods table schema
delivery_type INT  # 0=商家自配, 1=第三方配送
shipping_type INT  # 0=发仓库, 1=发用户
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Merchant creates PrepareGoods package                      │
│  Sets: delivery_type, shipping_type                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PrepareGoods record created                                │
│  ✓ delivery_type stored here (SINGLE SOURCE)               │
│  ✓ order_ids links to tigu_order                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  To get delivery_type for an order:                         │
│  1. Find PrepareGoods WHERE order_ids LIKE '%order_id%'    │
│  2. Read delivery_type from PrepareGoods                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Pattern

### Querying delivery_type

```python
# Method 1: Via PrepareGoods lookup
async def get_order_delivery_type(
    session: AsyncSession,
    order_id: int
) -> int | None:
    """
    Get delivery_type for an order from PrepareGoods.

    Returns:
        0 = Merchant self-delivery
        1 = Third-party driver delivery
        None = Order not in any PrepareGoods package yet
    """
    stmt = (
        select(PrepareGoods.delivery_type)
        .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# Method 2: Via order_sn
async def get_order_delivery_type_by_sn(
    session: AsyncSession,
    order_sn: str
) -> int | None:
    """Get delivery_type by order serial number"""

    # First get order_id from order_sn
    order_stmt = select(Order.id).where(Order.order_sn == order_sn)
    order_result = await session.execute(order_stmt)
    order_id = order_result.scalar_one_or_none()

    if not order_id:
        return None

    # Then find PrepareGoods
    prepare_stmt = (
        select(PrepareGoods.delivery_type)
        .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    )
    prepare_result = await session.execute(prepare_stmt)
    return prepare_result.scalar_one_or_none()


# Method 3: Join pattern (for bulk queries)
async def get_orders_with_delivery_config(
    session: AsyncSession
) -> list[dict]:
    """Get orders with their delivery configuration from PrepareGoods"""

    stmt = """
        SELECT
            o.id,
            o.order_sn,
            pg.delivery_type,
            pg.shipping_type,
            pg.prepare_status
        FROM tigu_order o
        INNER JOIN tigu_prepare_goods pg
            ON FIND_IN_SET(o.id, REPLACE(pg.order_ids, ',', ','))
        WHERE pg.delivery_type IS NOT NULL
    """

    result = await session.execute(text(stmt))
    return [dict(row) for row in result]
```

---

## Service Layer Integration

### PrepareGoodsService (Phase 2)

```python
# bff/app/services/prepare_goods_service.py

async def create_prepare_package(
    session: AsyncSession,
    order_ids: List[int],
    shop_id: int,
    delivery_type: int,  # ← Set here, ONCE
    shipping_type: int,
    warehouse_id: int | None = None
) -> PrepareGoods:
    """
    Create prepare package - sets delivery_type as source of truth.

    This is the ONLY place where delivery_type should be set.
    All other services read from PrepareGoods.
    """
    prepare_goods = PrepareGoods(
        prepare_sn=generate_prepare_sn(),
        order_ids=",".join(str(oid) for oid in order_ids),
        delivery_type=delivery_type,  # Single source of truth
        shipping_type=shipping_type,
        shop_id=shop_id,
        warehouse_id=warehouse_id,
        create_time=datetime.now()
    )

    session.add(prepare_goods)
    await session.commit()

    return prepare_goods
```

### OrderService (Phase 2)

```python
# bff/app/services/order_service.py

async def get_order_with_delivery_config(
    session: AsyncSession,
    order_sn: str
) -> dict:
    """
    Get order with delivery configuration from PrepareGoods.

    Never reads delivery_type from Order table (doesn't exist).
    Always reads from PrepareGoods (single source of truth).
    """
    # Get order
    order_stmt = select(Order).where(Order.order_sn == order_sn)
    order_result = await session.execute(order_stmt)
    order = order_result.scalar_one_or_none()

    if not order:
        return None

    # Get delivery config from PrepareGoods
    prepare_stmt = (
        select(PrepareGoods)
        .where(PrepareGoods.order_ids.like(f"%{order.id}%"))
    )
    prepare_result = await session.execute(prepare_stmt)
    prepare_goods = prepare_result.scalar_one_or_none()

    return {
        "order": order,
        "delivery_type": prepare_goods.delivery_type if prepare_goods else None,
        "shipping_type": order.shipping_type,  # Can also use prepare_goods.shipping_type
        "prepare_status": prepare_goods.prepare_status if prepare_goods else None
    }
```

---

## Schema Design Principles

### ✅ Single Source of Truth Benefits

1. **Data Consistency**: No synchronization needed between tables
2. **Simpler Logic**: One place to update delivery_type
3. **Clear Ownership**: PrepareGoods owns delivery configuration
4. **No Migration Needed**: No ALTER TABLE on tigu_order
5. **Backward Compatible**: Existing orders unaffected

### 📊 Data Relationship

```
┌──────────────────────────────────────────┐
│         tigu_prepare_goods               │
│  ┌────────────────────────────────────┐  │
│  │ id (PK)                            │  │
│  │ prepare_sn                         │  │
│  │ delivery_type ← SOURCE OF TRUTH   │  │
│  │ shipping_type                      │  │
│  │ order_ids (CSV: "101,102,103")    │  │
│  └────────────────────────────────────┘  │
└──────────────────┬───────────────────────┘
                   │
                   │ Links via order_ids
                   │
        ┌──────────┴──────────┬──────────────┐
        │                     │              │
┌───────▼────────┐   ┌───────▼────────┐   ┌▼────────────┐
│  Order 101     │   │  Order 102     │   │ Order 103   │
│  ┌──────────┐  │   │  ┌──────────┐  │   │ ┌────────┐  │
│  │ id: 101  │  │   │  │ id: 102  │  │   │ │ id: 103│  │
│  │ order_sn │  │   │  │ order_sn │  │   │ │order_sn│  │
│  │ shipping │  │   │  │ shipping │  │   │ │shipping│  │
│  │ _type    │  │   │  │ _type    │  │   │ │_type   │  │
│  └──────────┘  │   │  └──────────┘  │   │ └────────┘  │
│  ❌ NO         │   │  ❌ NO         │   │ ❌ NO       │
│  delivery_type │   │  delivery_type │   │ delivery   │
│                │   │                │   │ _type      │
└────────────────┘   └────────────────┘   └────────────┘
```

---

## API Response Pattern

### OrderDetail Schema

```python
# bff/app/schemas/order.py

class OrderDetail(BaseModel):
    """
    Order detail response including delivery configuration.

    Note: delivery_type comes from PrepareGoods, not Order table.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Order fields
    order_sn: str = Field(alias='orderSn')
    shipping_status: int = Field(alias='shippingStatus')
    shipping_type: int = Field(alias='shippingType')

    # Delivery configuration from PrepareGoods
    delivery_type: int | None = Field(
        default=None,
        alias='deliveryType',
        description="从PrepareGoods读取: 0=商家自配, 1=第三方配送"
    )

    prepare_status: int | None = Field(
        default=None,
        alias='prepareStatus',
        description="从PrepareGoods读取: 备货状态"
    )

    # ... other fields


# Service layer populates delivery_type
async def _serialize_detail(
    session: AsyncSession,
    order: Order
) -> OrderDetail:
    # Get delivery config from PrepareGoods
    prepare_goods = await get_prepare_goods_for_order(session, order.id)

    return OrderDetail(
        order_sn=order.order_sn,
        shipping_status=order.shipping_status,
        shipping_type=order.shipping_type,
        delivery_type=prepare_goods.delivery_type if prepare_goods else None,
        prepare_status=prepare_goods.prepare_status if prepare_goods else None,
        # ... other fields
    )
```

---

## Performance Considerations

### Index for Efficient Lookups

```sql
-- Already exists in database
-- Ensures fast lookup of PrepareGoods by order_id

-- Option 1: Full-text search index (if order_ids is TEXT)
ALTER TABLE tigu_prepare_goods
ADD FULLTEXT INDEX idx_order_ids (order_ids);

-- Then query with:
SELECT * FROM tigu_prepare_goods
WHERE MATCH(order_ids) AGAINST('101' IN BOOLEAN MODE);

-- Option 2: Use JSON column (future enhancement)
-- Change order_ids from CSV to JSON array: [101, 102, 103]
-- Then use JSON_CONTAINS for exact matching
```

### Caching Strategy

```python
# Cache PrepareGoods lookups to avoid repeated queries

from functools import lru_cache
from datetime import datetime, timedelta

class PrepareGoodsCache:
    """In-memory cache for PrepareGoods lookups"""

    def __init__(self):
        self._cache = {}
        self._ttl = timedelta(minutes=5)

    async def get_by_order_id(
        self,
        session: AsyncSession,
        order_id: int
    ) -> PrepareGoods | None:
        # Check cache
        cache_key = f"order_{order_id}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._ttl:
                return cached_data

        # Cache miss - query database
        stmt = (
            select(PrepareGoods)
            .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
        )
        result = await session.execute(stmt)
        prepare_goods = result.scalar_one_or_none()

        # Update cache
        self._cache[cache_key] = (prepare_goods, datetime.now())

        return prepare_goods
```

---

## Migration Notes (Phase 6)

### ✅ No Schema Changes Needed

Since we're using PrepareGoods as the source of truth:

**What we DON'T need to do:**
- ❌ ALTER TABLE tigu_order ADD COLUMN delivery_type
- ❌ Data backfill for delivery_type
- ❌ Synchronization logic between tables

**What we DO need to do:**
- ✅ Add index on tigu_prepare_goods.order_ids (performance)
- ✅ Add caching for PrepareGoods lookups (performance)
- ✅ Update service layer to read from PrepareGoods

---

## Edge Cases

### Case 1: Order Not Yet in PrepareGoods

```python
# Order created but merchant hasn't created PrepareGoods yet
order_id = 12345
delivery_type = await get_order_delivery_type(session, order_id)
# Result: None

# Handle gracefully
if delivery_type is None:
    # Order is in "pending prepare" state
    # Use default or show as "待分配配送方式"
    delivery_type = 1  # Default to third-party
```

### Case 2: Order in Multiple PrepareGoods (Should Not Happen)

```python
# Business rule: One order should only be in ONE PrepareGoods package
# But if it happens due to data error:

stmt = (
    select(PrepareGoods)
    .where(PrepareGoods.order_ids.like(f"%{order_id}%"))
    .order_by(PrepareGoods.create_time.desc())  # Get most recent
    .limit(1)
)
result = await session.execute(stmt)
prepare_goods = result.scalar_one_or_none()
```

### Case 3: PrepareGoods Deleted

```python
# If PrepareGoods is soft-deleted or removed:
# Fall back to shipping_type only

if delivery_type is None:
    # Can infer from driver assignment
    if order.driver_id is not None:
        delivery_type = 1  # Third-party (has driver)
    else:
        delivery_type = 0  # Merchant self-delivery (no driver)
```

---

## Summary

### ✅ Decision: Single Source of Truth

**Source**: `tigu_prepare_goods.delivery_type`

**Rationale**:
1. Avoid duplicate data
2. Prevent synchronization bugs
3. Simplify data model
4. No migration needed
5. Clear ownership

### 📋 Implementation Checklist

- [x] Remove delivery_type from Order model
- [ ] Create helper functions to read from PrepareGoods (Phase 2)
- [ ] Update service layer to use PrepareGoods (Phase 2)
- [ ] Add caching for performance (Phase 2)
- [ ] Update API schemas to include delivery_type from PrepareGoods (Phase 2)
- [ ] Add index on order_ids for fast lookup (Phase 6)

---

**Document Version**: 1.0
**Date**: 2025-11-09
**Status**: Approved
**Review**: Ready for Phase 2 implementation
