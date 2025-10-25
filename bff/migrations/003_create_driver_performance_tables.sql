-- Migration: Create driver performance tables
-- Date: 2025-10-24
-- Description: Creates driver_performance, driver_performance_log, and driver_alert tables

USE tigu_b2b;

CREATE TABLE IF NOT EXISTS driver_performance (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    driver_id BIGINT UNSIGNED NOT NULL,
    period_start DATETIME(6) NOT NULL,
    period_end DATETIME(6) NOT NULL,
    total_deliveries INT NOT NULL DEFAULT 0,
    successful_deliveries INT NOT NULL DEFAULT 0,
    failed_deliveries INT NOT NULL DEFAULT 0,
    avg_delivery_time DECIMAL(10,2) NULL,
    total_active_time DECIMAL(10,2) NULL,
    total_distance DECIMAL(10,2) NULL,
    customer_rating DECIMAL(3,2) NULL,
    on_time_percentage DECIMAL(5,2) NULL,
    orders_per_hour DECIMAL(5,2) NULL,
    fuel_efficiency DECIMAL(5,2) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_driver_performance_driver FOREIGN KEY (driver_id) REFERENCES tigu_driver (id) ON DELETE CASCADE,
    INDEX idx_driver_performance_driver (driver_id),
    INDEX idx_driver_performance_period (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS driver_performance_log (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    driver_id BIGINT UNSIGNED NOT NULL,
    order_id BIGINT UNSIGNED NULL,
    action_type VARCHAR(50) NOT NULL,
    action_timestamp DATETIME(6) NOT NULL,
    latitude DECIMAL(10,6) NULL,
    longitude DECIMAL(10,6) NULL,
    duration_minutes DECIMAL(10,2) NULL,
    distance_km DECIMAL(10,2) NULL,
    fuel_used DECIMAL(8,2) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    notes TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_driver_performance_log_driver FOREIGN KEY (driver_id) REFERENCES tigu_driver (id) ON DELETE CASCADE,
    CONSTRAINT fk_driver_performance_log_order FOREIGN KEY (order_id) REFERENCES tigu_order (id) ON DELETE SET NULL,
    INDEX idx_driver_performance_log_driver (driver_id),
    INDEX idx_driver_performance_log_order (order_id),
    INDEX idx_driver_performance_log_action (action_type),
    INDEX idx_driver_performance_log_timestamp (action_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS driver_alert (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    driver_id BIGINT UNSIGNED NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    metric_value DECIMAL(10,2) NULL,
    threshold_value DECIMAL(10,2) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    acknowledged_at DATETIME(6) NULL,
    resolved_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_driver_alert_driver FOREIGN KEY (driver_id) REFERENCES tigu_driver (id) ON DELETE CASCADE,
    INDEX idx_driver_alert_driver (driver_id),
    INDEX idx_driver_alert_status (status),
    INDEX idx_driver_alert_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
