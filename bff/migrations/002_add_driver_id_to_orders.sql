-- Migration: Add driver_id to orders table
-- Date: 2025-10-24
-- Description: Links orders to independent drivers table

-- Modify existing driver_id column to reference tigu_driver
ALTER TABLE tigu_order
MODIFY COLUMN driver_id BIGINT UNSIGNED NULL;

-- Add new foreign key constraint to tigu_driver
ALTER TABLE tigu_order
ADD CONSTRAINT fk_tigu_order_driver
FOREIGN KEY (driver_id) REFERENCES tigu_driver(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Add index for performance
ALTER TABLE tigu_order
ADD INDEX idx_tigu_order_driver_id (driver_id);
