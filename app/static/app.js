// API Configuration
const API_BASE = '/api';
let token = localStorage.getItem('token');
let currentUser = null;

// Products and Machines cache for lookups
let productsCache = [];
let machinesCache = [];

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
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);

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
            showToast('Đăng ký thành công! Hãy đăng nhập.', 'success');
            showLogin();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
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

function showApp() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('registerModal').style.display = 'none';
    document.getElementById('app').style.display = 'block';
    document.getElementById('currentUser').textContent = `👤 ${currentUser?.username || 'User'}`;
    loadAllData();
}

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

// Load all data
async function loadAllData() {
    await Promise.all([
        loadMachines(),
        loadProducts(),
        loadSlots(),
        loadOrders()
    ]);
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
        renderSlots(data.data);
    }
}

async function loadOrders() {
    const data = await apiCall('/orders');
    if (data.success) {
        renderOrders(data.data);
    }
}

// Render functions
function renderMachines(machines) {
    const tbody = document.getElementById('machinesTable');
    tbody.innerHTML = machines.map(m => `
        <tr>
            <td>${m.id}</td>
            <td>${m.name}</td>
            <td>${m.location || '-'}</td>
            <td><span class="status status-${m.status}">${m.status}</span></td>
            <td>${formatDate(m.created_at)}</td>
            <td class="actions">
                <button class="btn btn-edit" onclick='editItem("machine", ${JSON.stringify(m)})'>Sửa</button>
                <button class="btn btn-delete" onclick="deleteItem('machine', ${m.id})">Xóa</button>
            </td>
        </tr>
    `).join('');
}

function renderProducts(products) {
    const tbody = document.getElementById('productsTable');
    tbody.innerHTML = products.map(p => `
        <tr>
            <td>${p.id}</td>
            <td>${p.name}</td>
            <td>${formatPrice(p.price)}</td>
            <td class="product-image-cell">
                ${p.image
            ? `<img src="${p.image}" alt="${p.name}" class="product-thumbnail" onclick="showImagePreview('${p.image}')">`
            : '<span class="no-image">📷 Chưa có ảnh</span>'
        }
            </td>
            <td><span class="status status-${p.active}">${p.active ? 'Hoạt động' : 'Ngưng'}</span></td>
            <td class="actions">
                <div class="action-menu">
                    <button class="btn btn-more" onclick="toggleActionMenu(event, 'product-${p.id}')">⋯</button>
                    <div id="menu-product-${p.id}" class="action-dropdown">
                        <button onclick='editItem("product", ${JSON.stringify(p)}); closeAllMenus();'>✏️ Sửa</button>
                        <button onclick="deleteItem('product', ${p.id}); closeAllMenus();">🗑️ Xóa</button>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderSlots(slots) {
    const tbody = document.getElementById('slotsTable');
    tbody.innerHTML = slots.map(s => {
        const machine = machinesCache.find(m => m.id === s.machine_id);
        const product = productsCache.find(p => p.id === s.product_id);
        return `
            <tr>
                <td>${s.id}</td>
                <td>${machine?.name || s.machine_id}</td>
                <td>${s.slot_no}</td>
                <td>${product?.name || '-'}</td>
                <td>${s.quantity}</td>
                <td class="actions">
                    <button class="btn btn-edit" onclick='editItem("slot", ${JSON.stringify(s)})'>Sửa</button>
                    <button class="btn btn-delete" onclick="deleteItem('slot', ${s.id})">Xóa</button>
                </td>
            </tr>
        `;
    }).join('');
}

function renderOrders(orders) {
    const tbody = document.getElementById('ordersTable');
    const paymentLabels = {
        'cash': '💵 Tiền mặt',
        'qr_code': '📱 QR Code',
        'card': '💳 Thẻ'
    };
    tbody.innerHTML = orders.map(o => {
        const machine = machinesCache.find(m => m.id === o.machine_id);
        return `
            <tr>
                <td>${o.id}</td>
                <td>${machine?.name || o.machine_id}</td>
                <td>${o.slot_no}</td>
                <td>${o.quantity}</td>
                <td>${formatPrice(o.total_price)}</td>
                <td><span class="payment-method payment-${o.payment_method}">${paymentLabels[o.payment_method] || o.payment_method}</span></td>
                <td><span class="status status-${o.status}">${o.status}</span></td>
                <td>${formatDate(o.created_at)}</td>
            </tr>
        `;
    }).join('');
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
    currentEditId = item.id;
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
        slot: isEdit ? 'Sửa khe hàng' : 'Thêm khe hàng'
    };
    return titles[type];
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
            `;
        case 'product':
            return `
                <div class="form-group">
                    <label>Tên sản phẩm</label>
                    <input type="text" name="name" value="${item?.name || ''}" required>
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
                            <input type="url" id="imageUrlInput" placeholder="https://example.com/image.jpg" value="${item?.image || ''}" onchange="previewUrlImage(this.value)">
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
                        ${machinesCache.map(m => `<option value="${m.id}" ${item?.machine_id === m.id ? 'selected' : ''}>${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Số khe</label>
                    <input type="text" name="slot_no" value="${item?.slot_no || ''}" required>
                </div>
                <div class="form-group">
                    <label>Sản phẩm</label>
                    <select name="product_id">
                        <option value="">-- Không có --</option>
                        ${productsCache.map(p => `<option value="${p.id}" ${item?.product_id === p.id ? 'selected' : ''}>${p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Số lượng</label>
                    <input type="number" name="quantity" value="${item?.quantity || 0}" required>
                </div>
            `;
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {};

    formData.forEach((value, key) => {
        if (key === 'active') {
            data[key] = value === 'true';
        } else if (key === 'price' || key === 'quantity' || key === 'machine_id') {
            data[key] = parseInt(value) || 0;
        } else if (key === 'product_id') {
            data[key] = value ? parseInt(value) : null;
        } else {
            data[key] = value;
        }
    });

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

    const endpoint = `/${currentFormType}s${currentEditId ? '/' + currentEditId : ''}`;
    const method = currentEditId ? 'PUT' : 'POST';

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
    if (!confirm('Bạn có chắc muốn xóa?')) return;

    const result = await apiCall(`/${type}s/${id}`, 'DELETE');

    if (result.success) {
        showToast('Đã xóa thành công!', 'success');
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

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
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
    // Update tab buttons
    document.querySelectorAll('.image-tab').forEach(t => t.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');

    // Reset states
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

    // Hide preview if switching tabs and no image selected
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

    // Show tabs and upload area again
    const tabs = document.querySelector('.image-source-tabs');
    const fileArea = document.getElementById('fileUploadArea');
    const urlArea = document.getElementById('urlInputArea');

    if (tabs) tabs.classList.remove('hidden');
    if (fileArea) {
        fileArea.classList.remove('hidden');
        fileArea.style.display = 'flex';
    }
    if (urlArea) urlArea.classList.add('hidden');

    // Reset tabs to first tab active
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
