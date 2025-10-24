-- Migration: Add driver_id column to tigu_order table
-- Date: 2025-10-24
-- Description: Adds driver_id foreign key to support driver assignment to orders

-- Add driver_id column
ALTER TABLE tigu_order
ADD COLUMN driver_id BIGINT UNSIGNED NULL AFTER warehouse_id;

-- Add foreign key constraint
ALTER TABLE tigu_order
ADD CONSTRAINT fk_tigu_order_driver
FOREIGN KEY (driver_id) REFERENCES sys_user(user_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Add index for performance
CREATE INDEX idx_tigu_order_driver_id ON tigu_order(driver_id);
