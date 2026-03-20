/**
 * app.js — Entry point: khởi tạo ứng dụng, load sản phẩm, đăng ký event listeners
 * Phụ thuộc: tất cả module trên (config, api, ui, cart, payment, iot, websocket)
 *
 * Chú ý: `cart` state được quản lý bởi cart.js. Truy cập qua getCart().
 */

// Danh sách sản phẩm được tải từ server
let products = [];

// ===========================
// Session Management
// ===========================
const SESSION_ID = 'session-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now();
let heartbeatInterval;

async function startHeartbeat() {
    try {
        const res = await apiSendHeartbeat(SESSION_ID);
        if (res && res.rejected) {
            showInUseOverlay();
        } else if (res && res.success === false) {
            console.warn(`[app.js] ❌ Heartbeat failed: ${res.message || 'Unknown error'}`);
            // If it's an auth error, we might want to show the setup overlay again
            if (res.message && res.message.includes('Invalid machine key')) {
                showSetupOverlay();
            }
        } else {
            hideInUseOverlay();
        }
    } catch (err) {
        console.error('Lỗi khi gửi heartbeat:', err);
    }
}

function showInUseOverlay() {
    const overlay = document.getElementById('in-use-overlay');
    if (overlay && overlay.style.display !== 'flex') {
        overlay.style.display = 'flex';
    }
}

function hideInUseOverlay() {
    const overlay = document.getElementById('in-use-overlay');
    if (overlay && overlay.style.display !== 'none') {
        overlay.style.display = 'none';
    }
}

function showSetupOverlay() {
    const overlay = document.getElementById('setup-overlay');
    if (overlay && overlay.style.display !== 'flex') {
        overlay.style.display = 'flex';
    }
}

function checkConfig() {
    if (!ENV.MACHINE_ID || !ENV.MACHINE_KEY) {
        console.warn('[app.js] ⚠️ Machine not configured. Showing setup overlay.');
        showSetupOverlay();
        return false;
    }
    return true;
}

function clearConfig() {
    if (confirm('Bạn có chắc chắn muốn xóa cấu hình hiện tại của máy này không?')) {
        localStorage.removeItem('VITE_MACHINE_ID');
        localStorage.removeItem('VITE_MACHINE_KEY');
        alert('Đã xóa cấu hình. Trang web sẽ tải lại.');
        location.reload();
    }
}

function saveManualConfig() {
    const id = document.getElementById('setup-machine-id').value;
    const key = document.getElementById('setup-machine-key').value;

    if (!id || !key) {
        alert('Vui lòng nhập đầy đủ ID và Key');
        return;
    }

    localStorage.setItem('VITE_MACHINE_ID', id);
    localStorage.setItem('VITE_MACHINE_KEY', key);
    alert('Đã lưu cấu hình thành công!');
    location.reload();
}

// Expose to global for HTML button
window.clearConfig = clearConfig;
window.saveManualConfig = saveManualConfig;

// ===========================
// Load Products
// ===========================

/**
 * Tải danh sách sản phẩm từ server và render.
 * Hàm này cũng được gọi lại sau khi thanh toán thành công.
 */
async function loadProducts() {
    try {
        // 1. Kiểm tra trạng thái máy
        const statusData = await apiFetchMachineStatus();
        if (statusData.success) {
            const status = (statusData.data.status || '').toLowerCase();
            if (status !== 'active' && status !== 'online') {
                renderMachineUnavailable(statusData.data.status); // Keep original case for display
                return;
            }
        }

        // 2. Fetch slots và products song song
        const [slotsResult, productsResult] = await Promise.all([
            apiFetchSlots(),
            apiFetchProducts(),
        ]);

        if (slotsResult.success && productsResult.success) {
            // Map product_id → product (chỉ các sản phẩm active)
            const productMap = {};
            for (const p of productsResult.data) {
                if (p.active) productMap[p.product_id] = p;
            }

            // Chỉ hiển thị sản phẩm được gán vào slot
            products = [];
            for (const slot of slotsResult.data) {
                if (slot.product_id && productMap[slot.product_id]) {
                    const info = productMap[slot.product_id];
                    products.push({
                        product_id: info.product_id,
                        product_name: info.product_name,
                        price: info.price,
                        image: info.image,
                        active: info.active,
                        stock: slot.stock,
                        slot_code: slot.slot_code,
                        slot_id: slot.slot_id,
                    });
                }
            }

            // [NEW] Khởi tạo WebSocket đồng bộ máy nếu chưa có
            if (ENV.MACHINE_ID) {
                connectMachineSocket(
                    ENV.MACHINE_ID, 
                    // 1. Stock Update
                    (data) => {
                        const pIndex = products.findIndex(p => p.slot_code === data.slot_code);
                        if (pIndex !== -1) {
                            console.log(`🔄 Updating stock for ${data.slot_code}: ${products[pIndex].stock} -> ${data.new_stock}`);
                            products[pIndex].stock = data.new_stock;
                            renderProducts(products); // Re-render UI
                        }
                    },
                    // 2. [NEW] Payment Update (Cash)
                    (data) => {
                        // data: {order_id: 123, status: 'completed', paid: 10000, remaining: 0, denomination: 10000}
                        console.log('💰 Real-time Cash Update received:', data);
                        if (typeof updateCashModalUI === 'function') {
                            updateCashModalUI(data.paid, data.price || 0, data.remaining, data.change || 0, data.status === 'completed');
                        }
                        if (data.status === 'completed' && typeof handleCashPaymentSuccess === 'function') {
                            handleCashPaymentSuccess(data.order_id, data.change || 0);
                        }
                    }
                );
            }

            renderProducts(products);
        } else {
            showToast('Không thể tải danh sách sản phẩm');
            renderProducts([]);
        }
    } catch (err) {
        console.error('Error loading products:', err);
        showToast('Lỗi kết nối server. Vui lòng kiểm tra backend.');
        renderProducts([]);
    }
}

// ===========================
// Global wrappers (gọi từ HTML onclick)
// ===========================

/**
 * Wrapper cho onclick="addToCart(id)" trong product card (HTML inline).
 * Hàm addToCart thực sự nằm trong cart.js và nhận thêm mảng products.
 */
function addToCart(productId, slotCode) {
    // Gọi sang cart.js, truyền danh sách products hiện tại để kiểm tra stock
    window._cartAddToCart(productId, slotCode, products);
}

// ===========================
// View Management (Mobile)
// ===========================

function showCartView() {
    const mainContainer = document.querySelector('.main-container');
    const cartSection = document.querySelector('.cart-section');
    const backBtn = document.getElementById('cart-back-btn');
    if (mainContainer && window.innerWidth <= 900) {
        mainContainer.classList.add('view-cart');
        if (cartSection) {
            cartSection.classList.add('expanded');
        }
        if (backBtn) {
            backBtn.style.display = 'inline-flex';
        }
    }
}

function hideCartView() {
    const mainContainer = document.querySelector('.main-container');
    const cartSection = document.querySelector('.cart-section');
    const backBtn = document.getElementById('cart-back-btn');
    if (mainContainer && window.innerWidth <= 900) {
        mainContainer.classList.remove('view-cart');
        if (cartSection) {
            cartSection.classList.remove('expanded');
        }
        if (backBtn) {
            backBtn.style.display = 'none';
        }
    }
}

// ===========================
// Event Listeners
// ===========================

document.getElementById('qr-close')?.addEventListener('click', hideQRModal);
document.getElementById('cancel-payment-btn')?.addEventListener('click', handleCancelPayment);
document.getElementById('success-close-btn')?.addEventListener('click', hideSuccessModal);

// Nút đóng giỏ hàng trên mobile
document.getElementById('cancel-cash-btn')?.addEventListener('click', () => {
    hideCartView();
    clearCart();
});

// Đóng modal khi click overlay
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
        hideQRModal();
        hideCashModal();
        hideSuccessModal();
    });
});

// Mobile: back to products when clicking title in products view
const mainContainer = document.querySelector('.main-container');
if (mainContainer && window.innerWidth <= 900) {
    document.addEventListener('click', (e) => {
        // Click on products section title to go back
        if (e.target.closest('.products-section .section-title') && mainContainer.classList.contains('view-cart')) {
            hideCartView();
        }
    });
}

// ===========================
// DOMContentLoaded — Khởi tạo
// ===========================

document.addEventListener('DOMContentLoaded', () => {
    // 0. Kiểm tra cấu hình
    if (!checkConfig()) return;

    // Đồng hồ
    updateClock();
    setInterval(updateClock, 1000);

    // Bắt đầu heartbeat
    startHeartbeat();
    heartbeatInterval = setInterval(startHeartbeat, 3000);

    // Tải sản phẩm
    loadProducts();

    // Render giỏ hàng trống
    renderCart(getCart());
});
