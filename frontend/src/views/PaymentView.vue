<template>
  <div class="payment-page">
    <div class="payment-card">
      <!-- Header -->
      <div class="payment-header">
        <h1>Thanh toán</h1>
        <p>{{ productName }}</p>
      </div>

      <!-- Price -->
      <div class="price-section">
        <p class="label">Số tiền</p>
        <p class="amount">{{ formatPrice(price) }}</p>
      </div>

      <!-- QR & Checkout -->
      <div class="qr-section" v-if="checkoutUrl">
        <!-- Countdown -->
        <div class="countdown" :class="{ urgent: timeLeft <= 60 }">
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span>{{ formatTime(timeLeft) }}</span>
        </div>

        <!-- QR Code -->
        <div class="qr-frame">
          <canvas ref="qrCanvas"></canvas>
        </div>

        <p class="qr-hint">Quét mã QR hoặc nhấn nút bên dưới để thanh toán</p>

        <div class="trust-section">
          <span class="trust-badge">🔒 Thanh toán an toàn qua PayOS</span>
        </div>

        <a :href="checkoutUrl" target="_blank" class="pay-btn">
          Mở trang thanh toán PayOS
        </a>
      </div>

      <!-- Loading -->
      <div v-else class="loading-section">
        <div class="spinner" />
        <p>Đang khởi tạo giao dịch an toàn...</p>
      </div>

      <!-- Status -->
      <div class="status-bar">
        <span class="pulse-dot" />
        <span>{{ statusMessage }}</span>
      </div>

      <!-- Cancel -->
      <div class="cancel-section">
        <button @click="cancelAndGoBack" class="cancel-btn">Hủy thanh toán</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrderStatus, cancelOrder } from '../api/payments.js'
import QRCode from 'qrcode'

const route = useRoute()
const router = useRouter()

const productName = ref(route.query.productName || 'Sản phẩm')
const price = ref(Number(route.query.price) || 0)
const orderCode = ref(route.query.orderCode || '')
const checkoutUrl = ref(route.query.checkoutUrl || '')
const qrCodeData = ref(route.query.qrCode || '')  // VietQR EMVCo string from PayOS
const timeLeft = ref(300)
const statusMessage = ref('Đang chờ thanh toán...')
const qrCanvas = ref(null)

let countdownTimer = null
let pollingTimer = null

// Generate QR image from PayOS VietQR data string
async function generateQR() {
  await nextTick()
  if (qrCanvas.value) {
    // Use PayOS QR data (VietQR EMVCo format) — this is the actual bank transfer QR
    // Falls back to checkoutUrl if PayOS didn't return qrCode
    const qrContent = qrCodeData.value || checkoutUrl.value
    if (qrContent) {
      try {
        await QRCode.toCanvas(qrCanvas.value, qrContent, {
          width: 240,
          margin: 2,
          color: { dark: '#1a1a2e', light: '#ffffff' }
        })
      } catch (err) {
        console.error('QR generation failed:', err)
      }
    }
  }
}

function formatPrice(val) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val)
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function startCountdown() {
  countdownTimer = setInterval(async () => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      clearInterval(countdownTimer)
      statusMessage.value = 'Hết thời gian thanh toán'
      if (orderCode.value) {
        await cancelOrder(orderCode.value)
      }
      router.push({ name: 'Cancel' })
    }
  }, 1000)
}

const isComplete = ref(false)

async function pollPaymentStatus() {
  if (!orderCode.value) return
  try {
    const result = await getOrderStatus(orderCode.value)
    if (result.success) {
      if (result.status === 'PAID' || result.status === 'paid') {
        isComplete.value = true
        statusMessage.value = 'Thanh toán thành công!'
        cleanup()
        router.push({ name: 'Success', query: { orderCode: orderCode.value, productName: productName.value } })
      } else if (result.status === 'CANCELLED' || result.status === 'cancelled' || result.status === 'EXPIRED') {
        isComplete.value = true
        statusMessage.value = 'Đơn hàng đã bị hủy hoặc hết hạn'
        cleanup()
        router.push({ name: 'Cancel' })
      }
    }
  } catch {}
}

function startPolling() {
  pollingTimer = setInterval(pollPaymentStatus, 3000)
}

function cleanup() {
  if (countdownTimer) clearInterval(countdownTimer)
  if (pollingTimer) clearInterval(pollingTimer)
}

async function cancelAndGoBack() {
  isComplete.value = true
  cleanup()
  if (orderCode.value) {
    await cancelOrder(orderCode.value)
  }
  router.push({ name: 'Home' })
}

onMounted(() => {
  generateQR()
  startCountdown()
  startPolling()
})

onUnmounted(() => {
  cleanup()
  // Nếu rời trang mà chưa hoàn thành (chưa Paid/Cancel/Hết giờ), tự động hủy
  if (!isComplete.value && orderCode.value) {
    cancelOrder(orderCode.value)
  }
})
</script>

<style scoped>
.payment-page {
  min-height: 100vh;
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.payment-card {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  overflow: hidden;
}
.payment-header {
  background: var(--color-primary);
  padding: 1.5rem;
  text-align: center;
}
.payment-header h1 {
  font-size: 1.5rem;
  color: white;
}
.payment-header p {
  color: rgba(255,255,255,0.8);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
.price-section {
  padding: 1.5rem;
  text-align: center;
  border-bottom: 1px solid var(--color-surface-alt);
}
.price-section .label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}
.price-section .amount {
  font-family: 'Rubik', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-accent);
}
.qr-section {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.countdown {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-family: 'Rubik', sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
}
.countdown svg { color: var(--color-warning); }
.countdown.urgent { color: var(--color-danger); }
.countdown.urgent svg { color: var(--color-danger); }

.qr-frame {
  background: white;
  padding: 1rem;
  border: 2px solid var(--color-surface-alt);
  border-radius: 1rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.qr-frame canvas {
  display: block;
  max-width: 100%;
  height: auto;
}
.qr-hint {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1rem;
}
.pay-btn {
  display: block;
  width: 100%;
  padding: 1rem;
  background: var(--color-primary);
  color: white;
  text-align: center;
  text-decoration: none;
  border-radius: 0.75rem;
  font-weight: 600;
  font-size: 1rem;
  transition: background 0.2s;
}
.pay-btn:hover { background: var(--color-primary-dark); }

/* Trust Section */
.trust-section {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}
.trust-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: oklch(0.72 0.19 145 / 0.1);
  border-radius: 9999px;
  color: var(--color-success);
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid oklch(0.72 0.19 145 / 0.2);
}

/* Loading Section */
.loading-section {
  padding: 3rem 1.5rem;
  text-align: center;
}
.spinner {
  width: 48px; height: 48px;
  border: 4px solid var(--color-surface-alt);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.5rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-section p { color: var(--color-text-muted); font-size: 0.9375rem; }

/* Status Bar */
.status-bar {
  padding: 1rem;
  margin: 0 1.5rem 1rem;
  background: var(--color-surface-alt);
  border-radius: 0.75rem;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
}
.pulse-dot {
  width: 8px; height: 8px;
  background: var(--color-info);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
.status-bar span:last-child { color: var(--color-text-muted); font-size: 0.875rem; font-weight: 500; }

/* Cancel Section */
.cancel-section {
  padding: 0 1.5rem 1.5rem;
}
.cancel-btn {
  width: 100%;
  padding: 0.875rem;
  background: none;
  border: none;
  border-radius: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: all 0.2s;
}
.cancel-btn:hover {
  background: rgba(239, 68, 68, 0.05);
  color: var(--color-danger);
}
.cancel-btn:active { transform: scale(0.97); }

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  .spinner, .pulse-dot, .cancel-btn {
    animation: none !important;
    transition: none !important;
  }
}</style>