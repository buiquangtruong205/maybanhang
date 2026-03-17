# Cấu Trúc Cơ Sở Dữ Liệu - Máy Bán Hàng Tự Động

> **File nguồn:** `backend/app/models/database.py`

---

## Tổng quan

Database hiện gồm các bảng chính được chia thành các nhóm chức năng:

| Nhóm | Số bảng | Bảng |
|------|---------|------|
| Quản trị | 1 | `users` |
| Thiết bị IoT | 1 | `machines` |
| Sản phẩm & Kho | 2 | `products`, `slots` |
| Bán hàng & Thanh toán | 3 | `orders`, `transactions`, `payment_callbacks` |
| Bảo mật IoT | 2 | `device_identity`, `device_sessions` |
| Audit Logs | 2 | `api_audit_logs`, `staff_access_logs` |
| WebAuthn | 1 | `webauthn_credentials` |

---

## 1. Quản trị (Admin)

### Bảng `users`

Lưu thông tin tài khoản admin.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `user_id` | Integer | PK | ID người dùng |
| `username` | String(80) | UNIQUE, NOT NULL, INDEX | Tên đăng nhập |
| `password` | String(200) | NOT NULL | Mật khẩu (khuyến nghị hash) |
| `is_active` | Boolean | DEFAULT TRUE | Trạng thái hoạt động |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

---

## 2. Thiết bị IoT (Machines)

### Bảng `machines`

Thông tin máy bán hàng.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `machine_id` | Integer | PK | ID máy |
| `name` | String(100) | NOT NULL, INDEX | Tên máy |
| `location` | String(200) | NULLABLE | Vị trí đặt máy |
| `status` | String(20) | DEFAULT 'active', INDEX | Trạng thái máy |
| `secret_key` | String(200) | NULLABLE | Khóa bí mật xác thực |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

**Relationships:**
- `slots` → One-to-Many với bảng `slots`
- `device_identity` → One-to-One với bảng `device_identity`
- `device_sessions` → One-to-Many với bảng `device_sessions`

---

## 3. Sản phẩm & Kho (Products & Inventory)

### Bảng `products`

Danh mục sản phẩm.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `product_id` | Integer | PK | ID sản phẩm |
| `product_name` | String(100) | NOT NULL, INDEX | Tên sản phẩm |
| `price` | Numeric(10,2) | NOT NULL | Giá bán |
| `image` | String(500) | NULLABLE | URL hình ảnh |
| `active` | Boolean | DEFAULT TRUE, INDEX | Còn bán hay không |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

---

### Bảng `slots`

Các ngăn/khe trong máy bán hàng.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `slot_id` | Integer | PK | ID khe |
| `machine_id` | Integer | FK → machines, NOT NULL, INDEX | ID máy |
| `slot_code` | String(10) | NOT NULL | Mã khe (A1, B2,...) |
| `product_id` | Integer | FK → products, NULLABLE, INDEX | ID sản phẩm trong khe |
| `stock` | Integer | DEFAULT 0 | Số lượng tồn kho |
| `capacity` | Integer | DEFAULT 10 | Sức chứa tối đa |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

**Constraints:**
- `UNIQUE(machine_id, slot_code)` - Mỗi máy không có slot_code trùng
- `INDEX(machine_id, product_id)` - Composite index

---

## 4. Bán hàng & Thanh toán (Orders & Payments)

### Bảng `orders`

Đơn hàng.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `order_id` | Integer | PK | ID đơn hàng |
| `product_id` | Integer | FK → products, NOT NULL, INDEX | ID sản phẩm |
| `slot_id` | Integer | FK → slots, NULLABLE, INDEX | ID khe xuất hàng |
| `price_snapshot` | Numeric(10,2) | NOT NULL | Giá tại thời điểm mua |
| `status_payment` | String(20) | DEFAULT 'pending', INDEX | Trạng thái thanh toán |
| `status_slots` | String(20) | DEFAULT 'pending', INDEX | Trạng thái xuất hàng |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

**Giá trị `status_payment`:**
- `pending` - Chờ thanh toán
- `completed` - Đã thanh toán thành công
- `cancelled` - Đã hủy

**Giá trị `status_slots`:**
- `pending` - Chờ xuất hàng
- `dispensed` - Đã xuất xong
- `failed` - Xuất hàng thất bại
- `completed` - Hoàn tất theo luồng cũ
- `cancelled` - Đã hủy

---

### Bảng `transactions`

Giao dịch thanh toán.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `transaction_id` | Integer | PK | ID giao dịch |
| `order_id` | Integer | FK → orders, NOT NULL, INDEX | ID đơn hàng |
| `amount` | Numeric(10,2) | NOT NULL | Số tiền |
| `bank_trans_id` | String(100) | NULLABLE, INDEX | Mã giao dịch ngân hàng |
| `description` | Text | NULLABLE | Nội dung chuyển khoản |
| `sender_account` | String(50) | NULLABLE | Số tài khoản người gửi |
| `sender_bank` | String(50) | NULLABLE | Ngân hàng người gửi |
| `status` | String(50) | DEFAULT 'pending', INDEX | Trạng thái |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

**Giá trị thực tế đang dùng trong code:**
- `pending`
- `success`

---

### Bảng `payment_callbacks`

Log callback từ cổng thanh toán (dùng để đối soát).

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `callback_id` | BigInteger | PK | ID callback |
| `bank_trans_id` | String(100) | NULLABLE, INDEX | Mã giao dịch ngân hàng |
| `order_id` | Integer | FK → orders, NULLABLE, INDEX | ID đơn hàng |
| `payload_raw` | JSON | NULLABLE | Raw payload từ webhook |
| `payload_hash` | String(128) | NULLABLE, INDEX | Hash của payload |
| `signature_ok` | Boolean | DEFAULT FALSE, INDEX | Chữ ký hợp lệ? |
| `received_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm nhận |
| `ip_source` | String(45) | NULLABLE | IP nguồn gửi callback |

---

## 5. Bảo mật IoT (Device Security)

### Bảng `device_identity`

Danh tính thiết bị (certificate, MAC address,...).

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `machine_id` | Integer | PK, FK → machines | ID máy |
| `device_public_key` | Text | NULLABLE | Khóa công khai |
| `cert_fingerprint` | String(128) | NULLABLE, INDEX | Fingerprint chứng chỉ |
| `secure_element_id` | String(100) | NULLABLE, INDEX | ID secure element |
| `mac_address` | String(32) | NULLABLE, INDEX | Địa chỉ MAC |
| `provisioned_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm provision |
| `revoked_at` | DateTime | NULLABLE, INDEX | Thời điểm thu hồi |
| `status` | String(20) | DEFAULT 'active', INDEX | Trạng thái |

**Giá trị `status`:**
- `active` - Đang hoạt động
- `revoked` - Đã thu hồi

---

### Bảng `device_sessions`

Phiên đăng nhập của thiết bị IoT.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `session_id` | Integer | PK | ID session |
| `machine_id` | Integer | FK → machines, NOT NULL, INDEX | ID máy |
| `token_hash` | String(255) | UNIQUE, NOT NULL, INDEX | Hash của session token |
| `issued_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm cấp token |
| `expires_at` | DateTime | NOT NULL, INDEX | Thời điểm hết hạn |
| `last_seen_at` | DateTime | NULLABLE, INDEX | Lần cuối hoạt động |
| `ip_address` | String(45) | NULLABLE | IP address |
| `is_revoked` | Boolean | DEFAULT FALSE, INDEX | Đã thu hồi chưa |

---

## 6. Audit Logs (Nhật ký)

### Bảng `api_audit_logs`

Log tất cả API request từ thiết bị.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `request_id` | BigInteger | PK | ID request |
| `machine_id` | Integer | FK → machines, NULLABLE, INDEX | ID máy |
| `endpoint` | String(200) | NOT NULL, INDEX | API endpoint |
| `method` | String(10) | NOT NULL | HTTP method |
| `ip_address` | String(45) | NULLABLE, INDEX | IP address |
| `response_code` | Integer | NOT NULL, INDEX | HTTP response code |
| `payload_hash` | String(128) | NULLABLE, INDEX | Hash của payload |
| `signature_ok` | Boolean | DEFAULT FALSE, INDEX | Request hợp lệ? |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm |

---

### Bảng `staff_access_logs`

Log nhân viên truy cập/bảo trì máy.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `access_id` | Integer | PK | ID log |
| `user_id` | Integer | FK → users, NULLABLE, INDEX | ID nhân viên |
| `machine_id` | Integer | FK → machines, NOT NULL, INDEX | ID máy |
| `action` | String(30) | NOT NULL, INDEX | Hành động |
| `started_at` | DateTime | DEFAULT NOW(), INDEX | Bắt đầu |
| `ended_at` | DateTime | NULLABLE, INDEX | Kết thúc |
| `note` | Text | NULLABLE | Ghi chú |

**Giá trị `action`:**
- `open` - Mở máy
- `close` - Đóng máy
- `refill` - Nạp hàng
- `maintenance` - Bảo trì

---

## 7. WebAuthn / Passkey

### Bảng `webauthn_credentials`

Lưu Passkey của admin (mỗi user chỉ 1 passkey).

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|--------------|-----------|-------|
| `id` | Integer | PK | ID credential |
| `user_id` | Integer | FK → users, UNIQUE, INDEX | ID user |
| `credential_id` | LargeBinary | UNIQUE, NOT NULL | ID credential (binary) |
| `public_key` | LargeBinary | NOT NULL | Khóa công khai |
| `sign_count` | Integer | DEFAULT 0 | Số lần ký |
| `transports` | String(200) | NULLABLE | JSON array transports |
| `aaguid` | String(36) | NULLABLE | Authenticator model ID |
| `device_name` | String(100) | NULLABLE | Tên thiết bị |
| `last_used_at` | DateTime | NULLABLE, INDEX | Lần cuối sử dụng |
| `created_at` | DateTime | DEFAULT NOW(), INDEX | Thời điểm tạo |

---

## Sơ đồ quan hệ (ER Diagram)

```mermaid
erDiagram
    users ||--o| webauthn_credentials : has
    users ||--o{ staff_access_logs : creates
    
    machines ||--o{ slots : contains
    machines ||--o| device_identity : has
    machines ||--o{ device_sessions : has
    machines ||--o{ api_audit_logs : generates
    machines ||--o{ staff_access_logs : receives
    
    products ||--o{ slots : stored_in
    products ||--o{ orders : ordered_in
    
    slots ||--o{ orders : fulfills
    
    orders ||--o{ transactions : paid_by
    orders ||--o{ payment_callbacks : receives

    users {
        int user_id PK
        string username
        string password
        bool is_active
        datetime created_at
    }
    
    machines {
        int machine_id PK
        string name
        string location
        string status
        string secret_key
        datetime created_at
    }
    
    products {
        int product_id PK
        string product_name
        decimal price
        string image
        bool active
        datetime created_at
    }
    
    slots {
        int slot_id PK
        int machine_id FK
        string slot_code
        int product_id FK
        int stock
        int capacity
        datetime created_at
    }
    
    orders {
        int order_id PK
        int product_id FK
        int slot_id FK
        decimal price_snapshot
        string status_payment
        string status_slots
        datetime created_at
    }
    
    transactions {
        int transaction_id PK
        int order_id FK
        decimal amount
        string bank_trans_id
        string status
        datetime created_at
    }
    
    payment_callbacks {
        bigint callback_id PK
        string bank_trans_id
        int order_id FK
        json payload_raw
        bool signature_ok
        datetime received_at
    }
    
    device_identity {
        int machine_id PK_FK
        text device_public_key
        string cert_fingerprint
        string mac_address
        string status
    }
    
    device_sessions {
        int session_id PK
        int machine_id FK
        string token_hash
        datetime expires_at
        bool is_revoked
    }
    
    api_audit_logs {
        bigint request_id PK
        int machine_id FK
        string endpoint
        string method
        int response_code
        bool signature_ok
    }
    
    staff_access_logs {
        int access_id PK
        int user_id FK
        int machine_id FK
        string action
        datetime started_at
    }
    
    webauthn_credentials {
        int id PK
        int user_id FK
        binary credential_id
        binary public_key
        int sign_count
    }
```

---

## Ghi chú

1. **TimestampMixin**: Nhiều bảng kế thừa mixin này để tự động có cột `created_at`
2. **Index**: Hầu hết các cột thường xuyên query đều được đánh index
3. **Numeric vs Float**: Sử dụng `Numeric(10,2)` cho tiền tệ để tránh lỗi làm tròn
4. **Hash columns**: `password`, `secret_key`, `token_hash` nên lưu dạng hash, không plaintext
