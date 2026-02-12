import client from './http'

export const usersApi = {
    // List all users (Admin only)
    list() {
        return client.get('/users')
    },

    // Create new user (Admin only)
    create(data) {
        return client.post('/users', data)
    },

    // Update user (Admin only)
    update(id, data) {
        return client.put(`/users/${id}`, data)
    },

    // Delete user (Admin only)
    delete(id) {
        return client.delete(`/users/${id}`)
    },

    // Reset Admin DB (Dev helper)
    resetAdminDb() {
        return client.post('/users/reset-admin-db')
    }
}
