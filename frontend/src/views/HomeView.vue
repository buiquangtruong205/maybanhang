<template>
  <div class="home-page">
    <!-- Header -->
    <header class="home-header animate-fade-in">
      <div class="header-left">
        <div class="header-icon">
          <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
        </div>
        <div>
          <h1>Máy Bán Hàng Tự Động</h1>
          <p>Chọn sản phẩm yêu thích</p>
        </div>
      </div>
      <div class="status-indicator">
        <span class="status-dot" :class="isOnline ? 'online' : 'offline'" />
        <span :class="isOnline ? 'status-on' : 'status-off'">{{ isOnline ? 'Đang hoạt động' : 'Offline' }}</span>
      </div>
    </header>

    <!-- Skeleton Loading -->
    <div v-if="loading" class="products-container">
      <div class="products-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card">
          <div class="skeleton skeleton-image" />
          <div class="skeleton-body">
            <div class="skeleton skeleton-title" />
            <div class="skeleton skeleton-desc" />
            <div class="skeleton-row">
              <div class="skeleton skeleton-price" />
              <div class="skeleton skeleton-badge" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state animate-fade-in-up">
      <svg width="64" height="64" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
      <h3>Lỗi tải dữ liệu</h3>
      <p>{{ error }}</p>
      <button @click="loadProducts" class="retry-btn">🔄 Thử lại</button>
    </div>

    <!-- Products Grid -->
    <div v-else class="products-container">
      <div class="products-grid">
        <div v-for="(product, index) in availableProducts" :key="product.id"
             class="product-card"
             :class="{ 'out-of-stock': product.stock <= 0 }"
             :style="{ animationDelay: (index * 60) + 'ms' }"
             @click="selectProduct(product)">
          <div class="product-image">
            <img :src="product.image_url" :alt="product.name" @error="handleImageError" loading="lazy" />
            <div v-if="product.stock <= 0" class="sold-out-overlay"><span>Hết hàng</span></div>
            <span class="category-badge">{{ product.category }}</span>
          </div>
          <div class="product-info">
            <h3>{{ product.name }}</h3>
            <p class="description">{{ product.description }}</p>
            <div class="price-row">
              <span class="price">{{ formatPrice(product.price) }}</span>
              <span v-if="product.stock > 0" class="stock-badge">Còn {{ product.stock }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="products.length === 0" class="empty-state animate-fade-in">
        <div class="empty-icon">
          <svg width="56" height="56" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
        </div>
        <h3>Không có sản phẩm</h3>
        <p>Hiện tại không có sản phẩm nào</p>
      </div>
    </div>

    <!-- Product Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedProduct" class="modal-overlay">
          <div class="modal-backdrop" @click="closeModal" />
          <div class="product-modal">
            <div class="modal-hero">
              <img :src="selectedProduct.image_url" :alt="selectedProduct.name" />
              <div class="hero-gradient" />
              <button @click="closeModal" class="close-btn">
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
              <h3 class="hero-title">{{ selectedProduct.name }}</h3>
            </div>
            <div class="modal-body">
              <p class="modal-desc">{{ selectedProduct.description }}</p>
              <div class="price-display">
                <span>Thành tiền</span>
                <span class="price-big">{{ formatPrice(selectedProduct.price) }}</span>
              </div>
              <div class="modal-actions">
                <button @click="closeModal" class="btn-back">Quay lại</button>
                <button @click="proceedToPayment" :disabled="paying" class="btn-pay">
                  <svg v-if="paying" class="spin-icon" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  {{ paying ? 'Đang xử lý...' : '💳 Thanh toán ngay' }}
                </button>
              </div>
              <!-- Trust indicator -->
              <div class="modal-trust">
                <span class="trust-badge">🔒 Thanh toán an toàn qua PayOS</span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProducts } from '../api/products.js'
import { createPayment } from '../api/payments.js'

const router = useRouter()
const products = ref([])
const loading = ref(true)
const error = ref(null)
const selectedProduct = ref(null)
const isOnline = ref(true)
const paying = ref(false)
let refreshTimer = null

const availableProducts = computed(() => products.value.filter(p => p.is_available))

async function loadProducts() {
  loading.value = true; error.value = null
  try {
    const result = await getProducts()
    if (result.success) { products.value = result.products; isOnline.value = true }
    else { error.value = result.error || 'Không thể tải sản phẩm'; isOnline.value = false }
  } catch { error.value = 'Lỗi kết nối mạng'; isOnline.value = false }
  finally { loading.value = false }
}

function selectProduct(p) { if (p.stock > 0) selectedProduct.value = p }
function closeModal() { selectedProduct.value = null }

async function proceedToPayment() {
  if (!selectedProduct.value || paying.value) return
  paying.value = true
  try {
    const result = await createPayment(selectedProduct.value.id)
    if (result.success) {
      router.push({ name: 'Payment', params: { productId: selectedProduct.value.id },
        query: { orderCode: result.orderCode, checkoutUrl: result.checkoutUrl, qrCode: result.qrCode, productName: selectedProduct.value.name, price: selectedProduct.value.price }
      })
    } else { alert('Lỗi: ' + result.error) }
  } catch (e) { alert('Lỗi: ' + e.message) }
  finally { paying.value = false }
}

function formatPrice(p) { return new Intl.NumberFormat('vi-VN', { style: 'currency', currency:'VND' }).format(p) }
function handleImageError(e) { e.target.src = '/images/default-product.png' }

onMounted(() => { loadProducts(); refreshTimer = setInterval(loadProducts, 30000) })
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: var(--color-surface);
  padding: 1.5rem;
}

/* Header */
.home-header {
  max-width: 72rem;
  margin: 0 auto 2rem;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left { display: flex; align-items: center; gap: 0.75rem; }
.header-icon {
  width: 44px; height: 44px;
  background: var(--color-primary);
  border-radius: 0.75rem;
  display: flex; align-items: center; justify-content: center;
  color: white;
}
.home-header h1 { font-size: 1.5rem; color: var(--color-text); }
.home-header p { font-size: 0.875rem; color: var(--color-text-muted); }
.status-indicator { display: flex; align-items: center; gap: 0.5rem; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; }
.status-dot.online { background: var(--color-success); box-shadow: 0 0 8px var(--color-success); }
.status-dot.offline { background: var(--color-danger); }
.status-on { color: var(--color-success); font-size: 0.875rem; font-weight: 500; }
.status-off { color: var(--color-danger); font-size: 0.875rem; font-weight: 500; }

/* Skeleton Loading */
.skeleton-card {
  background: white;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.skeleton-image { aspect-ratio: 1; }
.skeleton-body { padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.skeleton-title { height: 1rem; width: 70%; }
.skeleton-desc { height: 0.75rem; width: 90%; }
.skeleton-row { display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem; }
.skeleton-price { height: 1.25rem; width: 5rem; }
.skeleton-badge { height: 1rem; width: 3rem; border-radius: 9999px; }

/* Error */
.error-state {
  text-align: center; padding: 4rem 2rem;
  max-width: 72rem; margin: 0 auto;
  background: white; border-radius: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.error-state svg { color: var(--color-danger); margin: 0 auto 1rem; display: block; }
.error-state h3 { color: var(--color-text); margin-bottom: 0.5rem; font-size: 1.25rem; }
.error-state p { color: var(--color-text-muted); margin-bottom: 1.5rem; }
.retry-btn {
  background: var(--color-primary); color: white;
  padding: 0.75rem 1.5rem; border-radius: 0.75rem;
  font-weight: 600; border: none; font-size: 1rem;
  transition: background 0.2s, transform 0.1s;
}
.retry-btn:hover { background: var(--color-primary-dark); }
.retry-btn:active { transform: scale(0.97); }

/* Products Grid */
.products-container { max-width: 72rem; margin: 0 auto; }
.products-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
@media (min-width: 768px) { .products-grid { grid-template-columns: repeat(3, 1fr); gap: 1.5rem; } }
@media (min-width: 1024px) { .products-grid { grid-template-columns: repeat(4, 1fr); } }

/* Product Card — Stagger entrance animation */
.product-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  animation: fadeInUp 0.4s ease-out both;
}
.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.12);
}
.product-card:active { transform: translateY(-2px) scale(0.99); }
.product-card.out-of-stock { opacity: 0.5; pointer-events: none; }

.product-image {
  position: relative;
  aspect-ratio: 1;
  background: var(--color-surface-alt);
  overflow: hidden;
}
.product-image img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
.product-card:hover .product-image img { transform: scale(1.05); }
.sold-out-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
}
.sold-out-overlay span { color: white; font-weight: 700; font-size: 1.125rem; }
.category-badge {
  position: absolute; top: 0.75rem; left: 0.75rem;
  background: rgba(0,0,0,0.5);
  color: white; font-size: 0.7rem;
  padding: 0.25rem 0.625rem; border-radius: 9999px;
  backdrop-filter: blur(4px);
}
.product-info { padding: 1rem; }
.product-info h3 {
  font-size: 1rem; font-weight: 600;
  color: var(--color-text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}
.description {
  font-size: 0.875rem; color: var(--color-text-muted);
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 0.75rem;
}
.price-row { display: flex; align-items: center; justify-content: space-between; }
.price {
  font-family: 'Rubik', sans-serif;
  font-weight: 700; font-size: 1.125rem;
  color: var(--color-accent);
}
.stock-badge {
  font-size: 0.7rem; font-weight: 600;
  background: oklch(0.72 0.19 145 / 0.1);
  color: var(--color-success);
  padding: 0.25rem 0.5rem; border-radius: 9999px;
}

/* Empty State */
.empty-state { text-align: center; padding: 4rem 0; }
.empty-icon {
  width: 96px; height: 96px;
  background: var(--color-surface-alt);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 1.5rem;
  color: var(--color-text-muted);
}
.empty-state h3 { color: var(--color-text); margin-bottom: 0.5rem; }
.empty-state p { color: var(--color-text-muted); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  display: flex; align-items: flex-end; justify-content: center;
}
@media (min-width: 768px) { .modal-overlay { align-items: center; } }
.modal-backdrop {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
}
.product-modal {
  position: relative; z-index: 10;
  width: 100%; max-width: 32rem;
  background: white;
  border-radius: 1.5rem 1.5rem 0 0;
  overflow: hidden;
  max-height: 85vh;
}
@media (min-width: 768px) { .product-modal { border-radius: 1.5rem; } }
.modal-hero {
  position: relative; height: 200px;
  background: var(--color-surface-alt);
  overflow: hidden;
}
.modal-hero img { width: 100%; height: 100%; object-fit: cover; }
.hero-gradient {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
}
.close-btn {
  position: absolute; top: 1rem; right: 1rem;
  width: 40px; height: 40px;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(4px);
  border-radius: 50%; border: none;
  color: white; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.close-btn:hover { background: rgba(0,0,0,0.5); }
.hero-title {
  position: absolute; bottom: 1rem; left: 1.5rem; right: 1.5rem;
  font-size: 1.5rem; color: white;
}
.modal-body { padding: 1.5rem; }
.modal-desc { color: var(--color-text-muted); margin-bottom: 1rem; }
.price-display {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem; background: var(--color-surface-alt);
  border-radius: 0.75rem; margin-bottom: 1.5rem;
}
.price-display span:first-child { color: var(--color-text-muted); font-weight: 500; }
.price-big {
  font-family: 'Rubik', sans-serif;
  font-size: 1.75rem; font-weight: 700;
  color: var(--color-accent);
}

/* CTA — Von Restorff: visually distinct */
.modal-actions { display: flex; gap: 0.75rem; }
.btn-back {
  flex: 1; padding: 0.875rem;
  background: var(--color-surface-alt);
  color: var(--color-text);
  border: none; border-radius: 0.75rem;
  font-weight: 600; font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}
.btn-back:hover { background: oklch(0.90 0.005 90); }
.btn-back:active { transform: scale(0.97); }
.btn-pay {
  flex: 2; padding: 0.875rem;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white; border: none;
  border-radius: 0.75rem;
  font-weight: 700; font-size: 1.0625rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  transition: box-shadow 0.2s, transform 0.1s;
  box-shadow: 0 4px 16px oklch(0.65 0.14 180 / 0.3);
}
.btn-pay:hover { box-shadow: 0 6px 24px oklch(0.65 0.14 180 / 0.45); }
.btn-pay:active { transform: scale(0.97); }
.btn-pay:disabled { opacity: 0.5; box-shadow: none; }
.spin-icon { width: 20px; height: 20px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Trust indicator */
.modal-trust { text-align: center; margin-top: 1rem; }

/* Modal animation */
.modal-enter-active, .modal-leave-active { transition: opacity 0.25s; }
.modal-enter-active > div:last-child, .modal-leave-active > div:last-child { transition: transform 0.25s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from > div:last-child { transform: translateY(100%); }
.modal-leave-to > div:last-child { transform: translateY(100%); }
@media (min-width: 768px) {
  .modal-enter-from > div:last-child { transform: scale(0.95) translateY(20px); }
  .modal-leave-to > div:last-child { transform: scale(0.95) translateY(20px); }
}
</style>