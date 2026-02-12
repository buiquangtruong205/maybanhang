<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <p>{{ message }}</p>
      </div>

      <div class="modal-actions">
        <button class="btn-cancel" @click="close">Hủy</button>
        <button class="btn-confirm" @click="confirm">
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isOpen: Boolean,
  title: {
    type: String,
    default: 'Xác nhận'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'Xóa'
  }
})

const emit = defineEmits(['close', 'confirm'])

function close() {
  emit('close')
}

function confirm() {
  emit('confirm')
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
  max-width: 400px;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: modal-pop 0.2s ease-out;
}

@keyframes modal-pop {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
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
  margin: 0;
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
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9375rem;
  line-height: 1.5;
}

.modal-actions {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.btn-cancel,
.btn-confirm {
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
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

.btn-confirm {
  background: var(--color-danger);
  color: white;
}

.btn-confirm:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>
