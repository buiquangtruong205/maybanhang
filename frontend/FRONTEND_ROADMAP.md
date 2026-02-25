# 🗺️ Bản Kế Hoạch Hoàn Thiện Frontend - Vending Machine V2

> Tài liệu này mô tả chi tiết các bước cần thực hiện để hoàn thiện frontend,  
> sắp xếp theo **thứ tự ưu tiên** và **mức độ phụ thuộc** giữa các module.
>
> ⏱️ **Cập nhật lần cuối:** 25/02/2026

---

## 📊 Trạng Thái Hiện Tại

### ✅ Đã hoàn thiện (Sẵn sàng sử dụng)

| Module | File chính | Chức năng |
| :--- | :--- | :--- |
| **Trang chủ khách hàng** | `HomeView.vue` | Hiển thị danh sách sản phẩm, chọn mua hàng |
| **Thanh toán** | `PaymentView.vue` | QR code PayOS, kiểm tra trạng thái real-time |
| **Thành công / Hủy** | `SuccessView.vue`, `CancelView.vue` | Trang kết quả thanh toán |
| **Đăng nhập Admin** | `LoginView.vue` | JWT login, redirect sau đăng nhập |
| **Bố cục Admin** | `AdminLayout.vue` | Sidebar, header, navigation, role-based menu |
| **Dashboard** | `DashboardView.vue` | Thống kê, biểu đồ doanh thu, top sản phẩm, báo sự cố |
| **Quản lý sản phẩm** | `ProductsView.vue` | CRUD sản phẩm, tìm kiếm, phân trang |
| **Quản lý đơn hàng** | `OrdersView.vue` | Danh sách đơn, lọc theo trạng thái, xác nhận thủ công |
| **Quản lý máy** | `MachinesView.vue` | CRUD máy bán hàng, trạng thái online/offline |
| **Quản lý vị trí hàng** | `SlotsView.vue` | CRUD slots, nạp hàng (refill), liên kết sản phẩm–máy |
| **Quản lý người dùng** | `UsersView.vue` + `UserModal.vue` | CRUD user, phân quyền Admin/Nhân viên |
| **Quản lý sự cố** | `IssuesView.vue` | Danh sách sự cố, cập nhật trạng thái, đánh dấu đã xử lý |
| **Nhật ký nạp hàng** | `RefillLogsView.vue` | Lịch sử nạp hàng, ai nạp, máy nào |
| **Cấu hình hệ thống** | `SettingsView.vue` | Key-value settings, khôi phục mặc định |
| **Components chung** | `Header.vue`, `ConfirmModal.vue`, `LoadingSpinner.vue` | Tái sử dụng xuyên suốt |
| **Components sản phẩm** | `ProductCard.vue`, `ProductModal.vue` | Thẻ sản phẩm, modal chi tiết |
| **Components biểu đồ** | `RevenueChart.vue`, `TopProducts.vue` | Chart.js biểu đồ doanh thu |
| **QR Code** | `QrCodeDisplay.vue` | Hiển thị QR code với fallback |
| **Router** | `router/index.js` | Routing + auth guard middleware |
| **Stores** | 4 Pinia stores | auth, product, payment, machine |
| **API Layer** | 5 API files | http, admin, products, payments, users |
| **Socket.IO** | `plugins/socket.js` | Kết nối real-time tới backend |
| **Tiện ích** | `formatters.js`, `constants.js` | Định dạng tiền tệ, ngày giờ, trạng thái |

### ✅ Đã sửa chữa (Giai đoạn 1 — Hoàn thành 25/02/2026)

| Hạng mục | Vấn đề cũ | Trạng thái |
| :--- | :--- | :--- |
| ~~**Machine Store cứng**~~ | Hardcode `MACHINE_01`, name, location | ✅ Thêm `layThongTinMay()` gọi API |
| ~~**Socket.IO URL cứng**~~ | Hardcode `http://localhost:5001` | ✅ Hàm `laySocketURL()` dùng biến môi trường + auto-detect |
| ~~**`.env.example` cũ**~~ | Port 5000 sai, thiếu VITE_SOCKET_URL | ✅ Cập nhật port 5001, thêm biến, comment tiếng Việt |
| ~~**README.md sơ sài**~~ | Chỉ 39 dòng, thiếu mô tả | ✅ Viết lại hoàn toàn cho V2 |

### ⚠️ Còn cần bổ sung (Giai đoạn 2–6)

| Hạng mục | Vấn đề | Mức độ |
| :--- | :--- | :--- |
| **Thiếu hệ thống thông báo** | Dùng `alert()` thay vì Toast/Snackbar chuyên nghiệp | 🟡 Trung bình |
| **Thiếu PWA** | Chưa hỗ trợ Progressive Web App (offline, install) | 🟡 Trung bình |
| **Thiếu Skeleton Loading** | Chỉ có text "Đang tải..." thay vì skeleton UI | 🟢 Thấp |
| **Thiếu Dark/Light mode** | Chỉ có dark mode, chưa chuyển đổi được | 🟢 Thấp |
| **Thiếu i18n** | Chưa hỗ trợ đa ngôn ngữ (Việt/Anh) | 🟢 Thấp |

---

## 📋 Kế Hoạch Chi Tiết Theo Giai Đoạn

---

### ✅ Giai Đoạn 1: Sửa lỗi & Chuẩn hóa — HOÀN THÀNH ✅

> **Hoàn thành ngày:** 25/02/2026

- [x] 1.1 Sửa `stores/machine.js` — Thêm `layThongTinMay()` gọi API thay vì hardcode
- [x] 1.2 Sửa `plugins/socket.js` — Hàm `laySocketURL()` dùng biến môi trường + auto-detect + sửa typo `reconnectionRequests`
- [x] 1.3 Cập nhật `.env.example` — Sửa port 5000→5001, thêm `VITE_SOCKET_URL`, comment tiếng Việt
- [x] 1.4 Viết lại `README.md` — Hoàn toàn mới cho V2 (công nghệ, 10 trang admin, cấu trúc, biến môi trường)

---

### 🎨 Giai Đoạn 2: Nâng cấp UI/UX

> **Mục tiêu:** Tăng chất lượng trải nghiệm người dùng.

#### 2.1 Hệ thống Toast/Thông báo
- **Giải pháp:** Tạo component `ToastNotification.vue` + composable `useToast()`
- **Thay thế:** Tất cả `alert()` → `toast.success()`, `toast.error()`
- **File mới:**
  - `components/common/ToastNotification.vue`
  - `composables/useToast.js`

#### 2.2 Skeleton Loading
- **Giải pháp:** Tạo component `SkeletonLoader.vue` cho các trang CRUD
- **Thay thế:** Text "Đang tải..." → Skeleton hiệu ứng shimmer
- **Áp dụng:** Dashboard, Products, Orders, Machines, Slots
- **File mới:** `components/common/SkeletonLoader.vue`

#### 2.3 Cải thiện trang khách hàng
- **Thêm:** Hiệu ứng chuyển trang mượt hơn (Vue Transition)
- **Thêm:** Hình ảnh sản phẩm đẹp hơn (hoặc placeholder SVG)
- **Thêm:** Bộ đếm ngược thanh toán rõ ràng hơn
- **File:** `HomeView.vue`, `PaymentView.vue`

#### 2.4 Responsive nâng cao
- **Kiểm tra:** Admin layout trên tablet (768px–1024px)
- **Sửa:** Sidebar collapse trên mobile, bottom navigation
- **File:** `AdminLayout.vue` + CSS liên quan

---

### 🔌 Giai Đoạn 3: Tích hợp Real-time nâng cao

> **Mục tiêu:** Frontend phản hồi real-time từ backend và ESP32.

#### 3.1 Socket.IO cho trạng thái máy
- **Mới:** Nhận sự kiện `machine_status` từ backend
- **Hiển thị:** Badge real-time trên trang Machines (Online/Offline/Lỗi)
- **File:** `MachinesView.vue`, `DashboardView.vue`

#### 3.2 Socket.IO cho thông báo đơn hàng
- **Mới:** Toast thông báo khi có đơn hàng mới (cho admin)
- **Mới:** Tự động refresh danh sách đơn hàng real-time
- **File:** `OrdersView.vue`, `DashboardView.vue`

#### 3.3 Socket.IO cho sự cố
- **Đã có:** Backend emit `issue_update`
- **Thêm:** Frontend lắng nghe và hiển thị Toast cảnh báo
- **File:** `IssuesView.vue`, `AdminLayout.vue`

---

### 📱 Giai Đoạn 4: PWA (Progressive Web App)

> **Mục tiêu:** Web app có thể cài đặt trên điện thoại như ứng dụng thật.

#### 4.1 Cấu hình PWA
- **Thư viện:** `vite-plugin-pwa`
- **Thêm:** Service Worker, manifest.json
- **File:** `vite.config.js` + `public/manifest.json`

#### 4.2 Offline Support
- **Cache:** Trang chủ, danh sách sản phẩm (đã load)
- **Hiển thị:** Banner "Đang offline" khi mất kết nối
- **File mới:** `composables/useOnlineStatus.js`

#### 4.3 App Icons & Splash Screen
- **Tạo:** Icon các kích thước (192x192, 512x512)
- **Tạo:** Splash screen cho iOS và Android
- **Thư mục:** `public/icons/`

---

### 🧪 Giai Đoạn 5: Testing

> **Mục tiêu:** Đảm bảo giao diện hoạt động đúng.

#### 5.1 Unit Tests cho Components
- **Thư viện:** `vitest` + `@vue/test-utils`
- **Test:** ProductCard, ConfirmModal, ToastNotification
- **Thư mục:** `tests/unit/`

#### 5.2 E2E Tests cho luồng chính
- **Thư viện:** `playwright` hoặc `cypress`
- **Test luồng:**
  1. Khách hàng: Chọn sản phẩm → Thanh toán → Thành công
  2. Admin: Đăng nhập → Dashboard → CRUD sản phẩm
  3. Admin: Quản lý đơn hàng → Xác nhận thủ công
- **Thư mục:** `tests/e2e/`

---

### 📈 Giai Đoạn 6: Tối ưu & Mở rộng (Tùy chọn)

> **Mục tiêu:** Nâng cấp hiệu năng và tính năng sau khi core ổn định.

#### 6.1 SEO & Meta Tags
- **Thêm:** Vue Meta (hoặc `useHead`) cho các trang public
- **Thêm:** Open Graph meta tags cho chia sẻ mạng xã hội
- **File:** Các views khách hàng

#### 6.2 Dark/Light Mode Toggle
- **Thêm:** Nút chuyển đổi theme
- **Lưu:** Preference vào localStorage
- **File:** `AdminLayout.vue`, CSS variables

#### 6.3 Đa ngôn ngữ (i18n)
- **Thư viện:** `vue-i18n`
- **Ngôn ngữ:** Tiếng Việt (mặc định), Tiếng Anh
- **File mới:** `locales/vi.json`, `locales/en.json`

#### 6.4 Xuất PDF đơn hàng
- **Thư viện:** `jspdf`
- **Chức năng:** Xuất chi tiết đơn hàng dạng PDF
- **File:** Thêm nút trong `OrdersView.vue`

#### 6.5 Biểu đồ nâng cao
- **Thêm:** Biểu đồ tròn phân bổ sản phẩm
- **Thêm:** Biểu đồ so sánh doanh thu theo máy
- **File:** Components mới trong `components/admin/`

---

## 🎯 Lộ Trình Thực Hiện

```
Giai đoạn 1 (Sửa lỗi)     ██████████  HOÀN THÀNH ✅ (25/02/2026)
Giai đoạn 2 (UI/UX)        ████████░░  ~4-6 giờ   ← TIẾP THEO
Giai đoạn 3 (Real-time)    ██████░░░░  ~2-3 giờ   ← Song song với Backend GĐ2 (MQTT)
Giai đoạn 4 (PWA)          ██████░░░░  ~3-4 giờ   ← Trước khi deploy
Giai đoạn 5 (Testing)      ████░░░░░░  ~3-4 giờ   ← Khi tính năng ổn định
Giai đoạn 6 (Mở rộng)      ████░░░░░░  ~4-8 giờ   ← Tùy chọn, sau khi core ổn
```

---

## 📁 Cấu Trúc Dự Kiến Sau Hoàn Thiện

```
frontend/src/
├── main.js
├── App.vue
├── api/
│   ├── http.js                     # Axios client
│   ├── admin.js                    # API quản trị (tổng hợp)
│   ├── products.js                 # API sản phẩm (khách hàng)
│   ├── payments.js                 # API thanh toán
│   └── users.js                    # API người dùng
├── assets/                         # Hình ảnh, fonts
├── components/
│   ├── admin/                      # Components cho Admin
│   │   ├── RevenueChart.vue
│   │   ├── TopProducts.vue
│   │   └── UserModal.vue
│   ├── common/                     # Components dùng chung
│   │   ├── ConfirmModal.vue
│   │   ├── Header.vue
│   │   ├── LoadingSpinner.vue
│   │   ├── ToastNotification.vue   ← MỚI
│   │   └── SkeletonLoader.vue      ← MỚI
│   ├── payment/
│   │   └── QrCodeDisplay.vue
│   └── product/
│       ├── ProductCard.vue
│       └── ProductModal.vue
├── composables/                    ← MỚI
│   ├── useToast.js                 ← MỚI: Hệ thống thông báo
│   └── useOnlineStatus.js          ← MỚI: Kiểm tra kết nối
├── plugins/
│   └── socket.js                   # Socket.IO client
├── router/
│   └── index.js                    # Vue Router + auth guard
├── stores/
│   ├── auth.js                     # Xác thực JWT
│   ├── machine.js                  # Trạng thái máy (ĐÃ SỬA: gọi API)
│   ├── payment.js                  # Luồng thanh toán
│   └── product.js                  # Danh sách sản phẩm
├── utils/
│   ├── constants.js                # Hằng số
│   └── formatters.js               # Định dạng hiển thị
└── views/
    ├── HomeView.vue                # Trang chủ khách hàng
    ├── PaymentView.vue             # Trang thanh toán
    ├── SuccessView.vue             # Thanh toán thành công
    ├── CancelView.vue              # Hủy thanh toán
    ├── NotFoundView.vue            # 404
    └── admin/
        ├── AdminLayout.vue         # Bố cục admin
        ├── LoginView.vue           # Đăng nhập
        ├── DashboardView.vue       # Tổng quan
        ├── ProductsView.vue        # Quản lý sản phẩm
        ├── OrdersView.vue          # Quản lý đơn hàng
        ├── MachinesView.vue        # Quản lý máy
        ├── SlotsView.vue           # Quản lý vị trí hàng
        ├── UsersView.vue           # Quản lý người dùng
        ├── IssuesView.vue          # Quản lý sự cố
        ├── RefillLogsView.vue      # Nhật ký nạp hàng
        └── SettingsView.vue        # Cấu hình hệ thống
```
