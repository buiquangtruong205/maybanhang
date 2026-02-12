<template>
  <div v-if="isOpen" class="modal-overlay">
    <div class="modal-backdrop" @click="cancel" />
    <div class="modal-content confirm-card">
      <h3 class="modal-title">{{ title }}</h3>
      <p class="modal-message">{{ message }}</p>
      <div class="modal-actions">
        <button class="btn-ghost" @click="cancel">Hủy</button>
        <button class="btn-primary danger-btn" @click="confirm">Xác nhận xóa</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isOpen: Boolean,
  title: { type: String, default: 'Xác nhận' },
  message: { type: String, default: 'Bạn có chắc chắn muốn thực hiện hành động này?' }
})

const emit = defineEmits(['close', 'confirm'])

function cancel() {
  emit('close')
}

function confirm() {
  emit('confirm')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: center; justify-content: center;
}
.modal-backdrop {
  position: absolute; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
}
.confirm-card {
  position: relative; z-index: 101;
  width: 90%; max-width: 400px;
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 1rem; padding: 1.5rem;
  animation: scaleIn 0.2s ease-out;
}
.modal-title { color: white; font-size: 1.25rem; margin-bottom: 0.5rem; font-weight: 700; }
.modal-message { color: rgba(255,255,255,0.8); margin-bottom: 1.5rem; font-size: 0.9375rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; }
.danger-btn {
  background: var(--color-danger);
  color: white;
}
.danger-btn:hover {
  background: oklch(0.55 0.22 27);
  box-shadow: 0 4px 12px oklch(0.63 0.22 27 / 0.25);
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
