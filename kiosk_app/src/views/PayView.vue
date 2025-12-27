<template>
  <div class="pay-view">
    <!-- Header -->
    <header class="header">
      <button @click="goBack" class="back-btn">← Quay lại</button>
      <h1 class="title">💳 Thanh toán</h1>
      <div class="timer" v-if="timeLeft > 0">
        ⏰ {{ formatTime(timeLeft) }}
      </div>
    </header>

    <!-- Product Info -->
    <div class="product-section" v-if="product">
      <div class="product-card">
        <img 
          :src="product.image_url || '/images/default-product.png'" 
          :alt="product.name"
          class="product-image"
        />
        <div class="product-info">
          <h2>{{ product.name }}</h2>
          <p>{{ product.description }}</p>
          <div class="price">{{ formatPrice(product.price) }}</div>
        </div>
      </div>
    </div>

    <!-- Payment Status -->
    <div class="payment-section">
      <!-- Loading State -->
      <div v-if="paymentStatus === 'creating'" class="status-card loading">
        <div class="spinner"></div>
        <h3>Đang tạo thanh toán...</h3>
        <p>Vui lòng đợi trong giây lát</p>
      </div>

      <!-- QR Code Display -->
      <div v-else-if="paymentStatus === 'pending'" class="status-card qr-display">
        <h3>📱 Quét mã QR để thanh toán</h3>
        
        <!-- QR Code Component -->
        <div class="qr-container">
          <Qrcode 
            v-if="checkoutUrl" 
            :value="checkoutUrl" 
            :size="250"
            class="qr-code"
          />
          <div v-else class="qr-placeholder">
            <div class="spinner"></div>
            <p>Đang tạo mã QR...</p>
          </div>
        </div>

        <div class="payment-info">
          <p class="order-code">Mã đơn hàng: <strong>{{ orderCode }}</strong></p>
          <p class="amount">Số tiền: <strong>{{ formatPrice(product?.price || 0) }}</strong></p>
          
          <!-- Manual Payment Link -->
          <div class="manual-payment" v-if="checkoutUrl">
            <p>Hoặc nhấn vào link bên dưới:</p>
            <a :href="checkoutUrl" target="_blank" class="payment-link">
              🔗 Mở trang thanh toán
            </a>
          </div>
        </div>

        <div class="payment-status">
          <div class="status-indicator checking"></div>
          <span>Đang chờ thanh toán...</span>
        </div>
      </div>

      <!-- Success State -->
      <div v-else-if="paymentStatus === 'paid'" class="status-card success">
        <div class="success-icon">✅</div>
        <h3>Thanh toán thành công!</h3>
        <p>Đang chuẩn bị xuất hàng...</p>
        <div class="dispensing-animation">
          <div class="product-drop"></div>
        </div>
      </div>

      <!-- Dispensed State -->
      <div v-else-if="paymentStatus === 'dispensed'" class="status-card dispensed">
        <div class="success-icon">🎉</div>
        <h3>Hoàn tất!</h3>
        <p>Sản phẩm đã được xuất. Cảm ơn bạn đã sử dụng dịch vụ!</p>
        <button @click="goHome" class="home-btn">🏠 Về trang chủ</button>
      </div>

      <!-- Error State -->
      <div v-else-if="paymentStatus === 'error'" class="status-card error">
        <div class="error-icon">❌</div>
        <h3>Có lỗi xảy ra</h3>
        <p>{{ errorMessage }}</p>
        <div class="error-actions">
          <button @click="retryPayment" class="retry-btn">🔄 Thử lại</button>
          <button @click="goBack" class="cancel-btn">← Quay lại</button>
        </div>
      </div>

      <!-- Timeout State -->
      <div v-else-if="paymentStatus === 'timeout'" class="status-card timeout">
        <div class="timeout-icon">⏰</div>
        <h3>Hết thời gian thanh toán</h3>
        <p>Phiên thanh toán đã hết hạn. Vui lòng thử lại.</p>
        <button @click="goBack" class="back-btn-large">← Chọn sản phẩm khác</button>
      </div>
    </div>

    <!-- Instructions -->
    <div class="instructions" v-if="paymentStatus === 'pending'">
      <h4>📋 Hướng dẫn thanh toán:</h4>
      <ol>
        <li>Mở ứng dụng ngân hàng trên điện thoại</li>
        <li>Chọn chức năng quét mã QR</li>
        <li>Quét mã QR hiển thị trên màn hình</li>
        <li>Xác nhận thanh toán trong ứng dụng</li>
        <li>Chờ hệ thống xử lý và xuất hàng</li>
      </ol>
    </div>
  </div>
</template>

<script>
import Qrcode from '../components/Qrcode.vue';
import { getProductById, createPayment, getOrderStatus } from '../api/products.js';

export default {
  name: 'PayView',
  components: {
    Qrcode
  },
  data() {
    return {
      product: null,
      paymentStatus: 'creating', // creating, pending, paid, dispensed, error, timeout
      orderCode: null,
      checkoutUrl: null,
      qrUrl: null,
      errorMessage: '',
      timeLeft: 300, // 5 minutes in seconds
      statusCheckInterval: null,
      timerInterval: null,
      machineId: 'KIOSK_001'
    };
  },
  async mounted() {
    await this.initializePayment();
  },
  beforeUnmount() {
    this.clearIntervals();
  },
  methods: {
    async initializePayment() {
      try {
        // Get product data from route params/query
        const productId = this.$route.params.productId;
        const productQuery = this.$route.query.product;
        
        if (productQuery) {
          // Use product data from query (passed from HomeView)
          this.product = JSON.parse(productQuery);
        } else if (productId) {
          // Fetch product data from API
          const result = await getProductById(productId);
          if (result.success) {
            this.product = result.product;
          } else {
            throw new Error('Không thể tải thông tin sản phẩm');
          }
        } else {
          throw new Error('Không có thông tin sản phẩm');
        }

        // Create payment
        await this.createPaymentRequest();
        
      } catch (error) {
        console.error('Initialize payment error:', error);
        this.paymentStatus = 'error';
        this.errorMessage = error.message;
      }
    },

    async createPaymentRequest() {
      try {
        this.paymentStatus = 'creating';
        
        const result = await createPayment(
          this.machineId,
          this.product.id,
          this.product.price
        );

        if (result.success) {
          this.orderCode = result.orderCode;
          this.checkoutUrl = result.checkoutUrl;
          this.qrUrl = result.qrUrl;
          this.paymentStatus = 'pending';
          
          // Start checking payment status
          this.startStatusCheck();
          this.startTimer();
          
        } else {
          throw new Error(result.error || 'Không thể tạo thanh toán');
        }
      } catch (error) {
        console.error('Create payment error:', error);
        this.paymentStatus = 'error';
        this.errorMessage = error.message;
      }
    },

    startStatusCheck() {
      this.statusCheckInterval = setInterval(async () => {
        try {
          const result = await getOrderStatus(this.orderCode);
          
          if (result.success) {
            const status = result.status;
            
            if (status === 'PAID') {
              this.paymentStatus = 'paid';
              this.clearIntervals();
              
              // Simulate dispensing after 3 seconds
              setTimeout(() => {
                this.paymentStatus = 'dispensed';
              }, 3000);
              
            } else if (status === 'CANCELLED') {
              this.paymentStatus = 'error';
              this.errorMessage = 'Thanh toán đã bị hủy';
              this.clearIntervals();
            }
          }
        } catch (error) {
          console.error('Status check error:', error);
          // Continue checking, don't show error for network issues
        }
      }, 3000); // Check every 3 seconds
    },

    startTimer() {
      this.timerInterval = setInterval(() => {
        this.timeLeft--;
        
        if (this.timeLeft <= 0) {
          this.paymentStatus = 'timeout';
          this.clearIntervals();
        }
      }, 1000);
    },

    clearIntervals() {
      if (this.statusCheckInterval) {
        clearInterval(this.statusCheckInterval);
        this.statusCheckInterval = null;
      }
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
    },

    async retryPayment() {
      this.timeLeft = 300; // Reset timer
      await this.createPaymentRequest();
    },

    goBack() {
      this.clearIntervals();
      this.$router.go(-1);
    },

    goHome() {
      this.clearIntervals();
      this.$router.push('/');
    },

    formatPrice(price) {
      return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
      }).format(price);
    },

    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
  }
};
</script>

<style scoped>
.pay-view {
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

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s;
}

.back-btn:hover {
  background: #5a6268;
}

.title {
  font-size: 2.5rem;
  color: #333;
  margin: 0;
  font-weight: bold;
}

.timer {
  background: #e74c3c;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 1.1rem;
}

.product-section {
  margin-bottom: 30px;
}

.product-card {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 30px;
}

.product-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 15px;
}

.product-info h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 2rem;
}

.product-info p {
  margin: 0 0 15px 0;
  color: #666;
  font-size: 1.1rem;
}

.price {
  font-size: 2rem;
  font-weight: bold;
  color: #e74c3c;
}

.payment-section {
  margin-bottom: 30px;
}

.status-card {
  background: white;
  border-radius: 15px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  text-align: center;
}

.status-card h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.8rem;
}

.status-card p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 1.1rem;
}

/* Loading State */
.loading .spinner {
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

/* QR Display */
.qr-container {
  margin: 30px 0;
  display: flex;
  justify-content: center;
}

.qr-code {
  border: 10px solid #f8f9fa;
  border-radius: 15px;
}

.qr-placeholder {
  width: 250px;
  height: 250px;
  border: 2px dashed #ddd;
  border-radius: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
}

.payment-info {
  margin: 30px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}

.order-code, .amount {
  margin: 10px 0;
  font-size: 1.1rem;
}

.manual-payment {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ddd;
}

.payment-link {
  display: inline-block;
  background: #667eea;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
  transition: background 0.3s;
}

.payment-link:hover {
  background: #5a6fd8;
}

.payment-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
  font-size: 1.1rem;
  color: #666;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.checking {
  background: #ffc107;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* Success State */
.success-icon, .error-icon, .timeout-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.dispensing-animation {
  margin: 30px 0;
  height: 100px;
  position: relative;
  overflow: hidden;
}

.product-drop {
  width: 40px;
  height: 40px;
  background: #28a745;
  border-radius: 50%;
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  animation: drop 2s ease-in infinite;
}

@keyframes drop {
  0% { top: -40px; }
  100% { top: 100px; }
}

/* Button Styles */
.home-btn, .retry-btn, .cancel-btn, .back-btn-large {
  padding: 15px 30px;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.3s;
  margin: 10px;
}

.home-btn {
  background: #28a745;
  color: white;
}

.home-btn:hover {
  background: #218838;
}

.retry-btn {
  background: #667eea;
  color: white;
}

.retry-btn:hover {
  background: #5a6fd8;
}

.cancel-btn, .back-btn-large {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover, .back-btn-large:hover {
  background: #5a6268;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

/* Instructions */
.instructions {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.instructions h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 1.5rem;
}

.instructions ol {
  text-align: left;
  color: #666;
  font-size: 1.1rem;
  line-height: 1.6;
}

.instructions li {
  margin-bottom: 10px;
}

/* Responsive */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 15px;
  }

  .title {
    font-size: 2rem;
  }

  .product-card {
    flex-direction: column;
    text-align: center;
  }

  .product-image {
    width: 100px;
    height: 100px;
  }

  .qr-code {
    width: 200px !important;
    height: 200px !important;
  }

  .error-actions {
    flex-direction: column;
  }
}
</style>