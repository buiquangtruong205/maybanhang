/**
 * Vending Machine - Sales Interface
 * JavaScript logic for product display, cart management, and QR payment
 */

// ===========================
// Configuration
// ===========================
const API_BASE_URL = 'http://localhost:5000/api';
const POLLING_INTERVAL = 2000; // 2 seconds
const PAYMENT_TIMEOUT = 300; // 5 minutes in seconds

// ===========================
// State Management
// ===========================
let cart = [];
let products = [];
let currentOrderCode = null;
let currentPaymentCode = null; // Payment code unique từ PayOS (order_id * 10000 + suffix)
let pollingTimer = null;
let countdownTimer = null;
let countdownSeconds = PAYMENT_TIMEOUT;
let paymentSocket = null; // Socket.IO instance
const WS_BASE_URL = API_BASE_URL.replace('/api', ''); // http://localhost:5000

// Placeholder images (sẽ được khởi tạo sau khi hàm getPlaceholderImage được định nghĩa)
let PLACEHOLDER_IMAGE_150;
let PLACEHOLDER_IMAGE_50;

// ===========================
// DOM Elements
// ===========================
const productsGrid = document.getElementById('products-grid');
const cartItems = document.getElementById('cart-items');
const cartCount = document.getElementById('cart-count');
const totalAmount = document.getElementById('total-amount');
const checkoutBtn = document.getElementById('checkout-btn');
const clockEl = document.getElementById('clock');

// QR Modal
const qrModal = document.getElementById('qr-modal');
const qrCode = document.getElementById('qr-code');
const orderCodeDisplay = document.getElementById('order-code-display');
const paymentAmountDisplay = document.getElementById('payment-amount-display');
const paymentStatus = document.getElementById('payment-status');
const countdown = document.getElementById('countdown');
const qrClose = document.getElementById('qr-close');
const cancelPaymentBtn = document.getElementById('cancel-payment-btn');

// Success Modal
const successModal = document.getElementById('success-modal');
const successOrderCode = document.getElementById('success-order-code');
const successCloseBtn = document.getElementById('success-close-btn');

// Toast
const errorToast = document.getElementById('error-toast');
const toastMessage = document.getElementById('toast-message');

// ===========================
// Utility Functions
// ===========================
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

function getPlaceholderImage(width = 150, height = 150, text = 'No Image') {
    // Tạo placeholder image dạng SVG data URI để tránh lỗi mạng
    const svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#e0e0e0"/><text x="50%" y="50%" font-family="Arial,sans-serif" font-size="12" fill="#999" text-anchor="middle" dominant-baseline="middle">${text}</text></svg>`;
    // Sử dụng URL encoding thay vì base64 để đảm bảo hoạt động
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

function getImageUrl(imagePath) {
    // Convert relative image path từ backend thành full URL
    if (!imagePath) {
        return null;
    }

    // Nếu đã là full URL (http/https), trả về nguyên bản
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
        return imagePath;
    }

    // Nếu là data URI, trả về nguyên bản
    if (imagePath.startsWith('data:')) {
        return imagePath;
    }

    // Convert relative path thành full URL
    // Backend trả về dạng /static/uploads/filename.jpg
    // Cần convert thành http://192.168.0.101:5000/static/uploads/filename.jpg
    const baseUrl = API_BASE_URL.replace('/api', ''); // Lấy base URL (http://192.168.0.101:5000)

    // Đảm bảo imagePath bắt đầu bằng /
    const path = imagePath.startsWith('/') ? imagePath : '/' + imagePath;

    return baseUrl + path;
}

// Hàm helper để xử lý lỗi ảnh
function handleImageError(img, placeholder) {
    if (img.src !== placeholder) {
        img.src = placeholder;
        img.onerror = null; // Ngăn vòng lặp vô hạn
    }
}

// Khởi tạo placeholder images
PLACEHOLDER_IMAGE_150 = getPlaceholderImage(150, 150, 'No Image');
PLACEHOLDER_IMAGE_50 = getPlaceholderImage(50, 50, 'No Image');

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function showToast(message, duration = 3000) {
    toastMessage.textContent = message;
    errorToast.classList.add('active');
    setTimeout(() => {
        errorToast.classList.remove('active');
    }, duration);
}

function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ===========================
// API Functions
// ===========================
async function fetchProducts() {
    try {
        // 1. Check machine status first
        // Assume ID 1 for this demo context, similar to how X-Machine-Key is hardcoded
        const statusRes = await fetch(`${API_BASE_URL}/machines/1`);
        const statusData = await statusRes.json();

        if (statusData.success) {
            const status = statusData.data.status;
            // Allow: active, online. Disallow: inactive, maintenance
            if (status !== 'active' && status !== 'online') {
                productsGrid.innerHTML = `
                    <div class="maintenance-mode">
                        <div class="maintenance-icon">🚫</div>
                        <h2>Máy đang tạm ngưng hoạt động</h2>
                        <p>Trạng thái: ${status === 'maintenance' ? 'Đang bảo trì' : 'Ngưng hoạt động'}</p>
                    </div>
                `;
                // Disable checkout if needed, though hidden products prevent adding to cart
                return;
            }
        }

        // 2. Fetch products if active
        const response = await fetch(`${API_BASE_URL}/products`, {
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();

        if (result.success) {
            products = result.data.filter(p => p.active);
            renderProducts();
        } else {
            showToast('Không thể tải danh sách sản phẩm');
            renderProducts(); // Show empty state
        }
    } catch (error) {
        console.error('Error fetching products:', error);
        // Don't block purely on network error, try to show cached or empty
        showToast('Lỗi kết nối server. Vui lòng kiểm tra backend.');
        renderProducts();
    }
}

async function createOrder(items, totalPrice) {
    try {
        // Sử dụng endpoint IoT để tạo order
        const firstItem = items[0];

        const response = await fetch(`${API_BASE_URL}/iot/create-order`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: firstItem.product_id,
                quantity: firstItem.quantity
                // slot_code không cần trong demo mode
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error creating order:', error);
        throw error;
    }
}

async function createPayment(orderCode, amount, items) {
    try {
        const response = await fetch(`${API_BASE_URL}/payment/create`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_code: orderCode,
                amount: amount,
                description: `Thanh toán đơn hàng #${orderCode}`,
                items: items.map(item => ({
                    name: item.name,
                    quantity: item.quantity,
                    price: item.price
                }))
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error creating payment:', error);
        throw error;
    }
}

async function checkPaymentStatus(orderCode) {
    try {
        const response = await fetch(`${API_BASE_URL}/payment/status/${orderCode}`, {
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error checking payment status:', error);
        throw error;
    }
}

async function checkOrderStatus(orderId) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error checking order status:', error);
        throw error;
    }
}

async function cancelPayment(orderCode) {
    try {
        const response = await fetch(`${API_BASE_URL}/payment/cancel/${orderCode}`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': 'may1',
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error cancelling payment:', error);
        throw error;
    }
}

// ===========================
// Render Functions
// ===========================
function renderProducts() {
    if (products.length === 0) {
        productsGrid.innerHTML = `
            <div class="loading-spinner">
                <p>Không có sản phẩm nào</p>
            </div>
        `;
        return;
    }

    productsGrid.innerHTML = products.map(product => {
        const imageUrl = product.image ? getImageUrl(product.image) : PLACEHOLDER_IMAGE_150;
        return `
        <div class="product-card ${product.stock <= 0 ? 'out-of-stock' : ''}" 
             data-product-id="${product.product_id}"
             onclick="addToCart(${product.product_id})">
            <img class="product-image" 
                 src="${imageUrl}" 
                 alt="${product.product_name}">
            <h3 class="product-name">
                ${product.product_name} 
                <span class="product-stock">(SL: ${product.stock})</span>
            </h3>
            <p class="product-price">${formatCurrency(product.price)}</p>
        </div>
        `;
    }).join('');

    // Gán event handler cho tất cả ảnh sản phẩm
    productsGrid.querySelectorAll('.product-image').forEach(img => {
        img.onerror = function () {
            handleImageError(this, PLACEHOLDER_IMAGE_150);
        };
    });
}


function renderCart() {
    if (cart.length === 0) {
        cartItems.innerHTML = `
            <div class="empty-cart">
                <span class="empty-icon">📦</span>
                <p>Chưa có sản phẩm nào</p>
            </div>
        `;
        cartCount.textContent = '0';
        totalAmount.textContent = formatCurrency(0);
        checkoutBtn.disabled = true;
        return;
    }

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

    cartItems.innerHTML = cart.map(item => {
        const imageUrl = item.image ? getImageUrl(item.image) : PLACEHOLDER_IMAGE_50;
        return `
        <div class="cart-item" data-product-id="${item.product_id}">
            <img class="cart-item-image" 
                 src="${imageUrl}" 
                 alt="${item.name}">
            <div class="cart-item-info">
                <p class="cart-item-name">${item.name}</p>
                <p class="cart-item-price">${formatCurrency(item.price)}</p>
            </div>
            <div class="cart-item-quantity">
                <button class="qty-btn" onclick="updateQuantity(${item.product_id}, -1)">-</button>
                <span class="qty-value">${item.quantity}</span>
                <button class="qty-btn" onclick="updateQuantity(${item.product_id}, 1)">+</button>
            </div>
            <button class="cart-item-remove" onclick="removeFromCart(${item.product_id})">✕</button>
        </div>
        `;
    }).join('');

    // Gán event handler cho tất cả ảnh trong giỏ hàng
    cartItems.querySelectorAll('.cart-item-image').forEach(img => {
        img.onerror = function () {
            handleImageError(this, PLACEHOLDER_IMAGE_50);
        };
    });

    cartCount.textContent = itemCount;
    totalAmount.textContent = formatCurrency(total);
    checkoutBtn.disabled = false;
}

// ===========================
// Cart Functions
// ===========================
function addToCart(productId) {
    const product = products.find(p => p.product_id === productId);
    if (!product) return;

    const existingItem = cart.find(item => item.product_id === productId);
    const currentQty = existingItem ? existingItem.quantity : 0;

    // Check stock limit
    if (product.stock !== undefined && currentQty + 1 > product.stock) {
        showToast('vui lòng giảm số lượng hoặc chọn sản phẩm khác xin cảm ơn!');
        return;
    }

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: product.product_id,
            name: product.product_name,  // Use product_name from API
            price: product.price,
            image: product.image,
            quantity: 1
        });
    }

    renderCart();
}

function updateQuantity(productId, delta) {
    const item = cart.find(item => item.product_id === productId);
    if (!item) return;

    // Check stock limit when increasing quantity
    if (delta > 0) {
        const product = products.find(p => p.product_id === productId);
        if (product && product.stock !== undefined && item.quantity + delta > product.stock) {
            showToast('vui lòng giảm số lượng hoặc chọn sản phẩm khác xin cảm ơn!');
            return;
        }
    }

    item.quantity += delta;

    if (item.quantity <= 0) {
        removeFromCart(productId);
    } else {
        renderCart();
    }
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    renderCart();
}

function clearCart() {
    cart = [];
    renderCart();
}

// ===========================
// Payment Functions
// ===========================
async function startCheckout() {
    if (cart.length === 0) return;

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    try {
        // Tạo order trong backend trước
        const orderResult = await createOrder(cart, total);
        if (!orderResult.success) {
            showToast(orderResult.message || 'Không thể tạo đơn hàng');
            return;
        }
        currentOrderCode = orderResult.data.order_id;

        // Create PayOS payment link
        const paymentResult = await createPayment(currentOrderCode, total, cart);

        if (paymentResult.success) {
            // Lưu payment_code unique từ PayOS (để dùng cho polling)
            currentPaymentCode = paymentResult.data.payment_code || currentOrderCode;
            console.log(`💳 Payment created: order_id=${currentOrderCode}, payment_code=${currentPaymentCode}`);

            // Sử dụng qr_code nếu có, nếu không thì dùng checkout_url để tạo QR
            const qrData = paymentResult.data.qr_code || paymentResult.data.checkout_url;
            showQRModal(qrData, currentOrderCode, total);

            // Sử dụng payment_code cho polling PayOS (Fallback)
            startPaymentPolling(currentOrderCode, currentPaymentCode);

            // Khởi tạo WebSocket connection (Primary Real-time)
            connectPaymentSocket(currentOrderCode);
        } else {
            showToast(paymentResult.message || 'Không thể tạo mã thanh toán. Vui lòng kiểm tra cấu hình PayOS.');
        }
    } catch (error) {
        console.error('Checkout error:', error);
        showToast('Lỗi kết nối server. Vui lòng thử lại.');
    }
}

function showQRModal(qrData, orderCode, amount) {
    // QR code từ PayOS có thể là URL hoặc text string
    // Nếu là text string, cần generate QR code image
    let qrImageUrl;

    if (!qrData) {
        // Nếu không có QR code, sử dụng placeholder
        qrImageUrl = getPlaceholderImage(300, 300, 'No QR Code');
    } else if (qrData.startsWith('http://') || qrData.startsWith('https://') || qrData.startsWith('data:')) {
        // Nếu đã là URL hoặc data URI, dùng trực tiếp
        qrImageUrl = qrData;
    } else {
        // Nếu là text string, generate QR code image từ API
        // Sử dụng API online để tạo QR code
        const encodedText = encodeURIComponent(qrData);
        qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodedText}`;
    }

    // Gán event handler để xử lý lỗi load QR code
    qrCode.onerror = function () {
        // Nếu QR code image không load được, thử dùng placeholder
        if (qrImageUrl && !qrImageUrl.startsWith('data:')) {
            this.src = getPlaceholderImage(300, 300, 'QR Code Error');
        }
    };

    qrCode.src = qrImageUrl;
    orderCodeDisplay.textContent = orderCode;
    paymentAmountDisplay.textContent = formatCurrency(amount);

    // Reset countdown
    countdownSeconds = PAYMENT_TIMEOUT;
    countdown.textContent = formatTime(countdownSeconds);

    // Reset status
    paymentStatus.innerHTML = `
        <div class="status-waiting">
            <div class="pulse-ring"></div>
            <span>Đang chờ thanh toán...</span>
        </div>
    `;

    qrModal.classList.add('active');
    startCountdown();
}

function hideQRModal() {
    qrModal.classList.remove('active');
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket(); // Clean up WebSocket
}

function startPaymentPolling(orderCode, paymentCode) {
    console.log(`🔄 Starting payment polling: order_id=${orderCode}, payment_code=${paymentCode}`);
    pollingTimer = setInterval(async () => {
        try {
            // Kiểm tra order status từ database trước (nhanh hơn)
            const orderStatus = await checkOrderStatus(orderCode);
            console.log('📋 Order status:', orderStatus.data);

            // API trả về status_payment, không phải status
            if (orderStatus.success && orderStatus.data && orderStatus.data.status_payment === 'completed') {
                console.log('✅ Order completed from DB!');
                handlePaymentSuccess(orderCode);
                return;
            }

            // Nếu order chưa completed, kiểm tra PayOS status bằng payment_code
            const paymentStatus = await checkPaymentStatus(paymentCode);
            console.log('💳 PayOS status:', paymentStatus.data?.status);

            // PayOS có thể trả về status: PAID, SUCCESS, COMPLETED
            const payosStatus = paymentStatus.success && paymentStatus.data ? paymentStatus.data.status : null;
            const isPaid = payosStatus && (
                payosStatus.toUpperCase() === 'PAID' ||
                payosStatus.toUpperCase() === 'SUCCESS' ||
                payosStatus.toUpperCase() === 'COMPLETED'
            );

            if (isPaid) {
                console.log('✅ PayOS confirmed PAID! Triggering success...');
                // Gọi ngay handlePaymentSuccess khi PayOS báo PAID
                handlePaymentSuccess(orderCode);
                return;
            }
        } catch (error) {
            console.log('Polling error:', error);
        }
    }, POLLING_INTERVAL);
}

function stopPaymentPolling() {
    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

function startCountdown() {
    countdownTimer = setInterval(() => {
        countdownSeconds--;
        countdown.textContent = formatTime(countdownSeconds);

        if (countdownSeconds <= 0) {
            handlePaymentTimeout();
        }
    }, 1000);
}

function stopCountdown() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
}

function handlePaymentSuccess(orderCode) {
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket(); // Clean up WebSocket
    hideQRModal();

    // Show success modal
    successOrderCode.textContent = orderCode;
    successModal.classList.add('active');

    // Clear cart
    clearCart();

    // Refresh products (to update stock)
    fetchProducts();
}

function handlePaymentTimeout() {
    stopPaymentPolling();
    stopCountdown();
    disconnectPaymentSocket(); // Clean up WebSocket
    hideQRModal();
    showToast('Hết thời gian thanh toán. Vui lòng thử lại.');
}

async function handleCancelPayment() {
    if (currentOrderCode) {
        try {
            await cancelPayment(currentOrderCode);
        } catch (error) {
            console.log('Cancel error:', error);
        }
    }
    hideQRModal();
    showToast('Đã hủy thanh toán');
}

// ===========================
// WebSocket Functions
// ===========================
function connectPaymentSocket(orderCode) {
    // Nếu đã có socket, disconnect trước
    if (paymentSocket) {
        paymentSocket.disconnect();
    }

    try {
        console.log(`🔌 Connecting to WebSocket: ${WS_BASE_URL}/payment`);

        // Initialize Socket.IO connection to /payment namespace
        paymentSocket = io(`${WS_BASE_URL}/payment`, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5
        });

        // Connection handlers
        paymentSocket.on('connect', () => {
            console.log('✅ WebSocket connected successfully');
            // Subscribe to this specific order
            paymentSocket.emit('subscribe', { order_id: orderCode });
        });

        paymentSocket.on('subscribed', (data) => {
            console.log(`📢 Subscribed to updates for order #${data.order_id}`);
            // Khi đã kết nối WS thành công, có thể giảm tần suất polling hoặc stop hẳn polling
            // Tuy nhiên, để an toàn (redundancy), ta vẫn giữ polling nhưng có thể tăng interval lên nếu muốn
            // Ở đây ta giữ nguyên polling làm backup layer
        });

        paymentSocket.on('payment_success', (data) => {
            console.log('🎉 Payment success event received via WebSocket:', data);

            // Verify correct order
            if (parseInt(data.order_id) === parseInt(orderCode)) {
                // Handle success immediately
                handlePaymentSuccess(orderCode);
            }
        });

        paymentSocket.on('payment_failed', (data) => {
            console.log('❌ Payment failed event:', data);
            if (parseInt(data.order_id) === parseInt(orderCode)) {
                showToast(`Thanh toán thất bại: ${data.reason}`);
            }
        });

        paymentSocket.on('disconnect', (reason) => {
            console.log('⚠️ WebSocket disconnected:', reason);
            // Nếu mất kết nối WS, polling vẫn đang chạy sẽ đóng vai trò backup
        });

        paymentSocket.on('connect_error', (error) => {
            console.log('⚠️ WebSocket connection error:', error);
        });

    } catch (e) {
        console.error('Error initializing WebSocket:', e);
    }
}

function disconnectPaymentSocket() {
    if (paymentSocket) {
        console.log('🔌 Disconnecting WebSocket...');
        paymentSocket.disconnect();
        paymentSocket = null;
    }
}

function hideSuccessModal() {
    successModal.classList.remove('active');
}

// ===========================
// Event Listeners
// ===========================
checkoutBtn.addEventListener('click', startCheckout);
qrClose.addEventListener('click', hideQRModal);
cancelPaymentBtn.addEventListener('click', handleCancelPayment);
successCloseBtn.addEventListener('click', hideSuccessModal);

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
        hideQRModal();
        hideSuccessModal();
    });
});

// Mobile cart toggle
const cartSection = document.querySelector('.cart-section');
const sectionTitle = cartSection?.querySelector('.section-title');
if (sectionTitle && window.innerWidth <= 900) {
    sectionTitle.addEventListener('click', () => {
        cartSection.classList.toggle('expanded');
    });
}

// ===========================
// Initialize
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    // Update clock
    updateClock();
    setInterval(updateClock, 1000);

    // Load products
    fetchProducts();

    // Initial cart render
    renderCart();

    // IoT Panel toggle
    const iotToggle = document.getElementById('iot-toggle');
    const iotPanelBody = document.getElementById('iot-panel-body');
    if (iotToggle && iotPanelBody) {
        iotToggle.addEventListener('click', () => {
            iotPanelBody.classList.toggle('collapsed');
            iotToggle.textContent = iotPanelBody.classList.contains('collapsed') ? '▶' : '▼';
        });
    }
});

// ===========================
// Device Status & Logging
// ===========================
const MACHINE_KEY = 'may1';

function iotLog(message, isError = false) {
    const logContent = document.getElementById('log-content');
    if (!logContent) return;

    const time = new Date().toLocaleTimeString('vi-VN');
    const entry = document.createElement('div');
    entry.className = `log-entry ${isError ? 'log-error' : 'log-success'}`;

    // Check if message is an object/json
    let displayMessage = message;
    if (typeof message === 'object') {
        displayMessage = '<pre>' + JSON.stringify(message, null, 2) + '</pre>';
    }

    entry.innerHTML = `<span class="log-time">[${time}]</span> ${displayMessage}`;
    logContent.insertBefore(entry, logContent.firstChild);

    // Keep only last 50 entries
    while (logContent.children.length > 50) {
        logContent.removeChild(logContent.lastChild);
    }
}

/**
 * Upload log to server for persistent storage
 */
async function uploadDeviceLog(level, message, data = null) {
    try {
        await fetch(`${API_BASE_URL}/iot/logs`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': MACHINE_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level: level,
                message: message,
                data: data
            })
        });
    } catch (e) {
        console.error('Failed to upload log:', e);
    }
}

// Check Device Identity
async function checkDeviceIdentity() {
    iotLog('🔍 Đang kiểm tra định danh thiết bị...');
    try {
        // Fetch machine identity
        // Machine ID is hardcoded to 1 for this demo context
        const token = localStorage.getItem('token'); // Assuming admin token if needed, or machine key auth

        // Use endpoint that returns identity for machine 1
        // Note: In a real scenario, this might need auth token. 
        // For this demo, we'll try to fetch public info or use machine key if endpoint allows.
        // Based on backend code: /devices/identity/<int:machine_id> requires @token_required
        // AND /iot/register-device uses machine key.

        // Let's try to simulate a "registry check" by calling the registration endpoint 
        // which returns current status if already registered.

        const response = await fetch(`${API_BASE_URL}/iot/register-device`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': MACHINE_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mac_address: 'CHECK_STATUS', // Dummy update to get status back
                fingerprint: 'browser-client',
                firmware_version: '1.0.0-web'
            })
        });

        const result = await response.json();
        if (result.success) {
            iotLog(`✅ Định danh thiết bị: Đang hoạt động`);
            iotLog(result.data);
            uploadDeviceLog('info', 'Kiểm tra định danh: Thành công', result.data);
        } else {
            iotLog(`❌ Kiểm tra định danh thất bại: ${result.message}`, true);
            uploadDeviceLog('error', `Kiểm tra định danh thất bại: ${result.message}`);
        }
    } catch (error) {
        iotLog(`❌ Lỗi: ${error.message}`, true);
        uploadDeviceLog('error', `Lỗi kiểm tra định danh: ${error.message}`);
    }
}

// Check Device Session
async function checkDeviceSession() {
    iotLog('🔑 Đang kiểm tra phiên làm việc...');
    try {
        // We'll use heartbeat to check/refresh session
        const response = await fetch(`${API_BASE_URL}/iot/heartbeat`, {
            method: 'POST',
            headers: {
                'X-Machine-Key': MACHINE_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                uptime: 1,
                free_memory: 100,
                wifi_rssi: -50
            })
        });

        const result = await response.json();
        if (result.success) {
            iotLog(`✅ Phiên hợp lệ: ID ${result.data.session_id}`);
            iotLog(`   Giờ máy chủ: ${result.data.server_time}`);
            uploadDeviceLog('info', 'Kiểm tra phiên: Hợp lệ', result.data);
        } else {
            iotLog(`❌ Kiểm tra phiên thất bại: ${result.message}`, true);
            uploadDeviceLog('error', `Kiểm tra phiên thất bại: ${result.message}`);
        }
    } catch (error) {
        iotLog(`❌ Lỗi: ${error.message}`, true);
        uploadDeviceLog('error', `Lỗi kiểm tra phiên: ${error.message}`);
    }
}

// Send Heartbeat (Manual)
async function sendHeartbeat() {
    iotLog('💓 Đang gửi Heartbeat...');
    checkDeviceSession(); // Reuses logic
}

// Start log ready message
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (document.getElementById('iot-panel')) {
            iotLog('📱 Giám sát thiết bị đã sẵn sàng');
            iotLog('ℹ️ Sử dụng các nút bên dưới để kiểm tra trạng thái');
        }
    }, 1000);
});
