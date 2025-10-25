-- Migration: Add driver_id to orders table
-- Date: 2025-10-24
-- Description: Links orders to independent drivers table

-- Check if column exists and add it if not
SET @col_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tigu_order'
    AND COLUMN_NAME = 'driver_id'
);

-- Add driver_id column if it doesn't exist
SET @add_column = IF(@col_exists = 0,
    'ALTER TABLE tigu_order ADD COLUMN driver_id BIGINT UNSIGNED NULL AFTER warehouse_id',
    'SELECT "Column driver_id already exists" AS info'
);

PREPARE stmt FROM @add_column;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Ensure column is BIGINT UNSIGNED (in case it exists but has wrong type)
ALTER TABLE tigu_order
MODIFY COLUMN driver_id BIGINT UNSIGNED NULL;

-- Check if foreign key constraint exists
SET @fk_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tigu_order'
    AND CONSTRAINT_NAME = 'fk_tigu_order_driver'
    AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);

-- Add foreign key constraint if it doesn't exist
SET @add_fk = IF(@fk_exists = 0,
    'ALTER TABLE tigu_order ADD CONSTRAINT fk_tigu_order_driver FOREIGN KEY (driver_id) REFERENCES tigu_driver(id) ON DELETE SET NULL ON UPDATE CASCADE',
    'SELECT "Foreign key fk_tigu_order_driver already exists" AS info'
);

PREPARE stmt FROM @add_fk;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if index exists
SET @idx_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tigu_order'
    AND INDEX_NAME = 'idx_tigu_order_driver_id'
);

-- Add index if it doesn't exist
SET @add_idx = IF(@idx_exists = 0,
    'ALTER TABLE tigu_order ADD INDEX idx_tigu_order_driver_id (driver_id)',
    'SELECT "Index idx_tigu_order_driver_id already exists" AS info'
);

PREPARE stmt FROM @add_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
