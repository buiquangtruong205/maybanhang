/**
 * Vending Machine - Sales Interface
 * JavaScript logic for product display, cart management, and QR payment
 */

// ===========================
// Configuration
// ===========================
const API_BASE_URL = 'http://192.168.0.101:5000/api';
const POLLING_INTERVAL = 2000; // 2 seconds
const PAYMENT_TIMEOUT = 300; // 5 minutes in seconds

// ===========================
// State Management
// ===========================
let cart = [];
let products = [];
let currentOrderCode = null;
let pollingTimer = null;
let countdownTimer = null;
let countdownSeconds = PAYMENT_TIMEOUT;

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
        const response = await fetch(`${API_BASE_URL}/products`);
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
        showToast('Lỗi kết nối server. Vui lòng khởi động backend.');
        renderProducts(); // Show empty state
    }
}

async function createOrder(items, totalPrice) {
    try {
        // For simplicity, we'll use the first item's slot_id
        // In production, you'd handle multiple items properly
        const firstItem = items[0];

        const response = await fetch(`${API_BASE_URL}/orders/pending`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: firstItem.product_id,
                price_snapshot: totalPrice,
                slot_id: 1 // Default slot, should be dynamic in production
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
        const response = await fetch(`${API_BASE_URL}/payment/status/${orderCode}`);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error checking payment status:', error);
        throw error;
    }
}

async function checkOrderStatus(orderId) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`);
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
            method: 'POST'
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
                 alt="${product.name}">
            <h3 class="product-name">${product.name}</h3>
            <p class="product-price">${formatCurrency(product.price)}</p>
        </div>
        `;
    }).join('');
    
    // Gán event handler cho tất cả ảnh sản phẩm
    productsGrid.querySelectorAll('.product-image').forEach(img => {
        img.onerror = function() {
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
        img.onerror = function() {
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

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: product.product_id,
            name: product.name,
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
            // Sử dụng qr_code nếu có, nếu không thì dùng checkout_url để tạo QR
            const qrData = paymentResult.data.qr_code || paymentResult.data.checkout_url;
            showQRModal(qrData, currentOrderCode, total);
            startPaymentPolling(currentOrderCode);
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
    qrCode.onerror = function() {
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
}

function startPaymentPolling(orderCode) {
    pollingTimer = setInterval(async () => {
        try {
            // Kiểm tra order status từ database trước (nhanh hơn)
            const orderStatus = await checkOrderStatus(orderCode);
            
            if (orderStatus.success && orderStatus.data && orderStatus.data.status === 'completed') {
                handlePaymentSuccess(orderCode);
                return;
            }
            
            // Nếu order chưa completed, kiểm tra PayOS status
            const paymentStatus = await checkPaymentStatus(orderCode);
            
            // PayOS có thể trả về status: PAID, SUCCESS, COMPLETED, hoặc các giá trị khác
            const payosStatus = paymentStatus.success && paymentStatus.data ? paymentStatus.data.status : null;
            const isPaid = payosStatus && (
                payosStatus.toUpperCase() === 'PAID' || 
                payosStatus.toUpperCase() === 'SUCCESS' || 
                payosStatus.toUpperCase() === 'COMPLETED'
            );
            
            if (isPaid) {
                // PayOS đã báo thành công, nhưng database chưa cập nhật
                // Endpoint payment/status sẽ tự động sync, nhưng để chắc chắn, kiểm tra lại order status sau 1 giây
                setTimeout(async () => {
                    const recheckOrder = await checkOrderStatus(orderCode);
                    if (recheckOrder.success && recheckOrder.data && recheckOrder.data.status === 'completed') {
                        handlePaymentSuccess(orderCode);
                    }
                }, 1000);
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
});

