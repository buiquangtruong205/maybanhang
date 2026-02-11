<template>
  <div class="cancel-page">
    <div class="cancel-card animate-fade-in-up">
      <!-- Cancel Icon -->
      <div class="icon-circle danger">
        <svg width="56" height="56" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>

      <h1>Đã hủy thanh toán</h1>
      <p>Đơn hàng đã bị hủy hoặc hết thời gian. Bạn có thể thử lại bất cứ lúc nào.</p>

      <button @click="$router.push({ name: 'Home' })" class="home-btn">
        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
        Quay lại chọn sản phẩm
      </button>
    </div>
  </div>
</template>

<script setup>
// No logic needed
</script>

<style scoped>
.cancel-page {
  min-height: 100vh;
  background: var(--color-surface);
  display: flex; align-items: center; justify-content: center;
  padding: 1.5rem;
}
.cancel-card {
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
.icon-circle.danger {
  background: oklch(0.63 0.22 27 / 0.1);
  color: var(--color-danger);
}
h1 {
  font-size: 1.75rem;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
p {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
  line-height: 1.6;
}
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
