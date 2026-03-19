/**
 * env.example.js — Template biến môi trường Frontend
 *
 * Hướng dẫn:
 *   1. Sao chép file này thành `env.js` (cùng thư mục)
 *   2. Điền giá trị thực tế vào env.js
 *   3. KHÔNG chỉnh sửa file này với giá trị thật — nó được commit lên Git
 */
const __ENV__ = {
    // Backend API URL — ví dụ: 'http://192.168.1.100:5000/api'
    VITE_API_BASE_URL: 'https://maybanhang-o9t8.onrender.com/api',

    // Machine key — phải khớp với MACHINE_KEYS trong backend .env
    VITE_MACHINE_KEY: 'maybanhang-v3',

    // ID máy bán hàng (số nguyên)
    VITE_MACHINE_ID: 3,
};
