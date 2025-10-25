-- Test Data Cleanup: Remove sample drivers
-- Date: 2025-10-24
-- Description: Removes all test driver data

-- Remove driver assignments from orders first (due to foreign key)
UPDATE tigu_order
SET driver_id = NULL
WHERE driver_id IN (
    SELECT id FROM tigu_driver
    WHERE phone IN (
        '+1-555-0101', '+1-555-0102', '+1-555-0103', '+1-555-0104', '+1-555-0105',
        '+1-555-0106', '+1-555-0107', '+1-555-0108', '+1-555-0109', '+1-555-0110'
    )
);

-- Delete test drivers by their unique phone numbers
DELETE FROM tigu_driver
WHERE phone IN (
    '+1-555-0101', -- John Smith
    '+1-555-0102', -- Maria Garcia
    '+1-555-0103', -- Wei Zhang
    '+1-555-0104', -- Ahmed Hassan
    '+1-555-0105', -- Sarah Johnson
    '+1-555-0106', -- Carlos Rodriguez
    '+1-555-0107', -- Yuki Tanaka
    '+1-555-0108', -- Michael Brown
    '+1-555-0109', -- Priya Patel
    '+1-555-0110'  -- David Kim
);

-- Display remaining drivers count
SELECT
    COUNT(*) as remaining_drivers,
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as active_drivers
FROM tigu_driver;
