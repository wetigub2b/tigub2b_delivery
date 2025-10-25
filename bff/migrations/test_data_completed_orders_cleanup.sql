-- Test Data Cleanup: Remove completed test orders
-- Date: 2025-10-24
-- Description: Removes completed test order data (TEST-COMPLETE-*)

USE tigu_b2b;

-- Delete order items first (due to foreign key constraint)
DELETE FROM tigu_order_item
WHERE order_id IN (
    SELECT id FROM tigu_order WHERE order_sn LIKE 'TEST-COMPLETE-%'
);

-- Delete completed test orders
DELETE FROM tigu_order
WHERE order_sn LIKE 'TEST-COMPLETE-%';

-- Display remaining test orders for driver_id = 11
SELECT '=== Remaining Test Orders for Driver 11 ===' as Status;

SELECT
    o.order_sn,
    o.receiver_name,
    o.shipping_status,
    CASE o.shipping_status
        WHEN 0 THEN 'Pending Pickup'
        WHEN 1 THEN 'In Transit'
        WHEN 2 THEN 'Partially Shipped'
        WHEN 3 THEN 'Delivered'
    END as status_label,
    o.driver_id
FROM tigu_order o
WHERE o.driver_id = 11
ORDER BY o.shipping_status, o.order_sn;

-- Summary count by status
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
