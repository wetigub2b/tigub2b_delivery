-- Migration: Create independent driver table
-- Date: 2025-10-24
-- Description: Creates a standalone driver table with driver-specific information

CREATE TABLE IF NOT EXISTS tigu_driver (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    license_number VARCHAR(50),
    vehicle_type VARCHAR(50),
    vehicle_plate VARCHAR(20),
    vehicle_model VARCHAR(100),
    status TINYINT DEFAULT 1 COMMENT '1:active, 0:inactive',
    rating DECIMAL(3,2) DEFAULT 5.00,
    total_deliveries INT DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
