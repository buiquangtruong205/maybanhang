/**
 * websocket.js — Kết nối Socket.IO cho cả thanh toán và đồng bộ máy
 * Phụ thuộc: config.js (API)
 */

let paymentSocket = null;
let machineSocket = null;

/**
 * ==========================================
 * 1. PAYMENT NAMESPACE (/payment)
 * ==========================================
 */

/**
 * Kết nối WebSocket đến /payment namespace để theo dõi 1 đơn hàng cụ thể.
 */
function connectPaymentSocket(orderCode, onSuccess, onFailed) {
    disconnectPaymentSocket();

    try {
        console.log(`🔌 Payment Socket: ${API.WS_BASE}/payment`);

        paymentSocket = io(`${API.WS_BASE}/payment`, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
        });

        paymentSocket.on('connect', () => {
            console.log('✅ Payment Socket connected');
            paymentSocket.emit('subscribe', { order_id: orderCode });
        });

        paymentSocket.on('payment_success', (data) => {
            console.log('🎉 payment_success:', data);
            if (parseInt(data.order_id) === parseInt(orderCode)) {
                onSuccess(orderCode);
            }
        });

        paymentSocket.on('payment_failed', (data) => {
            console.log('❌ payment_failed:', data);
            if (parseInt(data.order_id) === parseInt(orderCode)) {
                if (typeof onFailed === 'function') onFailed(data.reason);
            }
        });

    } catch (e) {
        console.error('Error initializing Payment WebSocket:', e);
    }
}

function disconnectPaymentSocket() {
    if (paymentSocket) {
        paymentSocket.disconnect();
        paymentSocket = null;
    }
}

/**
 * ==========================================
 * 2. MACHINE NAMESPACE (/machine) — NEW
 * ==========================================
 */

/**
 * Kết nối WebSocket đến /machine namespace để đồng bộ stock/status.
 */
function connectMachineSocket(machineId, onStockUpdate) {
    if (machineSocket) return; // Tránh kết nối lặp lại

    try {
        console.log(`🔌 Machine Socket: ${API.WS_BASE}/machine (ID: ${machineId})`);

        machineSocket = io(`${API.WS_BASE}/machine`, {
            transports: ['websocket', 'polling'],
            reconnection: true
        });

        machineSocket.on('connect', () => {
            console.log('✅ Machine Socket connected');
            machineSocket.emit('join', { machine_id: machineId });
        });

        machineSocket.on('stock_update', (data) => {
            console.log('📦 Real-time Stock Update:', data);
            if (typeof onStockUpdate === 'function') {
                onStockUpdate(data);
            }
        });

        machineSocket.on('machine_status_update', (data) => {
            console.log('🖥️ Machine Status Change:', data);
            // Có thể dùng để hiển thị thông báo bảo trì, v.v.
        });

        machineSocket.on('disconnect', () => {
            console.log('⚠️ Machine Socket disconnected');
        });

    } catch (e) {
        console.error('Error initializing Machine WebSocket:', e);
    }
}

function disconnectMachineSocket() {
    if (machineSocket) {
        machineSocket.disconnect();
        machineSocket = null;
    }
}
