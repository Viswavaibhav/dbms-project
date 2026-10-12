import os
import sqlite3
from datetime import datetime
try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None
    DictCursor = None
from config import Config

class DatabaseManager:
    def __init__(self):
        self.mode = "MYSQL" # "MYSQL" or "SQLITE"
        self._check_connection()

    def _check_connection(self):
        """Attempts connection to MySQL. If unavailable, falls back to SQLite."""
        if pymysql is None:
            print("[DBMS Manager] PyMySQL package not detected. Falling back to local embedded database.")
            self.mode = "SQLITE"
            self._init_sqlite_if_needed()
            return

        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                charset='utf8mb4',
                cursorclass=DictCursor,
                connect_timeout=3
            )
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB};")
            conn.select_db(Config.MYSQL_DB)
            conn.close()
            self.mode = "MYSQL"
            print(f"[DBMS Manager] Connected to MySQL Server at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}")
        except Exception as e:
            print(f"[DBMS Manager] MySQL connection note ({e}). Falling back to local embedded database.")
            self.mode = "SQLITE"
            self._init_sqlite_if_needed()

    def get_connection(self):
        """Returns active database connection."""
        if self.mode == "MYSQL":
            try:
                return pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    charset='utf8mb4',
                    cursorclass=DictCursor,
                    autocommit=True
                )
            except Exception as e:
                print(f"[DBMS Warning] MySQL disconnected ({e}), switching to SQLite fallback.")
                self.mode = "SQLITE"
                self._init_sqlite_if_needed()
                return self._get_sqlite_conn()
        else:
            return self._get_sqlite_conn()

    def _get_sqlite_conn(self):
        conn = sqlite3.connect("hotel_management.sqlite3", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Provide MySQL compatibility functions in SQLite
        conn.create_function("CONCAT", -1, lambda *args: "".join(str(a) if a is not None else "" for a in args))
        conn.create_function("DATEDIFF", 2, lambda d1, d2: 1)
        conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return conn

    def _init_sqlite_if_needed(self):
        db_path = "hotel_management.sqlite3"
        needs_init = not os.path.exists(db_path) or os.path.getsize(db_path) == 0
        if needs_init:
            conn = self._get_sqlite_conn()
            cur = conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS departments (
                    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS staff (
                    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dept_id INTEGER NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NOT NULL,
                    role TEXT NOT NULL,
                    salary REAL NOT NULL DEFAULT 35000.0,
                    hire_date DATE NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
                );

                CREATE TABLE IF NOT EXISTS room_types (
                    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    base_price_per_night REAL NOT NULL,
                    max_occupancy INTEGER NOT NULL DEFAULT 2,
                    bed_type TEXT NOT NULL,
                    amenities TEXT,
                    description TEXT
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_number TEXT NOT NULL UNIQUE,
                    floor INTEGER NOT NULL,
                    type_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'AVAILABLE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (type_id) REFERENCES room_types(type_id)
                );

                CREATE TABLE IF NOT EXISTS guests (
                    guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NOT NULL,
                    id_proof_type TEXT NOT NULL,
                    id_proof_number TEXT NOT NULL,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guest_id INTEGER NOT NULL,
                    check_in_date DATE NOT NULL,
                    check_out_date DATE NOT NULL,
                    number_of_guests INTEGER NOT NULL DEFAULT 1,
                    status TEXT DEFAULT 'CONFIRMED',
                    special_requests TEXT,
                    total_room_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guest_id) REFERENCES guests(guest_id)
                );

                CREATE TABLE IF NOT EXISTS reservation_rooms (
                    reservation_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    price_per_night REAL NOT NULL,
                    PRIMARY KEY (reservation_id, room_id),
                    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                );

                CREATE TABLE IF NOT EXISTS service_categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                );

                CREATE TABLE IF NOT EXISTS services (
                    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    service_name TEXT NOT NULL,
                    unit_price REAL NOT NULL,
                    description TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    FOREIGN KEY (category_id) REFERENCES service_categories(category_id)
                );

                CREATE TABLE IF NOT EXISTS guest_service_orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    service_id INTEGER NOT NULL,
                    staff_id INTEGER,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    order_status TEXT DEFAULT 'PENDING',
                    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completion_time TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
                    FOREIGN KEY (service_id) REFERENCES services(service_id),
                    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
                );

                CREATE TABLE IF NOT EXISTS billing_invoices (
                    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER NOT NULL UNIQUE,
                    room_charges REAL NOT NULL DEFAULT 0.0,
                    service_charges REAL NOT NULL DEFAULT 0.0,
                    tax_amount REAL NOT NULL DEFAULT 0.0,
                    discount_amount REAL NOT NULL DEFAULT 0.0,
                    grand_total REAL NOT NULL DEFAULT 0.0,
                    payment_status TEXT DEFAULT 'UNPAID',
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    transaction_ref TEXT UNIQUE,
                    notes TEXT,
                    FOREIGN KEY (invoice_id) REFERENCES billing_invoices(invoice_id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    table_affected TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Initial Seed
                INSERT OR IGNORE INTO departments (dept_id, name, description) VALUES
                (1, 'Front Office', 'Guest reception, check-in, check-out, concierge and bell desk services'),
                (2, 'Housekeeping', 'Room cleaning, linen management, turndown and sanitization services'),
                (3, 'Food & Beverage', 'Fine dining restaurant, bar, and 24/7 in-room dining services'),
                (4, 'Spa & Wellness', 'Massage therapy, sauna, personal training and wellness packages'),
                (5, 'Maintenance & Engineering', 'HVAC, plumbing, electrical and structural maintenance');

                INSERT OR IGNORE INTO staff (staff_id, dept_id, first_name, last_name, email, phone, role, salary, hire_date, status) VALUES
                (1, 1, 'Alexander', 'Wright', 'alex.wright@grandazure.com', '+1-555-0101', 'Front Desk Manager', 55000.00, '2023-01-15', 'ACTIVE'),
                (2, 1, 'Sophia', 'Chen', 'sophia.chen@grandazure.com', '+1-555-0102', 'Concierge Specialist', 42000.00, '2023-04-10', 'ACTIVE'),
                (3, 2, 'Marcus', 'Rodriguez', 'marcus.r@grandazure.com', '+1-555-0201', 'Housekeeping Supervisor', 48000.00, '2022-11-01', 'ACTIVE'),
                (4, 2, 'Elena', 'Petrova', 'elena.p@grandazure.com', '+1-555-0202', 'Senior Room Attendant', 36000.00, '2023-06-12', 'ACTIVE'),
                (5, 3, 'Chef Jean-Luc', 'Dubois', 'jeanluc.d@grandazure.com', '+1-555-0301', 'Executive Head Chef', 72000.00, '2022-03-20', 'ACTIVE'),
                (6, 3, 'David', 'Kim', 'david.kim@grandazure.com', '+1-555-0302', 'Room Service Lead Server', 38000.00, '2023-08-01', 'ACTIVE'),
                (7, 4, 'Amara', 'Okonkwo', 'amara.o@grandazure.com', '+1-555-0401', 'Lead Spa Therapist', 46000.00, '2023-02-14', 'ACTIVE'),
                (8, 5, 'Liam', 'O''Connor', 'liam.oc@grandazure.com', '+1-555-0501', 'Chief Maintenance Technician', 51000.00, '2022-09-05', 'ACTIVE');

                INSERT OR IGNORE INTO room_types (type_id, type_name, base_price_per_night, max_occupancy, bed_type, amenities, description) VALUES
                (1, 'Deluxe King Suite', 220.00, 2, '1 King Bed', 'City View, High-Speed Wi-Fi, Smart 55" TV, Rain Shower, Mini-Bar, Nespresso Machine', 'Spacious luxury room with floor-to-ceiling windows and panoramic skyline views.'),
                (2, 'Executive Double Queen', 260.00, 4, '2 Queen Beds', 'Balcony, Marble Bathroom, Double Vanity, Workstation, High-Speed Wi-Fi, Safe', 'Ideal for executive travel and families, complete with dedicated workstation.'),
                (3, 'Presidential Penthouse', 650.00, 6, '2 King Beds + Sofa Bed', 'Private Terrace, Jacuzzi, Dining Room, Butler Service, Ocean View', 'Ultimate luxury experience featuring private terrace, bespoke butler service, and jacuzzi.'),
                (4, 'Standard Cozy Room', 140.00, 2, '1 Queen Bed', 'Courtyard View, Wi-Fi, 43" Smart TV, Ensuite Bathroom, Coffee Station', 'Comfortable modern accommodation offering great value and serene courtyard serenity.');

                INSERT OR IGNORE INTO rooms (room_id, room_number, floor, type_id, status) VALUES
                (1, '101', 1, 4, 'AVAILABLE'),
                (2, '102', 1, 4, 'AVAILABLE'),
                (3, '103', 1, 4, 'MAINTENANCE'),
                (4, '201', 2, 1, 'OCCUPIED'),
                (5, '202', 2, 1, 'AVAILABLE'),
                (6, '203', 2, 1, 'BOOKED'),
                (7, '301', 3, 2, 'OCCUPIED'),
                (8, '302', 3, 2, 'CLEANING'),
                (9, '401', 4, 3, 'OCCUPIED'),
                (10, '402', 4, 3, 'AVAILABLE');

                INSERT OR IGNORE INTO guests (guest_id, first_name, last_name, email, phone, id_proof_type, id_proof_number, address) VALUES
                (1, 'Eleanor', 'Vance', 'eleanor.vance@example.com', '+1-202-555-0143', 'PASSPORT', 'USA94820149', '742 Evergreen Terrace, Seattle, WA'),
                (2, 'Julian', 'Sterling', 'julian.sterling@example.com', '+1-312-555-0199', 'NATIONAL_ID', 'ID88204910', '1200 Lake Shore Drive, Chicago, IL'),
                (3, 'Dr. Aisha', 'Khan', 'aisha.khan@example.com', '+44-7700-900077', 'PASSPORT', 'GBR71829011', '45 Kensington Gardens, London, UK'),
                (4, 'Carlos', 'Mendoza', 'carlos.m@example.com', '+1-415-555-0182', 'DRIVING_LICENSE', 'DL-CA-4910294', '88 Mission St, San Francisco, CA'),
                (5, 'Hannah', 'Schmidt', 'hannah.s@example.com', '+49-151-5550123', 'PASSPORT', 'DEU99301290', 'Blumenstrasse 14, Munich, Germany');

                INSERT OR IGNORE INTO service_categories (category_id, name, description) VALUES
                (1, 'Dining & Room Service', 'Gourmet in-room breakfast, lunches, dinners, beverages and snacks'),
                (2, 'Housekeeping & Laundry', 'Extra pillows, towel replacement, dry cleaning and express laundry'),
                (3, 'Spa & Wellness', 'Deep tissue massage, aromatherapy, facial therapy and private sauna sessions'),
                (4, 'Concierge & Transport', 'Airport luxury limousine transfers, VIP city tours, and valet parking');

                INSERT OR IGNORE INTO services (service_id, category_id, service_name, unit_price, description, is_available) VALUES
                (1, 1, 'Continental Champagne Breakfast', 38.00, 'Freshly baked pastries, smoked salmon, organic fruits, artisan coffee and champagne', 1),
                (2, 1, 'Wagyu Ribeye Steak (Dinner)', 65.00, 'Prime dry-aged Wagyu beef, truffle mashed potatoes, asparagus and red wine jus', 1),
                (3, 1, 'Club Sandwich & Truffle Fries', 22.00, 'Triple-decker smoked turkey, crispy bacon, avocado, paired with truffle fries', 1),
                (4, 1, 'Artisan Cocktail / Wine Bottle', 45.00, 'Selection of sommelier-curated vintage wines or bespoke craft cocktail shaker', 1),
                (5, 2, 'Express Dry Cleaning (Per Suit)', 30.00, 'Same-day steam press and luxury garment dry cleaning service', 1),
                (6, 2, 'Luxury Bed Turndown & Aromatherapy', 15.00, 'Evening lavender pillow mist, premium chocolates, and warm herbal tea setup', 1),
                (7, 3, 'Swedish Full Body Massage (60 min)', 110.00, 'Relaxing full body tension release massage with organic essential oils', 1),
                (8, 3, 'Deep Detox Facial Treatment', 85.00, 'Hydrating anti-aging facial utilizing vitamin serums and lymphatic massage', 1),
                (9, 4, 'Executive Airport Chauffeur Transfer', 95.00, 'Direct airport transfer in Mercedes S-Class with Wi-Fi and chilled water', 1);

                INSERT OR IGNORE INTO reservations (reservation_id, guest_id, check_in_date, check_out_date, number_of_guests, status, special_requests, total_room_cost) VALUES
                (1001, 1, '2026-10-10', '2026-10-14', 2, 'CHECKED_IN', 'High floor preferred, late check-out requested', 880.00),
                (1002, 2, '2026-10-11', '2026-10-15', 3, 'CHECKED_IN', 'Extra hypoallergenic pillows, quiet room', 1040.00),
                (1003, 3, '2026-10-12', '2026-10-16', 2, 'CHECKED_IN', 'VIP Welcome amenity, fruit platter', 2600.00),
                (1004, 4, '2026-10-18', '2026-10-21', 1, 'CONFIRMED', 'Airport pickup coordination needed', 660.00),
                (1005, 5, '2026-10-05', '2026-10-09', 2, 'CHECKED_OUT', 'Anniversary celebration package', 880.00);

                INSERT OR IGNORE INTO reservation_rooms (reservation_id, room_id, price_per_night) VALUES
                (1001, 4, 220.00),
                (1002, 7, 260.00),
                (1003, 9, 650.00),
                (1004, 6, 220.00),
                (1005, 5, 220.00);

                INSERT OR IGNORE INTO guest_service_orders (order_id, reservation_id, room_id, service_id, staff_id, quantity, unit_price, total_price, order_status, notes) VALUES
                (201, 1001, 4, 1, 6, 2, 38.00, 76.00, 'COMPLETED', 'Delivered at 08:30 AM with hot coffee'),
                (202, 1001, 4, 7, 7, 1, 110.00, 110.00, 'IN_PROGRESS', 'Spa appointment booked for 4:00 PM today'),
                (203, 1002, 7, 2, 6, 2, 65.00, 130.00, 'COMPLETED', 'Medium-rare steak, delivered to Room 301'),
                (204, 1002, 7, 5, 4, 2, 30.00, 60.00, 'PENDING', 'Two formal business suits to dry clean before tomorrow 9 AM'),
                (205, 1003, 9, 4, 6, 2, 45.00, 90.00, 'COMPLETED', 'Vintage Pinot Noir served in Presidential suite'),
                (206, 1003, 9, 9, 2, 1, 95.00, 95.00, 'PENDING', 'Mercedes pickup scheduled at departure');

                INSERT OR IGNORE INTO billing_invoices (invoice_id, reservation_id, room_charges, service_charges, tax_amount, discount_amount, grand_total, payment_status) VALUES
                (501, 1005, 880.00, 148.00, 123.36, 0.00, 1151.36, 'PAID');

                INSERT OR IGNORE INTO payments (payment_id, invoice_id, amount, payment_method, transaction_ref, notes) VALUES
                (901, 501, 1151.36, 'CREDIT_CARD', 'TXN_CHASE_994821', 'Settled in full upon checkout by Hannah Schmidt');

                INSERT OR IGNORE INTO audit_logs (log_id, action_type, table_affected, record_id, details) VALUES
                (1, 'INITIALIZE', 'system', 1, 'Database schema seeded with luxury hotel guest services catalog and rooms'),
                (2, 'CHECK_IN', 'reservations', 1001, 'Guest Eleanor Vance checked into Room 201');
            """)
            conn.commit()
            conn.close()

    def execute_query(self, query, params=None):
        """Executes a SELECT query and returns rows as dictionaries."""
        conn = self.get_connection()
        if self.mode == "MYSQL":
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                res = cur.fetchall()
            conn.close()
            return res
        else:
            # SQLite query transformation if needed (e.g., %s -> ?)
            sqlite_q = query.replace('%s', '?')
            cur = conn.cursor()
            cur.execute(sqlite_q, params or ())
            rows = cur.fetchall()
            res = [dict(row) for row in rows]
            conn.close()
            return res

    def execute_non_query(self, query, params=None):
        """Executes INSERT/UPDATE/DELETE query and returns affected rows / lastrowid."""
        conn = self.get_connection()
        if self.mode == "MYSQL":
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                last_id = cur.lastrowid
                rowcount = cur.rowcount
            conn.close()
            return {"lastrowid": last_id, "rowcount": rowcount}
        else:
            sqlite_q = query.replace('%s', '?')
            cur = conn.cursor()
            cur.execute(sqlite_q, params or ())
            conn.commit()
            last_id = cur.lastrowid
            rowcount = cur.rowcount
            conn.close()
            return {"lastrowid": last_id, "rowcount": rowcount}

db = DatabaseManager()
