<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Tổng quan</h1>
      <div class="header-actions">
        <button class="btn-report" @click="openIssueModal">Báo sự cố ⚠️</button>
        <button class="btn-primary" @click="handleExport" :disabled="exporting">
          {{ exporting ? 'Đang xuất...' : 'Xuất Báo Cáo Excel' }}
        </button>
      </div>
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
        <div class="chart-section" v-if="authStore.isAdmin">
          <RevenueChart :period="period" :data="chartData" @period-change="changePeriod" />
        </div>
        <div class="chart-section" v-else>
           <!-- Placeholder for Staff -->
           <div class="staff-welcome" style="height: 100%; display: flex; align-items: center; justify-content: center; background: var(--color-card); border-radius: 1rem; color: rgba(255,255,255,0.5);">
              <p>Xin chào nhân viên vận hành! 👋</p>
           </div>
        </div>
        <div class="top-products-section">
          <TopProducts :products="topProducts" />
        </div>
      </div>
    </div>

    <!-- Issue Reporting Modal -->
    <div v-if="showIssueModal" class="modal-overlay">
      <div class="modal-backdrop" @click="showIssueModal = false" />
      <div class="modal-content">
        <h3 class="modal-title">Báo cáo sự cố máy bán hàng</h3>
        <form @submit.prevent="submitIssue" class="modal-form">
          <label class="form-label">Chọn máy (nếu có)</label>
          <select v-model="issueForm.machine_id" class="admin-input">
            <option :value="null">Không rõ máy</option>
            <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.name }} - {{ m.location }}</option>
          </select>
          
          <label class="form-label">Nội dung sự cố</label>
          <textarea 
            v-model="issueForm.content" 
            class="admin-input textarea" 
            placeholder="Mô tả chi tiết sự cố (vd: Máy kẹt lò xo, không nhả hàng...)" 
            required
            rows="4"
          ></textarea>

          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showIssueModal = false">Hủy</button>
            <button type="submit" class="btn-primary" :disabled="submitting">
              {{ submitting ? 'Đang gửi...' : 'Gửi báo cáo' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getStats, getRevenueChart, getTopProducts, exportExcel, getMachines, createIssue } from '../../api/admin.js'
import { formatCurrency } from '../../utils/formatters.js'
import RevenueChart from '../../components/admin/RevenueChart.vue'
import TopProducts from '../../components/admin/TopProducts.vue'
import { useAuthStore } from '../../stores/auth.js'
import socket from '../../plugins/socket'

const authStore = useAuthStore()
const loading = ref(true)
const exporting = ref(false)
const submitting = ref(false)
const statCards = ref([])
const period = ref('week')
const chartData = ref({})
const topProducts = ref([])
const machines = ref([])
const showIssueModal = ref(false)
const issueForm = ref({ machine_id: null, content: '' })

// Socket handler
function handleOrderUpdate(data) {
  console.log("🔔 Real-time update:", data)
  // Hiển thị thông báo (có thể nâng cấp lên Toast đẹp hơn sau)
  // alert(`Đơn hàng mới #${data.order_code}: ${data.status}`) -> hơi phiền, chỉ refresh số liệu thôi
  loadAll()
}

onMounted(async () => {
  await loadAll()
  socket.on('order_update', handleOrderUpdate)
  
  // Debug connection status
  console.log("🔌 Socket status:", socket.connected)
  socket.on("connect", () => console.log("🟢 Dashboard: Socket connected"))
  socket.on("disconnect", () => console.log("🔴 Dashboard: Socket disconnected"))
})

onUnmounted(() => {
  socket.off('order_update', handleOrderUpdate)
})

async function loadAll() {
  loading.value = true
  try {
    const [s, c, t] = await Promise.all([
      getStats(),
      authStore.isAdmin ? getRevenueChart(period.value) : Promise.resolve({}),
      getTopProducts(5)
    ])
    
    if (authStore.isAdmin) {
        statCards.value = [
          { label: 'Doanh thu', value: formatCurrency(s.total_revenue), color: 'var(--color-success)' },
          { label: 'Tổng đơn hàng', value: s.total_orders, color: 'white' },
          { label: 'Đã thanh toán', value: s.paid_orders, color: 'var(--color-primary-light)' },
          { label: 'Máy đang chạy', value: `${s.online_machines}/${s.total_machines}`, color: 'var(--color-info)' },
        ]
        chartData.value = c
    } else {
        // Staff only sees machine status
        statCards.value = [
             { label: 'Máy đang chạy', value: `${s.online_machines}/${s.total_machines}`, color: 'var(--color-info)' },
             { label: 'Tổng đơn hàng', value: s.total_orders, color: 'white' } // Maybe allow viewing order count
        ]
    }
    
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

</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.header-actions { display: flex; gap: 0.75rem; }
.page-title { font-size: 1.5rem; color: white; margin: 0; }
.btn-report {
  background: rgba(255, 100, 100, 0.1);
  color: #ff6b6b;
  border: 1px solid rgba(255, 100, 100, 0.2);
  padding: 0.6rem 1.25rem;
  border-radius: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-report:hover {
  background: #ff6b6b;
  color: white;
}
.loading-text { color: rgba(255,255,255,0.4); text-align: center; padding: 3rem 0; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
@media (min-width: 1024px) { .stats-grid { grid-template-columns: repeat(4, 1fr); } }
.stat-card { background: var(--color-card); border: 1px solid rgba(255,255,255,0.05); border-radius: 1rem; padding: 1.25rem; }
.form-label { display: block; color: rgba(255,255,255,0.6); font-size: 0.875rem; margin-bottom: 0.5rem; }
.textarea { resize: vertical; padding: 0.75rem; }
.stat-label { font-size: 0.875rem; color: rgba(255,255,255,0.4); margin-bottom: 0.25rem; }
.stat-value { font-family: 'Rubik', sans-serif; font-size: 1.5rem; font-weight: 700; }

.dashboard-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
@media (min-width: 1024px) { .dashboard-grid { grid-template-columns: 2fr 1fr; } }
.chart-section { height: 400px; }
.top-products-section { height: 400px; }
</style>
