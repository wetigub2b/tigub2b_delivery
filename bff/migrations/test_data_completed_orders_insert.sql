-- Test Data: Add completed orders for driver_id = 11
-- Date: 2025-10-24
-- Description: Creates test completed orders (shipping_status = 3) to populate the "Completed" tab in TaskBoard

USE tigu_b2b;

-- Get next available ID
SET @next_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM tigu_order);

-- Insert completed test orders (order_sn is unique)
INSERT INTO tigu_order (
    id, order_sn, user_id, shop_id, shipping_status, shipping_type, order_status, pay_status,
    receiver_name, receiver_phone, receiver_province, receiver_city, receiver_district, receiver_address,
    receiver_postal_code,
    driver_id, warehouse_id,
    total_amount, pay_amount, shipping_fee, pay_shipping_fee, vip_discount_amount,
    shipping_time, finish_time,
    create_time
)
VALUES
    -- Completed Order 1
    (
        @next_id + 0, 'TEST-COMPLETE-001', 1, 1, 3, 1, 3, 1,
        'George Chen', '+1-416-555-0107', 'Ontario', 'Toronto', 'Downtown', '789 King St W, Toronto',
        'M5V 1K1',
        11, 1,
        129.99, 129.99, 10.00, 10.00, 0.00,
        DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 12 HOUR),
        DATE_SUB(NOW(), INTERVAL 2 DAY)
    ),
    -- Completed Order 2
    (
        @next_id + 1, 'TEST-COMPLETE-002', 1, 1, 3, 1, 3, 1,
        'Helen Wu', '+1-416-555-0108', 'Ontario', 'Mississauga', 'Port Credit', '321 Lakeshore Rd, Mississauga',
        'L5B 3Y3',
        11, 1,
        349.99, 349.99, 15.00, 15.00, 0.00,
        DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY),
        DATE_SUB(NOW(), INTERVAL 3 DAY)
    ),
    -- Completed Order 3
    (
        @next_id + 2, 'TEST-COMPLETE-003', 1, 1, 3, 1, 3, 1,
        'Ivan Zhang', '+1-416-555-0109', 'Ontario', 'Markham', 'Unionville', '456 Highway 7 E, Markham',
        'L3R 1B5',
        11, 1,
        79.99, 79.99, 8.00, 8.00, 0.00,
        DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY),
        DATE_SUB(NOW(), INTERVAL 4 DAY)
    )
ON DUPLICATE KEY UPDATE
    receiver_name = VALUES(receiver_name),
    receiver_phone = VALUES(receiver_phone),
    receiver_address = VALUES(receiver_address),
    shipping_status = VALUES(shipping_status),
    driver_id = VALUES(driver_id);

-- Get next available ID for order items
SET @next_item_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM tigu_order_item);

-- Insert order items for completed orders
INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 0,
    o.id,
    1013,
    2013,
    '{"en": "Phone Case", "zh": "手机壳"}',
    '{"en": "Clear", "zh": "透明"}',
    'CASE-CLR-013',
    3,
    43.33,
    129.99
FROM tigu_order o
WHERE o.order_sn = 'TEST-COMPLETE-001'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 1,
    o.id,
    1014,
    2014,
    '{"en": "Tablet 10 inch", "zh": "10英寸平板电脑"}',
    '{"en": "64GB", "zh": "64GB"}',
    'TABLET-10-64-014',
    1,
    349.99,
    349.99
FROM tigu_order o
WHERE o.order_sn = 'TEST-COMPLETE-002'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 2,
    o.id,
    1015,
    2015,
    '{"en": "Power Bank 20000mAh", "zh": "20000mAh移动电源"}',
    '{"en": "Black", "zh": "黑色"}',
    'PWRBANK-20K-015',
    2,
    39.99,
    79.98
FROM tigu_order o
WHERE o.order_sn = 'TEST-COMPLETE-003'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Display inserted completed orders
SELECT '=== Completed Orders Created ===' as Status;

SELECT
    o.order_sn,
    o.receiver_name,
    o.receiver_address,
    o.shipping_status,
    CASE o.shipping_status
        WHEN 0 THEN 'Pending Pickup'
        WHEN 1 THEN 'In Transit'
        WHEN 2 THEN 'Partially Shipped'
        WHEN 3 THEN 'Delivered'
    END as status_label,
    o.driver_id,
    o.shipping_time,
    o.finish_time,
    COUNT(oi.id) as item_count
FROM tigu_order o
LEFT JOIN tigu_order_item oi ON o.id = oi.order_id
WHERE o.order_sn LIKE 'TEST-COMPLETE-%'
GROUP BY o.id
ORDER BY o.finish_time DESC;

-- Summary of all test orders for driver_id = 11
SELECT '=== All Test Orders Summary ===' as Status;

SELECT
    shipping_status,
    CASE shipping_status
        WHEN 0 THEN 'Pending Pickup'
        WHEN 1 THEN 'In Transit (Shipped)'
        WHEN 2 THEN 'In Transit (Partially)'
        WHEN 3 THEN 'Completed'
    END as status_label,
    COUNT(*) as count
FROM tigu_order
WHERE driver_id = 11
GROUP BY shipping_status
ORDER BY shipping_status;
