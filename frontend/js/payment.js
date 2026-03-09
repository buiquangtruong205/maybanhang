/**
 * payment.js — Quản lý luồng thanh toán: tạo order, QR modal, polling, đếm ngược
 * Phụ thuộc: config.js (CONFIG), api.js, ui.js, websocket.js, cart.js
 */

// ===========================
// State
// ===========================
let currentOrderCode = null;
let currentPaymentCode = null;
let pollingTimer = null;
let countdownTimer = null;
let countdownSeconds = CONFIG.PAYMENT_TIMEOUT;

// ===========================
// Polling
// ===========================

function startPaymentPolling(orderCode, paymentCode) {
    console.log(`🔄 Polling: order=${orderCode}, payment=${paymentCode}`);

    pollingTimer = setInterval(async () => {
        try {
            // 1. Kiểm tra trạng thái DB trước
            const orderStatus = await apiGetOrderStatus(orderCode);
            console.log('📋 Order status:', orderStatus.data);

            if (orderStatus.success && orderStatus.data?.status_payment === 'completed') {
                console.log('✅ Order completed (DB)');
                handlePaymentSuccess(orderCode);
                return;
            }

            // 2. Fallback: kiểm tra PayOS
            const paymentStatus = await apiGetPaymentStatus(paymentCode);
            const payosStatus = paymentStatus.success && paymentStatus.data
                ? paymentStatus.data.status
                : null;

            const isPaid = payosStatus && ['PAID', 'SUCCESS', 'COMPLETED'].includes(payosStatus.toUpperCase());

            if (isPaid) {
                console.log('✅ PayOS confirmed PAID');
                handlePaymentSuccess(orderCode);
            }
        } catch (err) {
            console.log('Polling error:', err);
        }
    }, CONFIG.POLLING_INTERVAL);
}

function stopPaymentPolling() {
    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

// ===========================
// Countdown
// ===========================

function startCountdown() {
    const countdown = document.getElementById('countdown');
    countdownSeconds = CONFIG.PAYMENT_TIMEOUT;

    countdownTimer = setInterval(() => {
        countdownSeconds--;
        if (countdown) countdown.textContent = formatTime(countdownSeconds);

        if (countdownSeconds <= 0) handlePaymentTimeout();
    }, 1000);
}

function stopCountdown() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
}

// ===========================
// QR Modal
// ===========================

function showQRModal(qrData, orderCode, amount) {
    const qrModal = document.getElementById('qr-modal');
    const qrCode = document.getElementById('qr-code');
    const orderCodeDisplay = document.getElementById('order-code-display');
    const paymentAmountDisplay = document.getElementById('payment-amount-display');
    const paymentStatusEl = document.getElementById('payment-status');
    const countdown = document.getElementById('countdown');

    let qrImageUrl;
    if (!qrData) {
        qrImageUrl = getPlaceholderImage(300, 300, 'No QR Code');
    } else if (qrData.startsWith('http') || qrData.startsWith('data:')) {
        qrImageUrl = qrData;
    } else {
        qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrData)}`;
    }

    qrCode.onerror = function () {
        if (qrImageUrl && !qrImageUrl.startsWith('data:')) {
            this.src = getPlaceholderImage(300, 300, 'QR Code Error');
        }
    };

    qrCode.src = qrImageUrl;
    orderCodeDisplay.textContent = orderCode;
    paymentAmountDisplay.textContent = formatCurrency(amount);
    countdown.textContent = formatTime(CONFIG.PAYMENT_TIMEOUT);

    paymentStatusEl.innerHTML = `
        <div class="status-waiting">
            <div class="pulse-ring"></div>
            <span>Đang chờ thanh toán...</span>
        </div>`;

    qrModal.classList.add('active');
    startCountdown();
}

function hideQRModal() {
    const qrModal = document.getElementById('qr-modal');
    qrModal.classList.remove('active');
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket();
}

// ===========================
// Checkout (Entry point)
// ===========================

async function startCheckout() {
    const currentCart = getCart(); // Lấy từ cart.js
    if (currentCart.length === 0) return;

    const total = currentCart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    try {
        // 1. Tạo order
        const firstItem = currentCart[0];
        const orderResult = await apiCreateOrder(firstItem.product_id, firstItem.quantity);

        if (!orderResult.success) {
            showToast(orderResult.message || 'Không thể tạo đơn hàng');
            return;
        }
        currentOrderCode = orderResult.data.order_id;

        // 2. Tạo thanh toán PayOS
        const paymentResult = await apiCreatePayment(currentOrderCode, total, currentCart);

        if (paymentResult.success) {
            currentPaymentCode = paymentResult.data.payment_code || currentOrderCode;
            console.log(`💳 order=${currentOrderCode}, payment=${currentPaymentCode}`);

            const qrData = paymentResult.data.qr_code || paymentResult.data.checkout_url;
            showQRModal(qrData, currentOrderCode, total);

            // Polling (backup) + WebSocket (primary)
            startPaymentPolling(currentOrderCode, currentPaymentCode);
            connectPaymentSocket(
                currentOrderCode,
                handlePaymentSuccess,
                (reason) => showToast(`Thanh toán thất bại: ${reason}`)
            );
        } else {
            showToast(paymentResult.message || 'Không thể tạo mã thanh toán. Kiểm tra cấu hình PayOS.');
        }
    } catch (err) {
        console.error('Checkout error:', err);
        showToast('Lỗi kết nối server. Vui lòng thử lại.');
    }
}

// ===========================
// Success / Timeout / Cancel
// ===========================

function handlePaymentSuccess(orderCode) {
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket();
    hideQRModal();

    const successModal = document.getElementById('success-modal');
    const successOrderCode = document.getElementById('success-order-code');
    successOrderCode.textContent = orderCode;
    successModal.classList.add('active');

    clearCart();
    loadProducts(); // Refresh tồn kho (defined in app.js)
}

function handlePaymentTimeout() {
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket();
    hideQRModal();
    showToast('Hết thời gian thanh toán. Vui lòng thử lại.');
}

async function handleCancelPayment() {
    if (currentOrderCode) {
        try {
            await apiCancelPayment(currentOrderCode);
        } catch (err) {
            console.log('Cancel error:', err);
        }
    }
    hideQRModal();
    showToast('Đã hủy thanh toán');
}

function hideSuccessModal() {
    const successModal = document.getElementById('success-modal');
    successModal.classList.remove('active');
    // Reset tiền thừa
    const changeEl = document.getElementById('success-change');
    if (changeEl) changeEl.style.display = 'none';
}

// ===========================
// Cash Payment (Tiền mặt)
// ===========================

let cashPollingTimer = null;
let cashOrderCode = null;
let cashPrice = 0;

/**
 * Bắt đầu luồng thanh toán tiền mặt.
 * Được gọi khi người dùng nhấn nút "Tiền Mặt".
 */
async function startCashPayment() {
    const currentCart = getCart();
    if (currentCart.length === 0) return;

    const total = currentCart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    try {
        // Tạo đơn hàng
        const firstItem = currentCart[0];
        const orderResult = await apiCreateOrder(firstItem.product_id, firstItem.quantity);

        if (!orderResult.success) {
            showToast(orderResult.message || 'Không thể tạo đơn hàng');
            return;
        }

        cashOrderCode = orderResult.data.order_id;
        cashPrice = total;

        showCashModal(cashOrderCode, total);

        // Kết nối WebSocket (phương thức chính)
        connectPaymentSocket(
            cashOrderCode,
            (orderId) => handleCashPaymentSuccess(orderId, null),
            (reason) => showToast(`Thanh toán thất bại: ${reason}`)
        );

        // Polling dự phòng (cập nhật UI số tiền đã nhét)
        startCashPolling(cashOrderCode, total);

    } catch (err) {
        console.error('Cash checkout error:', err);
        showToast('Lỗi kết nối server. Vui lòng thử lại.');
    }
}

/**
 * Hiển thị Cash Modal với thông tin đơn hàng.
 */
function showCashModal(orderCode, amount) {
    const modal = document.getElementById('cash-modal');
    document.getElementById('cash-price-display').textContent = formatCurrency(amount);
    document.getElementById('cash-inserted-display').textContent = formatCurrency(0);
    document.getElementById('cash-remaining-display').textContent = formatCurrency(amount);
    document.getElementById('cash-progress-fill').style.width = '0%';
    document.getElementById('cash-progress-pct').textContent = '0%';

    const changeRow = document.getElementById('cash-change-row');
    if (changeRow) changeRow.style.display = 'none';

    document.getElementById('cash-payment-status').innerHTML = `
        <div class="status-waiting">
            <div class="pulse-ring"></div>
            <span>Đang chờ nhận tiền...</span>
        </div>`;

    modal.classList.add('active');
}

/**
 * Ẩn Cash Modal.
 */
function hideCashModal() {
    const modal = document.getElementById('cash-modal');
    if (modal) modal.classList.remove('active');
    stopCashPolling();
    disconnectPaymentSocket();
}

/**
 * Polling kiểm tra số tiền đã nhét và cập nhật UI.
 */
function startCashPolling(orderCode, price) {
    stopCashPolling();

    cashPollingTimer = setInterval(async () => {
        try {
            const result = await apiGetCashStatus(orderCode);
            if (!result.success) return;

            const d = result.data;
            updateCashModalUI(d.total_inserted, d.price, d.remaining, d.change, d.is_paid);

            if (d.is_paid) {
                handleCashPaymentSuccess(orderCode, d.change);
            }
        } catch (err) {
            console.log('Cash polling error:', err);
        }
    }, 1500); // Polling mỗi 1.5s
}

function stopCashPolling() {
    if (cashPollingTimer) {
        clearInterval(cashPollingTimer);
        cashPollingTimer = null;
    }
}

/**
 * Cập nhật giao diện Cash Modal với dữ liệu real-time.
 */
function updateCashModalUI(totalInserted, price, remaining, change, isPaid) {
    const pct = Math.min(100, Math.round((totalInserted / price) * 100));

    const insertedEl = document.getElementById('cash-inserted-display');
    const remainingEl = document.getElementById('cash-remaining-display');
    const progressFill = document.getElementById('cash-progress-fill');
    const progressPct = document.getElementById('cash-progress-pct');
    const changeRow = document.getElementById('cash-change-row');
    const changeEl = document.getElementById('cash-change-display');
    const remainingRow = document.getElementById('cash-remaining-row');

    if (insertedEl) insertedEl.textContent = formatCurrency(totalInserted);
    if (remainingEl) remainingEl.textContent = formatCurrency(remaining);
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (progressPct) progressPct.textContent = `${pct}%`;

    if (isPaid && change > 0) {
        if (changeRow) changeRow.style.display = '';
        if (changeEl) changeEl.textContent = formatCurrency(change);
        if (remainingRow) remainingRow.style.display = 'none';
    }
}

/**
 * Xử lý khi thanh toán tiền mặt thành công.
 */
function handleCashPaymentSuccess(orderCode, change) {
    stopCashPolling();
    disconnectPaymentSocket();
    hideCashModal();

    const successModal = document.getElementById('success-modal');
    const successOrderCode = document.getElementById('success-order-code');
    const successChangeEl = document.getElementById('success-change');
    const successChangeAmount = document.getElementById('success-change-amount');

    if (successOrderCode) successOrderCode.textContent = orderCode;

    // Hiển thị tiền thừa nếu có
    if (change !== null && change > 0 && successChangeEl && successChangeAmount) {
        successChangeAmount.textContent = formatCurrency(change);
        successChangeEl.style.display = '';
    }

    if (successModal) successModal.classList.add('active');

    clearCart();
    loadProducts(); // Refresh tồn kho
}

/**
 * Hủy thanh toán tiền mặt.
 */
function handleCancelCashPayment() {
    stopCashPolling();
    disconnectPaymentSocket();
    hideCashModal();
    showToast('Đã hủy thanh toán tiền mặt');
}

