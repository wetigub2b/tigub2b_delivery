-- Migration: Create tigu_driver_marks table for map markers
-- Description: Stores location markers for driver map display (Greater Toronto Area)
-- Date: 2024-12-01
-- Updated: 2024-12-02 - Added shop_id and warehouse_id for pickup location linking

USE tigu_b2b;

-- Drop existing table to recreate with new columns
DROP TABLE IF EXISTS tigu_driver_marks;

-- Create tigu_driver_marks table
CREATE TABLE tigu_driver_marks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key',
    name VARCHAR(255) NOT NULL COMMENT 'Marker display name',
    latitude DECIMAL(10, 8) NOT NULL COMMENT 'Latitude coordinate',
    longitude DECIMAL(11, 8) NOT NULL COMMENT 'Longitude coordinate',
    type VARCHAR(50) DEFAULT NULL COMMENT 'Marker type (Warehouse, Hub, Depot, Vendor, etc.)',
    description TEXT DEFAULT NULL COMMENT 'Marker description',
    shop_id BIGINT UNSIGNED DEFAULT NULL COMMENT 'Link to tigu_shop for vendor pickup locations',
    warehouse_id BIGINT UNSIGNED DEFAULT NULL COMMENT 'Link to tigu_warehouse for warehouse pickup locations',
    is_active TINYINT(1) DEFAULT 1 COMMENT 'Active status (1=active, 0=inactive)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    INDEX idx_location (latitude, longitude) COMMENT 'Index for location queries',
    INDEX idx_type (type) COMMENT 'Index for filtering by type',
    INDEX idx_active (is_active) COMMENT 'Index for active markers',
    INDEX idx_shop_id (shop_id) COMMENT 'Index for shop lookup',
    INDEX idx_warehouse_id (warehouse_id) COMMENT 'Index for warehouse lookup'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Map markers for driver dashboard - pickup locations for vendors and warehouses';

-- Insert sample markers for Greater Toronto Area (GTA)
-- Warehouse pickup locations (linked to tigu_warehouse)
INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description, warehouse_id) VALUES
    ('Warehouse 1 - Burlington', 43.32580000, -79.79910000, 'Warehouse', 'Main warehouse in Burlington', 1968605598853562370);

-- Vendor pickup locations (linked to tigu_shop)
INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description, shop_id) VALUES
    ('金家建材', 43.65320000, -79.38320000, 'Vendor', 'Vendor pickup - Downtown Toronto', 2001),
    ('GreenBuild Supplies', 43.58900000, -79.64410000, 'Vendor', 'Vendor pickup - Mississauga', 2002),
    ('Modern Timber Co.', 43.85610000, -79.33700000, 'Vendor', 'Vendor pickup - Markham', 2003);

-- Verify insertion
SELECT COUNT(*) as marker_count FROM tigu_driver_marks WHERE is_active = 1;
SELECT id, name, type, shop_id, warehouse_id FROM tigu_driver_marks;
