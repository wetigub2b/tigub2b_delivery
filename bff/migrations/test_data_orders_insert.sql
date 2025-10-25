-- Test Data: Insert sample orders for driver testing
-- Date: 2025-10-24
-- Description: Creates test orders assigned to driver with phone 15888888888

-- Get the driver ID for phone 15888888888
SET @driver_id = (SELECT id FROM tigu_driver WHERE phone = '15888888888');

-- Get next available ID
SET @next_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM tigu_order);

-- Insert test orders (order_sn is unique, so duplicates will be ignored)
INSERT INTO tigu_order (
    id, order_sn, user_id, shop_id, shipping_status, shipping_type, order_status, pay_status,
    receiver_name, receiver_phone, receiver_province, receiver_city, receiver_district, receiver_address,
    driver_id, total_amount, pay_amount, vip_discount_amount, create_time
)
VALUES
    -- Pending pickup orders (shipping_status = 0)
    (@next_id + 0, 'TEST-ORD-001', 1, 1, 0, 1, 1, 1, 'Alice Johnson', '+1-555-1001', 'Ontario', 'Toronto', 'Downtown', '123 King Street West, Unit 501', @driver_id, 59.98, 59.98, 0.00, NOW()),
    (@next_id + 1, 'TEST-ORD-002', 1, 1, 0, 1, 1, 1, 'Bob Smith', '+1-555-1002', 'Ontario', 'Toronto', 'Midtown', '456 Yonge Street, Apt 302', @driver_id, 49.99, 49.99, 0.00, NOW()),
    (@next_id + 2, 'TEST-ORD-003', 1, 1, 0, 1, 1, 1, 'Carol Wang', '+1-555-1003', 'Ontario', 'Toronto', 'North York', '789 Finch Avenue East, Suite 12', @driver_id, 79.99, 79.99, 0.00, NOW()),

    -- In transit orders (shipping_status = 1)
    (@next_id + 3, 'TEST-ORD-004', 1, 1, 1, 1, 2, 1, 'David Lee', '+1-555-1004', 'Ontario', 'Mississauga', 'Port Credit', '321 Lakeshore Road, Building A', @driver_id, 299.99, 299.99, 0.00, NOW()),
    (@next_id + 4, 'TEST-ORD-005', 1, 1, 1, 1, 2, 1, 'Emma Brown', '+1-555-1005', 'Ontario', 'Markham', 'Unionville', '654 Main Street, Unit 8', @driver_id, 179.97, 179.97, 0.00, NOW()),

    -- Partially shipped orders (shipping_status = 2)
    (@next_id + 5, 'TEST-ORD-006', 1, 1, 2, 1, 2, 1, 'Frank Zhang', '+1-555-1006', 'Ontario', 'Richmond Hill', 'Oak Ridges', '987 Highway 7, Suite 201', @driver_id, 79.98, 79.98, 0.00, NOW())
ON DUPLICATE KEY UPDATE
    receiver_name = VALUES(receiver_name),
    receiver_phone = VALUES(receiver_phone),
    receiver_address = VALUES(receiver_address),
    shipping_status = VALUES(shipping_status),
    driver_id = VALUES(driver_id);

-- Get next available ID for order items
SET @next_item_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM tigu_order_item);

-- Insert order items for each order
INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 0,
    o.id,
    1001,
    2001,
    '{"en": "Wireless Mouse", "zh": "无线鼠标"}',
    '{"en": "Black", "zh": "黑色"}',
    'MOUSE-BLK-001',
    2,
    29.99,
    59.98
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-001'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 1,
    o.id,
    1002,
    2002,
    '{"en": "USB Keyboard", "zh": "USB键盘"}',
    '{"en": "White", "zh": "白色"}',
    'KEYB-WHT-002',
    1,
    49.99,
    49.99
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-002'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 2,
    o.id,
    1003,
    2003,
    '{"en": "Laptop Stand", "zh": "笔记本电脑支架"}',
    '{"en": "Silver", "zh": "银色"}',
    'STAND-SLV-003',
    1,
    79.99,
    79.99
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-003'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 3,
    o.id,
    1004,
    2004,
    '{"en": "Monitor 27 inch", "zh": "27英寸显示器"}',
    '{"en": "4K", "zh": "4K"}',
    'MON-27-4K-004',
    1,
    299.99,
    299.99
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-004'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 4,
    o.id,
    1005,
    2005,
    '{"en": "Webcam HD", "zh": "高清网络摄像头"}',
    '{"en": "1080p", "zh": "1080p"}',
    'CAM-HD-1080-005',
    3,
    59.99,
    179.97
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-005'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO tigu_order_item (id, order_id, product_id, sku_id, product_name, sku_name, sku_code, quantity, price, total_price)
SELECT
    @next_item_id + 5,
    o.id,
    1006,
    2006,
    '{"en": "Desk Lamp LED", "zh": "LED台灯"}',
    '{"en": "Adjustable", "zh": "可调节"}',
    'LAMP-LED-ADJ-006',
    2,
    39.99,
    79.98
FROM tigu_order o
WHERE o.order_sn = 'TEST-ORD-006'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Display inserted orders
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
    d.name as driver_name,
    COUNT(oi.id) as item_count
FROM tigu_order o
LEFT JOIN tigu_driver d ON o.driver_id = d.id
LEFT JOIN tigu_order_item oi ON o.id = oi.order_id
WHERE o.order_sn LIKE 'TEST-ORD-%'
GROUP BY o.id
ORDER BY o.shipping_status, o.order_sn;
