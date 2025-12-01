-- Migration: Create tigu_driver_marks table for map markers
-- Description: Stores location markers for driver map display (Greater Toronto Area)
-- Date: 2024-12-01

USE tigu_b2b;

-- Create tigu_driver_marks table
CREATE TABLE IF NOT EXISTS tigu_driver_marks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key',
    name VARCHAR(255) NOT NULL COMMENT 'Marker display name',
    latitude DECIMAL(10, 8) NOT NULL COMMENT 'Latitude coordinate',
    longitude DECIMAL(11, 8) NOT NULL COMMENT 'Longitude coordinate',
    type VARCHAR(50) DEFAULT NULL COMMENT 'Marker type (Warehouse, Hub, Depot, etc.)',
    description TEXT DEFAULT NULL COMMENT 'Marker description',
    is_active TINYINT(1) DEFAULT 1 COMMENT 'Active status (1=active, 0=inactive)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    INDEX idx_location (latitude, longitude) COMMENT 'Index for location queries',
    INDEX idx_type (type) COMMENT 'Index for filtering by type',
    INDEX idx_active (is_active) COMMENT 'Index for active markers'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Map markers for driver dashboard display';

-- Insert sample markers for Greater Toronto Area (GTA)
INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description) VALUES
    ('Toronto Warehouse', 43.65320000, -79.38320000, 'Warehouse', 'Main distribution center in downtown Toronto'),
    ('Mississauga Hub', 43.58900000, -79.64410000, 'Hub', 'West GTA distribution hub'),
    ('Markham Center', 43.85610000, -79.33700000, 'Hub', 'North GTA distribution center'),
    ('Scarborough Depot', 43.77310000, -79.25780000, 'Depot', 'East GTA depot'),
    ('Brampton Station', 43.73150000, -79.76240000, 'Station', 'Northwest GTA station'),
    ('Richmond Hill Point', 43.88280000, -79.44030000, 'Point', 'North York region pickup point'),
    ('Vaughan Facility', 43.83610000, -79.49830000, 'Facility', 'Vaughan distribution facility'),
    ('Oakville Center', 43.46750000, -79.68770000, 'Center', 'Oakville service center'),
    ('Ajax Station', 43.85090000, -79.02040000, 'Station', 'East GTA Ajax station'),
    ('Milton Hub', 43.51830000, -79.87740000, 'Hub', 'West GTA Milton hub')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Verify insertion
SELECT COUNT(*) as marker_count FROM tigu_driver_marks WHERE is_active = 1;
