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
// Dynamic Configuration Loader
// ===========================
const getDynamicConfig = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const paramId = urlParams.get('machine_id');
    const paramKey = urlParams.get('machine_key');

    // 1. If URL has params, they take precedence and are saved to localStorage
    if (paramId && paramKey) {
        localStorage.setItem('VITE_MACHINE_ID', paramId);
        localStorage.setItem('VITE_MACHINE_KEY', paramKey);
        // Clean URL to prevent re-saving on refresh (optional but recommended)
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        return { id: parseInt(paramId), key: paramKey };
    }

    // 2. Otherwise, look into localStorage
    const savedId = localStorage.getItem('VITE_MACHINE_ID');
    const savedKey = localStorage.getItem('VITE_MACHINE_KEY');
    if (savedId && savedKey) {
        return { id: parseInt(savedId), key: savedKey };
    }

    // 3. Finally, fallback to env.js constants
    return {
        id: _env.VITE_MACHINE_ID || null,
        key: _env.VITE_MACHINE_KEY || null
    };
};

const DYNAMIC_CONFIG = getDynamicConfig();

// ===========================
// Environment Config
// ===========================
const ENV = {
    API_BASE_URL: _env.VITE_API_BASE_URL || 'http://localhost:5000/api',
    MACHINE_KEY: DYNAMIC_CONFIG.key,
    MACHINE_ID: DYNAMIC_CONFIG.id,
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

    // Session Management
    FRONTEND_HEARTBEAT: () => `${ENV.API_BASE_URL}/iot/frontend-heartbeat`,

    // Orders
    CREATE_ORDER: () => `${ENV.API_BASE_URL}/iot/create-order`,
    ORDER_STATUS: (orderId) => `${ENV.API_BASE_URL}/orders/${orderId}/status`,

    // Payments
    PAYMENT_CREATE: () => `${ENV.API_BASE_URL}/payment/create`,
    PAYMENT_STATUS: (code) => `${ENV.API_BASE_URL}/payment/status/${code}`,
    PAYMENT_CANCEL: (code) => `${ENV.API_BASE_URL}/payment/cancel/${code}`,

    // Cash Payment
    CASH_INSERT: () => `${ENV.API_BASE_URL}/iot/cash-insert`,
    CASH_STATUS: (orderId) => `${ENV.API_BASE_URL}/iot/cash-status/${orderId}`,
};

// ===========================
// App Constants
// ===========================
const CONFIG = {
    POLLING_INTERVAL: 8000,   // ms — Tần suất polling kiểm tra thanh toán (8 seconds)
    PAYMENT_TIMEOUT: 300,    // giây — Thời gian chờ quét QR (5 phút)
    LOG_MAX_ENTRIES: 50,     // Số dòng log tối đa trong panel IoT
};
