import http from './http.js'

// --- Auth ---
export async function login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    const data = await http.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return data
}

export async function register(username, password, fullName = '') {
    return await http.post('/auth/register', { username, password, full_name: fullName })
}

// Reporting
export const getRevenueChart = async (period) => await http.get(`/stats/revenue-chart?period=${period}`)
export const getTopProducts = async (limit) => await http.get(`/stats/top-products?limit=${limit}`)
export const exportExcel = async () => {
    const blob = await http.get('/stats/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Bao_Cao_Don_Hang_${new Date().toISOString().slice(0, 10)}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

// --- Stats ---
export const getStats = async () => await http.get('/stats/')

// --- Products ---
export async function getProducts() {
    return await http.get('/products/')
}
export async function createProduct(data) {
    return await http.post('/products/', data)
}
export async function updateProduct(id, data) {
    return await http.put(`/products/${id}`, data)
}
export async function deleteProduct(id) {
    return await http.delete(`/products/${id}`)
}

// --- Machines ---
export async function getMachines() {
    return await http.get('/machines/')
}
export async function createMachine(data) {
    return await http.post('/machines/', data)
}
export async function updateMachine(id, data) {
    return await http.put(`/machines/${id}`, data)
}
export async function deleteMachine(id) {
    return await http.delete(`/machines/${id}`)
}

// --- Orders ---
export async function getOrders(params = {}) {
    let url = '/orders/?limit=50'
    if (params.status) url += `&status=${params.status}`
    return await http.get(url)
}
export async function manualConfirmOrder(orderCode) {
    return await http.post(`/orders/${orderCode}/manual-confirm`)
}

// --- Slots ---
export async function getSlots(params = {}) {
    let url = '/slots/'
    if (params.machine_id) url += `?machine_id=${params.machine_id}`
    return await http.get(url)
}
export async function createSlot(data) {
    return await http.post('/slots/', data)
}
export async function updateSlot(id, data) {
    return await http.put(`/slots/${id}`, data)
}
export async function deleteSlot(id) {
    return await http.delete(`/slots/${id}`)
}
export async function refillSlot(id) {
    return await http.post(`/slots/${id}/refill`)
}

// --- Issues ---
export async function getIssues(params = {}) {
    let url = '/issues/'
    if (params.status) url += `?status=${params.status}`
    return await http.get(url)
}
export async function createIssue(data) {
    return await http.post('/issues/', data)
}
export async function updateIssueStatus(id, status) {
    return await http.put(`/issues/${id}`, { status })
}

// --- System Settings ---
export async function getSettings() {
    return await http.get('/settings/')
}
export async function updateSetting(key, value) {
    return await http.put(`/settings/${key}`, { value })
}
export async function restoreDefaultSettings() {
    return await http.post('/settings/restore-defaults')
}
