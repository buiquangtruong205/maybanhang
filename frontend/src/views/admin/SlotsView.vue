<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Vị trí hàng (Slots)</h1>
      <div class="header-actions">
        <select v-model="machineFilter" class="filter-select" @change="load">
          <option value="">Tất cả máy</option>
          <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
        <button class="btn-primary" @click="openModal()">+ Thêm vị trí</button>
      </div>
    </div>

    <div class="admin-card">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Slot</th>
            <th>Máy</th>
            <th>Sản phẩm</th>
            <th>Tồn kho</th>
            <th style="text-align:right">Thao tác</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td class="slot-code">{{ s.slot_code }}</td>
            <td>{{ machineName(s.machine_id) }}</td>
            <td>{{ productName(s.product_id) }}</td>
            <td>
              <div class="stock-bar">
                <div class="stock-fill" :style="{ width: stockPercent(s) + '%', background: stockColor(s) }" />
              </div>
              <span class="stock-text">{{ s.stock }}/{{ s.capacity }}</span>
            </td>
            <td class="actions">
              <button class="btn-ghost success" @click="quickRefill(s.id)" title="Nạp đầy nhanh">⚡ Refill</button>
              <button class="btn-ghost" @click="openModal(s)">Sửa</button>
              <button class="btn-ghost danger" @click="remove(s.id)">Xóa</button>
            </td>
          </tr>
          <tr v-if="!slots.length">
            <td colspan="5" class="empty">Chưa có slot</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-backdrop" @click="showModal = false" />
      <div class="modal-content">
        <h3 class="modal-title">{{ form.id ? 'Cập nhật' : 'Thêm mới' }} vị trí hàng</h3>
        <form @submit.prevent="save" class="modal-form">
          <input v-model="form.slot_code" placeholder="Mã slot (A1, B2...)" required class="admin-input" />
          <select v-model.number="form.machine_id" class="admin-input" required>
            <option value="" disabled>Chọn máy</option>
            <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
          <select v-model.number="form.product_id" class="admin-input">
            <option value="" disabled>Chọn sản phẩm</option>
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <div class="row-2">
            <input v-model.number="form.stock" type="number" placeholder="Tồn kho" class="admin-input" min="0" />
            <input v-model.number="form.capacity" type="number" placeholder="Sức chứa" class="admin-input" min="1" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showModal = false">Hủy</button>
            <button type="submit" class="btn-primary">{{ form.id ? 'Cập nhật' : 'Tạo' }}</button>
          </div>
        </form>
      </div>
    </div>
    <!-- Confirm Modal -->
    <ConfirmModal 
      :isOpen="showConfirm"
      title="Xóa slot"
      message="Bạn có chắc chắn muốn xóa slot này không? Hành động này không thể hoàn tác."
      @close="showConfirm = false"
      @confirm="executeDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSlots, createSlot, updateSlot, deleteSlot, refillSlot, getMachines, getProducts } from '../../api/admin.js'
import ConfirmModal from '../../components/ConfirmModal.vue'

const slots = ref([])
const machines = ref([])
const products = ref([])
const machineFilter = ref('')
const showModal = ref(false)
const showConfirm = ref(false)
const confirmId = ref(null)
const form = ref({})

async function quickRefill(id) {
  try {
    await refillSlot(id)
    await load()
  } catch (e) {
    alert('Không thể nạp hàng: ' + e.message)
  }
}

onMounted(async () => {
  try {
    const [m, p] = await Promise.all([getMachines(), getProducts()])
    machines.value = m
    products.value = p
  } catch {}
  load()
})

async function load() {
  try {
    const params = machineFilter.value ? { machine_id: machineFilter.value } : {}
    slots.value = await getSlots(params)
  } catch {}
}

function machineName(id) { return machines.value.find(m => m.id === id)?.name || `#${id}` }
function productName(id) { return products.value.find(p => p.id === id)?.name || (id ? `#${id}` : '—') }
function stockPercent(s) { return s.capacity ? (s.stock / s.capacity) * 100 : 0 }
function stockColor(s) {
  const pct = stockPercent(s)
  if (pct > 50) return 'var(--color-success)'
  if (pct > 20) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function openModal(s = null) {
  form.value = s ? { ...s } : { slot_code: '', machine_id: '', product_id: '', stock: 0, capacity: 10 }
  showModal.value = true
}

async function save() {
  try {
    if (form.value.id) await updateSlot(form.value.id, form.value)
    else await createSlot(form.value)
    showModal.value = false
    await load()
  } catch (e) { alert(e.message) }
}

function remove(id) {
  confirmId.value = id
  showConfirm.value = true
}

async function executeDelete() {
  try {
    await deleteSlot(confirmId.value)
    showConfirm.value = false
    await load()
  } catch (e) {
    alert('Có lỗi xảy ra: ' + e.message)
    showConfirm.value = false
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
.page-title { font-size: 1.5rem; color: white; }
.header-actions { display: flex; gap: 0.75rem; align-items: center; }
.filter-select {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.1);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
}
.filter-select option { background: #1a1a2e; }
.slot-code { font-family: monospace; font-weight: 700; color: var(--color-primary-light); }
.stock-bar {
  width: 80px;
  height: 6px;
  background: rgba(255,255,255,0.05);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}
.stock-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.stock-text { font-size: 0.75rem; color: rgba(255,255,255,0.5); }
.actions { text-align: right; display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn-ghost.danger { color: var(--color-danger); }
.btn-ghost.danger:hover { background: oklch(0.63 0.22 27 / 0.1); }
.btn-ghost.success { color: var(--color-success); font-weight: 700; }
.btn-ghost.success:hover { background: oklch(0.72 0.19 145 / 0.1); }
.empty { text-align: center; color: rgba(255,255,255,0.3); padding: 2rem !important; }
.modal-title { color: white; font-size: 1.125rem; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.75rem; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }
</style>
