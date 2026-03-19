/**
 * api.js — Tất cả các hàm gọi API đến backend
 * Phụ thuộc: config.js (ENV, API)
 */

// ===========================
// Helpers
// ===========================

/** Header mặc định cho mọi request từ máy bán hàng */
function machineHeaders() {
    return {
        'X-Machine-Key': ENV.MACHINE_KEY,
        'Content-Type': 'application/json',
    };
}

// ===========================
// Products & Machine
// ===========================

/**
 * Gửi heartbeat từ frontend để duy trì session.
 * @param {string} sessionId
 * @returns {Promise<object>}
 */
async function apiSendHeartbeat(sessionId) {
    const res = await fetch(API.FRONTEND_HEARTBEAT(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({ session_id: sessionId }),
    });
    return res.json();
}

/**
 * Lấy trạng thái máy bán hàng.
 * @returns {Promise<object>} API response
 */
async function apiFetchMachineStatus() {
    const res = await fetch(API.MACHINE_STATUS(), {
        headers: machineHeaders(),
    });
    return res.json();
}

/**
 * Lấy danh sách slots của máy.
 * @returns {Promise<object>}
 */
async function apiFetchSlots() {
    const res = await fetch(API.SLOTS(), {
        headers: machineHeaders(),
    });
    return res.json();
}

/**
 * Lấy danh sách sản phẩm.
 * @returns {Promise<object>}
 */
async function apiFetchProducts() {
    const res = await fetch(API.PRODUCTS(), {
        headers: machineHeaders(),
    });
    return res.json();
}

// ===========================
// Orders
// ===========================

/**
 * Tạo đơn hàng mới qua IoT endpoint.
 * @param {number} productId
 * @param {number} quantity
 * @param {string} slotCode
 * @returns {Promise<object>}
 */
async function apiCreateOrder(productId, quantity, slotCode) {
    const res = await fetch(API.CREATE_ORDER(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({ product_id: productId, quantity, slot_code: slotCode }),
    });
    return res.json();
}

/**
 * Kiểm tra trạng thái đơn hàng từ DB.
 * @param {number} orderId
 * @returns {Promise<object>}
 */
async function apiGetOrderStatus(orderId) {
    const res = await fetch(API.ORDER_STATUS(orderId), {
        headers: machineHeaders(),
    });
    return res.json();
}

// ===========================
// Payments
// ===========================

/**
 * Tạo link thanh toán PayOS.
 * @param {number} orderCode
 * @param {number} amount
 * @param {Array}  items
 * @returns {Promise<object>}
 */
async function apiCreatePayment(orderCode, amount, items) {
    const res = await fetch(API.PAYMENT_CREATE(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({
            order_code: orderCode,
            amount,
            description: `Thanh toán đơn hàng #${orderCode}`,
            items: items.map(({ name, quantity, price }) => ({ name, quantity, price })),
        }),
    });
    return res.json();
}

/**
 * Kiểm tra trạng thái thanh toán từ PayOS.
 * @param {number|string} paymentCode
 * @returns {Promise<object>}
 */
async function apiGetPaymentStatus(paymentCode) {
    const res = await fetch(API.PAYMENT_STATUS(paymentCode), {
        headers: machineHeaders(),
    });
    return res.json();
}

/**
 * Hủy thanh toán.
 * @param {number|string} orderCode
 * @returns {Promise<object>}
 */
async function apiCancelPayment(orderCode) {
    const res = await fetch(API.PAYMENT_CANCEL(orderCode), {
        method: 'POST',
        headers: machineHeaders(),
    });
    return res.json();
}

// ===========================

// ===========================
// Cash Payment
// ===========================

/**
 * Báo nhận được tờ tiền (mô phỏng hoặc từ Arduino).
 * @param {number} orderId      - ID đơn hàng
 * @param {number} denomination - Mệnh giá tờ tiền (VNĐ)
 * @returns {Promise<object>}
 */
async function apiInsertCash(orderId, denomination) {
    const res = await fetch(API.CASH_INSERT(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({ order_id: orderId, denomination }),
    });
    return res.json();
}

/**
 * Kiểm tra tổng số tiền đã nhét cho một đơn hàng.
 * @param {number} orderId
 * @returns {Promise<object>}
 */
async function apiGetCashStatus(orderId) {
    const res = await fetch(API.CASH_STATUS(orderId), {
        headers: machineHeaders(),
    });
    return res.json();
}

