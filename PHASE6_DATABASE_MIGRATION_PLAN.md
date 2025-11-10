# Phase 6: Database Migration Plan

**Date**: 2025-11-09
**Phase**: Deployment & Migration
**Database**: tigu_b2b (MySQL)

---

## Overview

This document outlines the database changes required for Phase 6 deployment of the 4-workflow delivery system.

---

## Database Status Analysis

### ✅ Tables Already Exist (No Creation Needed)

These tables were already created in the database:

1. **tigu_prepare_goods** ✅
   - Purpose: Merchant prepare goods packages
   - Status: EXISTS

2. **tigu_prepare_goods_item** ✅
   - Purpose: Items in prepare packages
   - Status: EXISTS

3. **tigu_order_action** ✅
   - Purpose: Order workflow audit trail
   - Status: EXISTS

4. **tigu_order** ✅
   - Purpose: Order information (needs modification)
   - Status: EXISTS

5. **tigu_uploaded_files** ✅
   - Purpose: File uploads for photo evidence
   - Status: EXISTS (has biz_id and biz_type)

6. **tigu_warehouse** ✅
   - Purpose: Warehouse information
   - Status: EXISTS

7. **tigu_driver** ✅
   - Purpose: Driver information
   - Status: EXISTS

---

## Required Database Changes

### 1. ❌ Add Missing Column to tigu_order

**Column to Add**: `delivery_type`

**Current Status**: Column does NOT exist

**Migration SQL**:
```sql
-- Add delivery_type column to tigu_order
ALTER TABLE tigu_order
ADD COLUMN delivery_type INT NULL
COMMENT '配送方式: 0=商家自配, 1=第三方配送'
AFTER shipping_type;
```

**Verification**:
```sql
-- Verify column was added
DESCRIBE tigu_order;
SHOW COLUMNS FROM tigu_order LIKE 'delivery_type';
```

**Existing Columns** (Already Present):
- ✅ `shipping_type` - Already exists
- ✅ `shipping_status` - Already exists
- ✅ `driver_receive_time` - Already exists
- ✅ `arrive_warehouse_time` - Already exists
- ✅ `warehouse_shipping_time` - Already exists

---

### 2. ✅ Indexes on tigu_uploaded_files (Already Exists)

**Current Status**: Index already exists on `biz_id`

**Index Name**: `idx_biz` (composite index on biz_type, biz_id)

**Verification**:
```sql
-- Check existing index
SHOW INDEX FROM tigu_uploaded_files WHERE Column_name='biz_id';
```

**Result**: ✅ NO ACTION NEEDED - Index already exists

---

### 3. ❌ Add Index to tigu_order

**Index to Add**: Composite index on `delivery_type` and `shipping_type`

**Current Status**: Index does NOT exist

**Migration SQL**:
```sql
-- Add composite index for workflow queries
ALTER TABLE tigu_order
ADD INDEX idx_delivery_shipping_type (delivery_type, shipping_type);
```

**Purpose**:
- Optimize workflow-specific queries
- Speed up filtering by delivery type
- Improve PrepareGoods lookups

**Verification**:
```sql
-- Verify index was created
SHOW INDEX FROM tigu_order WHERE Key_name='idx_delivery_shipping_type';
```

---

### 4. 🔄 Data Migration (Optional)

**Backfill delivery_type for Existing Orders**

**Current Status**: Existing orders have `delivery_type = NULL`

**Migration Strategy Options**:

#### Option A: Assume Third-Party Delivery (Recommended)
```sql
-- Set all existing orders to third-party delivery
UPDATE tigu_order
SET delivery_type = 1
WHERE delivery_type IS NULL;
```

**Pros**:
- Safe assumption for existing driver-based system
- Matches current workflow behavior
- Prevents NULL issues

**Cons**:
- May not reflect actual historical delivery method

#### Option B: Set Based on shipping_type
```sql
-- Set delivery_type based on shipping_type
UPDATE tigu_order
SET delivery_type = CASE
    WHEN shipping_type = 0 THEN 1  -- To warehouse = likely third-party
    WHEN shipping_type = 1 THEN 1  -- To user = could be either
    ELSE 1
END
WHERE delivery_type IS NULL;
```

#### Option C: Leave as NULL
```sql
-- Do nothing - leave existing orders as NULL
-- NULL can represent "legacy workflow" before refactoring
```

**Recommendation**: Use **Option A** (set to 1 for third-party) to maintain consistency.

**Verification**:
```sql
-- Check how many orders need backfilling
SELECT COUNT(*) FROM tigu_order WHERE delivery_type IS NULL;

-- After migration, verify
SELECT delivery_type, COUNT(*)
FROM tigu_order
GROUP BY delivery_type;
```

---

## Complete Migration Script

### Pre-Migration Checks

```sql
-- 1. Backup database
-- mysqldump -u tigu -p tigu_b2b > tigu_b2b_backup_$(date +%Y%m%d).sql

-- 2. Verify table existence
USE tigu_b2b;
SHOW TABLES LIKE 'tigu_%';

-- 3. Check current order count
SELECT COUNT(*) as total_orders FROM tigu_order;

-- 4. Check NULL delivery_type count
SELECT COUNT(*) as orders_needing_backfill
FROM tigu_order
WHERE delivery_type IS NULL;

-- 5. Verify new tables exist
SELECT COUNT(*) FROM tigu_prepare_goods;
SELECT COUNT(*) FROM tigu_prepare_goods_item;
SELECT COUNT(*) FROM tigu_order_action;
```

### Migration Execution

```sql
USE tigu_b2b;

-- ==========================================
-- PHASE 6 DATABASE MIGRATION
-- Date: 2025-11-09
-- Purpose: Add 4-workflow delivery system support
-- ==========================================

-- Step 1: Add delivery_type column to tigu_order
ALTER TABLE tigu_order
ADD COLUMN delivery_type INT NULL
COMMENT '配送方式: 0=商家自配, 1=第三方配送'
AFTER shipping_type;

-- Step 2: Add composite index for workflow queries
ALTER TABLE tigu_order
ADD INDEX idx_delivery_shipping_type (delivery_type, shipping_type);

-- Step 3: Backfill delivery_type for existing orders
-- (Choose one option based on business requirements)

-- Option A: Set all to third-party (RECOMMENDED)
UPDATE tigu_order
SET delivery_type = 1
WHERE delivery_type IS NULL;

-- OR Option B: Set based on shipping_type
-- UPDATE tigu_order
-- SET delivery_type = CASE
--     WHEN shipping_type = 0 THEN 1
--     WHEN shipping_type = 1 THEN 1
--     ELSE 1
-- END
-- WHERE delivery_type IS NULL;

-- OR Option C: Leave as NULL (not recommended)
-- (No UPDATE statement)
```

### Post-Migration Verification

```sql
-- 1. Verify column was added
DESCRIBE tigu_order;
SHOW COLUMNS FROM tigu_order LIKE 'delivery_type';

-- 2. Verify index was created
SHOW INDEX FROM tigu_order WHERE Key_name='idx_delivery_shipping_type';

-- 3. Check data distribution
SELECT
    delivery_type,
    shipping_type,
    COUNT(*) as order_count
FROM tigu_order
GROUP BY delivery_type, shipping_type
ORDER BY delivery_type, shipping_type;

-- 4. Verify no NULL values (if backfill was done)
SELECT COUNT(*) as null_count
FROM tigu_order
WHERE delivery_type IS NULL;

-- 5. Test query performance with new index
EXPLAIN SELECT *
FROM tigu_order
WHERE delivery_type = 1 AND shipping_type = 0
LIMIT 10;

-- 6. Verify new tables have data (from testing)
SELECT
    'prepare_goods' as table_name,
    COUNT(*) as row_count
FROM tigu_prepare_goods
UNION ALL
SELECT
    'prepare_goods_item',
    COUNT(*)
FROM tigu_prepare_goods_item
UNION ALL
SELECT
    'order_action',
    COUNT(*)
FROM tigu_order_action;
```

---

## Rollback Plan

If migration needs to be rolled back:

```sql
USE tigu_b2b;

-- Step 1: Remove index
ALTER TABLE tigu_order DROP INDEX idx_delivery_shipping_type;

-- Step 2: Remove column (WARNING: This deletes data!)
ALTER TABLE tigu_order DROP COLUMN delivery_type;

-- Step 3: Restore from backup if needed
-- mysql -u tigu -p tigu_b2b < tigu_b2b_backup_YYYYMMDD.sql
```

**Note**: Rollback will delete the `delivery_type` column data. Only perform if absolutely necessary.

---

## Migration Impact Analysis

### Tables Affected

| Table | Change Type | Impact Level | Downtime Required |
|-------|-------------|--------------|-------------------|
| tigu_order | ADD COLUMN | LOW | No (nullable) |
| tigu_order | ADD INDEX | LOW | No (online DDL) |
| tigu_order | UPDATE DATA | MEDIUM | No (batched updates) |

### Estimated Execution Time

Based on table size:

```sql
-- Check current order count
SELECT COUNT(*) FROM tigu_order;
```

**Time Estimates**:
- **< 10,000 orders**: ~5 seconds
- **10,000 - 100,000 orders**: ~30 seconds
- **100,000 - 1,000,000 orders**: ~5 minutes
- **> 1,000,000 orders**: ~30 minutes (use batched updates)

### Batched Update Strategy (For Large Tables)

If you have > 100,000 orders, use batched updates:

```sql
-- Batch update in chunks of 10,000
SET @batch_size = 10000;
SET @offset = 0;

-- Repeat this until no rows affected:
UPDATE tigu_order
SET delivery_type = 1
WHERE delivery_type IS NULL
LIMIT @batch_size;

-- Check progress:
SELECT COUNT(*) FROM tigu_order WHERE delivery_type IS NULL;
```

---

## Performance Considerations

### Index Size

The new composite index will use approximately:
- **Per Row**: 8 bytes (4 bytes per INT column)
- **For 10,000 orders**: ~78 KB
- **For 100,000 orders**: ~780 KB
- **For 1,000,000 orders**: ~7.8 MB

**Storage Impact**: Minimal

### Query Performance Improvement

**Before Index** (Full table scan):
```sql
-- Slow query without index
SELECT * FROM tigu_order
WHERE delivery_type = 1 AND shipping_type = 0;
-- Scans all rows
```

**After Index** (Index range scan):
```sql
-- Fast query with index
SELECT * FROM tigu_order
WHERE delivery_type = 1 AND shipping_type = 0;
-- Uses idx_delivery_shipping_type
-- Expected: 100-1000x faster
```

---

## Data Integrity Checks

### Before Migration

```sql
-- Check for data consistency
SELECT
    shipping_type,
    shipping_status,
    COUNT(*) as count
FROM tigu_order
GROUP BY shipping_type, shipping_status;

-- Check for orphaned records
SELECT COUNT(*) FROM tigu_order_item oi
LEFT JOIN tigu_order o ON oi.order_id = o.id
WHERE o.id IS NULL;
```

### After Migration

```sql
-- Validate delivery_type values
SELECT delivery_type, COUNT(*)
FROM tigu_order
GROUP BY delivery_type;
-- Expected: 0 and 1 only (or NULL if Option C)

-- Validate workflow combinations
SELECT
    delivery_type,
    shipping_type,
    COUNT(*) as workflow_count
FROM tigu_order
GROUP BY delivery_type, shipping_type;
-- Expected: (0,0), (0,1), (1,0), (1,1)
```

---

## Summary of Database Changes

### Changes Required

✅ **Tables**: All required tables already exist
❌ **Columns**: 1 column to add (`tigu_order.delivery_type`)
❌ **Indexes**: 1 index to add (`idx_delivery_shipping_type`)
🔄 **Data**: Optional backfill of `delivery_type` for existing orders

### Total Changes: 2-3 Operations

1. **ADD COLUMN** tigu_order.delivery_type
2. **ADD INDEX** tigu_order.idx_delivery_shipping_type
3. **UPDATE DATA** (optional) backfill delivery_type

### Execution Time: < 1 minute

For typical order volumes (< 100k orders).

### Risk Level: LOW

- Non-breaking changes (nullable column)
- Online DDL supported (no table locking)
- Easy rollback (if needed)
- Minimal performance impact

---

## Deployment Checklist

**Pre-Deployment**:
- [ ] Create database backup
- [ ] Test migration on staging database
- [ ] Verify all tests pass
- [ ] Review execution time estimates
- [ ] Prepare rollback plan
- [ ] Schedule maintenance window (if needed)

**Deployment**:
- [ ] Connect to production database
- [ ] Run pre-migration checks
- [ ] Execute migration script
- [ ] Run post-migration verification
- [ ] Monitor error logs
- [ ] Test sample workflows

**Post-Deployment**:
- [ ] Verify query performance
- [ ] Check data consistency
- [ ] Monitor application logs
- [ ] User acceptance testing
- [ ] Document any issues

---

## Monitoring Queries

Use these queries to monitor the system after migration:

```sql
-- 1. Workflow distribution
SELECT
    CONCAT('Workflow ',
        CASE
            WHEN delivery_type = 0 AND shipping_type = 0 THEN '1 (Merchant→Warehouse)'
            WHEN delivery_type = 0 AND shipping_type = 1 THEN '2 (Merchant→User)'
            WHEN delivery_type = 1 AND shipping_type = 0 THEN '3 (Driver→Warehouse)'
            WHEN delivery_type = 1 AND shipping_type = 1 THEN '4 (Driver→User)'
            ELSE 'Unknown'
        END
    ) as workflow,
    COUNT(*) as order_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tigu_order), 2) as percentage
FROM tigu_order
GROUP BY delivery_type, shipping_type;

-- 2. Recent order actions
SELECT
    oa.action_type,
    CASE oa.action_type
        WHEN 0 THEN 'Goods Prepared'
        WHEN 1 THEN 'Driver Pickup'
        WHEN 2 THEN 'Driver to Warehouse'
        WHEN 3 THEN 'Warehouse Receive'
        WHEN 4 THEN 'Warehouse Ship'
        WHEN 5 THEN 'Delivery Complete'
        ELSE 'Other'
    END as action_name,
    COUNT(*) as count,
    MAX(oa.create_time) as latest_action
FROM tigu_order_action oa
GROUP BY oa.action_type
ORDER BY oa.action_type;

-- 3. Prepare goods status
SELECT
    prepare_status,
    CASE prepare_status
        WHEN NULL THEN 'Pending'
        WHEN 0 THEN 'Prepared'
        WHEN 1 THEN 'Driver Pickup'
        WHEN 2 THEN 'Driver to Warehouse'
        WHEN 3 THEN 'Warehouse Received'
        WHEN 4 THEN 'Warehouse Shipped'
        WHEN 5 THEN 'Delivered'
        WHEN 6 THEN 'Complete'
        ELSE 'Unknown'
    END as status_name,
    COUNT(*) as count
FROM tigu_prepare_goods
GROUP BY prepare_status
ORDER BY prepare_status;

-- 4. Index usage
SELECT
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    SEQ_IN_INDEX,
    COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'tigu_b2b'
    AND TABLE_NAME = 'tigu_order'
    AND INDEX_NAME = 'idx_delivery_shipping_type';
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Status**: Ready for Execution
