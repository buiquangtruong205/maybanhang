<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Tổng quan</h1>
      <button class="btn-primary" @click="handleExport" :disabled="exporting">
        {{ exporting ? 'Đang xuất...' : 'Xuất Báo Cáo Excel' }}
      </button>
    </div>

    <!-- Stats Cards -->
    <div v-if="loading" class="loading-text">Đang tải dữ liệu...</div>
    <div v-else>
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.label" class="stat-card">
          <p class="stat-label">{{ card.label }}</p>
          <p class="stat-value" :style="{ color: card.color }">{{ card.value }}</p>
        </div>
      </div>

      <!-- Charts & Top Products -->
      <div class="dashboard-grid">
        <div class="chart-section">
          <RevenueChart :period="period" :data="chartData" @period-change="changePeriod" />
        </div>
        <div class="top-products-section">
          <TopProducts :products="topProducts" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats, getRevenueChart, getTopProducts, exportExcel } from '../../api/admin.js'
import RevenueChart from '../../components/admin/RevenueChart.vue'
import TopProducts from '../../components/admin/TopProducts.vue'

const loading = ref(true)
const exporting = ref(false)
const statCards = ref([])
const period = ref('week')
const chartData = ref({})
const topProducts = ref([])

onMounted(async () => {
  await loadAll()
})

async function loadAll() {
  loading.value = true
  try {
    const [s, c, t] = await Promise.all([
      getStats(),
      getRevenueChart(period.value),
      getTopProducts(5)
    ])
    
    statCards.value = [
      { label: 'Doanh thu', value: formatVnd(s.total_revenue), color: 'var(--color-success)' },
      { label: 'Tổng đơn hàng', value: s.total_orders, color: 'white' },
      { label: 'Đơn hoàn thành', value: s.completed_orders, color: 'var(--color-primary-light)' },
      { label: 'Máy online', value: `${s.online_machines}/${s.total_machines}`, color: 'var(--color-info)' },
    ]
    chartData.value = c
    topProducts.value = t
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function changePeriod(p) {
  period.value = p
  chartData.value = await getRevenueChart(p)
}

async function handleExport() {
  exporting.value = true
  try {
    await exportExcel()
  } catch (e) {
    alert('Lỗi xuất file: ' + e.message)
  } finally {
    exporting.value = false
  }
}

function formatVnd(amount) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount || 0)
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; color: white; margin: 0; }
.loading-text { color: rgba(255,255,255,0.4); text-align: center; padding: 3rem 0; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
@media (min-width: 1024px) { .stats-grid { grid-template-columns: repeat(4, 1fr); } }
.stat-card { background: var(--color-card); border: 1px solid rgba(255,255,255,0.05); border-radius: 1rem; padding: 1.25rem; }
.stat-label { font-size: 0.875rem; color: rgba(255,255,255,0.4); margin-bottom: 0.25rem; }
.stat-value { font-family: 'Rubik', sans-serif; font-size: 1.5rem; font-weight: 700; }

.dashboard-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
@media (min-width: 1024px) { .dashboard-grid { grid-template-columns: 2fr 1fr; } }
.chart-section { height: 400px; }
.top-products-section { height: 400px; }
</style>
