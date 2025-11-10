# Route Planner Update - New Workflow Integration

**Date**: 2025-11-09
**Component**: Route Optimization Endpoint
**Status**: ✅ UPDATED

## Overview

Updated the route planner to use the new `tigu_prepare_goods` based workflow instead of querying `tigu_order` directly.

## Changes Made

### File: `bff/app/api/v1/routes/routes.py`

**Old Workflow**:
```python
# Directly queried tigu_order table
orders = await order_service.fetch_assigned_orders(session, driver.id, include_completed=False)
return await route_service.build_route_plan(orders)
```

**New Workflow**:
```python
# 1. Get PrepareGoods packages assigned to driver
packages = await session.execute(
    select(PrepareGoods)
    .where(PrepareGoods.driver_id == driver.id)
    .where(PrepareGoods.prepare_status < 6)  # Not completed
)

# 2. Extract order IDs from packages
all_order_ids = []
for pkg in packages:
    order_ids = parse_order_id_list(pkg.order_ids)
    all_order_ids.extend(order_ids)

# 3. Fetch orders for those IDs
orders = await session.execute(
    select(Order)
    .where(Order.id.in_(unique_order_ids))
    .where(Order.shipping_status < 7)
)

# 4. Build route plan
return await route_service.build_route_plan(order_summaries)
```

## Workflow Logic

### Data Flow:
1. **Driver Authentication** → Get driver_id
2. **Query PrepareGoods** → Get all packages assigned to driver
3. **Filter Active** → Exclude completed packages (`prepare_status = 6`)
4. **Extract Orders** → Parse `order_ids` field from each package
5. **Deduplicate** → Remove duplicate order IDs
6. **Fetch Orders** → Get full order details for route optimization
7. **Build Route** → Create optimized delivery route

### Status Filtering:
- **PrepareGoods**: `prepare_status < 6` (exclude completed)
- **Orders**: `shipping_status < 7` (exclude completed)

## Empty Route Handling

If no packages or no orders are found:
```python
return RoutePlan(id="empty", stops=[])
```

## Dependencies

**New Imports**:
- `PrepareGoods` model
- `Order` model
- `parse_order_id_list` utility
- `selectinload` for eager loading

## Testing

**Test Cases**:
1. Driver with multiple prepare packages → Route includes all orders
2. Driver with no packages → Empty route returned
3. Packages with overlapping orders → Orders deduplicated
4. Mix of completed and active packages → Only active included

## Benefits

✅ **Single Source of Truth**: Routes based on `tigu_prepare_goods`
✅ **Workflow Alignment**: Matches 4-workflow delivery system
✅ **Deduplication**: Handles orders in multiple packages
✅ **Status Filtering**: Only active deliveries in route

## Deployment

**Steps**:
1. Backend already contains updated code
2. Restart backend: `./deploy_backend.sh`
3. Frontend requires no changes (API contract unchanged)
4. Test route planner with driver account

## API Contract

**Endpoint**: `POST /api/routes/optimize`
**Request**: No body (uses authenticated driver)
**Response**: `RoutePlan` with ordered stops
**Status**: No changes to response format

---

**Status**: ✅ Ready for deployment
**Backend Restart Required**: Yes
**Frontend Changes**: None
