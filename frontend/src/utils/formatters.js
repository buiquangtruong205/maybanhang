/**
 * Định dạng tiền tệ VNĐ
 * @param {number} amount 
 * @returns {string} ví dụ: 10.000 đ
 */
export function formatCurrency(amount) {
    if (amount === undefined || amount === null) return '0 đ'
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
        maximumFractionDigits: 0
    }).format(amount).replace('₫', 'đ')
}

/**
 * Định dạng ngày giờ
 * @param {string|Date} dateString 
 * @returns {string} ví dụ: 12/02/2026 18:30
 */
export function formatDateTime(dateString) {
    if (!dateString) return ''
    const date = new Date(dateString)
    return new Intl.NumberFormat('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date).replace(',', '')
}

/**
 * Rút gọn chuỗi (ví dụ cho mã đơn hàng dài)
 * @param {string} str 
 * @param {number} len 
 */
export function truncateString(str, len = 8) {
    if (!str) return ''
    if (str.length <= len) return str
    return str.substring(0, len) + '...'
}
