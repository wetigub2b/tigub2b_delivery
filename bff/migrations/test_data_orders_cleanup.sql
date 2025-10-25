-- Test Data Cleanup: Remove sample orders
-- Date: 2025-10-24
-- Description: Removes all test order data

-- Delete order items first (due to foreign key)
DELETE FROM tigu_order_item
WHERE order_id IN (
    SELECT id FROM tigu_order WHERE order_sn LIKE 'TEST-ORD-%'
);

-- Delete test orders
DELETE FROM tigu_order
WHERE order_sn LIKE 'TEST-ORD-%';

-- Display remaining orders count
SELECT
    COUNT(*) as total_orders,
    SUM(CASE WHEN shipping_status = 0 THEN 1 ELSE 0 END) as pending_pickup,
    SUM(CASE WHEN shipping_status = 1 THEN 1 ELSE 0 END) as in_transit,
    SUM(CASE WHEN shipping_status = 2 THEN 1 ELSE 0 END) as partially_shipped,
    SUM(CASE WHEN shipping_status = 3 THEN 1 ELSE 0 END) as delivered
FROM tigu_order;
