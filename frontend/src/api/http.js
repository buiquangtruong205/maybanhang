import axios from 'axios'

/**
 * Axios HTTP client configured for V2 Backend.
 * Uses Vite proxy (/api → http://127.0.0.1:5001/api)
 */
const http = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Response interceptor: extract data or handle errors
http.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'Lỗi kết nối'
        console.error('[API Error]', message)
        return Promise.reject(new Error(message))
    }
)

export default http
