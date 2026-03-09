/**
 * websocket.js — Kết nối Socket.IO để nhận thông báo thanh toán real-time
 * Phụ thuộc: config.js (API)
 */

let paymentSocket = null;

/**
 * Kết nối WebSocket đến /payment namespace và lắng nghe sự kiện.
 * @param {number}   orderCode       - Mã đơn hàng cần theo dõi
 * @param {Function} onSuccess       - Callback khi thanh toán thành công
 * @param {Function} onFailed        - Callback khi thanh toán thất bại
 */
function connectPaymentSocket(orderCode, onSuccess, onFailed) {
    // Ngắt kết nối cũ nếu có
    disconnectPaymentSocket();

    try {
        console.log(`🔌 Connecting WebSocket: ${API.WS_BASE}/payment`);

        paymentSocket = io(`${API.WS_BASE}/payment`, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
        });

        paymentSocket.on('connect', () => {
            console.log('✅ WebSocket connected');
            paymentSocket.emit('subscribe', { order_id: orderCode });
        });

        paymentSocket.on('subscribed', (data) => {
            console.log(`📢 Subscribed order #${data.order_id}`);
        });

        paymentSocket.on('payment_success', (data) => {
            console.log('🎉 payment_success via WebSocket:', data);
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

        paymentSocket.on('disconnect', (reason) => {
            console.log('⚠️ WebSocket disconnected:', reason);
        });

        paymentSocket.on('connect_error', (err) => {
            console.log('⚠️ WebSocket error:', err);
        });

    } catch (e) {
        console.error('Error initializing WebSocket:', e);
    }
}

/**
 * Ngắt kết nối WebSocket.
 */
function disconnectPaymentSocket() {
    if (paymentSocket) {
        console.log('🔌 Disconnecting WebSocket...');
        paymentSocket.disconnect();
        paymentSocket = null;
    }
}
