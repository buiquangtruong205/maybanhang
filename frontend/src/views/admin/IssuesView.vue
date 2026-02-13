<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Quản lý Sự cố</h1>
      <div class="flex gap-2">
        <select v-model="filterStatus" class="admin-input !w-auto">
          <option value="">Tất cả trạng thái</option>
          <option value="OPEN">Mới (Open)</option>
          <option value="IN_PROGRESS">Đang xử lý</option>
          <option value="RESOLVED">Đã xong</option>
        </select>
        <button @click="fetchIssues" class="btn-secondary">
          <i class="fas fa-sync-alt mr-2"></i>Làm mới
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="glass-card p-6 flex items-center justify-between">
        <div>
          <div class="text-gray-400 text-sm mb-1">Đang xử lý</div>
          <div class="text-3xl font-bold text-yellow-400">{{ issues.filter(i => i.status !== 'RESOLVED').length }}</div>
        </div>
        <div class="w-12 h-12 rounded-full bg-yellow-400/10 flex items-center justify-center text-yellow-400">
          <i class="fas fa-tools text-xl"></i>
        </div>
      </div>
      <div class="glass-card p-6 flex items-center justify-between">
        <div>
          <div class="text-gray-400 text-sm mb-1">Đã giải quyết</div>
          <div class="text-3xl font-bold text-emerald-400">{{ issues.filter(i => i.status === 'RESOLVED').length }}</div>
        </div>
        <div class="w-12 h-12 rounded-full bg-emerald-400/10 flex items-center justify-center text-emerald-400">
          <i class="fas fa-check-circle text-xl"></i>
        </div>
      </div>
    </div>

    <!-- Issues Grid -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary mb-4"></div>
      <p>Đang tải dữ liệu...</p>
    </div>

    <div v-else-if="issues.length === 0" class="text-center py-20 opacity-50">
      <i class="fas fa-clipboard-check text-6xl mb-4 text-primary"></i>
      <p class="text-xl">Không có sự cố nào!</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="issue in issues" 
        :key="issue.id" 
        class="glass-card p-6 relative group"
        :class="issue.status === 'RESOLVED' ? 'opacity-75' : ''"
      >
        <!-- Status Badge -->
        <div class="absolute top-4 right-4">
          <span class="status-badge" :class="getStatusBadgeClass(issue.status)">
            <span class="w-2 h-2 rounded-full bg-current animate-pulse"></span>
            {{ getStatusLabel(issue.status) }}
          </span>
        </div>

        <!-- Content -->
        <div class="mb-4">
          <div class="text-xs text-gray-500 font-mono mb-2">#{{ issue.id }} • {{ formatDate(issue.created_at) }}</div>
          <h3 class="text-lg font-bold text-white mb-2 line-clamp-2" :title="issue.content">
            {{ issue.content }}
          </h3>
          <div class="flex items-center gap-2 text-sm text-gray-400">
            <i class="fas fa-hdd opacity-50"></i>
            <span>{{ issue.machine?.name || 'N/A' }}</span>
          </div>
        </div>

        <!-- Footer / User -->
        <div class="pt-4 border-t border-white/5 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs">
               {{ (issue.user?.username || 'U')[0] }}
            </div>
            <div class="text-sm">
              <div class="text-gray-300">{{ issue.user?.full_name || 'Unknown' }}</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
              v-if="issue.status !== 'RESOLVED'"
              @click="updateStatus(issue, 'RESOLVED')" 
              class="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40 flex items-center justify-center transition"
              title="Đánh dấu đã xong"
            >
              <i class="fas fa-check"></i>
            </button>
            <button 
              @click="deleteItem(issue)" 
              class="w-8 h-8 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/40 flex items-center justify-center transition"
              title="Xóa báo cáo"
            >
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getIssues, updateIssueStatus, deleteIssue } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const issues = ref([])
const loading = ref(false)
const filterStatus = ref('')

// ... keep existing logic ...

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'OPEN': return 'open'
    case 'IN_PROGRESS': return 'progress'
    case 'RESOLVED': return 'resolved'
    default: return 'muted'
  }
}

const getStatusLabel = (status) => {
  switch (status) {
    case 'OPEN': return 'Mới (Open)'
    case 'IN_PROGRESS': return 'Đang xử lý'
    case 'RESOLVED': return 'Đã xong'
    case 'CLOSED': return 'Đóng'
    default: return status
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('vi-VN')
}

watch(filterStatus, () => fetchIssues())

onMounted(() => {
  fetchIssues()
})
</script>
