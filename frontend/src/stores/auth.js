import { defineStore } from 'pinia'
import { login as apiLogin } from '../api/admin.js'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: JSON.parse(localStorage.getItem('user')) || null,
        token: localStorage.getItem('token') || null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 'ADMIN',
        isStaff: (state) => state.user?.role === 'STAFF',
        currentUser: (state) => state.user
    },

    actions: {
        async login(username, password) {
            try {
                const data = await apiLogin(username, password)
                this.token = data.access_token
                this.user = data.user

                localStorage.setItem('token', this.token)
                localStorage.setItem('user', JSON.stringify(this.user))

                return { success: true }
            } catch (error) {
                return { success: false, error: error.message }
            }
        },

        logout() {
            this.token = null
            this.user = null
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            // Chuyển hướng về login sẽ được xử lý ở router hoặc component gọi hàm này
        }
    }
})
