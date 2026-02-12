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
            {{ loading ? 'Đang xử lý...' : (isEdit ? 'Cập nhật' : 'Thêm mới') }}
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
  background: var(--color-surface);
  color: var(--color-text);
  width: 100%;
  max-width: 500px;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
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
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--color-text);
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
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.required {
  color: var(--color-danger);
}

.form-group input,
.form-group select {
  padding: 0.625rem 0.875rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  font-size: 0.9375rem;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 2px rgba(var(--color-primary), 0.25);
}

.form-group input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.btn-cancel,
.btn-submit {
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text);
}

.btn-submit {
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
}

.btn-submit:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
