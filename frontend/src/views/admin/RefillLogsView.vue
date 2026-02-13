<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Nhật ký Nạp hàng</h1>
      <button @click="fetchLogs" class="btn-secondary">
        <i class="fas fa-sync-alt mr-2"></i>Làm mới
      </button>
    </div>

    <div class="glass-card p-6 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="modern-table">
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Nhân viên</th>
              <th>Máy / Vị trí</th>
              <th>Sản phẩm</th>
              <th class="text-center">Số lượng</th>
              <th class="text-right">Chi tiết kho</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" class="animate-pulse">
              <td colspan="6" class="p-8 text-center text-gray-500">Đang tải dữ liệu...</td>
            </tr>
            <tr v-else-if="logs.length === 0">
              <td colspan="6" class="p-8 text-center text-gray-500">Chưa có dữ liệu nạp hàng nào.</td>
            </tr>
            <tr v-for="log in logs" :key="log.id">
              <td class="text-sm text-gray-400">
                {{ formatDate(log.timestamp) }}
              </td>
              <td>
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold ring-1 ring-indigo-500/30">
                    {{ (log.user?.username || 'U')[0].toUpperCase() }}
                  </div>
                  <span class="text-gray-200 font-medium">{{ log.user?.full_name || log.user?.username || `User #${log.user_id}` }}</span>
                </div>
              </td>
              <td class="text-sm text-gray-300">
                <span class="font-mono bg-white/5 px-2 py-1 rounded text-xs">
                  {{ log.machine?.name }} / {{ log.slot?.slot_code }}
                </span>
              </td>
              <td>
                <div class="flex items-center gap-3">
                   <div class="w-8 h-8 rounded bg-white/5 p-1">
                     <img 
                      v-if="log.product?.image_url" 
                      :src="log.product.image_url" 
                      alt="Product" 
                      class="w-full h-full object-contain"
                    />
                   </div>
                  <span class="text-sm font-medium text-white">{{ log.product?.name }}</span>
                </div>
              </td>
              <td class="text-center">
                <span class="text-emerald-400 font-bold text-lg">+{{ log.quantity }}</span>
              </td>
              <td class="text-right text-sm text-gray-400">
                <span class="opacity-50">{{ log.old_quantity }}</span>
                <i class="fas fa-arrow-right mx-2 text-xs opacity-30"></i> 
                <span class="text-white font-bold">{{ log.new_quantity }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRefillLogs } from '@/api/admin'

const logs = ref([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    logs.value = await getRefillLogs({ limit: 50 }) // Default fetch recent 50 logs
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('vi-VN')
}

onMounted(() => {
  fetchLogs()
})
</script>
