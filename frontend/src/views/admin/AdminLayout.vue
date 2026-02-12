<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <h2>Hệ Thống Quản Trị</h2>
        <p>Máy Bán Hàng Tự Động V2</p>
      </div>

      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item" exact-active-class="active">
          <span v-html="item.icon" class="nav-icon" />
          {{ item.label }}
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-name">{{ userName }}</div>
        <button @click="logout" class="logout-btn" title="Đăng xuất">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="admin-main">
      <div class="admin-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const userName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.full_name || user.username || 'Admin'
  } catch { return 'Admin' }
})
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

const navItems = [
  { to: '/admin', label: 'Tổng quan', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>' },
  { to: '/admin/products', label: 'Sản phẩm', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>' },
  { to: '/admin/orders', label: 'Đơn hàng', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>' },
  { to: '/admin/machines', label: 'Máy', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>' },
  { to: '/admin/slots', label: 'Vị trí hàng', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>' },
  { to: '/admin/users', label: 'Thành viên', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>' },
]

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
  background: var(--color-surface-dark);
}

.admin-sidebar {
  width: 260px;
  background: var(--color-sidebar);
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.sidebar-header h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: white;
  letter-spacing: -0.01em;
}
.sidebar-header p {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
  margin-top: 0.25rem;
}

.sidebar-nav {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255,255,255,0.5);
  text-decoration: none;
  transition: all 0.2s;
}
.nav-item:hover {
  color: white;
  background: rgba(255,255,255,0.05);
}
.nav-item.active {
  color: var(--color-primary-light);
  background: rgba(var(--color-primary), 0.12);
  background: oklch(0.65 0.14 180 / 0.12);
}
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: oklch(0.65 0.14 180 / 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-light);
  font-size: 0.875rem;
  font-weight: 700;
}
.user-name {
  flex: 1;
  color: white;
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-btn {
  color: rgba(255,255,255,0.35);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
  min-height: auto;
  min-width: auto;
}
.logout-btn:hover { color: var(--color-danger); }

.admin-main {
  flex: 1;
  overflow: auto;
}
.admin-content {
  padding: 2rem;
  max-width: 80rem;
  margin: 0 auto;
}
</style>
