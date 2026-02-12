<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isEdit ? 'Chỉnh sửa thành viên' : 'Thêm thành viên mới' }}</h3>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <form @submit.prevent="handleSubmit" class="modal-body">
        <div class="form-group">
          <label>Tên đăng nhập <span class="required">*</span></label>
          <input 
            v-model="form.username" 
            type="text" 
            required 
            :disabled="isEdit"
            placeholder="Nhập tên đăng nhập..."
          >
          <small v-if="isEdit" class="hint">Không thể thay đổi tên đăng nhập</small>
        </div>

        <div class="form-group">
          <label>Mật khẩu <span v-if="!isEdit" class="required">*</span></label>
          <input 
            v-model="form.password" 
            type="password" 
            :required="!isEdit"
            :placeholder="isEdit ? 'Để trống nếu không đổi' : 'Nhập mật khẩu...'"
          >
        </div>

        <div class="form-group">
          <label>Họ và tên</label>
          <input 
            v-model="form.full_name" 
            type="text" 
            placeholder="Nhập họ tên đầy đủ..."
          >
        </div>

        <div class="form-group">
          <label>Phân quyền <span class="required">*</span></label>
          <select v-model="form.role" required>
            <option value="STAFF">Nhân viên (STAFF)</option>
            <option value="ADMIN">Quản trị viên (ADMIN)</option>
          </select>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="close">Hủy</button>
          <button type="submit" class="btn-submit" :disabled="loading">
            {{ loading ? 'Đang lưu...' : (isEdit ? 'Cập nhật' : 'Thêm mới') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  user: Object
})

const emit = defineEmits(['close', 'submit'])

const loading = ref(false)
const isEdit = ref(false)
const form = reactive({
  username: '',
  password: '',
  full_name: '',
  role: 'STAFF'
})

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    if (props.user) {
      isEdit.value = true
      form.username = props.user.username
      form.full_name = props.user.full_name
      form.role = props.user.role
      form.password = ''
    } else {
      isEdit.value = false
      form.username = ''
      form.password = ''
      form.full_name = ''
      form.role = 'STAFF'
    }
  }
})

function close() {
  emit('close')
}

async function handleSubmit() {
  loading.value = true
  try {
    const data = { ...form }
    if (isEdit.value && !data.password) {
      delete data.password
    }
    await emit('submit', data)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--color-card);
  color: white;
  width: 100%;
  max-width: 500px;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.75rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #ef4444;
  transform: rotate(90deg);
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.required {
  color: var(--color-danger);
}

.form-group input,
.form-group select {
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9375rem;
  transition: all 0.2s;
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.25);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 3px oklch(0.65 0.14 180 / 0.15);
}

.form-group select option {
  background: var(--color-card);
  color: white;
}

.form-group input:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.1);
}

.hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.btn-cancel,
.btn-submit {
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-submit {
  background: var(--color-primary);
  color: white;
  border: none;
  box-shadow: 0 4px 12px oklch(0.65 0.14 180 / 0.2);
}

.btn-submit:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px oklch(0.65 0.14 180 / 0.3);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
}

.btn-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
