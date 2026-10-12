# Hotel Reservation & Guest Services DBMS - Architecture & ER Diagram

## 1. System Overview
The **Hotel Reservation & Guest Services DBMS** is an enterprise-grade relational database application engineered for luxury hospitality operations. It manages the complete guest lifecycle: from initial room selection and booking, guest check-in/out, live room state tracking, specialized concierge & in-room guest services (dining, housekeeping, wellness, transport), through to automated tax calculation, invoice generation, payment processing, and system audit logging.

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ STAFF : employs
    ROOM_TYPES ||--o{ ROOMS : classifies
    GUESTS ||--o{ RESERVATIONS : books
    RESERVATIONS ||--|{ RESERVATION_ROOMS : includes
    ROOMS ||--o{ RESERVATION_ROOMS : assigned_in
    SERVICE_CATEGORIES ||--o{ SERVICES : categorizes
    RESERVATIONS ||--o{ GUEST_SERVICE_ORDERS : requests
    ROOMS ||--o{ GUEST_SERVICE_ORDERS : delivered_to
    SERVICES ||--o{ GUEST_SERVICE_ORDERS : item_ordered
    STAFF ||--o{ GUEST_SERVICE_ORDERS : fulfills
    RESERVATIONS ||--|| BILLING_INVOICES : generates
    BILLING_INVOICES ||--o{ PAYMENTS : settles
    
    DEPARTMENTS {
        int dept_id PK
        string name
        string description
    }
    STAFF {
        int staff_id PK
        int dept_id FK
        string first_name
        string last_name
        string email
        string phone
        string role
        decimal salary
        date hire_date
        string status
    }
    ROOM_TYPES {
        int type_id PK
        string type_name
        decimal base_price_per_night
        int max_occupancy
        string bed_type
        string amenities
    }
    ROOMS {
        int room_id PK
        string room_number UK
        int floor
        int type_id FK
        string status "AVAILABLE, BOOKED, OCCUPIED, CLEANING, MAINTENANCE"
    }
    GUESTS {
        int guest_id PK
        string first_name
        string last_name
        string email UK
        string phone
        string id_proof_type
        string id_proof_number
        string address
    }
    RESERVATIONS {
        int reservation_id PK
        int guest_id FK
        date check_in_date
        date check_out_date
        int number_of_guests
        string status "CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED"
        decimal total_room_cost
    }
    RESERVATION_ROOMS {
        int reservation_id PK,FK
        int room_id PK,FK
        decimal price_per_night
    }
    SERVICE_CATEGORIES {
        int category_id PK
        string name
        string description
    }
    SERVICES {
        int service_id PK
        int category_id FK
        string service_name
        decimal unit_price
        string description
        boolean is_available
    }
    GUEST_SERVICE_ORDERS {
        int order_id PK
        int reservation_id FK
        int room_id FK
        int service_id FK
        int staff_id FK
        int quantity
        decimal unit_price
        decimal total_price
        string order_status "PENDING, IN_PROGRESS, COMPLETED, CANCELLED"
        timestamp order_time
    }
    BILLING_INVOICES {
        int invoice_id PK
        int reservation_id FK,UK
        decimal room_charges
        decimal service_charges
        decimal tax_amount
        decimal discount_amount
        decimal grand_total
        string payment_status "UNPAID, PARTIALLY_PAID, PAID"
    }
    PAYMENTS {
        int payment_id PK
        int invoice_id FK
        decimal amount
        string payment_method "CASH, CREDIT_CARD, DEBIT_CARD, UPI, ONLINE"
        string transaction_ref UK
        timestamp payment_date
    }
    AUDIT_LOGS {
        int log_id PK
        string action_type
        string table_affected
        int record_id
        string details
        timestamp timestamp
    }
```

---

## 3. Relational Schema & Normalization (3NF / BCNF)
Every relation in this DBMS conforms to **Third Normal Form (3NF)** and **Boyce-Codd Normal Form (BCNF)**:
1. **1NF**: All table columns are atomic; repeating groups are eliminated.
2. **2NF**: No partial dependencies; in composite tables like `reservation_rooms(reservation_id, room_id)`, attributes depend on the full composite key.
3. **3NF & BCNF**: No transitive dependencies. Room rates are tied to `room_types`, services to `service_categories`, and staff to `departments`. Historical unit prices are locked into transactions to prevent cascading price updates if base prices change later.

---

## 4. Database Procedures, Triggers & Views
- **Triggers**:
  - `trg_calc_service_order_insert` / `trg_calc_service_order_update`: Guarantees `total_price = quantity * unit_price`.
  - `trg_audit_reservation_status`: Real-time system auditing of reservation lifecycle changes.
- **Stored Procedures**:
  - `sp_create_reservation`: Validates room availability and dates, atomicity guarantees.
  - `sp_check_in`: Updates reservation to `CHECKED_IN` and automatically updates room to `OCCUPIED`.
  - `sp_order_guest_service`: Validates active service pricing and registers order.
  - `sp_generate_checkout_bill`: Calculates stay length, aggregates dining/amenities orders, computes 12% hospitality tax and net discount, moves room to `CLEANING`.
  - `sp_record_payment`: Records payment and transitions invoice to `PARTIALLY_PAID` or `PAID`.
- **Views**:
  - `vw_active_guest_stays`: Fast multi-table join for active guests and real-time accrued charges.
  - `vw_room_inventory`: Room matrix with occupant details and cleaning status.
  - `vw_pending_services`: Live order dispatch queue for staff.
  - `vw_financial_summary`: Invoices, revenue, and outstanding receivables.
