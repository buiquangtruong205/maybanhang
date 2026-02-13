<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Sản phẩm</h1>
      <button v-if="authStore.isAdmin" class="btn-primary" @click="openModal()">+ Thêm sản phẩm</button>
    </div>

    <div class="glass-card p-6 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="modern-table">
          <thead>
            <tr>
              <th>Sản phẩm</th>
              <th>Giá</th>
              <th>Danh mục</th>
              <th>Trạng thái</th>
              <th class="text-right">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="products.length === 0">
              <td colspan="5" class="p-8 text-center text-gray-400">Chưa có sản phẩm nào.</td>
            </tr>
            <tr v-for="p in products" :key="p.id">
              <td>
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded bg-white/5 p-1 shrink-0">
                     <img v-if="p.image_url" :src="p.image_url" :alt="p.name" class="w-full h-full object-cover rounded-sm">
                     <div v-else class="w-full h-full bg-white/5 rounded-sm flex items-center justify-center text-xs text-gray-500">N/A</div>
                  </div>
                  <div>
                    <div class="font-bold text-white">{{ p.name }}</div>
                    <div class="text-xs text-gray-500 truncate max-w-[200px]">{{ p.description }}</div>
                  </div>
                </div>
              </td>
              <td class="font-mono text-emerald-400 font-bold">{{ formatVnd(p.price) }}</td>
              <td>
                <span class="inline-flex px-2 py-1 bg-white/5 rounded text-xs font-mono text-gray-300 border border-white/5">
                  {{ p.category }}
                </span>
              </td>
              <td>
                <span class="status-badge" :class="p.is_available ? 'resolved' : 'open'">
                   {{ p.is_available ? 'Còn hàng' : 'Hết hàng' }}
                </span>
              </td>
              <td class="text-right">
                <div class="flex justify-end gap-2">
                  <button v-if="authStore.isAdmin" class="p-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition" @click="openModal(p)" title="Sửa">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
                  </button>
                  <button v-if="authStore.isAdmin" class="p-2 rounded-full hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition" @click="remove(p.id)" title="Xóa">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-backdrop" @click="showModal = false" />
      <div class="modal-content">
        <h3 class="modal-title">{{ form.id ? 'Sửa' : 'Thêm' }} sản phẩm</h3>
        <form @submit.prevent="save" class="modal-form">
          <input v-model="form.name" placeholder="Tên sản phẩm" required class="admin-input" />
          <div class="form-group-price">
             <input v-model.number="form.price" type="number" placeholder="Giá (VND)" required class="admin-input" :disabled="!authStore.isAdmin && !!form.id" />
             <small v-if="!authStore.isAdmin && form.id" class="text-muted">Chỉ Admin mới được sửa giá</small>
          </div>
          <input v-model="form.category" placeholder="Danh mục (drink, water...)" class="admin-input" />
          <input v-model="form.image_url" placeholder="URL hình ảnh" class="admin-input" />
          <input v-model="form.description" placeholder="Mô tả" class="admin-input" />
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
      title="Xóa sản phẩm"
      message="Bạn có chắc chắn muốn xóa sản phẩm này không? Hành động này không thể hoàn tác."
      @close="showConfirm = false"
      @confirm="executeDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProducts, createProduct, updateProduct, deleteProduct } from '../../api/admin.js'
import ConfirmModal from '../../components/ConfirmModal.vue'
import { useAuthStore } from '../../stores/auth.js'

const authStore = useAuthStore()
const products = ref([])
const showModal = ref(false)
const showConfirm = ref(false)
const confirmId = ref(null)
const form = ref({})

onMounted(() => load())

async function load() {
  try { products.value = await getProducts() } catch {}
}

function openModal(p = null) {
  form.value = p ? { ...p } : { name: '', price: 0, category: 'drink', image_url: '', description: '', is_available: true }
  showModal.value = true
}

async function save() {
  try {
    if (form.value.id) await updateProduct(form.value.id, form.value)
    else await createProduct(form.value)
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
    await deleteProduct(confirmId.value)
    showConfirm.value = false
    await load()
  } catch (e) {
    alert('Có lỗi xảy ra: ' + e.message)
    showConfirm.value = false
  }
}

function formatVnd(v) { return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v || 0) }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; color: white; }
.product-name { display: flex; align-items: center; gap: 0.75rem; }
.thumb { width: 40px; height: 40px; border-radius: 0.5rem; object-fit: cover; background: rgba(255,255,255,0.05); }
.product-name small { display: block; font-size: 0.75rem; color: rgba(255,255,255,0.35); }
.price { font-family: 'Rubik', sans-serif; font-weight: 600; color: var(--color-accent); }
.actions { text-align: right; display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn-ghost.danger { color: var(--color-danger); }
.btn-ghost.danger:hover { background: oklch(0.63 0.22 27 / 0.1); }
.empty { text-align: center; color: rgba(255,255,255,0.3); padding: 2rem !important; }
.modal-title { color: white; font-size: 1.125rem; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.75rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }
</style>
