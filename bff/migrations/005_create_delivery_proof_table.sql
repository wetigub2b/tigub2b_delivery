-- Migration: Create delivery proof table
-- Description: Store delivery proof photos and notes
-- Author: System
-- Date: 2025-10-26

CREATE TABLE IF NOT EXISTS tigu_delivery_proof (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    order_sn VARCHAR(64) NOT NULL,
    driver_id BIGINT UNSIGNED NOT NULL,
    photo_url VARCHAR(512) NOT NULL,
    notes TEXT,
    file_size INT UNSIGNED COMMENT 'File size in bytes',
    mime_type VARCHAR(50) COMMENT 'Image MIME type',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_order_id (order_id),
    INDEX idx_order_sn (order_sn),
    INDEX idx_driver_id (driver_id),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (order_id) REFERENCES tigu_order(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES tigu_driver(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Delivery proof of delivery photos and notes';
