<template>
  <div class="home-view">
    <!-- Header -->
    <header class="header">
      <h1 class="title">🏪 Máy Bán Hàng Tự Động</h1>
      <div class="status">
        <span class="status-indicator" :class="{ online: isOnline }"></span>
        <span>{{ isOnline ? 'Đang hoạt động' : 'Offline' }}</span>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Đang tải sản phẩm...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error">
      <h3>❌ Lỗi tải dữ liệu</h3>
      <p>{{ error }}</p>
      <button @click="loadProducts" class="retry-btn">🔄 Thử lại</button>
    </div>

    <!-- Products Grid -->
    <div v-else class="products-container">
      <div class="products-header">
        <h2>📦 Chọn sản phẩm</h2>
        <button @click="loadProducts" class="refresh-btn">🔄 Làm mới</button>
      </div>

      <div class="products-grid">
        <div 
          v-for="product in availableProducts" 
          :key="product.id"
          class="product-card"
          :class="{ 'out-of-stock': product.stock <= 0 }"
          @click="selectProduct(product)"
        >
          <!-- Product Image -->
          <div class="product-image">
            <img 
              :src="product.image_url || '/images/default-product.png'" 
              :alt="product.name"
              @error="handleImageError"
            />
            <div v-if="product.stock <= 0" class="out-of-stock-overlay">
              <span>Hết hàng</span>
            </div>
          </div>

          <!-- Product Info -->
          <div class="product-info">
            <h3 class="product-name">{{ product.name }}</h3>
            <p class="product-description">{{ product.description }}</p>
            <div class="product-details">
              <span class="product-price">{{ formatPrice(product.price) }}</span>
              <span class="product-stock">Còn: {{ product.stock }}</span>
            </div>
            <div class="product-category">{{ product.category }}</div>
          </div>

          <!-- Select Button -->
          <button 
            class="select-btn"
            :disabled="product.stock <= 0"
            @click.stop="selectProduct(product)"
          >
            {{ product.stock > 0 ? '🛒 Chọn mua' : '❌ Hết hàng' }}
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="products.length === 0 && !loading" class="empty-state">
        <h3>📭 Không có sản phẩm</h3>
        <p>Hiện tại không có sản phẩm nào có sẵn</p>
      </div>
    </div>

    <!-- Product Selection Modal -->
    <div v-if="selectedProduct" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Xác nhận mua hàng</h3>
          <button @click="closeModal" class="close-btn">✕</button>
        </div>
        
        <div class="modal-content">
          <div class="selected-product">
            <img 
              :src="selectedProduct.image_url || '/images/default-product.png'" 
              :alt="selectedProduct.name"
            />
            <div class="product-details">
              <h4>{{ selectedProduct.name }}</h4>
              <p>{{ selectedProduct.description }}</p>
              <div class="price">{{ formatPrice(selectedProduct.price) }}</div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="closeModal" class="cancel-btn">Hủy</button>
          <button @click="proceedToPayment" class="confirm-btn">
            💳 Thanh toán {{ formatPrice(selectedProduct.price) }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getProducts } from '../api/products.js';

export default {
  name: 'HomeView',
  data() {
    return {
      products: [],
      loading: true,
      error: null,
      selectedProduct: null,
      isOnline: true,
      refreshInterval: null
    };
  },
  computed: {
    availableProducts() {
      return this.products.filter(product => product.is_available);
    }
  },
  async mounted() {
    await this.loadProducts();
    this.startAutoRefresh();
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },
  methods: {
    async loadProducts() {
      this.loading = true;
      this.error = null;
      
      try {
        const result = await getProducts();
        
        if (result.success) {
          this.products = result.products;
          this.isOnline = true;
          console.log(`Loaded ${result.products.length} products`);
        } else {
          this.error = result.error || 'Không thể tải sản phẩm';
          this.isOnline = false;
        }
      } catch (error) {
        this.error = 'Lỗi kết nối mạng';
        this.isOnline = false;
        console.error('Load products error:', error);
      } finally {
        this.loading = false;
      }
    },

    selectProduct(product) {
      if (product.stock <= 0) return;
      this.selectedProduct = product;
    },

    closeModal() {
      this.selectedProduct = null;
    },

    async proceedToPayment() {
      if (!this.selectedProduct) return;
      
      // Navigate to payment view with product data
      this.$router.push({
        name: 'PayView',
        params: {
          productId: this.selectedProduct.id
        },
        query: {
          product: JSON.stringify(this.selectedProduct)
        }
      });
    },

    formatPrice(price) {
      return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
      }).format(price);
    },

    handleImageError(event) {
      event.target.src = '/images/default-product.png';
    },

    startAutoRefresh() {
      // Refresh products every 30 seconds
      this.refreshInterval = setInterval(() => {
        this.loadProducts();
      }, 30000);
    }
  }
};
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 30px;
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.title {
  font-size: 2.5rem;
  color: #333;
  margin: 0;
  font-weight: bold;
}

.status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  color: #666;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #dc3545;
  animation: pulse 2s infinite;
}

.status-indicator.online {
  background: #28a745;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.loading, .error {
  text-align: center;
  background: white;
  padding: 60px 40px;
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn, .refresh-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s;
}

.retry-btn:hover, .refresh-btn:hover {
  background: #5a6fd8;
}

.products-container {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.products-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.products-header h2 {
  color: #333;
  margin: 0;
  font-size: 2rem;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
}

.product-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  border-color: #667eea;
}

.product-card.out-of-stock {
  opacity: 0.6;
  cursor: not-allowed;
}

.product-image {
  position: relative;
  height: 200px;
  background: white;
  border-radius: 10px;
  margin-bottom: 15px;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.out-of-stock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
}

.product-info {
  margin-bottom: 15px;
}

.product-name {
  font-size: 1.4rem;
  color: #333;
  margin: 0 0 8px 0;
  font-weight: bold;
}

.product-description {
  color: #666;
  margin: 0 0 12px 0;
  font-size: 0.95rem;
}

.product-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.product-price {
  font-size: 1.3rem;
  font-weight: bold;
  color: #e74c3c;
}

.product-stock {
  background: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85rem;
}

.product-category {
  background: #6c757d;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  display: inline-block;
}

.select-btn {
  width: 100%;
  padding: 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.select-btn:hover:not(:disabled) {
  background: #218838;
}

.select-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.modal-content {
  padding: 30px;
}

.selected-product {
  display: flex;
  gap: 20px;
  align-items: center;
}

.selected-product img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 10px;
}

.selected-product .product-details h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.selected-product .product-details p {
  margin: 0 0 12px 0;
  color: #666;
}

.selected-product .price {
  font-size: 1.5rem;
  font-weight: bold;
  color: #e74c3c;
}

.modal-actions {
  display: flex;
  gap: 15px;
  padding: 20px 30px;
  border-top: 1px solid #eee;
}

.cancel-btn, .confirm-btn {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
}

.confirm-btn {
  background: #28a745;
  color: white;
}

.confirm-btn:hover {
  background: #218838;
}

/* Responsive */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .title {
    font-size: 2rem;
  }

  .products-grid {
    grid-template-columns: 1fr;
  }

  .selected-product {
    flex-direction: column;
    text-align: center;
  }

  .modal-actions {
    flex-direction: column;
  }
}
</style>