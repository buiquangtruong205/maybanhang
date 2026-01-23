# 📋 TÀI LIỆU API - VENDING MACHINE BACKEND

## 🔐 XÁC THỰC

### Header xác thực

| Loại | Header Key | Value | Sử dụng cho |
|------|------------|-------|-------------|
| JWT Token | `Authorization` | `Bearer <token>` | Admin API (CRUD) |
| Machine Key | `X-Machine-Key` | `may1`, `may2`... | IoT API (ESP/Arduino) |

---

## 📊 BẢNG TẤT CẢ API ENDPOINTS

### Ký hiệu:
- 🔓 Public (không cần auth)
- 🔑 JWT Token (admin)
- 🔧 Machine Key (IoT)

---

## 1. AUTH - Xác thực người dùng

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| POST | `/api/register` | 🔓 | Đăng ký tài khoản |
| POST | `/api/login` | 🔓 | Đăng nhập |
| GET | `/api/users/me` | 🔑 | Lấy thông tin user hiện tại |

### POST /api/register
```json
// Body
{
  "username": "admin",
  "password": "123456"
}
// Response
{
  "success": true,
  "data": {"user_id": 1, "username": "admin"}
}
```

### POST /api/login
```json
// Body
{
  "username": "admin",
  "password": "123456"
}
// Response
{
  "success": true,
  "data": {"access_token": "eyJhbG...", "token_type": "bearer"}
}
```

---

## 2. PRODUCTS - Quản lý sản phẩm

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/products` | 🔓 | Danh sách sản phẩm |
| GET | `/api/products/{id}` | 🔓 | Chi tiết sản phẩm |
| POST | `/api/products` | 🔑 | Tạo sản phẩm |
| PUT | `/api/products/{id}` | 🔑 | Cập nhật sản phẩm |
| DELETE | `/api/products/{id}` | 🔑 | Xóa sản phẩm |
| POST | `/api/upload` | 🔑 | Upload ảnh sản phẩm |

### POST /api/products
```json
// Body
{
  "product_name": "Coca Cola",
  "price": 15000,
  "image": "/static/uploads/abc.jpg",
  "active": true
}
```

### POST /api/upload
```
// Form-data
file: [binary file]

// Response
{
  "success": true,
  "data": {"url": "/static/uploads/abc123.jpg", "filename": "abc123.jpg"}
}
```

---

## 3. SLOTS - Quản lý vị trí (kệ hàng)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/slots` | 🔓 | Danh sách slots |
| GET | `/api/slots?machine_id=1` | 🔓 | Slots theo máy |
| GET | `/api/slots/{id}` | 🔓 | Chi tiết slot |
| POST | `/api/slots` | 🔑 | Tạo slot |
| PUT | `/api/slots/{id}` | 🔑 | Cập nhật slot |
| DELETE | `/api/slots/{id}` | 🔑 | Xóa slot |

### POST /api/slots
```json
// Body
{
  "machine_id": 1,
  "slot_code": "A1",
  "product_id": 5,
  "stock": 10,
  "capacity": 20
}
```

---

## 4. MACHINES - Quản lý máy bán hàng

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/machines` | 🔓 | Danh sách máy |
| GET | `/api/machines/{id}` | 🔓 | Chi tiết máy |
| POST | `/api/machines` | 🔑 | Tạo máy |
| PUT | `/api/machines/{id}` | 🔑 | Cập nhật máy |
| DELETE | `/api/machines/{id}` | 🔑 | Xóa máy |

### POST /api/machines
```json
// Body
{
  "name": "Máy 01",
  "location": "Tầng 1 - Sảnh A",
  "status": "active",
  "secret_key": "may1"
}
```

---

## 5. ORDERS - Quản lý đơn hàng

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/orders` | 🔑 | Danh sách đơn hàng |
| GET | `/api/orders/{id}` | 🔑 | Chi tiết đơn hàng |
| POST | `/api/orders` | 🔓 | Tạo đơn (hoàn thành) |
| POST | `/api/orders/pending` | 🔓 | Tạo đơn chờ thanh toán |
| PUT | `/api/orders/{id}/complete` | 🔓 | Đánh dấu hoàn thành |
| PUT | `/api/orders/{id}/cancel` | 🔓 | Hủy đơn |
| GET | `/api/orders/{id}/status` | 🔓 | Kiểm tra trạng thái |

### POST /api/orders/pending
```json
// Body
{
  "product_id": 5,
  "price_snapshot": 15000,
  "slot_id": 1  // optional
}
// Response
{
  "success": true,
  "data": {"order_id": 123, "status_payment": "pending", ...}
}
```

---

## 6. PAYMENT - Thanh toán PayOS

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| POST | `/api/payment/create` | 🔓 | Tạo link thanh toán |
| GET | `/api/payment/status/{order_code}` | 🔓 | Kiểm tra trạng thái |
| POST | `/api/payment/cancel/{order_code}` | 🔓 | Hủy thanh toán |
| POST | `/api/payment/webhook` | 🔓 | Webhook từ PayOS |
| POST | `/api/payment/sync/{order_code}` | 🔓 | Đồng bộ trạng thái |
| GET | `/api/payment/success` | 🔓 | Trang thành công |
| GET | `/api/payment/cancel` | 🔓 | Trang hủy |

### POST /api/payment/create
```json
// Body
{
  "order_code": 123,
  "amount": 15000,
  "description": "Thanh toán đơn hàng #123",
  "items": [
    {"name": "Coca Cola", "quantity": 1, "price": 15000}
  ],
  "buyer_name": "Nguyen Van A",  // optional
  "buyer_email": "a@email.com",  // optional
  "buyer_phone": "0901234567"    // optional
}
// Response
{
  "success": true,
  "data": {
    "checkout_url": "https://pay.payos.vn/...",
    "qr_code": "https://...",
    "order_code": 123
  }
}
```

---

## 7. TRANSACTIONS - Giao dịch

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/transactions` | 🔑 | Danh sách giao dịch |
| GET | `/api/transactions/{id}` | 🔑 | Chi tiết giao dịch |
| POST | `/api/transactions` | 🔓 | Tạo giao dịch |

### POST /api/transactions
```json
// Body
{
  "order_id": 123,
  "amount": 15000,
  "bank_trans_id": "FT12345",
  "description": "Thanh toán đơn #123",
  "status": "success"
}
```

---

## 8. USERS - Quản lý người dùng

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/users` | 🔑 | Danh sách users |
| GET | `/api/users/{id}` | 🔑 | Chi tiết user |
| PUT | `/api/users/{id}` | 🔑 | Cập nhật user |
| DELETE | `/api/users/{id}` | 🔑 | Xóa user |

### PUT /api/users/{id}
```json
// Body
{
  "username": "newname",
  "password": "newpass",
  "is_active": true
}
```

---

## 9. STATS - Thống kê

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/stats` | 🔑 | Thống kê tổng hợp |

### Response /api/stats
```json
{
  "success": true,
  "data": {
    "monthly_revenue": 1500000,
    "best_product": {"product_name": "Coca Cola", "total_sold": 50},
    "top_customer": {"sender_bank": "Vietcombank", "total_amount": 500000},
    "total_orders": 100
  }
}
```

---

## 10. IOT - API cho ESP/Arduino 🔧

**Tất cả đều yêu cầu Header:** `X-Machine-Key: may1`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/iot/ping` | Ping báo máy hoạt động |
| POST | `/api/iot/create-order` | Tạo đơn hàng |
| GET | `/api/iot/check-payment/{id}` | Kiểm tra thanh toán |
| POST | `/api/iot/dispense-complete` | Báo hoàn thành xuất hàng |
| GET | `/api/iot/pending-orders` | Lấy đơn chờ xuất |
| POST | `/api/iot/stock-update` | Cập nhật tồn kho |
| POST | `/api/iot/telemetry` | Gửi dữ liệu sensor |

### POST /api/iot/ping
```json
// Headers
X-Machine-Key: may1
Content-Type: application/json

// Body (optional)
{"status": "online", "temperature": 25.5}

// Response
{"success": true, "message": "Pong", "machine_id": 1}
```

### POST /api/iot/create-order
```json
// Body
{"product_id": 5, "slot_code": "A1", "quantity": 1}

// Response
{
  "success": true,
  "data": {
    "order_id": 123,
    "product_name": "Coca Cola",
    "price": 15000,
    "status_payment": "pending"
  }
}
```

### GET /api/iot/check-payment/{order_id}
```json
// Response
{
  "success": true,
  "data": {
    "order_id": 123,
    "status_payment": "completed",
    "paid": true,
    "price": 15000
  }
}
```

### POST /api/iot/dispense-complete
```json
// Body
{"order_id": 123, "success": true, "message": "OK"}

// Response
{"success": true, "message": "Dispense completed"}
```

### GET /api/iot/pending-orders
```json
// Response
{
  "success": true,
  "data": [
    {"order_id": 123, "slot_id": 1, "product_id": 5, "price": 15000}
  ]
}
```

### POST /api/iot/stock-update
```json
// Body
{"slot_code": "A1", "stock": 5}

// Response
{"success": true, "old_stock": 10, "new_stock": 5}
```

### POST /api/iot/telemetry
```json
// Body
{
  "temperature": 25.5,
  "humidity": 60.0,
  "voltage": 12.1,
  "door_open": false,
  "metrics": {"sensor1": 100}
}

// Response
{"success": true, "log_id": 456}
```

---

## 🔴 MÃ LỖI HTTP

| Code | Ý nghĩa |
|------|---------|
| `200` | Thành công |
| `201` | Tạo mới thành công |
| `400` | Dữ liệu không hợp lệ |
| `401` | Chưa đăng nhập / Thiếu key |
| `403` | Không có quyền / Key sai |
| `404` | Không tìm thấy |
| `422` | Lỗi validation |
| `500` | Lỗi server |

---

## 📌 LƯU Ý

1. **Content-Type**: Tất cả request body đều là JSON, cần header `Content-Type: application/json`
2. **Machine Keys cấu hình trong**: `backend/app/config.py` → `MACHINE_KEYS`
3. **JWT Token format**: `Authorization: Bearer eyJhbG...`
4. **Base URL**: `http://localhost:5000/api` (local) hoặc `https://maybanhang-o9t8.onrender.com/api` (Render)
