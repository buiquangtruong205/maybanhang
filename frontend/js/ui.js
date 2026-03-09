/**
 * ui.js — Render sản phẩm & giỏ hàng, các hàm tiện ích UI
 * Phụ thuộc: config.js (ENV)
 */

// ===========================
// Image Helpers
// ===========================

function getPlaceholderImage(width = 150, height = 150, text = 'No Image') {
    const svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#e0e0e0"/><text x="50%" y="50%" font-family="Arial,sans-serif" font-size="12" fill="#999" text-anchor="middle" dominant-baseline="middle">${text}</text></svg>`;
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

// Khởi tạo placeholder sẵn
const PLACEHOLDER_IMAGE_150 = getPlaceholderImage(150, 150, 'No Image');
const PLACEHOLDER_IMAGE_50 = getPlaceholderImage(50, 50, 'No Image');

function getImageUrl(imagePath) {
    if (!imagePath) return null;
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) return imagePath;
    if (imagePath.startsWith('data:')) return imagePath;
    const baseUrl = ENV.API_BASE_URL.replace('/api', '');
    const path = imagePath.startsWith('/') ? imagePath : '/' + imagePath;
    return baseUrl + path;
}

function handleImageError(img, placeholder) {
    if (img.src !== placeholder) {
        img.src = placeholder;
        img.onerror = null;
    }
}

// ===========================
// Format Helpers
// ===========================

function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
    }).format(amount);
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// ===========================
// Toast
// ===========================

function showToast(message, duration = 3000) {
    const errorToast = document.getElementById('error-toast');
    const toastMessage = document.getElementById('toast-message');
    toastMessage.textContent = message;
    errorToast.classList.add('active');
    setTimeout(() => errorToast.classList.remove('active'), duration);
}

// ===========================
// Clock
// ===========================

function updateClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    clockEl.textContent = new Date().toLocaleTimeString('vi-VN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
}

// ===========================
// Product Grid Render
// ===========================

/**
 * Render danh sách sản phẩm vào lưới.
 * @param {Array} products
 */
function renderProducts(products) {
    const productsGrid = document.getElementById('products-grid');
    if (!productsGrid) return;

    if (products.length === 0) {
        productsGrid.innerHTML = `<div class="loading-spinner"><p>Không có sản phẩm nào</p></div>`;
        return;
    }

    productsGrid.innerHTML = products.map(product => {
        const imageUrl = product.image ? getImageUrl(product.image) : PLACEHOLDER_IMAGE_150;
        const slotLabel = product.slot_code ? `[${product.slot_code}] ` : '';
        return `
        <div class="product-card ${product.stock <= 0 ? 'out-of-stock' : ''}"
             data-product-id="${product.product_id}"
             onclick="addToCart(${product.product_id})">
            <img class="product-image" src="${imageUrl}" alt="${product.product_name}">
            <h3 class="product-name">
                ${slotLabel}${product.product_name}
                <span class="product-stock">(SL: ${product.stock})</span>
            </h3>
            <p class="product-price">${formatCurrency(product.price)}</p>
        </div>
        `;
    }).join('');

    productsGrid.querySelectorAll('.product-image').forEach(img => {
        img.onerror = function () { handleImageError(this, PLACEHOLDER_IMAGE_150); };
    });
}

/**
 * Hiển thị thông báo máy đang bảo trì / tắt.
 * @param {string} status
 */
function renderMachineUnavailable(status) {
    const productsGrid = document.getElementById('products-grid');
    if (!productsGrid) return;
    productsGrid.innerHTML = `
        <div class="maintenance-mode">
            <div class="maintenance-icon">🚫</div>
            <h2>Máy đang tạm ngưng hoạt động</h2>
            <p>Trạng thái: ${status === 'maintenance' ? 'Đang bảo trì' : 'Ngưng hoạt động'}</p>
        </div>
    `;
}

// ===========================
// Cart Render
// ===========================

/**
 * Render giỏ hàng.
 * @param {Array} cart
 */
function renderCart(cart) {
    const cartItems = document.getElementById('cart-items');
    const cartCount = document.getElementById('cart-count');
    const totalAmount = document.getElementById('total-amount');
    const checkoutBtn = document.getElementById('checkout-btn');
    const checkoutCashBtn = document.getElementById('checkout-cash-btn');
    if (!cartItems) return;

    if (cart.length === 0) {
        cartItems.innerHTML = `
            <div class="empty-cart">
                <span class="empty-icon">📦</span>
                <p>Chưa có sản phẩm nào</p>
            </div>`;
        cartCount.textContent = '0';
        totalAmount.textContent = formatCurrency(0);
        if (checkoutBtn) checkoutBtn.disabled = true;
        if (checkoutCashBtn) checkoutCashBtn.disabled = true;
        return;
    }

    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    cartItems.innerHTML = cart.map(item => {
        const imageUrl = item.image ? getImageUrl(item.image) : PLACEHOLDER_IMAGE_50;
        return `
        <div class="cart-item" data-product-id="${item.product_id}">
            <img class="cart-item-image" src="${imageUrl}" alt="${item.name}">
            <div class="cart-item-info">
                <p class="cart-item-name">${item.name}</p>
                <p class="cart-item-price">${formatCurrency(item.price)}</p>
            </div>
            <div class="cart-item-quantity"><span class="qty-value">1</span></div>
            <button class="cart-item-remove" onclick="removeFromCart(${item.product_id})">✕</button>
        </div>`;
    }).join('');

    cartItems.querySelectorAll('.cart-item-image').forEach(img => {
        img.onerror = function () { handleImageError(this, PLACEHOLDER_IMAGE_50); };
    });

    cartCount.textContent = '1';
    totalAmount.textContent = formatCurrency(total);
    if (checkoutBtn) checkoutBtn.disabled = false;
    if (checkoutCashBtn) checkoutCashBtn.disabled = false;
}
