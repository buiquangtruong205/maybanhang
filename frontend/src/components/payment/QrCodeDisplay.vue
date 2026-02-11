<template>
  <div class="qr-container-fixed">
    <!-- Dòng chẩn đoán: Nếu hiện dòng này nghĩa là dữ liệu đã đến Kiosk -->
    <div class="qr-diagnostic" v-if="value && !hasError">
      <span class="status-dot"></span>
      <span>Đã kết nối dữ liệu thanh toán</span>
    </div>

    <div class="qr-main-box">
      <!-- Ảnh QR chính - Tự động đổi nguồn nếu lỗi -->
      <img 
        v-if="value && !hasError"
        :src="currentQrUrl" 
        class="qr-actual-image"
        @error="handleImageError"
        @load="handleImageLoad"
      />
      
      <!-- Hiển thị khi đang tải hoặc lỗi -->
      <div v-if="!isLoaded || hasError" class="qr-status-box">
        <div v-if="loading && !hasError" class="loader-container">
          <div class="simple-spinner"></div>
          <p>Đang tải mã QR...</p>
        </div>
        
        <div v-if="hasError" class="error-container">
          <div class="error-icon">⚠️</div>
          <p class="error-text">Lỗi kết nối mạng</p>
          <p class="error-sub">Không thể tải ảnh từ máy chủ QR</p>
          <button @click="retryWithNextSource" class="retry-btn">
            🔄 Thử nguồn khác ({{ retryCount + 1 }}/3)
          </button>
        </div>
      </div>
    </div>

    <!-- Thông tin cứu cánh -->
    <div class="qr-footer-info" v-if="value">
      <div class="vietqr-preview">
        <code>{{ value.substring(0, 15) }}...{{ value.substring(value.length - 10) }}</code>
      </div>
      <p class="hint-text">Dùng App Ngân hàng quét mã phía trên</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Qrcode',
  props: ['value', 'orderCode'],
  data() {
    return {
      isLoaded: false,
      hasError: false,
      loading: true,
      retryCount: 0,
      // Danh sách các máy chủ QR khác nhau để dự phòng
      sources: [
        (val) => `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(val)}`,
        (val) => `https://quickchart.io/qr?text=${encodeURIComponent(val)}&size=250`,
        (val) => `https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl=${encodeURIComponent(val)}`
      ]
    }
  },
  computed: {
    currentQrUrl() {
      if (!this.value) return '';
      return this.sources[this.retryCount % this.sources.length](this.value);
    }
  },
  watch: {
    value() {
      this.resetState();
    }
  },
  methods: {
    handleImageLoad() {
      this.isLoaded = true;
      this.loading = false;
      this.hasError = false;
    },
    handleImageError() {
      console.error(`Vending Machine: QR Source #${this.retryCount} failed.`);
      if (this.retryCount < this.sources.length - 1) {
        this.retryCount++;
      } else {
        this.hasError = true;
        this.loading = false;
      }
    },
    retryWithNextSource() {
      this.retryCount = (this.retryCount + 1) % this.sources.length;
      this.hasError = false;
      this.loading = true;
      this.isLoaded = false;
    },
    resetState() {
      this.retryCount = 0;
      this.isLoaded = false;
      this.hasError = false;
      this.loading = true;
    }
  }
}
</script>

<style scoped>
.qr-container-fixed {
  width: 100%;
  max-width: 320px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #ffffff;
  border: 2px solid #e0e6ed;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

.qr-diagnostic {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #2ecc71;
  margin-bottom: 15px;
  background: #f0fff4;
  padding: 5px 12px;
  border-radius: 20px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #2ecc71;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(46, 204, 113, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
}

.qr-main-box {
  width: 250px;
  height: 250px;
  background: #f8fafc;
  border: 1px solid #edf2f7;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
}

.qr-actual-image {
  width: 90%;
  height: 90%;
  object-fit: contain;
}

.qr-status-box {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8fafc;
  padding: 20px;
  text-align: center;
}

.error-container {
  color: #e74c3c;
}

.error-icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.error-text {
  font-weight: bold;
  margin-bottom: 4px;
}

.error-sub {
  font-size: 0.8rem;
  color: #7f8c8d;
  margin-bottom: 15px;
}

.retry-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #5a6fd8;
  transform: translateY(-1px);
}

.simple-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.qr-footer-info {
  margin-top: 15px;
  text-align: center;
}

.vietqr-preview {
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 8px;
}

.hint-text {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.9rem;
}
</style>
