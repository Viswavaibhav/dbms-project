// ============================================================================
// GRAND AZURE HOTEL DBMS - CLIENT APPLICATION JAVASCRIPT
// SPA Navigation, API Orchestration, Modals & Live SQL Runner
// ============================================================================

const API = {
  get: async (url) => {
    const res = await fetch(url);
    return await res.json();
  },
  post: async (url, data) => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  },
  put: async (url, data) => {
    const res = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  }
};

// Global App State
const state = {
  currentTab: 'dashboard',
  rooms: [],
  roomTypes: [],
  guests: [],
  reservations: [],
  services: [],
  staff: []
};

// Toast notification
function showToast(message, isSuccess = true) {
  const toast = document.createElement('div');
  toast.className = `toast ${isSuccess ? 'success' : 'error'}`;
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    padding: 14px 20px; border-radius: 8px; font-weight: 600; font-size: 0.88rem;
    background: ${isSuccess ? 'rgba(16, 185, 129, 0.95)' : 'rgba(239, 68, 68, 0.95)'};
    color: #fff; box-shadow: 0 10px 25px rgba(0,0,0,0.5); backdrop-filter: blur(8px);
    transition: all 0.3s ease; animation: fadeIn 0.2s ease-out;
  `;
  toast.innerText = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Navigation Tab Switcher
function switchTab(tabName) {
  state.currentTab = tabName;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-view').forEach(view => {
    view.style.display = view.id === `view-${tabName}` ? 'block' : 'none';
  });

  const titles = {
    dashboard: ['Executive Dashboard', 'Real-time overview of hotel occupancy, guest stays, and financial metrics'],
    rooms: ['Room Inventory & Operations', 'Manage luxury suites, floor distribution, and housekeeping statuses'],
    reservations: ['Guest Reservations', 'Manage upcoming stays, process instant check-in, and guest departures'],
    'guest-services': ['Guest Services & In-Room Dining', 'Track room service orders, spa appointments, and housekeeping requests'],
    billing: ['Billing & Invoices', 'Review generated invoices, compute taxes, and record settlements'],
    staff: ['Staff & Departments', 'Organizational directory and department allocations'],
    'sql-lab': ['SQL Query Studio & Lab Viva', 'Live SQL execution console for academic demonstration, joins, and DBMS verification']
  };

  if (titles[tabName]) {
    document.getElementById('page-title-text').innerText = titles[tabName][0];
    document.getElementById('page-subtitle-text').innerText = titles[tabName][1];
  }

  // Reload current view data
  loadTabData(tabName);
}

// Load data for specific tab
async function loadTabData(tab) {
  if (tab === 'dashboard') {
    loadAnalytics();
    loadDashboardRooms();
  } else if (tab === 'rooms') {
    loadRoomsTable();
  } else if (tab === 'reservations') {
    loadReservationsTable();
  } else if (tab === 'guest-services') {
    loadServicesCatalog();
    loadServiceOrders();
  } else if (tab === 'billing') {
    loadBillingTable();
  } else if (tab === 'staff') {
    loadStaffDirectory();
  }
}

// System Status Check
async function checkSystemStatus() {
  try {
    const data = await API.get('/api/status');
    const badge = document.getElementById('db-status-pill');
    if (badge) {
      badge.className = `db-status-pill ${data.mode.toLowerCase()}`;
      badge.innerHTML = `<span class="pulse-dot"></span> ${data.mode}: ${data.database}`;
    }
  } catch (e) {
    console.error("Status check error", e);
  }
}

// Analytics Loading
async function loadAnalytics() {
  try {
    const res = await API.get('/api/analytics');
    if (!res.success) return;
    const d = res.data;
    document.getElementById('stat-occupancy').innerText = `${d.occupancy_rate}%`;
    document.getElementById('stat-active-stays').innerText = d.active_stays;
    document.getElementById('stat-pending-services').innerText = d.pending_services;
    document.getElementById('stat-total-revenue').innerText = `$${d.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  } catch (err) {
    console.error(err);
  }
}

// Dashboard Rooms Matrix
async function loadDashboardRooms() {
  try {
    const res = await API.get('/api/rooms');
    if (!res.success) return;
    state.rooms = res.rooms;
    const container = document.getElementById('dashboard-rooms-grid');
    if (!container) return;

    container.innerHTML = res.rooms.map(r => `
      <div class="room-box" onclick="showRoomStatusModal(${r.room_id}, '${r.room_number}', '${r.status}')">
        <div class="room-top">
          <span class="room-number">Room ${r.room_number}</span>
          <span class="badge badge-${r.status.toLowerCase()}">${r.status}</span>
        </div>
        <div class="room-type-tag">${r.type_name} • Fl ${r.floor}</div>
        <div class="room-price">$${r.base_price_per_night}/night</div>
        ${r.current_guest ? `<div class="room-guest"><i class="fas fa-user-check"></i> ${r.current_guest}</div>` : ''}
      </div>
    `).join('');
  } catch (e) {
    console.error(e);
  }
}

// Rooms Tab
async function loadRoomsTable() {
  await loadDashboardRooms();
  const res = await API.get('/api/rooms');
  if (!res.success) return;
  const tbody = document.getElementById('rooms-table-body');
  if (!tbody) return;

  tbody.innerHTML = res.rooms.map(r => `
    <tr>
      <td><strong>${r.room_number}</strong></td>
      <td>Floor ${r.floor}</td>
      <td>${r.type_name}</td>
      <td>$${r.base_price_per_night}</td>
      <td>${r.max_occupancy} Guests (${r.bed_type})</td>
      <td><span class="badge badge-${r.status.toLowerCase()}">${r.status}</span></td>
      <td>${r.current_guest || '<span style="color:#64748b">—</span>'}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="showRoomStatusModal(${r.room_id}, '${r.room_number}', '${r.status}')">
          <i class="fas fa-edit"></i> Status
        </button>
      </td>
    </tr>
  `).join('');
}

// Reservations Tab
async function loadReservationsTable() {
  const res = await API.get('/api/reservations');
  if (!res.success) return;
  state.reservations = res.reservations;
  const tbody = document.getElementById('reservations-table-body');
  if (!tbody) return;

  tbody.innerHTML = res.reservations.map(r => `
    <tr>
      <td>#${r.reservation_id}</td>
      <td><strong>${r.guest_name}</strong><br><small style="color:#94a3b8">${r.phone}</small></td>
      <td>Room ${r.room_number} <br><small style="color:#94a3b8">${r.type_name}</small></td>
      <td>${r.check_in_date} to ${r.check_out_date}</td>
      <td>$${parseFloat(r.total_room_cost).toFixed(2)}</td>
      <td><span class="badge badge-${r.status.toLowerCase()}">${r.status}</span></td>
      <td>
        ${r.status === 'CONFIRMED' ? `
          <button class="btn btn-success btn-sm" onclick="checkInGuest(${r.reservation_id})">
            <i class="fas fa-sign-in-alt"></i> Check-In
          </button>
          <button class="btn btn-danger btn-sm" onclick="cancelReservation(${r.reservation_id})">
            Cancel
          </button>
        ` : ''}
        ${r.status === 'CHECKED_IN' ? `
          <button class="btn btn-primary btn-sm" onclick="openCheckOutModal(${r.reservation_id}, '${r.guest_name}', ${r.total_room_cost}, ${r.service_total})">
            <i class="fas fa-file-invoice-dollar"></i> Check-Out & Bill
          </button>
        ` : ''}
        ${r.status === 'CHECKED_OUT' ? `
          <span style="color:#10b981; font-weight:600;"><i class="fas fa-check-circle"></i> Completed</span>
        ` : ''}
      </td>
    </tr>
  `).join('');
}

// Guest Services Tab
async function loadServicesCatalog() {
  const res = await API.get('/api/services');
  if (!res.success) return;
  state.services = res.services;
  const catalog = document.getElementById('services-catalog-grid');
  if (!catalog) return;

  catalog.innerHTML = res.services.map(s => `
    <div class="service-card">
      <div>
        <div class="service-card-header">
          <h4>${s.service_name}</h4>
          <span class="badge" style="background:rgba(212,175,55,0.15); color:var(--gold-accent); border:1px solid rgba(212,175,55,0.3)">
            ${s.category_name}
          </span>
        </div>
        <p>${s.description}</p>
      </div>
      <div class="service-card-bottom">
        <span class="room-price">$${parseFloat(s.unit_price).toFixed(2)}</span>
        <button class="btn btn-primary btn-sm" onclick="openOrderServiceModal(${s.service_id}, '${s.service_name}', ${s.unit_price})">
          <i class="fas fa-concierge-bell"></i> Order for Room
        </button>
      </div>
    </div>
  `).join('');
}

async function loadServiceOrders() {
  const res = await API.get('/api/service-orders');
  if (!res.success) return;
  const tbody = document.getElementById('service-orders-table-body');
  if (!tbody) return;

  tbody.innerHTML = res.orders.map(o => `
    <tr>
      <td>#${o.order_id}</td>
      <td><strong>Room ${o.room_number}</strong> (${o.guest_name})</td>
      <td>${o.service_name} (x${o.quantity})</td>
      <td>$${parseFloat(o.total_price).toFixed(2)}</td>
      <td><span class="badge badge-${o.order_status.toLowerCase()}">${o.order_status}</span></td>
      <td>${o.assigned_staff || 'Front Desk'}</td>
      <td>
        ${o.order_status === 'PENDING' ? `
          <button class="btn btn-outline btn-sm" onclick="updateOrderStatus(${o.order_id}, 'IN_PROGRESS')">Fulfill</button>
        ` : ''}
        ${o.order_status === 'IN_PROGRESS' ? `
          <button class="btn btn-success btn-sm" onclick="updateOrderStatus(${o.order_id}, 'COMPLETED')">Complete</button>
        ` : ''}
      </td>
    </tr>
  `).join('');
}

// Billing Tab
async function loadBillingTable() {
  const res = await API.get('/api/billing');
  if (!res.success) return;
  const tbody = document.getElementById('billing-table-body');
  if (!tbody) return;

  tbody.innerHTML = res.invoices.map(inv => `
    <tr>
      <td>#INV-${inv.invoice_id}</td>
      <td><strong>${inv.guest_name}</strong><br><small style="color:#94a3b8">Room ${inv.room_number || 'N/A'}</small></td>
      <td>$${parseFloat(inv.room_charges).toFixed(2)}</td>
      <td>$${parseFloat(inv.service_charges).toFixed(2)}</td>
      <td>$${parseFloat(inv.tax_amount).toFixed(2)} (12%)</td>
      <td><strong>$${parseFloat(inv.grand_total).toFixed(2)}</strong></td>
      <td>
        <span class="badge badge-${inv.payment_status.toLowerCase()}">${inv.payment_status}</span>
      </td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="viewInvoiceModal(${inv.invoice_id})">
          <i class="fas fa-eye"></i> View Bill
        </button>
        ${inv.payment_status !== 'PAID' ? `
          <button class="btn btn-primary btn-sm" onclick="openPaymentModal(${inv.invoice_id}, ${inv.grand_total}, ${inv.amount_paid})">
            <i class="fas fa-credit-card"></i> Pay
          </button>
        ` : ''}
      </td>
    </tr>
  `).join('');
}

// Staff Tab
async function loadStaffDirectory() {
  const res = await API.get('/api/staff');
  if (!res.success) return;
  state.staff = res.staff;
  const tbody = document.getElementById('staff-table-body');
  if (!tbody) return;

  tbody.innerHTML = res.staff.map(s => `
    <tr>
      <td>#${s.staff_id}</td>
      <td><strong>${s.first_name} ${s.last_name}</strong></td>
      <td>${s.department_name}</td>
      <td>${s.role}</td>
      <td>${s.phone}</td>
      <td>$${parseFloat(s.salary).toLocaleString()} / yr</td>
      <td><span class="badge badge-available">${s.status}</span></td>
    </tr>
  `).join('');
}

// ============================================================================
// ACTIONS & MODALS
// ============================================================================

// Check in guest
async function checkInGuest(resId) {
  if (!confirm(`Confirm Check-In for Reservation #${resId}? Room will be marked OCCUPIED.`)) return;
  const res = await API.post(`/api/reservations/${resId}/check-in`, {});
  if (res.success) {
    showToast(res.message);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

// Cancel reservation
async function cancelReservation(resId) {
  if (!confirm(`Cancel Reservation #${resId}? Room will be made AVAILABLE.`)) return;
  const res = await API.post(`/api/reservations/${resId}/cancel`, {});
  if (res.success) {
    showToast(res.message);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

// Open Check-Out Modal
function openCheckOutModal(resId, guestName, roomCost, serviceCost) {
  document.getElementById('checkout-res-id').value = resId;
  document.getElementById('checkout-guest-name').innerText = guestName;
  document.getElementById('checkout-room-cost').innerText = `$${parseFloat(roomCost).toFixed(2)}`;
  document.getElementById('checkout-service-cost').innerText = `$${parseFloat(serviceCost).toFixed(2)}`;
  
  const discount = parseFloat(document.getElementById('checkout-discount-pct').value || 0);
  calculateCheckoutTotal(roomCost, serviceCost, discount);
  
  document.getElementById('modal-checkout').classList.add('active');
}

function calculateCheckoutTotal(roomCost, serviceCost, discountPct) {
  const subtotal = roomCost + serviceCost;
  const discount = (subtotal * discountPct) / 100;
  const taxable = subtotal - discount;
  const tax = taxable * 0.12;
  const grandTotal = taxable + tax;

  document.getElementById('checkout-discount-val').innerText = `-$${discount.toFixed(2)}`;
  document.getElementById('checkout-tax-val').innerText = `$${tax.toFixed(2)}`;
  document.getElementById('checkout-grand-total').innerText = `$${grandTotal.toFixed(2)}`;
}

async function submitCheckout() {
  const resId = document.getElementById('checkout-res-id').value;
  const discountPct = document.getElementById('checkout-discount-pct').value || 0;
  
  const res = await API.post(`/api/reservations/${resId}/check-out`, { discount_percent: discountPct });
  if (res.success) {
    closeModal('modal-checkout');
    showToast(res.message);
    loadTabData(state.currentTab);
    viewInvoiceModal(res.invoice_id);
  } else {
    showToast(res.error, false);
  }
}

// View Detailed Invoice
async function viewInvoiceModal(invoiceId) {
  const res = await API.get(`/api/billing/${invoiceId}`);
  if (!res.success) return showToast(res.error, false);
  const inv = res.invoice;

  document.getElementById('inv-number').innerText = `#INV-${inv.invoice_id}`;
  document.getElementById('inv-guest').innerText = inv.guest_name;
  document.getElementById('inv-email').innerText = inv.email;
  document.getElementById('inv-room').innerText = `Room ${inv.room_number} (${inv.type_name})`;
  document.getElementById('inv-dates').innerText = `${inv.check_in_date} to ${inv.check_out_date}`;
  document.getElementById('inv-room-charge').innerText = `$${inv.room_charges.toFixed(2)}`;
  document.getElementById('inv-tax').innerText = `$${inv.tax_amount.toFixed(2)}`;
  document.getElementById('inv-discount').innerText = `-$${inv.discount_amount.toFixed(2)}`;
  document.getElementById('inv-grand-total').innerText = `$${inv.grand_total.toFixed(2)}`;
  document.getElementById('inv-paid').innerText = `$${inv.total_paid.toFixed(2)}`;
  document.getElementById('inv-balance').innerText = `$${inv.balance_due.toFixed(2)}`;

  const servList = document.getElementById('inv-services-list');
  servList.innerHTML = inv.service_items.length > 0 ? inv.service_items.map(s => `
    <div style="display:flex; justify-content:space-between; font-size:0.85rem; padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.06);">
      <span>${s.service_name} (x${s.quantity})</span>
      <span>$${s.total_price.toFixed(2)}</span>
    </div>
  `).join('') : '<span style="color:#64748b">No additional services ordered.</span>';

  document.getElementById('modal-invoice-view').classList.add('active');
}

// Open Payment Modal
function openPaymentModal(invoiceId, grandTotal, paidSoFar) {
  document.getElementById('pay-invoice-id').value = invoiceId;
  const balance = Math.max(0, grandTotal - paidSoFar);
  document.getElementById('pay-amount').value = balance.toFixed(2);
  document.getElementById('pay-balance-hint').innerText = `Remaining balance: $${balance.toFixed(2)}`;
  document.getElementById('modal-payment').classList.add('active');
}

async function submitPayment() {
  const invoiceId = document.getElementById('pay-invoice-id').value;
  const amount = document.getElementById('pay-amount').value;
  const method = document.getElementById('pay-method').value;
  const notes = document.getElementById('pay-notes').value;

  const res = await API.post(`/api/billing/${invoiceId}/payment`, {
    amount: amount,
    payment_method: method,
    notes: notes
  });

  if (res.success) {
    closeModal('modal-payment');
    showToast(res.message);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

// Open Order Service Modal
async function openOrderServiceModal(serviceId, serviceName, price) {
  document.getElementById('order-service-id').value = serviceId;
  document.getElementById('order-service-name').innerText = serviceName;
  document.getElementById('order-service-price').innerText = `$${parseFloat(price).toFixed(2)}`;

  // Populate active reservations
  const res = await API.get('/api/reservations?status=CHECKED_IN');
  const select = document.getElementById('order-res-select');
  select.innerHTML = res.reservations.length > 0 ? res.reservations.map(r => `
    <option value="${r.reservation_id}">Room ${r.room_number} - ${r.guest_name}</option>
  `).join('') : '<option disabled>No guests currently checked in!</option>';

  document.getElementById('modal-order-service').classList.add('active');
}

async function submitServiceOrder() {
  const resId = document.getElementById('order-res-select').value;
  const serviceId = document.getElementById('order-service-id').value;
  const qty = document.getElementById('order-qty').value;
  const notes = document.getElementById('order-notes').value;

  if (!resId) return showToast("Please select a checked-in guest room.", false);

  const res = await API.post('/api/service-orders', {
    reservation_id: resId,
    service_id: serviceId,
    quantity: qty,
    notes: notes
  });

  if (res.success) {
    closeModal('modal-order-service');
    showToast(res.message);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

async function updateOrderStatus(orderId, status) {
  const res = await API.put(`/api/service-orders/${orderId}/status`, { status: status });
  if (res.success) {
    showToast(res.message);
    loadServiceOrders();
  } else {
    showToast(res.error, false);
  }
}

// Room Status Modal
function showRoomStatusModal(roomId, roomNumber, currentStatus) {
  document.getElementById('room-status-id').value = roomId;
  document.getElementById('room-status-title').innerText = `Room ${roomNumber} Status`;
  document.getElementById('room-status-select').value = currentStatus;
  document.getElementById('modal-room-status').classList.add('active');
}

async function submitRoomStatusUpdate() {
  const roomId = document.getElementById('room-status-id').value;
  const status = document.getElementById('room-status-select').value;
  const res = await API.put(`/api/rooms/${roomId}/status`, { status: status });
  if (res.success) {
    closeModal('modal-room-status');
    showToast(res.message);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

// New Reservation Modal
async function openNewReservationModal() {
  // Load guests
  const gRes = await API.get('/api/guests');
  const gSelect = document.getElementById('res-guest-select');
  gSelect.innerHTML = gRes.guests.map(g => `<option value="${g.guest_id}">${g.first_name} ${g.last_name} (${g.phone})</option>`).join('');

  // Load available rooms
  const rRes = await API.get('/api/rooms');
  const rSelect = document.getElementById('res-room-select');
  const avail = rRes.rooms.filter(r => r.status === 'AVAILABLE');
  rSelect.innerHTML = avail.length > 0 ? avail.map(r => `
    <option value="${r.room_id}">Room ${r.room_number} - ${r.type_name} ($${r.base_price_per_night}/nt)</option>
  `).join('') : '<option disabled>No rooms currently available!</option>';

  // Set default dates
  const today = new Date().toISOString().split('T')[0];
  const nextDay = new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0];
  document.getElementById('res-check-in').value = today;
  document.getElementById('res-check-out').value = nextDay;

  document.getElementById('modal-new-reservation').classList.add('active');
}

async function submitNewReservation() {
  const guestId = document.getElementById('res-guest-select').value;
  const roomId = document.getElementById('res-room-select').value;
  const checkIn = document.getElementById('res-check-in').value;
  const checkOut = document.getElementById('res-check-out').value;
  const numGuests = document.getElementById('res-num-guests').value;
  const requests = document.getElementById('res-requests').value;

  const res = await API.post('/api/reservations', {
    guest_id: guestId,
    room_id: roomId,
    check_in_date: checkIn,
    check_out_date: checkOut,
    number_of_guests: numGuests,
    special_requests: requests
  });

  if (res.success) {
    closeModal('modal-new-reservation');
    showToast(`Reservation #${res.reservation_id} confirmed ($${res.total_cost})`);
    loadTabData(state.currentTab);
  } else {
    showToast(res.error, false);
  }
}

// New Guest Registration Modal
function openNewGuestModal() {
  document.getElementById('modal-new-guest').classList.add('active');
}

async function submitNewGuest() {
  const fn = document.getElementById('guest-fn').value;
  const ln = document.getElementById('guest-ln').value;
  const email = document.getElementById('guest-email').value;
  const phone = document.getElementById('guest-phone').value;
  const idType = document.getElementById('guest-id-type').value;
  const idNum = document.getElementById('guest-id-num').value;
  const addr = document.getElementById('guest-addr').value;

  const res = await API.post('/api/guests', {
    first_name: fn,
    last_name: ln,
    email: email,
    phone: phone,
    id_proof_type: idType,
    id_proof_number: idNum,
    address: addr
  });

  if (res.success) {
    closeModal('modal-new-guest');
    showToast("Guest registered successfully!");
    openNewReservationModal();
  } else {
    showToast(res.error, false);
  }
}

// SQL Runner Studio
async function executeCustomQuery() {
  const query = document.getElementById('sql-query-input').value;
  const statusDiv = document.getElementById('sql-query-status');
  const tableDiv = document.getElementById('sql-results-table');

  statusDiv.innerHTML = '<span style="color:var(--gold-accent)"><i class="fas fa-spinner fa-spin"></i> Executing query...</span>';

  const res = await API.post('/api/sql-runner', { query: query });
  if (!res.success) {
    statusDiv.innerHTML = `<span style="color:#ef4444"><i class="fas fa-times-circle"></i> ${res.error}</span>`;
    tableDiv.innerHTML = '';
    return;
  }

  statusDiv.innerHTML = `<span style="color:#10b981"><i class="fas fa-check-circle"></i> Query returned ${res.count} rows successfully.</span>`;
  
  if (res.rows.length === 0) {
    tableDiv.innerHTML = '<div style="padding:15px; color:#94a3b8">Zero rows returned.</div>';
    return;
  }

  let html = '<table class="data-table"><thead><tr>';
  res.columns.forEach(col => { html += `<th>${col}</th>`; });
  html += '</tr></thead><tbody>';

  res.rows.forEach(row => {
    html += '<tr>';
    res.columns.forEach(col => {
      html += `<td>${row[col] !== null ? row[col] : '<span style="color:#64748b">NULL</span>'}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';

  tableDiv.innerHTML = html;
}

function setSqlTemplate(type) {
  const templates = {
    active_stays: "SELECT * FROM vw_active_guest_stays;",
    room_occupancy: "SELECT r.status, COUNT(*) as count, GROUP_CONCAT(r.room_number) as rooms FROM rooms r GROUP BY r.status;",
    top_services: "SELECT s.service_name, sc.name as category, COUNT(gso.order_id) as times_ordered, SUM(gso.total_price) as total_revenue FROM services s JOIN service_categories sc ON s.category_id = sc.category_id JOIN guest_service_orders gso ON s.service_id = gso.service_id WHERE gso.order_status = 'COMPLETED' GROUP BY s.service_id, s.service_name, sc.name ORDER BY total_revenue DESC;",
    unpaid_bills: "SELECT invoice_id, guest_name, grand_total, payment_status FROM vw_financial_summary WHERE payment_status <> 'PAID';",
    audit_history: "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 20;"
  };
  if (templates[type]) {
    document.getElementById('sql-query-input').value = templates[type];
  }
}

// Provision MySQL Button
async function initMySqlFromUi() {
  if (!confirm("This will execute schema.sql, procedures.sql, and sample_data.sql into your configured MySQL database. Continue?")) return;
  const res = await API.post('/api/init-mysql', {});
  if (res.success) {
    showToast(res.message);
    checkSystemStatus();
    loadTabData(state.currentTab);
  } else {
    showToast(`MySQL Init Note: ${res.message}`, false);
  }
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  checkSystemStatus();
  switchTab('dashboard');
});
