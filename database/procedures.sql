-- ============================================================================
-- HOTEL RESERVATION & GUEST SERVICES DBMS PROJECT
-- Stored Procedures, Triggers, and Views
-- ============================================================================

USE hotel_management_db;

-- ----------------------------------------------------------------------------
-- TRIGGERS
-- ----------------------------------------------------------------------------

DELIMITER $$

-- Trigger 1: Auto-calculate service order total before insert
DROP TRIGGER IF EXISTS trg_calc_service_order_insert$$
CREATE TRIGGER trg_calc_service_order_insert
BEFORE INSERT ON guest_service_orders
FOR EACH ROW
BEGIN
    SET NEW.total_price = NEW.quantity * NEW.unit_price;
END$$

-- Trigger 2: Auto-calculate service order total before update
DROP TRIGGER IF EXISTS trg_calc_service_order_update$$
CREATE TRIGGER trg_calc_service_order_update
BEFORE UPDATE ON guest_service_orders
FOR EACH ROW
BEGIN
    SET NEW.total_price = NEW.quantity * NEW.unit_price;
END$$

-- Trigger 3: Audit log when reservation status changes
DROP TRIGGER IF EXISTS trg_audit_reservation_status$$
CREATE TRIGGER trg_audit_reservation_status
AFTER UPDATE ON reservations
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO audit_logs (action_type, table_affected, record_id, details)
        VALUES ('STATUS_CHANGE', 'reservations', NEW.reservation_id, 
                CONCAT('Reservation #', NEW.reservation_id, ' status changed from ', OLD.status, ' to ', NEW.status));
    END IF;
END$$

-- Trigger 4: Audit log on new guest registration
DROP TRIGGER IF EXISTS trg_audit_guest_insert$$
CREATE TRIGGER trg_audit_guest_insert
AFTER INSERT ON guests
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (action_type, table_affected, record_id, details)
    VALUES ('CREATE', 'guests', NEW.guest_id, 
            CONCAT('Registered new guest: ', NEW.first_name, ' ', NEW.last_name, ' (', NEW.email, ')'));
END$$

DELIMITER ;

-- ----------------------------------------------------------------------------
-- STORED PROCEDURES
-- ----------------------------------------------------------------------------

DELIMITER $$

-- Procedure 1: Create a new Reservation atomically
DROP PROCEDURE IF EXISTS sp_create_reservation$$
CREATE PROCEDURE sp_create_reservation(
    IN p_guest_id INT,
    IN p_room_id INT,
    IN p_check_in DATE,
    IN p_check_out DATE,
    IN p_num_guests INT,
    IN p_special_requests TEXT,
    OUT p_reservation_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_room_status VARCHAR(20);
    DECLARE v_price_per_night DECIMAL(10, 2);
    DECLARE v_nights INT;
    DECLARE v_total_cost DECIMAL(10, 2);

    -- Calculate duration
    SET v_nights = DATEDIFF(p_check_out, p_check_in);
    
    IF v_nights <= 0 THEN
        SET p_reservation_id = NULL;
        SET p_message = 'Check-out date must be strictly after check-in date.';
    ELSE
        -- Check room availability
        SELECT r.status, rt.base_price_per_night INTO v_room_status, v_price_per_night
        FROM rooms r
        JOIN room_types rt ON r.type_id = rt.type_id
        WHERE r.room_id = p_room_id;

        IF v_room_status IS NULL THEN
            SET p_reservation_id = NULL;
            SET p_message = 'Specified room does not exist.';
        ELSEIF v_room_status <> 'AVAILABLE' THEN
            SET p_reservation_id = NULL;
            SET p_message = CONCAT('Room is currently ', v_room_status, ' and cannot be booked.');
        ELSE
            SET v_total_cost = v_nights * v_price_per_night;

            -- Insert reservation record
            INSERT INTO reservations (guest_id, check_in_date, check_out_date, number_of_guests, special_requests, total_room_cost, status)
            VALUES (p_guest_id, p_check_in, p_check_out, p_num_guests, p_special_requests, v_total_cost, 'CONFIRMED');

            SET p_reservation_id = LAST_INSERT_ID();

            -- Link room
            INSERT INTO reservation_rooms (reservation_id, room_id, price_per_night)
            VALUES (p_reservation_id, p_room_id, v_price_per_night);

            -- Update room status
            UPDATE rooms SET status = 'BOOKED' WHERE room_id = p_room_id;

            SET p_message = 'Reservation created successfully!';
        END IF;
    END IF;
END$$

-- Procedure 2: Check-In Guest
DROP PROCEDURE IF EXISTS sp_check_in$$
CREATE PROCEDURE sp_check_in(
    IN p_reservation_id INT,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_curr_status VARCHAR(20);

    SELECT status INTO v_curr_status
    FROM reservations
    WHERE reservation_id = p_reservation_id;

    IF v_curr_status IS NULL THEN
        SET p_success = FALSE;
        SET p_message = 'Reservation not found.';
    ELSEIF v_curr_status <> 'CONFIRMED' THEN
        SET p_success = FALSE;
        SET p_message = CONCAT('Cannot check-in. Current reservation status is ', v_curr_status);
    ELSE
        UPDATE reservations SET status = 'CHECKED_IN' WHERE reservation_id = p_reservation_id;

        -- Update room status to OCCUPIED
        UPDATE rooms r
        JOIN reservation_rooms rr ON r.room_id = rr.room_id
        SET r.status = 'OCCUPIED'
        WHERE rr.reservation_id = p_reservation_id;

        SET p_success = TRUE;
        SET p_message = 'Guest checked in successfully. Room status is now OCCUPIED.';
    END IF;
END$$

-- Procedure 3: Request / Order a Guest Service
DROP PROCEDURE IF EXISTS sp_order_guest_service$$
CREATE PROCEDURE sp_order_guest_service(
    IN p_reservation_id INT,
    IN p_room_id INT,
    IN p_service_id INT,
    IN p_staff_id INT,
    IN p_quantity INT,
    IN p_notes TEXT,
    OUT p_order_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_unit_price DECIMAL(10, 2);
    DECLARE v_is_available BOOLEAN;

    SELECT unit_price, is_available INTO v_unit_price, v_is_available
    FROM services
    WHERE service_id = p_service_id;

    IF v_unit_price IS NULL THEN
        SET p_order_id = NULL;
        SET p_message = 'Service not found.';
    ELSEIF NOT v_is_available THEN
        SET p_order_id = NULL;
        SET p_message = 'Service is currently unavailable.';
    ELSE
        INSERT INTO guest_service_orders (
            reservation_id, room_id, service_id, staff_id, quantity, unit_price, total_price, order_status, notes
        )
        VALUES (
            p_reservation_id, p_room_id, p_service_id, p_staff_id, p_quantity, v_unit_price, (p_quantity * v_unit_price), 'PENDING', p_notes
        );

        SET p_order_id = LAST_INSERT_ID();
        SET p_message = 'Guest service requested successfully.';
    END IF;
END$$

-- Procedure 4: Check-out and generate final invoice
DROP PROCEDURE IF EXISTS sp_generate_checkout_bill$$
CREATE PROCEDURE sp_generate_checkout_bill(
    IN p_reservation_id INT,
    IN p_discount_percent DECIMAL(5, 2),
    OUT p_invoice_id INT,
    OUT p_grand_total DECIMAL(10, 2),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_room_charges DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_service_charges DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_tax_amount DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_discount_amount DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_subtotal DECIMAL(10, 2) DEFAULT 0.00;

    -- Retrieve room total
    SELECT total_room_cost INTO v_room_charges
    FROM reservations
    WHERE reservation_id = p_reservation_id;

    -- Aggregate completed service charges
    SELECT COALESCE(SUM(total_price), 0.00) INTO v_service_charges
    FROM guest_service_orders
    WHERE reservation_id = p_reservation_id AND order_status <> 'CANCELLED';

    SET v_subtotal = v_room_charges + v_service_charges;
    SET v_discount_amount = (v_subtotal * COALESCE(p_discount_percent, 0.00)) / 100.00;
    -- Standard 12% luxury tax / hospitality GST
    SET v_tax_amount = (v_subtotal - v_discount_amount) * 0.12;
    SET p_grand_total = (v_subtotal - v_discount_amount) + v_tax_amount;

    -- Create or update invoice
    INSERT INTO billing_invoices (
        reservation_id, room_charges, service_charges, tax_amount, discount_amount, grand_total, payment_status
    )
    VALUES (
        p_reservation_id, v_room_charges, v_service_charges, v_tax_amount, v_discount_amount, p_grand_total, 'UNPAID'
    )
    ON DUPLICATE KEY UPDATE
        room_charges = VALUES(room_charges),
        service_charges = VALUES(service_charges),
        tax_amount = VALUES(tax_amount),
        discount_amount = VALUES(discount_amount),
        grand_total = VALUES(grand_total);

    SELECT invoice_id INTO p_invoice_id
    FROM billing_invoices
    WHERE reservation_id = p_reservation_id;

    -- Mark reservation as checked out
    UPDATE reservations SET status = 'CHECKED_OUT' WHERE reservation_id = p_reservation_id;

    -- Mark rooms as CLEANING
    UPDATE rooms r
    JOIN reservation_rooms rr ON r.room_id = rr.room_id
    SET r.status = 'CLEANING'
    WHERE rr.reservation_id = p_reservation_id;

    SET p_message = 'Guest checked out. Invoice created and rooms moved to cleaning.';
END$$

-- Procedure 5: Record Payment
DROP PROCEDURE IF EXISTS sp_record_payment$$
CREATE PROCEDURE sp_record_payment(
    IN p_invoice_id INT,
    IN p_amount DECIMAL(10, 2),
    IN p_method VARCHAR(20),
    IN p_transaction_ref VARCHAR(100),
    IN p_notes TEXT,
    OUT p_payment_id INT,
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_grand_total DECIMAL(10, 2);
    DECLARE v_paid_so_far DECIMAL(10, 2);

    SELECT grand_total INTO v_grand_total
    FROM billing_invoices
    WHERE invoice_id = p_invoice_id;

    IF v_grand_total IS NULL THEN
        SET p_payment_id = NULL;
        SET p_status = 'ERROR';
        SET p_message = 'Invoice does not exist.';
    ELSE
        INSERT INTO payments (invoice_id, amount, payment_method, transaction_ref, notes)
        VALUES (p_invoice_id, p_amount, p_method, p_transaction_ref, p_notes);

        SET p_payment_id = LAST_INSERT_ID();

        SELECT COALESCE(SUM(amount), 0.00) INTO v_paid_so_far
        FROM payments
        WHERE invoice_id = p_invoice_id;

        IF v_paid_so_far >= v_grand_total THEN
            UPDATE billing_invoices SET payment_status = 'PAID' WHERE invoice_id = p_invoice_id;
            SET p_status = 'PAID';
            SET p_message = 'Payment recorded. Invoice fully settled!';
        ELSE
            UPDATE billing_invoices SET payment_status = 'PARTIALLY_PAID' WHERE invoice_id = p_invoice_id;
            SET p_status = 'PARTIALLY_PAID';
            SET p_message = CONCAT('Payment recorded. Remaining balance: $', FORMAT(v_grand_total - v_paid_so_far, 2));
        END IF;
    END IF;
END$$

DELIMITER ;

-- ----------------------------------------------------------------------------
-- VIEWS (Complex joins, reporting, aggregates)
-- ----------------------------------------------------------------------------

-- View 1: Active guest stays with accrued service cost
CREATE OR REPLACE VIEW vw_active_guest_stays AS
SELECT 
    r.reservation_id,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_name,
    g.email,
    g.phone,
    rm.room_number,
    rt.type_name AS room_type,
    r.check_in_date,
    r.check_out_date,
    r.number_of_guests,
    r.status AS reservation_status,
    r.total_room_cost,
    COALESCE(SUM(gso.total_price), 0.00) AS service_charges_accrued
FROM reservations r
JOIN guests g ON r.guest_id = g.guest_id
JOIN reservation_rooms rr ON r.reservation_id = rr.reservation_id
JOIN rooms rm ON rr.room_id = rm.room_id
JOIN room_types rt ON rm.type_id = rt.type_id
LEFT JOIN guest_service_orders gso ON r.reservation_id = gso.reservation_id AND gso.order_status <> 'CANCELLED'
WHERE r.status = 'CHECKED_IN'
GROUP BY r.reservation_id, rm.room_number, rt.type_name, g.first_name, g.last_name, g.email, g.phone, r.check_in_date, r.check_out_date, r.number_of_guests, r.status, r.total_room_cost;

-- View 2: Room occupancy & live status
CREATE OR REPLACE VIEW vw_room_inventory AS
SELECT 
    r.room_id,
    r.room_number,
    r.floor,
    rt.type_name,
    rt.base_price_per_night,
    rt.bed_type,
    r.status AS room_status,
    (
        SELECT CONCAT(g.first_name, ' ', g.last_name)
        FROM reservation_rooms rr
        JOIN reservations res ON rr.reservation_id = res.reservation_id
        JOIN guests g ON res.guest_id = g.guest_id
        WHERE rr.room_id = r.room_id AND res.status IN ('CONFIRMED', 'CHECKED_IN')
        LIMIT 1
    ) AS current_guest
FROM rooms r
JOIN room_types rt ON r.type_id = rt.type_id;

-- View 3: Pending guest service requests
CREATE OR REPLACE VIEW vw_pending_services AS
SELECT 
    gso.order_id,
    rm.room_number,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_name,
    sc.name AS category_name,
    s.service_name,
    gso.quantity,
    gso.total_price,
    gso.order_status,
    gso.order_time,
    CONCAT(st.first_name, ' ', st.last_name) AS assigned_staff,
    gso.notes
FROM guest_service_orders gso
JOIN rooms rm ON gso.room_id = rm.room_id
JOIN reservations r ON gso.reservation_id = r.reservation_id
JOIN guests g ON r.guest_id = g.guest_id
JOIN services s ON gso.service_id = s.service_id
JOIN service_categories sc ON s.category_id = sc.category_id
LEFT JOIN staff st ON gso.staff_id = st.staff_id
WHERE gso.order_status IN ('PENDING', 'IN_PROGRESS');

-- View 4: Financial & Billing Summary
CREATE OR REPLACE VIEW vw_financial_summary AS
SELECT 
    bi.invoice_id,
    bi.reservation_id,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_name,
    g.email AS guest_email,
    bi.room_charges,
    bi.service_charges,
    bi.tax_amount,
    bi.discount_amount,
    bi.grand_total,
    bi.payment_status,
    COALESCE(SUM(p.amount), 0.00) AS total_paid,
    (bi.grand_total - COALESCE(SUM(p.amount), 0.00)) AS outstanding_balance,
    bi.generated_at
FROM billing_invoices bi
JOIN reservations r ON bi.reservation_id = r.reservation_id
JOIN guests g ON r.guest_id = g.guest_id
LEFT JOIN payments p ON bi.invoice_id = p.invoice_id
GROUP BY bi.invoice_id, bi.reservation_id, g.first_name, g.last_name, g.email, bi.room_charges, bi.service_charges, bi.tax_amount, bi.discount_amount, bi.grand_total, bi.payment_status, bi.generated_at;
