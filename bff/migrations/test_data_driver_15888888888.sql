-- Test Data: Insert driver with phone 15888888888
-- Date: 2025-10-24
-- Description: Creates a test driver for phone number 15888888888

INSERT INTO tigu_driver (name, phone, email, license_number, vehicle_type, vehicle_plate, vehicle_model, status, rating, total_deliveries, notes)
VALUES
    ('Test Driver', '15888888888', 'testdriver@example.com', 'DL888888', 'Van', 'TEST-888', 'Ford Transit 2023', 1, 5.00, 50, 'Test driver account')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    email = VALUES(email),
    license_number = VALUES(license_number),
    vehicle_type = VALUES(vehicle_type),
    vehicle_plate = VALUES(vehicle_plate),
    vehicle_model = VALUES(vehicle_model),
    status = VALUES(status),
    rating = VALUES(rating),
    total_deliveries = VALUES(total_deliveries),
    notes = VALUES(notes);

-- Display the driver
SELECT * FROM tigu_driver WHERE phone = '15888888888';
