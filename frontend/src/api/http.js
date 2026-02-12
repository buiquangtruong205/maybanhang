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

// Request interceptor: attach token
http.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor: extract data or handle errors
http.interceptors.response.use(
    (response) => response.data,
    (error) => {
        let message = 'Lỗi hệ thống không xác định'

        if (error.response) {
            // Server responded with error status
            message = error.response.data?.detail || `Lỗi máy chủ (${error.response.status})`
        } else if (error.request) {
            // Request made but no response received (Network Error)
            if (error.code === 'ECONNABORTED') message = 'Yêu cầu quá hạn (Timeout)'
            else if (error.message === 'Network Error') message = 'Không thể kết nối tới máy chủ. Vui lòng kiểm tra mạng.'
            else message = 'Máy chủ không phản hồi hoặc đang bảo trì'
        } else {
            message = error.message
        }

        console.error('[Lỗi API]', message)
        return Promise.reject(new Error(message))
    }
)

export default http
