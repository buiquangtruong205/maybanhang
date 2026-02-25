<template>
  <!-- Header: Phần đầu trang chứa tiêu đề và trạng thái máy -->
  <header class="home-header animate-fade-in shadow-sm">
    <div class="header-left">
      <!-- Icon ứng dụng - Double click để vào trang quản trị (Admin) -->
      <div 
        class="header-icon cursor-pointer transition-transform active:scale-95" 
        @dblclick="$emit('admin-click')" 
        title="Nhấp đúp để vào Admin"
      >
        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
      </div>
      <div class="header-text">
        <h1 class="text-xl font-bold text-slate-800 tracking-tight">Máy Bán Hàng Tự Động</h1>
        <p class="text-sm text-slate-500 font-medium">Chọn sản phẩm yêu thích của bạn</p>
      </div>
    </div>
    
    <!-- Chỉ báo trạng thái Online/Offline của máy -->
    <div class="status-indicator flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
      <span class="status-dot w-2 h-2 rounded-full" :class="isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'" />
      <span class="text-sm font-semibold" :class="isOnline ? 'text-green-600' : 'text-red-600'">
        {{ isOnline ? 'Đang hoạt động' : 'Đang Ngoại tuyến' }}
      </span>
    </div>
  </header>
</template>

<script setup>
/**
 * Header Component
 * Hiển thị tiêu đề ứng dụng và trạng thái kết nối của máy bán hàng.
 */
defineProps({
  isOnline: {
    type: Boolean,
    default: true
  }
})

defineEmits(['admin-click'])
</script>

<style scoped>
.home-header {
  max-width: 72rem;
  margin: 0 auto 2rem;
  background: white;
  border-radius: 1.25rem;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  border-radius: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px oklch(0.65 0.14 180 / 0.2);
}

.status-dot {
  box-shadow: 0 0 8px currentColor;
}
</style>
