// API Configuration
const API_BASE = '/api';
let token = localStorage.getItem('token');
let currentUser = null;

// Products, Machines, Slots and Users cache for lookups
let productsCache = [];
let machinesCache = [];
let slotsCache = [];
let usersCache = [];

// XSS Protection: Escape HTML special characters
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Stub function for removed Firmware OTA feature
// Load Firmware Updates
async function loadFirmware() {
    const data = await apiCall('/firmware/updates');
    if (data.success) {
        renderFirmwareUpdates(data.data);
    }
}

function renderFirmwareUpdates(updates) {
    const tbody = document.getElementById('deviceFirmwareTable');
    if (!tbody) return;

    tbody.innerHTML = updates.map(u => `
        <tr>
            <td>${u.update_id}</td>
            <td>${u.machine_id}</td>
            <td>${u.from_version} ➝ <b>${u.to_version}</b></td>
            <td><span class="status status-${u.status}">${u.status}</span></td>
            <td>${formatDate(u.deployed_at)}</td>
            <td>${formatDate(u.completed_at)}</td>
        </tr>
    `).join('');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        checkAuth();
    } else {
        showLogin();
    }

    setupEventListeners();
});

function setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Register form (chỉ dùng lần đầu)
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Data form
    document.getElementById('dataForm').addEventListener('submit', handleFormSubmit);
}

// Auth functions
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            token = data.data.access_token;
            localStorage.setItem('token', token);
            currentUser = { username };
            showApp();
            showToast('Đăng nhập thành công!', 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;

    try {
        const res = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            showToast('Đăng ký tài khoản thành công!', 'success');

            // Tự động đăng nhập với tài khoản vừa tạo
            const loginRes = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const loginData = await loginRes.json();

            if (loginData.success) {
                token = loginData.data.access_token;
                localStorage.setItem('token', token);
                currentUser = { username };
                showApp();
                showToast('Đăng ký hoàn tất! 🎉', 'success');
            } else {
                showToast(loginData.message, 'error');
            }
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        console.error('Error during registration:', err);
        showToast('Lỗi kết nối server', 'error');
    }
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.success) {
            currentUser = data.data;
            showApp();
        } else {
            logout();
        }
    } catch (err) {
        logout();
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    showLogin();
}

function showLogin() {
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('registerModal').style.display = 'none';
    document.getElementById('app').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('registerModal').style.display = 'flex';
}

/**
 * Try to show register page
 * Check if user already exists, show error if yes, show register form if no
 */
async function tryShowRegister() {
    try {
        const res = await fetch(`${API_BASE}/users/count`);
        const data = await res.json();

        if (data.success && data.count > 0) {
            // Already has user - show error message
            showToast('Bạn không thể tạo tài khoản do chính sách của web. Hệ thống chỉ cho phép 1 tài khoản.', 'error');
        } else {
            // No users - show register form
            showRegister();
        }
    } catch (err) {
        console.error('Error checking user count:', err);
        showToast('Lỗi kết nối server', 'error');
    }
}

function showApp() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('registerModal').style.display = 'none';
    document.getElementById('app').style.display = 'block';
    document.getElementById('currentUser').textContent = `👤 ${currentUser?.username || 'User'}`;
    loadAllData();
    initAdminWebSocket();
}

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

// Sub-tab switching for devices
function switchDeviceTab(tabName) {
    document.querySelectorAll('#devices .sub-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#devices .sub-tab-content').forEach(c => c.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(`device-${tabName}`).classList.add('active');
}

// Sub-tab switching for security
function switchSecurityTab(tabName) {
    document.querySelectorAll('#security .sub-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#security .sub-tab-content').forEach(c => c.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(`security-${tabName}`).classList.add('active');
}

// Load all data
async function loadAllData() {
    await Promise.all([
        loadStats(),
        loadMachines(),
        loadProducts(),
        loadSlots(),
        loadOrders(),
        loadTransactions(),
        loadFirmware(),
        loadUsers(),
        loadAdminLogs()
    ]);

    // Populate telemetry machine filter
    const filter = document.getElementById('telemetryMachineFilter');
    if (filter && machinesCache.length > 0) {
        filter.innerHTML = '<option value="">-- Tất cả máy --</option>' +
            machinesCache.map(m => `<option value="${m.machine_id}">${m.name}</option>`).join('');
    }
}

// Load statistics
async function loadStats() {
    const data = await apiCall('/stats');
    if (data.success) {
        const stats = data.data;

        // Doanh thu
        document.getElementById('statRevenue').textContent = formatPrice(stats.monthly_revenue);

        // Sản phẩm bán chạy nhất
        document.getElementById('statBestProduct').textContent = stats.best_product.product_name || '-';
        if (stats.best_product.total_sold > 0) {
            document.getElementById('statBestProductSold').textContent = `${stats.best_product.total_sold} đã bán`;
        }

        // Người mua nhiều nhất
        document.getElementById('statTopCustomer').textContent = stats.top_customer.sender_bank;
        if (stats.top_customer.transaction_count > 0) {
            document.getElementById('statTopCustomerCount').textContent =
                `${stats.top_customer.transaction_count} giao dịch - ${formatPrice(stats.top_customer.total_amount)}`;
        }

        // Tổng đơn hàng
        document.getElementById('statTotalOrders').textContent = stats.total_orders;
    }
}

// API calls
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    if (body) options.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${endpoint}`, options);
    return await res.json();
}

// Load functions
async function loadMachines() {
    const data = await apiCall('/machines');
    if (data.success) {
        machinesCache = data.data;
        renderMachines(data.data);
    }
}

async function loadProducts() {
    const data = await apiCall('/products');
    if (data.success) {
        productsCache = data.data;
        renderProducts(data.data);
    }
}

async function loadSlots() {
    const data = await apiCall('/slots');
    if (data.success) {
        slotsCache = data.data;
        renderSlots(data.data);
    }
}

async function loadOrders() {
    const data = await apiCall('/orders');
    if (data.success) {
        renderOrders(data.data);
    }
}

async function loadTransactions() {
    const data = await apiCall('/transactions');
    if (data.success) {
        renderTransactions(data.data);
    }
}

async function loadUsers() {
    const data = await apiCall('/users');
    if (data.success) {
        usersCache = data.data;
    }
}

async function loadAdminLogs() {
    // Tải Stats
    const statsData = await apiCall('/admin-logs/stats');
    if (statsData.success) {
        document.getElementById('statAdminTotal').textContent = statsData.data.total_actions;
        document.getElementById('statAdminLogins').textContent = statsData.data.logins;
        document.getElementById('statAdminUpdates').textContent = statsData.data.updates;
        document.getElementById('statAdminFailed').textContent = statsData.data.login_failed;
    }

    // Tải danh sách filter
    const actionFilter = document.getElementById('adminActionFilter')?.value || '';
    const typeFilter = document.getElementById('adminTypeFilter')?.value || '';

    let url = '/admin-logs?per_page=100';
    if (actionFilter) url += `&action=${actionFilter}`;
    if (typeFilter) url += `&target_type=${typeFilter}`;

    const logsData = await apiCall(url);
    if (logsData.success) {
        renderAdminLogs(logsData.data);
    }
}



// Render functions
function renderMachines(machines) {
    const tbody = document.getElementById('machinesTable');
    tbody.innerHTML = machines.map(m => {
        const itemJson = escapeHtml(JSON.stringify(m));
        const statusClass = m.status === 'active' ? 'active' : (m.status === 'maintenance' ? 'warning' : 'inactive');
        const wifiClass = m.wifi_status === 'connected' ? 'active' : 'inactive';
        
        return `
        <tr>
            <td class="id-column">${m.machine_id}</td>
            <td>${m.name}</td>
            <td>${m.location || '-'}</td>
            <td class="table-align-center"><span class="status status-${wifiClass}">${m.wifi_signal || (m.wifi_status === 'connected' ? 'ON' : 'OFF')}</span></td>
            <td class="table-align-center"><code>${m.uptime || '-'}</code></td>
            <td class="table-align-center"><span class="status status-${statusClass}">${m.status}</span></td>
            <td class="table-align-center">
                <div class="control-actions">
                    <button class="btn btn-control btn-unlock" title="Mở khóa" onclick="sendMachineCommand(${m.machine_id}, 'UNLOCK')">🔓</button>
                    <button class="btn btn-control btn-reboot" title="Reboot" onclick="sendMachineCommand(${m.machine_id}, 'REBOOT')">🔄</button>
                    <button class="btn btn-control btn-test" title="Test Motor" onclick="sendMachineCommand(${m.machine_id}, 'TEST_MOTOR')">⚙️</button>
                </div>
            </td>
            <td class="table-align-center">
                <div class="actions">
                    <button class="btn btn-edit" onclick='editItem("machine", ${itemJson})'>Sửa</button>
                    <button class="btn btn-delete" onclick="deleteItem('machine', ${m.machine_id})">Xóa</button>
                </div>
            </td>
        </tr>
    `;
    }).join('');
}

async function sendMachineCommand(machineId, command) {
    if (!confirm(`Bạn có chắc muốn gửi lệnh ${command} tới máy #${machineId}?`)) return;
    
    showToast(`Đang gửi lệnh ${command}...`, 'info');
    const result = await apiCall(`/machines/${machineId}/control`, 'POST', { command });
    if (result.success) {
        showToast(result.message, 'success');
    } else {
        showToast(result.message || 'Lỗi gửi lệnh', 'error');
    }
}

function renderProducts(products) {
    const tbody = document.getElementById('productsTable');
    tbody.innerHTML = products.map(p => {
        const itemJson = escapeHtml(JSON.stringify(p));
        const productName = p.product_name || p.name || '';
        return `
        <tr>
            <td class="id-column">${p.product_id}</td>
            <td class="table-align-center">${productName}</td>
            <td>${formatPrice(p.price)}</td>
            <td class="product-image-cell table-align-center">
                ${p.image
                ? `<img src="${p.image}" alt="${escapeHtml(productName)}" class="product-thumbnail" onclick="showImagePreview('${escapeHtml(p.image)}')">`
                : '<span class="no-image">📷 Chưa có ảnh</span>'
            }
            </td>
            <td class="table-align-center"><span class="status status-${p.active}">${p.active ? 'Hoạt động' : 'Ngưng'}</span></td>
            <td class="table-align-center">
                <div class="actions">
                    <button class="btn btn-edit" onclick='editItem("product", ${itemJson})'>Sửa</button>
                    <button class="btn btn-delete" onclick="deleteItem('product', ${p.product_id})">Xóa</button>
                </div>
            </td>
        </tr>
    `;
    }).join('');
}

function renderSlots(slots) {
    const tbody = document.getElementById('slotsTable');
    tbody.innerHTML = slots.map(s => {
        const machine = machinesCache.find(m => m.machine_id === s.machine_id);
        const product = productsCache.find(p => p.product_id === s.product_id);
        const productName = product?.product_name || product?.name || '-';
        const itemJson = escapeHtml(JSON.stringify(s));
        return `
            <tr>
                <td class="id-column">${s.slot_id}</td>
                <td class="table-align-center">${machine?.name || s.machine_id}</td>
                <td class="table-align-center"><code>${s.slot_code}</code></td>
                <td class="table-align-center">${productName}</td>
                <td class="table-align-center">${s.stock}</td>
                <td class="table-align-center">${s.capacity}</td>
                <td class="table-align-center">
                    <div class="actions">
                        <button class="btn btn-edit" onclick='editItem("slot", ${itemJson})'>Sửa</button>
                        <button class="btn btn-delete" onclick="deleteItem('slot', ${s.slot_id})">Xóa</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function renderOrders(orders) {
    const tbody = document.getElementById('ordersTable');
    const sortedOrders = [...orders].sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB - dateA;
    });

    tbody.innerHTML = sortedOrders.map(o => {
        const product = productsCache.find(p => p.product_id === o.product_id);
        const productName = product?.product_name || product?.name || o.product_id;
        const slot = slotsCache.find(s => s.slot_id === o.slot_id);
        return `
            <tr>
                <td class="id-column">${o.order_id}</td>
                <td class="table-align-center">${productName}</td>
                <td class="table-align-center">${formatPrice(o.price_snapshot)}</td>
                <td class="table-align-center"><code>${slot?.slot_code || o.slot_id}</code></td>
                <td class="table-align-center"><span class="status status-${o.status_payment}">${o.status_payment}</span></td>
                <td class="table-align-center"><span class="status status-${o.status_slots}">${o.status_slots}</span></td>
                <td class="table-align-center">${formatDate(o.created_at)}</td>
            </tr>
        `;
    }).join('');
}

function renderTransactions(transactions) {
    const tbody = document.getElementById('transactionsTable');
    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td class="id-column">${t.transaction_id}</td>
            <td class="table-align-center">${t.order_id}</td>
            <td class="table-align-center">${formatPrice(t.amount)}</td>
            <td class="table-align-center"><code>${t.bank_trans_id || '-'}</code></td>
            <td class="table-align-center">${formatDate(t.created_at)}</td>
            <td>${t.description || '-'}</td>
            <td class="table-align-center"><span class="status status-${t.status}">${t.status}</span></td>
        </tr>
    `).join('');
}

function renderAdminLogs(logs) {
    const tbody = document.getElementById('adminLogsTable');
    if (!tbody) return;

    tbody.innerHTML = logs.map(l => {
        let userDisplay = l.user_id || 'Khách/Hệ thống';
        if (l.user_id) {
            const user = usersCache.find(u => u.user_id === l.user_id);
            if (user) userDisplay = `${user.username} (${l.user_id})`;
        }

        let actionClass = 'secondary';
        if (l.action.includes('login')) actionClass = l.action === 'login_failed' ? 'error' : 'success';
        else if (l.action.includes('create')) actionClass = 'primary';
        else if (l.action.includes('delete')) actionClass = 'error';
        else if (l.action.includes('update')) actionClass = 'warning';

        return `
            <tr>
                <td class="id-column">${l.log_id}</td>
                <td>${escapeHtml(userDisplay.toString())}</td>
                <td class="table-align-center"><span class="status status-${actionClass}">${escapeHtml(l.action)}</span></td>
                <td>${escapeHtml(l.detail || '-')}</td>
                <td class="table-align-center">${l.target_type ? escapeHtml(l.target_type) + ' #' + l.target_id : '-'}</td>
                <td class="table-align-center"><code>${escapeHtml(l.ip_address || '-')}</code></td>
                <td class="table-align-center">${formatDate(l.created_at)}</td>
            </tr>
        `;
    }).join('');
}



// Action handlers for new features
async function revokeDeviceIdentity(machineId) {
    if (!confirm('Bạn có chắc muốn thu hồi định danh thiết bị này?')) return;
    const result = await apiCall(`/devices/identity/${machineId}/revoke`, 'PUT');
    if (result.success) {
        showToast('Đã thu hồi định danh thiết bị!', 'success');
        loadDeviceIdentities();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

async function revokeSession(sessionId) {
    if (!confirm('Bạn có chắc muốn thu hồi session này?')) return;
    const result = await apiCall(`/devices/sessions/${sessionId}/revoke`, 'PUT');
    if (result.success) {
        showToast('Đã thu hồi session!', 'success');
        loadDeviceSessions();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

async function resolveSecurityEvent(eventId) {
    const result = await apiCall(`/security/events/${eventId}/resolve`, 'PUT');
    if (result.success) {
        showToast('Đã đánh dấu đã xử lý!', 'success');
        loadSecurityEvents();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

async function endAccessLog(accessId) {
    const note = prompt('Ghi chú khi kết thúc (tùy chọn):');
    const result = await apiCall(`/security/access-logs/${accessId}/end`, 'PUT', { note });
    if (result.success) {
        showToast('Đã kết thúc phiên truy cập!', 'success');
        loadAccessLogs();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

async function deleteFirmwareUpdate(updateId) {
    if (!confirm('Bạn có chắc muốn xóa cập nhật này?')) return;
    const result = await apiCall(`/firmware/updates/${updateId}`, 'DELETE');
    if (result.success) {
        showToast('Đã xóa cập nhật firmware!', 'success');
        loadFirmware();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

// Form handling
let currentFormType = null;
let currentEditId = null;

function showAddModal(type) {
    currentFormType = type;
    currentEditId = null;
    document.getElementById('formModalTitle').textContent = getFormTitle(type, false);
    document.getElementById('formFields').innerHTML = getFormFields(type, null);
    document.getElementById('formModal').style.display = 'flex';
}

function editItem(type, item) {
    currentFormType = type;
    // Lấy đúng ID theo loại
    if (type === 'machine') currentEditId = item.machine_id;
    else if (type === 'product') currentEditId = item.product_id;
    else if (type === 'slot') currentEditId = item.slot_id;
    else currentEditId = item.id;

    document.getElementById('formModalTitle').textContent = getFormTitle(type, true);
    document.getElementById('formFields').innerHTML = getFormFields(type, item);
    document.getElementById('formModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('formModal').style.display = 'none';
}

function getFormTitle(type, isEdit) {
    const titles = {
        machine: isEdit ? 'Sửa máy bán hàng' : 'Thêm máy bán hàng',
        product: isEdit ? 'Sửa sản phẩm' : 'Thêm sản phẩm',
        slot: isEdit ? 'Sửa khe hàng' : 'Thêm khe hàng',
        import: 'Nhập hàng vào kho',
        firmware: 'Tạo cập nhật Firmware',
        accessLog: 'Ghi nhận truy cập'
    };
    return titles[type] || 'Thêm mới';
}

function getFormFields(type, item) {
    switch (type) {
        case 'machine':
            return `
                <div class="form-group">
                    <label>Tên máy</label>
                    <input type="text" name="name" value="${item?.name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Vị trí</label>
                    <input type="text" name="location" value="${item?.location || ''}">
                </div>
                <div class="form-group">
                    <label>Trạng thái</label>
                    <select name="status">
                        <option value="active" ${item?.status === 'active' ? 'selected' : ''}>Hoạt động</option>
                        <option value="inactive" ${item?.status === 'inactive' ? 'selected' : ''}>Ngưng</option>
                        <option value="maintenance" ${item?.status === 'maintenance' ? 'selected' : ''}>Bảo trì</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Secret Key</label>
                    <input type="text" name="secret_key" value="${item?.secret_key || ''}">
                </div>
            `;
        case 'product':
            const productName = item?.product_name || item?.name || '';
            return `
                <div class="form-group">
                    <label>Tên sản phẩm</label>
                    <input type="text" name="product_name" value="${productName}" required>
                </div>
                <div class="form-group">
                    <label>Giá</label>
                    <input type="number" name="price" value="${item?.price || ''}" required>
                </div>
                <div class="form-group">
                    <label>Ảnh sản phẩm</label>
                    <div class="image-source-tabs ${item?.image ? 'hidden' : ''}">
                        <button type="button" class="image-tab active" onclick="switchImageTab('file')">📁 Chọn từ máy</button>
                        <button type="button" class="image-tab" onclick="switchImageTab('url')">🔗 Nhập URL</button>
                    </div>
                    <div class="image-upload-container">
                        <input type="file" id="imageFile" accept="image/*" onchange="previewImage(this)" style="display:none">
                        <input type="hidden" name="image" id="imageUrl" value="${item?.image || ''}">
                        
                        <div id="fileUploadArea" class="upload-area ${item?.image ? 'hidden' : ''}" onclick="document.getElementById('imageFile').click()">
                            <span class="upload-icon">📁</span>
                            <span>Click để chọn ảnh từ máy</span>
                        </div>
                        
                        <div id="urlInputArea" class="url-input-area hidden">
                            <input type="text" id="imageUrlInput" placeholder="https://example.com/image.jpg" value="${item?.image || ''}" onchange="previewUrlImage(this.value)">
                        </div>
                        
                        <div id="imagePreviewContainer" class="${item?.image ? '' : 'hidden'}">
                            <img id="formImagePreview" src="${item?.image || ''}" alt="Preview" class="image-preview">
                            <button type="button" class="btn-remove-image" onclick="removeImage()">✕</button>
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label>Trạng thái</label>
                    <select name="active">
                        <option value="true" ${item?.active !== false ? 'selected' : ''}>Hoạt động</option>
                        <option value="false" ${item?.active === false ? 'selected' : ''}>Ngưng</option>
                    </select>
                </div>
            `;
        case 'slot':
            return `
                <div class="form-group">
                    <label>Máy bán hàng</label>
                    <select name="machine_id" required>
                        ${machinesCache.map(m => `<option value="${m.machine_id}" ${item?.machine_id === m.machine_id ? 'selected' : ''}>${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Mã khe</label>
                    <input type="text" name="slot_code" value="${item?.slot_code || ''}" required>
                </div>
                <div class="form-group">
                    <label>Sản phẩm</label>
                    <select name="product_id">
                        <option value="">-- Không có --</option>
                        ${productsCache.map(p => `<option value="${p.product_id}" ${item?.product_id === p.product_id ? 'selected' : ''}>${p.product_name || p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Tồn kho</label>
                    <input type="number" name="stock" value="${item?.stock || 0}" required>
                </div>
                <div class="form-group">
                    <label>Sức chứa</label>
                    <input type="number" name="capacity" value="${item?.capacity || 10}" required>
                </div>
            `;
        case 'import':
            return `
                <div class="form-group">
                    <label>Máy bán hàng</label>
                    <select name="machine_id" id="importMachine" required onchange="filterSlotsForImport()">
                        <option value="">-- Chọn máy --</option>
                        ${machinesCache.map(m => `<option value="${m.machine_id}">${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Khe hàng</label>
                    <select name="slot_id" id="importSlot" required>
                        <option value="">-- Chọn khe --</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Sản phẩm</label>
                    <select name="product_id" required>
                        ${productsCache.map(p => `<option value="${p.product_id}">${p.product_name || p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Số lượng nhập</label>
                    <input type="number" name="quantity" min="1" value="1" required>
                </div>
                <input type="hidden" name="user_id" value="${currentUser?.user_id || 1}">
            `;
        case 'firmware':
            return `
                <div class="form-group">
                    <label>Máy bán hàng</label>
                    <select name="machine_id" required>
                        ${machinesCache.map(m => `<option value="${m.machine_id}">${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Từ version</label>
                    <input type="text" name="from_version" placeholder="1.0.0">
                </div>
                <div class="form-group">
                    <label>Đến version</label>
                    <input type="text" name="to_version" required placeholder="1.1.0">
                </div>
                <div class="form-group">
                    <label>Checksum</label>
                    <input type="text" name="checksum" placeholder="MD5/SHA256">
                </div>
            `;
        case 'accessLog':
            return `
                <div class="form-group">
                    <label>Máy bán hàng</label>
                    <select name="machine_id" required>
                        ${machinesCache.map(m => `<option value="${m.machine_id}">${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Hành động</label>
                    <select name="action" required>
                        <option value="open">Mở máy</option>
                        <option value="close">Đóng máy</option>
                        <option value="refill">Nhập hàng</option>
                        <option value="maintenance">Bảo trì</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Ghi chú</label>
                    <textarea name="note" rows="3"></textarea>
                </div>
                <input type="hidden" name="user_id" value="${currentUser?.user_id || 1}">
            `;
        default:
            return '';
    }
}

function filterSlotsForImport() {
    const machineId = document.getElementById('importMachine').value;
    const slotSelect = document.getElementById('importSlot');
    const filteredSlots = slotsCache.filter(s => s.machine_id == machineId);

    slotSelect.innerHTML = '<option value="">-- Chọn khe --</option>' +
        filteredSlots.map(s => `<option value="${s.slot_id}">${s.slot_code}</option>`).join('');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {};

    formData.forEach((value, key) => {
        if (key === 'active') {
            data[key] = value === 'true';
        } else if (['price', 'stock', 'capacity', 'machine_id', 'slot_id', 'product_id', 'quantity', 'user_id'].includes(key)) {
            data[key] = value ? parseInt(value) : null;
        } else {
            data[key] = value;
        }
    });

    // Validate số lượng tồn kho không vượt quá sức chứa (slot)
    if (currentFormType === 'slot') {
        // Kiểm tra trùng mã khe trên cùng một máy
        const isDuplicate = slotsCache.some(s =>
            s.machine_id == data.machine_id &&
            s.slot_code == data.slot_code &&
            s.slot_id != currentEditId
        );
        if (isDuplicate) {
            showToast('Khe đã có sản phẩm', 'error');
            return;
        }

        if (data.stock > data.capacity) {
            showToast(`Số lượng tồn kho (${data.stock}) không được vượt quá sức chứa (${data.capacity})! Vui lòng sửa lại.`, 'error');
            return;
        }
    }

    // Handle file upload for product images
    if (currentFormType === 'product') {
        const fileInput = document.getElementById('imageFile');
        if (fileInput && fileInput.files && fileInput.files[0]) {
            showToast('Đang tải ảnh lên...', 'info');
            const uploadResult = await uploadImage(fileInput.files[0]);
            if (uploadResult.success) {
                data.image = uploadResult.data.url;
            } else {
                showToast(uploadResult.message || 'Lỗi upload ảnh', 'error');
                return;
            }
        }
    }

    // Determine endpoint and method
    let endpoint, method;
    if (currentFormType === 'import') {
        endpoint = '/imports';
        method = 'POST';
    } else if (currentFormType === 'firmware') {
        endpoint = '/firmware/updates';
        method = 'POST';
    } else if (currentFormType === 'accessLog') {
        endpoint = '/security/access-logs';
        method = 'POST';
    } else {
        endpoint = `/${currentFormType}s${currentEditId ? '/' + currentEditId : ''}`;
        method = currentEditId ? 'PUT' : 'POST';
    }

    const result = await apiCall(endpoint, method, data);

    if (result.success) {
        showToast(currentEditId ? 'Cập nhật thành công!' : 'Thêm mới thành công!', 'success');
        closeModal();
        loadAllData();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}

async function deleteItem(type, id) {
    let confirmMsg = 'Bạn có chắc chắn muốn xóa mục này?';
    if (type === 'product') {
        confirmMsg = 'Bạn có chắc chắn muốn ngưng hoạt động sản phẩm này?\n(Lưu ý: Sản phẩm sẽ bị ẩn nhưng lịch sử đơn hàng vẫn được giữ lại)';
    } else if (type === 'machine') {
        confirmMsg = 'Bạn có chắc chắn muốn xóa máy này?\n(Toàn bộ khe hàng của máy cũng sẽ bị xóa theo)';
    }

    if (!confirm(confirmMsg)) return;

    const result = await apiCall(`/${type}s/${id}`, 'DELETE');

    if (result.success) {
        showToast(result.message || 'Thao tác thành công!', 'success');
        loadAllData();
    } else {
        showToast(result.message || 'Có lỗi xảy ra', 'error');
    }
}


// Utilities
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN') + ' ' + date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);
}

let toastTimeout = null;

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    // Clear previous timeout to prevent race conditions
    if (toastTimeout) clearTimeout(toastTimeout);

    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
        toastTimeout = null;
    }, 3000);
}

// Image Preview functions
function showImagePreview(imageUrl) {
    const modal = document.getElementById('imagePreviewModal');
    const previewImg = document.getElementById('previewImage');
    previewImg.src = imageUrl;
    modal.style.display = 'flex';
}

function closeImagePreview() {
    document.getElementById('imagePreviewModal').style.display = 'none';
}

// Action Menu functions
function toggleActionMenu(event, menuId) {
    event.stopPropagation();
    closeAllMenus();
    const menu = document.getElementById('menu-' + menuId);
    if (menu) {
        menu.classList.toggle('show');
    }
}

function closeAllMenus() {
    document.querySelectorAll('.action-dropdown').forEach(menu => {
        menu.classList.remove('show');
    });
}

// Close menus when clicking outside
document.addEventListener('click', function (event) {
    if (!event.target.closest('.action-menu')) {
        closeAllMenus();
    }
});

// Image Upload functions
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const formImagePreview = document.getElementById('formImagePreview');
            const imagePreviewContainer = document.getElementById('imagePreviewContainer');
            const fileUploadArea = document.getElementById('fileUploadArea');
            const tabs = document.querySelector('.image-source-tabs');

            if (formImagePreview) formImagePreview.src = e.target.result;
            if (imagePreviewContainer) imagePreviewContainer.classList.remove('hidden');
            if (fileUploadArea) fileUploadArea.style.display = 'none';
            if (tabs) tabs.classList.add('hidden');
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function previewUrlImage(url) {
    if (url) {
        const imageUrl = document.getElementById('imageUrl');
        const formImagePreview = document.getElementById('formImagePreview');
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        const urlInputArea = document.getElementById('urlInputArea');
        const tabs = document.querySelector('.image-source-tabs');

        if (imageUrl) imageUrl.value = url;
        if (formImagePreview) formImagePreview.src = url;
        if (imagePreviewContainer) imagePreviewContainer.classList.remove('hidden');
        if (urlInputArea) urlInputArea.classList.add('hidden');
        if (tabs) tabs.classList.add('hidden');
    }
}

function switchImageTab(tab) {
    document.querySelectorAll('.image-tab').forEach(t => t.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');

    const fileArea = document.getElementById('fileUploadArea');
    const urlArea = document.getElementById('urlInputArea');
    const previewContainer = document.getElementById('imagePreviewContainer');
    const imageUrl = document.getElementById('imageUrl');

    if (tab === 'file') {
        if (fileArea) {
            fileArea.classList.remove('hidden');
            fileArea.style.display = 'flex';
        }
        if (urlArea) urlArea.classList.add('hidden');
    } else {
        if (fileArea) {
            fileArea.classList.add('hidden');
            fileArea.style.display = 'none';
        }
        if (urlArea) urlArea.classList.remove('hidden');
    }

    if (imageUrl && !imageUrl.value && previewContainer) {
        previewContainer.classList.add('hidden');
    }
}

function removeImage() {
    const imageFile = document.getElementById('imageFile');
    const imageUrl = document.getElementById('imageUrl');
    const imageUrlInput = document.getElementById('imageUrlInput');
    const formImagePreview = document.getElementById('formImagePreview');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');

    if (imageFile) imageFile.value = '';
    if (imageUrl) imageUrl.value = '';
    if (imageUrlInput) imageUrlInput.value = '';
    if (formImagePreview) formImagePreview.src = '';
    if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');

    const tabs = document.querySelector('.image-source-tabs');
    const fileArea = document.getElementById('fileUploadArea');
    const urlArea = document.getElementById('urlInputArea');

    if (tabs) tabs.classList.remove('hidden');
    if (fileArea) {
        fileArea.classList.remove('hidden');
        fileArea.style.display = 'flex';
    }
    if (urlArea) urlArea.classList.add('hidden');

    document.querySelectorAll('.image-tab').forEach((t, i) => {
        if (i === 0) t.classList.add('active');
        else t.classList.remove('active');
    });
}

async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    return await res.json();
}

// =======================
// WebAuthn / Passkey Functions
// Giữ lại để có thể bật lại sau này.
// Hiện tại giao diện đăng nhập ưu tiên username/password nên không hiện nút Passkey.
// =======================

function isWebAuthnSupported() {
    return window.PublicKeyCredential !== undefined;
}

function base64urlToBuffer(base64url) {
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const padLen = (4 - base64.length % 4) % 4;
    const padded = base64 + '='.repeat(padLen);
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

function bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    const base64 = btoa(binary);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

async function checkPasskeyStatus() {
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/webauthn/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        const passkeyBtn = document.getElementById('passkeyBtn');
        if (passkeyBtn && data.success) {
            if (data.data.has_passkey) {
                passkeyBtn.classList.add('has-passkey');
                passkeyBtn.title = `Passkey: ${data.data.device_name || 'Registered'}`;
            } else {
                passkeyBtn.classList.remove('has-passkey');
                passkeyBtn.title = 'Đăng ký Passkey';
            }
        }
    } catch (err) {
        console.error('Error checking passkey status:', err);
    }
}

async function registerPasskeyRequired() {
    if (!isWebAuthnSupported()) {
        showToast('Trình duyệt không hỗ trợ Passkey', 'error');
        return false;
    }

    if (!token) {
        showToast('Vui lòng đăng nhập trước', 'error');
        return false;
    }

    try {
        showToast('Vui lòng đăng ký Passkey để hoàn tất...', 'info');

        const beginRes = await fetch(`${API_BASE}/webauthn/register/begin`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const beginData = await beginRes.json();

        if (!beginData.success) {
            showToast(beginData.message, 'error');
            return false;
        }

        const options = JSON.parse(beginData.data);
        options.challenge = base64urlToBuffer(options.challenge);
        options.user.id = base64urlToBuffer(options.user.id);

        if (options.excludeCredentials) {
            options.excludeCredentials = options.excludeCredentials.map(cred => ({
                ...cred,
                id: base64urlToBuffer(cred.id)
            }));
        }

        const credential = await navigator.credentials.create({
            publicKey: options
        });

        const credentialData = {
            id: credential.id,
            rawId: bufferToBase64url(credential.rawId),
            type: credential.type,
            response: {
                clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
                attestationObject: bufferToBase64url(credential.response.attestationObject)
            },
            device_name: navigator.platform || 'Unknown Device'
        };

        if (credential.response.getTransports) {
            credentialData.response.transports = credential.response.getTransports();
        }

        const completeRes = await fetch(`${API_BASE}/webauthn/register/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentialData)
        });
        const completeData = await completeRes.json();

        if (completeData.success) {
            showToast('Passkey đã được thiết lập! 🔑', 'success');
            return true;
        }

        showToast(completeData.message, 'error');
        return false;
    } catch (err) {
        if (err.name === 'NotAllowedError') {
            showToast('Đăng ký Passkey bị hủy', 'error');
        } else {
            console.error('Passkey registration error:', err);
            showToast(`Lỗi đăng ký Passkey: ${err.message}`, 'error');
        }
        return false;
    }
}

async function registerPasskey() {
    if (!isWebAuthnSupported()) {
        showToast('Trình duyệt không hỗ trợ Passkey', 'error');
        return;
    }

    if (!token) {
        showToast('Vui lòng đăng nhập trước', 'error');
        return;
    }

    try {
        showToast('Đang khởi tạo đăng ký Passkey...', 'info');

        const beginRes = await fetch(`${API_BASE}/webauthn/register/begin`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const beginData = await beginRes.json();

        if (!beginData.success) {
            showToast(beginData.message, 'error');
            return;
        }

        const options = JSON.parse(beginData.data);
        options.challenge = base64urlToBuffer(options.challenge);
        options.user.id = base64urlToBuffer(options.user.id);

        if (options.excludeCredentials) {
            options.excludeCredentials = options.excludeCredentials.map(cred => ({
                ...cred,
                id: base64urlToBuffer(cred.id)
            }));
        }

        const credential = await navigator.credentials.create({
            publicKey: options
        });

        const credentialData = {
            id: credential.id,
            rawId: bufferToBase64url(credential.rawId),
            type: credential.type,
            response: {
                clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
                attestationObject: bufferToBase64url(credential.response.attestationObject)
            },
            device_name: navigator.platform || 'Unknown Device'
        };

        if (credential.response.getTransports) {
            credentialData.response.transports = credential.response.getTransports();
        }

        const completeRes = await fetch(`${API_BASE}/webauthn/register/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentialData)
        });
        const completeData = await completeRes.json();

        if (completeData.success) {
            showToast('Đăng ký Passkey thành công! 🎉', 'success');
            checkPasskeyStatus();
        } else {
            showToast(completeData.message, 'error');
        }
    } catch (err) {
        if (err.name === 'NotAllowedError') {
            showToast('Đăng ký bị hủy hoặc hết thời gian', 'error');
        } else {
            console.error('Passkey registration error:', err);
            showToast(`Lỗi đăng ký Passkey: ${err.message}`, 'error');
        }
    }
}

async function loginWithPasskey() {
    if (!isWebAuthnSupported()) {
        showToast('Trình duyệt không hỗ trợ Passkey', 'error');
        return;
    }

    try {
        const username = document.getElementById('username')?.value || '';

        showToast('Đang khởi tạo đăng nhập Passkey...', 'info');

        const beginRes = await fetch(`${API_BASE}/webauthn/login/begin`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username || null })
        });
        const beginData = await beginRes.json();

        if (!beginData.success) {
            showToast(beginData.message, 'error');
            return;
        }

        const options = JSON.parse(beginData.data);
        const sessionKey = beginData.session_key;
        options.challenge = base64urlToBuffer(options.challenge);

        if (options.allowCredentials) {
            options.allowCredentials = options.allowCredentials.map(cred => ({
                ...cred,
                id: base64urlToBuffer(cred.id)
            }));
        }

        const assertion = await navigator.credentials.get({
            publicKey: options
        });

        const assertionData = {
            id: assertion.id,
            rawId: bufferToBase64url(assertion.rawId),
            type: assertion.type,
            response: {
                clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
                authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
                signature: bufferToBase64url(assertion.response.signature)
            },
            session_key: sessionKey
        };

        if (assertion.response.userHandle) {
            assertionData.response.userHandle = bufferToBase64url(assertion.response.userHandle);
        }

        const completeRes = await fetch(`${API_BASE}/webauthn/login/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(assertionData)
        });
        const completeData = await completeRes.json();

        if (completeData.success) {
            token = completeData.data.access_token;
            localStorage.setItem('token', token);
            currentUser = { username: completeData.data.username };
            showApp();
            showToast('Đăng nhập Passkey thành công! 🔑', 'success');
        } else {
            showToast(completeData.message, 'error');
        }
    } catch (err) {
        if (err.name === 'NotAllowedError') {
            showToast('Đăng nhập bị hủy hoặc hết thời gian', 'error');
        } else {
            console.error('Passkey login error:', err);
            showToast(`Lỗi đăng nhập Passkey: ${err.message}`, 'error');
        }
    }
}

async function managePasskey() {
    if (!token) {
        showToast('Vui lòng đăng nhập trước', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/webauthn/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.success) {
            showToast(data.message, 'error');
            return;
        }

        if (data.data.has_passkey) {
            const deviceName = data.data.device_name || 'Unknown';
            const createdAt = data.data.created_at ? new Date(data.data.created_at).toLocaleDateString('vi-VN') : 'Unknown';
            const lastUsed = data.data.last_used_at ? new Date(data.data.last_used_at).toLocaleString('vi-VN') : 'Chưa sử dụng';

            const confirmRemove = confirm(
                `Bạn đã có Passkey:\n\n` +
                `• Thiết bị: ${deviceName}\n` +
                `• Ngày tạo: ${createdAt}\n` +
                `• Lần cuối sử dụng: ${lastUsed}\n\n` +
                `Bạn có muốn XÓA Passkey này không?\n\n` +
                `⚠️ Bạn sẽ cần nhập mật khẩu để xác nhận.`
            );

            if (confirmRemove) {
                const password = prompt('Nhập mật khẩu để xác nhận xóa Passkey:');

                if (!password) {
                    showToast('Đã hủy xóa Passkey', 'info');
                    return;
                }

                const removeRes = await fetch(`${API_BASE}/webauthn/remove`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ password })
                });
                const removeData = await removeRes.json();

                if (removeData.success) {
                    showToast('Đã xóa Passkey thành công', 'success');
                    checkPasskeyStatus();
                } else {
                    showToast(removeData.message, 'error');
                }
            }
        } else if (confirm('Bạn chưa có Passkey.\n\nBạn có muốn đăng ký Passkey không?')) {
            registerPasskey();
        }
    } catch (err) {
        console.error('Error managing passkey:', err);
        showToast('Lỗi khi quản lý Passkey', 'error');
    }
}

// Load Device Logs
async function loadDeviceLogs() {
    const data = await apiCall('/devices/logs');
    if (data.success) {
        renderDeviceLogs(data.data);
    }
}

function renderDeviceLogs(logs) {
    const tbody = document.getElementById('deviceLogsTable');
    if (!tbody) return;
    tbody.innerHTML = logs.map(l => `
        <tr>
            <td class="id-column">${l.log_id}</td>
            <td class="table-align-center">#${l.machine_id}</td>
            <td class="table-align-center"><span class="status status-${l.level === 'error' ? 'inactive' : (l.level === 'warning' ? 'warning' : 'active')}">${l.level}</span></td>
            <td>${escapeHtml(l.message)}</td>
            <td class="table-align-center"><code>${JSON.stringify(l.data)}</code></td>
            <td class="table-align-center">${formatDate(l.timestamp)}</td>
        </tr>
    `).join('');
}

async function loadDeviceIdentities() {
    const data = await apiCall('/devices/identity');
    if (data.success) {
        renderDeviceIdentity(data.data);
    }
}

function renderDeviceIdentity(identities) {
    const tbody = document.getElementById('deviceIdentityTable');
    if (!tbody) return;
    tbody.innerHTML = identities.map(i => {
        const statusClass = i.status === 'active' ? 'active' : 'inactive';
        return `
            <tr>
                <td class="id-column">${i.machine_id}</td>
                <td class="table-align-center"><code>${i.mac_address || '-'}</code></td>
                <td class="table-align-center"><code>${i.fingerprint || '-'}</code></td>
                <td class="table-align-center"><span class="status status-${statusClass}">${i.status}</span></td>
                <td class="table-align-center">${formatDate(i.issued_at)}</td>
                <td class="table-align-center">
                    <div class="actions">
                        <button class="btn btn-delete btn-sm" onclick="revokeDeviceIdentity(${i.machine_id})">Thu hồi</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function loadDeviceSessions() {
    const data = await apiCall('/devices/sessions');
    if (data.success) {
        renderDeviceSessions(data.data);
    }
}

function renderDeviceSessions(sessions) {
    const tbody = document.getElementById('deviceSessionsTable');
    if (!tbody) return;
    tbody.innerHTML = sessions.map(s => {
        const isExpired = new Date(s.expires_at) < new Date();
        const statusClass = (s.status === 'active' && !isExpired) ? 'active' : 'inactive';
        return `
            <tr>
                <td class="id-column">${s.session_id.substring(0, 8)}...</td>
                <td class="table-align-center">#${s.machine_id}</td>
                <td class="table-align-center"><code>${s.ip_address || '-'}</code></td>
                <td class="table-align-center">${formatDate(s.issued_at)}</td>
                <td class="table-align-center">${formatDate(s.expires_at)}</td>
                <td class="table-align-center"><span class="status status-${statusClass}">${isExpired ? 'Hết hạn' : s.status}</span></td>
                <td class="table-align-center">
                    <div class="actions">
                        <button class="btn btn-delete btn-sm" onclick="revokeSession('${s.session_id}')">Thu hồi</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Global variable for admin socket
let adminSocket = null;

function initAdminWebSocket() {
    if (adminSocket) return;

    try {
        console.log('🔌 Connecting Admin WebSocket...');
        adminSocket = io('/admin', {
            transports: ['websocket', 'polling'],
            reconnection: true
        });

        adminSocket.on('connect', () => {
            console.log('✅ Admin WebSocket connected');
        });

        // 1. Live Device Logs
        adminSocket.on('admin_log', (data) => {
            console.log('📝 Real-time Log:', data);
            // Prepend to logs table if currently on logs tab
            const tbody = document.getElementById('deviceLogsTable');
            if (tbody) {
                const logHtml = `
                    <tr class="highlight-new">
                        <td>NEW</td>
                        <td>${data.machine_id}</td>
                        <td><span class="status status-${data.level === 'error' ? 'inactive' : (data.level === 'warning' ? 'maintenance' : 'active')}">${data.level}</span></td>
                        <td>${escapeHtml(data.message)}<br><small style="color:var(--text-muted); font-family:monospace">${escapeHtml(JSON.stringify(data.data))}</small></td>
                        <td>${data.data ? '✅' : '-'}</td>
                        <td>${formatDate(data.timestamp)}</td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('afterbegin', logHtml);
                // Keep only top 50
                if (tbody.children.length > 50) tbody.lastElementChild.remove();
            }
            showToast(`Máy #${data.machine_id}: ${data.message}`, data.level === 'error' ? 'error' : 'info');
        });

        // 2. Live Order Notifications
        adminSocket.on('admin_order_new', (data) => {
            console.log('🛒 New Order:', data);
            showToast(`📦 Đơn hàng mới: ${data.product_name} - ${formatPrice(data.amount)}`, 'success', 10000);
            
            // Reload stats and orders
            loadStats();
            loadOrders();
        });

        // 3. Live Machine Status
        adminSocket.on('admin_machine_status', (data) => {
            console.log('🖥️ Machine Status:', data);
            // Update machine in cache and re-render
            const mIndex = machinesCache.findIndex(m => m.machine_id === data.machine_id);
            if (mIndex !== -1) {
                machinesCache[mIndex] = { ...machinesCache[mIndex], ...data };
                renderMachines(machinesCache);
            }
        });

        adminSocket.on('disconnect', () => {
            console.log('⚠️ Admin WebSocket disconnected');
            adminSocket = null;
        });

    } catch (e) {
        console.error('Error initializing Admin WebSocket:', e);
    }
}

// Update loadAllData to include logs
const originalLoadAllData = loadAllData;
loadAllData = async function () {
    await originalLoadAllData();
    await loadDeviceLogs();
    await loadDeviceIdentities();
    await loadDeviceSessions();
};
