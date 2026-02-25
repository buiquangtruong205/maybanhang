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
        <button @click="fetchIssues" class="btn-secondary flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          Làm mới
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
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        </div>
      </div>
      <div class="glass-card p-6 flex items-center justify-between">
        <div>
          <div class="text-gray-400 text-sm mb-1">Đã giải quyết</div>
          <div class="text-3xl font-bold text-emerald-400">{{ issues.filter(i => i.status === 'RESOLVED').length }}</div>
        </div>
        <div class="w-12 h-12 rounded-full bg-emerald-400/10 flex items-center justify-center text-emerald-400">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
      </div>
    </div>

    <!-- Issues Grid -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary mb-4"></div>
      <p>Đang tải dữ liệu...</p>
    </div>

    <div v-else-if="issues.length === 0" class="text-center py-20 opacity-50">
      <svg class="w-16 h-16 mb-4 text-primary mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
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
            <svg class="w-4 h-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"/></svg>
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
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
            </button>
            <button 
              @click="deleteItem(issue)" 
              class="w-8 h-8 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/40 flex items-center justify-center transition"
              title="Xóa báo cáo"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
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
