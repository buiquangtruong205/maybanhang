/**
 * cart.js — Quản lý trạng thái giỏ hàng
 * Phụ thuộc: ui.js (renderCart, showToast)
 */

// State giỏ hàng (module-level)
let cart = [];

/**
 * Thêm sản phẩm vào giỏ (giới hạn 1 sản phẩm mỗi lần mua).
 * @param {number} productId
 * @param {Array}  products  - Danh sách sản phẩm hiện có
 */
function addToCart(productId, slotCode, products) {
    const product = products.find(p => p.product_id === productId && p.slot_code === slotCode);
    if (!product) return;

    if (product.stock !== undefined && product.stock <= 0) {
        showToast('Sản phẩm đã hết hàng!');
        return;
    }

    // Mỗi lần chỉ mua 1 sản phẩm — thay thế giỏ hàng hoàn toàn
    cart = [{
        product_id: product.product_id,
        slot_code: product.slot_code,
        name: product.product_name,
        price: product.price,
        image: product.image,
        quantity: 1,
    }];

    renderCart(cart);
    
    // Switch to cart view
    showCartView();
}

/**
 * Xóa một sản phẩm khỏi giỏ hàng.
 * @param {number} productId
 */
function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    renderCart(cart);
    // Return to products view if cart is empty
    if (cart.length === 0) {
        hideCartView();
    }
}

/**
 * Xóa toàn bộ giỏ hàng.
 */
function clearCart() {
    cart = [];
    renderCart(cart);
}

/**
 * Lấy giỏ hàng hiện tại (read-only snapshot).
 * @returns {Array}
 */
function getCart() {
    return [...cart];
}

// Expose cho app.js — được gọi qua window._cartAddToCart(productId, products)
window._cartAddToCart = addToCart;
