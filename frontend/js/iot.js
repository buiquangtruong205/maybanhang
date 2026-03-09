/**
 * iot.js — Nhật ký thiết bị IoT và kiểm tra định danh / phiên
 * Phụ thuộc: config.js (CONFIG), api.js
 */

// ===========================
// Log Panel
// ===========================

/**
 * In một dòng log vào panel IoT.
 * @param {string|object} message
 * @param {boolean}       isError
 */
function iotLog(message, isError = false) {
    const logContent = document.getElementById('log-content');
    if (!logContent) return;

    const time = new Date().toLocaleTimeString('vi-VN');
    const entry = document.createElement('div');
    entry.className = `log-entry ${isError ? 'log-error' : 'log-success'}`;

    const display = typeof message === 'object'
        ? '<pre>' + JSON.stringify(message, null, 2) + '</pre>'
        : message;

    entry.innerHTML = `<span class="log-time">[${time}]</span> ${display}`;
    logContent.insertBefore(entry, logContent.firstChild);

    // Giữ tối đa LOG_MAX_ENTRIES dòng
    while (logContent.children.length > CONFIG.LOG_MAX_ENTRIES) {
        logContent.removeChild(logContent.lastChild);
    }
}

// ===========================
// Device Checks
// ===========================

/** Kiểm tra định danh thiết bị */
async function checkDeviceIdentity() {
    iotLog('🔍 Đang kiểm tra định danh thiết bị...');
    try {
        const result = await apiRegisterDevice();
        if (result.success) {
            iotLog('✅ Định danh thiết bị: Đang hoạt động');
            iotLog(result.data);
            apiUploadLog('info', 'Kiểm tra định danh: Thành công', result.data);
        } else {
            iotLog(`❌ Kiểm tra định danh thất bại: ${result.message}`, true);
            apiUploadLog('error', `Kiểm tra định danh thất bại: ${result.message}`);
        }
    } catch (err) {
        iotLog(`❌ Lỗi: ${err.message}`, true);
        apiUploadLog('error', `Lỗi kiểm tra định danh: ${err.message}`);
    }
}

/** Kiểm tra / làm mới phiên thiết bị */
async function checkDeviceSession() {
    iotLog('🔑 Đang kiểm tra phiên làm việc...');
    try {
        const result = await apiSendHeartbeat();
        if (result.success) {
            iotLog(`✅ Phiên hợp lệ: ID ${result.data.session_id}`);
            iotLog(`   Giờ máy chủ: ${result.data.server_time}`);
            apiUploadLog('info', 'Kiểm tra phiên: Hợp lệ', result.data);
        } else {
            iotLog(`❌ Kiểm tra phiên thất bại: ${result.message}`, true);
            apiUploadLog('error', `Kiểm tra phiên thất bại: ${result.message}`);
        }
    } catch (err) {
        iotLog(`❌ Lỗi: ${err.message}`, true);
        apiUploadLog('error', `Lỗi kiểm tra phiên: ${err.message}`);
    }
}

/** Gửi Heartbeat thủ công (wrapper) */
async function sendHeartbeat() {
    iotLog('💓 Đang gửi Heartbeat...');
    checkDeviceSession();
}
