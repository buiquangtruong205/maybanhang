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
 * Lấy trạng thái máy bán hàng.
 * @returns {Promise<object>} API response
 */
async function apiFetchMachineStatus() {
    const res = await fetch(API.MACHINE_STATUS());
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
 * @returns {Promise<object>}
 */
async function apiCreateOrder(productId, quantity) {
    const res = await fetch(API.CREATE_ORDER(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({ product_id: productId, quantity }),
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
// IoT
// ===========================

/**
 * Upload log lên server.
 * @param {string} level   - 'info' | 'warn' | 'error'
 * @param {string} message
 * @param {*}      data
 */
async function apiUploadLog(level, message, data = null) {
    try {
        await fetch(API.IOT_LOGS(), {
            method: 'POST',
            headers: machineHeaders(),
            body: JSON.stringify({ level, message, data }),
        });
    } catch (e) {
        console.error('Failed to upload log:', e);
    }
}

/**
 * Gửi heartbeat / kiểm tra phiên thiết bị.
 * @returns {Promise<object>}
 */
async function apiSendHeartbeat() {
    const res = await fetch(API.IOT_HEARTBEAT(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({ uptime: 1, free_memory: 100, wifi_rssi: -50 }),
    });
    return res.json();
}

/**
 * Đăng ký / kiểm tra định danh thiết bị.
 * @returns {Promise<object>}
 */
async function apiRegisterDevice() {
    const res = await fetch(API.IOT_REGISTER(), {
        method: 'POST',
        headers: machineHeaders(),
        body: JSON.stringify({
            mac_address: 'CHECK_STATUS',
            fingerprint: 'browser-client',
            firmware_version: '1.0.0-web',
        }),
    });
    return res.json();
}

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

