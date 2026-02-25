# 🛒 Vending Machine Frontend — Phiên Bản 2

Giao diện web cho máy bán hàng tự động — hỗ trợ khách hàng mua hàng và quản trị viên quản lý hệ thống.

## 🛠️ Công Nghệ

| Thành phần | Công nghệ |
| :--- | :--- |
| **Framework** | Vue 3 (Composition API + `<script setup>`) |
| **Công cụ build** | Vite |
| **CSS** | Tailwind CSS 4 |
| **Quản lý trạng thái** | Pinia |
| **Routing** | Vue Router 4 (có auth guard) |
| **HTTP Client** | Axios (với interceptor JWT) |
| **Real-time** | Socket.IO Client |
| **Biểu đồ** | Chart.js + vue-chartjs |
| **QR Code** | qrcode (thư viện) |

---

## 🚀 Cài Đặt và Chạy

### 1. Cài dependencies
```bash
cd Version_2/frontend
npm install
```

### 2. Cấu hình `.env`
```bash
cp .env.example .env
# Sửa các giá trị nếu cần (mặc định dùng localhost:5001)
```

### 3. Chạy chế độ phát triển
```bash
npm run dev
```

Ứng dụng chạy tại: `http://localhost:5173`

### 4. Build cho production
```bash
npm run build
```

---

## 📱 Các Trang Chính

### 🛒 Trang Khách Hàng

| Đường dẫn | Trang | Mô tả |
| :--- | :--- | :--- |
| `/` | Trang chủ | Danh sách sản phẩm, chọn mua hàng |
| `/payment/:productId` | Thanh toán | QR code PayOS, theo dõi trạng thái real-time |
| `/success` | Thành công | Thông báo thanh toán thành công |
| `/cancel` | Hủy | Thông báo thanh toán bị hủy |

### 🔧 Trang Quản Trị (`/admin`)

| Đường dẫn | Trang | Mô tả |
| :--- | :--- | :--- |
| `/admin/login` | Đăng nhập | JWT login |
| `/admin` | Tổng quan | Thống kê, biểu đồ doanh thu, top sản phẩm |
| `/admin/products` | Sản phẩm | CRUD sản phẩm, tìm kiếm |
| `/admin/orders` | Đơn hàng | Danh sách, lọc trạng thái, xác nhận thủ công |
| `/admin/machines` | Máy bán hàng | CRUD máy, trạng thái online/offline |
| `/admin/slots` | Vị trí hàng | Liên kết sản phẩm–máy, nạp hàng |
| `/admin/users` | Người dùng | CRUD user, phân quyền Admin/Nhân viên |
| `/admin/issues` | Sự cố | Báo cáo, cập nhật trạng thái |
| `/admin/refill-logs` | Nhật ký nạp hàng | Lịch sử nạp hàng |
| `/admin/settings` | Cấu hình | Key-value settings hệ thống |

---

## 📁 Cấu Trúc Thư Mục

```
frontend/src/
├── main.js                         # Điểm khởi động ứng dụng
├── App.vue                         # Component gốc
├── api/                            # Lớp giao tiếp API
│   ├── http.js                     # Axios client + interceptors
│   ├── admin.js                    # API quản trị (tổng hợp)
│   ├── products.js                 # API sản phẩm (khách hàng)
│   ├── payments.js                 # API thanh toán
│   └── users.js                    # API người dùng
├── assets/                         # Hình ảnh, fonts
├── components/
│   ├── admin/                      # Components quản trị
│   │   ├── RevenueChart.vue        # Biểu đồ doanh thu
│   │   ├── TopProducts.vue         # Top sản phẩm bán chạy
│   │   └── UserModal.vue           # Modal tạo/sửa user
│   ├── common/                     # Components dùng chung
│   │   ├── ConfirmModal.vue        # Hộp thoại xác nhận
│   │   ├── Header.vue              # Header trang chủ
│   │   └── LoadingSpinner.vue      # Hiệu ứng loading
│   ├── payment/
│   │   └── QrCodeDisplay.vue       # Hiển thị QR code
│   └── product/
│       ├── ProductCard.vue         # Thẻ sản phẩm
│       └── ProductModal.vue        # Modal chi tiết sản phẩm
├── plugins/
│   └── socket.js                   # Socket.IO client (real-time)
├── router/
│   └── index.js                    # Vue Router + auth guard
├── stores/                         # Pinia stores
│   ├── auth.js                     # Xác thực JWT
│   ├── machine.js                  # Thông tin máy (từ API)
│   ├── payment.js                  # Luồng thanh toán
│   └── product.js                  # Danh sách sản phẩm
├── utils/
│   ├── constants.js                # Hằng số (trạng thái, URL)
│   └── formatters.js               # Định dạng tiền, ngày giờ
└── views/
    ├── HomeView.vue                # Trang chủ
    ├── PaymentView.vue             # Thanh toán
    ├── SuccessView.vue             # Thành công
    ├── CancelView.vue              # Hủy
    ├── NotFoundView.vue            # 404
    └── admin/                      # 11 trang quản trị
```

---

## 🔄 Luồng Thanh Toán

```
1. Khách hàng chọn sản phẩm trên HomeView
2. Chuyển sang PaymentView → gọi API tạo thanh toán
3. Backend tạo QR PayOS → trả về QR code URL
4. Hiển thị QR code → khách quét QR thanh toán
5. Socket.IO nhận sự kiện order_update từ backend
6. Cập nhật trạng thái real-time → chuyển sang SuccessView
7. ESP32 nhận lệnh nhả hàng → khách nhận sản phẩm
```

---

## 🔧 Biến Môi Trường

| Biến | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `VITE_API_URL` | URL API Backend | `http://localhost:5001/api/v1` |
| `VITE_SOCKET_URL` | URL Socket.IO | `http://localhost:5001` |
| `VITE_MACHINE_ID` | Mã định danh máy (kiểu kiosk) | `VM001` |
| `VITE_REFRESH_INTERVAL` | Tự động refresh (ms) | `30000` |
| `VITE_PAYMENT_TIMEOUT` | Thời gian chờ thanh toán (giây) | `300` |

---

## 🧩 Tính Năng Nổi Bật

- ✅ **Glassmorphism UI** — Giao diện hiện đại, hiệu ứng kính mờ
- ✅ **Real-time** — Socket.IO cập nhật đơn hàng tức thì
- ✅ **Responsive** — Tương thích từ điện thoại đến desktop
- ✅ **Role-based** — Phân quyền Admin / Nhân viên
- ✅ **Biểu đồ** — Doanh thu, top sản phẩm (Chart.js)
- ✅ **Báo cáo Excel** — Xuất dữ liệu từ Dashboard
