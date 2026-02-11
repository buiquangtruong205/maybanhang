<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Sản phẩm</h1>
      <button class="btn-primary" @click="openModal()">+ Thêm sản phẩm</button>
    </div>

    <div class="admin-card">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Tên</th>
            <th>Giá</th>
            <th>Danh mục</th>
            <th>Trạng thái</th>
            <th style="text-align:right">Thao tác</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in products" :key="p.id">
            <td>
              <div class="product-name">
                <img v-if="p.image_url" :src="p.image_url" :alt="p.name" class="thumb" />
                <div>
                  <span>{{ p.name }}</span>
                  <small v-if="p.description">{{ p.description }}</small>
                </div>
              </div>
            </td>
            <td class="price">{{ formatVnd(p.price) }}</td>
            <td><span class="badge badge-info">{{ p.category }}</span></td>
            <td><span :class="p.is_available ? 'badge badge-success' : 'badge badge-muted'">{{ p.is_available ? 'Còn hàng' : 'Hết hàng' }}</span></td>
            <td class="actions">
              <button class="btn-ghost" @click="openModal(p)">Sửa</button>
              <button class="btn-ghost danger" @click="remove(p.id)">Xóa</button>
            </td>
          </tr>
          <tr v-if="!products.length">
            <td colspan="5" class="empty">Chưa có sản phẩm</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-backdrop" @click="showModal = false" />
      <div class="modal-content">
        <h3 class="modal-title">{{ form.id ? 'Sửa' : 'Thêm' }} sản phẩm</h3>
        <form @submit.prevent="save" class="modal-form">
          <input v-model="form.name" placeholder="Tên sản phẩm" required class="admin-input" />
          <input v-model.number="form.price" type="number" placeholder="Giá (VND)" required class="admin-input" />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProducts, createProduct, updateProduct, deleteProduct } from '../../api/admin.js'

const products = ref([])
const showModal = ref(false)
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

async function remove(id) {
  if (!confirm('Xóa sản phẩm này?')) return
  try { await deleteProduct(id); await load() } catch {}
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
