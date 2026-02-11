<template>
  <div class="success-page">
    <div class="success-card animate-fade-in-up">
      <!-- Success Icon -->
      <div class="icon-circle success animate-bounce-once">
        <svg width="56" height="56" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <h1>Thanh toán thành công!</h1>
      <p class="product-name">{{ productName }}</p>
      <p class="order-code">Mã đơn: <strong>{{ orderCode }}</strong></p>

      <div class="dispense-card">
        <p>Vui lòng chờ máy nhả sản phẩm</p>
        <div class="spinner" />
      </div>

      <button @click="$router.push({ name: 'Home' })" class="home-btn">
        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        Về trang chủ
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const productName = route.query.productName || ''
const orderCode = route.query.orderCode || ''
</script>

<style scoped>
.success-page {
  min-height: 100vh;
  background: var(--color-surface);
  display: flex; align-items: center; justify-content: center;
  padding: 1.5rem;
}
.success-card {
  text-align: center;
  max-width: 24rem;
  width: 100%;
}
.icon-circle {
  width: 96px; height: 96px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 1.5rem;
}
.icon-circle.success {
  background: oklch(0.72 0.19 145 / 0.1);
  color: var(--color-success);
}
h1 {
  font-size: 1.75rem;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
.product-name { color: var(--color-text-muted); margin-bottom: 0.25rem; }
.order-code {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  margin-bottom: 2rem;
}
.order-code strong {
  font-family: monospace;
  color: var(--color-primary);
}
.dispense-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  padding: 1.5rem;
  margin-bottom: 2rem;
}
.dispense-card p { color: var(--color-text-muted); font-size: 0.875rem; margin-bottom: 1rem; }
.spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--color-surface-alt);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }
.home-btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: var(--color-primary);
  color: white;
  padding: 0.75rem 2rem;
  border-radius: 0.75rem;
  font-weight: 600;
  border: none;
  font-size: 1rem;
  transition: background 0.2s, transform 0.1s;
}
.home-btn:hover { background: var(--color-primary-dark); }
.home-btn:active { transform: scale(0.97); }
</style>
