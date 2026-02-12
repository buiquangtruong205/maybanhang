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

// --- Helper: auth header ---
function authHeader() {
    const token = localStorage.getItem('token')
    return token ? { headers: { Authorization: `Bearer ${token}` } } : {}
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
export const getStats = async () => await http.get('/stats/', authHeader())

// --- Products ---
export async function getProducts() {
    return await http.get('/products/')
}
export async function createProduct(data) {
    return await http.post('/products/', data, authHeader())
}
export async function updateProduct(id, data) {
    return await http.put(`/products/${id}`, data, authHeader())
}
export async function deleteProduct(id) {
    return await http.delete(`/products/${id}`, authHeader())
}

// --- Machines ---
export async function getMachines() {
    return await http.get('/machines/')
}
export async function createMachine(data) {
    return await http.post('/machines/', data, authHeader())
}
export async function updateMachine(id, data) {
    return await http.put(`/machines/${id}`, data, authHeader())
}
export async function deleteMachine(id) {
    return await http.delete(`/machines/${id}`, authHeader())
}

// --- Orders ---
export async function getOrders(params = {}) {
    let url = '/orders/?limit=50'
    if (params.status) url += `&status=${params.status}`
    return await http.get(url, authHeader())
}

// --- Slots ---
export async function getSlots(params = {}) {
    let url = '/slots/'
    if (params.machine_id) url += `?machine_id=${params.machine_id}`
    return await http.get(url)
}
export async function createSlot(data) {
    return await http.post('/slots/', data, authHeader())
}
export async function updateSlot(id, data) {
    return await http.put(`/slots/${id}`, data, authHeader())
}
export async function deleteSlot(id) {
    return await http.delete(`/slots/${id}`, authHeader())
}
