```
<template>
  <div class="home-page pb-12">
    <!-- Component Header: Tiêu đề và Trạng thái -->
    <Header 
      :is-online="isOnline" 
      @admin-click="router.push('/admin/products')" 
    />

    <main class="products-container px-4 sm:px-0">
      <!-- Skeleton Loading: Hiệu ứng chờ khi đang tải dữ liệu -->
      <div v-if="loading" class="products-grid">
        <div v-for="n in 8" :key="n" class="skeleton h-64 rounded-2xl shadow-sm" />
      </div>

      <!-- Trạng thái Lỗi kết nối -->
      <div v-else-if="error" class="error-state animate-fade-in-up py-16 text-center bg-white rounded-3xl shadow-sm border border-slate-100">
        <div class="w-16 h-16 bg-rose-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-slate-800 mb-2">Không thể kết nối máy bán hàng</h3>
        <p class="text-slate-500 mb-8">{{ error }}</p>
        <button @click="loadProducts" class="px-8 py-3 bg-primary text-white font-bold rounded-xl shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all">
          🔄 Thử kết nối lại
        </button>
      </div>

      <!-- Danh sách Sản phẩm -->
      <div v-else>
        <div v-if="availableProducts.length > 0" class="products-grid">
          <!-- Component ProductCard: Thẻ sản phẩm riêng lẻ -->
          <ProductCard 
            v-for="(product, index) in availableProducts" 
            :key="product.id"
            :product="product"
            :style="{ animationDelay: (index * 50) + 'ms' }"
            @select="selectProduct"
          />
        </div>

        <!-- Trạng thái Trống (Không có sản phẩm) -->
        <div v-else class="empty-state py-24 text-center">
          <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-300">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
            </svg>
          </div>
          <h3 class="text-lg font-bold text-slate-400">Danh mục sản phẩm đang trống</h3>
          <p class="text-slate-400 text-sm">Vui lòng quay lại sau ít phút</p>
        </div>
      </div>
    </main>

    <!-- Component ProductModal: Chi tiết và Thanh toán -->
    <ProductModal 
      :product="selectedProduct"
      :is-online="isOnline"
      :paying="paying"
      @close="closeModal"
      @pay="proceedToPayment"
    />
  </div>
</template>

<script setup>
/**
 * HomeView - Trang chính của ứng dụng Kiosk/Web
 * Áp dụng: Vue 3 Composition API, Clean Code (Tách component), UI/UX Pro Max.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProducts } from '../api/products.js'
import { createPayment } from '../api/payments.js'

// Import các component đã tách nhỏ
import Header from '../components/common/Header.vue'
import ProductCard from '../components/product/ProductCard.vue'
import ProductModal from '../components/product/ProductModal.vue'

// -- Khai báo State --
const router = useRouter()
const products = ref([])
const loading = ref(true)
const error = ref(null)
const selectedProduct = ref(null)
const isOnline = ref(true)
const paying = ref(false)
let refreshTimer = null

// -- Computed (Dữ liệu tính toán) --
// Chỉ hiển thị các sản phẩm được đánh dấu là 'is_available'
const availableProducts = computed(() => products.value.filter(p => p.is_available))

// -- Phương thức xử lý API --

/**
 * Tải danh sách sản phẩm từ máy chủ
 * Tự động xác định trạng thái Online/Offline của hệ thống
 */
async function loadProducts() {
  // Không đặt loading = true khi cập nhật nền để tránh nhấp nháy UI
  if (products.value.length === 0) loading.value = true
  error.value = null
  
  try {
    const result = await getProducts()
    if (result.success) { 
      products.value = result.products
      isOnline.value = true 
    } else { 
      error.value = result.error || 'Lỗi dữ liệu từ máy bán hàng'
      isOnline.value = false 
    }
  } catch { 
    error.value = 'Hệ thống đang gặp lỗi kết nối. Vui lòng kiểm tra lại mạng.'
    isOnline.value = false 
  } finally { 
    loading.value = false 
  }
}

/**
 * Xử lý khi người dùng chọn sản phẩm
 */
function selectProduct(p) { 
  if (p.stock > 0) selectedProduct.value = p 
}

function closeModal() { 
  selectedProduct.value = null 
}

/**
 * Tiến hành quy trình thanh toán qua PayOS
 */
async function proceedToPayment() {
  if (!selectedProduct.value || paying.value) return
  paying.value = true
  
  try {
    const result = await createPayment(selectedProduct.value.id)
    if (result.success) {
      // Chuyển hướng sang trang quét mã QR thanh toán
      router.push({ 
        name: 'Payment', 
        params: { productId: selectedProduct.value.id },
        query: { 
          orderCode: result.orderCode, 
          checkoutUrl: result.checkoutUrl, 
          qrCode: result.qrCode, 
          productName: selectedProduct.value.name, 
          price: selectedProduct.value.price 
        }
      })
    } else { 
      // Thông báo lỗi cho người dùng bằng Tiếng Việt
      alert('Không thể tạo đơn hàng: ' + (result.error || 'Lỗi không xác định')) 
    }
  } catch (e) { 
    alert('Lỗi hệ thống: ' + e.message) 
  } finally { 
    paying.value = false 
  }
}

// -- Vòng đời Component --
onMounted(() => { 
  loadProducts()
  // Tự động làm mới dữ liệu mỗi 30 giây để cập nhật tồn kho thời gian thực
  refreshTimer = setInterval(loadProducts, 30000) 
})

onUnmounted(() => { 
  if (refreshTimer) clearInterval(refreshTimer) 
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background-color: var(--color-surface);
  padding: 1.5rem 0;
}

.products-container {
  max-width: 72rem;
  margin: 0 auto;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (min-width: 768px) { 
  .products-grid { 
    grid-template-columns: repeat(3, 1fr); 
    gap: 1.5rem; 
  } 
}

@media (min-width: 1024px) { 
  .products-grid { 
    grid-template-columns: repeat(4, 1fr); 
  } 
}

/* Hiệu ứng mượt mà cho transition từ router-view */
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
