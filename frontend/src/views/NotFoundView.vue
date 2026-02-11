<template>
  <div class="notfound-page">
    <div class="notfound-card animate-fade-in-up">
      <!-- 404 Icon -->
      <div class="icon-circle warning">
        <svg width="56" height="56" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <h1>404 — Không tìm thấy</h1>
      <p>Trang bạn tìm không tồn tại.</p>

      <button @click="$router.push({ name: 'Home' })" class="home-btn">
        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        Về trang chủ
      </button>
    </div>
  </div>
</template>

<script setup>
// No logic needed
</script>

<style scoped>
.notfound-page {
  min-height: 100vh;
  background: var(--color-surface);
  display: flex; align-items: center; justify-content: center;
  padding: 1.5rem;
}
.notfound-card {
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
.icon-circle.warning {
  background: oklch(0.80 0.16 85 / 0.1);
  color: var(--color-warning);
}
h1 {
  font-size: 1.75rem;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
p {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
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
