-- Seed Data: Driver performance metrics, logs, and alerts
-- Date: 2025-10-24
-- Description: Inserts sample performance data for dashboard testing

USE tigu_b2b;

-- Resolve driver_id for the seeded driver account
SET @driver_id := (SELECT id FROM tigu_driver WHERE phone = '15888888888' LIMIT 1);

-- Exit early if the driver does not exist
SET @missing_driver := (@driver_id IS NULL);

-- Derive analysis window (last 30 days)
SET @period_start := DATE_SUB(DATE(NOW()), INTERVAL 30 DAY);
SET @period_end := DATE(NOW());

-- Insert aggregated performance metrics when missing
INSERT INTO driver_performance (
    driver_id,
    period_start,
    period_end,
    total_deliveries,
    successful_deliveries,
    failed_deliveries,
    avg_delivery_time,
    total_active_time,
    total_distance,
    customer_rating,
    on_time_percentage,
    orders_per_hour,
    fuel_efficiency
)
SELECT
    @driver_id,
    @period_start,
    @period_end,
    120,
    110,
    10,
    42.50,
    360.0,
    820.5,
    4.65,
    92.50,
    3.8,
    12.5
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1
        FROM driver_performance
        WHERE driver_id = @driver_id
          AND period_start = @period_start
          AND period_end = @period_end
    );

-- Link test order ids for log entries
SET @order_1 := (SELECT id FROM tigu_order WHERE order_sn = 'TEST-ORD-004' LIMIT 1);
SET @order_2 := (SELECT id FROM tigu_order WHERE order_sn = 'TEST-ORD-005' LIMIT 1);
SET @order_3 := (SELECT id FROM tigu_order WHERE order_sn = 'TEST-ORD-006' LIMIT 1);

-- Insert recent performance logs if they are absent
INSERT INTO driver_performance_log (
    driver_id,
    order_id,
    action_type,
    action_timestamp,
    latitude,
    longitude,
    duration_minutes,
    distance_km,
    fuel_used,
    status,
    notes
)
SELECT
    @driver_id,
    @order_1,
    'delivery',
    DATE_SUB(NOW(), INTERVAL 2 DAY),
    43.6532,
    -79.3832,
    38.5,
    18.2,
    2.1,
    'completed',
    'Delivered downtown order ahead of schedule'
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_performance_log
        WHERE driver_id = @driver_id
          AND order_id = @order_1
          AND action_type = 'delivery'
    );

INSERT INTO driver_performance_log (
    driver_id,
    order_id,
    action_type,
    action_timestamp,
    latitude,
    longitude,
    duration_minutes,
    distance_km,
    fuel_used,
    status,
    notes
)
SELECT
    @driver_id,
    @order_2,
    'pickup',
    DATE_SUB(NOW(), INTERVAL 1 DAY),
    43.8561,
    -79.3370,
    24.0,
    9.4,
    1.2,
    'completed',
    'Late pickup due to warehouse congestion'
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_performance_log
        WHERE driver_id = @driver_id
          AND order_id = @order_2
          AND action_type = 'pickup'
    );

INSERT INTO driver_performance_log (
    driver_id,
    order_id,
    action_type,
    action_timestamp,
    latitude,
    longitude,
    duration_minutes,
    distance_km,
    fuel_used,
    status,
    notes
)
SELECT
    @driver_id,
    @order_3,
    'route_start',
    DATE_SUB(NOW(), INTERVAL 12 HOUR),
    43.7001,
    -79.4163,
    15.0,
    0.0,
    NULL,
    'completed',
    'Started evening delivery route'
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_performance_log
        WHERE driver_id = @driver_id
          AND order_id = @order_3
          AND action_type = 'route_start'
    );

-- Insert dashboard alerts
INSERT INTO driver_alert (
    driver_id,
    alert_type,
    severity,
    title,
    description,
    metric_value,
    threshold_value,
    status
)
SELECT
    @driver_id,
    'performance_drop',
    'critical',
    'Success rate dipped below SLA',
    'Driver success rate fell under 90% during the past week. Review delivery blockers.',
    88.5,
    95.0,
    'open'
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_alert
        WHERE driver_id = @driver_id
          AND alert_type = 'performance_drop'
          AND severity = 'critical'
    );

INSERT INTO driver_alert (
    driver_id,
    alert_type,
    severity,
    title,
    description,
    metric_value,
    threshold_value,
    status
)
SELECT
    @driver_id,
    'late_delivery',
    'medium',
    '3 late deliveries this week',
    'Multiple orders exceeded the on-time threshold. Coordinate route coaching.',
    3,
    1,
    'open'
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_alert
        WHERE driver_id = @driver_id
          AND alert_type = 'late_delivery'
    );

INSERT INTO driver_alert (
    driver_id,
    alert_type,
    severity,
    title,
    description,
    metric_value,
    threshold_value,
    status,
    acknowledged_at
)
SELECT
    @driver_id,
    'customer_complaint',
    'low',
    'Customer reported damaged package',
    'Package photo indicates minor damage. Awaiting resolution outcome.',
    NULL,
    NULL,
    'acknowledged',
    DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE @missing_driver = 0
  AND NOT EXISTS (
        SELECT 1 FROM driver_alert
        WHERE driver_id = @driver_id
          AND alert_type = 'customer_complaint'
    );

-- Show seeded data for verification
SELECT * FROM driver_performance WHERE driver_id = @driver_id ORDER BY created_at DESC LIMIT 5;
SELECT id, driver_id, alert_type, severity, status, created_at FROM driver_alert WHERE driver_id = @driver_id ORDER BY created_at DESC;
