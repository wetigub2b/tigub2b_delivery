-- Test Data: Insert sample drivers
-- Date: 2025-10-24
-- Description: Inserts test driver data. Can be run repeatedly without duplicates.

-- Insert test drivers (phone is unique, so duplicates will be ignored)
INSERT INTO tigu_driver (name, phone, email, license_number, vehicle_type, vehicle_plate, vehicle_model, status, rating, total_deliveries, notes)
VALUES
    ('John Smith', '+1-555-0101', 'john.smith@example.com', 'DL123456', 'Van', 'ABC-1234', 'Ford Transit 2022', 1, 4.85, 156, 'Experienced driver, good with fragile items'),
    ('Maria Garcia', '+1-555-0102', 'maria.garcia@example.com', 'DL234567', 'Truck', 'XYZ-5678', 'Mercedes Sprinter 2023', 1, 4.92, 203, 'Fast and reliable'),
    ('Wei Zhang', '+1-555-0103', 'wei.zhang@example.com', 'DL345678', 'Van', 'LMN-9012', 'Toyota Hiace 2021', 1, 4.78, 89, 'New to the team'),
    ('Ahmed Hassan', '+1-555-0104', 'ahmed.hassan@example.com', 'DL456789', 'Truck', 'PQR-3456', 'Isuzu NPR 2022', 1, 4.95, 312, 'Top rated driver, very professional'),
    ('Sarah Johnson', '+1-555-0105', 'sarah.johnson@example.com', 'DL567890', 'Van', 'STU-7890', 'Ram ProMaster 2023', 1, 4.88, 178, 'Specializes in urgent deliveries'),
    ('Carlos Rodriguez', '+1-555-0106', 'carlos.rodriguez@example.com', 'DL678901', 'Truck', 'VWX-2345', 'Freightliner M2 2020', 0, 4.65, 245, 'Currently on leave'),
    ('Yuki Tanaka', '+1-555-0107', 'yuki.tanaka@example.com', 'DL789012', 'Van', 'YZA-6789', 'Nissan NV 2022', 1, 4.90, 134, 'Excellent customer service'),
    ('Michael Brown', '+1-555-0108', 'michael.brown@example.com', 'DL890123', 'Van', 'BCD-0123', 'Chevrolet Express 2021', 1, 4.82, 167, 'Good with heavy loads'),
    ('Priya Patel', '+1-555-0109', 'priya.patel@example.com', 'DL901234', 'Truck', 'EFG-4567', 'Hino 268A 2023', 1, 4.94, 221, 'Very punctual and organized'),
    ('David Kim', '+1-555-0110', 'david.kim@example.com', 'DL012345', 'Van', 'HIJ-8901', 'Ford E-Series 2020', 1, 4.76, 98, 'Weekend driver')
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

-- Display inserted drivers
SELECT
    id,
    name,
    phone,
    vehicle_type,
    vehicle_plate,
    status,
    rating,
    total_deliveries
FROM tigu_driver
ORDER BY id;
