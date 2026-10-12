-- ============================================================================
-- HOTEL RESERVATION & GUEST SERVICES DBMS PROJECT
-- Realistic Sample Data Population
-- ============================================================================

USE hotel_management_db;

-- 1. Departments
INSERT INTO departments (name, description) VALUES
('Front Office', 'Guest reception, check-in, check-out, concierge and bell desk services'),
('Housekeeping', 'Room cleaning, linen management, turndown and sanitization services'),
('Food & Beverage', 'Fine dining restaurant, bar, and 24/7 in-room dining services'),
('Spa & Wellness', 'Massage therapy, sauna, personal training and wellness packages'),
('Maintenance & Engineering', 'HVAC, plumbing, electrical and structural maintenance')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- 2. Staff
INSERT INTO staff (dept_id, first_name, last_name, email, phone, role, salary, hire_date, status) VALUES
(1, 'Alexander', 'Wright', 'alex.wright@grandazure.com', '+1-555-0101', 'Front Desk Manager', 55000.00, '2023-01-15', 'ACTIVE'),
(1, 'Sophia', 'Chen', 'sophia.chen@grandazure.com', '+1-555-0102', 'Concierge Specialist', 42000.00, '2023-04-10', 'ACTIVE'),
(2, 'Marcus', 'Rodriguez', 'marcus.r@grandazure.com', '+1-555-0201', 'Housekeeping Supervisor', 48000.00, '2022-11-01', 'ACTIVE'),
(2, 'Elena', 'Petrova', 'elena.p@grandazure.com', '+1-555-0202', 'Senior Room Attendant', 36000.00, '2023-06-12', 'ACTIVE'),
(3, 'Chef Jean-Luc', 'Dubois', 'jeanluc.d@grandazure.com', '+1-555-0301', 'Executive Head Chef', 72000.00, '2022-03-20', 'ACTIVE'),
(3, 'David', 'Kim', 'david.kim@grandazure.com', '+1-555-0302', 'Room Service Lead Server', 38000.00, '2023-08-01', 'ACTIVE'),
(4, 'Amara', 'Okonkwo', 'amara.o@grandazure.com', '+1-555-0401', 'Lead Spa Therapist', 46000.00, '2023-02-14', 'ACTIVE'),
(5, 'Liam', 'O''Connor', 'liam.oc@grandazure.com', '+1-555-0501', 'Chief Maintenance Technician', 51000.00, '2022-09-05', 'ACTIVE')
ON DUPLICATE KEY UPDATE salary=VALUES(salary);

-- 3. Room Types
INSERT INTO room_types (type_name, base_price_per_night, max_occupancy, bed_type, amenities, description) VALUES
('Deluxe King Suite', 220.00, 2, '1 King Bed', 'City View, High-Speed Wi-Fi, Smart 55" TV, Rain Shower, Mini-Bar, Nespresso Machine', 'Spacious luxury room with floor-to-ceiling windows and panoramic skyline views.'),
('Executive Double Queen', 260.00, 4, '2 Queen Beds', 'Balcony, Marble Bathroom, Double Vanity, Workstation, High-Speed Wi-Fi, Safe', 'Ideal for executive travel and families, complete with dedicated ergonomic workstation.'),
('Presidential Penthouse', 650.00, 6, '2 King Beds + Sofa Bed', 'Private Terrace, Jacuzzi, Dining Room, Butler Service, Ocean/Skyline View, Premium Audio', 'Ultimate luxury experience featuring private terrace, bespoke butler service, and jacuzzi.'),
('Standard Cozy Room', 140.00, 2, '1 Queen Bed', 'Courtyard View, Wi-Fi, 43" Smart TV, Ensuite Bathroom, Coffee Station', 'Comfortable modern accommodation offering great value and serene courtyard serenity.')
ON DUPLICATE KEY UPDATE base_price_per_night=VALUES(base_price_per_night);

-- 4. Rooms
INSERT INTO rooms (room_number, floor, type_id, status) VALUES
('101', 1, 4, 'AVAILABLE'),
('102', 1, 4, 'AVAILABLE'),
('103', 1, 4, 'MAINTENANCE'),
('201', 2, 1, 'OCCUPIED'),
('202', 2, 1, 'AVAILABLE'),
('203', 2, 1, 'BOOKED'),
('301', 3, 2, 'OCCUPIED'),
('302', 3, 2, 'CLEANING'),
('401', 4, 3, 'OCCUPIED'),
('402', 4, 3, 'AVAILABLE')
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- 5. Guests
INSERT INTO guests (first_name, last_name, email, phone, id_proof_type, id_proof_number, address) VALUES
('Eleanor', 'Vance', 'eleanor.vance@example.com', '+1-202-555-0143', 'PASSPORT', 'USA94820149', '742 Evergreen Terrace, Seattle, WA'),
('Julian', 'Sterling', 'julian.sterling@example.com', '+1-312-555-0199', 'NATIONAL_ID', 'ID88204910', '1200 Lake Shore Drive, Chicago, IL'),
('Dr. Aisha', 'Khan', 'aisha.khan@example.com', '+44-7700-900077', 'PASSPORT', 'GBR71829011', '45 Kensington Gardens, London, UK'),
('Carlos', 'Mendoza', 'carlos.m@example.com', '+1-415-555-0182', 'DRIVING_LICENSE', 'DL-CA-4910294', '88 Mission St, San Francisco, CA'),
('Hannah', 'Schmidt', 'hannah.s@example.com', '+49-151-5550123', 'PASSPORT', 'DEU99301290', 'Blumenstrasse 14, Munich, Germany')
ON DUPLICATE KEY UPDATE phone=VALUES(phone);

-- 6. Service Categories
INSERT INTO service_categories (name, description) VALUES
('Dining & Room Service', 'Gourmet in-room breakfast, lunches, dinners, beverages and snacks'),
('Housekeeping & Laundry', 'Extra pillows, towel replacement, dry cleaning and express laundry'),
('Spa & Wellness', 'Deep tissue massage, aromatherapy, facial therapy and private sauna sessions'),
('Concierge & Transport', 'Airport luxury limousine transfers, VIP city tours, and valet parking')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- 7. Services
INSERT INTO services (category_id, service_name, unit_price, description, is_available) VALUES
(1, 'Continental Champagne Breakfast', 38.00, 'Freshly baked pastries, smoked salmon, organic fruits, artisan coffee and Moët champagne', TRUE),
(1, 'Wagyu Ribeye Steak (Dinner)', 65.00, 'Prime dry-aged Wagyu beef, truffle mashed potatoes, grilled asparagus and red wine jus', TRUE),
(1, 'Club Sandwich & Truffle Fries', 22.00, 'Triple-decker smoked turkey, crispy bacon, avocado, paired with hand-cut parmesan truffle fries', TRUE),
(1, 'Artisan Cocktail / Wine Bottle', 45.00, 'Selection of sommelier-curated vintage wines or bespoke craft cocktail shaker', TRUE),
(2, 'Express Dry Cleaning (Per Suit)', 30.00, 'Same-day steam press and luxury garment dry cleaning service', TRUE),
(2, 'Luxury Bed Turndown & Aromatherapy', 15.00, 'Evening lavender pillow mist, premium chocolates, and warm herbal tea setup', TRUE),
(3, 'Swedish Full Body Massage (60 min)', 110.00, 'Relaxing full body tension release massage with organic botanical essential oils', TRUE),
(3, 'Deep Detox Facial Treatment', 85.00, 'Hydrating anti-aging facial utilizing vitamin serums and lymphatic drainage massage', TRUE),
(4, 'Executive Airport Chauffeur Transfer', 95.00, 'Direct airport transfer in Mercedes S-Class or BMW 7-Series with Wi-Fi and chilled water', TRUE)
ON DUPLICATE KEY UPDATE unit_price=VALUES(unit_price);

-- 8. Realistic Reservations
INSERT INTO reservations (reservation_id, guest_id, check_in_date, check_out_date, number_of_guests, status, special_requests, total_room_cost) VALUES
(1001, 1, '2026-10-10', '2026-10-14', 2, 'CHECKED_IN', 'High floor preferred, late check-out requested', 880.00),
(1002, 2, '2026-10-11', '2026-10-15', 3, 'CHECKED_IN', 'Extra hypoallergenic pillows, quiet room', 1040.00),
(1003, 3, '2026-10-12', '2026-10-16', 2, 'CHECKED_IN', 'VIP Welcome amenity, fruit platter', 2600.00),
(1004, 4, '2026-10-18', '2026-10-21', 1, 'CONFIRMED', 'Airport pickup coordination needed', 660.00),
(1005, 5, '2026-10-05', '2026-10-09', 2, 'CHECKED_OUT', 'Anniversary celebration package', 880.00)
ON DUPLICATE KEY UPDATE total_room_cost=VALUES(total_room_cost);

-- 9. Reservation Rooms
INSERT INTO reservation_rooms (reservation_id, room_id, price_per_night) VALUES
(1001, 4, 220.00), -- Room 201
(1002, 7, 260.00), -- Room 301
(1003, 9, 650.00), -- Room 401
(1004, 6, 220.00), -- Room 203
(1005, 5, 220.00)  -- Room 202
ON DUPLICATE KEY UPDATE price_per_night=VALUES(price_per_night);

-- 10. Guest Service Orders
INSERT INTO guest_service_orders (order_id, reservation_id, room_id, service_id, staff_id, quantity, unit_price, total_price, order_status, notes) VALUES
(201, 1001, 4, 1, 6, 2, 38.00, 76.00, 'COMPLETED', 'Delivered at 08:30 AM with hot coffee'),
(202, 1001, 4, 7, 7, 1, 110.00, 110.00, 'IN_PROGRESS', 'Spa appointment booked for 4:00 PM today'),
(203, 1002, 7, 2, 6, 2, 65.00, 130.00, 'COMPLETED', 'Medium-rare steak, delivered to Room 301'),
(204, 1002, 7, 5, 4, 2, 30.00, 60.00, 'PENDING', 'Two formal business suits to dry clean before tomorrow 9 AM'),
(205, 1003, 9, 4, 6, 2, 45.00, 90.00, 'COMPLETED', 'Vintage Pinot Noir served in Presidential suite'),
(206, 1003, 9, 9, 2, 1, 95.00, 95.00, 'PENDING', 'Mercedes pickup scheduled at departure')
ON DUPLICATE KEY UPDATE total_price=VALUES(total_price);

-- 11. Invoices & Payments for Checked Out Guest (1005)
INSERT INTO billing_invoices (invoice_id, reservation_id, room_charges, service_charges, tax_amount, discount_amount, grand_total, payment_status) VALUES
(501, 1005, 880.00, 148.00, 123.36, 0.00, 1151.36, 'PAID')
ON DUPLICATE KEY UPDATE grand_total=VALUES(grand_total);

INSERT INTO payments (payment_id, invoice_id, amount, payment_method, transaction_ref, notes) VALUES
(901, 501, 1151.36, 'CREDIT_CARD', 'TXN_CHASE_994821', 'Settled in full upon checkout by Hannah Schmidt')
ON DUPLICATE KEY UPDATE amount=VALUES(amount);

-- 12. Audit Logs Seed
INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES
('INITIALIZE', 'system', 1, 'Database schema seeded with luxury hotel guest services catalog and rooms'),
('CHECK_IN', 'reservations', 1001, 'Guest Eleanor Vance checked into Room 201'),
('CHECK_IN', 'reservations', 1002, 'Guest Julian Sterling checked into Room 301'),
('CHECK_IN', 'reservations', 1003, 'Guest Dr. Aisha Khan checked into Room 401');
