<template>
  <div>
    <h1 class="page-title">Tổng quan</h1>

    <!-- Stats Cards -->
    <div v-if="loading" class="loading-text">Đang tải dữ liệu...</div>
    <div v-else class="stats-grid">
      <div v-for="card in statCards" :key="card.label" class="stat-card">
        <p class="stat-label">{{ card.label }}</p>
        <p class="stat-value" :style="{ color: card.color }">{{ card.value }}</p>
      </div>
    </div>

    <!-- Quick Links -->
    <div class="quick-links">
      <router-link to="/admin/products" class="quick-link">
        <p class="link-title">Sản phẩm</p>
        <p class="link-sub">Quản lý CRUD</p>
      </router-link>
      <router-link to="/admin/orders" class="quick-link">
        <p class="link-title">Đơn hàng</p>
        <p class="link-sub">Lịch sử giao dịch</p>
      </router-link>
      <router-link to="/admin/machines" class="quick-link">
        <p class="link-title">Máy</p>
        <p class="link-sub">Trạng thái & quản lý</p>
      </router-link>
      <router-link to="/admin/slots" class="quick-link">
        <p class="link-title">Slots</p>
        <p class="link-sub">Vị trí sản phẩm</p>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '../../api/admin.js'

const loading = ref(true)
const statCards = ref([])

onMounted(async () => {
  try {
    const s = await getStats()
    statCards.value = [
      { label: 'Doanh thu', value: formatVnd(s.total_revenue), color: 'var(--color-success)' },
      { label: 'Tổng đơn hàng', value: s.total_orders, color: 'white' },
      { label: 'Đơn hoàn thành', value: s.completed_orders, color: 'var(--color-primary-light)' },
      { label: 'Máy online', value: `${s.online_machines}/${s.total_machines}`, color: 'var(--color-info)' },
    ]
  } catch (e) {
    statCards.value = [{ label: 'Lỗi', value: e.message, color: 'var(--color-danger)' }]
  } finally {
    loading.value = false
  }
})

function formatVnd(amount) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount || 0)
}
</script>

<style scoped>
.page-title {
  font-size: 1.5rem;
  color: white;
  margin-bottom: 1.5rem;
}
.loading-text {
  color: rgba(255,255,255,0.4);
  text-align: center;
  padding: 3rem 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}
@media (min-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(4, 1fr); }
}
.stat-card {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 1rem;
  padding: 1.25rem;
}
.stat-label {
  font-size: 0.875rem;
  color: rgba(255,255,255,0.4);
  margin-bottom: 0.25rem;
}
.stat-value {
  font-family: 'Rubik', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
@media (min-width: 768px) {
  .quick-links { grid-template-columns: repeat(4, 1fr); }
}
.quick-link {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 1rem;
  padding: 1.25rem;
  text-align: center;
  text-decoration: none;
  transition: border-color 0.2s;
}
.quick-link:hover {
  border-color: oklch(0.65 0.14 180 / 0.3);
}
.link-title {
  color: white;
  font-weight: 600;
}
.link-sub {
  color: rgba(255,255,255,0.4);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
</style>
