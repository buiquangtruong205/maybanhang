<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Đơn hàng</h1>
      <select v-model="statusFilter" class="filter-select" @change="load">
        <option value="">Tất cả</option>
        <option value="pending">Chờ thanh toán</option>
        <option value="paid">Đã thanh toán</option>
        <option value="completed">Hoàn thành</option>
        <option value="cancelled">Đã hủy</option>
      </select>
    </div>

    <div class="admin-card">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Mã đơn</th>
            <th>Sản phẩm</th>
            <th>Số tiền</th>
            <th>Trạng thái</th>
            <th>Thời gian</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.id">
            <td class="order-code">{{ o.order_code }}</td>
            <td>{{ o.product?.name || `SP #${o.product_id}` }}</td>
            <td class="price">{{ formatVnd(o.amount) }}</td>
            <td><span :class="'badge ' + statusClass(o.status)">{{ statusLabel(o.status) }}</span></td>
            <td class="time">{{ formatDate(o.created_at) }}</td>
          </tr>
          <tr v-if="!orders.length">
            <td colspan="5" class="empty">Chưa có đơn hàng</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getOrders } from '../../api/admin.js'

const orders = ref([])
const statusFilter = ref('')

onMounted(() => load())

async function load() {
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    orders.value = await getOrders(params)
  } catch {}
}

const statusMap = { pending: 'Chờ TT', paid: 'Đã TT', completed: 'Xong', cancelled: 'Hủy' }
function statusLabel(s) { return statusMap[s] || s }
function statusClass(s) {
  return { paid: 'badge-success', completed: 'badge-info', cancelled: 'badge-danger', pending: 'badge-warning' }[s] || 'badge-muted'
}
function formatVnd(v) { return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v || 0) }
function formatDate(d) { return d ? new Date(d).toLocaleString('vi-VN') : '-' }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; color: white; }
.filter-select {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.1);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
}
.filter-select option { background: #1a1a2e; }
.order-code { font-family: monospace; font-size: 0.8rem; }
.price { font-family: 'Rubik', sans-serif; font-weight: 600; color: var(--color-accent); }
.time { font-size: 0.8rem; color: rgba(255,255,255,0.4); }
.empty { text-align: center; color: rgba(255,255,255,0.3); padding: 2rem !important; }
</style>
