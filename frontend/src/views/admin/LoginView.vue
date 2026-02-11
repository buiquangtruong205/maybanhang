<template>
  <div class="login-page">
    <div class="login-wrapper">
      <div class="login-brand">
        <div class="brand-icon">
          <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
        </div>
        <h1>VM Admin</h1>
        <p>Đăng nhập để quản lý</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="error" class="login-error">{{ error }}</div>

        <div class="form-group">
          <label>Tên đăng nhập</label>
          <input v-model="username" type="text" required autofocus placeholder="admin" class="admin-input" />
        </div>

        <div class="form-group">
          <label>Mật khẩu</label>
          <input v-model="password" type="password" required placeholder="••••••" class="admin-input" />
        </div>

        <button type="submit" :disabled="loading" class="btn-primary login-btn">
          <svg v-if="loading" class="spin-icon" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          {{ loading ? 'Đang đăng nhập...' : 'Đăng nhập' }}
        </button>
      </form>

      <p class="login-back">
        <router-link to="/">← Quay lại trang khách hàng</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../../api/admin.js'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const data = await login(username.value, password.value)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    router.push('/admin')
  } catch (e) {
    error.value = e.message || 'Đăng nhập thất bại'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-surface-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.login-wrapper {
  width: 100%;
  max-width: 380px;
}
.login-brand {
  text-align: center;
  margin-bottom: 2rem;
}
.brand-icon {
  width: 64px;
  height: 64px;
  border-radius: 1.5rem;
  background: oklch(0.65 0.14 180 / 0.15);
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-light);
}
.login-brand h1 {
  font-size: 1.75rem;
  color: white;
}
.login-brand p {
  font-size: 0.875rem;
  color: rgba(255,255,255,0.4);
  margin-top: 0.25rem;
}
.login-form {
  background: var(--color-card);
  border-radius: 1.5rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.login-error {
  background: oklch(0.63 0.22 27 / 0.1);
  color: var(--color-danger);
  font-size: 0.875rem;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
}
.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255,255,255,0.5);
  margin-bottom: 0.375rem;
}
.login-btn {
  width: 100%;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
.spin-icon {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.login-back {
  text-align: center;
  margin-top: 1.5rem;
}
.login-back a {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.3);
  text-decoration: none;
  transition: color 0.2s;
}
.login-back a:hover { color: rgba(255,255,255,0.6); }
</style>
