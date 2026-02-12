<template>
  <div class="users-view">
    <div class="header">
      <div class="title">
        <h1>Quản lý thành viên</h1>
        <p>Danh sách tài khoản quản trị và nhân viên</p>
      </div>
      <button class="btn-primary" @click="openCreateModal">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Thêm thành viên
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon bg-primary-soft">
          <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
        </div>
        <div class="stat-info">
          <h3>Tổng thành viên</h3>
          <p>{{ users.length }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-success-soft">
          <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
        <div class="stat-info">
          <h3>Admin</h3>
          <p>{{ adminCount }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-info-soft">
          <svg class="w-6 h-6 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
        </div>
        <div class="stat-info">
          <h3>Nhân viên</h3>
          <p>{{ users.length - adminCount }}</p>
        </div>
      </div>
    </div>

    <!-- Users Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Tên đăng nhập</th>
            <th>Họ và tên</th>
            <th>Vai trò</th>
            <th class="text-right">Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" class="loading-row">
            <td colspan="5" class="text-center">Đang tải dữ liệu...</td>
          </tr>
          <tr v-else-if="users.length === 0" class="empty-row">
            <td colspan="5" class="text-center">Chưa có thành viên nào</td>
          </tr>
          <tr v-for="user in users" :key="user.id">
            <td>#{{ user.id }}</td>
            <td class="font-medium">{{ user.username }}</td>
            <td>{{ user.full_name || '---' }}</td>
            <td>
              <span class="badge" :class="user.role === 'ADMIN' ? 'badge-primary' : 'badge-secondary'">
                {{ user.role }}
              </span>
            </td>
            <td class="text-right actions-cell">
              <button class="btn-icon" title="Sửa" @click="openEditModal(user)">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              </button>
              <button 
                class="btn-icon text-danger" 
                title="Xóa" 
                @click="confirmDelete(user)"
                :disabled="user.role === 'ADMIN' && user.username === 'admin'"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UserModal 
      :is-open="showModal" 
      :user="selectedUser"
      @close="closeModal"
      @submit="handleSave"
    />

    <ConfirmModal
      :is-open="showDeleteModal"
      title="Xác nhận xóa"
      :message="`Bạn có chắc chắn muốn xóa thành viên ${userToDelete?.username}?`"
      @close="showDeleteModal = false"
      @confirm="handleDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersApi } from '@/api/users'
import UserModal from '@/components/admin/UserModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const users = ref([])
const loading = ref(false)
const showModal = ref(false)
const showDeleteModal = ref(false)
const selectedUser = ref(null)
const userToDelete = ref(null)

const adminCount = computed(() => users.value.filter(u => u.role === 'ADMIN').length)

onMounted(() => {
  fetchUsers()
})

async function fetchUsers() {
  loading.value = true
  try {
    const res = await usersApi.list()
    users.value = res // res đã là mảng dữ liệu
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  selectedUser.value = null
  showModal.value = true
}

function openEditModal(user) {
  selectedUser.value = { ...user } // Clone to avoid direct mutation
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  selectedUser.value = null
}

async function handleSave(formData) {
  try {
    if (selectedUser.value) {
      await usersApi.update(selectedUser.value.id, formData)
    } else {
      await usersApi.create(formData)
    }
    await fetchUsers()
    closeModal()
  } catch (error) {
    alert(error.response?.data?.detail || 'Có lỗi xảy ra')
  }
}

function confirmDelete(user) {
  userToDelete.value = user
  showDeleteModal.value = true
}

async function handleDelete() {
  if (!userToDelete.value) return
  try {
    await usersApi.delete(userToDelete.value.id)
    await fetchUsers()
    showDeleteModal.value = false
    userToDelete.value = null
  } catch (error) {
    alert(error.response?.data?.detail || 'Có lỗi xảy ra')
  }
}
</script>

<style scoped>
.users-view {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  animation: fadeIn 0.5s ease-out;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 10; /* Đưa header lên trên cùng để không bị các layer khác đè lên */
}

.title h1 {
  font-size: 1.75rem;
  font-weight: 800;
  color: white; /* Đảm bảo nổi bật trên nền tối */
  margin-bottom: 0.25rem;
  letter-spacing: -0.02em;
}

.title p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.9375rem;
}

.btn-primary {
  display: flex;
  align-items: center;
  background: var(--color-primary);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 700;
  cursor: pointer !important; /* Buộc hiện con trỏ tay */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px oklch(0.65 0.14 180 / 0.2);
  position: relative;
  z-index: 20; /* Luôn nằm trên mọi thành phần của nội dung */
  pointer-events: auto !important; /* Đảm bảo nhận được click */
}

.btn-primary:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px oklch(0.65 0.14 180 / 0.3);
  filter: brightness(1.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1.25rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 100%);
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

.stat-icon {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bg-primary-soft { background: oklch(0.65 0.14 180 / 0.12); color: var(--color-primary-light); }
.bg-success-soft { background: oklch(0.72 0.19 145 / 0.12); color: var(--color-success); }
.bg-info-soft { background: oklch(0.70 0.12 230 / 0.12); color: var(--color-info); }

.stat-info h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-info p {
  font-size: 1.75rem;
  font-weight: 800;
  color: white; /* Chữ trắng rõ nét */
  line-height: 1;
}

.table-container {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(12px);
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 1.25rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 700;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.data-table td {
  padding: 1.125rem 1.5rem;
  font-size: 0.9375rem;
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.2s ease;
}

.data-table tr:last-child td { border-bottom: none; }

.data-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
  color: white;
}

.badge {
  display: inline-flex;
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-primary {
  background: oklch(0.65 0.14 180 / 0.15);
  color: var(--color-primary-light);
  border: 1px solid oklch(0.65 0.14 180 / 0.3);
}

.badge-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.actions-cell {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-icon {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0.625rem;
  border-radius: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
  transform: scale(1.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-icon.text-danger:hover {
  background: oklch(0.63 0.22 27 / 0.15);
  color: var(--color-danger);
  border-color: oklch(0.63 0.22 27 / 0.3);
}

.btn-icon:disabled {
  opacity: 0.2;
  cursor: not-allowed;
  transform: none;
}
</style>
