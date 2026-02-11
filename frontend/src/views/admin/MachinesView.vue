<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Máy</h1>
      <button class="btn-primary" @click="openModal()">+ Thêm máy</button>
    </div>

    <div class="machines-grid">
      <div v-for="m in machines" :key="m.id" class="machine-card">
        <div class="card-header">
          <span :class="'status-dot ' + (m.status === 'online' ? 'online' : 'offline')" />
          <h3>{{ m.name }}</h3>
          <div class="card-actions">
            <button class="icon-btn" @click="openModal(m)" title="Sửa">✏️</button>
            <button class="icon-btn" @click="remove(m.id)" title="Xóa">🗑️</button>
          </div>
        </div>
        <div class="card-body">
          <p><strong>Vị trí:</strong> {{ m.location || '—' }}</p>
          <p><strong>Trạng thái:</strong> <span :class="'badge ' + (m.status === 'online' ? 'badge-success' : 'badge-danger')">{{ m.status }}</span></p>
          <p v-if="m.last_ping"><strong>Ping:</strong> {{ new Date(m.last_ping).toLocaleString('vi-VN') }}</p>
        </div>
      </div>

      <div v-if="!machines.length" class="empty-state">Chưa có máy nào</div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-backdrop" @click="showModal = false" />
      <div class="modal-content">
        <h3 class="modal-title">{{ form.id ? 'Sửa' : 'Thêm' }} máy</h3>
        <form @submit.prevent="save" class="modal-form">
          <input v-model="form.name" placeholder="Tên/mã máy (VM001)" required class="admin-input" />
          <input v-model="form.location" placeholder="Vị trí" class="admin-input" />
          <input v-model="form.secret_key" placeholder="Secret key" class="admin-input" />
          <select v-model="form.status" class="admin-input">
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="maintenance">Bảo trì</option>
          </select>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showModal = false">Hủy</button>
            <button type="submit" class="btn-primary">{{ form.id ? 'Cập nhật' : 'Tạo' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMachines, createMachine, updateMachine, deleteMachine } from '../../api/admin.js'

const machines = ref([])
const showModal = ref(false)
const form = ref({})

onMounted(() => load())

async function load() {
  try { machines.value = await getMachines() } catch {}
}

function openModal(m = null) {
  form.value = m ? { ...m } : { name: '', location: '', secret_key: '', status: 'online' }
  showModal.value = true
}

async function save() {
  try {
    if (form.value.id) await updateMachine(form.value.id, form.value)
    else await createMachine(form.value)
    showModal.value = false
    await load()
  } catch (e) { alert(e.message) }
}

async function remove(id) {
  if (!confirm('Xóa máy này?')) return
  try { await deleteMachine(id); await load() } catch {}
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; color: white; }

.machines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}
.machine-card {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 1rem;
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.card-header h3 {
  flex: 1;
  color: white;
  font-size: 1rem;
}
.card-actions { display: flex; gap: 0.25rem; }
.icon-btn {
  background: none; border: none; cursor: pointer;
  font-size: 0.875rem;
  min-width: 32px; min-height: 32px;
  border-radius: 0.5rem;
  transition: background 0.15s;
}
.icon-btn:hover { background: rgba(255,255,255,0.05); }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%;
}
.status-dot.online { background: var(--color-success); box-shadow: 0 0 6px var(--color-success); }
.status-dot.offline { background: rgba(255,255,255,0.2); }
.card-body {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.card-body p {
  font-size: 0.875rem;
  color: rgba(255,255,255,0.6);
}
.card-body strong { color: rgba(255,255,255,0.35); }

.empty-state { text-align: center; color: rgba(255,255,255,0.3); padding: 3rem; grid-column: 1 / -1; }
.modal-title { color: white; font-size: 1.125rem; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.75rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }
</style>
