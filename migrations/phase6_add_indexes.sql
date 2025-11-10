-- ==========================================
-- PHASE 6 DATABASE MIGRATION
-- Date: 2025-11-09
-- Purpose: Add indexes for JOIN performance
-- Single Source of Truth: delivery_type in tigu_prepare_goods ONLY
-- ==========================================

USE tigu_b2b;

-- Pre-migration checks
SELECT 'Starting Phase 6 Migration...' as status;

-- Verify tables exist
SELECT 'Checking tables...' as status;
SELECT COUNT(*) as prepare_goods_exists FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'tigu_b2b' AND TABLE_NAME = 'tigu_prepare_goods';

SELECT COUNT(*) as order_exists FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'tigu_b2b' AND TABLE_NAME = 'tigu_order';

-- Check if indexes already exist (idempotent check)
SELECT 'Checking existing indexes...' as status;
SELECT COUNT(*) as idx_order_ids_exists FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'tigu_b2b'
  AND TABLE_NAME = 'tigu_prepare_goods'
  AND INDEX_NAME = 'idx_order_ids';

SELECT COUNT(*) as idx_delivery_shipping_exists FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'tigu_b2b'
  AND TABLE_NAME = 'tigu_prepare_goods'
  AND INDEX_NAME = 'idx_delivery_shipping';

-- ==========================================
-- MIGRATION STEP 1: Add index on order_ids
-- ==========================================
SELECT 'Adding index on order_ids...' as status;

-- Check if index exists, create if not
SET @idx_exists = (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'tigu_b2b'
      AND TABLE_NAME = 'tigu_prepare_goods'
      AND INDEX_NAME = 'idx_order_ids'
);

SET @sql1 = IF(@idx_exists = 0,
    'ALTER TABLE tigu_prepare_goods ADD INDEX idx_order_ids (order_ids(100))',
    'SELECT "Index idx_order_ids already exists, skipping..." as status'
);

PREPARE stmt1 FROM @sql1;
EXECUTE stmt1;
DEALLOCATE PREPARE stmt1;

-- ==========================================
-- MIGRATION STEP 2: Add composite index
-- ==========================================
SELECT 'Adding composite index on delivery_type, shipping_type...' as status;

-- Check if index exists, create if not
SET @idx_exists2 = (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = 'tigu_b2b'
      AND TABLE_NAME = 'tigu_prepare_goods'
      AND INDEX_NAME = 'idx_delivery_shipping'
);

SET @sql2 = IF(@idx_exists2 = 0,
    'ALTER TABLE tigu_prepare_goods ADD INDEX idx_delivery_shipping (delivery_type, shipping_type)',
    'SELECT "Index idx_delivery_shipping already exists, skipping..." as status'
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- ==========================================
-- POST-MIGRATION VERIFICATION
-- ==========================================
SELECT 'Verifying migration...' as status;

-- Check indexes were created
SELECT 'Checking indexes after migration...' as status;
SHOW INDEX FROM tigu_prepare_goods WHERE Key_name IN ('idx_order_ids', 'idx_delivery_shipping');

-- Verify index structure
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    CARDINALITY
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'tigu_b2b'
  AND TABLE_NAME = 'tigu_prepare_goods'
  AND INDEX_NAME IN ('idx_order_ids', 'idx_delivery_shipping')
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- Test query performance
SELECT 'Testing query performance...' as status;
EXPLAIN
SELECT delivery_type
FROM tigu_prepare_goods
WHERE order_ids LIKE '%123%'
LIMIT 1;

-- Summary
SELECT 'Phase 6 Migration Complete!' as status;
SELECT NOW() as completed_at;
