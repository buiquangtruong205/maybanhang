<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="brand">VM Admin v2</h2>
      </div>
      
      <nav class="sidebar-nav">
        <router-link to="/admin/dashboard" class="nav-item">
          <span class="icon">📊</span> Tổng quan
        </router-link>
        <router-link to="/admin/products" class="nav-item">
          <span class="icon">🛒</span> Sản phẩm
        </router-link>
        <router-link to="/admin/machines" class="nav-item">
          <span class="icon">📠</span> Máy bán hàng
        </router-link>
        <router-link to="/admin/orders" class="nav-item">
          <span class="icon">📜</span> Đơn hàng
        </router-link>
        <router-link to="/admin/users" class="nav-item">
          <span class="icon">👤</span> Người dùng
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button class="btn-logout" @click="handleLogout">Đăng xuất</button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <header class="top-header">
        <div class="breadcrumb">
          Admin / {{ $route.meta.title || 'Trang chủ' }}
        </div>
        <div class="user-profile">
          Quản trị viên
        </div>
      </header>
      
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function handleLogout() {
  // logic logout
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg, #0f172a);
  color: white;
}

.sidebar {
  width: 260px;
  background: var(--color-sidebar, #1e293b);
  border-right: 1px solid rgba(255,255,255,0.05);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.brand { font-size: 1.25rem; font-weight: 700; margin: 0; color: var(--color-primary); }

.sidebar-nav {
  padding: 1.5rem 1rem;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: rgba(255,255,255,0.6);
  text-decoration: none;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  transition: all 0.2s;
}

.nav-item:hover, .router-link-active {
  background: rgba(255,255,255,0.05);
  color: white;
}

.router-link-active {
  border-left: 3px solid var(--color-primary);
}

.sidebar-footer { padding: 1.5rem; }

.btn-logout {
  width: 100%;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 0.5rem;
  cursor: pointer;
}

.main-content { flex: 1; display: flex; flex-direction: column; }

.top-header {
  height: 64px;
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
}

.content-wrapper { padding: 2rem; flex: 1; overflow-y: auto; }
</style>
