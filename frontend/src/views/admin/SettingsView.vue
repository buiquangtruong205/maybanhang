<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">Cấu hình Hệ thống</h1>
      <button class="btn-ghost danger" @click="confirmRestore">
        ⟲ Khôi phục mặc định
      </button>
    </div>

    <div v-if="loading" class="loading">Đang tải cấu hình...</div>
    
    <div v-else class="settings-container">
      <!-- Tabs -->
      <div class="settings-tabs">
        <button 
          v-for="group in groups" 
          :key="group.id"
          class="tab-btn"
          :class="{ active: activeTab === group.id }"
          @click="activeTab = group.id"
        >
          <span class="tab-icon">{{ group.icon }}</span>
          {{ group.label }}
        </button>
      </div>

      <!-- Content -->
      <div class="settings-content">
        <div v-for="setting in filteredSettings" :key="setting.key" class="setting-item">
          <div class="setting-info">
            <label class="setting-label">{{ setting.description || setting.key }}</label>
            <small class="setting-key">{{ setting.key }}</small>
          </div>
          
          <div class="setting-control">
            <!-- Boolean Toggle -->
            <label v-if="setting.type === 'boolean'" class="toggle-switch">
              <input 
                type="checkbox" 
                :checked="setting.value === 'true'"
                @change="e => update(setting, e.target.checked ? 'true' : 'false')"
              >
              <span class="slider"></span>
            </label>

            <!-- Number Input -->
            <input 
              v-else-if="setting.type === 'number'"
              type="number"
              v-model="setting.tempValue"
              @blur="saveIfChanged(setting)"
              @keyup.enter="saveIfChanged(setting)"
              class="admin-input"
            >

            <!-- Text Input -->
            <input 
              v-else
              type="text"
              v-model="setting.tempValue"
              @blur="saveIfChanged(setting)"
              @keyup.enter="saveIfChanged(setting)"
              class="admin-input"
            >
             <span v-if="setting.saving" class="saving-status">Đang lưu...</span>
             <span v-if="setting.saved" class="saved-status">✓ Đã lưu</span>
          </div>
        </div>
        
        <div v-if="filteredSettings.length === 0" class="empty-state">
          Không có cấu hình nào trong nhóm này
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSettings, updateSetting, restoreDefaultSettings } from '../../api/admin.js'

const loading = ref(true)
const settings = ref([])
const activeTab = ref('system')

const groups = [
  { id: 'system', label: 'Hệ thống', icon: '🖥️' },
  { id: 'hardware', label: 'Phần cứng', icon: '🔌' },
  { id: 'payment', label: 'Thanh toán', icon: '💳' },
]

onMounted(async () => {
  await load()
})

async function load() {
  loading.value = true
  try {
    const data = await getSettings()
    settings.value = data.map(s => ({
      ...s,
      tempValue: s.value, // Local state for editing
      saving: false,
      saved: false
    }))
  } catch (e) {
    console.error(e)
    alert('Lỗi tải cấu hình')
  } finally {
    loading.value = false
  }
}

const filteredSettings = computed(() => {
  return settings.value.filter(s => s.group === activeTab.value)
})

async function update(setting, newValue) {
  setting.saving = true
  setting.saved = false
  try {
    await updateSetting(setting.key, newValue)
    setting.value = newValue
    setting.tempValue = newValue
    setting.saved = true
    setTimeout(() => setting.saved = false, 2000)
  } catch (e) {
    alert('Lỗi lưu cấu hình: ' + e.message)
    setting.tempValue = setting.value // Revert
  } finally {
    setting.saving = false
  }
}

function saveIfChanged(setting) {
  if (setting.tempValue !== setting.value) {
    update(setting, setting.tempValue)
  }
}

async function confirmRestore() {
  if (confirm('Bạn có chắc chắn muốn khôi phục toàn bộ cấu hình về mặc định? Hành động này không thể hoàn tác.')) {
     try {
       await restoreDefaultSettings()
       await load()
       alert('Đã khôi phục thành công!')
     } catch (e) {
       alert(e.message)
     }
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.page-title { font-size: 1.5rem; color: white; margin: 0; }
.settings-container { display: flex; gap: 2rem; align-items: flex-start; }
.settings-tabs { display: flex; flex-direction: column; gap: 0.5rem; min-width: 200px; }
.tab-btn {
  text-align: left;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.6);
  cursor: pointer;
  border-radius: 0.5rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}
.tab-btn:hover { background: rgba(255,255,255,0.05); color: white; }
.tab-btn.active { background: var(--color-primary); color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

.settings-content { flex: 1; background: var(--color-card); border-radius: 1rem; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.05); }

.setting-item { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.setting-item:last-child { border-bottom: none; }

.setting-info { display: flex; flex-direction: column; gap: 0.25rem; }
.setting-label { font-weight: 500; color: white; }
.setting-key { font-family: monospace; color: rgba(255,255,255,0.3); font-size: 0.75rem; }

.setting-control { display: flex; align-items: center; gap: 1rem; position: relative; }
.admin-input { width: 250px; text-align: right; }

.saving-status { font-size: 0.75rem; color: rgba(255,255,255,0.5); font-style: italic; position: absolute; right: 105%; white-space: nowrap; }
.saved-status { font-size: 0.75rem; color: var(--color-success); position: absolute; right: 105%; white-space: nowrap; }

/* Toggle Switch */
.toggle-switch { position: relative; display: inline-block; width: 44px; height: 24px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(255,255,255,0.1); transition: .4s; border-radius: 24px; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: var(--color-primary); }
input:checked + .slider:before { transform: translateX(20px); }

.btn-ghost.danger { color: var(--color-danger); border: 1px solid rgba(255,100,100,0.2); }
.btn-ghost.danger:hover { background: rgba(255,100,100,0.1); }
.loading, .empty-state { text-align: center; color: rgba(255,255,255,0.4); padding: 2rem; }

@media (max-width: 768px) {
  .settings-container { flex-direction: column; }
  .settings-tabs { flex-direction: row; width: 100%; overflow-x: auto; }
  .tab-btn { flex: 1; justify-content: center; }
  .setting-item { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
  .setting-control, .admin-input { width: 100%; text-align: left; }
}
</style>
