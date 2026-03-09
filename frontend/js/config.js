/**
 * config.js — Đọc biến môi trường từ env.js và xây dựng các hằng số ứng dụng.
 *
 * Không hardcode giá trị thật ở đây.
 * Mọi giá trị nhạy cảm được định nghĩa trong js/env.js (bị gitignore).
 */

// ===========================
// Đọc từ __ENV__ (khai báo trong js/env.js)
// ===========================
if (typeof __ENV__ === 'undefined') {
    console.error(
        '[config.js] ❌ Không tìm thấy __ENV__!\n' +
        'Hãy sao chép frontend/js/env.example.js → frontend/js/env.js ' +
        'rồi điền đúng giá trị.'
    );
}

const _env = (typeof __ENV__ !== 'undefined') ? __ENV__ : {};

// ===========================
// Environment Config
// ===========================
const ENV = {
    API_BASE_URL: _env.VITE_API_BASE_URL || 'http://localhost:5000/api',
    MACHINE_KEY: _env.VITE_MACHINE_KEY || 'may1',
    MACHINE_ID: _env.VITE_MACHINE_ID || 1,
};

// ===========================
// API Endpoints (derived from ENV)
// ===========================
const API = {
    BASE: ENV.API_BASE_URL,
    WS_BASE: ENV.API_BASE_URL.replace('/api', ''),   // ws://host:port

    // Products & Slots
    PRODUCTS: () => `${ENV.API_BASE_URL}/products`,
    SLOTS: (machineId = ENV.MACHINE_ID) => `${ENV.API_BASE_URL}/slots?machine_id=${machineId}`,
    MACHINE_STATUS: (machineId = ENV.MACHINE_ID) => `${ENV.API_BASE_URL}/machines/${machineId}`,

    // Orders
    CREATE_ORDER: () => `${ENV.API_BASE_URL}/iot/create-order`,
    ORDER_STATUS: (orderId) => `${ENV.API_BASE_URL}/orders/${orderId}/status`,

    // Payments
    PAYMENT_CREATE: () => `${ENV.API_BASE_URL}/payment/create`,
    PAYMENT_STATUS: (code) => `${ENV.API_BASE_URL}/payment/status/${code}`,
    PAYMENT_CANCEL: (code) => `${ENV.API_BASE_URL}/payment/cancel/${code}`,

    // IoT
    IOT_LOGS: () => `${ENV.API_BASE_URL}/iot/logs`,
    IOT_HEARTBEAT: () => `${ENV.API_BASE_URL}/iot/heartbeat`,
    IOT_REGISTER: () => `${ENV.API_BASE_URL}/iot/register-device`,

    // Cash Payment
    CASH_INSERT: () => `${ENV.API_BASE_URL}/iot/cash-insert`,
    CASH_STATUS: (orderId) => `${ENV.API_BASE_URL}/iot/cash-status/${orderId}`,
};

// ===========================
// App Constants
// ===========================
const CONFIG = {
    POLLING_INTERVAL: 2000,   // ms — Tần suất polling kiểm tra thanh toán
    PAYMENT_TIMEOUT: 300,    // giây — Thời gian chờ quét QR (5 phút)
    LOG_MAX_ENTRIES: 50,     // Số dòng log tối đa trong panel IoT
};
