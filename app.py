import os
from datetime import datetime, date
from decimal import Decimal
from flask import Flask, render_template, request, jsonify
from config import Config
from db_helper import db
from setup_database import init_mysql

app = Flask(__name__)
app.config.from_object(Config)

def serialize_row(row):
    """Converts Decimal, Date, and Timestamp objects to JSON serializable types."""
    if not row:
        return row
    res = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            res[k] = float(v)
        elif isinstance(v, (datetime, date)):
            res[k] = v.isoformat()
        else:
            res[k] = v
    return res

def serialize_rows(rows):
    return [serialize_row(r) for r in rows]

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================================
# SYSTEM & ANALYTICS APIs
# ============================================================================
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "success": True,
        "mode": db.mode,
        "database": Config.MYSQL_DB if db.mode == "MYSQL" else "hotel_management.sqlite3",
        "host": Config.MYSQL_HOST if db.mode == "MYSQL" else "Local Embedded Engine"
    })

@app.route('/api/init-mysql', methods=['POST'])
def run_mysql_init():
    success, msg = init_mysql()
    if success:
        db._check_connection()
    return jsonify({"success": success, "message": msg, "mode": db.mode})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        # Total and Occupied Rooms
        rooms = db.execute_query("SELECT status, COUNT(*) as count FROM rooms GROUP BY status")
        room_counts = {r['status']: r['count'] for r in rooms}
        total_rooms = sum(room_counts.values()) or 1
        occupied = room_counts.get('OCCUPIED', 0)
        occupancy_rate = round((occupied / total_rooms) * 100, 1)

        # Active checked-in guests
        active_guests = db.execute_query("SELECT COUNT(*) as count FROM reservations WHERE status = 'CHECKED_IN'")[0]['count']

        # Pending guest services
        pending_services = db.execute_query("SELECT COUNT(*) as count FROM guest_service_orders WHERE order_status IN ('PENDING', 'IN_PROGRESS')")[0]['count']

        # Total revenue
        rev_data = db.execute_query("SELECT COALESCE(SUM(amount), 0) as total FROM payments")
        total_rev = float(rev_data[0]['total']) if rev_data else 0.0

        # Room types breakdown
        room_types = db.execute_query("""
            SELECT rt.type_name, COUNT(r.room_id) as count 
            FROM room_types rt 
            LEFT JOIN rooms r ON rt.type_id = r.type_id 
            GROUP BY rt.type_id, rt.type_name
        """)

        return jsonify({
            "success": True,
            "data": {
                "total_rooms": total_rooms,
                "occupied_rooms": occupied,
                "available_rooms": room_counts.get('AVAILABLE', 0),
                "cleaning_rooms": room_counts.get('CLEANING', 0),
                "maintenance_rooms": room_counts.get('MAINTENANCE', 0),
                "occupancy_rate": occupancy_rate,
                "active_stays": active_guests,
                "pending_services": pending_services,
                "total_revenue": total_rev,
                "room_types_breakdown": serialize_rows(room_types)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# ROOMS & ROOM TYPES APIs
# ============================================================================
@app.route('/api/rooms', methods=['GET'])
def list_rooms():
    try:
        query = """
            SELECT r.room_id, r.room_number, r.floor, r.status,
                   rt.type_id, rt.type_name, rt.base_price_per_night, rt.max_occupancy, rt.bed_type, rt.amenities,
                   (
                       SELECT CONCAT(g.first_name, ' ', g.last_name)
                       FROM reservation_rooms rr
                       JOIN reservations res ON rr.reservation_id = res.reservation_id
                       JOIN guests g ON res.guest_id = g.guest_id
                       WHERE rr.room_id = r.room_id AND res.status = 'CHECKED_IN'
                       LIMIT 1
                   ) as current_guest,
                   (
                       SELECT res.reservation_id
                       FROM reservation_rooms rr
                       JOIN reservations res ON rr.reservation_id = res.reservation_id
                       WHERE rr.room_id = r.room_id AND res.status = 'CHECKED_IN'
                       LIMIT 1
                   ) as active_reservation_id
            FROM rooms r
            JOIN room_types rt ON r.type_id = rt.type_id
            ORDER BY r.room_number ASC
        """
        rows = db.execute_query(query)
        return jsonify({"success": True, "rooms": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/rooms', methods=['POST'])
def add_room():
    try:
        data = request.json
        room_number = data.get('room_number')
        floor = int(data.get('floor', 1))
        type_id = int(data.get('type_id'))
        
        db.execute_non_query(
            "INSERT INTO rooms (room_number, floor, type_id, status) VALUES (%s, %s, %s, 'AVAILABLE')",
            (room_number, floor, type_id)
        )
        return jsonify({"success": True, "message": f"Room {room_number} added successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/rooms/<int:room_id>/status', methods=['PUT'])
def update_room_status(room_id):
    try:
        new_status = request.json.get('status')
        if new_status not in ['AVAILABLE', 'BOOKED', 'OCCUPIED', 'CLEANING', 'MAINTENANCE']:
            return jsonify({"success": False, "error": "Invalid room status."}), 400

        db.execute_non_query(
            "UPDATE rooms SET status = %s WHERE room_id = %s",
            (new_status, room_id)
        )
        # Log to audit
        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('UPDATE_STATUS', 'rooms', %s, %s)",
            (room_id, f"Manually changed room #{room_id} status to {new_status}")
        )
        return jsonify({"success": True, "message": f"Room status updated to {new_status}."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/room-types', methods=['GET'])
def list_room_types():
    try:
        types = db.execute_query("SELECT * FROM room_types ORDER BY base_price_per_night ASC")
        return jsonify({"success": True, "room_types": serialize_rows(types)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# GUESTS APIs
# ============================================================================
@app.route('/api/guests', methods=['GET'])
def list_guests():
    try:
        search = request.args.get('search', '').strip()
        if search:
            query = """
                SELECT * FROM guests 
                WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone LIKE %s
                ORDER BY created_at DESC
            """
            term = f"%{search}%"
            rows = db.execute_query(query, (term, term, term, term))
        else:
            rows = db.execute_query("SELECT * FROM guests ORDER BY created_at DESC")
        return jsonify({"success": True, "guests": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/guests', methods=['POST'])
def add_guest():
    try:
        data = request.json
        fn = data.get('first_name')
        ln = data.get('last_name')
        email = data.get('email')
        phone = data.get('phone')
        id_type = data.get('id_proof_type', 'PASSPORT')
        id_number = data.get('id_proof_number')
        addr = data.get('address', '')

        res = db.execute_non_query(
            """INSERT INTO guests (first_name, last_name, email, phone, id_proof_type, id_proof_number, address) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (fn, ln, email, phone, id_type, id_number, addr)
        )
        guest_id = res['lastrowid']
        return jsonify({"success": True, "guest_id": guest_id, "message": "Guest registered successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ============================================================================
# RESERVATIONS APIs
# ============================================================================
@app.route('/api/reservations', methods=['GET'])
def list_reservations():
    try:
        status_filter = request.args.get('status')
        query = """
            SELECT r.reservation_id, r.guest_id, r.check_in_date, r.check_out_date,
                   r.number_of_guests, r.status, r.special_requests, r.total_room_cost, r.created_at,
                   CONCAT(g.first_name, ' ', g.last_name) as guest_name, g.email, g.phone,
                   rm.room_id, rm.room_number, rt.type_name,
                   (
                       SELECT COALESCE(SUM(gso.total_price), 0)
                       FROM guest_service_orders gso
                       WHERE gso.reservation_id = r.reservation_id AND gso.order_status <> 'CANCELLED'
                   ) as service_total
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN reservation_rooms rr ON r.reservation_id = rr.reservation_id
            JOIN rooms rm ON rr.room_id = rm.room_id
            JOIN room_types rt ON rm.type_id = rt.type_id
        """
        params = []
        if status_filter:
            query += " WHERE r.status = %s"
            params.append(status_filter)
        query += " ORDER BY r.reservation_id DESC"

        rows = db.execute_query(query, tuple(params))
        return jsonify({"success": True, "reservations": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    try:
        data = request.json
        guest_id = int(data.get('guest_id'))
        room_id = int(data.get('room_id'))
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        num_guests = int(data.get('number_of_guests', 1))
        special = data.get('special_requests', '')

        # Calculate stay duration
        d1 = datetime.strptime(check_in, '%Y-%m-%d')
        d2 = datetime.strptime(check_out, '%Y-%m-%d')
        nights = (d2 - d1).days

        if nights <= 0:
            return jsonify({"success": False, "error": "Check-out must be after check-in."}), 400

        # Retrieve room price and check availability
        room = db.execute_query("""
            SELECT r.status, rt.base_price_per_night 
            FROM rooms r 
            JOIN room_types rt ON r.type_id = rt.type_id 
            WHERE r.room_id = %s
        """, (room_id,))

        if not room:
            return jsonify({"success": False, "error": "Room does not exist."}), 404
        if room[0]['status'] != 'AVAILABLE':
            return jsonify({"success": False, "error": f"Room is currently {room[0]['status']}."}), 400

        price_per_night = float(room[0]['base_price_per_night'])
        total_cost = nights * price_per_night

        # Insert reservation
        res = db.execute_non_query("""
            INSERT INTO reservations (guest_id, check_in_date, check_out_date, number_of_guests, special_requests, total_room_cost, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'CONFIRMED')
        """, (guest_id, check_in, check_out, num_guests, special, total_cost))
        
        reservation_id = res['lastrowid']

        # Link room & update room status to BOOKED
        db.execute_non_query("""
            INSERT INTO reservation_rooms (reservation_id, room_id, price_per_night)
            VALUES (%s, %s, %s)
        """, (reservation_id, room_id, price_per_night))

        db.execute_non_query("UPDATE rooms SET status = 'BOOKED' WHERE room_id = %s", (room_id,))

        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('CREATE_RESERVATION', 'reservations', %s, %s)",
            (reservation_id, f"Created booking #{reservation_id} for guest #{guest_id} in room #{room_id} (${total_cost})")
        )

        return jsonify({"success": True, "reservation_id": reservation_id, "total_cost": total_cost})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/reservations/<int:res_id>/check-in', methods=['POST'])
def check_in_guest(res_id):
    try:
        # Check current status
        r = db.execute_query("SELECT status FROM reservations WHERE reservation_id = %s", (res_id,))
        if not r or r[0]['status'] != 'CONFIRMED':
            return jsonify({"success": False, "error": "Reservation must be in CONFIRMED state to check in."}), 400

        db.execute_non_query("UPDATE reservations SET status = 'CHECKED_IN' WHERE reservation_id = %s", (res_id,))
        db.execute_non_query("""
            UPDATE rooms r
            JOIN reservation_rooms rr ON r.room_id = rr.room_id
            SET r.status = 'OCCUPIED'
            WHERE rr.reservation_id = %s
        """, (res_id,))

        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('CHECK_IN', 'reservations', %s, %s)",
            (res_id, f"Guest checked into Reservation #{res_id}")
        )
        return jsonify({"success": True, "message": "Guest checked in successfully. Room status set to OCCUPIED."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reservations/<int:res_id>/check-out', methods=['POST'])
def check_out_guest(res_id):
    try:
        discount_pct = float(request.json.get('discount_percent', 0.0))

        # Retrieve room total
        res_info = db.execute_query("SELECT total_room_cost, status FROM reservations WHERE reservation_id = %s", (res_id,))
        if not res_info:
            return jsonify({"success": False, "error": "Reservation not found."}), 404
        if res_info[0]['status'] != 'CHECKED_IN':
            return jsonify({"success": False, "error": "Guest must be CHECKED_IN to process check-out."}), 400

        room_charges = float(res_info[0]['total_room_cost'])

        # Aggregate service charges
        serv = db.execute_query("""
            SELECT COALESCE(SUM(total_price), 0) as total 
            FROM guest_service_orders 
            WHERE reservation_id = %s AND order_status <> 'CANCELLED'
        """, (res_id,))
        service_charges = float(serv[0]['total']) if serv else 0.0

        subtotal = room_charges + service_charges
        discount_amount = round((subtotal * discount_pct) / 100.0, 2)
        taxable_amount = subtotal - discount_amount
        tax_amount = round(taxable_amount * 0.12, 2) # 12% Hospitality tax
        grand_total = round(taxable_amount + tax_amount, 2)

        # Upsert Invoice
        existing_inv = db.execute_query("SELECT invoice_id FROM billing_invoices WHERE reservation_id = %s", (res_id,))
        if existing_inv:
            inv_id = existing_inv[0]['invoice_id']
            db.execute_non_query("""
                UPDATE billing_invoices 
                SET room_charges = %s, service_charges = %s, tax_amount = %s, discount_amount = %s, grand_total = %s
                WHERE invoice_id = %s
            """, (room_charges, service_charges, tax_amount, discount_amount, grand_total, inv_id))
        else:
            inv_res = db.execute_non_query("""
                INSERT INTO billing_invoices (reservation_id, room_charges, service_charges, tax_amount, discount_amount, grand_total, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, 'UNPAID')
            """, (res_id, room_charges, service_charges, tax_amount, discount_amount, grand_total))
            inv_id = inv_res['lastrowid']

        # Update reservation status to CHECKED_OUT
        db.execute_non_query("UPDATE reservations SET status = 'CHECKED_OUT' WHERE reservation_id = %s", (res_id,))

        # Update rooms to CLEANING
        db.execute_non_query("""
            UPDATE rooms r
            JOIN reservation_rooms rr ON r.room_id = rr.room_id
            SET r.status = 'CLEANING'
            WHERE rr.reservation_id = %s
        """, (res_id,))

        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('CHECK_OUT', 'reservations', %s, %s)",
            (res_id, f"Guest checked out. Invoice #{inv_id} generated for ${grand_total}")
        )

        return jsonify({
            "success": True,
            "invoice_id": inv_id,
            "grand_total": grand_total,
            "message": "Check-out completed! Room scheduled for cleaning."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reservations/<int:res_id>/cancel', methods=['POST'])
def cancel_reservation(res_id):
    try:
        db.execute_non_query("UPDATE reservations SET status = 'CANCELLED' WHERE reservation_id = %s", (res_id,))
        db.execute_non_query("""
            UPDATE rooms r
            JOIN reservation_rooms rr ON r.room_id = rr.room_id
            SET r.status = 'AVAILABLE'
            WHERE rr.reservation_id = %s
        """, (res_id,))
        return jsonify({"success": True, "message": "Reservation cancelled and room made available."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# GUEST SERVICES & ORDERS APIs
# ============================================================================
@app.route('/api/services', methods=['GET'])
def list_services():
    try:
        rows = db.execute_query("""
            SELECT s.service_id, s.category_id, s.service_name, s.unit_price, s.description, s.is_available,
                   sc.name as category_name
            FROM services s
            JOIN service_categories sc ON s.category_id = sc.category_id
            ORDER BY sc.name, s.service_name
        """)
        return jsonify({"success": True, "services": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/service-orders', methods=['GET'])
def list_service_orders():
    try:
        status_filter = request.args.get('status')
        query = """
            SELECT gso.order_id, gso.reservation_id, gso.room_id, gso.service_id, gso.staff_id,
                   gso.quantity, gso.unit_price, gso.total_price, gso.order_status, gso.order_time, gso.notes,
                   rm.room_number, s.service_name, sc.name as category_name,
                   CONCAT(g.first_name, ' ', g.last_name) as guest_name,
                   CONCAT(st.first_name, ' ', st.last_name) as assigned_staff
            FROM guest_service_orders gso
            JOIN rooms rm ON gso.room_id = rm.room_id
            JOIN services s ON gso.service_id = s.service_id
            JOIN service_categories sc ON s.category_id = sc.category_id
            JOIN reservations r ON gso.reservation_id = r.reservation_id
            JOIN guests g ON r.guest_id = g.guest_id
            LEFT JOIN staff st ON gso.staff_id = st.staff_id
        """
        params = []
        if status_filter:
            query += " WHERE gso.order_status = %s"
            params.append(status_filter)
        query += " ORDER BY gso.order_id DESC"

        rows = db.execute_query(query, tuple(params))
        return jsonify({"success": True, "orders": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/service-orders', methods=['POST'])
def create_service_order():
    try:
        data = request.json
        res_id = int(data.get('reservation_id'))
        service_id = int(data.get('service_id'))
        staff_id = data.get('staff_id')
        staff_id = int(staff_id) if staff_id else None
        qty = int(data.get('quantity', 1))
        notes = data.get('notes', '')

        # Lookup room of reservation
        rm_row = db.execute_query("SELECT room_id FROM reservation_rooms WHERE reservation_id = %s LIMIT 1", (res_id,))
        if not rm_row:
            return jsonify({"success": False, "error": "Reservation room association not found."}), 404
        room_id = rm_row[0]['room_id']

        # Lookup service unit price
        srv = db.execute_query("SELECT unit_price, is_available FROM services WHERE service_id = %s", (service_id,))
        if not srv or not srv[0]['is_available']:
            return jsonify({"success": False, "error": "Selected service is unavailable."}), 400

        unit_price = float(srv[0]['unit_price'])
        total_price = unit_price * qty

        res = db.execute_non_query("""
            INSERT INTO guest_service_orders (reservation_id, room_id, service_id, staff_id, quantity, unit_price, total_price, order_status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
        """, (res_id, room_id, service_id, staff_id, qty, unit_price, total_price, notes))

        order_id = res['lastrowid']
        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('SERVICE_ORDER', 'guest_service_orders', %s, %s)",
            (order_id, f"Placed guest service order #{order_id} for Room #{room_id} (${total_price})")
        )

        return jsonify({"success": True, "order_id": order_id, "message": "Service order dispatched successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/service-orders/<int:order_id>/status', methods=['PUT'])
def update_service_order_status(order_id):
    try:
        status = request.json.get('status')
        if status not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            return jsonify({"success": False, "error": "Invalid order status."}), 400

        db.execute_non_query(
            "UPDATE guest_service_orders SET order_status = %s, completion_time = CASE WHEN %s = 'COMPLETED' THEN CURRENT_TIMESTAMP ELSE completion_time END WHERE order_id = %s",
            (status, status, order_id)
        )
        return jsonify({"success": True, "message": f"Service order #{order_id} marked as {status}."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# BILLING & PAYMENTS APIs
# ============================================================================
@app.route('/api/billing', methods=['GET'])
def list_invoices():
    try:
        rows = db.execute_query("""
            SELECT bi.*, 
                   CONCAT(g.first_name, ' ', g.last_name) as guest_name, g.email as guest_email,
                   rm.room_number,
                   COALESCE((SELECT SUM(amount) FROM payments WHERE invoice_id = bi.invoice_id), 0) as amount_paid
            FROM billing_invoices bi
            JOIN reservations r ON bi.reservation_id = r.reservation_id
            JOIN guests g ON r.guest_id = g.guest_id
            LEFT JOIN reservation_rooms rr ON r.reservation_id = rr.reservation_id
            LEFT JOIN rooms rm ON rr.room_id = rm.room_id
            ORDER BY bi.invoice_id DESC
        """)
        return jsonify({"success": True, "invoices": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/billing/<int:invoice_id>', methods=['GET'])
def get_invoice_details(invoice_id):
    try:
        inv = db.execute_query("""
            SELECT bi.*, 
                   CONCAT(g.first_name, ' ', g.last_name) as guest_name, g.email, g.phone, g.address,
                   r.check_in_date, r.check_out_date, rm.room_number, rt.type_name, rt.base_price_per_night
            FROM billing_invoices bi
            JOIN reservations r ON bi.reservation_id = r.reservation_id
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN reservation_rooms rr ON r.reservation_id = rr.reservation_id
            JOIN rooms rm ON rr.room_id = rm.room_id
            JOIN room_types rt ON rm.type_id = rt.type_id
            WHERE bi.invoice_id = %s
        """, (invoice_id,))

        if not inv:
            return jsonify({"success": False, "error": "Invoice not found."}), 404

        invoice_data = serialize_row(inv[0])

        # Get service line items
        service_items = db.execute_query("""
            SELECT gso.order_id, s.service_name, gso.quantity, gso.unit_price, gso.total_price, gso.order_time
            FROM guest_service_orders gso
            JOIN services s ON gso.service_id = s.service_id
            WHERE gso.reservation_id = %s AND gso.order_status <> 'CANCELLED'
        """, (invoice_data['reservation_id'],))

        # Get payments
        payments = db.execute_query("SELECT * FROM payments WHERE invoice_id = %s ORDER BY payment_date DESC", (invoice_id,))

        invoice_data['service_items'] = serialize_rows(service_items)
        invoice_data['payments'] = serialize_rows(payments)
        total_paid = sum([p['amount'] for p in invoice_data['payments']])
        invoice_data['total_paid'] = total_paid
        invoice_data['balance_due'] = max(0.0, round(invoice_data['grand_total'] - total_paid, 2))

        return jsonify({"success": True, "invoice": invoice_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/billing/<int:invoice_id>/payment', methods=['POST'])
def record_payment(invoice_id):
    try:
        data = request.json
        amount = float(data.get('amount'))
        method = data.get('payment_method', 'CREDIT_CARD')
        ref = data.get('transaction_ref') or f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        notes = data.get('notes', '')

        # Insert payment
        p_res = db.execute_non_query("""
            INSERT INTO payments (invoice_id, amount, payment_method, transaction_ref, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (invoice_id, amount, method, ref, notes))

        # Check total payments against grand total
        inv = db.execute_query("SELECT grand_total FROM billing_invoices WHERE invoice_id = %s", (invoice_id,))
        grand_total = float(inv[0]['grand_total'])

        paid_row = db.execute_query("SELECT SUM(amount) as paid FROM payments WHERE invoice_id = %s", (invoice_id,))
        total_paid = float(paid_row[0]['paid']) if paid_row else 0.0

        if total_paid >= grand_total:
            new_status = 'PAID'
        else:
            new_status = 'PARTIALLY_PAID'

        db.execute_non_query("UPDATE billing_invoices SET payment_status = %s WHERE invoice_id = %s", (new_status, invoice_id))

        db.execute_non_query(
            "INSERT INTO audit_logs (action_type, table_affected, record_id, details) VALUES ('PAYMENT', 'payments', %s, %s)",
            (p_res['lastrowid'], f"Payment of ${amount} recorded for Invoice #{invoice_id} ({new_status})")
        )

        return jsonify({"success": True, "payment_status": new_status, "message": "Payment recorded successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# STAFF & DEPARTMENTS APIs
# ============================================================================
@app.route('/api/staff', methods=['GET'])
def list_staff():
    try:
        rows = db.execute_query("""
            SELECT s.*, d.name as department_name
            FROM staff s
            JOIN departments d ON s.dept_id = d.dept_id
            ORDER BY d.name, s.first_name
        """)
        return jsonify({"success": True, "staff": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/departments', methods=['GET'])
def list_departments():
    try:
        rows = db.execute_query("SELECT * FROM departments ORDER BY name")
        return jsonify({"success": True, "departments": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/audit-logs', methods=['GET'])
def list_audit_logs():
    try:
        rows = db.execute_query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
        return jsonify({"success": True, "logs": serialize_rows(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# LIVE SQL RUNNER / LAB VIVA CONSOLE
# ============================================================================
@app.route('/api/sql-runner', methods=['POST'])
def run_custom_sql():
    try:
        raw_query = request.json.get('query', '').strip()
        if not raw_query:
            return jsonify({"success": False, "error": "Query cannot be empty."}), 400

        # Safety restriction for interactive query runner
        q_upper = raw_query.upper().lstrip()
        if not (q_upper.startswith('SELECT') or q_upper.startswith('SHOW') or q_upper.startswith('DESCRIBE') or q_upper.startswith('EXPLAIN')):
            return jsonify({
                "success": False, 
                "error": "For security in the demo console, only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are permitted."
            }), 403

        rows = db.execute_query(raw_query)
        serialized = serialize_rows(rows)
        columns = list(serialized[0].keys()) if serialized else []
        return jsonify({
            "success": True,
            "columns": columns,
            "rows": serialized,
            "count": len(serialized)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f"🏨 Luxury Hotel DBMS Management Application Running!")
    print(f"🌐 Access Web Dashboard: http://127.0.0.1:{port}")
    print(f"💽 DBMS Mode: {db.mode}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
