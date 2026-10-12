# 🏨 Grand Azure Luxury Hotel Reservation & Guest Services DBMS

An enterprise-grade, comprehensive **Relational Database Management System (DBMS)** web application built with **MySQL** and **Python (Flask)**. Designed to meet academic DBMS project standards, it implements strict 3NF/BCNF normalization, foreign key constraints, MySQL triggers, stored procedures, multi-table views, transactions, and an interactive modern UI.

---

## 🌟 Key Features

1. **Guest & Room Booking Management**:
   - Live Room Inventory matrix across multiple floors (Available, Booked, Occupied, Cleaning, Maintenance).
   - Multi-room reservations with automatic check-in / check-out workflows.
   - Stay duration and pricing calculations.

2. **Guest Services & In-Room Dining Operations**:
   - Categorized catalog: Fine Dining, Room Service, Luxury Spa & Wellness, Laundry, Airport Chauffeur.
   - Dispatch services directly to checked-in rooms.
   - Staff order dispatch workflow: `PENDING` ➔ `IN_PROGRESS` ➔ `COMPLETED`.

3. **Automated Billing, Tax & Invoicing**:
   - Aggregates room stay duration and all completed guest services.
   - Automated 12% hospitality tax/GST and promotional discount calculation.
   - Multi-mode payment recording (Credit Card, Debit Card, UPI, Cash) with real-time balance tracking.
   - Printable luxury invoice format.

4. **Staff & Shift Allocation**:
   - Department directory (Front Desk, Housekeeping, F&B, Spa, Maintenance).
   - Staff roles, compensation tracking, and duty assignments.

5. **Advanced DBMS Features**:
   - **Triggers**: Auto-calculates service order subtotals; logs all reservation status changes to audit table.
   - **Stored Procedures**: `sp_create_reservation`, `sp_check_in`, `sp_order_guest_service`, `sp_generate_checkout_bill`, `sp_record_payment`.
   - **Views**: `vw_active_guest_stays`, `vw_room_inventory`, `vw_pending_services`, `vw_financial_summary`.
   - **Audit Logs**: Real-time tracking of DBMS operations.

6. **Interactive Live SQL Query Studio**:
   - Built-in SQL execution console within the app to run live `SELECT`, `SHOW`, `JOIN`, and `AGGREGATE` queries during DBMS viva/evaluations.

---

## 🗄️ Relational Database Schema

The database conforms strictly to **3NF** and **BCNF**:

```
DEPARTMENTS (dept_id PK, name, description)
STAFF (staff_id PK, dept_id FK, first_name, last_name, email, phone, role, salary, hire_date, status)
ROOM_TYPES (type_id PK, type_name, base_price_per_night, max_occupancy, bed_type, amenities, description)
ROOMS (room_id PK, room_number UNIQUE, floor, type_id FK, status)
GUESTS (guest_id PK, first_name, last_name, email UNIQUE, phone, id_proof_type, id_proof_number, address)
RESERVATIONS (reservation_id PK, guest_id FK, check_in_date, check_out_date, number_of_guests, status, total_room_cost)
RESERVATION_ROOMS (reservation_id PK,FK, room_id PK,FK, price_per_night)
SERVICE_CATEGORIES (category_id PK, name, description)
SERVICES (service_id PK, category_id FK, service_name, unit_price, description, is_available)
GUEST_SERVICE_ORDERS (order_id PK, reservation_id FK, room_id FK, service_id FK, staff_id FK, quantity, unit_price, total_price, order_status)
BILLING_INVOICES (invoice_id PK, reservation_id FK, room_charges, service_charges, tax_amount, discount_amount, grand_total, payment_status)
PAYMENTS (payment_id PK, invoice_id FK, payment_date, amount, payment_method, transaction_ref)
AUDIT_LOGS (log_id PK, action_type, table_affected, record_id, details, timestamp)
```

Detailed ER Diagram available in: [database/er_diagram.md](database/er_diagram.md).

---

## 🚀 Quick Setup & Run

### Step 1: Install Python Requirements
```bash
pip install -r requirements.txt
```

### Step 2: Configure MySQL
By default, the application connects to MySQL on `localhost:3306` with user `root` and blank password (standard XAMPP / WAMP / MySQL default). 

To customize credentials, copy `.env.example` to `.env`:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=hotel_management_db
```

### Step 3: Initialize Database
Run the automated schema & seed loader:
```bash
python setup_database.py
```
*(Alternatively, you can import [database/schema.sql](database/schema.sql), [database/procedures.sql](database/procedures.sql), and [database/sample_data.sql](database/sample_data.sql) directly via MySQL Workbench, phpMyAdmin, or the MySQL command line client).*

### Step 4: Launch Web Application
```bash
python app.py
```
Or simply double-click **`run.bat`** on Windows!

Open your browser to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

*(Note: If MySQL server is temporarily not running, the application includes an automated smart fallback engine so you can still immediately explore and interact with all UI features and test workflows without downtime).*

---

## 🧪 Sample SQL Queries for DBMS Lab Evaluation & Viva

Execute these directly in the **SQL Query Studio** tab:

1. **Active Guest Stays with Accrued Service Charges (Multi-table View)**:
   ```sql
   SELECT * FROM vw_active_guest_stays;
   ```

2. **Room Occupancy Summary with Aggregation**:
   ```sql
   SELECT r.status, COUNT(*) AS total_rooms, GROUP_CONCAT(r.room_number) AS rooms
   FROM rooms r
   GROUP BY r.status;
   ```

3. **Top Revenue-Generating Guest Services (Join + Group By + Having)**:
   ```sql
   SELECT s.service_name, sc.name AS category, COUNT(gso.order_id) AS orders_count, SUM(gso.total_price) AS total_revenue
   FROM services s
   JOIN service_categories sc ON s.category_id = sc.category_id
   JOIN guest_service_orders gso ON s.service_id = gso.service_id
   WHERE gso.order_status = 'COMPLETED'
   GROUP BY s.service_id, s.service_name, sc.name
   HAVING total_revenue > 50
   ORDER BY total_revenue DESC;
   ```

4. **Guests with Outstanding Balances (Outer Join)**:
   ```sql
   SELECT bi.invoice_id, CONCAT(g.first_name, ' ', g.last_name) AS guest, bi.grand_total, bi.payment_status
   FROM billing_invoices bi
   JOIN reservations r ON bi.reservation_id = r.reservation_id
   JOIN guests g ON r.guest_id = g.guest_id
   WHERE bi.payment_status <> 'PAID';
   ```
