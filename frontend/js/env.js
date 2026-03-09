/**
 * env.js — Biến môi trường Frontend (KHÔNG commit file này lên Git!)
 *
 * Sao chép từ env.example.js và điền giá trị thực tế.
 * File này đã được thêm vào .gitignore.
 */
const __ENV__ = {
    // Backend API URL — đổi thành IP/domain thực khi deploy
    VITE_API_BASE_URL: 'http://localhost:5000/api',

    // Machine key dùng để xác thực request từ máy bán hàng
    VITE_MACHINE_KEY: 'may1',

    // ID máy bán hàng này
    VITE_MACHINE_ID: 1,
};
